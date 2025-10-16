"""
SkyPlatform IAM SDK 中间件模块
"""
import logging
from typing import Optional, Callable, Dict, Any
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
import jwt

from .config import AuthConfig
from .connect_agenterra_iam import ConnectAgenterraIam
from .exceptions import (
    AuthenticationError,
    AuthorizationError,
    ConfigurationError
)

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """
    认证中间件
    自动拦截请求进行Token验证和权限检查
    """

    def __init__(
            self,
            app,
            config: AuthConfig,
            skip_validation: Optional[Callable[[Request], bool]] = None
    ):
        """
        初始化认证中间件
        
        Args:
            app: FastAPI应用实例
            config: 认证配置
            skip_validation: 自定义跳过验证的函数
        """
        super().__init__(app)
        self.config = config
        self.iam_client = ConnectAgenterraIam(config=config)
        self.skip_validation = skip_validation

        # 验证配置
        try:
            self.config.validate_config()
        except ValueError as e:
            raise ConfigurationError(str(e))

    def is_path_whitelisted(self, path: str) -> bool:
        """
        检查路径是否在本地白名单中
        """
        if not self.config:
            return False
        return self.config.is_path_whitelisted(path)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        中间件主要处理逻辑
        """
        try:
            # 获取请求路径
            api_path = request.url.path
            
            # 首先检查路径是否在本地白名单中
            if self.is_path_whitelisted(api_path):
                logger.info(f"路径 {api_path} 在本地白名单中，跳过认证直接允许访问")
                # 设置白名单标识
                request.state.user = None
                request.state.authenticated = False
                request.state.is_whitelist = True
                # 直接调用下一个处理器
                response = await call_next(request)
                return response

            # 提取Token（可能为空，白名单接口不需要token）
            token = self._extract_token(request)

            # 验证Token和权限（即使token为空也要调用IAM验证，因为可能是白名单接口）
            user_info = await self._verify_token_and_permission(request, token)
            if not user_info:
                return self._create_error_response(
                    status_code=401,
                    message="Token验证失败",
                    detail="提供的Token无效或已过期"
                )

            # 检查是否为白名单接口
            if user_info.get('is_whitelist', False):
                # 白名单接口，允许访问但不设置用户信息
                request.state.user = None
                request.state.authenticated = False
                request.state.is_whitelist = True
            else:
                # 正常认证接口，设置用户信息
                request.state.user = user_info
                request.state.authenticated = True
                request.state.is_whitelist = False

            # 继续处理请求
            response = await call_next(request)
            return response

        except HTTPException as e:
            return self._create_error_response(
                status_code=e.status_code,
                message=str(e.detail),
                detail=getattr(e, 'detail', None)
            )
        except AuthenticationError as e:
            return self._create_error_response(
                status_code=e.status_code,
                message=e.message,
                detail=e.detail
            )
        except AuthorizationError as e:
            return self._create_error_response(
                status_code=e.status_code,
                message=e.message,
                detail=e.detail
            )
        except Exception as e:
            logger.error(f"认证中间件处理异常: {str(e)}")
            if self.config.enable_debug:
                logger.exception("详细异常信息:")

            return self._create_error_response(
                status_code=500,
                message="内部服务器错误",
                detail=str(e) if self.config.enable_debug else None
            )

    def _extract_token(self, request: Request) -> Optional[str]:
        """
        从请求中提取Token
        """
        # 从Authorization头提取
        auth_header = request.headers.get(self.config.token_header)
        if auth_header and auth_header.startswith(self.config.token_prefix):
            return auth_header[len(self.config.token_prefix):].strip()

        # 从查询参数提取（备选方案）
        token = request.query_params.get("token")
        if token:
            return token

        return None

    async def _verify_token_and_permission(self, request: Request, token: Optional[str]) -> Optional[Dict[str, Any]]:
        """
        验证Token和权限
        """
        try:
            # 获取请求信息
            api_path = request.url.path
            method = request.method

            # 从请求头获取服务认证信息（可选）
            server_ak = request.headers.get("SERVER-AK", "")
            server_sk = request.headers.get("SERVER-SK", "")

            # 调用IAM验证接口（即使token为空也要调用，因为可能是白名单接口）
            user_info = self.iam_client.verify_token(
                token=token or "",  # 如果token为None，传递空字符串
                api=api_path,
                method=method,
                server_ak=server_ak,
                server_sk=server_sk
            )

            return user_info

        except HTTPException:
            # 重新抛出HTTP异常
            raise
        except Exception as e:
            logger.error(f"Token验证异常: {str(e)}")
            if self.config.enable_debug:
                logger.exception("详细异常信息:")
            return None

    def _create_error_response(
            self,
            status_code: int,
            message: str,
            detail: Optional[str] = None
    ) -> JSONResponse:
        """
        创建错误响应
        """
        error_data = {
            "success": False,
            "message": message,
            "status_code": status_code
        }

        if detail:
            error_data["detail"] = detail

        return JSONResponse(
            status_code=status_code,
            content=error_data
        )


class AuthService:
    """
    认证服务类
    提供依赖注入式的认证功能
    """

    def __init__(self, auth_config: AuthConfig):
        if auth_config is None:
            raise ValueError("auth_config参数不能为None，必须传入AuthConfig配置对象")
        self.security = HTTPBearer(auto_error=False)
        self.iam_client = ConnectAgenterraIam(config=auth_config)
        self.auth_config = auth_config

    def is_path_whitelisted(self, path: str) -> bool:
        """
        检查路径是否在白名单中
        """
        if not self.auth_config:
            return False
        return self.auth_config.is_path_whitelisted(path)

    async def verify_token(self, request: Request):
        """验证token和权限"""
        # 通过token, server_ak, server_sk判断是否有权限
        api_path = request.url.path
        
        # 首先检查路径是否在白名单中
        if self.is_path_whitelisted(api_path):
            logger.info(f"路径 {api_path} 在白名单中，跳过IAM鉴权")
            return True
        
        credentials: HTTPAuthorizationCredentials = await self.security(request)
        method = request.method

        server_ak = request.headers.get("SERVER-AK", "")
        server_sk = request.headers.get("SERVER-SK", "")

        token = ""
        if credentials is not None:
            token = credentials.credentials
        user_info_by_iam = self.iam_client.verify_token(token, api_path, method, server_ak, server_sk)
        if user_info_by_iam:
            return True
        return False

    async def get_current_user(self, request: Request) -> Optional[Dict]:
        """获取当前用户信息"""
        try:
            # 直接调用verify_token方法进行token验证
            if not await self.verify_token(request):
                return None

            # 获取token用于后续用户信息获取
            credentials: HTTPAuthorizationCredentials = await self.security(request)
            if not credentials:
                return None
                
            token = credentials.credentials

            # 直接解析JWT token获取payload
            payload = self.decode_jwt_token(token)
            if not payload:
                logger.error("JWT token解析失败")
                return None

            # 从payload中提取用户信息
            iam_user_id = payload.get("sub")  # JWT标准中用户ID存储在sub字段
            username = None

            # 解析新的凭证信息结构
            all_credentials = payload.get("all_credentials", [])
            total_credentials = payload.get("total_credentials", 0)

            # 从all_credentials中提取username（向后兼容）
            for cred in all_credentials:
                if cred.get("type") == "username":
                    username = cred.get("value")
                    break

            # 向后兼容性：如果没有all_credentials，尝试从payload的其他字段构建
            if not all_credentials:
                credentials_list = []
                # 检查payload中是否有直接的username字段
                if payload.get("username"):
                    username = payload.get("username")
                    credentials_list.append({"type": "username", "value": username})
                if payload.get("email"):
                    credentials_list.append({"type": "email", "value": payload.get("email")})
                if payload.get("phone"):
                    credentials_list.append({"type": "phone", "value": payload.get("phone")})
                all_credentials = credentials_list
                total_credentials = len(credentials_list)

            if not username:
                return None

            # 构建用户信息字典
            user_info = {
                "id": iam_user_id,
                "username": username,
                "all_credentials": all_credentials,
                "total_credentials": total_credentials,
                "microservice": payload.get("microservice")  # 添加微服务信息
            }

            # 向后兼容：添加传统字段映射
            for cred in all_credentials:
                if cred.get("type") == "email":
                    user_info["email"] = cred.get("value")
                elif cred.get("type") == "phone":
                    user_info["phone"] = cred.get("value")
                elif cred.get("type") == "username" and not user_info.get("username"):
                    user_info["username"] = cred.get("value")

            # 统计凭证类型分布
            cred_types = [cred.get("type") for cred in all_credentials]
            cred_type_count = {cred_type: cred_types.count(cred_type) for cred_type in set(cred_types)}

            logger.info(
                f"用户认证成功: user_id={iam_user_id}, username={username}, 凭证数量={total_credentials}, 凭证类型分布={cred_type_count}")
            logger.debug(f"JWT payload: {payload}")

            # 将用户信息添加到请求状态中
            request.state.user = user_info
            return user_info

        except HTTPException as e:
            logger.error(f"获取当前用户信息失败: {str(e)}")
            # 重新抛出HTTP异常（403权限不足）
            return None
        except Exception as e:
            logger.error(f"获取当前用户信息失败: {str(e)}")
            return None

    async def require_auth(self, request: Request) -> Dict:
        """要求用户必须登录"""
        try:
            user_info = await self.get_current_user(request)
            if not user_info:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="需要登录认证",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return user_info
        except HTTPException:
            # 重新抛出HTTP异常（可能是403权限不足或401未认证）
            raise

    async def optional_auth(self, request: Request) -> Optional[Dict]:
        """可选的用户认证（不强制要求登录）"""
        try:
            return await self.get_current_user(request)
        except HTTPException:
            # 对于可选认证，如果是403权限不足，仍然抛出异常
            # 如果是401未认证，返回None
            raise

    def decode_jwt_token(self, token: str) -> Optional[Dict]:
        """直接解析JWT token获取payload"""
        try:
            # 不验证签名，只解析payload（因为token已经通过verify_token验证过）
            decoded_payload = jwt.decode(token, options={"verify_signature": False})
            logger.debug(f"JWT token解析成功: {decoded_payload}")
            return decoded_payload
        except jwt.InvalidTokenError as e:
            logger.error(f"JWT token解析失败: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"JWT token解析异常: {str(e)}")
            return None


# 全局认证服务实例（延迟初始化）
auth_service = None


def setup_auth_middleware(auth_config: AuthConfig) -> None:
    """
    设置认证中间件配置
    
    Args:
        auth_config: 认证配置实例，包含白名单路径等配置
    """
    global auth_service
    auth_service = AuthService(auth_config)
    logger.info(f"认证中间件已配置，白名单路径数量: {len(auth_config.get_whitelist_paths())}")


# 便捷的依赖函数
async def get_current_user(request: Request) -> Dict:
    """获取当前用户的依赖函数"""
    if auth_service is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="认证服务未初始化，请先调用setup_auth_middleware函数进行配置"
        )
    return await auth_service.require_auth(request)


async def get_optional_user(request: Request) -> Optional[Dict]:
    """获取可选当前用户的依赖函数"""
    if auth_service is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="认证服务未初始化，请先调用setup_auth_middleware函数进行配置"
        )
    return await auth_service.optional_auth(request)
