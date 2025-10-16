"""
Mock Agent函数

提供各种类型的 Mock Agent 函数用于测试。
"""

import asyncio
import time
from typing import Any, Dict, List, Optional, Generator, AsyncGenerator
from unittest.mock import Mock, AsyncMock

from ppio_sandbox.agent_runtime.runtime.context import RequestContext


class MockAgentFunctions:
    """Mock Agent 函数集合"""
    
    @staticmethod
    def simple_sync_agent(request: dict) -> dict:
        """简单的同步 Agent 函数"""
        return {
            "response": f"Processed: {request.get('prompt', '')}",
            "status": "success",
            "type": "sync"
        }
    
    @staticmethod
    async def simple_async_agent(request: dict) -> dict:
        """简单的异步 Agent 函数"""
        await asyncio.sleep(0.01)  # 模拟异步操作
        return {
            "response": f"Async processed: {request.get('prompt', '')}",
            "status": "success",
            "type": "async"
        }
    
    @staticmethod
    def agent_with_context(request: dict, context: RequestContext) -> dict:
        """带上下文的 Agent 函数"""
        return {
            "response": f"Processed: {request.get('prompt', '')}",
            "sandbox_id": context.sandbox_id,
            "request_id": context.request_id,
            "headers_count": len(context.headers),
            "type": "with_context"
        }
    
    @staticmethod
    async def async_agent_with_context(request: dict, context: RequestContext) -> dict:
        """异步带上下文的 Agent 函数"""
        await asyncio.sleep(0.01)
        return {
            "response": f"Async processed: {request.get('prompt', '')}",
            "sandbox_id": context.sandbox_id,
            "request_id": context.request_id,
            "session_id": context.session_id,  # 测试向后兼容性
            "type": "async_with_context"
        }
    
    @staticmethod
    def streaming_agent(request: dict) -> Generator[str, None, None]:
        """同步流式 Agent 函数"""
        prompt = request.get("prompt", "")
        chunk_count = request.get("chunks", 3)
        
        for i in range(chunk_count):
            time.sleep(0.01)  # 模拟处理时间
            yield f"Chunk {i+1}: Processing '{prompt}'"
        
        yield f"Final: Completed processing '{prompt}'"
    
    @staticmethod
    async def async_streaming_agent(request: dict) -> AsyncGenerator[str, None]:
        """异步流式 Agent 函数"""
        prompt = request.get("prompt", "")
        chunk_count = request.get("chunks", 3)
        
        for i in range(chunk_count):
            await asyncio.sleep(0.01)  # 模拟异步处理时间
            yield f"Async Chunk {i+1}: Processing '{prompt}'"
        
        yield f"Async Final: Completed processing '{prompt}'"
    
    @staticmethod
    def slow_agent(request: dict) -> dict:
        """慢速 Agent 函数（用于超时测试）"""
        delay = request.get("delay", 1.0)
        time.sleep(delay)
        return {
            "response": f"Slow processed after {delay}s",
            "delay": delay
        }
    
    @staticmethod
    async def slow_async_agent(request: dict) -> dict:
        """慢速异步 Agent 函数"""
        delay = request.get("delay", 1.0)
        await asyncio.sleep(delay)
        return {
            "response": f"Slow async processed after {delay}s",
            "delay": delay
        }
    
    @staticmethod
    def error_agent(request: dict) -> dict:
        """抛出异常的 Agent 函数"""
        error_type = request.get("error_type", "ValueError")
        error_message = request.get("error_message", "Test error")
        
        if error_type == "ValueError":
            raise ValueError(error_message)
        elif error_type == "RuntimeError":
            raise RuntimeError(error_message)
        elif error_type == "KeyError":
            raise KeyError(error_message)
        else:
            raise Exception(error_message)
    
    @staticmethod
    async def async_error_agent(request: dict) -> dict:
        """抛出异常的异步 Agent 函数"""
        await asyncio.sleep(0.01)
        error_type = request.get("error_type", "ValueError")
        error_message = request.get("error_message", "Async test error")
        
        if error_type == "ValueError":
            raise ValueError(error_message)
        elif error_type == "RuntimeError":
            raise RuntimeError(error_message)
        else:
            raise Exception(error_message)
    
    @staticmethod
    def data_processing_agent(request: dict) -> dict:
        """数据处理 Agent 函数"""
        data = request.get("data", {})
        operation = request.get("operation", "count")
        
        if operation == "count":
            result = len(data) if isinstance(data, (list, dict, str)) else 0
        elif operation == "sum" and isinstance(data, list):
            result = sum(x for x in data if isinstance(x, (int, float)))
        elif operation == "keys" and isinstance(data, dict):
            result = list(data.keys())
        else:
            result = "unknown_operation"
        
        return {
            "operation": operation,
            "result": result,
            "input_type": type(data).__name__
        }
    
    @staticmethod
    def large_response_agent(request: dict) -> dict:
        """返回大量数据的 Agent 函数"""
        size = request.get("size", 1000)
        return {
            "response": "Large data response",
            "data": [f"item_{i}" for i in range(size)],
            "size": size
        }
    
    @staticmethod
    def conditional_agent(request: dict) -> dict:
        """根据输入条件返回不同结果的 Agent 函数"""
        condition = request.get("condition", "default")
        
        if condition == "success":
            return {"status": "success", "message": "Operation completed"}
        elif condition == "warning":
            return {"status": "warning", "message": "Operation completed with warnings"}
        elif condition == "error":
            return {"status": "error", "message": "Operation failed"}
        else:
            return {"status": "unknown", "message": "Unknown condition"}


class MockHealthChecks:
    """Mock 健康检查函数集合"""
    
    @staticmethod
    def healthy_ping() -> dict:
        """健康的 ping 函数"""
        return {
            "status": "Healthy",
            "timestamp": "2024-01-01T00:00:00Z",
            "service": "mock_agent"
        }
    
    @staticmethod
    def busy_ping() -> dict:
        """繁忙状态的 ping 函数"""
        return {
            "status": "HealthyBusy",
            "message": "System under load",
            "timestamp": "2024-01-01T00:00:00Z"
        }
    
    @staticmethod
    async def async_ping() -> dict:
        """异步 ping 函数"""
        await asyncio.sleep(0.01)
        return {
            "status": "Healthy",
            "async": True,
            "timestamp": "2024-01-01T00:00:00Z"
        }
    
    @staticmethod
    def error_ping() -> dict:
        """抛出异常的 ping 函数"""
        raise RuntimeError("Health check failed")
    
    @staticmethod
    def custom_ping_with_metrics() -> dict:
        """带指标的自定义 ping 函数"""
        return {
            "status": "Healthy",
            "metrics": {
                "cpu_usage": 45.2,
                "memory_usage": 67.8,
                "active_connections": 15
            },
            "timestamp": "2024-01-01T00:00:00Z"
        }


class MockMiddlewares:
    """Mock 中间件函数集合"""
    
    @staticmethod
    async def logging_middleware(request, call_next):
        """日志中间件"""
        start_time = time.time()
        
        # 记录请求开始
        print(f"Request started: {request.url}")
        
        # 调用下一个中间件或处理器
        response = await call_next(request)
        
        # 记录请求完成
        duration = time.time() - start_time
        print(f"Request completed in {duration:.4f}s")
        
        return response
    
    @staticmethod
    async def auth_middleware(request, call_next):
        """认证中间件"""
        # 检查授权头
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            from starlette.responses import JSONResponse
            return JSONResponse(
                {"error": "Missing or invalid authorization"},
                status_code=401
            )
        
        return await call_next(request)
    
    @staticmethod
    async def cors_middleware(request, call_next):
        """CORS 中间件"""
        response = await call_next(request)
        
        # 添加 CORS 头
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        
        return response
    
    @staticmethod
    async def error_handling_middleware(request, call_next):
        """错误处理中间件"""
        try:
            return await call_next(request)
        except Exception as e:
            from starlette.responses import JSONResponse
            return JSONResponse(
                {"error": str(e), "type": type(e).__name__},
                status_code=500
            )
    
    @staticmethod
    async def request_modification_middleware(request, call_next):
        """修改请求的中间件"""
        # 修改请求（实际实现中需要小心处理）
        # 这里只是模拟添加一些元数据
        
        response = await call_next(request)
        
        # 修改响应
        if hasattr(response, 'headers'):
            response.headers["X-Processed-By"] = "MockMiddleware"
        
        return response


class MockAgentFactory:
    """Mock Agent 工厂类"""
    
    @classmethod
    def create_configurable_agent(cls, config: dict):
        """创建可配置的 Agent 函数"""
        def configurable_agent(request: dict) -> dict:
            # 使用配置和请求生成响应
            response_template = config.get("response_template", "Processed: {prompt}")
            prompt = request.get("prompt", "")
            
            result = {
                "response": response_template.format(prompt=prompt),
                "config": config,
                "request_id": request.get("request_id")
            }
            
            # 如果配置要求延迟
            if config.get("delay"):
                time.sleep(config["delay"])
            
            # 如果配置要求抛出异常
            if config.get("raise_error"):
                raise ValueError(config.get("error_message", "Configured error"))
            
            return result
        
        return configurable_agent
    
    @classmethod
    def create_streaming_agent(cls, chunk_count: int = 5, delay: float = 0.01):
        """创建流式 Agent 函数"""
        async def streaming_agent(request: dict) -> AsyncGenerator[str, None]:
            prompt = request.get("prompt", "")
            for i in range(chunk_count):
                await asyncio.sleep(delay)
                yield f"Stream chunk {i+1}/{chunk_count}: {prompt}"
        
        return streaming_agent
    
    @classmethod
    def create_mock_with_validation(cls, required_fields: List[str]):
        """创建带输入验证的 Mock Agent"""
        def validating_agent(request: dict) -> dict:
            # 验证必填字段
            missing_fields = [field for field in required_fields if field not in request]
            if missing_fields:
                raise ValueError(f"Missing required fields: {missing_fields}")
            
            return {
                "response": "Validation passed",
                "validated_fields": required_fields,
                "request_data": request
            }
        
        return validating_agent


# 预定义的常用 Mock Agent 实例
MOCK_AGENTS = {
    "simple": MockAgentFunctions.simple_sync_agent,
    "async": MockAgentFunctions.simple_async_agent,
    "streaming": MockAgentFunctions.streaming_agent,
    "async_streaming": MockAgentFunctions.async_streaming_agent,
    "with_context": MockAgentFunctions.agent_with_context,
    "error": MockAgentFunctions.error_agent,
    "slow": MockAgentFunctions.slow_agent,
    "data_processing": MockAgentFunctions.data_processing_agent,
}

MOCK_HEALTH_CHECKS = {
    "healthy": MockHealthChecks.healthy_ping,
    "busy": MockHealthChecks.busy_ping,
    "async": MockHealthChecks.async_ping,
    "error": MockHealthChecks.error_ping,
    "metrics": MockHealthChecks.custom_ping_with_metrics,
}

MOCK_MIDDLEWARES = {
    "logging": MockMiddlewares.logging_middleware,
    "auth": MockMiddlewares.auth_middleware,
    "cors": MockMiddlewares.cors_middleware,
    "error_handling": MockMiddlewares.error_handling_middleware,
    "request_modification": MockMiddlewares.request_modification_middleware,
}