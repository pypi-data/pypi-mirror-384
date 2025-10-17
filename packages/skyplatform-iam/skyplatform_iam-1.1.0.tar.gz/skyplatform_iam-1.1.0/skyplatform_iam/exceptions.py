"""
SkyPlatform IAM SDK 异常模块
"""
from typing import Optional


class SkyPlatformAuthException(Exception):
    """
    SkyPlatform认证SDK基础异常类
    """
    def __init__(self, message: str, status_code: int = 500, detail: Optional[str] = None):
        self.message = message
        self.status_code = status_code
        self.detail = detail
        super().__init__(self.message)


class AuthenticationError(SkyPlatformAuthException):
    """
    认证失败异常
    """
    def __init__(self, message: str = "认证失败", detail: Optional[str] = None):
        super().__init__(message, status_code=401, detail=detail)


class AuthorizationError(SkyPlatformAuthException):
    """
    授权失败异常
    """
    def __init__(self, message: str = "权限不足", detail: Optional[str] = None):
        super().__init__(message, status_code=403, detail=detail)


class TokenExpiredError(AuthenticationError):
    """
    Token过期异常
    """
    def __init__(self, message: str = "Token已过期", detail: Optional[str] = None):
        super().__init__(message, detail=detail)


class TokenInvalidError(AuthenticationError):
    """
    Token无效异常
    """
    def __init__(self, message: str = "Token无效", detail: Optional[str] = None):
        super().__init__(message, detail=detail)


class ConfigurationError(SkyPlatformAuthException):
    """
    配置错误异常
    """
    def __init__(self, message: str = "配置错误", detail: Optional[str] = None):
        super().__init__(message, status_code=500, detail=detail)


class IAMServiceError(SkyPlatformAuthException):
    """
    IAM服务错误异常
    """
    def __init__(self, message: str = "IAM服务错误", status_code: int = 500, detail: Optional[str] = None):
        super().__init__(message, status_code=status_code, detail=detail)


class NetworkError(SkyPlatformAuthException):
    """
    网络错误异常
    """
    def __init__(self, message: str = "网络连接错误", detail: Optional[str] = None):
        super().__init__(message, status_code=503, detail=detail)