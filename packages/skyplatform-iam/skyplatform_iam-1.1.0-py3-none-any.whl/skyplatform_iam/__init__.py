"""
SkyPlatform IAM SDK
提供FastAPI认证中间件和IAM服务连接功能
"""

from .config import AuthConfig
from .middleware import AuthMiddleware, AuthService, setup_auth_middleware, get_current_user, get_optional_user
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

# 全局IAM客户端实例
_global_iam_client = None

# 导出主要类和函数
__all__ = [
    # 配置
    "AuthConfig",
    
    # 中间件
    "AuthMiddleware",
    "AuthService",
    "setup_auth_middleware",
    "get_current_user",
    "get_optional_user",
    
    # 客户端
    "ConnectAgenterraIam",
    "get_iam_client",
    
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


def init_skyplatform_iam(app, config: AuthConfig = None):
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
        建议传入完整的AuthConfig对象以避免环境变量配置问题。
    """
    if config is None:
        config = AuthConfig.from_env()
    
    # 验证配置的完整性
    config.validate_config()
    
    # 初始化全局认证服务
    setup_auth_middleware(config)
    
    # 添加中间件
    middleware = AuthMiddleware(app=app, config=config)
    app.add_middleware(AuthMiddleware, config=config)
    
    return middleware


def get_iam_client(config: AuthConfig = None) -> ConnectAgenterraIam:
    """
    获取全局IAM客户端实例
    
    Args:
        config: 认证配置，如果为None则从环境变量创建
        
    Returns:
        ConnectAgenterraIam: IAM客户端实例
        
    Note:
        此函数使用单例模式，确保整个应用中只有一个IAM客户端实例。
        第一次调用时会创建实例，后续调用会返回同一个实例。
        如果需要更新配置，可以传入新的config参数。
        
    Example:
        # 使用默认配置（从环境变量）
        iam_client = get_iam_client()
        
        # 使用自定义配置
        config = AuthConfig(
            agenterra_iam_host="https://iam.example.com",
            server_name="my_server",
            access_key="my_access_key"
        )
        iam_client = get_iam_client(config)
        
        # 调用IAM服务方法
        result = iam_client.register(
            cred_type="username",
            cred_value="test_user",
            password="password123"
        )
    """
    global _global_iam_client
    
    # 如果传入了新的配置，或者实例不存在，则创建/更新实例
    if config is not None:
        if _global_iam_client is None:
            _global_iam_client = ConnectAgenterraIam(config=config)
        else:
            # 重新加载配置
            _global_iam_client.reload_config(config)
    elif _global_iam_client is None:
        # 使用默认配置创建实例
        default_config = AuthConfig.from_env()
        _global_iam_client = ConnectAgenterraIam(config=default_config)
    
    return _global_iam_client