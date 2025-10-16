"""
会话生命周期集成测试

测试 SandboxSession 的完整生命周期
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import patch, Mock, AsyncMock

from ppio_sandbox.agent_runtime.client.session import SandboxSession
from ppio_sandbox.agent_runtime.client.models import SessionStatus, PingResponse
from ppio_sandbox.agent_runtime.client.exceptions import (
    SandboxOperationError,
    SessionNotFoundError,
    InvocationError
)

from ..mocks.mock_sandbox import (
    create_healthy_sandbox,
    create_paused_sandbox,
    MockAsyncSandbox
)


class TestSessionCreationAndInitialization:
    """会话创建和初始化测试"""
    
    @pytest.mark.integration
    async def test_session_creation_from_sandbox(self, sample_template):
        """测试从 Sandbox 创建会话"""
        sandbox = MockAsyncSandbox()
        mock_client = Mock()
        
        session = SandboxSession(
            template_id=sample_template.template_id,
            sandbox=sandbox,
            client=mock_client
        )
        
        # 验证初始状态
        assert session.template_id == sample_template.template_id
        assert session.sandbox is sandbox
        assert session.status == SessionStatus.ACTIVE
        assert session.is_active is True
        assert session.is_paused is False
        assert isinstance(session.created_at, datetime)
        assert isinstance(session.last_activity, datetime)
        
        # 验证属性
        assert session.sandbox_id
        assert session.session_id == session.sandbox_id
        assert session.host_url.startswith("https://")
        assert session.age_seconds >= 0
        assert session.idle_seconds >= 0
    
    @pytest.mark.integration
    async def test_session_with_different_sandbox_types(self, sample_template):
        """测试不同类型的 Sandbox"""
        mock_client = Mock()
        
        # 测试有 get_host 方法的 sandbox
        sandbox_with_host = Mock()
        sandbox_with_host.id = "sandbox-with-host"
        sandbox_with_host.get_host.return_value = "custom-host.example.com"
        
        session1 = SandboxSession(
            template_id=sample_template.template_id,
            sandbox=sandbox_with_host,
            client=mock_client
        )
        assert "custom-host.example.com" in session1.host_url
        
        # 测试没有 get_host 方法的 sandbox
        sandbox_without_host = Mock()
        sandbox_without_host.id = "sandbox-without-host"
        del sandbox_without_host.get_host
        
        session2 = SandboxSession(
            template_id=sample_template.template_id,
            sandbox=sandbox_without_host,
            client=mock_client
        )
        assert "session-sandbox-without-host" in session2.host_url


class TestSessionStateTransitions:
    """会话状态转换测试"""
    
    @pytest.mark.integration
    async def test_complete_state_lifecycle(self, sample_template):
        """测试完整的状态生命周期：ACTIVE -> PAUSED -> ACTIVE -> CLOSED"""
        sandbox = create_healthy_sandbox()
        mock_client = Mock()
        
        session = SandboxSession(
            template_id=sample_template.template_id,
            sandbox=sandbox,
            client=mock_client
        )
        
        # 1. 初始状态：ACTIVE
        assert session.status == SessionStatus.ACTIVE
        assert session.is_active is True
        assert session.is_paused is False
        
        # 2. 转换到 PAUSED
        await session.pause()
        assert session.status == SessionStatus.PAUSED
        assert session.is_active is False
        assert session.is_paused is True
        
        # 3. 转换回 ACTIVE
        await session.resume()
        assert session.status == SessionStatus.ACTIVE
        assert session.is_active is True
        assert session.is_paused is False
        
        # 4. 转换到 CLOSED
        await session.close()
        assert session.status == SessionStatus.CLOSED
        assert session.is_active is False
        assert session.is_paused is False
    
    @pytest.mark.integration
    async def test_pause_resume_multiple_times(self, sample_template):
        """测试多次暂停恢复"""
        sandbox = create_healthy_sandbox()
        mock_client = Mock()
        
        session = SandboxSession(
            template_id=sample_template.template_id,
            sandbox=sandbox,
            client=mock_client
        )
        
        # 多次暂停和恢复
        for i in range(3):
            # 暂停
            await session.pause()
            assert session.status == SessionStatus.PAUSED
            assert session.is_paused is True
            
            # 恢复
            await session.resume()
            assert session.status == SessionStatus.ACTIVE
            assert session.is_active is True
        
        # 最终关闭
        await session.close()
        assert session.status == SessionStatus.CLOSED
    
    @pytest.mark.integration
    async def test_state_transition_errors(self, sample_template):
        """测试状态转换错误"""
        sandbox = create_healthy_sandbox()
        mock_client = Mock()
        
        session = SandboxSession(
            template_id=sample_template.template_id,
            sandbox=sandbox,
            client=mock_client
        )
        
        # Mock sandbox 操作失败
        with patch.object(sandbox, 'pause', side_effect=Exception("Pause failed")):
            with pytest.raises(SandboxOperationError) as exc_info:
                await session.pause()
            
            assert "Failed to pause sandbox" in str(exc_info.value)
            # 状态应该保持 ACTIVE（未改变）
            assert session.status == SessionStatus.ACTIVE
        
        # Mock 恢复失败
        session.status = SessionStatus.PAUSED  # 手动设置状态
        with patch.object(sandbox, 'resume', side_effect=Exception("Resume failed")):
            with pytest.raises(SandboxOperationError) as exc_info:
                await session.resume()
            
            assert "Failed to resume sandbox" in str(exc_info.value)
        
        # Mock 关闭失败
        with patch.object(sandbox, 'close', side_effect=Exception("Close failed")):
            with pytest.raises(SandboxOperationError) as exc_info:
                await session.close()
            
            assert "Failed to close session" in str(exc_info.value)
            # 关闭失败时状态应该变为 ERROR
            assert session.status == SessionStatus.ERROR


class TestSessionInvocationLifecycle:
    """会话调用生命周期测试"""
    
    @pytest.mark.integration
    async def test_invocation_updates_activity(self, sample_template):
        """测试调用更新活动时间"""
        sandbox = create_healthy_sandbox()
        mock_client = Mock()
        
        session = SandboxSession(
            template_id=sample_template.template_id,
            sandbox=sandbox,
            client=mock_client
        )
        
        initial_activity = session.last_activity
        await asyncio.sleep(0.01)  # 确保时间差
        
        # Mock HTTP 客户端
        with patch.object(session, '_get_http_client') as mock_http_client:
            mock_client_obj = AsyncMock()
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"result": "activity test"}
            mock_client_obj.post.return_value = mock_response
            mock_http_client.return_value = mock_client_obj
            
            await session.invoke("Test activity update")
        
        # 验证活动时间被更新
        assert session.last_activity > initial_activity
    
    @pytest.mark.integration
    async def test_invocation_with_different_request_types(self, sample_template):
        """测试不同请求类型的调用"""
        sandbox = create_healthy_sandbox()
        mock_client = Mock()
        
        session = SandboxSession(
            template_id=sample_template.template_id,
            sandbox=sandbox,
            client=mock_client
        )
        
        # Mock HTTP 客户端
        with patch.object(session, '_get_http_client') as mock_http_client:
            mock_client_obj = AsyncMock()
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"result": "success"}
            mock_client_obj.post.return_value = mock_response
            mock_http_client.return_value = mock_client_obj
            
            # 1. 字符串请求
            result1 = await session.invoke("String request")
            assert result1["result"] == "success"
            
            # 2. 字典请求
            result2 = await session.invoke({"prompt": "Dict request", "data": {"key": "value"}})
            assert result2["result"] == "success"
            
            # 3. InvocationRequest 对象
            from ppio_sandbox.agent_runtime.client.models import InvocationRequest
            request = InvocationRequest(
                prompt="Object request",
                data={"test": True},
                metadata={"source": "integration_test"}
            )
            result3 = await session.invoke(request)
            assert result3["result"] == "success"
    
    @pytest.mark.integration
    async def test_invocation_after_state_changes(self, sample_template):
        """测试状态变化后的调用"""
        sandbox = create_healthy_sandbox()
        mock_client = Mock()
        
        session = SandboxSession(
            template_id=sample_template.template_id,
            sandbox=sandbox,
            client=mock_client
        )
        
        # Mock HTTP 客户端
        with patch.object(session, '_get_http_client') as mock_http_client:
            mock_client_obj = AsyncMock()
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"result": "state test"}
            mock_client_obj.post.return_value = mock_response
            mock_http_client.return_value = mock_client_obj
            
            # 1. ACTIVE 状态下调用成功
            result = await session.invoke("Active state test")
            assert result["result"] == "state test"
            
            # 2. 暂停后调用失败
            await session.pause()
            with pytest.raises(SessionNotFoundError) as exc_info:
                await session.invoke("Paused state test")
            assert "is not active" in str(exc_info.value)
            
            # 3. 恢复后调用成功
            await session.resume()
            result = await session.invoke("Resumed state test")
            assert result["result"] == "state test"
            
            # 4. 关闭后调用失败
            await session.close()
            with pytest.raises(SessionNotFoundError) as exc_info:
                await session.invoke("Closed state test")
            assert "is not active" in str(exc_info.value)
    
    @pytest.mark.integration
    async def test_streaming_invocation_lifecycle(self, sample_template):
        """测试流式调用生命周期"""
        sandbox = create_healthy_sandbox()
        mock_client = Mock()
        
        session = SandboxSession(
            template_id=sample_template.template_id,
            sandbox=sandbox,
            client=mock_client
        )
        
        # Mock 流式响应
        async def mock_stream():
            for i in range(5):
                await asyncio.sleep(0.005)
                yield f"Stream chunk {i}"
        
        with patch.object(session, '_get_http_client') as mock_http_client:
            mock_client_obj = AsyncMock()
            mock_stream_response = Mock()
            mock_stream_response.status_code = 200
            mock_stream_response.aiter_text = mock_stream
            mock_client_obj.stream.return_value.__aenter__.return_value = mock_stream_response
            mock_http_client.return_value = mock_client_obj
            
            initial_activity = session.last_activity
            await asyncio.sleep(0.01)
            
            chunks = []
            async for chunk in await session.invoke("Stream test", stream=True):
                chunks.append(chunk)
            
            assert len(chunks) == 5
            assert all("Stream chunk" in chunk for chunk in chunks)
            # 验证活动时间被更新
            assert session.last_activity > initial_activity


class TestSessionHealthAndMonitoring:
    """会话健康和监控测试"""
    
    @pytest.mark.integration
    async def test_ping_during_lifecycle(self, sample_template):
        """测试生命周期中的健康检查"""
        sandbox = create_healthy_sandbox()
        mock_client = Mock()
        
        session = SandboxSession(
            template_id=sample_template.template_id,
            sandbox=sandbox,
            client=mock_client
        )
        
        # Mock HTTP 客户端
        with patch.object(session, '_get_http_client') as mock_http_client:
            mock_client_obj = AsyncMock()
            healthy_response = Mock()
            healthy_response.status_code = 200
            healthy_response.json.return_value = {
                "status": "healthy",
                "timestamp": datetime.now().isoformat()
            }
            mock_client_obj.get.return_value = healthy_response
            mock_http_client.return_value = mock_client_obj
            
            # 1. ACTIVE 状态下 ping 成功
            ping_result = await session.ping()
            assert isinstance(ping_result, PingResponse)
            assert ping_result.status == "healthy"
            
            # 2. 暂停状态下 ping 仍然可以工作
            await session.pause()
            ping_result = await session.ping()
            assert ping_result.status == "healthy"
            
            # 3. 恢复状态下 ping 正常
            await session.resume()
            ping_result = await session.ping()
            assert ping_result.status == "healthy"
    
    @pytest.mark.integration
    async def test_status_monitoring_during_lifecycle(self, sample_template):
        """测试生命周期中的状态监控"""
        sandbox = create_healthy_sandbox()
        mock_client = Mock()
        
        session = SandboxSession(
            template_id=sample_template.template_id,
            sandbox=sandbox,
            client=mock_client
        )
        
        # Mock ping 方法
        with patch.object(session, 'ping') as mock_ping:
            mock_ping.return_value = PingResponse(status="healthy")
            
            # 1. ACTIVE 状态监控
            status = await session.get_status()
            assert status == SessionStatus.ACTIVE
            
            # 2. 暂停后状态监控
            await session.pause()
            status = await session.get_status()
            assert status == SessionStatus.PAUSED
            
            # 3. 恢复后状态监控
            await session.resume()
            status = await session.get_status()
            assert status == SessionStatus.ACTIVE
            
            # 4. 关闭后状态监控
            await session.close()
            # 关闭后不再依赖 ping
            status = await session.get_status()
            assert status == SessionStatus.CLOSED
    
    @pytest.mark.integration
    async def test_refresh_updates_activity(self, sample_template):
        """测试刷新更新活动时间"""
        sandbox = create_healthy_sandbox()
        mock_client = Mock()
        
        session = SandboxSession(
            template_id=sample_template.template_id,
            sandbox=sandbox,
            client=mock_client
        )
        
        initial_activity = session.last_activity
        await asyncio.sleep(0.01)
        
        await session.refresh()
        
        assert session.last_activity > initial_activity
    
    @pytest.mark.integration
    async def test_time_properties_during_lifecycle(self, sample_template):
        """测试生命周期中的时间属性"""
        sandbox = create_healthy_sandbox()
        mock_client = Mock()
        
        session = SandboxSession(
            template_id=sample_template.template_id,
            sandbox=sandbox,
            client=mock_client
        )
        
        # 初始时间
        initial_age = session.age_seconds
        initial_idle = session.idle_seconds
        
        # 等待一小段时间
        await asyncio.sleep(0.02)
        
        # 时间应该增加
        assert session.age_seconds > initial_age
        assert session.idle_seconds > initial_idle
        
        # 更新活动时间
        await session.refresh()
        
        # 空闲时间应该重置
        new_idle = session.idle_seconds
        assert new_idle < session.age_seconds
        assert new_idle >= 0


class TestSessionConcurrencyAndRaceConditions:
    """会话并发和竞态条件测试"""
    
    @pytest.mark.integration
    async def test_concurrent_state_operations(self, sample_template):
        """测试并发状态操作"""
        sandbox = create_healthy_sandbox()
        mock_client = Mock()
        
        session = SandboxSession(
            template_id=sample_template.template_id,
            sandbox=sandbox,
            client=mock_client
        )
        
        # 并发执行暂停和恢复操作
        async def pause_resume_cycle():
            await session.pause()
            await asyncio.sleep(0.01)
            await session.resume()
        
        # 执行多个并发循环
        tasks = [pause_resume_cycle() for _ in range(3)]
        await asyncio.gather(*tasks)
        
        # 最终状态应该是 ACTIVE
        assert session.status == SessionStatus.ACTIVE
    
    @pytest.mark.integration
    async def test_concurrent_invocations(self, sample_template):
        """测试并发调用"""
        sandbox = create_healthy_sandbox()
        mock_client = Mock()
        
        session = SandboxSession(
            template_id=sample_template.template_id,
            sandbox=sandbox,
            client=mock_client
        )
        
        # Mock HTTP 客户端
        with patch.object(session, '_get_http_client') as mock_http_client:
            mock_client_obj = AsyncMock()
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"result": "concurrent"}
            mock_client_obj.post.return_value = mock_response
            mock_http_client.return_value = mock_client_obj
            
            # 并发执行多个调用
            tasks = [
                session.invoke(f"Concurrent request {i}")
                for i in range(10)
            ]
            
            results = await asyncio.gather(*tasks)
            
            # 验证所有调用都成功
            assert len(results) == 10
            assert all(r["result"] == "concurrent" for r in results)
    
    @pytest.mark.integration
    async def test_concurrent_monitoring_operations(self, sample_template):
        """测试并发监控操作"""
        sandbox = create_healthy_sandbox()
        mock_client = Mock()
        
        session = SandboxSession(
            template_id=sample_template.template_id,
            sandbox=sandbox,
            client=mock_client
        )
        
        # Mock ping 和相关方法
        with patch.object(session, 'ping') as mock_ping:
            mock_ping.return_value = PingResponse(status="healthy")
            
            # 并发执行监控操作
            tasks = [
                session.ping(),
                session.get_status(),
                session.refresh(),
                session.ping(),
                session.get_status()
            ]
            
            results = await asyncio.gather(*tasks)
            
            # 验证结果
            assert len(results) == 5
            assert isinstance(results[0], PingResponse)  # ping
            assert results[1] == SessionStatus.ACTIVE   # get_status
            assert results[2] is None                   # refresh
            assert isinstance(results[3], PingResponse)  # ping
            assert results[4] == SessionStatus.ACTIVE   # get_status


class TestSessionErrorRecovery:
    """会话错误恢复测试"""
    
    @pytest.mark.integration
    async def test_recovery_from_sandbox_errors(self, sample_template):
        """测试从 Sandbox 错误中恢复"""
        sandbox = create_healthy_sandbox()
        mock_client = Mock()
        
        session = SandboxSession(
            template_id=sample_template.template_id,
            sandbox=sandbox,
            client=mock_client
        )
        
        # 模拟暂停失败，但之后操作成功
        call_count = 0
        original_pause = sandbox.pause
        
        async def failing_pause():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("First pause fails")
            return await original_pause()
        
        sandbox.pause = failing_pause
        
        # 第一次暂停失败
        with pytest.raises(SandboxOperationError):
            await session.pause()
        assert session.status == SessionStatus.ACTIVE
        
        # 第二次暂停成功
        await session.pause()
        assert session.status == SessionStatus.PAUSED
    
    @pytest.mark.integration
    async def test_recovery_from_invocation_errors(self, sample_template):
        """测试从调用错误中恢复"""
        sandbox = create_healthy_sandbox()
        mock_client = Mock()
        
        session = SandboxSession(
            template_id=sample_template.template_id,
            sandbox=sandbox,
            client=mock_client
        )
        
        with patch.object(session, '_get_http_client') as mock_http_client:
            mock_client_obj = AsyncMock()
            
            # 第一次调用失败
            error_response = Mock()
            error_response.status_code = 500
            error_response.text = "Server Error"
            
            # 第二次调用成功
            success_response = Mock()
            success_response.status_code = 200
            success_response.json.return_value = {"result": "recovered"}
            
            mock_client_obj.post.side_effect = [error_response, success_response]
            mock_http_client.return_value = mock_client_obj
            
            # 第一次调用失败
            with pytest.raises(InvocationError):
                await session.invoke("First call")
            
            # 第二次调用成功
            result = await session.invoke("Second call")
            assert result["result"] == "recovered"
    
    @pytest.mark.integration
    async def test_graceful_degradation(self, sample_template):
        """测试优雅降级"""
        sandbox = create_healthy_sandbox()
        mock_client = Mock()
        
        session = SandboxSession(
            template_id=sample_template.template_id,
            sandbox=sandbox,
            client=mock_client
        )
        
        # Mock ping 失败但会话仍然可以运行其他操作
        with patch.object(session, 'ping', side_effect=Exception("Ping unavailable")):
            # ping 失败
            with pytest.raises(Exception):
                await session.ping()
            
            # 但状态查询应该通过其他方式工作
            status = await session.get_status()
            assert status == SessionStatus.ERROR  # 因为 ping 失败
            
            # 其他操作仍然可以进行
            await session.refresh()
            assert session.status in [SessionStatus.ACTIVE, SessionStatus.ERROR]
