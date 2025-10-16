# PPIO Agent Runtime - HTTP Server Implementation
# Copyright (c) 2024 PPIO
# Licensed under the MIT License

"""HTTP server implementation for PPIO Agent Runtime based on Starlette."""

import asyncio
import inspect
import json
import logging
import time
import traceback
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Union, AsyncGenerator, Generator

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse, StreamingResponse
from starlette.routing import Route
import uvicorn

from .models import RuntimeConfig, InvocationRequest, InvocationResponse, PingResponse, PingStatus
from .context import RequestContext, AgentRuntimeContext


logger = logging.getLogger(__name__)


class AgentRuntimeServer:
    """Agent Runtime 服务器"""
    
    def __init__(self, config: RuntimeConfig):
        """初始化服务器
        
        Args:
            config: 运行时配置
        """
        self.config = config
        self._entrypoint_func: Optional[Callable] = None
        self._ping_func: Optional[Callable] = None
        self._middlewares: List[Callable] = []
        self._app: Optional[Starlette] = None
        
        self._setup_app()
    
    def set_entrypoint_handler(self, func: Callable) -> None:
        """设置入口点处理函数"""
        self._entrypoint_func = func
        logger.info(f"Entrypoint handler set: {func.__name__}")
    
    def set_ping_handler(self, func: Optional[Callable]) -> None:
        """设置健康检查处理函数"""
        self._ping_func = func
        if func:
            logger.info(f"Ping handler set: {func.__name__}")
    
    def add_middleware(self, middleware_func: Callable) -> None:
        """添加中间件"""
        self._middlewares.append(middleware_func)
        logger.info(f"Middleware added: {middleware_func.__name__}")
    
    def run(self, port: int, host: str) -> None:
        """启动服务器"""
        logger.info(f"Starting Agent Runtime server on {host}:{port}")
        uvicorn.run(
            self._app,
            host=host,
            port=port,
            log_level="info" if self.config.debug else "warning",
            access_log=self.config.debug
        )
    
    def _setup_app(self) -> None:
        """设置 Starlette 应用"""
        middleware = []
        
        # CORS 中间件
        if self.config.cors_origins:
            middleware.append(
                Middleware(
                    CORSMiddleware,
                    allow_origins=self.config.cors_origins,
                    allow_methods=["GET", "POST", "OPTIONS"],
                    allow_headers=["*"],
                )
            )
        
        # 路由
        routes = [
            Route("/", self._handle_root, methods=["GET"]),
            Route("/ping", self._handle_ping, methods=["GET"]),
            Route("/invocations", self._handle_invocations, methods=["POST"]),
        ]
        
        self._app = Starlette(
            debug=self.config.debug,
            routes=routes,
            middleware=middleware
        )
    
    async def _handle_root(self, request: Request) -> JSONResponse:
        """处理根端点"""
        return JSONResponse({
            "service": "PPIO Agent Runtime",
            "status": "running",
            "timestamp": datetime.now().isoformat(),
            "endpoints": {
                "invocations": "/invocations",
                "ping": "/ping"
            }
        })
    
    async def _handle_ping(self, request: Request) -> JSONResponse:
        """处理 /ping 端点"""
        try:
            if self._ping_func:
                # 调用自定义健康检查函数
                if inspect.iscoroutinefunction(self._ping_func):
                    result = await self._ping_func()
                else:
                    result = self._ping_func()
                
                if isinstance(result, dict):
                    response = PingResponse(**result)
                elif isinstance(result, PingResponse):
                    response = result
                else:
                    response = PingResponse(
                        status=PingStatus.HEALTHY,
                        message=str(result) if result else None,
                        timestamp=datetime.now().isoformat()
                    )
            else:
                response = PingResponse(
                    status=PingStatus.HEALTHY,
                    timestamp=datetime.now().isoformat()
                )
            
            return JSONResponse(response.dict())
            
        except Exception as e:
            logger.error(f"Ping function error: {e}")
            error_response = PingResponse(
                status=PingStatus.HEALTHY_BUSY,
                message=f"Health check error: {str(e)}",
                timestamp=datetime.now().isoformat()
            )
            return JSONResponse(error_response.dict(), status_code=500)
    
    async def _handle_invocations(self, request: Request) -> Response:
        """处理 /invocations 端点"""
        start_time = time.time()
        context = None
        
        try:
            # 检查请求大小
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > self.config.max_request_size:
                return JSONResponse(
                    {"error": f"Request too large: {content_length} bytes"},
                    status_code=413
                )
            
            # 解析请求体
            try:
                request_data = await request.json()
            except Exception as e:
                return JSONResponse(
                    {"error": f"Invalid JSON: {str(e)}"},
                    status_code=400
                )
            
            # 创建调用请求
            invoke_request = InvocationRequest(**request_data)
            
            # 创建请求上下文
            context = RequestContext(
                sandbox_id=invoke_request.sandbox_id,
                request_id=str(uuid.uuid4()),
                headers=dict(request.headers)
            )
            
            # 设置上下文
            AgentRuntimeContext.set_current_context(context)
            
            try:
                # 执行中间件
                for middleware in self._middlewares:
                    if inspect.iscoroutinefunction(middleware):
                        await middleware(request, self._call_next_placeholder)
                    else:
                        middleware(request, self._call_next_placeholder)
                
                # 执行 Agent 函数
                result = await self._execute_agent_function(invoke_request, context)
                
                # 处理流式响应
                if invoke_request.stream and self._is_streaming_result(result):
                    return await self._create_streaming_response(result)
                
                # 创建普通响应
                duration = time.time() - start_time
                response = InvocationResponse(
                    result=result,
                    status="success",
                    duration=duration,
                    metadata={"request_id": context.request_id}
                )
                
                return JSONResponse(response.dict())
                
            finally:
                # 清除上下文
                AgentRuntimeContext.clear_current_context()
                
        except Exception as e:
            logger.error(f"Invocation error: {e}\n{traceback.format_exc()}")
            duration = time.time() - start_time
            error_response = InvocationResponse(
                result=None,
                status="error",
                duration=duration,
                error=str(e),
                metadata={"request_id": context.request_id if context else None}
            )
            return JSONResponse(error_response.dict(), status_code=500)
    
    async def _execute_agent_function(self, request: InvocationRequest, context: RequestContext) -> Any:
        """执行 Agent 函数"""
        if not self._entrypoint_func:
            raise RuntimeError("No entrypoint function registered")
        
        # 准备函数参数
        func_signature = inspect.signature(self._entrypoint_func)
        params = list(func_signature.parameters.keys())
        
        # 根据函数签名决定传递参数
        if len(params) >= 2:
            # 函数接受 request 和 context 参数
            args = (request.dict(), context)
        else:
            # 函数只接受 request 参数
            args = (request.dict(),)
        
        # 执行函数
        if inspect.iscoroutinefunction(self._entrypoint_func):
            return await self._entrypoint_func(*args)
        else:
            # 在线程池中执行同步函数
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._entrypoint_func, *args)
    
    def _is_streaming_result(self, result: Any) -> bool:
        """检查结果是否为流式结果"""
        return (
            hasattr(result, '__iter__') or 
            hasattr(result, '__aiter__') or
            inspect.isgenerator(result) or
            inspect.isasyncgen(result)
        )
    
    async def _create_streaming_response(self, result: Any) -> StreamingResponse:
        """创建流式响应"""
        async def stream_generator():
            try:
                if inspect.isasyncgen(result):
                    # 异步生成器
                    async for chunk in result:
                        yield f"data: {json.dumps(str(chunk))}\n\n"
                elif inspect.isgenerator(result):
                    # 同步生成器
                    for chunk in result:
                        yield f"data: {json.dumps(str(chunk))}\n\n"
                elif hasattr(result, '__aiter__'):
                    # 异步迭代器
                    async for chunk in result:
                        yield f"data: {json.dumps(str(chunk))}\n\n"
                else:
                    # 普通迭代器
                    for chunk in result:
                        yield f"data: {json.dumps(str(chunk))}\n\n"
            except Exception as e:
                logger.error(f"Streaming error: {e}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        return StreamingResponse(
            stream_generator(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )
    
    def _call_next_placeholder(self, request: Request):
        """中间件调用占位符"""
        # 这个函数在实际的中间件系统中会被替换
        pass
