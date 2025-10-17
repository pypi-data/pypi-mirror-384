"""
SkyPlatform IAM SDK
提供FastAPI认证中间件和IAM服务连接功能
"""

from .config import AuthConfig
from .middleware import (
    AuthMiddleware, 
    AuthService, 
    setup_auth_middleware, 
    get_current_user, 
    get_optional_user,
    create_auth_middleware
)
from .connect_agenterra_iam import ConnectAgenterraIam
from .global_manager import GlobalIAMManager, get_global_manager
from .api import (
    init_skyplatform_iam,
    get_iam_client,
    create_lazy_iam_client,
    LazyIAMClient,
    get_current_user_info,
    verify_permission,
    get_config,
    get_sdk_status,
    reset_sdk,
    setup_auth  # 向后兼容的别名
)
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

__version__ = "2.0.0"
__author__ = "x9"
__description__ = "SkyPlatform IAM认证SDK，提供FastAPI中间件和IAM服务连接功能"

# 导出主要类和函数
__all__ = [
    # 配置
    "AuthConfig",
    
    # 新的统一API（推荐使用）
    "init_skyplatform_iam",
    "get_iam_client",
    "create_lazy_iam_client",
    "LazyIAMClient",
    "get_current_user_info",
    "verify_permission",
    "get_config",
    "get_sdk_status",
    "reset_sdk",
    
    # 全局管理器
    "GlobalIAMManager",
    "get_global_manager",
    
    # 中间件
    "AuthMiddleware",
    "AuthService",
    "create_auth_middleware",
    "get_current_user",
    "get_optional_user",
    
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
    
    # 向后兼容（已废弃）
    "setup_auth_middleware",
    "setup_auth",
    
    # 版本信息
    "__version__",
    "__author__",
    "__description__"
]


# 向后兼容的便捷函数（已废弃）
def create_auth_middleware_legacy(config: AuthConfig = None, **kwargs) -> AuthMiddleware:
    """
    创建认证中间件的便捷函数（已废弃）
    
    Args:
        config: 认证配置，如果为None则从环境变量创建
        **kwargs: 其他中间件参数
        
    Returns:
        AuthMiddleware: 认证中间件实例
        
    Deprecated:
        请使用 init_skyplatform_iam() + create_auth_middleware() 替代
    """
    import warnings
    warnings.warn(
        "create_auth_middleware_legacy()已废弃，请使用init_skyplatform_iam() + create_auth_middleware()替代",
        DeprecationWarning,
        stacklevel=2
    )
    
    if config is None:
        config = AuthConfig.from_env()
    
    return AuthMiddleware(config=config, use_global_manager=False, **kwargs)


def setup_auth_legacy(app, config: AuthConfig = None):
    """
    一键设置认证中间件的便捷函数（已废弃）
    
    Args:
        app: FastAPI应用实例
        config: 认证配置，如果为None则从环境变量创建
        
    Returns:
        AuthMiddleware: 认证中间件实例
        
    Deprecated:
        请使用 init_skyplatform_iam() 替代
    """
    import warnings
    warnings.warn(
        "setup_auth_legacy()已废弃，请使用init_skyplatform_iam()替代",
        DeprecationWarning,
        stacklevel=2
    )
    
    if config is None:
        config = AuthConfig.from_env()
    
    # 验证配置的完整性
    config.validate_config()
    
    # 初始化全局认证服务
    setup_auth_middleware(config)
    
    # 添加中间件
    middleware = AuthMiddleware(app=app, config=config, use_global_manager=False)
    app.add_middleware(AuthMiddleware, config=config, use_global_manager=False)
    
    return middleware