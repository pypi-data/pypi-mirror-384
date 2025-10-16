"""
Mock服务器

提供模拟 HTTP 服务器和网络请求的工具。
"""

import asyncio
import json
import time
from typing import Any, Dict, List, Optional, Callable, Union
from unittest.mock import Mock, AsyncMock, MagicMock
from contextlib import asynccontextmanager

import httpx
from starlette.applications import Starlette
from starlette.responses import JSONResponse, StreamingResponse
from starlette.routing import Route


class MockHTTPServer:
    """Mock HTTP 服务器"""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 8999):
        self.host = host
        self.port = port
        self.app = None
        self.server = None
        self.responses = {}
        self.request_log = []
        
    def setup_response(self, path: str, method: str = "POST", 
                      response_data: Dict = None, status_code: int = 200,
                      delay: float = 0):
        """设置特定路径的响应"""
        self.responses[f"{method.upper()}:{path}"] = {
            "data": response_data or {"message": "mock response"},
            "status_code": status_code,
            "delay": delay
        }
    
    def create_app(self) -> Starlette:
        """创建 Starlette 应用"""
        async def handle_request(request):
            # 记录请求
            request_info = {
                "method": request.method,
                "path": request.url.path,
                "headers": dict(request.headers),
                "timestamp": time.time()
            }
            
            # 尝试读取请求体
            try:
                if request.method in ["POST", "PUT", "PATCH"]:
                    request_info["body"] = await request.json()
            except:
                request_info["body"] = None
            
            self.request_log.append(request_info)
            
            # 查找预设响应
            key = f"{request.method}:{request.url.path}"
            if key in self.responses:
                response_config = self.responses[key]
                
                # 模拟延迟
                if response_config["delay"] > 0:
                    await asyncio.sleep(response_config["delay"])
                
                return JSONResponse(
                    response_config["data"],
                    status_code=response_config["status_code"]
                )
            
            # 默认响应
            return JSONResponse(
                {"error": "Mock server - no response configured"},
                status_code=404
            )
        
        # 创建通用路由
        routes = [
            Route("/{path:path}", handle_request, methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
        ]
        
        return Starlette(routes=routes)
    
    async def start(self):
        """启动服务器"""
        import uvicorn
        self.app = self.create_app()
        config = uvicorn.Config(self.app, host=self.host, port=self.port, log_level="error")
        self.server = uvicorn.Server(config)
        await self.server.serve()
    
    def get_request_log(self) -> List[Dict]:
        """获取请求日志"""
        return self.request_log.copy()
    
    def clear_request_log(self):
        """清除请求日志"""
        self.request_log.clear()
    
    @property
    def base_url(self) -> str:
        """获取服务器基础 URL"""
        return f"http://{self.host}:{self.port}"


class MockAgentRuntimeServer:
    """Mock Agent Runtime 服务器"""
    
    def __init__(self):
        self.invocation_responses = []
        self.ping_responses = []
        self.request_count = 0
        self.error_responses = {}
        
    def setup_invocation_response(self, response_data: Dict, delay: float = 0):
        """设置调用响应"""
        self.invocation_responses.append({
            "data": response_data,
            "delay": delay
        })
    
    def setup_ping_response(self, response_data: Dict, delay: float = 0):
        """设置 ping 响应"""
        self.ping_responses.append({
            "data": response_data,
            "delay": delay
        })
    
    def setup_error_response(self, path: str, status_code: int, error_message: str):
        """设置错误响应"""
        self.error_responses[path] = {
            "status_code": status_code,
            "message": error_message
        }
    
    async def handle_invocation(self, request_data: Dict) -> Dict:
        """处理调用请求"""
        self.request_count += 1
        
        # 检查是否有错误响应配置
        if "/invocations" in self.error_responses:
            error_config = self.error_responses["/invocations"]
            raise httpx.HTTPStatusError(
                f"HTTP {error_config['status_code']}",
                request=None,
                response=Mock(status_code=error_config['status_code'])
            )
        
        # 使用预设响应或默认响应
        if self.invocation_responses:
            response_config = self.invocation_responses.pop(0)
            
            if response_config["delay"] > 0:
                await asyncio.sleep(response_config["delay"])
            
            return response_config["data"]
        
        # 默认响应
        return {
            "result": f"Mock response for: {request_data.get('prompt', '')}",
            "status": "success",
            "duration": 0.1,
            "metadata": {"mock": True, "request_count": self.request_count}
        }
    
    async def handle_ping(self) -> Dict:
        """处理 ping 请求"""
        # 检查是否有错误响应配置
        if "/ping" in self.error_responses:
            error_config = self.error_responses["/ping"]
            raise httpx.HTTPStatusError(
                f"HTTP {error_config['status_code']}",
                request=None,
                response=Mock(status_code=error_config['status_code'])
            )
        
        # 使用预设响应或默认响应
        if self.ping_responses:
            response_config = self.ping_responses.pop(0)
            
            if response_config["delay"] > 0:
                await asyncio.sleep(response_config["delay"])
            
            return response_config["data"]
        
        # 默认响应
        return {
            "status": "Healthy",
            "timestamp": "2024-01-01T00:00:00Z",
            "mock": True
        }
    
    def create_starlette_app(self) -> Starlette:
        """创建完整的 Mock Starlette 应用"""
        async def handle_root(request):
            return JSONResponse({
                "service": "Mock Agent Runtime",
                "status": "running",
                "mock": True
            })
        
        async def handle_ping_endpoint(request):
            try:
                result = await self.handle_ping()
                return JSONResponse(result)
            except httpx.HTTPStatusError as e:
                return JSONResponse(
                    {"error": "Mock ping error"},
                    status_code=e.response.status_code
                )
        
        async def handle_invocations_endpoint(request):
            try:
                request_data = await request.json()
                result = await self.handle_invocation(request_data)
                
                # 检查是否是流式请求
                if request_data.get("stream", False):
                    return StreamingResponse(
                        self._create_stream_response(result),
                        media_type="text/plain"
                    )
                
                return JSONResponse(result)
            except httpx.HTTPStatusError as e:
                return JSONResponse(
                    {"error": "Mock invocation error"},
                    status_code=e.response.status_code
                )
            except Exception as e:
                return JSONResponse(
                    {"error": str(e)},
                    status_code=500
                )
        
        routes = [
            Route("/", handle_root, methods=["GET"]),
            Route("/ping", handle_ping_endpoint, methods=["GET"]),
            Route("/invocations", handle_invocations_endpoint, methods=["POST"])
        ]
        
        return Starlette(routes=routes)
    
    async def _create_stream_response(self, result: Dict):
        """创建流式响应"""
        # 模拟流式数据
        chunks = [
            "Starting processing...",
            f"Processing: {result.get('result', '')}",
            "Finalizing...",
            "Done!"
        ]
        
        for chunk in chunks:
            yield f"data: {json.dumps(chunk)}\n\n"
            await asyncio.sleep(0.01)


class MockHTTPClient:
    """Mock HTTP 客户端"""
    
    def __init__(self):
        self.responses = {}
        self.request_history = []
        self.default_response = {"mock": True}
        
    def setup_response(self, method: str, url: str, 
                      response_data: Any = None, 
                      status_code: int = 200,
                      headers: Dict = None):
        """设置特定请求的响应"""
        key = f"{method.upper()}:{url}"
        self.responses[key] = {
            "data": response_data or self.default_response,
            "status_code": status_code,
            "headers": headers or {}
        }
    
    def create_mock_client(self) -> Mock:
        """创建 Mock HTTP 客户端"""
        mock_client = Mock()
        
        # 模拟异步上下文管理器
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        # 设置 HTTP 方法
        for method in ["get", "post", "put", "delete", "patch"]:
            setattr(mock_client, method, self._create_method_mock(method.upper()))
        
        return mock_client
    
    def _create_method_mock(self, method: str):
        """创建特定 HTTP 方法的 Mock"""
        async def method_mock(url: str, **kwargs):
            # 记录请求
            request_info = {
                "method": method,
                "url": url,
                "kwargs": kwargs,
                "timestamp": time.time()
            }
            self.request_history.append(request_info)
            
            # 查找预设响应
            key = f"{method}:{url}"
            if key in self.responses:
                response_config = self.responses[key]
                
                # 创建响应 Mock
                response_mock = Mock()
                response_mock.status_code = response_config["status_code"]
                response_mock.headers = response_config["headers"]
                response_mock.json = AsyncMock(return_value=response_config["data"])
                response_mock.text = json.dumps(response_config["data"])
                
                return response_mock
            
            # 默认响应
            default_mock = Mock()
            default_mock.status_code = 200
            default_mock.headers = {}
            default_mock.json = AsyncMock(return_value=self.default_response)
            default_mock.text = json.dumps(self.default_response)
            
            return default_mock
        
        return AsyncMock(side_effect=method_mock)
    
    def get_request_history(self) -> List[Dict]:
        """获取请求历史"""
        return self.request_history.copy()
    
    def clear_request_history(self):
        """清除请求历史"""
        self.request_history.clear()


class MockNetworkScenarios:
    """模拟网络场景"""
    
    @staticmethod
    def create_timeout_client(timeout_delay: float = 5.0):
        """创建会超时的客户端"""
        async def timeout_method(*args, **kwargs):
            await asyncio.sleep(timeout_delay)
            raise httpx.TimeoutException("Request timed out")
        
        mock_client = Mock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        for method in ["get", "post", "put", "delete"]:
            setattr(mock_client, method, AsyncMock(side_effect=timeout_method))
        
        return mock_client
    
    @staticmethod
    def create_network_error_client(error_type: str = "ConnectionError"):
        """创建网络错误客户端"""
        def error_method(*args, **kwargs):
            if error_type == "ConnectionError":
                raise httpx.ConnectError("Connection failed")
            elif error_type == "DNSError":
                raise httpx.ConnectError("DNS resolution failed")
            else:
                raise httpx.RequestError("Network error")
        
        mock_client = Mock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        for method in ["get", "post", "put", "delete"]:
            setattr(mock_client, method, AsyncMock(side_effect=error_method))
        
        return mock_client
    
    @staticmethod
    def create_rate_limited_client(limit_after: int = 3):
        """创建限流客户端"""
        request_count = {"count": 0}
        
        async def rate_limited_method(*args, **kwargs):
            request_count["count"] += 1
            if request_count["count"] > limit_after:
                # 模拟 429 Too Many Requests
                response_mock = Mock()
                response_mock.status_code = 429
                raise httpx.HTTPStatusError(
                    "429 Too Many Requests",
                    request=None,
                    response=response_mock
                )
            
            # 正常响应
            response_mock = Mock()
            response_mock.status_code = 200
            response_mock.json = AsyncMock(return_value={"success": True})
            return response_mock
        
        mock_client = Mock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        for method in ["get", "post", "put", "delete"]:
            setattr(mock_client, method, AsyncMock(side_effect=rate_limited_method))
        
        return mock_client


# 预定义的 Mock 服务器配置
MOCK_SERVER_CONFIGS = {
    "healthy_agent": {
        "invocation_response": {
            "result": "Healthy agent response",
            "status": "success",
            "duration": 0.1
        },
        "ping_response": {
            "status": "Healthy",
            "timestamp": "2024-01-01T00:00:00Z"
        }
    },
    "slow_agent": {
        "invocation_response": {
            "result": "Slow agent response",
            "status": "success", 
            "duration": 2.0
        },
        "invocation_delay": 2.0
    },
    "error_agent": {
        "error_responses": {
            "/invocations": {
                "status_code": 500,
                "message": "Internal server error"
            }
        }
    }
}