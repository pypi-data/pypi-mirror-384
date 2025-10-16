"""
Sandbox 会话管理

管理单个 Sandbox 实例的生命周期和 Agent 调用
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Any, AsyncIterator, Dict, Optional, Union
import httpx

from .exceptions import (
    InvocationError, 
    NetworkError, 
    SandboxOperationError, 
    SessionNotFoundError
)
from .models import InvocationRequest, PingResponse, SessionStatus


class SandboxSession:
    """Sandbox 会话管理"""
    
    def __init__(
        self,
        template_id: str,
        sandbox: Any,  # PPIO Sandbox 实例
        client: "AgentRuntimeClient"
    ):
        """初始化会话
        
        Args:
            template_id: 模板 ID
            sandbox: PPIO Sandbox 实例（一对一关系）
            client: Agent Runtime 客户端引用
        """
        self.template_id = template_id
        self.sandbox = sandbox
        self._client_ref = client  # 避免循环引用
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.status = SessionStatus.ACTIVE
        self._host_url: Optional[str] = None
        self._http_client: Optional[httpx.AsyncClient] = None
    
    async def _get_http_client(self) -> httpx.AsyncClient:
        """获取 HTTP 客户端"""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0),
                headers={"Content-Type": "application/json"}
            )
        return self._http_client
    
    async def _close_http_client(self):
        """关闭 HTTP 客户端"""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
    
    # === 核心调用方法 ===
    async def invoke(
        self,
        request: Union[InvocationRequest, Dict[str, Any], str],
        stream: bool = False
    ) -> Union[Dict[str, Any], AsyncIterator[str]]:
        """调用 Agent
        
        Args:
            request: 调用请求（支持多种格式）
            stream: 是否使用流式响应
            
        Returns:
            响应对象或流式迭代器
            
        Raises:
            InvocationError: 调用失败时抛出
            SessionNotFoundError: 会话不存在时抛出
            NetworkError: 网络错误时抛出
        """
        if self.status not in [SessionStatus.ACTIVE]:
            raise SessionNotFoundError(f"Session {self.sandbox_id} is not active (status: {self.status})")
        
        # 规范化请求格式
        if isinstance(request, str):
            request_data = InvocationRequest(prompt=request, stream=stream)
        elif isinstance(request, dict):
            request_data = InvocationRequest(**request)
            if stream:
                request_data.stream = stream
        elif isinstance(request, InvocationRequest):
            request_data = request
            if stream:
                request_data.stream = stream
        else:
            raise InvocationError("Invalid request format")
        
        # 设置 sandbox_id
        request_data.sandbox_id = self.sandbox_id
        
        try:
            self.last_activity = datetime.now()
            
            if request_data.stream:
                return await self._invoke_stream(request_data)
            else:
                return await self._invoke_sync(request_data)
                
        except Exception as e:
            if "connection" in str(e).lower() or "timeout" in str(e).lower():
                raise NetworkError(f"Network error during invocation: {str(e)}")
            else:
                raise InvocationError(f"Agent invocation failed: {str(e)}")
    
    async def _invoke_sync(self, request: InvocationRequest) -> Dict[str, Any]:
        """同步调用 Agent"""
        client = await self._get_http_client()
        
        response = await client.post(
            f"{self.host_url}/invocations",
            json=request.dict(exclude_unset=True),
            timeout=httpx.Timeout(request.timeout or 300)
        )
        
        if response.status_code != 200:
            raise InvocationError(f"Agent returned status {response.status_code}: {response.text}")
        
        return response.json()
    
    async def _invoke_stream(self, request: InvocationRequest) -> AsyncIterator[str]:
        """流式调用 Agent"""
        client = await self._get_http_client()
        
        async with client.stream(
            "POST",
            f"{self.host_url}/invocations", 
            json=request.dict(exclude_unset=True),
            timeout=httpx.Timeout(request.timeout or 300)
        ) as response:
            if response.status_code != 200:
                content = await response.aread()
                raise InvocationError(f"Agent returned status {response.status_code}: {content}")
            
            async for chunk in response.aiter_text():
                if chunk.strip():  # 跳过空行
                    yield chunk
    
    # === Sandbox 生命周期管理 ===
    async def pause(self) -> None:
        """暂停 Sandbox 实例
        
        暂停后：
        - Sandbox 进入休眠状态，保留内存状态
        - 停止 CPU 计算，节省资源
        - 可以通过 resume() 恢复执行
        
        Raises:
            SandboxOperationError: 暂停失败时抛出
        """
        try:
            if hasattr(self.sandbox, 'pause'):
                await self.sandbox.pause()
            else:
                # 如果 sandbox 没有 pause 方法，使用 API 调用
                await self._call_sandbox_api("pause")
            
            self.status = SessionStatus.PAUSED
            
        except Exception as e:
            raise SandboxOperationError(f"Failed to pause sandbox: {str(e)}")
    
    async def resume(self) -> None:
        """恢复 Sandbox 实例
        
        恢复后：
        - Sandbox 从暂停状态恢复
        - 保持之前的内存状态和上下文
        - 可以继续处理请求
        
        Raises:
            SandboxOperationError: 恢复失败时抛出
        """
        try:
            if hasattr(self.sandbox, 'resume'):
                await self.sandbox.resume()
            else:
                # 如果 sandbox 没有 resume 方法，使用 API 调用
                await self._call_sandbox_api("resume")
            
            self.status = SessionStatus.ACTIVE
            
        except Exception as e:
            raise SandboxOperationError(f"Failed to resume sandbox: {str(e)}")
    
    async def _call_sandbox_api(self, action: str) -> None:
        """调用 Sandbox API 执行操作"""
        # 这里需要根据实际的 Sandbox API 来实现
        # 暂时使用模拟实现
        pass
    
    # === 会话管理 ===
    async def ping(self) -> PingResponse:
        """健康检查
        
        Returns:
            健康检查响应
            
        Raises:
            NetworkError: 网络错误时抛出
            InvocationError: 检查失败时抛出
        """
        try:
            client = await self._get_http_client()
            
            response = await client.get(
                f"{self.host_url}/ping",
                timeout=httpx.Timeout(10.0)
            )
            
            if response.status_code == 200:
                data = response.json()
                return PingResponse(
                    status=data.get("status", "healthy"),
                    message=data.get("message"),
                    timestamp=data.get("timestamp", datetime.now().isoformat())
                )
            else:
                return PingResponse(
                    status="unhealthy",
                    message=f"HTTP {response.status_code}: {response.text}",
                    timestamp=datetime.now().isoformat()
                )
                
        except Exception as e:
            if "connection" in str(e).lower() or "timeout" in str(e).lower():
                raise NetworkError(f"Network error during ping: {str(e)}")
            else:
                raise InvocationError(f"Ping failed: {str(e)}")
    
    async def get_status(self) -> SessionStatus:
        """获取会话状态
        
        Returns:
            会话状态（ACTIVE, PAUSED, INACTIVE, CLOSED, ERROR）
        """
        # 可以添加实际的状态检查逻辑
        try:
            # 尝试 ping 来确认状态
            ping_response = await self.ping()
            if ping_response.status in ["healthy", "HealthyBusy"]:
                if self.status == SessionStatus.PAUSED:
                    return SessionStatus.PAUSED
                else:
                    return SessionStatus.ACTIVE
            else:
                return SessionStatus.ERROR
        except Exception:
            return SessionStatus.ERROR
    
    async def refresh(self) -> None:
        """刷新会话（重置超时时间）"""
        self.last_activity = datetime.now()
        # 可以添加实际的刷新逻辑，比如向 Sandbox 发送 keepalive 信号
    
    async def close(self) -> None:
        """关闭会话并销毁 Sandbox
        
        执行步骤：
        1. 停止 Agent 服务
        2. 销毁 Sandbox 实例
        3. 释放所有资源
        4. 更新会话状态为 CLOSED
        """
        try:
            # 关闭 HTTP 客户端
            await self._close_http_client()
            
            # 销毁 Sandbox 实例
            if hasattr(self.sandbox, 'close'):
                await self.sandbox.close()
            elif hasattr(self.sandbox, 'kill'):
                await self.sandbox.kill()
            
            self.status = SessionStatus.CLOSED
            
        except Exception as e:
            self.status = SessionStatus.ERROR
            raise SandboxOperationError(f"Failed to close session: {str(e)}")
    
    # === 属性 ===
    @property
    def host_url(self) -> str:
        """获取 Sandbox 主机 URL"""
        if not self._host_url:
            if self.sandbox and hasattr(self.sandbox, 'get_host'):
                # 使用实际的 Sandbox API
                host = self.sandbox.get_host(8080)
                self._host_url = f"https://{host}"
            else:
                # 模拟 URL（用于测试）
                self._host_url = f"https://session-{self.sandbox_id}.ppio.sandbox"
        return self._host_url
    
    @property
    def is_active(self) -> bool:
        """检查会话是否活跃"""
        return self.status == SessionStatus.ACTIVE
    
    @property
    def is_paused(self) -> bool:
        """检查会话是否已暂停"""
        return self.status == SessionStatus.PAUSED
    
    @property
    def sandbox_id(self) -> str:
        """获取 Sandbox 实例 ID（同时也是会话 ID）"""
        if hasattr(self.sandbox, 'id'):
            return self.sandbox.id
        elif hasattr(self.sandbox, 'sandbox_id'):
            return self.sandbox.sandbox_id
        else:
            return f"sandbox-{id(self.sandbox)}"
    
    @property
    def session_id(self) -> str:
        """获取会话 ID（等同于 sandbox_id）"""
        return self.sandbox_id
    
    @property
    def age_seconds(self) -> float:
        """获取会话存在时间（秒）"""
        return (datetime.now() - self.created_at).total_seconds()
    
    @property
    def idle_seconds(self) -> float:
        """获取会话空闲时间（秒）"""
        return (datetime.now() - self.last_activity).total_seconds()
    
    def __repr__(self) -> str:
        return f"SandboxSession(id={self.sandbox_id}, status={self.status}, template={self.template_id})"