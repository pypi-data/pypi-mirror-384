# PPIO Agent Runtime SDK - Exception Definitions
# Copyright (c) 2024 PPIO
# Licensed under the MIT License

"""Exception classes for PPIO Agent Runtime."""

from typing import Optional, Any, Dict


class PPIOAgentRuntimeError(Exception):
    """Base exception for all PPIO Agent Runtime errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.details = details or {}


class RuntimeConfigError(PPIOAgentRuntimeError):
    """Raised when there's a configuration error in the runtime."""
    pass


class RuntimeStartupError(PPIOAgentRuntimeError):
    """Raised when the runtime fails to start."""
    pass


class EntrypointNotFoundError(PPIOAgentRuntimeError):
    """Raised when the entrypoint function is not registered."""
    pass


class InvocationTimeoutError(PPIOAgentRuntimeError):
    """Raised when agent invocation times out."""
    pass


class InvocationError(PPIOAgentRuntimeError):
    """Raised when agent invocation fails."""
    pass


class ContextNotFoundError(PPIOAgentRuntimeError):
    """Raised when request context is not available."""
    pass


class MiddlewareError(PPIOAgentRuntimeError):
    """Raised when middleware execution fails."""
    pass


class ValidationError(PPIOAgentRuntimeError):
    """Raised when request validation fails."""
    pass
