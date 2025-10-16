"""
AgentRuntimeClient 单元测试

测试客户端主类的功能
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

from ppio_sandbox.agent_runtime.client.client import AgentRuntimeClient
from ppio_sandbox.agent_runtime.client.auth import AuthManager
from ppio_sandbox.agent_runtime.client.models import (
    ClientConfig,
    SandboxConfig,
    InvocationRequest,
    InvocationResponse,
    SessionStatus
)
from ppio_sandbox.agent_runtime.client.exceptions import (
    AuthenticationError,
    SandboxCreationError,
    SessionNotFoundError,
    TemplateNotFoundError,
    InvocationError
)

from ..mocks.mock_sandbox import MockAsyncSandbox
from ..mocks.test_fixtures import create_sample_template


class TestAgentRuntimeClientInit:
    """AgentRuntimeClient 初始化测试"""
    
    @pytest.mark.unit
    def test_client_init_with_api_key(self, test_api_key: str):
        """测试使用 API Key 初始化"""
        client = AgentRuntimeClient(api_key=test_api_key)
        
        assert client.auth_manager.api_key == test_api_key
        assert isinstance(client.config, ClientConfig)
        assert client.template_manager is not None
        assert client._sessions == {}
        assert client._closed is False
    
    @pytest.mark.unit
    def test_client_init_with_config(self, test_api_key: str, client_config: ClientConfig):
        """测试使用配置初始化"""
        client = AgentRuntimeClient(
            api_key=test_api_key,
            config=client_config
        )
        
        assert client.config is client_config
        assert client.config.base_url == "https://api.test.ppio.ai"
        assert client.config.timeout == 30
    
    @pytest.mark.unit
    def test_client_init_with_base_url(self, test_api_key: str):
        """测试使用基础 URL 初始化"""
        base_url = "https://custom.api.com"
        client = AgentRuntimeClient(
            api_key=test_api_key,
            base_url=base_url
        )
        
        assert client.config.base_url == base_url
    
    @pytest.mark.unit
    def test_client_init_from_env(self, test_api_key: str):
        """测试从环境变量初始化"""
        with patch.dict('os.environ', {'PPIO_API_KEY': test_api_key}):
            client = AgentRuntimeClient()
            assert client.auth_manager.api_key == test_api_key
    
    @pytest.mark.unit
    def test_client_init_without_api_key(self):
        """测试没有 API Key 时初始化失败"""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(AuthenticationError):
                AgentRuntimeClient()


class TestAgentRuntimeClientSessionManagement:
    """AgentRuntimeClient 会话管理测试"""
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_session_success(self, test_api_key: str, sample_template):
        """测试成功创建会话"""
        client = AgentRuntimeClient(api_key=test_api_key)
        
        # Mock template_manager
        with patch.object(client.template_manager, 'template_exists', return_value=True):
            with patch.object(client, '_create_sandbox_instance') as mock_create:
                mock_sandbox = MockAsyncSandbox()
                mock_create.return_value = mock_sandbox
                
                session = await client.create_session(sample_template.template_id)
        
        assert session.template_id == sample_template.template_id
        assert session.sandbox is mock_sandbox
        assert session.sandbox_id in client._sessions
        assert client._sessions[session.sandbox_id] is session
    
    @pytest.mark.unit
    @pytest.mark.asyncio

    async def test_create_session_template_not_found(self, test_api_key: str):
        """测试模板不存在时创建会话失败"""
        client = AgentRuntimeClient(api_key=test_api_key)
        
        with patch.object(client.template_manager, 'template_exists', return_value=False):
            with pytest.raises(TemplateNotFoundError) as exc_info:
                await client.create_session("non-existent-template")
        
        assert "not found" in str(exc_info.value)
    
    @pytest.mark.unit
    @pytest.mark.asyncio

    async def test_create_session_sandbox_creation_error(self, test_api_key: str, sample_template):
        """测试 Sandbox 创建失败"""
        client = AgentRuntimeClient(api_key=test_api_key)
        
        with patch.object(client.template_manager, 'template_exists', return_value=True):
            with patch.object(client, '_create_sandbox_instance', side_effect=Exception("Creation failed")):
                with pytest.raises(SandboxCreationError) as exc_info:
                    await client.create_session(sample_template.template_id)
        
        assert "Failed to create sandbox session" in str(exc_info.value)
    
    @pytest.mark.unit
    @pytest.mark.asyncio

    async def test_create_session_closed_client(self, test_api_key: str, sample_template):
        """测试关闭的客户端创建会话"""
        client = AgentRuntimeClient(api_key=test_api_key)
        client._closed = True
        
        with pytest.raises(RuntimeError) as exc_info:
            await client.create_session(sample_template.template_id)
        
        assert "Client is closed" in str(exc_info.value)
    
    @pytest.mark.unit
    @pytest.mark.asyncio

    async def test_get_session_existing(self, mock_sandbox_session):
        """测试获取现有会话"""
        client = AgentRuntimeClient(api_key="test-key")
        client._sessions[mock_sandbox_session.sandbox_id] = mock_sandbox_session
        
        session = await client.get_session(mock_sandbox_session.sandbox_id)
        
        assert session is mock_sandbox_session
    
    @pytest.mark.unit
    @pytest.mark.asyncio

    async def test_get_session_not_found(self, test_api_key: str):
        """测试获取不存在的会话"""
        client = AgentRuntimeClient(api_key=test_api_key)
        
        session = await client.get_session("non-existent-session")
        
        assert session is None
    
    @pytest.mark.unit
    @pytest.mark.asyncio

    async def test_list_sessions(self, test_api_key: str, mock_sandbox_session):
        """测试列出会话"""
        client = AgentRuntimeClient(api_key=test_api_key)
        client._sessions[mock_sandbox_session.sandbox_id] = mock_sandbox_session
        
        sessions = await client.list_sessions()
        
        assert len(sessions) == 1
        assert sessions[0] is mock_sandbox_session
    
    @pytest.mark.unit
    @pytest.mark.asyncio

    async def test_close_session_success(self, test_api_key: str, mock_sandbox_session):
        """测试成功关闭会话"""
        client = AgentRuntimeClient(api_key=test_api_key)
        client._sessions[mock_sandbox_session.sandbox_id] = mock_sandbox_session
        
        await client.close_session(mock_sandbox_session.sandbox_id)
        
        assert mock_sandbox_session.sandbox_id not in client._sessions
        mock_sandbox_session.close.assert_called_once()
    
    @pytest.mark.unit
    @pytest.mark.asyncio

    async def test_close_session_not_found(self, test_api_key: str):
        """测试关闭不存在的会话"""
        client = AgentRuntimeClient(api_key=test_api_key)
        
        with pytest.raises(SessionNotFoundError) as exc_info:
            await client.close_session("non-existent-session")
        
        assert "not found" in str(exc_info.value)
    
    @pytest.mark.unit
    @pytest.mark.asyncio

    async def test_close_all_sessions(self, test_api_key: str):
        """测试关闭所有会话"""
        client = AgentRuntimeClient(api_key=test_api_key)
        
        # 创建多个 mock 会话
        sessions = []
        for i in range(3):
            session = Mock()
            session.sandbox_id = f"session-{i}"
            session.close = AsyncMock()
            client._sessions[session.sandbox_id] = session
            sessions.append(session)
        
        await client.close_all_sessions()
        
        assert len(client._sessions) == 0
        for session in sessions:
            session.close.assert_called_once()


class TestAgentRuntimeClientTemplateManagement:
    """AgentRuntimeClient 模板管理测试"""
    
    @pytest.mark.unit
    @pytest.mark.asyncio

    async def test_list_templates(self, test_api_key: str, sample_templates):
        """测试列出模板"""
        client = AgentRuntimeClient(api_key=test_api_key)
        
        with patch.object(client.template_manager, 'list_templates', return_value=sample_templates):
            templates = await client.list_templates()
        
        assert templates is sample_templates
        client.template_manager.list_templates.assert_called_once_with(None, None)
    
    @pytest.mark.unit
    @pytest.mark.asyncio

    async def test_list_templates_with_filters(self, test_api_key: str, sample_templates):
        """测试带过滤条件列出模板"""
        client = AgentRuntimeClient(api_key=test_api_key)
        
        with patch.object(client.template_manager, 'list_templates', return_value=sample_templates):
            await client.list_templates(tags=["ai"], name_filter="test")
        
        client.template_manager.list_templates.assert_called_once_with(["ai"], "test")
    
    @pytest.mark.unit
    @pytest.mark.asyncio

    async def test_get_template(self, test_api_key: str, sample_template):
        """测试获取模板"""
        client = AgentRuntimeClient(api_key=test_api_key)
        
        with patch.object(client.template_manager, 'get_template', return_value=sample_template):
            template = await client.get_template(sample_template.template_id)
        
        assert template is sample_template
        client.template_manager.get_template.assert_called_once_with(sample_template.template_id)


class TestAgentRuntimeClientConvenienceMethods:
    """AgentRuntimeClient 便捷方法测试"""
    
    @pytest.mark.unit
    @pytest.mark.asyncio

    async def test_invoke_agent_create_session(self, test_api_key: str, sample_template):
        """测试自动创建会话调用 Agent"""
        client = AgentRuntimeClient(api_key=test_api_key)
        
        # Mock 创建会话
        mock_session = Mock()
        mock_session.sandbox_id = "auto-session"
        mock_session.invoke = AsyncMock(return_value={"result": "success"})
        mock_session.close = AsyncMock()
        
        with patch.object(client, 'create_session', return_value=mock_session):
            response = await client.invoke_agent(
                template_id=sample_template.template_id,
                request="test prompt"
            )
        
        assert isinstance(response, InvocationResponse)
        assert response.result["result"] == "success"
        assert response.status == "success"
        assert response.duration >= 0
        
        # 验证会话被自动关闭
        mock_session.close.assert_called_once()
    
    @pytest.mark.unit
    @pytest.mark.asyncio

    async def test_invoke_agent_existing_session(self, test_api_key: str, mock_sandbox_session):
        """测试使用现有会话调用 Agent"""
        client = AgentRuntimeClient(api_key=test_api_key)
        client._sessions[mock_sandbox_session.sandbox_id] = mock_sandbox_session
        
        with patch.object(client, 'get_session', return_value=mock_sandbox_session):
            response = await client.invoke_agent(
                template_id="any-template",
                request="test prompt",
                create_session=False,
                sandbox_id=mock_sandbox_session.sandbox_id
            )
        
        assert isinstance(response, InvocationResponse)
        mock_sandbox_session.invoke.assert_called_once()
    
    @pytest.mark.unit
    @pytest.mark.asyncio

    async def test_invoke_agent_session_not_found(self, test_api_key: str):
        """测试会话不存在时调用 Agent"""
        client = AgentRuntimeClient(api_key=test_api_key)
        
        with patch.object(client, 'get_session', return_value=None):
            with pytest.raises(SessionNotFoundError):
                await client.invoke_agent(
                    template_id="any-template",
                    request="test prompt",
                    create_session=False,
                    sandbox_id="non-existent"
                )
    
    @pytest.mark.unit
    @pytest.mark.asyncio

    async def test_invoke_agent_error_handling(self, test_api_key: str, sample_template):
        """测试调用 Agent 错误处理"""
        client = AgentRuntimeClient(api_key=test_api_key)
        
        # Mock 会话调用失败
        mock_session = Mock()
        mock_session.sandbox_id = "error-session"
        mock_session.invoke = AsyncMock(side_effect=Exception("Invocation failed"))
        mock_session.close = AsyncMock()
        
        with patch.object(client, 'create_session', return_value=mock_session):
            response = await client.invoke_agent(
                template_id=sample_template.template_id,
                request="test prompt"
            )
        
        assert response.status == "error"
        assert "Invocation failed" in response.error
        assert response.error_type == "Exception"
    
    @pytest.mark.unit
    @pytest.mark.asyncio

    async def test_invoke_agent_stream(self, test_api_key: str, sample_template):
        """测试流式调用 Agent"""
        client = AgentRuntimeClient(api_key=test_api_key)
        
        # Mock 流式响应
        async def mock_stream():
            for chunk in ["chunk1", "chunk2", "chunk3"]:
                yield chunk
        
        mock_session = Mock()
        mock_session.sandbox_id = "stream-session"
        mock_session.invoke = AsyncMock(return_value=mock_stream())
        mock_session.close = AsyncMock()
        
        with patch.object(client, 'create_session', return_value=mock_session):
            chunks = []
            async for chunk in await client.invoke_agent_stream(
                template_id=sample_template.template_id,
                request="test prompt"
            ):
                chunks.append(chunk)
        
        assert chunks == ["chunk1", "chunk2", "chunk3"]
        mock_session.close.assert_called_once()
    
    @pytest.mark.unit
    @pytest.mark.asyncio

    async def test_invoke_agent_invalid_parameters(self, test_api_key: str):
        """测试无效参数调用 Agent"""
        client = AgentRuntimeClient(api_key=test_api_key)
        
        with pytest.raises(ValueError) as exc_info:
            await client.invoke_agent(
                template_id="any-template",
                request="test prompt",
                create_session=False,  # 不创建会话
                sandbox_id=None        # 也不提供会话ID
            )
        
        assert "Either sandbox_id or create_session=True must be provided" in str(exc_info.value)


class TestAgentRuntimeClientContextManager:
    """AgentRuntimeClient 上下文管理器测试"""
    
    @pytest.mark.unit
    @pytest.mark.asyncio

    async def test_async_context_manager(self, test_api_key: str):
        """测试异步上下文管理器"""
        async with AgentRuntimeClient(api_key=test_api_key) as client:
            assert not client._closed
            assert isinstance(client, AgentRuntimeClient)
        
        # 退出后应该被关闭
        assert client._closed
    
    @pytest.mark.unit
    @pytest.mark.asyncio

    async def test_close_method(self, test_api_key: str):
        """测试关闭方法"""
        client = AgentRuntimeClient(api_key=test_api_key)
        
        # 添加一些会话
        mock_session = Mock()
        mock_session.close = AsyncMock()
        client._sessions["test-session"] = mock_session
        
        await client.close()
        
        assert client._closed is True
        assert len(client._sessions) == 0
        mock_session.close.assert_called_once()
    
    @pytest.mark.unit
    @pytest.mark.asyncio

    async def test_close_idempotent(self, test_api_key: str):
        """测试重复关闭"""
        client = AgentRuntimeClient(api_key=test_api_key)
        
        await client.close()
        assert client._closed is True
        
        # 再次关闭应该没有问题
        await client.close()
        assert client._closed is True


class TestAgentRuntimeClientSandboxCreation:
    """AgentRuntimeClient Sandbox 创建测试"""
    
    @pytest.mark.unit
    @pytest.mark.asyncio

    async def test_create_sandbox_instance_success(self, test_api_key: str, sandbox_config: SandboxConfig):
        """测试成功创建 Sandbox 实例"""
        client = AgentRuntimeClient(api_key=test_api_key)
        
        with patch('ppio_sandbox.core.AsyncSandbox') as mock_async_sandbox:
            mock_instance = MockAsyncSandbox()
            mock_async_sandbox.return_value = mock_instance
            
            sandbox = await client._create_sandbox_instance(
                template_id="test-template",
                timeout_seconds=300,
                config=sandbox_config
            )
        
        assert sandbox is mock_instance
        mock_async_sandbox.assert_called_once_with(
            template_id="test-template",
            api_key=test_api_key,
            timeout=300
        )
    
    @pytest.mark.unit
    @pytest.mark.asyncio

    async def test_create_sandbox_instance_error(self, test_api_key: str, sandbox_config: SandboxConfig):
        """测试创建 Sandbox 实例失败"""
        client = AgentRuntimeClient(api_key=test_api_key)
        
        with patch('ppio_sandbox.core.AsyncSandbox', side_effect=Exception("Creation failed")):
            with pytest.raises(SandboxCreationError) as exc_info:
                await client._create_sandbox_instance(
                    template_id="test-template",
                    timeout_seconds=300,
                    config=sandbox_config
                )
        
        assert "Failed to create sandbox instance" in str(exc_info.value)


class TestAgentRuntimeClientIntegration:
    """AgentRuntimeClient 集成测试"""
    
    @pytest.mark.unit
    async def test_client_lifecycle(self, test_api_key: str, sample_template):
        """测试客户端完整生命周期"""
        async with AgentRuntimeClient(api_key=test_api_key) as client:
            # 1. 验证初始状态
            assert not client._closed
            assert len(client._sessions) == 0
            
            # 2. Mock 模板存在
            with patch.object(client.template_manager, 'template_exists', return_value=True):
                with patch.object(client, '_create_sandbox_instance') as mock_create:
                    mock_sandbox = MockAsyncSandbox()
                    mock_create.return_value = mock_sandbox
                    
                    # 3. 创建会话
                    session = await client.create_session(sample_template.template_id)
                    assert len(client._sessions) == 1
                    
                    # 4. 列出会话
                    sessions = await client.list_sessions()
                    assert len(sessions) == 1
                    assert sessions[0] is session
                    
                    # 5. 获取会话
                    found_session = await client.get_session(session.sandbox_id)
                    assert found_session is session
                    
                    # 6. 关闭会话
                    await client.close_session(session.sandbox_id)
                    assert len(client._sessions) == 0
        
        # 7. 客户端应该被关闭
        assert client._closed
    
    @pytest.mark.unit
    @pytest.mark.asyncio

    async def test_concurrent_session_management(self, test_api_key: str, sample_templates):
        """测试并发会话管理"""
        client = AgentRuntimeClient(api_key=test_api_key)
        
        try:
            with patch.object(client.template_manager, 'template_exists', return_value=True):
                with patch.object(client, '_create_sandbox_instance') as mock_create:
                    # 创建多个 mock sandbox
                    mock_sandboxes = [MockAsyncSandbox() for _ in range(3)]
                    mock_create.side_effect = mock_sandboxes
                    
                    # 并发创建会话
                    tasks = [
                        client.create_session(template.template_id)
                        for template in sample_templates[:3]
                    ]
                    sessions = await asyncio.gather(*tasks)
                    
                    assert len(sessions) == 3
                    assert len(client._sessions) == 3
                    
                    # 并发关闭会话
                    close_tasks = [
                        client.close_session(session.sandbox_id)
                        for session in sessions
                    ]
                    await asyncio.gather(*close_tasks)
                    
                    assert len(client._sessions) == 0
        
        finally:
            await client.close()
    
    @pytest.mark.unit
    @pytest.mark.asyncio

    async def test_error_recovery(self, test_api_key: str, sample_template):
        """测试错误恢复"""
        client = AgentRuntimeClient(api_key=test_api_key)
        
        try:
            # 第一次创建失败
            with patch.object(client.template_manager, 'template_exists', return_value=True):
                with patch.object(client, '_create_sandbox_instance', side_effect=Exception("First failure")):
                    with pytest.raises(SandboxCreationError):
                        await client.create_session(sample_template.template_id)
            
            assert len(client._sessions) == 0
            
            # 第二次创建成功
            with patch.object(client.template_manager, 'template_exists', return_value=True):
                with patch.object(client, '_create_sandbox_instance') as mock_create:
                    mock_sandbox = MockAsyncSandbox()
                    mock_create.return_value = mock_sandbox
                    
                    session = await client.create_session(sample_template.template_id)
                    assert len(client._sessions) == 1
        
        finally:
            await client.close()
    
    @pytest.mark.unit
    def test_client_representation(self, test_api_key: str):
        """测试客户端字符串表示"""
        client = AgentRuntimeClient(api_key=test_api_key)
        
        repr_str = repr(client)
        assert "AgentRuntimeClient" in repr_str
        assert "sessions=0" in repr_str
        assert "closed=False" in repr_str
        
        client._closed = True
        repr_str = repr(client)
        assert "closed=True" in repr_str
