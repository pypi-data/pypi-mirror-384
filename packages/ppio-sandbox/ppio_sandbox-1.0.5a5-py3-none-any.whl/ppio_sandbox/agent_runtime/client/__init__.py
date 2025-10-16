"""
PPIO Agent Runtime Client 模块

提供 AI Agent 的客户端调用功能，面向后端开发者
"""

# 主要客户端类
from .client import AgentRuntimeClient

# 会话管理
from .session import SandboxSession

# 认证和模板管理
from .auth import AuthManager
from .template import TemplateManager

# 数据模型
from .models import (
    AgentTemplate,
    ClientConfig,
    InvocationRequest,
    InvocationResponse,
    PingResponse,
    SandboxConfig,
    SessionStatus,
)

# 异常类
from .exceptions import (
    AgentClientError,
    AuthenticationError,
    InvocationError,
    NetworkError,
    QuotaExceededError,
    RateLimitError,
    SandboxCreationError,
    SandboxOperationError,
    SessionNotFoundError,
    TemplateNotFoundError,
)

__version__ = "1.0.0"

__all__ = [
    # 核心客户端类
    "AgentRuntimeClient",
    "SandboxSession",
    "AuthManager", 
    "TemplateManager",
    
    # 数据模型
    "AgentTemplate",
    "ClientConfig",
    "InvocationRequest",
    "InvocationResponse",
    "PingResponse",
    "SandboxConfig",
    "SessionStatus",
    
    # 异常类
    "AgentClientError",
    "AuthenticationError",
    "InvocationError",
    "NetworkError",
    "QuotaExceededError",
    "RateLimitError",
    "SandboxCreationError",
    "SandboxOperationError",
    "SessionNotFoundError",
    "TemplateNotFoundError",
]