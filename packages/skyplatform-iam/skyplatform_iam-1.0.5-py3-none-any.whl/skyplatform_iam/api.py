"""
SkyPlatform IAM SDK 统一API模块
提供统一的初始化和全局访问接口
"""
import logging
from typing import Optional, Dict, Any
from fastapi import FastAPI, Request

from .config import AuthConfig
from .global_manager import get_global_manager, GlobalIAMManager
from .connect_agenterra_iam import ConnectAgenterraIam
from .exceptions import IAMServiceError, ConfigurationError

logger = logging.getLogger(__name__)


def init_skyplatform_iam(
    app: FastAPI, 
    config: Optional[AuthConfig] = None,
    **kwargs
) -> GlobalIAMManager:
    """
    统一初始化SkyPlatform IAM SDK
    一次配置，全局可用
    
    Args:
        app: FastAPI应用实例
        config: 认证配置，如果为None则从环境变量加载
        **kwargs: 额外配置参数
        
    Returns:
        GlobalIAMManager: 全局IAM管理器实例
        
    Raises:
        ConfigurationError: 配置错误
        IAMServiceError: IAM服务连接错误
        
    Example:
        # 方式1：直接配置
        config = AuthConfig(
            agenterra_iam_host="http://127.0.0.1:5001",
            server_name="Agenterra_shop",
            access_key="your_access_key"
        )
        init_skyplatform_iam(app, config)
        
        # 方式2：从环境变量加载
        init_skyplatform_iam(app)
    """
    logger.info("开始初始化SkyPlatform IAM SDK")
    
    try:
        # 获取全局管理器
        manager = get_global_manager()
        
        # 如果已经初始化，记录警告并返回
        if manager.is_initialized():
            logger.warning("SkyPlatform IAM SDK已经初始化，跳过重复初始化")
            return manager
        
        # 处理配置
        if config is None:
            logger.info("未提供配置，从环境变量加载")
            try:
                config = AuthConfig.from_env()
            except Exception as e:
                raise ConfigurationError(f"从环境变量加载配置失败: {str(e)}")
        
        # 应用额外配置参数
        if kwargs:
            logger.debug(f"应用额外配置参数: {kwargs}")
            config = config.copy_with_updates(**kwargs)
        
        # 初始化管理器
        manager.initialize(app, config)
        
        logger.info("SkyPlatform IAM SDK初始化完成")
        return manager
        
    except Exception as e:
        logger.error(f"SkyPlatform IAM SDK初始化失败: {str(e)}")
        raise


class LazyIAMClient:
    """
    懒加载的IAM客户端包装器
    解决模块导入时的初始化顺序问题
    """
    
    def __init__(self):
        self._client = None
        self._initialized = False
    
    def _get_client(self) -> ConnectAgenterraIam:
        """获取实际的IAM客户端实例"""
        if not self._initialized:
            try:
                manager = get_global_manager()
                self._client = manager.get_client()
                self._initialized = True
            except Exception as e:
                # 提供更详细的错误信息和解决建议
                error_msg = (
                    f"获取IAM客户端失败: {str(e)}\n\n"
                    "解决方案:\n"
                    "1. 确保在使用IAM客户端前调用 init_skyplatform_iam() 初始化SDK\n"
                    "2. 避免在模块导入时直接调用 get_iam_client()，应在函数内部调用\n"
                    "3. 检查初始化顺序，确保SDK在应用启动时正确初始化\n\n"
                    "正确的使用方式:\n"
                    "```python\n"
                    "# 在main.py或应用启动时\n"
                    "from skyplatform_iam import init_skyplatform_iam\n"
                    "init_skyplatform_iam(app, config)\n\n"
                    "# 在业务代码中\n"
                    "def some_function():\n"
                    "    iam_client = get_iam_client()  # 在函数内部调用\n"
                    "    return iam_client.login_with_password(...)\n"
                    "```"
                )
                logger.error(error_msg)
                raise IAMServiceError(error_msg)
        return self._client
    
    def __getattr__(self, name):
        """代理所有属性访问到实际的IAM客户端"""
        client = self._get_client()
        return getattr(client, name)
    
    def __repr__(self):
        """提供有用的调试信息"""
        if self._initialized and self._client:
            return f"<LazyIAMClient: {repr(self._client)}>"
        else:
            return "<LazyIAMClient: 未初始化，将在首次使用时自动初始化>"


def get_iam_client() -> ConnectAgenterraIam:
    """
    获取全局IAM客户端实例
    
    Returns:
        ConnectAgenterraIam: IAM客户端实例
        
    Raises:
        IAMServiceError: 如果SDK未初始化
        
    Example:
        # 正确的使用方式 - 注意要加括号调用函数
        iam_client = get_iam_client()  # 正确 ✓
        user_info = iam_client.get_user_by_id("user123")
        
        # 用于登录验证
        result = iam_client.login_with_password(
            username="test_user",
            password="password123"
        )
        
        # 常见错误 - 不要这样做
        # iam_client = get_iam_client  # 错误 ✗ 缺少括号
        # 这会导致 'function' object has no attribute 'login_with_password' 错误
        
    Note:
        确保在调用此函数前已经通过 init_skyplatform_iam() 初始化了SDK
        
    Warning:
        避免在模块导入时直接调用此函数，应在函数内部调用以避免初始化顺序问题
    """
    try:
        manager = get_global_manager()
        return manager.get_client()
    except Exception as e:
        # 提供更详细的错误信息和解决建议
        error_msg = (
            f"获取IAM客户端失败: {str(e)}\n\n"
            "解决方案:\n"
            "1. 确保在使用IAM客户端前调用 init_skyplatform_iam() 初始化SDK\n"
            "2. 避免在模块导入时直接调用 get_iam_client()，应在函数内部调用\n"
            "3. 检查初始化顺序，确保SDK在应用启动时正确初始化\n\n"
            "正确的使用方式:\n"
            "```python\n"
            "# 在main.py或应用启动时\n"
            "from skyplatform_iam import init_skyplatform_iam\n"
            "init_skyplatform_iam(app, config)\n\n"
            "# 在业务代码中\n"
            "def some_function():\n"
            "    iam_client = get_iam_client()  # 在函数内部调用\n"
            "    return iam_client.login_with_password(...)\n"
            "```\n\n"
            "如果需要在模块级别使用IAM客户端，请考虑使用 create_lazy_iam_client() 函数"
        )
        logger.error(error_msg)
        raise IAMServiceError(error_msg)


def create_lazy_iam_client() -> LazyIAMClient:
    """
    创建懒加载的IAM客户端实例
    
    这个函数专门用于解决模块导入时的初始化顺序问题。
    返回的客户端会在首次使用时才进行实际的初始化。
    
    Returns:
        LazyIAMClient: 懒加载的IAM客户端包装器
        
    Example:
        # 在模块级别安全使用（推荐用于解决导入顺序问题）
        iam_client = create_lazy_iam_client()
        
        # 在函数中使用时才会真正初始化
        def login_user(username, password):
            return iam_client.login_with_password(username, password)
            
        # 也可以在类中使用
        class AuthService:
            def __init__(self):
                self.iam_client = create_lazy_iam_client()
                
            def authenticate(self, username, password):
                return self.iam_client.login_with_password(username, password)
    """
    return LazyIAMClient()


async def get_current_user_info(request: Request) -> Optional[Dict[str, Any]]:
    """
    便捷方法：获取当前用户信息
    
    Args:
        request: FastAPI请求对象
        
    Returns:
        Optional[Dict]: 用户信息字典，如果未登录则返回None
        
    Raises:
        IAMServiceError: 如果SDK未初始化
        
    Example:
        @app.get("/profile")
        async def get_profile(request: Request):
            user = await get_current_user_info(request)
            if not user:
                raise HTTPException(401, "未登录")
            return {"user": user}
    """
    try:
        manager = get_global_manager()
        return await manager.get_current_user_info(request)
    except Exception as e:
        logger.error(f"获取当前用户信息失败: {str(e)}")
        if isinstance(e, IAMServiceError):
            raise
        return None


async def verify_permission(
    user_id: str, 
    permission: str, 
    resource: Optional[str] = None
) -> bool:
    """
    便捷方法：验证用户权限
    
    Args:
        user_id: 用户ID
        permission: 权限标识
        resource: 资源标识（可选）
        
    Returns:
        bool: 是否有权限
        
    Raises:
        IAMServiceError: 如果SDK未初始化
        
    Example:
        has_permission = await verify_permission("user123", "read", "document")
        if not has_permission:
            raise HTTPException(403, "权限不足")
    """
    try:
        manager = get_global_manager()
        return await manager.verify_permission(user_id, permission, resource)
    except Exception as e:
        logger.error(f"权限验证失败: {str(e)}")
        if isinstance(e, IAMServiceError):
            raise
        return False


def get_config() -> AuthConfig:
    """
    获取当前配置
    
    Returns:
        AuthConfig: 当前认证配置
        
    Raises:
        IAMServiceError: 如果SDK未初始化
        
    Example:
        config = get_config()
        print(f"当前服务名: {config.server_name}")
    """
    try:
        manager = get_global_manager()
        return manager.get_config()
    except Exception as e:
        logger.error(f"获取配置失败: {str(e)}")
        raise


def get_sdk_status() -> Dict[str, Any]:
    """
    获取SDK状态信息
    
    Returns:
        Dict: SDK状态信息
        
    Example:
        status = get_sdk_status()
        print(f"SDK初始化状态: {status['initialized']}")
    """
    try:
        manager = get_global_manager()
        return manager.get_status()
    except Exception as e:
        logger.error(f"获取SDK状态失败: {str(e)}")
        return {
            "initialized": False,
            "error": str(e)
        }


def reset_sdk() -> None:
    """
    重置SDK状态（主要用于测试）
    
    Warning:
        此方法会清除所有SDK状态，仅在测试环境中使用
    """
    logger.warning("重置SDK状态")
    try:
        manager = get_global_manager()
        manager.reset()
        logger.info("SDK状态已重置")
    except Exception as e:
        logger.error(f"重置SDK状态失败: {str(e)}")


# 向后兼容的别名
def setup_auth(app: FastAPI, config: Optional[AuthConfig] = None) -> GlobalIAMManager:
    """
    向后兼容的初始化函数
    
    Args:
        app: FastAPI应用实例
        config: 认证配置
        
    Returns:
        GlobalIAMManager: 全局IAM管理器实例
        
    Deprecated:
        请使用 init_skyplatform_iam() 替代
    """
    logger.warning("setup_auth()已废弃，请使用init_skyplatform_iam()替代")
    return init_skyplatform_iam(app, config)