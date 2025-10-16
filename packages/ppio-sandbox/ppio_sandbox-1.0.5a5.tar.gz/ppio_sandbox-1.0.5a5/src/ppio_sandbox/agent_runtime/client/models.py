"""
Agent Runtime Client 数据模型

定义客户端使用的数据模型
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SessionStatus(str, Enum):
    """会话状态"""
    ACTIVE = "active"      # 正在运行，可以处理请求
    PAUSED = "paused"      # 已暂停，保留状态但不处理请求
    INACTIVE = "inactive"  # 非活跃状态
    CLOSED = "closed"      # 已关闭，资源已释放
    ERROR = "error"        # 错误状态


class AgentTemplate(BaseModel):
    """Agent 模板信息"""
    template_id: str
    name: str
    version: str
    description: Optional[str] = None
    author: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    status: str
    
    # Agent 元信息（核心字段）
    metadata: Dict[str, Any] = Field(default_factory=dict)
    """
    Agent 元信息，包含完整的 AgentConfig 数据结构，与 CLI 工具的配置文件格式保持一致。
    
    典型结构示例（遵循 Kubernetes 风格的 YAML 配置格式）：
    {
      "agent": {
        "apiVersion": "v1",
        "kind": "Agent",
        "metadata": {
          "name": "string",              // Agent 名称
          "version": "string",           // Agent 版本
          "author": "string",            // 作者邮箱 (必填)
          "description": "string",       // Agent 描述
          "created": "string"            // 创建时间 (ISO 8601 格式)
        },
        "spec": {
          "entrypoint": "string",        // Python 入口文件，如 "agent.py" (必须是 .py 文件)
          "runtime": {
            "timeout": "number",         // 启动超时秒数，转换为 readyCmd 的超时参数 (1-3600)
            "memory_limit": "string",    // 内存限制，转换为 memoryMb (支持 "512Mi", "1Gi" 等格式)
            "cpu_limit": "string"        // CPU 限制，转换为 cpuCount (支持 "1", "1000m" 等格式)
          },
          "sandbox": {
            "template_id": "string"      // 部署后的模板ID
          }
        },
        // 状态字段 - 用于跟踪部署和构建状态 (由系统维护，用户不应手动修改)
        "status": {
          "phase": "string",            // 当前部署阶段
          "template_id": "string",      // 构建成功后的实际模板ID (用于后续更新)
          "last_deployed": "string",    // 最后部署时间
          "build_id": "string"          // 部署的唯一标识符
        }
      }
    }
    """
    
    # 扩展字段
    size: Optional[int] = None  # 模板大小（字节）
    build_time: Optional[float] = None  # 构建时间（秒）
    dependencies: List[str] = Field(default_factory=list)
    runtime_info: Optional[Dict[str, Any]] = None


class SandboxConfig(BaseModel):
    """Sandbox 配置"""
    timeout_seconds: int = 300
    memory_limit: Optional[str] = None  # 如 "512Mi", "1Gi"
    cpu_limit: Optional[str] = None     # 如 "500m", "1"
    env_vars: Dict[str, str] = Field(default_factory=dict)
    volumes: List[Dict[str, str]] = Field(default_factory=list)
    ports: List[int] = Field(default_factory=lambda: [8080])


class ClientConfig(BaseModel):
    """客户端配置"""
    base_url: Optional[str] = None
    timeout: int = 300
    max_retries: int = 3
    retry_delay: float = 1.0
    
    # 连接池配置
    max_connections: int = 100
    max_keepalive_connections: int = 20
    keepalive_expiry: float = 30.0


class InvocationRequest(BaseModel):
    """增强的调用请求模型"""
    # 基础字段
    prompt: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    sandbox_id: Optional[str] = None  # 可选，通常由系统自动填充
    
    # 控制字段
    timeout: Optional[int] = None
    stream: bool = False
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    
    # 元数据
    metadata: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    
    # 流式控制
    stream_options: Optional[Dict[str, Any]] = None
    
    # 向后兼容的属性
    @property
    def session_id(self) -> Optional[str]:
        """会话ID（等同于sandbox_id，向后兼容）"""
        return self.sandbox_id


class InvocationResponse(BaseModel):
    """增强的调用响应模型"""
    result: Any
    status: str = "success"
    duration: float
    
    # 元数据
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    error_type: Optional[str] = None
    
    # 性能信息
    processing_time: Optional[float] = None
    queue_time: Optional[float] = None
    
    # 使用统计
    tokens_used: Optional[int] = None
    cost: Optional[float] = None


class PingResponse(BaseModel):
    """健康检查响应模型"""
    status: str
    message: Optional[str] = None
    timestamp: Optional[str] = None
