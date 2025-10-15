"""
SkyPlatform IAM SDK 配置模块
"""
import os
from typing import Optional, List
from pydantic import BaseModel
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
            enable_debug=os.environ.get('AGENTERRA_ENABLE_DEBUG', 'false').lower() == 'true'
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
    
    def add_whitelist_path(self, path: str) -> None:
        """
        添加白名单路径
        """
        if path not in self.whitelist_paths:
            self.whitelist_paths.append(path)
    
    def remove_whitelist_path(self, path: str) -> None:
        """
        移除白名单路径
        """
        if path in self.whitelist_paths:
            self.whitelist_paths.remove(path)