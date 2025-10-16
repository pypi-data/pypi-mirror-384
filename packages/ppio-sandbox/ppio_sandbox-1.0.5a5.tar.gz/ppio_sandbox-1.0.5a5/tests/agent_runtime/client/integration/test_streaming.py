"""
流式响应集成测试

测试 Agent Runtime Client 的流式处理功能
"""

import pytest
import asyncio
from unittest.mock import patch, Mock, AsyncMock

from ppio_sandbox.agent_runtime.client import AgentRuntimeClient
from ppio_sandbox.agent_runtime.client.models import InvocationRequest
from ppio_sandbox.agent_runtime.client.exceptions import NetworkError, InvocationError

from ..mocks.mock_sandbox import MockAsyncSandbox
from ..mocks.test_fixtures import create_streaming_chunks


class TestStreamingInvocation:
    """流式调用测试"""
    
    @pytest.mark.integration
    async def test_basic_streaming_flow(self, test_api_key: str, sample_template):
        """测试基础流式处理流程"""
        async with AgentRuntimeClient(api_key=test_api_key) as client:
            with patch.object(client.template_manager, 'template_exists', return_value=True):
                with patch.object(client, '_create_sandbox_instance') as mock_create:
                    mock_sandbox = MockAsyncSandbox()
                    mock_create.return_value = mock_sandbox
                    
                    session = await client.create_session(sample_template.template_id)
                    
                    # Mock 流式响应
                    async def mock_stream():
                        chunks = create_streaming_chunks()
                        for chunk in chunks:
                            await asyncio.sleep(0.01)  # 模拟网络延迟
                            yield chunk
                    
                    with patch.object(session, '_get_http_client') as mock_http_client:
                        mock_client_obj = AsyncMock()
                        mock_stream_response = Mock()
                        mock_stream_response.status_code = 200
                        mock_stream_response.aiter_text = mock_stream
                        mock_client_obj.stream.return_value.__aenter__.return_value = mock_stream_response
                        mock_http_client.return_value = mock_client_obj
                        
                        collected_chunks = []
                        async for chunk in await session.invoke("Stream me some data", stream=True):
                            collected_chunks.append(chunk)
                        
                        expected_chunks = create_streaming_chunks()
                        assert len(collected_chunks) == len(expected_chunks)
                        assert collected_chunks == expected_chunks
    
    @pytest.mark.integration
    async def test_streaming_with_invocation_request(self, test_api_key: str, sample_template):
        """测试使用 InvocationRequest 的流式处理"""
        async with AgentRuntimeClient(api_key=test_api_key) as client:
            with patch.object(client.template_manager, 'template_exists', return_value=True):
                with patch.object(client, '_create_sandbox_instance') as mock_create:
                    mock_sandbox = MockAsyncSandbox()
                    mock_create.return_value = mock_sandbox
                    
                    session = await client.create_session(sample_template.template_id)
                    
                    # 创建流式请求
                    request = InvocationRequest(
                        prompt="Generate a story",
                        data={"topic": "AI", "length": "short"},
                        stream=True,
                        stream_options={"buffer_size": 1024},
                        metadata={"test": "streaming"}
                    )
                    
                    # Mock 流式响应
                    async def mock_story_stream():
                        story_parts = [
                            "Once upon a time,",
                            "there was an AI",
                            "that learned to dream.",
                            "It dreamed of electric sheep",
                            "and digital meadows.",
                            "The end."
                        ]
                        for part in story_parts:
                            await asyncio.sleep(0.005)
                            yield part
                    
                    with patch.object(session, '_get_http_client') as mock_http_client:
                        mock_client_obj = AsyncMock()
                        mock_stream_response = Mock()
                        mock_stream_response.status_code = 200
                        mock_stream_response.aiter_text = mock_story_stream
                        mock_client_obj.stream.return_value.__aenter__.return_value = mock_stream_response
                        mock_http_client.return_value = mock_client_obj
                        
                        story_parts = []
                        async for part in await session.invoke(request):
                            story_parts.append(part)
                        
                        assert len(story_parts) == 6
                        assert "Once upon a time," in story_parts
                        assert "The end." in story_parts
    
    @pytest.mark.integration
    async def test_streaming_convenience_method(self, test_api_key: str, sample_template):
        """测试流式便捷方法"""
        async with AgentRuntimeClient(api_key=test_api_key) as client:
            with patch.object(client.template_manager, 'template_exists', return_value=True):
                with patch.object(client, '_create_sandbox_instance') as mock_create:
                    mock_sandbox = MockAsyncSandbox()
                    mock_create.return_value = mock_sandbox
                    
                    # Mock session creation and streaming
                    with patch('ppio_sandbox.agent_runtime.client.session.SandboxSession') as mock_session_class:
                        async def mock_convenience_stream():
                            for i in range(5):
                                await asyncio.sleep(0.005)
                                yield f"Convenience chunk {i}"
                        
                        mock_session = AsyncMock()
                        mock_session.sandbox_id = "convenience-session"
                        mock_session.invoke.return_value = mock_convenience_stream()
                        mock_session.close = AsyncMock()
                        mock_session_class.return_value = mock_session
                        
                        chunks = []
                        async for chunk in await client.invoke_agent_stream(
                            template_id=sample_template.template_id,
                            request="Convenience streaming test"
                        ):
                            chunks.append(chunk)
                        
                        assert len(chunks) == 5
                        assert all("Convenience chunk" in chunk for chunk in chunks)
                        
                        # 验证会话被自动关闭
                        mock_session.close.assert_called_once()


class TestStreamingErrorHandling:
    """流式错误处理测试"""
    
    @pytest.mark.integration
    async def test_streaming_network_error(self, test_api_key: str, sample_template):
        """测试流式处理中的网络错误"""
        async with AgentRuntimeClient(api_key=test_api_key) as client:
            with patch.object(client.template_manager, 'template_exists', return_value=True):
                with patch.object(client, '_create_sandbox_instance') as mock_create:
                    mock_sandbox = MockAsyncSandbox()
                    mock_create.return_value = mock_sandbox
                    
                    session = await client.create_session(sample_template.template_id)
                    
                    # Mock 网络错误
                    with patch.object(session, '_get_http_client') as mock_http_client:
                        mock_client_obj = AsyncMock()
                        mock_client_obj.stream.side_effect = Exception("Network connection failed")
                        mock_http_client.return_value = mock_client_obj
                        
                        with pytest.raises(NetworkError) as exc_info:
                            async for chunk in await session.invoke("Test stream", stream=True):
                                pass  # 不应该到达这里
                        
                        assert "Network error during streaming" in str(exc_info.value)
    
    @pytest.mark.integration
    async def test_streaming_http_error(self, test_api_key: str, sample_template):
        """测试流式处理中的 HTTP 错误"""
        async with AgentRuntimeClient(api_key=test_api_key) as client:
            with patch.object(client.template_manager, 'template_exists', return_value=True):
                with patch.object(client, '_create_sandbox_instance') as mock_create:
                    mock_sandbox = MockAsyncSandbox()
                    mock_create.return_value = mock_sandbox
                    
                    session = await client.create_session(sample_template.template_id)
                    
                    # Mock HTTP 错误响应
                    with patch.object(session, '_get_http_client') as mock_http_client:
                        mock_client_obj = AsyncMock()
                        mock_stream_response = Mock()
                        mock_stream_response.status_code = 500
                        mock_stream_response.text = "Internal Server Error"
                        mock_client_obj.stream.return_value.__aenter__.return_value = mock_stream_response
                        mock_http_client.return_value = mock_client_obj
                        
                        with pytest.raises(InvocationError) as exc_info:
                            async for chunk in await session.invoke("Test stream", stream=True):
                                pass  # 不应该到达这里
                        
                        assert "Streaming request failed with status 500" in str(exc_info.value)
    
    @pytest.mark.integration
    async def test_streaming_partial_failure(self, test_api_key: str, sample_template):
        """测试流式处理中的部分失败"""
        async with AgentRuntimeClient(api_key=test_api_key) as client:
            with patch.object(client.template_manager, 'template_exists', return_value=True):
                with patch.object(client, '_create_sandbox_instance') as mock_create:
                    mock_sandbox = MockAsyncSandbox()
                    mock_create.return_value = mock_sandbox
                    
                    session = await client.create_session(sample_template.template_id)
                    
                    # Mock 部分成功的流式响应
                    async def partial_failure_stream():
                        for i in range(3):
                            yield f"Success chunk {i}"
                        raise Exception("Stream interrupted")
                    
                    with patch.object(session, '_get_http_client') as mock_http_client:
                        mock_client_obj = AsyncMock()
                        mock_stream_response = Mock()
                        mock_stream_response.status_code = 200
                        mock_stream_response.aiter_text = partial_failure_stream
                        mock_client_obj.stream.return_value.__aenter__.return_value = mock_stream_response
                        mock_http_client.return_value = mock_client_obj
                        
                        chunks = []
                        with pytest.raises(Exception) as exc_info:
                            async for chunk in await session.invoke("Test stream", stream=True):
                                chunks.append(chunk)
                        
                        # 应该收到部分数据
                        assert len(chunks) == 3
                        assert "Stream interrupted" in str(exc_info.value)
    
    @pytest.mark.integration
    async def test_streaming_timeout_handling(self, test_api_key: str, sample_template):
        """测试流式处理超时"""
        async with AgentRuntimeClient(api_key=test_api_key) as client:
            with patch.object(client.template_manager, 'template_exists', return_value=True):
                with patch.object(client, '_create_sandbox_instance') as mock_create:
                    mock_sandbox = MockAsyncSandbox()
                    mock_create.return_value = mock_sandbox
                    
                    session = await client.create_session(sample_template.template_id)
                    
                    # Mock 慢速流式响应
                    async def slow_stream():
                        for i in range(2):
                            await asyncio.sleep(0.1)  # 模拟慢速响应
                            yield f"Slow chunk {i}"
                    
                    with patch.object(session, '_get_http_client') as mock_http_client:
                        mock_client_obj = AsyncMock()
                        mock_stream_response = Mock()
                        mock_stream_response.status_code = 200
                        mock_stream_response.aiter_text = slow_stream
                        mock_client_obj.stream.return_value.__aenter__.return_value = mock_stream_response
                        mock_http_client.return_value = mock_client_obj
                        
                        # 使用短超时测试
                        chunks = []
                        try:
                            async with asyncio.timeout(0.05):  # 50ms 超时
                                async for chunk in await session.invoke("Test stream", stream=True):
                                    chunks.append(chunk)
                        except asyncio.TimeoutError:
                            pass  # 预期的超时
                        
                        # 可能收到部分数据或没有数据
                        assert len(chunks) <= 2


class TestStreamingAdvanced:
    """流式高级测试"""
    
    @pytest.mark.integration
    async def test_large_stream_handling(self, test_api_key: str, sample_template):
        """测试大型流数据处理"""
        async with AgentRuntimeClient(api_key=test_api_key) as client:
            with patch.object(client.template_manager, 'template_exists', return_value=True):
                with patch.object(client, '_create_sandbox_instance') as mock_create:
                    mock_sandbox = MockAsyncSandbox()
                    mock_create.return_value = mock_sandbox
                    
                    session = await client.create_session(sample_template.template_id)
                    
                    # Mock 大量数据流
                    async def large_stream():
                        for i in range(1000):  # 1000 个数据块
                            await asyncio.sleep(0.001)  # 小延迟
                            yield f"Large chunk {i}: " + "x" * 100  # 每块约 100 字符
                    
                    with patch.object(session, '_get_http_client') as mock_http_client:
                        mock_client_obj = AsyncMock()
                        mock_stream_response = Mock()
                        mock_stream_response.status_code = 200
                        mock_stream_response.aiter_text = large_stream
                        mock_client_obj.stream.return_value.__aenter__.return_value = mock_stream_response
                        mock_http_client.return_value = mock_client_obj
                        
                        import time
                        start_time = time.time()
                        
                        chunks = []
                        async for chunk in await session.invoke("Large stream test", stream=True):
                            chunks.append(chunk)
                        
                        end_time = time.time()
                        processing_time = end_time - start_time
                        
                        assert len(chunks) == 1000
                        assert processing_time < 5.0  # 应该在 5 秒内完成
                        
                        # 验证数据完整性
                        first_chunk = chunks[0]
                        last_chunk = chunks[-1]
                        assert "Large chunk 0:" in first_chunk
                        assert "Large chunk 999:" in last_chunk
    
    @pytest.mark.integration
    async def test_concurrent_streaming(self, test_api_key: str, sample_template):
        """测试并发流式处理"""
        async with AgentRuntimeClient(api_key=test_api_key) as client:
            with patch.object(client.template_manager, 'template_exists', return_value=True):
                with patch.object(client, '_create_sandbox_instance') as mock_create:
                    # 创建多个会话
                    sessions = []
                    for i in range(3):
                        mock_sandbox = MockAsyncSandbox()
                        mock_create.return_value = mock_sandbox
                        session = await client.create_session(f"template-{i}")
                        sessions.append(session)
                    
                    # 为每个会话设置流式响应
                    async def create_stream(session_id):
                        async def session_stream():
                            for i in range(10):
                                await asyncio.sleep(0.01)
                                yield f"Session {session_id} chunk {i}"
                        return session_stream
                    
                    # 并发执行流式调用
                    async def stream_session(session, session_id):
                        with patch.object(session, '_get_http_client') as mock_http_client:
                            mock_client_obj = AsyncMock()
                            mock_stream_response = Mock()
                            mock_stream_response.status_code = 200
                            mock_stream_response.aiter_text = await create_stream(session_id)
                            mock_client_obj.stream.return_value.__aenter__.return_value = mock_stream_response
                            mock_http_client.return_value = mock_client_obj
                            
                            chunks = []
                            async for chunk in await session.invoke(f"Concurrent stream {session_id}", stream=True):
                                chunks.append(chunk)
                            return chunks
                    
                    # 并发执行
                    tasks = [
                        stream_session(session, i)
                        for i, session in enumerate(sessions)
                    ]
                    
                    results = await asyncio.gather(*tasks)
                    
                    # 验证结果
                    assert len(results) == 3
                    for i, chunks in enumerate(results):
                        assert len(chunks) == 10
                        assert all(f"Session {i}" in chunk for chunk in chunks)
    
    @pytest.mark.integration
    async def test_streaming_memory_efficiency(self, test_api_key: str, sample_template):
        """测试流式处理内存效率"""
        import psutil
        import os
        
        async with AgentRuntimeClient(api_key=test_api_key) as client:
            with patch.object(client.template_manager, 'template_exists', return_value=True):
                with patch.object(client, '_create_sandbox_instance') as mock_create:
                    mock_sandbox = MockAsyncSandbox()
                    mock_create.return_value = mock_sandbox
                    
                    session = await client.create_session(sample_template.template_id)
                    
                    # 获取初始内存使用
                    process = psutil.Process(os.getpid())
                    initial_memory = process.memory_info().rss
                    
                    # Mock 大量数据流但立即处理（不存储）
                    async def memory_efficient_stream():
                        for i in range(500):
                            yield f"Memory test chunk {i}: " + "x" * 1000  # 每块约 1KB
                    
                    with patch.object(session, '_get_http_client') as mock_http_client:
                        mock_client_obj = AsyncMock()
                        mock_stream_response = Mock()
                        mock_stream_response.status_code = 200
                        mock_stream_response.aiter_text = memory_efficient_stream
                        mock_client_obj.stream.return_value.__aenter__.return_value = mock_stream_response
                        mock_http_client.return_value = mock_client_obj
                        
                        chunk_count = 0
                        total_size = 0
                        
                        async for chunk in await session.invoke("Memory efficiency test", stream=True):
                            chunk_count += 1
                            total_size += len(chunk)
                            # 立即处理数据，不存储
                            # 这模拟了真实的流式处理场景
                        
                        # 获取处理后内存使用
                        final_memory = process.memory_info().rss
                        memory_increase = final_memory - initial_memory
                        
                        assert chunk_count == 500
                        assert total_size > 500000  # 约 500KB 数据
                        # 内存增长应该远小于处理的数据总量
                        assert memory_increase < total_size * 0.1  # 内存增长应该小于数据量的 10%


class TestStreamingEdgeCases:
    """流式边界情况测试"""
    
    @pytest.mark.integration
    async def test_empty_stream(self, test_api_key: str, sample_template):
        """测试空流处理"""
        async with AgentRuntimeClient(api_key=test_api_key) as client:
            with patch.object(client.template_manager, 'template_exists', return_value=True):
                with patch.object(client, '_create_sandbox_instance') as mock_create:
                    mock_sandbox = MockAsyncSandbox()
                    mock_create.return_value = mock_sandbox
                    
                    session = await client.create_session(sample_template.template_id)
                    
                    # Mock 空流
                    async def empty_stream():
                        return
                        yield  # 永不执行
                    
                    with patch.object(session, '_get_http_client') as mock_http_client:
                        mock_client_obj = AsyncMock()
                        mock_stream_response = Mock()
                        mock_stream_response.status_code = 200
                        mock_stream_response.aiter_text = empty_stream
                        mock_client_obj.stream.return_value.__aenter__.return_value = mock_stream_response
                        mock_http_client.return_value = mock_client_obj
                        
                        chunks = []
                        async for chunk in await session.invoke("Empty stream test", stream=True):
                            chunks.append(chunk)
                        
                        assert len(chunks) == 0
    
    @pytest.mark.integration
    async def test_single_chunk_stream(self, test_api_key: str, sample_template):
        """测试单块流处理"""
        async with AgentRuntimeClient(api_key=test_api_key) as client:
            with patch.object(client.template_manager, 'template_exists', return_value=True):
                with patch.object(client, '_create_sandbox_instance') as mock_create:
                    mock_sandbox = MockAsyncSandbox()
                    mock_create.return_value = mock_sandbox
                    
                    session = await client.create_session(sample_template.template_id)
                    
                    # Mock 单块流
                    async def single_chunk_stream():
                        yield "This is the only chunk"
                    
                    with patch.object(session, '_get_http_client') as mock_http_client:
                        mock_client_obj = AsyncMock()
                        mock_stream_response = Mock()
                        mock_stream_response.status_code = 200
                        mock_stream_response.aiter_text = single_chunk_stream
                        mock_client_obj.stream.return_value.__aenter__.return_value = mock_stream_response
                        mock_http_client.return_value = mock_client_obj
                        
                        chunks = []
                        async for chunk in await session.invoke("Single chunk test", stream=True):
                            chunks.append(chunk)
                        
                        assert len(chunks) == 1
                        assert chunks[0] == "This is the only chunk"
    
    @pytest.mark.integration
    async def test_very_long_chunks(self, test_api_key: str, sample_template):
        """测试非常长的数据块"""
        async with AgentRuntimeClient(api_key=test_api_key) as client:
            with patch.object(client.template_manager, 'template_exists', return_value=True):
                with patch.object(client, '_create_sandbox_instance') as mock_create:
                    mock_sandbox = MockAsyncSandbox()
                    mock_create.return_value = mock_sandbox
                    
                    session = await client.create_session(sample_template.template_id)
                    
                    # Mock 超长块流
                    async def long_chunk_stream():
                        # 生成 1MB 的数据块
                        large_data = "x" * (1024 * 1024)
                        yield f"Large chunk start: {large_data} :Large chunk end"
                    
                    with patch.object(session, '_get_http_client') as mock_http_client:
                        mock_client_obj = AsyncMock()
                        mock_stream_response = Mock()
                        mock_stream_response.status_code = 200
                        mock_stream_response.aiter_text = long_chunk_stream
                        mock_client_obj.stream.return_value.__aenter__.return_value = mock_stream_response
                        mock_http_client.return_value = mock_client_obj
                        
                        chunks = []
                        async for chunk in await session.invoke("Long chunk test", stream=True):
                            chunks.append(chunk)
                        
                        assert len(chunks) == 1
                        chunk = chunks[0]
                        assert chunk.startswith("Large chunk start:")
                        assert chunk.endswith(":Large chunk end")
                        assert len(chunk) > 1024 * 1024  # 超过 1MB
    
    @pytest.mark.integration
    async def test_unicode_and_special_characters(self, test_api_key: str, sample_template):
        """测试 Unicode 和特殊字符"""
        async with AgentRuntimeClient(api_key=test_api_key) as client:
            with patch.object(client.template_manager, 'template_exists', return_value=True):
                with patch.object(client, '_create_sandbox_instance') as mock_create:
                    mock_sandbox = MockAsyncSandbox()
                    mock_create.return_value = mock_sandbox
                    
                    session = await client.create_session(sample_template.template_id)
                    
                    # Mock Unicode 和特殊字符流
                    async def unicode_stream():
                        unicode_chunks = [
                            "Hello 世界 🌍",
                            "Café ñandú 🦋",
                            "Привет мир 🇷🇺",
                            "こんにちは 世界 🗾",
                            "مرحبا بالعالم 🌍",
                            "Special chars: !@#$%^&*(){}[]|\\:;\"'<>?,./"
                        ]
                        for chunk in unicode_chunks:
                            yield chunk
                    
                    with patch.object(session, '_get_http_client') as mock_http_client:
                        mock_client_obj = AsyncMock()
                        mock_stream_response = Mock()
                        mock_stream_response.status_code = 200
                        mock_stream_response.aiter_text = unicode_stream
                        mock_client_obj.stream.return_value.__aenter__.return_value = mock_stream_response
                        mock_http_client.return_value = mock_client_obj
                        
                        chunks = []
                        async for chunk in await session.invoke("Unicode test", stream=True):
                            chunks.append(chunk)
                        
                        assert len(chunks) == 6
                        assert "Hello 世界 🌍" in chunks
                        assert "Café ñandú 🦋" in chunks
                        assert "Special chars:" in chunks[-1]
