"""
AgentRuntimeServer 单元测试

测试 AgentRuntimeServer 类的HTTP服务器功能，包括路由、中间件、请求处理等。
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch
from typing import Generator, AsyncGenerator

from starlette.applications import Starlette
from starlette.testclient import TestClient

from ppio_sandbox.agent_runtime.runtime.server import AgentRuntimeServer
from ppio_sandbox.agent_runtime.runtime.context import RequestContext, AgentRuntimeContext
from ppio_sandbox.agent_runtime.runtime.models import RuntimeConfig


class TestAgentRuntimeServerInitialization:
    """AgentRuntimeServer 初始化测试"""
    
    @pytest.mark.unit
    def test_default_initialization(self):
        """测试默认初始化"""
        config = RuntimeConfig()
        server = AgentRuntimeServer(config)
        
        assert server.config == config
        assert server._entrypoint_func is None
        assert server._ping_func is None
        assert server._middlewares == []
        assert server._app is not None
        assert isinstance(server._app, Starlette)
    
    @pytest.mark.unit
    def test_custom_config_initialization(self):
        """测试自定义配置初始化"""
        config = RuntimeConfig(
            host="127.0.0.1",
            port=9000,
            debug=True,
            max_request_size=2 * 1024 * 1024
        )
        
        server = AgentRuntimeServer(config)
        
        assert server.config.host == "127.0.0.1"
        assert server.config.port == 9000
        assert server.config.debug is True
        assert server.config.max_request_size == 2 * 1024 * 1024


class TestAgentRuntimeServerHandlerManagement:
    """AgentRuntimeServer 处理器管理测试"""
    
    @pytest.mark.unit
    def test_set_entrypoint_handler(self):
        """测试设置入口点处理器"""
        config = RuntimeConfig()
        server = AgentRuntimeServer(config)
        
        def test_agent(request: dict) -> dict:
            return {"response": "test", "input": request}
        
        server.set_entrypoint_handler(test_agent)
        
        assert server._entrypoint_func is test_agent
    
    @pytest.mark.unit
    def test_set_ping_handler(self):
        """测试设置 ping 处理器"""
        config = RuntimeConfig()
        server = AgentRuntimeServer(config)
        
        def test_ping() -> dict:
            return {"status": "healthy", "service": "test"}
        
        server.set_ping_handler(test_ping)
        
        assert server._ping_func is test_ping
    
    @pytest.mark.unit
    def test_add_middleware(self):
        """测试添加中间件"""
        config = RuntimeConfig()
        server = AgentRuntimeServer(config)
        
        async def test_middleware(request, call_next):
            response = await call_next(request)
            return response
        
        server.add_middleware(test_middleware)
        
        assert len(server._middlewares) == 1
        assert server._middlewares[0] is test_middleware


class TestAgentRuntimeServerRoutes:
    """AgentRuntimeServer 路由测试"""
    
    @pytest.mark.unit
    def test_root_endpoint(self):
        """测试根端点"""
        config = RuntimeConfig()
        server = AgentRuntimeServer(config)
        
        with TestClient(server._app) as client:
            response = client.get("/")
            
            assert response.status_code == 200
            data = response.json()
            assert data["service"] == "PPIO Agent Runtime"
            assert data["status"] == "running"
    
    @pytest.mark.unit
    def test_ping_endpoint_default(self):
        """测试默认 ping 端点"""
        config = RuntimeConfig()
        server = AgentRuntimeServer(config)
        
        with TestClient(server._app) as client:
            response = client.get("/ping")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "Healthy"
            assert "timestamp" in data
    
    @pytest.mark.unit
    def test_invocations_endpoint_no_handler(self):
        """测试没有处理器的调用端点"""
        config = RuntimeConfig()
        server = AgentRuntimeServer(config)
        
        request_data = {
            "prompt": "test prompt",
            "sandbox_id": "test-sandbox"
        }
        
        with TestClient(server._app) as client:
            response = client.post("/invocations", json=request_data)
            
            assert response.status_code == 500
            data = response.json()
            assert data["status"] == "error"
            assert "No entrypoint function registered" in data["error"]
    
    @pytest.mark.unit
    def test_invocations_endpoint_with_handler(self):
        """测试带处理器的调用端点"""
        config = RuntimeConfig()
        server = AgentRuntimeServer(config)
        
        def test_agent(request: dict, context: RequestContext) -> dict:
            return {
                "response": f"Processed: {request.get('prompt', '')}",
                "sandbox_id": context.sandbox_id,
                "request_id": context.request_id
            }
        
        server.set_entrypoint_handler(test_agent)
        
        request_data = {
            "prompt": "test prompt",
            "sandbox_id": "test-sandbox",
            "stream": False
        }
        
        with TestClient(server._app) as client:
            response = client.post("/invocations", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["result"]["response"] == "Processed: test prompt"
            assert data["result"]["sandbox_id"] == "test-sandbox"
            assert "duration" in data


class TestAgentRuntimeServerRequestProcessing:
    """AgentRuntimeServer 请求处理测试"""
    
    @pytest.mark.unit
    def test_json_request_parsing(self):
        """测试 JSON 请求解析"""
        config = RuntimeConfig()
        server = AgentRuntimeServer(config)
        
        def test_agent(request: dict) -> dict:
            return {"received": request}
        
        server.set_entrypoint_handler(test_agent)
        
        request_data = {
            "prompt": "test",
            "data": {"key": "value"},
            "sandbox_id": "test-sandbox"
        }
        
        with TestClient(server._app) as client:
            response = client.post("/invocations", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["result"]["received"]["prompt"] == "test"
            assert data["result"]["received"]["data"]["key"] == "value"
    
    @pytest.mark.unit
    def test_invalid_json_request(self):
        """测试无效 JSON 请求"""
        config = RuntimeConfig()
        server = AgentRuntimeServer(config)
        
        with TestClient(server._app) as client:
            response = client.post(
                "/invocations",
                content="invalid json",
                headers={"Content-Type": "application/json"}
            )
            
            assert response.status_code == 400
            data = response.json()
            assert "Invalid JSON" in data["error"]
    
    @pytest.mark.unit
    def test_async_agent_function(self):
        """测试异步 Agent 函数"""
        config = RuntimeConfig()
        server = AgentRuntimeServer(config)
        
        async def async_agent(request: dict) -> dict:
            await asyncio.sleep(0.01)  # 模拟异步操作
            return {"response": "async", "input": request.get("prompt")}
        
        server.set_entrypoint_handler(async_agent)
        
        request_data = {"prompt": "async test", "sandbox_id": "test"}
        
        with TestClient(server._app) as client:
            response = client.post("/invocations", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["result"]["response"] == "async"
            assert data["result"]["input"] == "async test"


class TestAgentRuntimeServerErrorHandling:
    """AgentRuntimeServer 错误处理测试"""
    
    @pytest.mark.unit
    def test_agent_function_exception(self):
        """测试 Agent 函数异常处理"""
        config = RuntimeConfig()
        server = AgentRuntimeServer(config)
        
        def error_agent(request: dict) -> dict:
            raise ValueError("Test error from agent")
        
        server.set_entrypoint_handler(error_agent)
        
        request_data = {"prompt": "test", "sandbox_id": "test"}
        
        with TestClient(server._app) as client:
            response = client.post("/invocations", json=request_data)
            
            assert response.status_code == 500
            data = response.json()
            assert data["status"] == "error"
            assert "Test error from agent" in data["error"]
            assert "duration" in data
