"""
SkyPlatform IAM SDK 中间件模块
"""
import logging
from typing import Optional, Callable, Dict, Any
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

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
        self.iam_client = ConnectAgenterraIam()
        self.skip_validation = skip_validation

        # 验证配置
        try:
            self.config.validate_config()
        except ValueError as e:
            raise ConfigurationError(str(e))

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        中间件主要处理逻辑
        """
        try:

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
            # FastAPI HTTPException直接返回
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
