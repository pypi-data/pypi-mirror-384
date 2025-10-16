"""
AgentRuntimeApp 单元测试

测试 AgentRuntimeApp 类的完整功能，包括初始化、配置、装饰器集成、生命周期管理等。
"""

import pytest
import asyncio
import inspect
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Generator, AsyncGenerator

from ppio_sandbox.agent_runtime.runtime.app import AgentRuntimeApp
from ppio_sandbox.agent_runtime.runtime.server import AgentRuntimeServer
from ppio_sandbox.agent_runtime.runtime.context import RequestContext, AgentRuntimeContext
from ppio_sandbox.agent_runtime.runtime.models import RuntimeConfig, PingStatus


class TestAgentRuntimeAppInitialization:
    """AgentRuntimeApp 初始化测试"""
    
    @pytest.mark.unit
    def test_default_initialization(self):
        """测试默认初始化"""
        app = AgentRuntimeApp()
        
        # 验证默认配置
        assert app.config is not None
        assert isinstance(app.config, RuntimeConfig)
        assert app.config.host == "0.0.0.0"
        assert app.config.port == 8080
        assert app.config.debug is False
        
        # 验证初始状态
        assert app._server is None
        assert app._entrypoint_func is None
        assert app._ping_func is None
        
    @pytest.mark.unit
    def test_custom_config_initialization(self):
        """测试自定义配置初始化"""
        config = RuntimeConfig(
            host="127.0.0.1",
            port=9000,
            debug=True,
            timeout=600,
            max_request_size=2 * 1024 * 1024
        )
        
        app = AgentRuntimeApp(config=config)
        
        assert app.config.host == "127.0.0.1"
        assert app.config.port == 9000
        assert app.config.debug is True
        assert app.config.timeout == 600
        assert app.config.max_request_size == 2 * 1024 * 1024
    
    @pytest.mark.unit
    def test_debug_flag_initialization(self):
        """测试调试标志初始化"""
        app = AgentRuntimeApp(debug=True)
        
        assert app.config.debug is True
        
        # 测试调试标志覆盖配置
        config = RuntimeConfig(debug=False)
        app = AgentRuntimeApp(config=config, debug=True)
        
        assert app.config.debug is True


class TestAgentRuntimeAppDecorators:
    """AgentRuntimeApp 装饰器集成测试"""
    
    @pytest.mark.unit
    def test_entrypoint_decorator_integration(self):
        """测试入口点装饰器集成"""
        app = AgentRuntimeApp()
        
        # 测试同步函数
        @app.entrypoint
        def sync_agent(request: dict) -> dict:
            return {"response": "sync", "data": request}
        
        assert app._entrypoint_func is sync_agent
        
        # 测试异步函数
        @app.entrypoint
        async def async_agent(request: dict) -> dict:
            return {"response": "async", "data": request}
        
        assert app._entrypoint_func is async_agent
        assert inspect.iscoroutinefunction(async_agent)
    
    @pytest.mark.unit
    def test_ping_decorator_integration(self):
        """测试 ping 装饰器集成"""
        app = AgentRuntimeApp()
        
        @app.ping
        def custom_ping() -> dict:
            return {"status": "healthy", "service": "test"}
        
        assert app._ping_func is custom_ping
        
        # 测试调用
        result = custom_ping()
        assert result["status"] == "healthy"
        assert result["service"] == "test"
    
    @pytest.mark.unit
    def test_middleware_decorator_integration(self):
        """测试中间件装饰器集成"""
        app = AgentRuntimeApp()
        
        # 中间件装饰器应该创建服务器实例
        assert app._server is None
        
        @app.middleware
        async def test_middleware(request, call_next):
            response = await call_next(request)
            return response
        
        # 注册中间件后应该有服务器实例
        assert app._server is not None
        assert isinstance(app._server, AgentRuntimeServer)


class TestAgentRuntimeAppContextAccess:
    """AgentRuntimeApp 上下文访问测试"""
    
    def teardown_method(self):
        """每个测试方法后清理上下文"""
        AgentRuntimeContext.clear_current_context()
    
    @pytest.mark.unit
    def test_context_property_access(self):
        """测试上下文属性访问"""
        app = AgentRuntimeApp()
        
        # 初始状态下没有上下文
        assert app.context is None
        
        # 设置上下文
        test_context = RequestContext(
            sandbox_id="test-sandbox",
            request_id="test-request"
        )
        AgentRuntimeContext.set_current_context(test_context)
        
        # 通过应用访问上下文
        retrieved_context = app.context
        assert retrieved_context is not None
        assert retrieved_context.sandbox_id == "test-sandbox"
        assert retrieved_context.request_id == "test-request"
    
    @pytest.mark.unit
    def test_context_in_agent_function(self):
        """测试在 Agent 函数中访问上下文"""
        app = AgentRuntimeApp()
        
        @app.entrypoint
        def context_aware_agent(request: dict) -> dict:
            # 在 Agent 函数中访问上下文
            current_context = app.context
            return {
                "response": "context_aware",
                "has_context": current_context is not None,
                "sandbox_id": current_context.sandbox_id if current_context else None
            }
        
        # 设置上下文并调用
        test_context = RequestContext(sandbox_id="test-ctx")
        AgentRuntimeContext.set_current_context(test_context)
        
        result = context_aware_agent({"test": "data"})
        
        assert result["has_context"] is True
        assert result["sandbox_id"] == "test-ctx"


class TestAgentRuntimeAppServerManagement:
    """AgentRuntimeApp 服务器管理测试"""
    
    @pytest.mark.unit
    def test_lazy_server_creation(self):
        """测试服务器的懒加载创建"""
        app = AgentRuntimeApp()
        
        # 初始状态没有服务器
        assert app._server is None
        
        # 注册入口点不会创建服务器
        @app.entrypoint
        def test_agent(request: dict) -> dict:
            return {"response": "test"}
        
        assert app._server is None
        
        # 注册中间件会创建服务器
        @app.middleware
        async def test_middleware(request, call_next):
            return await call_next(request)
        
        assert app._server is not None
    
    @pytest.mark.unit
    @patch('ppio_sandbox.agent_runtime.runtime.server.AgentRuntimeServer.run')
    def test_run_method_basic(self, mock_server_run):
        """测试基本的 run 方法"""
        app = AgentRuntimeApp()
        
        @app.entrypoint
        def test_agent(request: dict) -> dict:
            return {"response": "test"}
        
        # 测试运行
        app.run(port=8888, host="localhost")
        
        # 验证配置更新
        assert app.config.port == 8888
        assert app.config.host == "localhost"
        
        # 验证服务器被创建和运行
        assert app._server is not None
        mock_server_run.assert_called_once_with(8888, "localhost")
    
    @pytest.mark.unit
    def test_run_without_entrypoint_raises_error(self):
        """测试没有入口点时运行会抛出错误"""
        app = AgentRuntimeApp()
        
        with pytest.raises(RuntimeError) as exc_info:
            app.run()
        
        assert "No entrypoint function registered" in str(exc_info.value)


class TestAgentRuntimeAppErrorHandling:
    """AgentRuntimeApp 错误处理测试"""
    
    @pytest.mark.unit
    def test_agent_function_exceptions(self):
        """测试 Agent 函数异常处理"""
        app = AgentRuntimeApp()
        
        @app.entrypoint
        def error_agent(request: dict) -> dict:
            if request.get("should_error"):
                raise ValueError("Test error from agent")
            return {"response": "success"}
        
        # 正常调用
        result = error_agent({"data": "test"})
        assert result["response"] == "success"
        
        # 异常调用
        with pytest.raises(ValueError, match="Test error from agent"):
            error_agent({"should_error": True})
    
    @pytest.mark.unit
    def test_decorator_function_preservation(self):
        """测试装饰器保留函数属性"""
        app = AgentRuntimeApp()
        
        @app.entrypoint
        def documented_agent(request: dict) -> dict:
            """这是一个有文档的 Agent 函数。"""
            return {"response": "documented"}
        
        # 验证函数属性被保留
        assert documented_agent.__name__ == "documented_agent"
        assert "这是一个有文档的 Agent 函数" in documented_agent.__doc__
        
        # 验证函数仍然可以正常调用
        result = documented_agent({"test": "input"})
        assert result["response"] == "documented"