"""
测试数据和fixtures

提供标准化的测试数据、配置和工具函数。
"""

from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import json
import uuid

from ppio_sandbox.agent_runtime.runtime.models import (
    AgentConfig,
    AgentMetadata,
    AgentSpec,
    RuntimeSpec,
    RuntimeConfig,
    InvocationRequest,
    InvocationResponse,
    PingResponse,
    PingStatus,
)
from ppio_sandbox.agent_runtime.runtime.context import RequestContext


class TestDataFactory:
    """测试数据工厂"""
    
    @staticmethod
    def create_agent_metadata(
        name: str = "test-agent",
        version: str = "1.0.0",
        author: str = "test@example.com",
        description: Optional[str] = None,
        created: Optional[str] = None
    ) -> AgentMetadata:
        """创建 Agent 元数据"""
        return AgentMetadata(
            name=name,
            version=version,
            author=author,
            description=description or f"Test agent: {name}",
            created=created or datetime.now(timezone.utc).isoformat()
        )
    
    @staticmethod
    def create_runtime_config(
        host: str = "127.0.0.1",
        port: int = 8888,
        debug: bool = True,
        **kwargs
    ) -> RuntimeConfig:
        """创建运行时配置"""
        return RuntimeConfig(
            host=host,
            port=port,
            debug=debug,
            **kwargs
        )
    
    @staticmethod
    def create_invocation_request(
        prompt: Optional[str] = None,
        data: Optional[Dict] = None,
        sandbox_id: Optional[str] = None,
        **kwargs
    ) -> InvocationRequest:
        """创建调用请求"""
        return InvocationRequest(
            prompt=prompt or "Test prompt",
            data=data,
            sandbox_id=sandbox_id or f"sandbox-{uuid.uuid4().hex[:8]}",
            **kwargs
        )
    
    @staticmethod
    def create_request_context(
        sandbox_id: Optional[str] = None,
        request_id: Optional[str] = None,
        headers: Optional[Dict] = None
    ) -> RequestContext:
        """创建请求上下文"""
        return RequestContext(
            sandbox_id=sandbox_id or f"sandbox-{uuid.uuid4().hex[:8]}",
            request_id=request_id or f"req-{uuid.uuid4().hex[:8]}",
            headers=headers or {"Content-Type": "application/json"}
        )


class SampleData:
    """示例数据集合"""
    
    # 基础配置样本
    BASIC_RUNTIME_CONFIG = {
        "host": "127.0.0.1",
        "port": 8080,
        "debug": True,
        "timeout": 300,
        "max_request_size": 1024 * 1024,
        "cors_origins": ["*"],
        "enable_metrics": True,
        "enable_middleware": True
    }
    
    # 调用请求样本
    BASIC_INVOCATION_REQUEST = {
        "prompt": "Hello, how can you help me?",
        "data": {"user_id": "user123", "session": "sess456"},
        "sandbox_id": "sandbox-abc123",
        "timeout": 30,
        "stream": False,
        "metadata": {"source": "test", "priority": "normal"}
    }
    
    # 调用响应样本
    SUCCESS_RESPONSE = {
        "result": {
            "response": "I'm an AI assistant. I can help you with various tasks.",
            "confidence": 0.95,
        },
        "status": "success",
        "duration": 1.234,
        "metadata": {
            "model": "test-model-v1",
            "request_id": "req-abc123"
        }
    }
    
    ERROR_RESPONSE = {
        "result": None,
        "status": "error",
        "duration": 0.5,
        "error": "Invalid input format",
        "metadata": {
            "error_type": "ValidationError",
            "request_id": "req-error456"
        }
    }
    
    # Ping 响应样本
    HEALTHY_PING = {
        "status": "Healthy",
        "message": "All systems operational",
        "timestamp": "2024-01-01T12:00:00Z"
    }


class TestScenarios:
    """测试场景"""
    
    @staticmethod
    def get_performance_test_data(size: int = 1000) -> Dict:
        """获取性能测试数据"""
        return {
            "prompt": f"Process this large dataset with {size} items",
            "data": {
                "items": [{"id": i, "name": f"item_{i}"} for i in range(size)],
                "total_count": size,
            },
            "metadata": {
                "test_type": "performance",
                "data_size": size,
            }
        }
    
    @staticmethod
    def get_concurrent_test_requests(count: int = 10) -> List[Dict]:
        """获取并发测试请求"""
        requests = []
        for i in range(count):
            requests.append({
                "prompt": f"Concurrent request {i+1}",
                "data": {"request_id": i+1},
                "sandbox_id": f"sandbox-concurrent-{i+1}",
            })
        return requests


class ValidationHelpers:
    """验证辅助函数"""
    
    @staticmethod
    def validate_response_format(response: Dict, expected_keys: List[str] = None) -> bool:
        """验证响应格式"""
        if expected_keys is None:
            expected_keys = ["result", "status", "duration"]
        
        if not isinstance(response, dict):
            return False
        
        for key in expected_keys:
            if key not in response:
                return False
        
        return True
    
    @staticmethod
    def assert_response_structure(response: Dict, response_type: str = "invocation"):
        """断言响应结构正确"""
        if response_type == "invocation":
            assert "result" in response
            assert "status" in response
            assert "duration" in response
            assert response["status"] in ["success", "error"]
        
        elif response_type == "ping":
            assert "status" in response
            assert response["status"] in ["Healthy", "HealthyBusy"]


# 预定义的测试数据集
TEST_REQUESTS = {
    "basic": SampleData.BASIC_INVOCATION_REQUEST,
}

TEST_RESPONSES = {
    "success": SampleData.SUCCESS_RESPONSE,
    "error": SampleData.ERROR_RESPONSE,
}

TEST_PING_RESPONSES = {
    "healthy": SampleData.HEALTHY_PING,
}