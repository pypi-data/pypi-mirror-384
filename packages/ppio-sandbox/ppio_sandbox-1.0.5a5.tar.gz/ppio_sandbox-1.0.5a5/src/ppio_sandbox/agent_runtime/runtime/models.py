# PPIO Agent Runtime - Data Models
# Copyright (c) 2024 PPIO
# Licensed under the MIT License

"""Data models for PPIO Agent Runtime."""

import json
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Literal, Union
from pydantic import BaseModel, Field


class DeploymentPhase(str, Enum):
    """部署阶段枚举"""
    PENDING = "pending"
    BUILDING = "building" 
    DEPLOYED = "deployed"
    FAILED = "failed"


class PingStatus(str, Enum):
    """健康状态枚举"""
    HEALTHY = "Healthy"
    HEALTHY_BUSY = "HealthyBusy"


class AgentMetadata(BaseModel):
    """Agent 元数据"""
    name: str = Field(..., description="Agent名称，必须小写字母数字和连字符")
    version: str = Field(..., description="Agent版本") 
    author: str = Field(..., description="作者邮箱（必填）")
    description: Optional[str] = Field(None, description="Agent描述")
    created: Optional[str] = Field(None, description="创建时间（ISO 8601格式）")


class RuntimeSpec(BaseModel):
    """运行时规格配置"""
    timeout: Optional[int] = Field(None, ge=1, le=3600, description="启动超时秒数（1-3600）")
    memory_limit: Optional[str] = Field(None, description="内存限制，如'512Mi','1Gi'")
    cpu_limit: Optional[str] = Field(None, description="CPU限制，如'1','1000m'")


class SandboxSpec(BaseModel):
    """Sandbox 规格配置"""
    template_id: Optional[str] = Field(None, description="部署后的模板ID")


class AgentSpec(BaseModel):
    """Agent 规格配置"""
    entrypoint: str = Field(..., pattern=r".*\.py$", description="Python入口文件，必须是.py文件")
    runtime: Optional[RuntimeSpec] = Field(None, description="运行时配置")
    sandbox: Optional[SandboxSpec] = Field(None, description="Sandbox配置")


class AgentStatus(BaseModel):
    """Agent 状态信息（由系统维护）"""
    phase: Optional[DeploymentPhase] = Field(None, description="当前部署阶段")
    template_id: Optional[str] = Field(None, description="构建成功后的实际模板ID")
    last_deployed: Optional[str] = Field(None, description="最后部署时间")
    build_id: Optional[str] = Field(None, description="部署的唯一标识符")


class AgentConfig(BaseModel):
    """Agent 配置类 - Kubernetes 风格的配置结构"""
    apiVersion: Literal["v1"] = Field("v1", description="API版本")
    kind: Literal["Agent"] = Field("Agent", description="资源类型")
    metadata: AgentMetadata = Field(..., description="Agent元数据")
    spec: AgentSpec = Field(..., description="Agent规格配置")
    status: Optional[AgentStatus] = Field(None, description="Agent状态信息（由系统维护）")


class RuntimeConfig(BaseModel):
    """运行时配置类 - 用于Agent Runtime服务器配置"""
    host: str = "0.0.0.0"
    port: int = 8080
    debug: bool = False
    timeout: int = 300
    max_request_size: int = 1024 * 1024  # 1MB
    cors_origins: List[str] = Field(default_factory=lambda: ["*"])
    enable_metrics: bool = True
    enable_middleware: bool = True


class InvocationRequest(BaseModel):
    """调用请求模型"""
    prompt: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    sandbox_id: Optional[str] = None  # 可选，通常由系统自动填充
    timeout: Optional[int] = None
    stream: bool = False
    metadata: Optional[Dict[str, Any]] = None
    
    # 向后兼容的属性
    @property
    def session_id(self) -> Optional[str]:
        """会话ID（等同于sandbox_id，向后兼容）"""
        return self.sandbox_id


class InvocationResponse(BaseModel):
    """调用响应模型"""
    result: Any
    status: str = "success"
    duration: float
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class PingResponse(BaseModel):
    """健康检查响应模型"""
    status: PingStatus = PingStatus.HEALTHY
    message: Optional[str] = None
    timestamp: Optional[str] = None
