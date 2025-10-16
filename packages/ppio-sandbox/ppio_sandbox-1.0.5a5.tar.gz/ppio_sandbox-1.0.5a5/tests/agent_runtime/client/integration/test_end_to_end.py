"""
端到端集成测试

测试 Agent Runtime Client 的完整流程
"""

import pytest
import asyncio
from unittest.mock import patch, Mock, AsyncMock

from ppio_sandbox.agent_runtime.client import AgentRuntimeClient
from ppio_sandbox.agent_runtime.client.models import InvocationRequest, SessionStatus
from ppio_sandbox.agent_runtime.client.exceptions import (
    TemplateNotFoundError,
    SandboxCreationError,
    InvocationError
)

from ..mocks.mock_api import setup_template_responses, setup_agent_responses
from ..mocks.mock_sandbox import MockAsyncSandbox
from ..mocks.test_fixtures import create_sample_template


class TestEndToEndBasicFlow:
    """端到端基础流程测试"""
    
    @pytest.mark.integration
    async def test_complete_agent_invocation_flow(self, real_api_key):
        """测试完整的 Agent 调用流程"""
        if not real_api_key:
            pytest.skip("需要真实 API Key 进行集成测试")
        
        async with AgentRuntimeClient(api_key=real_api_key) as client:
            # 1. 列出可用模板
            templates = await client.list_templates()
            assert len(templates) > 0
            
            # 选择第一个模板
            template = templates[0]
            
            # 2. 创建会话
            session = await client.create_session(template.template_id)
            assert session.status == SessionStatus.ACTIVE
            
            try:
                # 3. 调用 Agent
                response = await session.invoke("Hello, this is a test message")
                assert response is not None
                
                # 4. 检查会话状态
                status = await session.get_status()
                assert status in [SessionStatus.ACTIVE, SessionStatus.PAUSED]
                
                # 5. 测试健康检查
                ping_response = await session.ping()
                assert ping_response.status in ["healthy", "busy"]
                
            finally:
                # 6. 清理会话
                await session.close()
                assert session.status == SessionStatus.CLOSED
    
    @pytest.mark.integration
    @pytest.mark.network
    async def test_mock_complete_flow(self, test_api_key: str):
        """使用 Mock 的完整流程测试"""
        # 使用 aioresponses 模拟 HTTP 请求
        from aioresponses import aioresponses
        
        with aioresponses() as mock_http:
            # 设置模板响应
            setup_template_responses(mock_http)
            setup_agent_responses(mock_http)
            
            async with AgentRuntimeClient(api_key=test_api_key) as client:
                # Mock sandbox 创建
                with patch.object(client, '_create_sandbox_instance') as mock_create:
                    mock_sandbox = MockAsyncSandbox()
                    mock_create.return_value = mock_sandbox
                    
                    # 1. 获取模板
                    template = await client.get_template("test-template-123")
                    assert template.template_id == "test-template-123"
                    
                    # 2. 创建会话
                    session = await client.create_session(template.template_id)
                    assert session.template_id == template.template_id
                    
                    # 3. 执行调用
                    with patch.object(session, '_get_http_client') as mock_http_client:
                        mock_client = AsyncMock()
                        mock_response = Mock()
                        mock_response.status_code = 200
                        mock_response.json.return_value = {"result": "Mock response"}
                        mock_client.post.return_value = mock_response
                        mock_http_client.return_value = mock_client
                        
                        result = await session.invoke("Test prompt")
                        assert result["result"] == "Mock response"
                    
                    # 4. 关闭会话
                    await session.close()
                    assert session.status == SessionStatus.CLOSED
    
    @pytest.mark.integration
    async def test_convenience_method_flow(self, test_api_key: str):
        """测试便捷方法流程"""
        from aioresponses import aioresponses
        
        with aioresponses() as mock_http:
            setup_template_responses(mock_http)
            setup_agent_responses(mock_http)
            
            async with AgentRuntimeClient(api_key=test_api_key) as client:
                with patch.object(client, '_create_sandbox_instance') as mock_create:
                    mock_sandbox = MockAsyncSandbox()
                    mock_create.return_value = mock_sandbox
                    
                    # 使用便捷方法一次性完成调用
                    with patch.object(client, 'template_manager'):
                        client.template_manager.template_exists = AsyncMock(return_value=True)
                        
                        # Mock session invoke
                        with patch('ppio_sandbox.agent_runtime.client.session.SandboxSession') as mock_session_class:
                            mock_session = AsyncMock()
                            mock_session.sandbox_id = "mock-session"
                            mock_session.invoke.return_value = {"result": "convenience response"}
                            mock_session.close = AsyncMock()
                            mock_session_class.return_value = mock_session
                            
                            response = await client.invoke_agent(
                                template_id="test-template-123",
                                request="Test convenience call"
                            )
                            
                            assert response.status == "success"
                            assert response.result["result"] == "convenience response"


class TestEndToEndErrorHandling:
    """端到端错误处理测试"""
    
    @pytest.mark.integration
    async def test_template_not_found_flow(self, test_api_key: str):
        """测试模板不存在的错误流程"""
        from aioresponses import aioresponses
        
        with aioresponses() as mock_http:
            # 设置模板不存在的响应
            mock_http.get(
                "https://api.ppio.ai/v1/templates/agents/non-existent",
                status=404,
                payload={"error": "Template not found"}
            )
            
            async with AgentRuntimeClient(api_key=test_api_key) as client:
                # 尝试获取不存在的模板
                with pytest.raises(TemplateNotFoundError):
                    await client.get_template("non-existent")
                
                # 尝试创建基于不存在模板的会话
                with patch.object(client.template_manager, 'template_exists', return_value=False):
                    with pytest.raises(TemplateNotFoundError):
                        await client.create_session("non-existent")
    
    @pytest.mark.integration
    async def test_sandbox_creation_error_flow(self, test_api_key: str):
        """测试 Sandbox 创建错误流程"""
        async with AgentRuntimeClient(api_key=test_api_key) as client:
            with patch.object(client.template_manager, 'template_exists', return_value=True):
                with patch.object(client, '_create_sandbox_instance', side_effect=Exception("Sandbox creation failed")):
                    with pytest.raises(SandboxCreationError) as exc_info:
                        await client.create_session("test-template")
                    
                    assert "Failed to create sandbox session" in str(exc_info.value)
    
    @pytest.mark.integration
    async def test_invocation_error_flow(self, test_api_key: str):
        """测试调用错误流程"""
        async with AgentRuntimeClient(api_key=test_api_key) as client:
            with patch.object(client.template_manager, 'template_exists', return_value=True):
                with patch.object(client, '_create_sandbox_instance') as mock_create:
                    mock_sandbox = MockAsyncSandbox()
                    mock_create.return_value = mock_sandbox
                    
                    session = await client.create_session("test-template")
                    
                    # Mock HTTP 客户端返回错误
                    with patch.object(session, '_get_http_client') as mock_http_client:
                        mock_client = AsyncMock()
                        mock_response = Mock()
                        mock_response.status_code = 500
                        mock_response.text = "Internal Server Error"
                        mock_client.post.return_value = mock_response
                        mock_http_client.return_value = mock_client
                        
                        with pytest.raises(InvocationError) as exc_info:
                            await session.invoke("Test prompt")
                        
                        assert "HTTP request failed with status 500" in str(exc_info.value)
    
    @pytest.mark.integration
    async def test_network_error_recovery(self, test_api_key: str):
        """测试网络错误恢复"""
        from aioresponses import aioresponses
        
        async with AgentRuntimeClient(api_key=test_api_key) as client:
            # 第一次请求失败
            with aioresponses() as mock_http:
                mock_http.get(
                    "https://api.ppio.ai/v1/templates/agents",
                    exception=Exception("Network error")
                )
                
                with pytest.raises(Exception):
                    await client.list_templates()
            
            # 第二次请求成功
            with aioresponses() as mock_http:
                setup_template_responses(mock_http)
                
                templates = await client.list_templates()
                assert len(templates) > 0


class TestEndToEndStreamingFlow:
    """端到端流式处理测试"""
    
    @pytest.mark.integration
    async def test_streaming_invocation_flow(self, test_api_key: str):
        """测试流式调用流程"""
        async with AgentRuntimeClient(api_key=test_api_key) as client:
            with patch.object(client.template_manager, 'template_exists', return_value=True):
                with patch.object(client, '_create_sandbox_instance') as mock_create:
                    mock_sandbox = MockAsyncSandbox()
                    mock_create.return_value = mock_sandbox
                    
                    session = await client.create_session("test-template")
                    
                    # Mock 流式响应
                    async def mock_stream():
                        for i in range(5):
                            await asyncio.sleep(0.01)
                            yield f"Stream chunk {i}"
                    
                    with patch.object(session, '_get_http_client') as mock_http_client:
                        mock_client = AsyncMock()
                        mock_stream_response = Mock()
                        mock_stream_response.status_code = 200
                        mock_stream_response.aiter_text = mock_stream
                        mock_client.stream.return_value.__aenter__.return_value = mock_stream_response
                        mock_http_client.return_value = mock_client
                        
                        chunks = []
                        async for chunk in await session.invoke("Stream test", stream=True):
                            chunks.append(chunk)
                        
                        assert len(chunks) == 5
                        assert all("Stream chunk" in chunk for chunk in chunks)
    
    @pytest.mark.integration
    async def test_streaming_convenience_method(self, test_api_key: str):
        """测试流式便捷方法"""
        async with AgentRuntimeClient(api_key=test_api_key) as client:
            with patch.object(client.template_manager, 'template_exists', return_value=True):
                with patch.object(client, '_create_sandbox_instance') as mock_create:
                    mock_sandbox = MockAsyncSandbox()
                    mock_create.return_value = mock_sandbox
                    
                    # Mock session creation and streaming
                    with patch('ppio_sandbox.agent_runtime.client.session.SandboxSession') as mock_session_class:
                        async def mock_stream():
                            for i in range(3):
                                yield f"Convenience chunk {i}"
                        
                        mock_session = AsyncMock()
                        mock_session.sandbox_id = "convenience-session"
                        mock_session.invoke.return_value = mock_stream()
                        mock_session.close = AsyncMock()
                        mock_session_class.return_value = mock_session
                        
                        chunks = []
                        async for chunk in await client.invoke_agent_stream(
                            template_id="test-template",
                            request="Convenience stream test"
                        ):
                            chunks.append(chunk)
                        
                        assert len(chunks) == 3
                        assert all("Convenience chunk" in chunk for chunk in chunks)


class TestEndToEndSessionManagement:
    """端到端会话管理测试"""
    
    @pytest.mark.integration
    async def test_multiple_sessions_flow(self, test_api_key: str):
        """测试多会话管理流程"""
        async with AgentRuntimeClient(api_key=test_api_key) as client:
            with patch.object(client.template_manager, 'template_exists', return_value=True):
                with patch.object(client, '_create_sandbox_instance') as mock_create:
                    # 创建多个 mock sandbox
                    mock_sandboxes = [MockAsyncSandbox() for _ in range(3)]
                    mock_create.side_effect = mock_sandboxes
                    
                    # 创建多个会话
                    sessions = []
                    for i in range(3):
                        session = await client.create_session(f"template-{i}")
                        sessions.append(session)
                    
                    # 验证所有会话都存在
                    all_sessions = await client.list_sessions()
                    assert len(all_sessions) == 3
                    
                    # 逐个关闭会话
                    for session in sessions:
                        await client.close_session(session.sandbox_id)
                    
                    # 验证所有会话都被关闭
                    remaining_sessions = await client.list_sessions()
                    assert len(remaining_sessions) == 0
    
    @pytest.mark.integration
    async def test_session_lifecycle_flow(self, test_api_key: str):
        """测试会话生命周期流程"""
        async with AgentRuntimeClient(api_key=test_api_key) as client:
            with patch.object(client.template_manager, 'template_exists', return_value=True):
                with patch.object(client, '_create_sandbox_instance') as mock_create:
                    mock_sandbox = MockAsyncSandbox()
                    mock_create.return_value = mock_sandbox
                    
                    # 1. 创建会话
                    session = await client.create_session("test-template")
                    assert session.status == SessionStatus.ACTIVE
                    
                    # 2. 暂停会话
                    await session.pause()
                    assert session.status == SessionStatus.PAUSED
                    
                    # 3. 恢复会话
                    await session.resume()
                    assert session.status == SessionStatus.ACTIVE
                    
                    # 4. 执行一些操作
                    with patch.object(session, '_get_http_client') as mock_http_client:
                        mock_client = AsyncMock()
                        mock_response = Mock()
                        mock_response.status_code = 200
                        mock_response.json.return_value = {"result": "lifecycle test"}
                        mock_client.post.return_value = mock_response
                        mock_http_client.return_value = mock_client
                        
                        result = await session.invoke("Lifecycle test")
                        assert result["result"] == "lifecycle test"
                    
                    # 5. 关闭会话
                    await session.close()
                    assert session.status == SessionStatus.CLOSED
    
    @pytest.mark.integration
    async def test_concurrent_session_operations(self, test_api_key: str):
        """测试并发会话操作"""
        async with AgentRuntimeClient(api_key=test_api_key) as client:
            with patch.object(client.template_manager, 'template_exists', return_value=True):
                with patch.object(client, '_create_sandbox_instance') as mock_create:
                    mock_sandbox = MockAsyncSandbox()
                    mock_create.return_value = mock_sandbox
                    
                    session = await client.create_session("test-template")
                    
                    # Mock HTTP 客户端
                    with patch.object(session, '_get_http_client') as mock_http_client:
                        mock_client = AsyncMock()
                        mock_response = Mock()
                        mock_response.status_code = 200
                        mock_response.json.return_value = {"result": "concurrent"}
                        mock_client.post.return_value = mock_response
                        mock_client.get.return_value = mock_response
                        mock_http_client.return_value = mock_client
                        
                        # 并发执行多个操作
                        tasks = [
                            session.invoke(f"Concurrent request {i}")
                            for i in range(5)
                        ]
                        tasks.append(session.ping())
                        tasks.append(session.get_status())
                        
                        results = await asyncio.gather(*tasks, return_exceptions=True)
                        
                        # 验证结果
                        assert len(results) == 7
                        # 前5个是 invoke 结果
                        for i in range(5):
                            assert results[i]["result"] == "concurrent"


class TestEndToEndAuthentication:
    """端到端认证测试"""
    
    @pytest.mark.integration
    async def test_invalid_api_key_flow(self):
        """测试无效 API Key 流程"""
        from aioresponses import aioresponses
        
        with aioresponses() as mock_http:
            # 设置认证错误响应
            mock_http.get(
                "https://api.ppio.ai/v1/templates/agents",
                status=401,
                payload={"error": "Invalid API Key"}
            )
            
            async with AgentRuntimeClient(api_key="invalid-key") as client:
                from ppio_sandbox.agent_runtime.client.exceptions import AuthenticationError
                
                with pytest.raises(AuthenticationError):
                    await client.list_templates()
    
    @pytest.mark.integration
    async def test_api_key_rotation_flow(self, test_api_key: str):
        """测试 API Key 轮换流程"""
        from aioresponses import aioresponses
        
        client = AgentRuntimeClient(api_key="old-key")
        
        try:
            # 第一次请求失败（旧 key）
            with aioresponses() as mock_http:
                mock_http.get(
                    "https://api.ppio.ai/v1/templates/agents",
                    status=401,
                    payload={"error": "Invalid API Key"}
                )
                
                from ppio_sandbox.agent_runtime.client.exceptions import AuthenticationError
                with pytest.raises(AuthenticationError):
                    await client.list_templates()
            
            # 更新 API Key
            client.auth_manager.update_api_key(test_api_key)
            
            # 第二次请求成功（新 key）
            with aioresponses() as mock_http:
                setup_template_responses(mock_http)
                
                templates = await client.list_templates()
                assert len(templates) > 0
        
        finally:
            await client.close()


class TestEndToEndAdvanced:
    """端到端高级测试"""
    
    @pytest.mark.integration
    async def test_rapid_session_creation_cleanup(self, test_api_key: str):
        """测试快速会话创建和清理"""
        async with AgentRuntimeClient(api_key=test_api_key) as client:
            with patch.object(client.template_manager, 'template_exists', return_value=True):
                with patch.object(client, '_create_sandbox_instance') as mock_create:
                    
                    sessions = []
                    session_count = 10
                    
                    # 快速创建会话
                    for i in range(session_count):
                        mock_sandbox = MockAsyncSandbox()
                        mock_create.return_value = mock_sandbox
                        
                        session = await client.create_session(f"template-{i}")
                        sessions.append(session)
                    
                    assert len(client._sessions) == session_count
                    
                    # 批量关闭会话
                    await client.close_all_sessions()
                    assert len(client._sessions) == 0
    
    @pytest.mark.integration
    async def test_high_frequency_invocations(self, test_api_key: str):
        """测试高频调用"""
        async with AgentRuntimeClient(api_key=test_api_key) as client:
            with patch.object(client.template_manager, 'template_exists', return_value=True):
                with patch.object(client, '_create_sandbox_instance') as mock_create:
                    mock_sandbox = MockAsyncSandbox()
                    mock_create.return_value = mock_sandbox
                    
                    session = await client.create_session("test-template")
                    
                    # Mock HTTP 客户端
                    with patch.object(session, '_get_http_client') as mock_http_client:
                        mock_client = AsyncMock()
                        mock_response = Mock()
                        mock_response.status_code = 200
                        mock_response.json.return_value = {"result": "high-freq"}
                        mock_client.post.return_value = mock_response
                        mock_http_client.return_value = mock_client
                        
                        # 高频调用
                        invocation_count = 50
                        tasks = [
                            session.invoke(f"High frequency request {i}")
                            for i in range(invocation_count)
                        ]
                        
                        results = await asyncio.gather(*tasks)
                        
                        assert len(results) == invocation_count
                        assert all(r["result"] == "high-freq" for r in results)
