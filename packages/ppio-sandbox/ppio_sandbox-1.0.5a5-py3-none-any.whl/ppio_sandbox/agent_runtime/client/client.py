"""
Agent Runtime 客户端

面向后端开发者的客户端，管理 Sandbox 会话和 Agent 调用
"""

import asyncio
import os
from typing import Any, AsyncIterator, Dict, List, Optional, Union

from ppio_sandbox.core import AsyncSandbox  # 导入现有的异步 Sandbox 功能
from .auth import AuthManager
from .exceptions import (
    AuthenticationError,
    InvocationError,
    SessionNotFoundError,
    SandboxCreationError,
    TemplateNotFoundError
)
from .models import (
    AgentTemplate,
    ClientConfig,
    InvocationRequest,
    InvocationResponse,
    SandboxConfig
)
from .session import SandboxSession
from .template import TemplateManager


class AgentRuntimeClient:
    """Agent Runtime 客户端"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 300,
        config: Optional[ClientConfig] = None
    ):
        """初始化客户端
        
        Args:
            api_key: API 密钥，如果不提供则从环境变量 PPIO_API_KEY 读取
            base_url: Sandbox 平台基础 URL，如果不提供则从环境变量
            timeout: 默认超时时间
            config: 客户端配置
            
        Environment Variables:
            PPIO_API_KEY: API 密钥
            
        Raises:
            AuthenticationError: API Key 未提供且环境变量不存在时抛出
        """
        # 设置配置
        self.config = config or ClientConfig(
            base_url=base_url,
            timeout=timeout
        )
        
        # 初始化认证管理器
        self.auth_manager = AuthManager(api_key)
        
        # 初始化模板管理器
        self.template_manager = TemplateManager(
            self.auth_manager, 
            self.config.base_url
        )
        
        # 会话管理
        self._sessions: Dict[str, SandboxSession] = {}
        self._closed = False
    
    # === 会话管理 ===
    async def create_session(
        self,
        template_id: str,
        timeout_seconds: int = 300,
        config: Optional[SandboxConfig] = None
    ) -> SandboxSession:
        """创建新的 Sandbox 会话
        
        每次调用都会：
        1. 从模板创建一个新的 Sandbox 实例
        2. 在 Sandbox 中启动 Agent 服务
        3. 返回对应的 SandboxSession 对象
        
        Args:
            template_id: Agent 模板 ID
            timeout_seconds: 会话超时时间
            config: Sandbox 配置
            
        Returns:
            SandboxSession 对象
            
        Raises:
            SandboxCreationError: 创建失败时抛出
            AuthenticationError: 认证失败时抛出
            TemplateNotFoundError: 模板不存在时抛出
        """
        if self._closed:
            raise RuntimeError("Client is closed")
        
        try:
            # 验证模板是否存在
            if not await self.template_manager.template_exists(template_id):
                raise TemplateNotFoundError(f"Template {template_id} not found")
            
            # 准备 Sandbox 配置
            sandbox_config = config or SandboxConfig()
            
            # 创建 Sandbox 实例
            # 这里需要根据实际的 Sandbox API 来调整
            sandbox = await self._create_sandbox_instance(
                template_id=template_id,
                timeout_seconds=timeout_seconds,
                config=sandbox_config
            )
            
            # 创建会话
            session = SandboxSession(
                template_id=template_id,
                sandbox=sandbox,
                client=self
            )
            
            # 注册会话
            self._sessions[session.sandbox_id] = session
            
            return session
            
        except TemplateNotFoundError:
            raise
        except AuthenticationError:
            raise
        except Exception as e:
            raise SandboxCreationError(f"Failed to create sandbox session: {str(e)}")
    
    async def _create_sandbox_instance(
        self,
        template_id: str,
        timeout_seconds: int,
        config: SandboxConfig
    ) -> Any:
        """创建 Sandbox 实例"""
        try:
            # 使用现有的异步 Sandbox 类创建实例
            # 这里需要根据实际的 ppio-sandbox 核心 API 来实现
            sandbox = AsyncSandbox(
                template_id=template_id,
                api_key=self.auth_manager.api_key,
                timeout=timeout_seconds
            )
            
            # 启动 Sandbox (根据实际 API 调整)
            # await sandbox.start()
            
            return sandbox
            
        except Exception as e:
            raise SandboxCreationError(f"Failed to create sandbox instance: {str(e)}")
    
    async def get_session(self, sandbox_id: str) -> Optional[SandboxSession]:
        """获取现有会话
        
        Args:
            sandbox_id: Sandbox/会话 ID
            
        Returns:
            会话对象，如果不存在则返回 None
        """
        return self._sessions.get(sandbox_id)
    
    async def list_sessions(self) -> List[SandboxSession]:
        """列出所有活跃会话
        
        Returns:
            会话列表
        """
        return list(self._sessions.values())
    
    async def close_session(self, sandbox_id: str) -> None:
        """关闭指定会话
        
        Args:
            sandbox_id: Sandbox/会话 ID
            
        Raises:
            SessionNotFoundError: 会话不存在时抛出
        """
        session = self._sessions.get(sandbox_id)
        if not session:
            raise SessionNotFoundError(f"Session {sandbox_id} not found")
        
        try:
            await session.close()
        finally:
            # 从会话列表中移除
            self._sessions.pop(sandbox_id, None)
    
    async def close_all_sessions(self) -> None:
        """关闭所有会话"""
        sessions = list(self._sessions.values())
        self._sessions.clear()
        
        # 并发关闭所有会话
        if sessions:
            await asyncio.gather(
                *[session.close() for session in sessions],
                return_exceptions=True
            )
    
    # === 模板管理 ===
    async def list_templates(
        self, 
        tags: Optional[List[str]] = None,
        name_filter: Optional[str] = None
    ) -> List[AgentTemplate]:
        """列出可用的 Agent 模板
        
        Args:
            tags: 标签过滤
            name_filter: 名称过滤
        
        Returns:
            模板列表
        """
        return await self.template_manager.list_templates(tags, name_filter)
    
    async def get_template(self, template_id: str) -> AgentTemplate:
        """获取特定模板信息
        
        Args:
            template_id: 模板 ID
            
        Returns:
            模板对象
            
        Raises:
            TemplateNotFoundError: 模板不存在时抛出
        """
        return await self.template_manager.get_template(template_id)
    
    # === 便捷调用方法 ===
    async def invoke_agent(
        self,
        template_id: str,
        request: Union[InvocationRequest, Dict[str, Any], str],
        create_session: bool = True,
        sandbox_id: Optional[str] = None,
        timeout: Optional[int] = None
    ) -> InvocationResponse:
        """便捷方法：直接调用 Agent（自动管理会话）
        
        Args:
            template_id: 模板 ID
            request: 调用请求（支持多种格式）
            create_session: 是否自动创建新会话
            sandbox_id: 指定使用的 Sandbox/会话 ID
            timeout: 调用超时时间
            
        Returns:
            调用响应
            
        Raises:
            SessionNotFoundError: 指定会话不存在时抛出
            InvocationError: 调用失败时抛出
        """
        import time
        start_time = time.time()
        
        # 获取或创建会话
        if sandbox_id:
            session = await self.get_session(sandbox_id)
            if not session:
                raise SessionNotFoundError(f"Session {sandbox_id} not found")
        elif create_session:
            session = await self.create_session(template_id, timeout or self.config.timeout)
        else:
            raise ValueError("Either sandbox_id or create_session=True must be provided")
        
        try:
            # 调用 Agent
            result = await session.invoke(request)
            
            # 构造响应
            return InvocationResponse(
                result=result,
                status="success",
                duration=time.time() - start_time,
                metadata={
                    "sandbox_id": session.sandbox_id,
                    "template_id": template_id
                }
            )
            
        except Exception as e:
            return InvocationResponse(
                result=None,
                status="error",
                duration=time.time() - start_time,
                error=str(e),
                error_type=type(e).__name__,
                metadata={
                    "sandbox_id": session.sandbox_id if 'session' in locals() else None,
                    "template_id": template_id
                }
            )
        finally:
            # 如果是自动创建的会话，调用完成后关闭
            if create_session and not sandbox_id and 'session' in locals():
                try:
                    await session.close()
                    self._sessions.pop(session.sandbox_id, None)
                except Exception:
                    pass  # 忽略关闭错误
    
    async def invoke_agent_stream(
        self,
        template_id: str,
        request: Union[InvocationRequest, Dict[str, Any], str],
        create_session: bool = True,
        sandbox_id: Optional[str] = None
    ) -> AsyncIterator[str]:
        """便捷方法：流式调用 Agent
        
        Args:
            template_id: 模板 ID
            request: 调用请求
            create_session: 是否自动创建新会话
            sandbox_id: 指定使用的 Sandbox/会话 ID
            
        Yields:
            流式响应数据
        """
        # 获取或创建会话
        if sandbox_id:
            session = await self.get_session(sandbox_id)
            if not session:
                raise SessionNotFoundError(f"Session {sandbox_id} not found")
        elif create_session:
            session = await self.create_session(template_id)
        else:
            raise ValueError("Either sandbox_id or create_session=True must be provided")
        
        try:
            # 流式调用
            async for chunk in await session.invoke(request, stream=True):
                yield chunk
                
        finally:
            # 如果是自动创建的会话，调用完成后关闭
            if create_session and not sandbox_id:
                try:
                    await session.close()
                    self._sessions.pop(session.sandbox_id, None)
                except Exception:
                    pass  # 忽略关闭错误
    
    # === 上下文管理器支持 ===
    async def __aenter__(self) -> "AgentRuntimeClient":
        """异步上下文管理器入口"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """异步上下文管理器出口"""
        await self.close()
    
    async def close(self) -> None:
        """关闭客户端并清理资源"""
        if self._closed:
            return
        
        self._closed = True
        
        # 关闭所有会话
        await self.close_all_sessions()
        
        # 关闭模板管理器
        await self.template_manager.close()
    
    def __repr__(self) -> str:
        return f"AgentRuntimeClient(sessions={len(self._sessions)}, closed={self._closed})"