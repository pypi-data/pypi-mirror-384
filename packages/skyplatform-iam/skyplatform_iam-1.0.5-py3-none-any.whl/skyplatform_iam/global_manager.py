"""
SkyPlatform IAM SDK 全局管理器模块
提供单例模式的全局状态管理，确保线程安全和统一配置
"""
import threading
import logging
from typing import Optional, Dict, Any, TYPE_CHECKING
from fastapi import FastAPI, Request

from .config import AuthConfig
from .connect_agenterra_iam import ConnectAgenterraIam
from .exceptions import ConfigurationError, IAMServiceError

# 使用TYPE_CHECKING避免循环导入
if TYPE_CHECKING:
    from .middleware import AuthMiddleware

logger = logging.getLogger(__name__)


class GlobalIAMManager:
    """
    全局IAM管理器，使用单例模式
    负责管理全局的IAM配置、客户端实例和中间件
    """
    
    _instance: Optional['GlobalIAMManager'] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> 'GlobalIAMManager':
        """单例模式实现，确保线程安全"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化全局管理器"""
        if hasattr(self, '_initialized') and self._initialized:
            return
            
        self._config: Optional[AuthConfig] = None
        self._iam_client: Optional[ConnectAgenterraIam] = None
        self._middleware: Optional['AuthMiddleware'] = None
        self._app: Optional[FastAPI] = None
        self._initialized = False
        self._init_lock = threading.Lock()
        
        logger.debug("GlobalIAMManager实例已创建")
    
    def initialize(self, app: FastAPI, config: Optional[AuthConfig] = None, **kwargs) -> None:
        """
        初始化IAM管理器
        
        Args:
            app: FastAPI应用实例
            config: 认证配置，如果为None则从环境变量加载
            **kwargs: 额外配置参数
            
        Raises:
            ConfigurationError: 配置错误
            IAMServiceError: IAM服务连接错误
        """
        with self._init_lock:
            if self._initialized:
                logger.warning("GlobalIAMManager已经初始化，跳过重复初始化")
                return
            
            try:
                # 1. 处理配置
                if config is None:
                    logger.info("未提供配置，尝试从环境变量加载")
                    config = AuthConfig.from_env()
                
                # 验证配置
                config.validate_config()
                self._config = config
                
                # 2. 创建IAM客户端
                self._iam_client = ConnectAgenterraIam(config=config)
                logger.info(f"IAM客户端已创建，连接到: {config.agenterra_iam_host}")
                
                # 3. 创建中间件（不直接注册，由用户决定）
                from .middleware import AuthMiddleware
                self._middleware = AuthMiddleware(app=app, config=config, use_global_manager=False)
                logger.info("认证中间件已创建")
                
                # 4. 保存应用引用
                self._app = app
                
                # 5. 标记为已初始化
                self._initialized = True
                
                logger.info(f"GlobalIAMManager初始化完成 - 服务: {config.server_name}, "
                          f"白名单路径数量: {len(config.get_whitelist_paths())}")
                
            except Exception as e:
                logger.error(f"GlobalIAMManager初始化失败: {str(e)}")
                # 清理部分初始化的状态
                self._config = None
                self._iam_client = None
                self._middleware = None
                self._app = None
                
                if isinstance(e, (ConfigurationError, IAMServiceError)):
                    raise
                else:
                    raise IAMServiceError(f"初始化失败: {str(e)}")
    
    def get_client(self) -> ConnectAgenterraIam:
        """
        获取IAM客户端实例
        
        Returns:
            ConnectAgenterraIam: IAM客户端实例
            
        Raises:
            IAMServiceError: 如果管理器未初始化
        """
        if not self._initialized or self._iam_client is None:
            raise IAMServiceError(
                "GlobalIAMManager未初始化，请先调用init_skyplatform_iam()函数进行初始化"
            )
        return self._iam_client
    
    def get_config(self) -> AuthConfig:
        """
        获取当前配置
        
        Returns:
            AuthConfig: 当前认证配置
            
        Raises:
            IAMServiceError: 如果管理器未初始化
        """
        if not self._initialized or self._config is None:
            raise IAMServiceError(
                "GlobalIAMManager未初始化，请先调用init_skyplatform_iam()函数进行初始化"
            )
        return self._config
    
    def get_middleware(self) -> 'AuthMiddleware':
        """
        获取中间件实例
        
        Returns:
            AuthMiddleware: 认证中间件实例
            
        Raises:
            IAMServiceError: 如果管理器未初始化
        """
        if not self._initialized or self._middleware is None:
            raise IAMServiceError(
                "GlobalIAMManager未初始化，请先调用init_skyplatform_iam()函数进行初始化"
            )
        return self._middleware
    
    def is_initialized(self) -> bool:
        """
        检查是否已初始化
        
        Returns:
            bool: 是否已初始化
        """
        return self._initialized
    
    async def get_current_user_info(self, request: Request) -> Optional[Dict[str, Any]]:
        """
        便捷方法：获取当前用户信息
        
        Args:
            request: FastAPI请求对象
            
        Returns:
            Optional[Dict]: 用户信息字典，如果未登录则返回None
            
        Raises:
            IAMServiceError: 如果管理器未初始化
        """
        if not self._initialized:
            raise IAMServiceError(
                "GlobalIAMManager未初始化，请先调用init_skyplatform_iam()函数进行初始化"
            )
        
        # 检查请求状态中是否已有用户信息（由中间件设置）
        if hasattr(request.state, 'user') and request.state.user:
            return request.state.user
        
        # 如果中间件没有设置用户信息，尝试手动验证
        try:
            from .middleware import AuthService
            auth_service = AuthService(self._config)
            return await auth_service.get_current_user(request)
        except Exception as e:
            logger.error(f"获取用户信息失败: {str(e)}")
            return None
    
    async def verify_permission(
        self, 
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
            IAMServiceError: 如果管理器未初始化
        """
        client = self.get_client()
        try:
            # 这里可以根据实际的IAM客户端API进行权限验证
            # 目前先返回True，具体实现需要根据ConnectAgenterraIam的API
            logger.info(f"验证权限: user_id={user_id}, permission={permission}, resource={resource}")
            return True
        except Exception as e:
            logger.error(f"权限验证失败: {str(e)}")
            return False
    
    def reset(self) -> None:
        """
        重置管理器状态（主要用于测试）
        """
        with self._init_lock:
            self._config = None
            self._iam_client = None
            self._middleware = None
            self._app = None
            self._initialized = False
            logger.info("GlobalIAMManager状态已重置")
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取管理器状态信息
        
        Returns:
            Dict: 状态信息
        """
        return {
            "initialized": self._initialized,
            "has_config": self._config is not None,
            "has_client": self._iam_client is not None,
            "has_middleware": self._middleware is not None,
            "has_app": self._app is not None,
            "server_name": self._config.server_name if self._config else None,
            "iam_host": self._config.agenterra_iam_host if self._config else None,
            "whitelist_paths_count": len(self._config.get_whitelist_paths()) if self._config else 0
        }


# 全局管理器实例
_global_manager = GlobalIAMManager()


def get_global_manager() -> GlobalIAMManager:
    """
    获取全局管理器实例
    
    Returns:
        GlobalIAMManager: 全局管理器实例
    """
    return _global_manager