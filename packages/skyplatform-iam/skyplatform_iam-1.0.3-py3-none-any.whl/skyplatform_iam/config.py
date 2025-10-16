"""
SkyPlatform IAM SDK 配置模块
"""
import os
import fnmatch
from typing import Optional, List
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class AuthConfig(BaseModel):
    """
    认证配置类
    支持环境变量和代码配置
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

    class Config:
        env_prefix = "AGENTERRA_"

    @classmethod
    def from_env(cls) -> "AuthConfig":
        """
        从环境变量创建配置
        """
        return cls(
            agenterra_iam_host=os.environ.get('AGENTERRA_IAM_HOST', ''),
            server_name=os.environ.get('AGENTERRA_SERVER_NAME', ''),
            access_key=os.environ.get('AGENTERRA_ACCESS_KEY', ''),
            enable_debug=os.environ.get('AGENTERRA_ENABLE_DEBUG', 'false').lower() == 'true',
            whitelist_paths=[]  # 初始化空的白名单路径列表
        )

    def validate_config(self) -> bool:
        """
        验证配置是否完整
        """
        required_fields = ['agenterra_iam_host', 'server_name', 'access_key']
        for field in required_fields:
            if not getattr(self, field):
                raise ValueError(f"配置项 {field} 不能为空")
        return True

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
