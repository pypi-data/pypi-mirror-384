"""
装饰器功能单元测试

测试 AgentRuntimeApp 中装饰器的功能和行为。
"""

import pytest
import asyncio
import inspect
from typing import Generator, AsyncGenerator

from ppio_sandbox.agent_runtime.runtime.app import AgentRuntimeApp
from ppio_sandbox.agent_runtime.runtime.context import RequestContext
from ppio_sandbox.agent_runtime.runtime.models import RuntimeConfig, PingStatus


class TestEntrypointDecorator:
    """@entrypoint 装饰器测试"""
    
    @pytest.mark.unit
    def test_sync_function_decoration(self):
        """测试同步函数装饰"""
        app = AgentRuntimeApp()
        
        @app.entrypoint
        def sync_agent(request: dict) -> dict:
            return {"response": "sync", "input": request.get("prompt", "")}
        
        # 验证函数被正确注册
        assert app._entrypoint_func is not None
        assert app._entrypoint_func == sync_agent
        
        # 验证装饰器不改变函数本身
        assert sync_agent.__name__ == "sync_agent"
        assert callable(sync_agent)
    
    @pytest.mark.unit
    def test_async_function_decoration(self):
        """测试异步函数装饰"""
        app = AgentRuntimeApp()
        
        @app.entrypoint
        async def async_agent(request: dict) -> dict:
            await asyncio.sleep(0.01)
            return {"response": "async", "input": request.get("prompt", "")}
        
        # 验证函数被正确注册
        assert app._entrypoint_func is not None
        assert app._entrypoint_func == async_agent
        assert inspect.iscoroutinefunction(async_agent)
    
    @pytest.mark.unit
    def test_function_with_context_decoration(self):
        """测试带上下文参数的函数装饰"""
        app = AgentRuntimeApp()
        
        @app.entrypoint
        def agent_with_context(request: dict, context: RequestContext) -> dict:
            return {
                "response": "with_context",
                "sandbox_id": context.sandbox_id,
                "request_id": context.request_id
            }
        
        # 验证函数被正确注册
        assert app._entrypoint_func is not None
        assert app._entrypoint_func == agent_with_context
        
        # 验证函数签名
        sig = inspect.signature(agent_with_context)
        params = list(sig.parameters.keys())
        assert "request" in params
        assert "context" in params
    
    @pytest.mark.unit
    def test_sync_generator_decoration(self):
        """测试同步生成器函数装饰"""
        app = AgentRuntimeApp()
        
        @app.entrypoint
        def streaming_agent(request: dict) -> Generator[str, None, None]:
            for i in range(3):
                yield f"chunk_{i}: {request.get('prompt', '')}"
        
        # 验证函数被正确注册
        assert app._entrypoint_func is not None
        assert app._entrypoint_func == streaming_agent
        
        # 验证返回值是生成器
        result = streaming_agent({"prompt": "test"})
        assert inspect.isgenerator(result)
        
        # 验证生成器内容
        chunks = list(result)
        assert len(chunks) == 3
        assert chunks[0] == "chunk_0: test"
    
    @pytest.mark.unit
    def test_multiple_entrypoint_registration(self):
        """测试多次注册入口点（应该覆盖）"""
        app = AgentRuntimeApp()
        
        @app.entrypoint
        def first_agent(request: dict) -> dict:
            return {"agent": "first"}
        
        assert app._entrypoint_func == first_agent
        
        @app.entrypoint
        def second_agent(request: dict) -> dict:
            return {"agent": "second"}
        
        # 第二个应该覆盖第一个
        assert app._entrypoint_func == second_agent
        assert app._entrypoint_func != first_agent


class TestPingDecorator:
    """@ping 装饰器测试"""
    
    @pytest.mark.unit
    def test_sync_ping_decoration(self):
        """测试同步 ping 函数装饰"""
        app = AgentRuntimeApp()
        
        @app.ping
        def custom_ping() -> dict:
            return {"status": "healthy", "service": "test"}
        
        # 验证函数被正确注册
        assert app._ping_func is not None
        assert app._ping_func == custom_ping
    
    @pytest.mark.unit
    def test_async_ping_decoration(self):
        """测试异步 ping 函数装饰"""
        app = AgentRuntimeApp()
        
        @app.ping
        async def async_ping() -> dict:
            await asyncio.sleep(0.01)
            return {"status": "healthy", "service": "async_test"}
        
        # 验证函数被正确注册
        assert app._ping_func is not None
        assert app._ping_func == async_ping
        assert inspect.iscoroutinefunction(async_ping)


class TestMiddlewareDecorator:
    """@middleware 装饰器测试"""
    
    @pytest.mark.unit
    def test_middleware_registration(self):
        """测试中间件注册"""
        config = RuntimeConfig()
        app = AgentRuntimeApp(config=config)
        
        @app.middleware
        async def test_middleware(request, call_next):
            # 模拟中间件逻辑
            response = await call_next(request)
            return response
        
        # 验证服务器被创建并且中间件被注册
        assert app._server is not None
        # 装饰器应该返回原函数
        assert test_middleware.__name__ == "test_middleware"


class TestDecoratorCombination:
    """装饰器组合测试"""
    
    @pytest.mark.unit
    def test_all_decorators_together(self):
        """测试所有装饰器一起使用"""
        config = RuntimeConfig(debug=True)
        app = AgentRuntimeApp(config=config)
        
        @app.entrypoint
        def main_agent(request: dict, context: RequestContext) -> dict:
            return {
                "response": "main",
                "sandbox_id": context.sandbox_id
            }
        
        @app.ping
        def health_check() -> dict:
            return {"status": "healthy", "timestamp": "2024-01-01"}
        
        @app.middleware
        async def logging_middleware(request, call_next):
            # 模拟日志记录
            response = await call_next(request)
            return response
        
        # 验证所有函数都被正确注册
        assert app._entrypoint_func == main_agent
        assert app._ping_func == health_check
        assert app._server is not None


class TestDecoratorErrorHandling:
    """装饰器错误处理测试"""
    
    @pytest.mark.unit
    def test_entrypoint_function_with_exceptions(self):
        """测试入口点函数抛出异常"""
        app = AgentRuntimeApp()
        
        @app.entrypoint
        def error_agent(request: dict) -> dict:
            if request.get("error"):
                raise ValueError("Test error")
            return {"response": "success"}
        
        # 正常调用
        result = error_agent({"prompt": "test"})
        assert result == {"response": "success"}
        
        # 异常调用
        with pytest.raises(ValueError, match="Test error"):
            error_agent({"error": True})