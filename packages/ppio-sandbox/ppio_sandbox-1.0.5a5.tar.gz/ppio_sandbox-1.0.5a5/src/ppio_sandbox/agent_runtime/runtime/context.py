# PPIO Agent Runtime - Request Context Management
# Copyright (c) 2024 PPIO
# Licensed under the MIT License

"""Request context management for PPIO Agent Runtime."""

import uuid
from typing import Any, Dict, Optional
from contextvars import ContextVar
from pydantic import BaseModel, Field


class RequestContext(BaseModel):
    """请求上下文模型"""
    
    sandbox_id: Optional[str] = None
    request_id: Optional[str] = None
    headers: Dict[str, str] = Field(default_factory=dict)
    
    # 向后兼容的属性
    @property
    def session_id(self) -> Optional[str]:
        """会话ID（等同于sandbox_id，向后兼容）"""
        return self.sandbox_id
    
    class Config:
        extra = "allow"


class AgentRuntimeContext:
    """运行时上下文管理器"""
    
    _context_var: ContextVar[Optional[RequestContext]] = ContextVar(
        "agent_runtime_context", default=None
    )
    
    @classmethod
    def get_current_context(cls) -> Optional[RequestContext]:
        """获取当前请求上下文"""
        return cls._context_var.get()
    
    @classmethod
    def set_current_context(cls, context: RequestContext) -> None:
        """设置当前请求上下文"""
        cls._context_var.set(context)
    
    @classmethod
    def clear_current_context(cls) -> None:
        """清除当前请求上下文"""
        cls._context_var.set(None)
