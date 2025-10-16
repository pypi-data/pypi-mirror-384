"""
并发处理集成测试

测试 Agent Runtime Client 的并发处理能力
"""

import pytest
import asyncio
from unittest.mock import patch, Mock, AsyncMock
from concurrent.futures import ThreadPoolExecutor

from ppio_sandbox.agent_runtime.client import AgentRuntimeClient
from ppio_sandbox.agent_runtime.client.models import SessionStatus
from ppio_sandbox.agent_runtime.client.exceptions import (
    SandboxCreationError,
    SessionNotFoundError
)

from ..mocks.mock_sandbox import MockAsyncSandbox


class TestConcurrentSessionManagement:
    """并发会话管理测试"""
    
    @pytest.mark.integration
    async def test_concurrent_session_creation(self, test_api_key: str, sample_templates):
        """测试并发创建会话"""
        async with AgentRuntimeClient(api_key=test_api_key) as client:
            with patch.object(client.template_manager, 'template_exists', return_value=True):
                with patch.object(client, '_create_sandbox_instance') as mock_create:
                    # 为每个模板创建不同的 mock sandbox
                    mock_sandboxes = [MockAsyncSandbox() for _ in range(len(sample_templates))]
                    mock_create.side_effect = mock_sandboxes
                    
                    # 并发创建会话
                    tasks = [
                        client.create_session(template.template_id)
                        for template in sample_templates[:5]  # 限制数量
                    ]
                    
                    sessions = await asyncio.gather(*tasks)
                    
                    # 验证结果
                    assert len(sessions) == 5
                    assert len(client._sessions) == 5
                    
                    # 验证每个会话都是唯一的
                    session_ids = {session.sandbox_id for session in sessions}
                    assert len(session_ids) == 5
                    
                    # 验证所有会话都是活跃的
                    for session in sessions:
                        assert session.status == SessionStatus.ACTIVE
    
    @pytest.mark.integration
    async def test_concurrent_session_operations(self, test_api_key: str, sample_template):
        """测试对同一会话的并发操作"""
        async with AgentRuntimeClient(api_key=test_api_key) as client:
            with patch.object(client.template_manager, 'template_exists', return_value=True):
                with patch.object(client, '_create_sandbox_instance') as mock_create:
                    mock_sandbox = MockAsyncSandbox()
                    mock_create.return_value = mock_sandbox
                    
                    session = await client.create_session(sample_template.template_id)
                    
                    # Mock HTTP 客户端
                    with patch.object(session, '_get_http_client') as mock_http_client:
                        mock_client_obj = AsyncMock()
                        mock_response = Mock()
                        mock_response.status_code = 200
                        mock_response.json.return_value = {"result": "concurrent"}
                        mock_client_obj.post.return_value = mock_response
                        mock_client_obj.get.return_value = mock_response
                        mock_http_client.return_value = mock_client_obj
                        
                        # 并发执行多种操作
                        tasks = [
                            session.invoke(f"Request {i}")
                            for i in range(10)
                        ]
                        tasks.extend([
                            session.ping(),
                            session.get_status(),
                            session.refresh()
                        ])
                        
                        results = await asyncio.gather(*tasks, return_exceptions=True)
                        
                        # 验证结果
                        assert len(results) == 13
                        
                        # 前 10 个是 invoke 结果
                        for i in range(10):
                            assert isinstance(results[i], dict)
                            assert results[i]["result"] == "concurrent"
                        
                        # 检查其他操作的结果
                        ping_result = results[10]
                        status_result = results[11]
                        refresh_result = results[12]
                        
                        assert hasattr(ping_result, 'status')  # PingResponse
                        assert status_result == SessionStatus.ACTIVE
                        assert refresh_result is None  # refresh 无返回值
    
    @pytest.mark.integration
    async def test_concurrent_session_closure(self, test_api_key: str, sample_templates):
        """测试并发关闭会话"""
        async with AgentRuntimeClient(api_key=test_api_key) as client:
            with patch.object(client.template_manager, 'template_exists', return_value=True):
                with patch.object(client, '_create_sandbox_instance') as mock_create:
                    # 创建多个会话
                    sessions = []
                    for i, template in enumerate(sample_templates[:5]):
                        mock_sandbox = MockAsyncSandbox()
                        mock_create.return_value = mock_sandbox
                        session = await client.create_session(template.template_id)
                        sessions.append(session)
                    
                    assert len(client._sessions) == 5
                    
                    # 并发关闭会话
                    close_tasks = [
                        client.close_session(session.sandbox_id)
                        for session in sessions
                    ]
                    
                    await asyncio.gather(*close_tasks)
                    
                    # 验证所有会话都被关闭
                    assert len(client._sessions) == 0
                    for session in sessions:
                        assert session.status == SessionStatus.CLOSED


class TestConcurrentInvocations:
    """并发调用测试"""
    
    @pytest.mark.integration
    async def test_concurrent_agent_invocations(self, test_api_key: str, sample_template):
        """测试并发 Agent 调用"""
        async with AgentRuntimeClient(api_key=test_api_key) as client:
            with patch.object(client.template_manager, 'template_exists', return_value=True):
                with patch.object(client, '_create_sandbox_instance') as mock_create:
                    mock_sandbox = MockAsyncSandbox()
                    mock_create.return_value = mock_sandbox
                    
                    session = await client.create_session(sample_template.template_id)
                    
                    # Mock HTTP 客户端
                    with patch.object(session, '_get_http_client') as mock_http_client:
                        mock_client_obj = AsyncMock()
                        
                        # 为每个请求创建唯一响应
                        def create_response(request_id):
                            response = Mock()
                            response.status_code = 200
                            response.json.return_value = {
                                "result": f"response_{request_id}",
                                "request_id": request_id
                            }
                            return response
                        
                        responses = [create_response(i) for i in range(20)]
                        mock_client_obj.post.side_effect = responses
                        mock_http_client.return_value = mock_client_obj
                        
                        # 并发执行 20 个调用
                        tasks = [
                            session.invoke(f"Concurrent request {i}")
                            for i in range(20)
                        ]
                        
                        results = await asyncio.gather(*tasks)
                        
                        # 验证结果
                        assert len(results) == 20
                        
                        # 验证每个响应都是唯一的
                        response_ids = {result["request_id"] for result in results}
                        assert len(response_ids) == 20
                        
                        # 验证所有响应都有正确的格式
                        for i, result in enumerate(results):
                            assert result["result"] == f"response_{i}"
    
    @pytest.mark.integration
    async def test_mixed_sync_and_streaming_calls(self, test_api_key: str, sample_template):
        """测试混合同步和流式调用"""
        async with AgentRuntimeClient(api_key=test_api_key) as client:
            with patch.object(client.template_manager, 'template_exists', return_value=True):
                with patch.object(client, '_create_sandbox_instance') as mock_create:
                    mock_sandbox = MockAsyncSandbox()
                    mock_create.return_value = mock_sandbox
                    
                    session = await client.create_session(sample_template.template_id)
                    
                    # Mock HTTP 客户端
                    with patch.object(session, '_get_http_client') as mock_http_client:
                        mock_client_obj = AsyncMock()
                        
                        # 同步调用响应
                        sync_response = Mock()
                        sync_response.status_code = 200
                        sync_response.json.return_value = {"result": "sync_response"}
                        
                        # 流式调用响应
                        async def stream_response():
                            for i in range(3):
                                yield f"stream_chunk_{i}"
                        
                        stream_mock = Mock()
                        stream_mock.status_code = 200
                        stream_mock.aiter_text = stream_response
                        
                        mock_client_obj.post.return_value = sync_response
                        mock_client_obj.stream.return_value.__aenter__.return_value = stream_mock
                        mock_http_client.return_value = mock_client_obj
                        
                        # 并发执行同步和流式调用
                        async def sync_call(i):
                            return await session.invoke(f"Sync call {i}")
                        
                        async def stream_call(i):
                            chunks = []
                            async for chunk in await session.invoke(f"Stream call {i}", stream=True):
                                chunks.append(chunk)
                            return chunks
                        
                        tasks = []
                        for i in range(5):
                            tasks.append(sync_call(i))
                            tasks.append(stream_call(i))
                        
                        results = await asyncio.gather(*tasks)
                        
                        # 验证结果
                        assert len(results) == 10
                        
                        # 验证同步和流式调用结果
                        for i in range(0, 10, 2):
                            sync_result = results[i]
                            stream_result = results[i + 1]
                            
                            assert sync_result["result"] == "sync_response"
                            assert len(stream_result) == 3
                            assert all("stream_chunk_" in chunk for chunk in stream_result)
    
    @pytest.mark.integration
    async def test_high_frequency_invocations(self, test_api_key: str, sample_template):
        """测试高频调用"""
        async with AgentRuntimeClient(api_key=test_api_key) as client:
            with patch.object(client.template_manager, 'template_exists', return_value=True):
                with patch.object(client, '_create_sandbox_instance') as mock_create:
                    mock_sandbox = MockAsyncSandbox()
                    mock_create.return_value = mock_sandbox
                    
                    session = await client.create_session(sample_template.template_id)
                    
                    # Mock HTTP 客户端
                    with patch.object(session, '_get_http_client') as mock_http_client:
                        mock_client_obj = AsyncMock()
                        mock_response = Mock()
                        mock_response.status_code = 200
                        mock_response.json.return_value = {"result": "high_freq"}
                        mock_client_obj.post.return_value = mock_response
                        mock_http_client.return_value = mock_client_obj
                        
                        import time
                        start_time = time.time()
                        
                        # 高频调用（100 个请求）
                        tasks = [
                            session.invoke(f"High freq {i}")
                            for i in range(100)
                        ]
                        
                        results = await asyncio.gather(*tasks)
                        
                        end_time = time.time()
                        total_time = end_time - start_time
                        
                        # 验证结果
                        assert len(results) == 100
                        assert all(r["result"] == "high_freq" for r in results)
                        
                        # 并发验证（100 个请求应该在合理时间内完成）
                        assert total_time < 2.0  # 2 秒内完成


class TestConcurrentErrorHandling:
    """并发错误处理测试"""
    
    @pytest.mark.integration
    async def test_concurrent_creation_with_failures(self, test_api_key: str, sample_templates):
        """测试并发创建时的部分失败"""
        async with AgentRuntimeClient(api_key=test_api_key) as client:
            with patch.object(client.template_manager, 'template_exists', return_value=True):
                with patch.object(client, '_create_sandbox_instance') as mock_create:
                    # 设置部分创建失败
                    def create_side_effect(template_id, **kwargs):
                        if "fail" in template_id:
                            raise Exception("Creation failed")
                        return MockAsyncSandbox()
                    
                    mock_create.side_effect = create_side_effect
                    
                    # 创建一些会失败的模板 ID
                    template_ids = [
                        "success-1",
                        "fail-1",
                        "success-2",
                        "fail-2",
                        "success-3"
                    ]
                    
                    # 并发创建会话
                    tasks = [
                        client.create_session(template_id)
                        for template_id in template_ids
                    ]
                    
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # 验证结果
                    assert len(results) == 5
                    
                    success_count = 0
                    failure_count = 0
                    
                    for i, result in enumerate(results):
                        if isinstance(result, Exception):
                            failure_count += 1
                            assert "fail" in template_ids[i]
                        else:
                            success_count += 1
                            assert "success" in template_ids[i]
                    
                    assert success_count == 3
                    assert failure_count == 2
                    assert len(client._sessions) == 3  # 只有成功的会话
    
    @pytest.mark.integration
    async def test_concurrent_invocations_with_failures(self, test_api_key: str, sample_template):
        """测试并发调用时的部分失败"""
        async with AgentRuntimeClient(api_key=test_api_key) as client:
            with patch.object(client.template_manager, 'template_exists', return_value=True):
                with patch.object(client, '_create_sandbox_instance') as mock_create:
                    mock_sandbox = MockAsyncSandbox()
                    mock_create.return_value = mock_sandbox
                    
                    session = await client.create_session(sample_template.template_id)
                    
                    # Mock HTTP 客户端
                    with patch.object(session, '_get_http_client') as mock_http_client:
                        mock_client_obj = AsyncMock()
                        
                        # 设置部分请求失败
                        def post_side_effect(*args, **kwargs):
                            # 从请求数据判断是否应该失败
                            json_data = kwargs.get('json', {})
                            prompt = json_data.get('prompt', '')
                            
                            if "fail" in prompt:
                                response = Mock()
                                response.status_code = 500
                                response.text = "Internal Server Error"
                                return response
                            else:
                                response = Mock()
                                response.status_code = 200
                                response.json.return_value = {"result": "success"}
                                return response
                        
                        mock_client_obj.post.side_effect = post_side_effect
                        mock_http_client.return_value = mock_client_obj
                        
                        # 并发执行成功和失败的调用
                        prompts = [
                            "success request 1",
                            "fail request 1",
                            "success request 2",
                            "fail request 2",
                            "success request 3"
                        ]
                        
                        tasks = [
                            session.invoke(prompt)
                            for prompt in prompts
                        ]
                        
                        results = await asyncio.gather(*tasks, return_exceptions=True)
                        
                        # 验证结果
                        assert len(results) == 5
                        
                        success_count = 0
                        failure_count = 0
                        
                        for i, result in enumerate(results):
                            if isinstance(result, Exception):
                                failure_count += 1
                                assert "fail" in prompts[i]
                            else:
                                success_count += 1
                                assert "success" in prompts[i]
                                assert result["result"] == "success"
                        
                        assert success_count == 3
                        assert failure_count == 2
    
    @pytest.mark.integration
    async def test_race_condition_handling(self, test_api_key: str, sample_template):
        """测试竞态条件处理"""
        async with AgentRuntimeClient(api_key=test_api_key) as client:
            with patch.object(client.template_manager, 'template_exists', return_value=True):
                with patch.object(client, '_create_sandbox_instance') as mock_create:
                    mock_sandbox = MockAsyncSandbox()
                    mock_create.return_value = mock_sandbox
                    
                    session = await client.create_session(sample_template.template_id)
                    
                    # 模拟竞态条件：并发地暂停和恢复会话
                    async def pause_resume_cycle():
                        for _ in range(5):
                            await session.pause()
                            await asyncio.sleep(0.001)
                            await session.resume()
                            await asyncio.sleep(0.001)
                    
                    # 并发执行多个暂停/恢复循环
                    tasks = [pause_resume_cycle() for _ in range(3)]
                    
                    await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # 验证最终状态是一致的
                    assert session.status in [SessionStatus.ACTIVE, SessionStatus.PAUSED]


class TestConcurrentResourceManagement:
    """并发资源管理测试"""
    
    @pytest.mark.integration
    async def test_concurrent_client_cleanup(self, test_api_key: str, sample_templates):
        """测试并发客户端清理"""
        clients = []
        
        try:
            # 创建多个客户端
            for i in range(5):
                client = AgentRuntimeClient(api_key=test_api_key)
                clients.append(client)
            
            # 为每个客户端创建会话
            all_sessions = []
            for client in clients:
                with patch.object(client.template_manager, 'template_exists', return_value=True):
                    with patch.object(client, '_create_sandbox_instance') as mock_create:
                        mock_sandbox = MockAsyncSandbox()
                        mock_create.return_value = mock_sandbox
                        
                        session = await client.create_session("test-template")
                        all_sessions.append(session)
            
            # 并发关闭所有客户端
            close_tasks = [client.close() for client in clients]
            await asyncio.gather(*close_tasks)
            
            # 验证所有客户端都被正确关闭
            for client in clients:
                assert client._closed is True
                assert len(client._sessions) == 0
            
            # 验证所有会话都被关闭
            for session in all_sessions:
                assert session.status == SessionStatus.CLOSED
        
        finally:
            # 确保清理
            for client in clients:
                if not client._closed:
                    await client.close()
    
    @pytest.mark.integration
    async def test_memory_usage_under_load(self, test_api_key: str, sample_template):
        """测试负载下的内存使用"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        async with AgentRuntimeClient(api_key=test_api_key) as client:
            with patch.object(client.template_manager, 'template_exists', return_value=True):
                with patch.object(client, '_create_sandbox_instance') as mock_create:
                    
                    # 创建大量会话
                    sessions = []
                    for i in range(50):
                        mock_sandbox = MockAsyncSandbox()
                        mock_create.return_value = mock_sandbox
                        session = await client.create_session(f"template-{i}")
                        sessions.append(session)
                    
                    # 检查内存使用
                    mid_memory = process.memory_info().rss
                    memory_per_session = (mid_memory - initial_memory) / 50
                    
                    # 每个会话的内存开销应该是合理的（小于 1MB）
                    assert memory_per_session < 1024 * 1024
                    
                    # 批量关闭会话
                    close_tasks = [
                        client.close_session(session.sandbox_id)
                        for session in sessions[:25]  # 关闭一半
                    ]
                    await asyncio.gather(*close_tasks)
                    
                    # 验证内存有所释放
                    final_memory = process.memory_info().rss
                    assert final_memory < mid_memory


class TestThreadSafety:
    """线程安全测试"""
    
    @pytest.mark.integration
    async def test_thread_safe_operations(self, test_api_key: str, sample_template):
        """测试线程安全操作"""
        async with AgentRuntimeClient(api_key=test_api_key) as client:
            with patch.object(client.template_manager, 'template_exists', return_value=True):
                with patch.object(client, '_create_sandbox_instance') as mock_create:
                    mock_sandbox = MockAsyncSandbox()
                    mock_create.return_value = mock_sandbox
                    
                    session = await client.create_session(sample_template.template_id)
                    
                    # Mock HTTP 客户端
                    with patch.object(session, '_get_http_client') as mock_http_client:
                        mock_client_obj = AsyncMock()
                        mock_response = Mock()
                        mock_response.status_code = 200
                        mock_response.json.return_value = {"result": "thread_safe"}
                        mock_client_obj.post.return_value = mock_response
                        mock_http_client.return_value = mock_client_obj
                        
                        # 在线程池中执行异步操作
                        def run_in_thread():
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            try:
                                return loop.run_until_complete(
                                    session.invoke("Thread safe test")
                                )
                            finally:
                                loop.close()
                        
                        # 使用线程池执行
                        with ThreadPoolExecutor(max_workers=5) as executor:
                            futures = [
                                executor.submit(run_in_thread)
                                for _ in range(10)
                            ]
                            
                            results = [future.result() for future in futures]
                        
                        # 验证结果
                        assert len(results) == 10
                        assert all(r["result"] == "thread_safe" for r in results)
