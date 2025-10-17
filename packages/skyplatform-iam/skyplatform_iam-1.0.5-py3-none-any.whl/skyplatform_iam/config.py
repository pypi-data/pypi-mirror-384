"""
SkyPlatform IAM SDK 配置模块
"""
import os
import fnmatch
import logging
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

logger = logging.getLogger(__name__)


class AuthConfig(BaseModel):
    """
    认证配置类
    支持环境变量和代码配置，增强配置验证和管理功能
    """
    # IAM服务配置
    agenterra_iam_host: str
    server_name: str
    access_key: str

    # Token配置
    token_header: str = "Authorization"
    token_prefix: str = "Bearer "

    # 错误处理配置
    enable_debug: bool = False

    # 白名单路径配置（实例变量）
    whitelist_paths: List[str] = Field(default_factory=list)
    
    # 连接配置
    timeout: int = 30
    max_retries: int = 3
    
    # 缓存配置
    enable_cache: bool = True
    cache_ttl: int = 300  # 5分钟

    class Config:
        env_prefix = "SKYPLATFORM_"
        validate_assignment = True

    @validator('agenterra_iam_host')
    def validate_iam_host(cls, v):
        """验证IAM主机地址"""
        if not v:
            raise ValueError("agenterra_iam_host不能为空")
        if not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError("agenterra_iam_host必须以http://或https://开头")
        return v.rstrip('/')  # 移除末尾的斜杠

    @validator('server_name')
    def validate_server_name(cls, v):
        """验证服务名称"""
        if not v or not v.strip():
            raise ValueError("server_name不能为空")
        return v.strip()

    @validator('access_key')
    def validate_access_key(cls, v):
        """验证访问密钥"""
        if not v or not v.strip():
            raise ValueError("access_key不能为空")
        if len(v.strip()) < 8:
            raise ValueError("access_key长度不能少于8个字符")
        return v.strip()

    @validator('timeout')
    def validate_timeout(cls, v):
        """验证超时时间"""
        if v <= 0:
            raise ValueError("timeout必须大于0")
        return v

    @validator('max_retries')
    def validate_max_retries(cls, v):
        """验证最大重试次数"""
        if v < 0:
            raise ValueError("max_retries不能小于0")
        return v

    @validator('cache_ttl')
    def validate_cache_ttl(cls, v):
        """验证缓存TTL"""
        if v <= 0:
            raise ValueError("cache_ttl必须大于0")
        return v

    @classmethod
    def from_env(cls, prefix: str = "SKYPLATFORM_") -> "AuthConfig":
        """
        从环境变量创建配置
        
        Args:
            prefix: 环境变量前缀，默认为SKYPLATFORM_
            
        Returns:
            AuthConfig: 配置实例
            
        Raises:
            ValueError: 配置验证失败
        """
        logger.info(f"从环境变量加载配置，前缀: {prefix}")
        
        # 支持多种环境变量前缀（向后兼容）
        def get_env_value(key: str, default: str = '') -> str:
            # 优先使用新前缀
            value = os.environ.get(f"{prefix}{key}", '')
            if not value:
                # 回退到旧前缀
                value = os.environ.get(f"AGENTERRA_{key}", default)
            return value
        
        # 解析白名单路径
        whitelist_paths_str = get_env_value('WHITELIST_PATHS', '')
        whitelist_paths = []
        if whitelist_paths_str:
            whitelist_paths = [path.strip() for path in whitelist_paths_str.split(',') if path.strip()]
        
        config = cls(
            agenterra_iam_host=get_env_value('IAM_HOST'),
            server_name=get_env_value('SERVER_NAME'),
            access_key=get_env_value('ACCESS_KEY'),
            enable_debug=get_env_value('ENABLE_DEBUG', 'false').lower() == 'true',
            whitelist_paths=whitelist_paths,
            timeout=int(get_env_value('TIMEOUT', '30')),
            max_retries=int(get_env_value('MAX_RETRIES', '3')),
            enable_cache=get_env_value('ENABLE_CACHE', 'true').lower() == 'true',
            cache_ttl=int(get_env_value('CACHE_TTL', '300'))
        )
        
        logger.info(f"配置加载完成: server_name={config.server_name}, "
                   f"iam_host={config.agenterra_iam_host}, "
                   f"whitelist_paths_count={len(config.whitelist_paths)}")
        
        return config

    def validate_config(self) -> None:
        """
        验证配置完整性
        
        Raises:
            ValueError: 配置验证失败
        """
        logger.debug("开始验证配置完整性")
        
        # Pydantic会自动调用validator，这里只需要检查业务逻辑
        if not self.agenterra_iam_host:
            raise ValueError("agenterra_iam_host不能为空")
        if not self.server_name:
            raise ValueError("server_name不能为空")
        if not self.access_key:
            raise ValueError("access_key不能为空")
            
        logger.info("配置验证通过")

    def merge_config(self, other: "AuthConfig") -> "AuthConfig":
        """
        合并配置，other的非空值会覆盖当前配置
        
        Args:
            other: 要合并的配置
            
        Returns:
            AuthConfig: 合并后的新配置实例
        """
        logger.debug("开始合并配置")
        
        # 获取当前配置的字典表示
        current_dict = self.dict()
        other_dict = other.dict()
        
        # 合并配置
        merged_dict = current_dict.copy()
        for key, value in other_dict.items():
            if key == 'whitelist_paths':
                # 白名单路径需要合并而不是覆盖
                merged_paths = list(set(current_dict[key] + value))
                merged_dict[key] = merged_paths
            elif value:  # 只有非空值才覆盖
                merged_dict[key] = value
        
        logger.debug(f"配置合并完成，合并后的配置: {merged_dict}")
        return AuthConfig(**merged_dict)

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式
        
        Returns:
            Dict: 配置字典
        """
        return self.dict()

    def copy_with_updates(self, **updates) -> "AuthConfig":
        """
        创建配置副本并更新指定字段
        
        Args:
            **updates: 要更新的字段
            
        Returns:
            AuthConfig: 更新后的配置副本
        """
        config_dict = self.dict()
        config_dict.update(updates)
        return AuthConfig(**config_dict)

    def _normalize_path(self, path: str) -> str:
        """
        标准化路径格式
        """
        if not path:
            return path
        
        # 确保路径以 / 开头
        if not path.startswith('/'):
            path = '/' + path
        
        # 移除重复的斜杠
        while '//' in path:
            path = path.replace('//', '/')
        
        return path

    def add_whitelist_path(self, path: str) -> None:
        """
        添加白名单路径
        """
        if not path:
            return
        
        normalized_path = self._normalize_path(path)
        if normalized_path not in self.whitelist_paths:
            self.whitelist_paths.append(normalized_path)

    def add_whitelist_paths(self, paths: List[str]) -> None:
        """
        批量添加白名单路径
        """
        for path in paths:
            self.add_whitelist_path(path)

    def remove_whitelist_path(self, path: str) -> None:
        """
        移除白名单路径
        """
        if not path:
            return
        
        normalized_path = self._normalize_path(path)
        if normalized_path in self.whitelist_paths:
            self.whitelist_paths.remove(normalized_path)

    def clear_whitelist_paths(self) -> None:
        """
        清空所有白名单路径
        """
        self.whitelist_paths.clear()

    def get_whitelist_paths(self) -> List[str]:
        """
        获取所有白名单路径
        """
        return self.whitelist_paths.copy()

    def is_path_whitelisted(self, path: str) -> bool:
        """
        检查路径是否在白名单中（支持通配符匹配）
        """
        if not path:
            return False
        
        normalized_path = self._normalize_path(path)
        
        for whitelist_path in self.whitelist_paths:
            # 支持通配符匹配
            if fnmatch.fnmatch(normalized_path, whitelist_path):
                return True
        
        return False
