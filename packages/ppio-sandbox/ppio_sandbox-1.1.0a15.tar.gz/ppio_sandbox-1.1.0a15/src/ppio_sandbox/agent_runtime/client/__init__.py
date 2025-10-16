"""
PPIO Agent Runtime Client Module

Provides client functionality for AI Agents, targeted at backend developers
"""

# Main client class
from .client import AgentRuntimeClient

# Session management
from .session import SandboxSession

# Authentication and template management
from .auth import AuthManager
from .template import TemplateManager

# Data models
from .models import (
    AgentTemplate,
    ClientConfig,
    InvocationRequest,
    InvocationResponse,
    RuntimeConfig,  # New AWS-compatible name
    SandboxConfig,  # Backward compatibility alias
    SessionStatus,
    # PingResponse imported from runtime module
    PingResponse,
    PingStatus,
    # AWS Agentcore compatible models
    AgentRuntimeRequest,
    AgentRuntimeResponse,
    StreamingChunk,
    MultimodalContent,
    ErrorResponse,
    ValidationError
)

# Exception classes
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
    # AWS Agentcore compatible exceptions
    ValidationException,
    ResourceNotFoundException,
    AccessDeniedException,
    ThrottlingException,
    InternalServerError,
    ServiceUnavailableException,
    ConflictException
)

__version__ = "1.0.0"

__all__ = [
    # Core client classes
    "AgentRuntimeClient",
    "SandboxSession",
    "AuthManager", 
    "TemplateManager",
    
    # Data models
    "AgentTemplate",
    "ClientConfig",
    "InvocationRequest",
    "InvocationResponse",
    "PingResponse",
    "PingStatus",
    "RuntimeConfig",  # New AWS-compatible name
    "SandboxConfig",  # Backward compatibility
    "SessionStatus",
    # AWS Agentcore compatible models
    "AgentRuntimeRequest",
    "AgentRuntimeResponse",
    "StreamingChunk",
    "MultimodalContent",
    "ErrorResponse",
    "ValidationError",
    
    # Exception classes
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
    # AWS Agentcore compatible exceptions
    "ValidationException",
    "ResourceNotFoundException",
    "AccessDeniedException",
    "ThrottlingException",
    "InternalServerError",
    "ServiceUnavailableException",
    "ConflictException",
]