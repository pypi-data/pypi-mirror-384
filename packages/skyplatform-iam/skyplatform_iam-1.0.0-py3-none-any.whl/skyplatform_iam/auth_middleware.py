from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict
import jwt

from .connect_agenterra_iam import ConnectAgenterraIam
import logging

logger = logging.getLogger(__name__)


class AuthMiddleware:
    def __init__(self):
        self.security = HTTPBearer(auto_error=False)
        self.iam_client = ConnectAgenterraIam()

    async def verify_token(self, request: Request):
        # 通过token, server_ak, server_sk判断是否有权限
        credentials: HTTPAuthorizationCredentials = await self.security(request)
        api_path = request.url.path
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
            print(403)
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


# 创建全局认证中间件实例
auth_middleware = AuthMiddleware()


# 便捷的依赖函数
async def get_current_user(request: Request) -> Dict:
    """获取当前用户的依赖函数"""
    return await auth_middleware.require_auth(request)


async def get_optional_user(request: Request) -> Optional[Dict]:
    """获取可选当前用户的依赖函数"""
    return await auth_middleware.optional_auth(request)
