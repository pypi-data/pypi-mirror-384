"""
上下文管理单元测试

测试 RequestContext 和 AgentRuntimeContext 的功能。
"""

import pytest
import asyncio
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from ppio_sandbox.agent_runtime.runtime.context import (
    RequestContext,
    AgentRuntimeContext,
)


class TestRequestContext:
    """RequestContext 模型测试"""
    
    @pytest.mark.unit
    def test_basic_context_creation(self):
        """测试基础上下文创建"""
        context = RequestContext(
            sandbox_id="sandbox-123",
            request_id="req-456",
            headers={"Content-Type": "application/json", "User-Agent": "test"}
        )
        
        assert context.sandbox_id == "sandbox-123"
        assert context.request_id == "req-456"
        assert context.headers["Content-Type"] == "application/json"
        assert context.headers["User-Agent"] == "test"
    
    @pytest.mark.unit
    def test_minimal_context(self):
        """测试最小上下文"""
        context = RequestContext()
        
        assert context.sandbox_id is None
        assert context.request_id is None
        assert context.headers == {}
    
    @pytest.mark.unit
    def test_backward_compatibility_session_id(self):
        """测试向后兼容的 session_id 属性"""
        context = RequestContext(sandbox_id="sandbox-123")
        
        # session_id 应该等于 sandbox_id
        assert context.session_id == "sandbox-123"
        assert context.session_id == context.sandbox_id
        
        # 测试 None 值
        context = RequestContext()
        assert context.session_id is None
    
    @pytest.mark.unit
    def test_extra_fields_allowed(self):
        """测试额外字段的处理（Pydantic extra="allow"）"""
        context = RequestContext(
            sandbox_id="test",
            request_id="req-123",
            custom_field="custom_value",
            another_field={"nested": "data"}
        )
        
        assert context.sandbox_id == "test"
        assert context.request_id == "req-123"
        # 额外字段应该被保存
        assert hasattr(context, 'custom_field')
        assert hasattr(context, 'another_field')
    
    @pytest.mark.unit
    def test_context_modification(self):
        """测试上下文修改"""
        context = RequestContext(sandbox_id="original")
        
        # 修改现有字段
        context.sandbox_id = "modified"
        assert context.sandbox_id == "modified"
        assert context.session_id == "modified"  # 确保向后兼容属性也更新
        
        # 添加新的 headers
        context.headers["Authorization"] = "Bearer token"
        assert context.headers["Authorization"] == "Bearer token"


class TestAgentRuntimeContext:
    """AgentRuntimeContext 管理器测试"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        # 确保开始时上下文是清除的
        AgentRuntimeContext.clear_current_context()
    
    def teardown_method(self):
        """每个测试方法后的清理"""
        # 确保测试后清理上下文
        AgentRuntimeContext.clear_current_context()
    
    @pytest.mark.unit
    def test_set_and_get_context(self):
        """测试设置和获取上下文"""
        # 初始状态应该没有上下文
        assert AgentRuntimeContext.get_current_context() is None
        
        # 创建并设置上下文
        context = RequestContext(
            sandbox_id="test-sandbox",
            request_id="test-request",
            headers={"Content-Type": "application/json"}
        )
        
        AgentRuntimeContext.set_current_context(context)
        
        # 获取上下文应该返回相同的对象
        retrieved_context = AgentRuntimeContext.get_current_context()
        assert retrieved_context is not None
        assert retrieved_context.sandbox_id == "test-sandbox"
        assert retrieved_context.request_id == "test-request"
        assert retrieved_context.headers["Content-Type"] == "application/json"
    
    @pytest.mark.unit
    def test_clear_context(self):
        """测试清除上下文"""
        # 设置上下文
        context = RequestContext(sandbox_id="test")
        AgentRuntimeContext.set_current_context(context)
        
        # 确认上下文已设置
        assert AgentRuntimeContext.get_current_context() is not None
        
        # 清除上下文
        AgentRuntimeContext.clear_current_context()
        
        # 确认上下文已清除
        assert AgentRuntimeContext.get_current_context() is None
    
    @pytest.mark.unit
    def test_context_override(self):
        """测试上下文覆盖"""
        # 设置第一个上下文
        context1 = RequestContext(sandbox_id="sandbox-1")
        AgentRuntimeContext.set_current_context(context1)
        
        assert AgentRuntimeContext.get_current_context().sandbox_id == "sandbox-1"
        
        # 设置第二个上下文（覆盖第一个）
        context2 = RequestContext(sandbox_id="sandbox-2")
        AgentRuntimeContext.set_current_context(context2)
        
        assert AgentRuntimeContext.get_current_context().sandbox_id == "sandbox-2"
    
    @pytest.mark.unit
    def test_thread_isolation(self):
        """测试线程隔离"""
        results = {}
        
        def worker_thread(thread_id: int):
            """工作线程函数"""
            # 每个线程设置自己的上下文
            context = RequestContext(sandbox_id=f"sandbox-{thread_id}")
            AgentRuntimeContext.set_current_context(context)
            
            # 短暂等待，让其他线程也设置上下文
            time.sleep(0.1)
            
            # 获取上下文，应该是自己设置的
            retrieved_context = AgentRuntimeContext.get_current_context()
            results[thread_id] = retrieved_context.sandbox_id if retrieved_context else None
        
        # 创建多个线程
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker_thread, args=(i,))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 验证每个线程都有自己的上下文
        for i in range(5):
            assert results[i] == f"sandbox-{i}"
        
        # 主线程应该没有上下文（或者有自己的上下文）
        main_context = AgentRuntimeContext.get_current_context()
        assert main_context is None  # 主线程没有设置上下文
    
    @pytest.mark.unit
    def test_async_context_isolation(self):
        """测试异步任务间的上下文隔离"""
        async def async_worker(task_id: int) -> Optional[str]:
            """异步工作函数"""
            # 每个任务设置自己的上下文
            context = RequestContext(sandbox_id=f"async-sandbox-{task_id}")
            AgentRuntimeContext.set_current_context(context)
            
            # 异步等待，让其他任务也有机会运行
            await asyncio.sleep(0.1)
            
            # 获取上下文，应该是自己设置的
            retrieved_context = AgentRuntimeContext.get_current_context()
            return retrieved_context.sandbox_id if retrieved_context else None
        
        async def test_async_isolation():
            # 并发运行多个异步任务
            tasks = [async_worker(i) for i in range(5)]
            results = await asyncio.gather(*tasks)
            
            # 验证每个任务都有自己的上下文
            for i, result in enumerate(results):
                assert result == f"async-sandbox-{i}"
        
        # 运行异步测试
        asyncio.run(test_async_isolation())
    
    @pytest.mark.unit
    def test_nested_context_operations(self):
        """测试嵌套上下文操作"""
        # 设置外层上下文
        outer_context = RequestContext(sandbox_id="outer")
        AgentRuntimeContext.set_current_context(outer_context)
        
        assert AgentRuntimeContext.get_current_context().sandbox_id == "outer"
        
        # 设置内层上下文
        inner_context = RequestContext(sandbox_id="inner")
        AgentRuntimeContext.set_current_context(inner_context)
        
        assert AgentRuntimeContext.get_current_context().sandbox_id == "inner"
        
        # 清除上下文
        AgentRuntimeContext.clear_current_context()
        
        # 应该完全清除，而不是回到外层上下文
        assert AgentRuntimeContext.get_current_context() is None
    
    @pytest.mark.unit
    def test_context_with_executor(self):
        """测试在线程池执行器中的上下文行为"""
        def worker_with_context(sandbox_id: str) -> Optional[str]:
            """在线程池中执行的工作函数"""
            context = RequestContext(sandbox_id=sandbox_id)
            AgentRuntimeContext.set_current_context(context)
            
            # 模拟一些工作
            time.sleep(0.05)
            
            retrieved_context = AgentRuntimeContext.get_current_context()
            return retrieved_context.sandbox_id if retrieved_context else None
        
        # 使用线程池执行器
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(worker_with_context, f"pool-sandbox-{i}")
                for i in range(5)
            ]
            
            results = [future.result() for future in futures]
        
        # 验证结果
        for i, result in enumerate(results):
            assert result == f"pool-sandbox-{i}"
    
    @pytest.mark.unit
    def test_context_persistence_across_calls(self):
        """测试上下文在多次调用间的持久性"""
        context = RequestContext(
            sandbox_id="persistent-sandbox",
            request_id="persistent-request"
        )
        
        AgentRuntimeContext.set_current_context(context)
        
        # 多次获取上下文，应该保持一致
        for _ in range(10):
            retrieved_context = AgentRuntimeContext.get_current_context()
            assert retrieved_context is not None
            assert retrieved_context.sandbox_id == "persistent-sandbox"
            assert retrieved_context.request_id == "persistent-request"
        
        # 修改上下文的某个属性
        retrieved_context = AgentRuntimeContext.get_current_context()
        retrieved_context.headers["Modified"] = "true"
        
        # 再次获取，修改应该保留
        final_context = AgentRuntimeContext.get_current_context()
        assert final_context.headers["Modified"] == "true"


class TestContextIntegration:
    """上下文集成测试"""
    
    def teardown_method(self):
        """清理测试后的上下文"""
        AgentRuntimeContext.clear_current_context()
    
    @pytest.mark.unit
    def test_context_in_function_calls(self):
        """测试在函数调用中传递上下文"""
        def process_request() -> Optional[str]:
            """模拟处理请求的函数"""
            context = AgentRuntimeContext.get_current_context()
            return context.sandbox_id if context else None
        
        def handle_request(sandbox_id: str) -> Optional[str]:
            """模拟处理请求的主函数"""
            context = RequestContext(sandbox_id=sandbox_id)
            AgentRuntimeContext.set_current_context(context)
            
            # 调用其他函数，它们应该能访问同样的上下文
            return process_request()
        
        # 测试函数调用链中的上下文传递
        result = handle_request("test-sandbox")
        assert result == "test-sandbox"
    
    @pytest.mark.unit
    def test_context_error_handling(self):
        """测试上下文在异常处理中的行为"""
        def function_that_raises():
            """抛出异常的函数"""
            context = AgentRuntimeContext.get_current_context()
            assert context is not None
            assert context.sandbox_id == "error-test"
            raise ValueError("Test error")
        
        context = RequestContext(sandbox_id="error-test")
        AgentRuntimeContext.set_current_context(context)
        
        # 即使函数抛出异常，上下文应该保持不变
        with pytest.raises(ValueError):
            function_that_raises()
        
        # 上下文应该仍然存在
        remaining_context = AgentRuntimeContext.get_current_context()
        assert remaining_context is not None
        assert remaining_context.sandbox_id == "error-test"
    
    @pytest.mark.unit
    async def test_async_context_propagation(self):
        """测试异步函数中的上下文传播"""
        async def async_processor() -> Optional[str]:
            """异步处理函数"""
            # 模拟异步操作
            await asyncio.sleep(0.01)
            
            context = AgentRuntimeContext.get_current_context()
            return context.sandbox_id if context else None
        
        async def async_handler(sandbox_id: str) -> Optional[str]:
            """异步处理主函数"""
            context = RequestContext(sandbox_id=sandbox_id)
            AgentRuntimeContext.set_current_context(context)
            
            # 调用其他异步函数
            return await async_processor()
        
        # 测试异步函数链中的上下文传播
        result = await async_handler("async-test")
        assert result == "async-test"