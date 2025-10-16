"""
数据模型单元测试

测试 Pydantic 数据模型的验证、序列化和反序列化功能。
"""

import pytest
from datetime import datetime
from typing import Dict, Any
from pydantic import ValidationError

from ppio_sandbox.agent_runtime.runtime.models import (
    AgentConfig,
    AgentMetadata,
    AgentSpec,
    AgentStatus,
    RuntimeSpec,
    SandboxSpec,
    RuntimeConfig,
    DeploymentPhase,
    InvocationRequest,
    InvocationResponse,
    PingResponse,
    PingStatus,
)


class TestAgentMetadata:
    """AgentMetadata 模型测试"""
    
    @pytest.mark.unit
    def test_valid_metadata_creation(self):
        """测试有效的元数据创建"""
        metadata = AgentMetadata(
            name="test-agent",
            version="1.0.0",
            author="test@example.com",
            description="Test agent",
            created="2024-01-01T00:00:00Z"
        )
        
        assert metadata.name == "test-agent"
        assert metadata.version == "1.0.0"
        assert metadata.author == "test@example.com"
        assert metadata.description == "Test agent"
        assert metadata.created == "2024-01-01T00:00:00Z"
    
    @pytest.mark.unit
    def test_minimal_metadata(self):
        """测试最小元数据（只有必填字段）"""
        metadata = AgentMetadata(
            name="minimal-agent",
            version="1.0.0",
            author="minimal@example.com"
        )
        
        assert metadata.name == "minimal-agent"
        assert metadata.version == "1.0.0"
        assert metadata.author == "minimal@example.com"
        assert metadata.description is None
        assert metadata.created is None
    
    @pytest.mark.unit
    def test_missing_required_fields(self):
        """测试缺少必填字段"""
        with pytest.raises(ValidationError):
            AgentMetadata(version="1.0.0")  # 缺少 name 和 author


class TestRuntimeSpec:
    """RuntimeSpec 模型测试"""
    
    @pytest.mark.unit
    def test_valid_runtime_spec(self):
        """测试有效的运行时规格"""
        spec = RuntimeSpec(
            timeout=300,
            memory_limit="1Gi",
            cpu_limit="1"
        )
        
        assert spec.timeout == 300
        assert spec.memory_limit == "1Gi"
        assert spec.cpu_limit == "1"
    
    @pytest.mark.unit
    def test_timeout_validation(self):
        """测试超时时间验证"""
        # 有效的超时时间
        RuntimeSpec(timeout=1)  # 最小值
        RuntimeSpec(timeout=3600)  # 最大值
        RuntimeSpec(timeout=300)  # 中间值
        
        # 无效的超时时间
        with pytest.raises(ValidationError):
            RuntimeSpec(timeout=0)  # 小于最小值
        
        with pytest.raises(ValidationError):
            RuntimeSpec(timeout=3601)  # 大于最大值
    
    @pytest.mark.unit
    def test_optional_fields(self):
        """测试可选字段"""
        spec = RuntimeSpec()
        
        assert spec.timeout is None
        assert spec.memory_limit is None
        assert spec.cpu_limit is None


class TestAgentSpec:
    """AgentSpec 模型测试"""
    
    @pytest.mark.unit
    def test_valid_agent_spec(self):
        """测试有效的 Agent 规格"""
        spec = AgentSpec(
            entrypoint="agent.py",
            runtime=RuntimeSpec(timeout=300),
            sandbox=SandboxSpec(template_id="tmpl_123")
        )
        
        assert spec.entrypoint == "agent.py"
        assert spec.runtime.timeout == 300
        assert spec.sandbox.template_id == "tmpl_123"
    
    @pytest.mark.unit
    def test_entrypoint_validation(self):
        """测试入口点文件验证"""
        # 有效的 Python 文件
        AgentSpec(entrypoint="agent.py")
        AgentSpec(entrypoint="my_agent.py")
        AgentSpec(entrypoint="path/to/agent.py")
        
        # 无效的文件扩展名
        with pytest.raises(ValidationError):
            AgentSpec(entrypoint="agent.js")
        
        with pytest.raises(ValidationError):
            AgentSpec(entrypoint="agent")
        
        with pytest.raises(ValidationError):
            AgentSpec(entrypoint="agent.txt")


class TestAgentConfig:
    """AgentConfig 模型测试"""
    
    @pytest.mark.unit
    def test_complete_agent_config(self):
        """测试完整的 Agent 配置"""
        config = AgentConfig(
            apiVersion="v1",
            kind="Agent",
            metadata=AgentMetadata(
                name="test-agent",
                version="1.0.0",
                author="test@example.com",
                description="Test Agent"
            ),
            spec=AgentSpec(
                entrypoint="agent.py",
                runtime=RuntimeSpec(
                    timeout=300,
                    memory_limit="1Gi",
                    cpu_limit="1"
                ),
                sandbox=SandboxSpec(template_id="tmpl_123")
            ),
            status=AgentStatus(
                phase=DeploymentPhase.DEPLOYED,
                template_id="tmpl_123",
                last_deployed="2024-01-01T00:00:00Z"
            )
        )
        
        assert config.apiVersion == "v1"
        assert config.kind == "Agent"
        assert config.metadata.name == "test-agent"
        assert config.spec.entrypoint == "agent.py"
        assert config.status.phase == DeploymentPhase.DEPLOYED
    
    @pytest.mark.unit
    def test_minimal_agent_config(self):
        """测试最小 Agent 配置"""
        config = AgentConfig(
            metadata=AgentMetadata(
                name="minimal-agent",
                version="1.0.0",
                author="minimal@example.com"
            ),
            spec=AgentSpec(entrypoint="agent.py")
        )
        
        assert config.apiVersion == "v1"  # 默认值
        assert config.kind == "Agent"  # 默认值
        assert config.status is None  # 可选


class TestRuntimeConfig:
    """RuntimeConfig 模型测试"""
    
    @pytest.mark.unit
    def test_default_runtime_config(self):
        """测试默认运行时配置"""
        config = RuntimeConfig()
        
        assert config.host == "0.0.0.0"
        assert config.port == 8080
        assert config.debug is False
        assert config.timeout == 300
        assert config.max_request_size == 1024 * 1024
        assert config.cors_origins == ["*"]
        assert config.enable_metrics is True
        assert config.enable_middleware is True


class TestInvocationRequest:
    """InvocationRequest 模型测试"""
    
    @pytest.mark.unit
    def test_basic_invocation_request(self):
        """测试基础调用请求"""
        request = InvocationRequest(
            prompt="Test prompt",
            data={"key": "value"},
            sandbox_id="sandbox-123",
            timeout=30,
            stream=False,
            metadata={"test": True}
        )
        
        assert request.prompt == "Test prompt"
        assert request.data == {"key": "value"}
        assert request.sandbox_id == "sandbox-123"
        assert request.timeout == 30
        assert request.stream is False
        assert request.metadata == {"test": True}
    
    @pytest.mark.unit
    def test_backward_compatibility(self):
        """测试向后兼容性"""
        request = InvocationRequest(sandbox_id="sandbox-123")
        
        # 测试 session_id 属性（向后兼容）
        assert request.session_id == "sandbox-123"
        assert request.session_id == request.sandbox_id


class TestInvocationResponse:
    """InvocationResponse 模型测试"""
    
    @pytest.mark.unit
    def test_successful_response(self):
        """测试成功响应"""
        response = InvocationResponse(
            result={"output": "test result"},
            status="success",
            duration=1.5,
            metadata={"processed": True}
        )
        
        assert response.result == {"output": "test result"}
        assert response.status == "success"
        assert response.duration == 1.5
        assert response.metadata == {"processed": True}
        assert response.error is None


class TestPingResponse:
    """PingResponse 模型测试"""
    
    @pytest.mark.unit
    def test_healthy_ping_response(self):
        """测试健康的 Ping 响应"""
        response = PingResponse(
            status=PingStatus.HEALTHY,
            message="All systems operational",
            timestamp="2024-01-01T00:00:00Z"
        )
        
        assert response.status == PingStatus.HEALTHY
        assert response.message == "All systems operational"
        assert response.timestamp == "2024-01-01T00:00:00Z"
    
    @pytest.mark.unit
    def test_default_ping_response(self):
        """测试默认 Ping 响应"""
        response = PingResponse()
        
        assert response.status == PingStatus.HEALTHY
        assert response.message is None
        assert response.timestamp is None


class TestModelSerialization:
    """模型序列化测试"""
    
    @pytest.mark.unit
    def test_agent_config_serialization(self):
        """测试 AgentConfig 序列化"""
        config = AgentConfig(
            metadata=AgentMetadata(
                name="test-agent",
                version="1.0.0",
                author="test@example.com"
            ),
            spec=AgentSpec(entrypoint="agent.py")
        )
        
        # 序列化为字典
        config_dict = config.dict()
        assert isinstance(config_dict, dict)
        assert config_dict["apiVersion"] == "v1"
        assert config_dict["kind"] == "Agent"
        assert config_dict["metadata"]["name"] == "test-agent"
        
        # 从字典反序列化
        new_config = AgentConfig(**config_dict)
        assert new_config.metadata.name == config.metadata.name
        assert new_config.spec.entrypoint == config.spec.entrypoint
    
    @pytest.mark.unit
    def test_json_serialization(self):
        """测试 JSON 序列化"""
        request = InvocationRequest(
            prompt="Test",
            data={"key": "value"},
            stream=True
        )
        
        # 测试 JSON 序列化
        json_str = request.json()
        assert isinstance(json_str, str)
        assert "Test" in json_str
        assert "true" in json_str.lower()  # stream: true
        
        # 测试从 JSON 反序列化
        parsed = InvocationRequest.parse_raw(json_str)
        assert parsed.prompt == request.prompt
        assert parsed.data == request.data
        assert parsed.stream == request.stream