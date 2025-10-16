"""
端到端集成测试

测试完整的 Agent 应用运行流程，包括真实的 HTTP 服务器启动、请求处理和响应验证。
"""

import asyncio
import json
import threading
import time
import requests
import pytest
from typing import Generator, AsyncGenerator
from unittest.mock import patch

from ppio_sandbox.agent_runtime.runtime.app import AgentRuntimeApp
from ppio_sandbox.agent_runtime.runtime.context import RequestContext
from ppio_sandbox.agent_runtime.runtime.models import RuntimeConfig


class TestEndToEndBasicFlow:
    """端到端基础流程测试"""
    
    def setup_method(self, method):
        """每个测试方法前的设置"""
        # 为每个测试方法分配不同的端口
        port_map = {
            "test_simple_agent_end_to_end": 8901,
            "test_agent_with_context_end_to_end": 8902,
            "test_custom_ping_end_to_end": 8903,
            "test_error_handling_end_to_end": 8904
        }
        self.test_port = port_map.get(method.__name__, 8905)
        self.base_url = f"http://localhost:{self.test_port}"
        self.server_thread = None
        self.app = None
    
    def teardown_method(self):
        """每个测试方法后的清理"""
        # 清理可能还在运行的服务器
        if self.server_thread and self.server_thread.is_alive():
            # 发送停止信号（这里需要服务器支持优雅关闭）
            pass
    
    def start_server_in_thread(self, app: AgentRuntimeApp):
        """在独立线程中启动服务器"""
        def run_server():
            try:
                app.run(port=self.test_port, host="127.0.0.1")
            except Exception as e:
                print(f"Server error: {e}")
        
        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        
        # 等待服务器启动
        self._wait_for_server_ready()
    
    def _wait_for_server_ready(self, timeout=5):
        """等待服务器准备就绪"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{self.base_url}/ping", timeout=1)
                if response.status_code == 200:
                    return
            except requests.exceptions.RequestException:
                pass
            time.sleep(0.1)
        raise TimeoutError("Server did not start within timeout")
    
    @pytest.mark.integration
    def test_simple_agent_end_to_end(self):
        """测试简单 Agent 的端到端流程"""
        # 创建应用
        config = RuntimeConfig(debug=True)
        app = AgentRuntimeApp(config=config)
        
        # 注册简单的 Agent 函数
        @app.entrypoint
        def simple_agent(request: dict) -> dict:
            # 从 data 字段获取自定义数据
            data = request.get('data', {})
            name = data.get('name', 'World')
            return {
                "response": f"Hello, {name}!",
                "timestamp": "2024-01-01T00:00:00Z",
                "processed": True
            }
        
        # 启动服务器
        self.start_server_in_thread(app)
        
        # 发送请求（使用正确的 InvocationRequest 结构）
        request_data = {
            "data": {"name": "Alice"},
            "sandbox_id": "test-sandbox-e2e"
        }
        
        response = requests.post(
            f"{self.base_url}/invocations",
            json=request_data,
            headers={"Content-Type": "application/json"}
        )
        
        # 验证响应
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert "result" in data
        assert data["result"]["response"] == "Hello, Alice!"
        assert data["result"]["processed"] is True
        assert "duration" in data
    
    @pytest.mark.integration
    def test_agent_with_context_end_to_end(self):
        """测试带上下文的 Agent 端到端流程"""
        config = RuntimeConfig(debug=True)
        app = AgentRuntimeApp(config=config)
        
        @app.entrypoint
        def context_agent(request: dict, context: RequestContext) -> dict:
            return {
                "response": "Context processed",
                "sandbox_id": context.sandbox_id,
                "request_id": context.request_id,
                "user_agent": context.headers.get("user-agent", "unknown"),
                "input_data": request
            }
        
        self.start_server_in_thread(app)
        
        request_data = {
            "data": {"message": "test with context"},
            "sandbox_id": "context-test-sandbox"
        }
        
        response = requests.post(
            f"{self.base_url}/invocations",
            json=request_data,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "TestClient/1.0"
            }
        )
        
        assert response.status_code == 200
        
        data = response.json()
        result = data["result"]
        assert result["sandbox_id"] == "context-test-sandbox"
        assert result["user_agent"] == "TestClient/1.0"
        assert result["input_data"]["data"]["message"] == "test with context"
        assert "request_id" in result
    
    @pytest.mark.integration
    def test_custom_ping_end_to_end(self):
        """测试自定义 ping 处理器的端到端流程"""
        config = RuntimeConfig()
        app = AgentRuntimeApp(config=config)
        
        @app.entrypoint
        def dummy_agent(request: dict) -> dict:
            return {"response": "dummy"}
        
        @app.ping
        def custom_ping() -> dict:
            return {
                "status": "Healthy",  # 使用有效的枚举值
                "message": "e2e_test_agent v1.0.0 - custom_ping,context_support",
                "timestamp": "2024-01-01T00:00:00Z"
            }
        
        self.start_server_in_thread(app)
        
        # 测试自定义 ping
        response = requests.get(f"{self.base_url}/ping")
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "Healthy"
        assert "e2e_test_agent v1.0.0" in data["message"]
        assert "custom_ping" in data["message"]
        assert "context_support" in data["message"]
        assert data["timestamp"] == "2024-01-01T00:00:00Z"
    
    @pytest.mark.integration
    def test_error_handling_end_to_end(self):
        """测试错误处理的端到端流程"""
        config = RuntimeConfig()
        app = AgentRuntimeApp(config=config)
        
        @app.entrypoint
        def error_agent(request: dict) -> dict:
            data = request.get("data", {})
            if data.get("should_error"):
                raise ValueError("Intentional test error")
            return {"response": "success"}
        
        self.start_server_in_thread(app)
        
        # 测试正常请求（使用正确的数据结构）
        normal_request = {
            "data": {"should_error": False}, 
            "sandbox_id": "test"
        }
        response = requests.post(f"{self.base_url}/invocations", json=normal_request)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["result"]["response"] == "success"
        
        # 测试错误请求
        error_request = {
            "data": {"should_error": True}, 
            "sandbox_id": "test"
        }
        response = requests.post(f"{self.base_url}/invocations", json=error_request)
        
        assert response.status_code == 500
        data = response.json()
        assert data["status"] == "error"
        assert "Intentional test error" in data["error"]
        assert "duration" in data


class TestEndToEndAsyncFlow:
    """端到端异步流程测试"""
    
    def setup_method(self, method):
        """每个测试方法前的设置"""
        # 为异步测试分配不同的端口范围
        port_map = {
            "test_async_agent_end_to_end": 8910,
        }
        self.test_port = port_map.get(method.__name__, 8911)
        self.base_url = f"http://localhost:{self.test_port}"
        self.server_thread = None
    
    def teardown_method(self):
        """清理"""
        pass
    
    def start_server_in_thread(self, app: AgentRuntimeApp):
        """在独立线程中启动服务器"""
        def run_server():
            try:
                app.run(port=self.test_port, host="127.0.0.1")
            except Exception as e:
                print(f"Server error: {e}")
        
        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        
        # 等待服务器启动
        self._wait_for_server_ready()
    
    def _wait_for_server_ready(self, timeout=5):
        """等待服务器准备就绪"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{self.base_url}/ping", timeout=1)
                if response.status_code == 200:
                    return
            except requests.exceptions.RequestException:
                pass
            time.sleep(0.1)
        raise TimeoutError("Server did not start within timeout")
    
    @pytest.mark.integration
    def test_async_agent_end_to_end(self):
        """测试异步 Agent 的端到端流程"""
        config = RuntimeConfig()
        app = AgentRuntimeApp(config=config)
        
        @app.entrypoint
        async def async_agent(request: dict) -> dict:
            # 模拟异步操作
            await asyncio.sleep(0.1)
            data = request.get('data', {})
            input_text = data.get('input', '')
            return {
                "response": f"Async processed: {input_text}",
                "async": True,
                "delay": 0.1
            }
        
        self.start_server_in_thread(app)
        
        request_data = {
            "data": {"input": "async test data"},
            "sandbox_id": "async-test"
        }
        
        start_time = time.time()
        response = requests.post(f"{self.base_url}/invocations", json=request_data)
        end_time = time.time()
        
        assert response.status_code == 200
        
        data = response.json()
        result = data["result"]
        assert result["response"] == "Async processed: async test data"
        assert result["async"] is True
        
        # 验证确实有异步延迟
        assert end_time - start_time >= 0.1
