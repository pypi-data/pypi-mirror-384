"""
SkyPlatform IAM SDK
提供FastAPI认证中间件和IAM服务连接功能
"""

from .config import AuthConfig
from .middleware import AuthMiddleware
from .connect_agenterra_iam import ConnectAgenterraIam
from .exceptions import (
    SkyPlatformAuthException,
    AuthenticationError,
    AuthorizationError,
    TokenExpiredError,
    TokenInvalidError,
    ConfigurationError,
    IAMServiceError,
    NetworkError
)

__version__ = "1.0.0"
__author__ = "x9"
__description__ = "SkyPlatform IAM认证SDK，提供FastAPI中间件和IAM服务连接功能"

# 导出主要类和函数
__all__ = [
    # 配置
    "AuthConfig",
    
    # 中间件
    "AuthMiddleware",
    
    # 客户端
    "ConnectAgenterraIam",
    
    # 异常
    "SkyPlatformAuthException",
    "AuthenticationError", 
    "AuthorizationError",
    "TokenExpiredError",
    "TokenInvalidError",
    "ConfigurationError",
    "IAMServiceError",
    "NetworkError",
    
    # 版本信息
    "__version__",
    "__author__",
    "__description__"
]


def create_auth_middleware(config: AuthConfig = None, **kwargs) -> AuthMiddleware:
    """
    创建认证中间件的便捷函数
    
    Args:
        config: 认证配置，如果为None则从环境变量创建
        **kwargs: 其他中间件参数
        
    Returns:
        AuthMiddleware: 认证中间件实例
        
    Note:
        此函数用于创建中间件实例，用于请求拦截和鉴权。
        客户端应用需要自己实现具体的业务接口。
    """
    if config is None:
        config = AuthConfig.from_env()
    
    return AuthMiddleware(config=config, **kwargs)


def setup_auth(app, config: AuthConfig = None):
    """
    一键设置认证中间件的便捷函数
    
    Args:
        app: FastAPI应用实例
        config: 认证配置，如果为None则从环境变量创建
        
    Returns:
        AuthMiddleware: 认证中间件实例
        
    Note:
        此函数只设置认证中间件，不包含预制路由。
        客户端应用需要根据业务需求自己实现认证相关的API接口。
    """
    if config is None:
        config = AuthConfig.from_env()
    
    # 添加中间件
    middleware = AuthMiddleware(app=app, config=config)
    app.add_middleware(AuthMiddleware, config=config)
    
    return middleware