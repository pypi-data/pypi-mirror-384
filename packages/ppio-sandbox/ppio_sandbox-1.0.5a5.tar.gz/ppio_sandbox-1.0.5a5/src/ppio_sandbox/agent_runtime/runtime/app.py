# PPIO Agent Runtime - Main Application Class
# Copyright (c) 2024 PPIO
# Licensed under the MIT License

"""Main application class for PPIO Agent Runtime."""

import asyncio
import logging
from typing import Callable, Optional

from .context import RequestContext, AgentRuntimeContext
from .models import RuntimeConfig
from .server import AgentRuntimeServer


logger = logging.getLogger(__name__)


class AgentRuntimeApp:
    """PPIO Agent Runtime 应用类"""
    
    def __init__(
        self, 
        config: Optional[RuntimeConfig] = None, 
        debug: bool = False
    ) -> None:
        """初始化应用
        
        Args:
            config: 运行时配置，如果不提供则使用默认配置
            debug: 启用调试模式（向后兼容）
        """
        self.config = config or RuntimeConfig()
        if debug:
            self.config.debug = True
        
        self._server: Optional[AgentRuntimeServer] = None
        self._entrypoint_func: Optional[Callable] = None
        self._ping_func: Optional[Callable] = None
        
        logger.info("Agent Runtime App initialized")
    
    def entrypoint(self, func: Callable) -> Callable:
        """注册主入口点函数 - 核心装饰器
        
        支持的函数签名：
        - func(request: dict) -> Any
        - func(request: dict, context: RequestContext) -> Any
        - async func(request: dict) -> Any
        - async func(request: dict, context: RequestContext) -> Any
        
        支持的返回类型：
        - 基础类型：str, dict, list, int, float, bool
        - 生成器：Generator[str, None, None] (同步流式)
        - 异步生成器：AsyncGenerator[str, None] (异步流式)
        
        Args:
            func: 要注册的函数
            
        Returns:
            装饰后的函数
        """
        self._entrypoint_func = func
        logger.info(f"Entrypoint function registered: {func.__name__}")
        return func
    
    def ping(self, func: Callable) -> Callable:
        """注册自定义健康检查函数（可选）
        
        支持的函数签名：
        - func() -> PingStatus
        - func() -> dict
        - async func() -> PingStatus
        - async func() -> dict
        
        Args:
            func: 健康检查函数
            
        Returns:
            装饰后的函数
        """
        self._ping_func = func
        logger.info(f"Ping function registered: {func.__name__}")
        return func
    
    def middleware(self, middleware_func: Callable) -> Callable:
        """注册中间件函数
        
        中间件函数签名：
        - async func(request: Request, call_next: Callable) -> Response
        
        Args:
            middleware_func: 中间件函数
            
        Returns:
            装饰后的函数
        """
        if not self._server:
            self._server = AgentRuntimeServer(self.config)
        
        self._server.add_middleware(middleware_func)
        logger.info(f"Middleware registered: {middleware_func.__name__}")
        return middleware_func
    
    def run(
        self, 
        port: Optional[int] = None, 
        host: Optional[str] = None
    ) -> None:
        """启动服务器
        
        Args:
            port: 端口号，如果不提供则使用配置中的端口（默认8080）
            host: 主机地址，如果不提供则使用配置中的地址（默认0.0.0.0）
        """
        # 更新配置
        if port is not None:
            self.config.port = port
        if host is not None:
            self.config.host = host
        
        # 检查是否注册了入口点函数
        if not self._entrypoint_func:
            raise RuntimeError("No entrypoint function registered. Use @app.entrypoint decorator.")
        
        # 创建和配置服务器
        self._server = AgentRuntimeServer(self.config)
        self._server.set_entrypoint_handler(self._entrypoint_func)
        
        if self._ping_func:
            self._server.set_ping_handler(self._ping_func)
        
        # 启动服务器
        self._server.run(self.config.port, self.config.host)
    
    @property
    def context(self) -> Optional[RequestContext]:
        """获取当前请求上下文"""
        return AgentRuntimeContext.get_current_context()
