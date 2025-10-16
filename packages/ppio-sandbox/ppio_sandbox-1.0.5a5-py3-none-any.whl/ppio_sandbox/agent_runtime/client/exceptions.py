"""
Agent Runtime Client 异常定义

定义客户端特定的异常类型，用于处理各种错误情况
"""

from typing import Optional


class AgentClientError(Exception):
    """客户端基础异常"""
    
    def __init__(self, message: str, error_code: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code


class AuthenticationError(AgentClientError):
    """认证错误"""
    pass


class TemplateNotFoundError(AgentClientError):
    """模板未找到错误"""
    pass


class SandboxCreationError(AgentClientError):
    """Sandbox 创建错误"""
    pass


class SessionNotFoundError(AgentClientError):
    """会话未找到错误"""
    pass


class InvocationError(AgentClientError):
    """调用错误"""
    pass


class NetworkError(AgentClientError):
    """网络错误"""
    pass


class RateLimitError(AgentClientError):
    """限流错误"""
    pass


class QuotaExceededError(AgentClientError):
    """配额超限错误"""
    pass


class SandboxOperationError(AgentClientError):
    """Sandbox 操作错误（暂停、恢复、重启等）"""
    pass