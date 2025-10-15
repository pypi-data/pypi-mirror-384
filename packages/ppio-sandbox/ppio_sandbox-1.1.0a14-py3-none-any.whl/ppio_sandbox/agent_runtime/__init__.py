# PPIO Agent Runtime SDK
# Copyright (c) 2024 PPIO
# Licensed under the MIT License

"""
PPIO Agent Runtime SDK

This SDK provides a lightweight AI agent runtime framework designed for the PPIO Agent Sandbox ecosystem.
It consists of two core modules:

1. Agent Runtime Module: For AI Agent developers to wrap Agent logic as standard HTTP services
2. Agent Client Module: For backend developers to call Agents deployed in Sandbox
"""

# Runtime module exports
from .exceptions import (
    PPIOAgentRuntimeError,
    RuntimeConfigError,
    RuntimeStartupError,
    InvocationTimeoutError,
    ContextNotFoundError,
)

from .runtime import (
    AgentRuntimeApp,
    RequestContext,
    AgentConfig,
    InvocationRequest,
    InvocationResponse,
    PingResponse,
    PingStatus,
)

# Client module exports
from .client import (
    AgentRuntimeClient,
    SandboxSession,
    SessionStatus,
    AuthManager,
    TemplateManager,
    AgentClientError,
    AuthenticationError,
    TemplateNotFoundError,
    SandboxCreationError,
    SessionNotFoundError,
)

__version__ = "1.0.0"

__all__ = [
    # Core runtime classes
    "AgentRuntimeApp",
    "RequestContext", 
    "AgentConfig",
    
    # Data models
    "InvocationRequest",
    "InvocationResponse", 
    "PingResponse",
    "PingStatus",
    
    # Client classes
    "AgentRuntimeClient",
    "SandboxSession",
    "SessionStatus",
    "AuthManager",
    "TemplateManager",
    
    # Runtime exceptions
    "PPIOAgentRuntimeError",
    "RuntimeConfigError",
    "RuntimeStartupError",
    "InvocationTimeoutError",
    "ContextNotFoundError",
    
    # Client exceptions
    "AgentClientError",
    "AuthenticationError",
    "TemplateNotFoundError",
    "SandboxCreationError",
    "SessionNotFoundError",
]
