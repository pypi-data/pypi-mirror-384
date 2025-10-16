"""
SandboxSession 单元测试

测试 Sandbox 会话管理功能
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from ppio_sandbox.agent_runtime.client.session import SandboxSession
from ppio_sandbox.agent_runtime.client.models import (
    InvocationRequest,
    SessionStatus,
    PingResponse
)
from ppio_sandbox.agent_runtime.client.exceptions import (
    InvocationError,
    NetworkError,
    SandboxOperationError,
    SessionNotFoundError
)

from ..mocks.mock_sandbox import (
    create_healthy_sandbox,
    create_paused_sandbox,
    create_error_sandbox,
    assert_sandbox_state,
    assert_operation_called
)
from ..mocks.test_fixtures import create_sample_request


class TestSandboxSessionInit:
    """SandboxSession 初始化测试"""
    
    @pytest.mark.unit
    def test_session_init(self, mock_sandbox, sample_template):
        """测试会话初始化"""
        mock_client = Mock()
        session = SandboxSession(
            template_id=sample_template.template_id,
            sandbox=mock_sandbox,
            client=mock_client
        )
        
        assert session.template_id == sample_template.template_id
        assert session.sandbox is mock_sandbox
        assert session._client_ref is mock_client
        assert session.status == SessionStatus.ACTIVE
        assert isinstance(session.created_at, datetime)
        assert isinstance(session.last_activity, datetime)
    
    @pytest.mark.unit
    def test_session_properties(self, mock_sandbox, sample_template):
        """测试会话属性"""
        mock_client = Mock()
        session = SandboxSession(
            template_id=sample_template.template_id,
            sandbox=mock_sandbox,
            client=mock_client
        )
        
        assert session.sandbox_id == mock_sandbox.id
        assert session.session_id == mock_sandbox.id  # 向后兼容
        assert session.host_url.startswith("https://")
        assert session.is_active is True
        assert session.is_paused is False
        assert session.age_seconds >= 0
        assert session.idle_seconds >= 0


class TestSandboxSessionInvoke:
    """SandboxSession 调用测试"""
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    @pytest.mark.asyncio

    async def test_invoke_success_dict(self, mock_sandbox, sample_template):
        """测试成功调用 - 字典格式请求"""
        mock_client = Mock()
        session = SandboxSession(
            template_id=sample_template.template_id,
            sandbox=mock_sandbox,
            client=mock_client
        )
        
        # Mock HTTP 响应
        mock_http_client = AsyncMock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": "success response"}
        mock_http_client.post.return_value = mock_response
        
        with patch.object(session, '_get_http_client', return_value=mock_http_client):
            result = await session.invoke({"prompt": "test"})
        
        assert result == {"result": "success response"}
        assert mock_http_client.post.called
        
        # 验证最后活动时间被更新
        assert session.last_activity > session.created_at
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    @pytest.mark.asyncio

    async def test_invoke_success_string(self, mock_sandbox, sample_template):
        """测试成功调用 - 字符串格式请求"""
        mock_client = Mock()
        session = SandboxSession(
            template_id=sample_template.template_id,
            sandbox=mock_sandbox,
            client=mock_client
        )
        
        mock_http_client = AsyncMock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": "string response"}
        mock_http_client.post.return_value = mock_response
        
        with patch.object(session, '_get_http_client', return_value=mock_http_client):
            result = await session.invoke("test prompt")
        
        assert result == {"result": "string response"}
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    @pytest.mark.asyncio

    async def test_invoke_success_invocation_request(self, mock_sandbox, sample_template, sample_request):
        """测试成功调用 - InvocationRequest 格式"""
        mock_client = Mock()
        session = SandboxSession(
            template_id=sample_template.template_id,
            sandbox=mock_sandbox,
            client=mock_client
        )
        
        mock_http_client = AsyncMock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": "request response"}
        mock_http_client.post.return_value = mock_response
        
        with patch.object(session, '_get_http_client', return_value=mock_http_client):
            result = await session.invoke(sample_request)
        
        assert result == {"result": "request response"}
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    @pytest.mark.asyncio

    async def test_invoke_streaming(self, mock_sandbox, sample_template):
        """测试流式调用"""
        mock_client = Mock()
        session = SandboxSession(
            template_id=sample_template.template_id,
            sandbox=mock_sandbox,
            client=mock_client
        )
        
        # Mock 流式响应
        async def mock_stream():
            for chunk in ["chunk1", "chunk2", "chunk3"]:
                yield chunk
        
        mock_stream_response = Mock()
        mock_stream_response.status_code = 200
        mock_stream_response.aiter_text = mock_stream
        
        mock_http_client = AsyncMock()
        mock_http_client.stream.return_value.__aenter__.return_value = mock_stream_response
        
        with patch.object(session, '_get_http_client', return_value=mock_http_client):
            chunks = []
            async for chunk in await session.invoke("test", stream=True):
                chunks.append(chunk)
        
        assert chunks == ["chunk1", "chunk2", "chunk3"]
        assert mock_http_client.stream.called
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    @pytest.mark.asyncio

    async def test_invoke_session_not_active(self, mock_sandbox, sample_template):
        """测试会话非活跃状态调用"""
        mock_client = Mock()
        session = SandboxSession(
            template_id=sample_template.template_id,
            sandbox=mock_sandbox,
            client=mock_client
        )
        session.status = SessionStatus.CLOSED
        
        with pytest.raises(SessionNotFoundError) as exc_info:
            await session.invoke("test")
        
        assert "is not active" in str(exc_info.value)
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    @pytest.mark.asyncio

    async def test_invoke_http_error(self, mock_sandbox, sample_template):
        """测试 HTTP 错误"""
        mock_client = Mock()
        session = SandboxSession(
            template_id=sample_template.template_id,
            sandbox=mock_sandbox,
            client=mock_client
        )
        
        mock_http_client = AsyncMock()
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_http_client.post.return_value = mock_response
        
        with patch.object(session, '_get_http_client', return_value=mock_http_client):
            with pytest.raises(InvocationError) as exc_info:
                await session.invoke("test")
        
        assert "status 500" in str(exc_info.value)
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    @pytest.mark.asyncio

    async def test_invoke_network_error(self, mock_sandbox, sample_template):
        """测试网络错误"""
        mock_client = Mock()
        session = SandboxSession(
            template_id=sample_template.template_id,
            sandbox=mock_sandbox,
            client=mock_client
        )
        
        mock_http_client = AsyncMock()
        mock_http_client.post.side_effect = Exception("Connection timeout")
        
        with patch.object(session, '_get_http_client', return_value=mock_http_client):
            with pytest.raises(NetworkError) as exc_info:
                await session.invoke("test")
        
        assert "Network error" in str(exc_info.value)
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    @pytest.mark.asyncio

    async def test_invoke_invalid_request_format(self, mock_sandbox, sample_template):
        """测试无效请求格式"""
        mock_client = Mock()
        session = SandboxSession(
            template_id=sample_template.template_id,
            sandbox=mock_sandbox,
            client=mock_client
        )
        
        with pytest.raises(InvocationError) as exc_info:
            await session.invoke(123)  # 无效类型
        
        assert "Invalid request format" in str(exc_info.value)


class TestSandboxSessionLifecycle:
    """SandboxSession 生命周期测试"""
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    @pytest.mark.asyncio

    async def test_pause_success(self, sample_template):
        """测试成功暂停"""
        sandbox = create_healthy_sandbox()
        mock_client = Mock()
        session = SandboxSession(
            template_id=sample_template.template_id,
            sandbox=sandbox,
            client=mock_client
        )
        
        await session.pause()
        
        assert session.status == SessionStatus.PAUSED
        assert_operation_called(sandbox, "pause", 1)
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    @pytest.mark.asyncio

    async def test_resume_success(self, sample_template):
        """测试成功恢复"""
        sandbox = create_paused_sandbox()
        mock_client = Mock()
        session = SandboxSession(
            template_id=sample_template.template_id,
            sandbox=sandbox,
            client=mock_client
        )
        session.status = SessionStatus.PAUSED
        
        await session.resume()
        
        assert session.status == SessionStatus.ACTIVE
        assert_operation_called(sandbox, "resume", 1)
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    @pytest.mark.asyncio

    async def test_pause_error(self, sample_template):
        """测试暂停错误"""
        sandbox = create_error_sandbox()
        mock_client = Mock()
        session = SandboxSession(
            template_id=sample_template.template_id,
            sandbox=sandbox,
            client=mock_client
        )
        
        with patch.object(sandbox, 'pause', side_effect=Exception("Pause failed")):
            with pytest.raises(SandboxOperationError) as exc_info:
                await session.pause()
        
        assert "Failed to pause sandbox" in str(exc_info.value)
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    @pytest.mark.asyncio

    async def test_close_success(self, sample_template):
        """测试成功关闭"""
        sandbox = create_healthy_sandbox()
        mock_client = Mock()
        session = SandboxSession(
            template_id=sample_template.template_id,
            sandbox=sandbox,
            client=mock_client
        )
        
        await session.close()
        
        assert session.status == SessionStatus.CLOSED
        assert_operation_called(sandbox, "close", 1)
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    @pytest.mark.asyncio

    async def test_close_error(self, sample_template):
        """测试关闭错误"""
        sandbox = create_healthy_sandbox()
        mock_client = Mock()
        session = SandboxSession(
            template_id=sample_template.template_id,
            sandbox=sandbox,
            client=mock_client
        )
        
        with patch.object(sandbox, 'close', side_effect=Exception("Close failed")):
            with pytest.raises(SandboxOperationError) as exc_info:
                await session.close()
        
        assert "Failed to close session" in str(exc_info.value)
        assert session.status == SessionStatus.ERROR


class TestSandboxSessionPing:
    """SandboxSession 健康检查测试"""
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    @pytest.mark.asyncio

    async def test_ping_success(self, mock_sandbox, sample_template):
        """测试成功的健康检查"""
        mock_client = Mock()
        session = SandboxSession(
            template_id=sample_template.template_id,
            sandbox=mock_sandbox,
            client=mock_client
        )
        
        mock_http_client = AsyncMock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "healthy",
            "message": "Service running",
            "timestamp": "2024-01-01T00:00:00Z"
        }
        mock_http_client.get.return_value = mock_response
        
        with patch.object(session, '_get_http_client', return_value=mock_http_client):
            ping_response = await session.ping()
        
        assert isinstance(ping_response, PingResponse)
        assert ping_response.status == "healthy"
        assert ping_response.message == "Service running"
        assert ping_response.timestamp == "2024-01-01T00:00:00Z"
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    @pytest.mark.asyncio

    async def test_ping_unhealthy(self, mock_sandbox, sample_template):
        """测试不健康状态"""
        mock_client = Mock()
        session = SandboxSession(
            template_id=sample_template.template_id,
            sandbox=mock_sandbox,
            client=mock_client
        )
        
        mock_http_client = AsyncMock()
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Error"
        mock_http_client.get.return_value = mock_response
        
        with patch.object(session, '_get_http_client', return_value=mock_http_client):
            ping_response = await session.ping()
        
        assert ping_response.status == "unhealthy"
        assert "HTTP 500" in ping_response.message
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    @pytest.mark.asyncio

    async def test_ping_network_error(self, mock_sandbox, sample_template):
        """测试 ping 网络错误"""
        mock_client = Mock()
        session = SandboxSession(
            template_id=sample_template.template_id,
            sandbox=mock_sandbox,
            client=mock_client
        )
        
        mock_http_client = AsyncMock()
        mock_http_client.get.side_effect = Exception("Connection failed")
        
        with patch.object(session, '_get_http_client', return_value=mock_http_client):
            with pytest.raises(NetworkError) as exc_info:
                await session.ping()
        
        assert "Network error during ping" in str(exc_info.value)


class TestSandboxSessionStatus:
    """SandboxSession 状态管理测试"""
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    @pytest.mark.asyncio

    async def test_get_status_active(self, mock_sandbox, sample_template):
        """测试获取活跃状态"""
        mock_client = Mock()
        session = SandboxSession(
            template_id=sample_template.template_id,
            sandbox=mock_sandbox,
            client=mock_client
        )
        
        # Mock ping 返回健康状态
        with patch.object(session, 'ping', return_value=PingResponse(status="healthy")):
            status = await session.get_status()
        
        assert status == SessionStatus.ACTIVE
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    @pytest.mark.asyncio

    async def test_get_status_paused(self, mock_sandbox, sample_template):
        """测试获取暂停状态"""
        mock_client = Mock()
        session = SandboxSession(
            template_id=sample_template.template_id,
            sandbox=mock_sandbox,
            client=mock_client
        )
        session.status = SessionStatus.PAUSED
        
        # Mock ping 返回健康状态，但会话处于暂停状态
        with patch.object(session, 'ping', return_value=PingResponse(status="healthy")):
            status = await session.get_status()
        
        assert status == SessionStatus.PAUSED
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    @pytest.mark.asyncio

    async def test_get_status_error(self, mock_sandbox, sample_template):
        """测试获取错误状态"""
        mock_client = Mock()
        session = SandboxSession(
            template_id=sample_template.template_id,
            sandbox=mock_sandbox,
            client=mock_client
        )
        
        # Mock ping 抛出异常
        with patch.object(session, 'ping', side_effect=Exception("Ping failed")):
            status = await session.get_status()
        
        assert status == SessionStatus.ERROR
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    @pytest.mark.asyncio

    async def test_refresh(self, mock_sandbox, sample_template):
        """测试刷新会话"""
        mock_client = Mock()
        session = SandboxSession(
            template_id=sample_template.template_id,
            sandbox=mock_sandbox,
            client=mock_client
        )
        
        old_activity = session.last_activity
        await asyncio.sleep(0.01)  # 确保时间差
        
        await session.refresh()
        
        assert session.last_activity > old_activity


class TestSandboxSessionProperties:
    """SandboxSession 属性测试"""
    
    @pytest.mark.unit
    def test_host_url_with_get_host(self, sample_template):
        """测试有 get_host 方法的 host_url"""
        sandbox = Mock()
        sandbox.id = "test-sandbox-123"
        sandbox.get_host.return_value = "test-host.example.com"
        
        mock_client = Mock()
        session = SandboxSession(
            template_id=sample_template.template_id,
            sandbox=sandbox,
            client=mock_client
        )
        
        assert session.host_url == "https://test-host.example.com"
        sandbox.get_host.assert_called_with(8080)
    
    @pytest.mark.unit
    def test_host_url_without_get_host(self, sample_template):
        """测试没有 get_host 方法的 host_url"""
        sandbox = Mock()
        sandbox.id = "test-sandbox-123"
        del sandbox.get_host  # 删除 get_host 方法
        
        mock_client = Mock()
        session = SandboxSession(
            template_id=sample_template.template_id,
            sandbox=sandbox,
            client=mock_client
        )
        
        assert session.host_url.startswith("https://session-")
        assert "test-sandbox-123" in session.host_url
    
    @pytest.mark.unit
    def test_sandbox_id_variants(self, sample_template):
        """测试不同的 sandbox_id 获取方式"""
        # 有 id 属性
        sandbox1 = Mock()
        sandbox1.id = "sandbox-with-id"
        
        session1 = SandboxSession(sample_template.template_id, sandbox1, Mock())
        assert session1.sandbox_id == "sandbox-with-id"
        
        # 有 sandbox_id 属性
        sandbox2 = Mock()
        del sandbox2.id
        sandbox2.sandbox_id = "sandbox-with-sandbox-id"
        
        session2 = SandboxSession(sample_template.template_id, sandbox2, Mock())
        assert session2.sandbox_id == "sandbox-with-sandbox-id"
        
        # 都没有，使用 fallback
        sandbox3 = Mock(spec=[])  # 空 spec 确保没有预定义属性
        
        session3 = SandboxSession(sample_template.template_id, sandbox3, Mock())
        assert session3.sandbox_id.startswith("sandbox-")
    
    @pytest.mark.unit
    def test_time_properties(self, mock_sandbox, sample_template):
        """测试时间相关属性"""
        mock_client = Mock()
        session = SandboxSession(
            template_id=sample_template.template_id,
            sandbox=mock_sandbox,
            client=mock_client
        )
        
        # 刚创建时
        assert session.age_seconds >= 0
        assert session.age_seconds < 1
        assert session.idle_seconds >= 0
        assert session.idle_seconds < 1
        
        # 更新活动时间
        import time
        time.sleep(0.01)
        session.last_activity = datetime.now()
        
        assert session.age_seconds > 0
        assert session.idle_seconds >= 0


class TestSandboxSessionIntegration:
    """SandboxSession 集成测试"""
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    @pytest.mark.asyncio

    async def test_session_lifecycle_complete(self, sample_template):
        """测试完整的会话生命周期"""
        sandbox = create_healthy_sandbox()
        mock_client = Mock()
        session = SandboxSession(
            template_id=sample_template.template_id,
            sandbox=sandbox,
            client=mock_client
        )
        
        # 1. 初始状态
        assert session.status == SessionStatus.ACTIVE
        assert session.is_active
        
        # 2. 执行调用
        mock_http_client = AsyncMock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": "success"}
        mock_http_client.post.return_value = mock_response
        
        with patch.object(session, '_get_http_client', return_value=mock_http_client):
            result = await session.invoke("test")
            assert result["result"] == "success"
        
        # 3. 暂停
        await session.pause()
        assert session.status == SessionStatus.PAUSED
        assert session.is_paused
        
        # 4. 恢复
        await session.resume()
        assert session.status == SessionStatus.ACTIVE
        assert session.is_active
        
        # 5. 关闭
        await session.close()
        assert session.status == SessionStatus.CLOSED
        assert not session.is_active
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    @pytest.mark.asyncio

    async def test_concurrent_operations(self, mock_sandbox, sample_template):
        """测试并发操作"""
        mock_client = Mock()
        session = SandboxSession(
            template_id=sample_template.template_id,
            sandbox=mock_sandbox,
            client=mock_client
        )
        
        # Mock HTTP 客户端
        mock_http_client = AsyncMock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": "concurrent"}
        mock_http_client.post.return_value = mock_response
        mock_http_client.get.return_value = mock_response
        
        with patch.object(session, '_get_http_client', return_value=mock_http_client):
            # 并发执行多个操作
            tasks = [
                session.invoke(f"request-{i}")
                for i in range(5)
            ]
            tasks.append(session.ping())
            tasks.append(session.refresh())
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 验证结果
            assert len(results) == 7
            for i in range(5):
                assert results[i]["result"] == "concurrent"
    
    @pytest.mark.unit
    def test_session_representation(self, mock_sandbox, sample_template):
        """测试会话字符串表示"""
        mock_client = Mock()
        session = SandboxSession(
            template_id=sample_template.template_id,
            sandbox=mock_sandbox,
            client=mock_client
        )
        
        repr_str = repr(session)
        assert "SandboxSession" in repr_str
        assert session.sandbox_id in repr_str
        assert str(session.status) in repr_str  # SessionStatus.ACTIVE 而不是 'active'
        assert session.template_id in repr_str
