"""
Mock Sandbox 实例

模拟 Sandbox 实例的行为，用于单元测试
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
from unittest.mock import Mock, AsyncMock
from ppio_sandbox.agent_runtime.client.models import SessionStatus


class MockSandbox:
    """Mock Sandbox 实例"""
    
    def __init__(self, sandbox_id: str = "mock-sandbox-123"):
        self.id = sandbox_id
        self.sandbox_id = sandbox_id
        self.created_at = datetime.now()
        self.status = "running"
        self.template_id = "test-template-123"
        self.host = "mock-sandbox.ppio.ai"
        self.port = 8080
        
        # 模拟状态
        self._paused = False
        self._closed = False
        self._error = None
        
        # 操作历史
        self.operation_history = []
    
    def get_host(self, port: int = 8080) -> str:
        """获取主机地址"""
        self._record_operation("get_host", {"port": port})
        if self._closed:
            raise Exception("Sandbox is closed")
        return f"{self.host}:{port}"
    
    async def pause(self):
        """暂停 Sandbox"""
        self._record_operation("pause")
        if self._closed:
            raise Exception("Cannot pause closed sandbox")
        
        await asyncio.sleep(0.01)  # 模拟操作延迟
        self._paused = True
        self.status = "paused"
    
    async def resume(self):
        """恢复 Sandbox"""
        self._record_operation("resume")
        if self._closed:
            raise Exception("Cannot resume closed sandbox")
        
        await asyncio.sleep(0.01)  # 模拟操作延迟
        self._paused = False
        self.status = "running"
    
    async def close(self):
        """关闭 Sandbox"""
        self._record_operation("close")
        await asyncio.sleep(0.01)  # 模拟操作延迟
        self._closed = True
        self.status = "closed"
    
    async def kill(self):
        """强制终止 Sandbox"""
        self._record_operation("kill")
        await asyncio.sleep(0.01)  # 模拟操作延迟
        self._closed = True
        self.status = "killed"
    
    def is_paused(self) -> bool:
        """检查是否已暂停"""
        return self._paused
    
    def is_closed(self) -> bool:
        """检查是否已关闭"""
        return self._closed
    
    def set_error(self, error: Exception):
        """设置错误状态"""
        self._error = error
        self.status = "error"
    
    def _record_operation(self, operation: str, params: Optional[Dict[str, Any]] = None):
        """记录操作历史"""
        self.operation_history.append({
            "operation": operation,
            "timestamp": datetime.now(),
            "params": params or {}
        })
    
    def get_operation_count(self, operation: str) -> int:
        """获取特定操作的调用次数"""
        return sum(1 for op in self.operation_history if op["operation"] == operation)
    
    def clear_history(self):
        """清除操作历史"""
        self.operation_history = []


class MockAsyncSandbox(MockSandbox):
    """异步 Mock Sandbox - 对应 ppio_sandbox.core.AsyncSandbox"""
    
    def __init__(self, template_id: str = "test-template-123", **kwargs):
        super().__init__()
        self.template_id = template_id
        self.api_key = kwargs.get("api_key", "test-api-key")
        self.timeout = kwargs.get("timeout", 300)
        self.memory_mb = kwargs.get("memory_mb", 1024)
        self.cpu_count = kwargs.get("cpu_count", 1)
        
        # 启动状态
        self._started = False
    
    async def start(self):
        """启动 Sandbox"""
        self._record_operation("start")
        if self._closed:
            raise Exception("Cannot start closed sandbox")
        
        await asyncio.sleep(0.05)  # 模拟启动延迟
        self._started = True
        self.status = "running"
    
    async def stop(self):
        """停止 Sandbox"""
        self._record_operation("stop")
        await asyncio.sleep(0.02)  # 模拟停止延迟
        self._started = False
        self.status = "stopped"
    
    def is_started(self) -> bool:
        """检查是否已启动"""
        return self._started


class MockSandboxFactory:
    """Mock Sandbox 工厂"""
    
    def __init__(self):
        self.created_sandboxes = []
        self.creation_delay = 0.1
        self.creation_error = None
    
    async def create_sandbox(self, template_id: str, **kwargs) -> MockAsyncSandbox:
        """创建 Sandbox 实例"""
        if self.creation_error:
            raise self.creation_error
        
        await asyncio.sleep(self.creation_delay)
        
        sandbox = MockAsyncSandbox(template_id=template_id, **kwargs)
        await sandbox.start()
        
        self.created_sandboxes.append(sandbox)
        return sandbox
    
    def set_creation_delay(self, delay: float):
        """设置创建延迟"""
        self.creation_delay = delay
    
    def set_creation_error(self, error: Exception):
        """设置创建错误"""
        self.creation_error = error
    
    def get_sandbox_count(self) -> int:
        """获取已创建的 Sandbox 数量"""
        return len(self.created_sandboxes)
    
    def get_active_sandboxes(self) -> list:
        """获取活跃的 Sandbox"""
        return [s for s in self.created_sandboxes if not s.is_closed()]
    
    def close_all_sandboxes(self):
        """关闭所有 Sandbox"""
        async def _close_all():
            for sandbox in self.created_sandboxes:
                if not sandbox.is_closed():
                    await sandbox.close()
        
        return _close_all()


# =============================================================================
# 预定义的 Mock 实例
# =============================================================================

def create_healthy_sandbox(sandbox_id: str = "healthy-sandbox") -> MockSandbox:
    """创建健康的 Sandbox"""
    sandbox = MockSandbox(sandbox_id)
    sandbox.status = "running"
    return sandbox


def create_paused_sandbox(sandbox_id: str = "paused-sandbox") -> MockSandbox:
    """创建已暂停的 Sandbox"""
    sandbox = MockSandbox(sandbox_id)
    sandbox._paused = True
    sandbox.status = "paused"
    return sandbox


def create_error_sandbox(sandbox_id: str = "error-sandbox") -> MockSandbox:
    """创建错误状态的 Sandbox"""
    sandbox = MockSandbox(sandbox_id)
    sandbox.set_error(Exception("Simulated sandbox error"))
    return sandbox


def create_slow_sandbox(sandbox_id: str = "slow-sandbox", delay: float = 1.0) -> MockSandbox:
    """创建响应缓慢的 Sandbox"""
    sandbox = MockSandbox(sandbox_id)
    
    # 重写异步方法以添加延迟
    original_pause = sandbox.pause
    original_resume = sandbox.resume
    original_close = sandbox.close
    
    async def slow_pause():
        await asyncio.sleep(delay)
        return await original_pause()
    
    async def slow_resume():
        await asyncio.sleep(delay)
        return await original_resume()
    
    async def slow_close():
        await asyncio.sleep(delay)
        return await original_close()
    
    sandbox.pause = slow_pause
    sandbox.resume = slow_resume
    sandbox.close = slow_close
    
    return sandbox


# =============================================================================
# 测试工具函数
# =============================================================================

def assert_sandbox_state(sandbox: MockSandbox, expected_status: str):
    """断言 Sandbox 状态"""
    assert sandbox.status == expected_status


def assert_operation_called(sandbox: MockSandbox, operation: str, times: int = 1):
    """断言操作被调用了指定次数"""
    actual_times = sandbox.get_operation_count(operation)
    assert actual_times == times, f"Expected {operation} to be called {times} times, but was called {actual_times} times"


def assert_sandbox_not_closed(sandbox: MockSandbox):
    """断言 Sandbox 未关闭"""
    assert not sandbox.is_closed(), "Sandbox should not be closed"


def assert_sandbox_closed(sandbox: MockSandbox):
    """断言 Sandbox 已关闭"""
    assert sandbox.is_closed(), "Sandbox should be closed"
