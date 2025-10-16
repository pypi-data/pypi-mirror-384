"""
Agent Runtime 模块测试的共享配置和 Fixtures

提供测试用的标准化配置、Mock 对象和工具函数。
"""

import asyncio
import pytest
from datetime import datetime
from typing import Dict, Any, Generator, AsyncGenerator, List
from unittest.mock import Mock, AsyncMock

from ppio_sandbox.agent_runtime.runtime import (
    AgentRuntimeApp,
    AgentRuntimeServer,
    RuntimeConfig,
    AgentConfig,
    AgentMetadata,
    AgentSpec,
    RequestContext,
    InvocationRequest,
    InvocationResponse,
    PingResponse,
    PingStatus
)

from ppio_sandbox.agent_runtime.client import (
    AgentRuntimeClient,
    SandboxSession,
    AuthManager,
    TemplateManager,
    AgentTemplate,
    ClientConfig,
    SandboxConfig,
    SessionStatus,
    AuthenticationError,
    TemplateNotFoundError,
    SandboxCreationError,
    SessionNotFoundError,
    InvocationError,
    NetworkError
)


# =============================================================================
# 配置 Fixtures
# =============================================================================

@pytest.fixture
def runtime_config() -> RuntimeConfig:
    """提供测试用的运行时配置"""
    return RuntimeConfig(
        host="127.0.0.1",
        port=8888,  # 使用不同端口避免冲突
        debug=True,
        timeout=30,
        max_request_size=1024 * 512,  # 512KB
        cors_origins=["*"],
        enable_metrics=True,
        enable_middleware=True
    )


@pytest.fixture
def agent_config() -> AgentConfig:
    """提供测试用的 Agent 配置"""
    return AgentConfig(
        apiVersion="v1",
        kind="Agent",
        metadata=AgentMetadata(
            name="test-agent",
            version="1.0.0",
            author="test@example.com",
            description="Test Agent for unit testing",
            created="2024-01-01T00:00:00Z"
        ),
        spec=AgentSpec(
            entrypoint="test_agent.py"
        )
    )


@pytest.fixture
def sample_request() -> InvocationRequest:
    """提供示例调用请求"""
    return InvocationRequest(
        prompt="Test prompt",
        data={"key": "value"},
        sandbox_id="test-sandbox-123",
        timeout=30,
        stream=False,
        metadata={"test": True}
    )


@pytest.fixture
def sample_context() -> RequestContext:
    """提供示例请求上下文"""
    return RequestContext(
        sandbox_id="test-sandbox-123",
        request_id="test-request-456",
        headers={"Content-Type": "application/json"}
    )


# =============================================================================
# 应用和服务器 Fixtures
# =============================================================================

@pytest.fixture
def mock_app(runtime_config: RuntimeConfig) -> AgentRuntimeApp:
    """提供 Mock 的 AgentRuntimeApp"""
    app = AgentRuntimeApp(config=runtime_config)
    
    # 注册一个简单的测试 Agent
    @app.entrypoint
    def test_agent(request: dict, context: RequestContext) -> dict:
        return {
            "response": f"Processed: {request.get('prompt', '')}",
            "sandbox_id": context.sandbox_id,
            "request_id": context.request_id
        }
    
    # 注册健康检查
    @app.ping
    def test_ping() -> dict:
        return {"status": "healthy", "service": "test-agent"}
    
    return app


@pytest.fixture
def mock_streaming_app(runtime_config: RuntimeConfig) -> AgentRuntimeApp:
    """提供支持流式响应的 Mock AgentRuntimeApp"""
    app = AgentRuntimeApp(config=runtime_config)
    
    # 注册流式 Agent
    @app.entrypoint
    async def streaming_agent(request: dict, context: RequestContext) -> AsyncGenerator[str, None]:
        prompt = request.get('prompt', '')
        for i in range(3):
            await asyncio.sleep(0.01)  # 模拟处理时间
            yield f"Chunk {i}: {prompt}"
    
    return app


@pytest.fixture
def test_server(runtime_config: RuntimeConfig) -> AgentRuntimeServer:
    """提供测试服务器实例"""
    server = AgentRuntimeServer(runtime_config)
    
    # 设置测试用的入口点函数
    def test_entrypoint(request: dict) -> dict:
        return {"result": "test"}
    
    server.set_entrypoint_handler(test_entrypoint)
    return server


# =============================================================================
# Agent 函数 Fixtures
# =============================================================================

@pytest.fixture
def sync_agent_function():
    """同步 Agent 函数"""
    def agent(request: dict, context: RequestContext) -> dict:
        return {
            "response": "sync response",
            "request_data": request,
            "context_id": context.request_id
        }
    return agent


@pytest.fixture
def async_agent_function():
    """异步 Agent 函数"""
    async def agent(request: dict, context: RequestContext) -> dict:
        await asyncio.sleep(0.01)
        return {
            "response": "async response",
            "request_data": request,
            "context_id": context.request_id
        }
    return agent


@pytest.fixture
def sync_generator_agent():
    """同步生成器 Agent 函数"""
    def agent(request: dict) -> Generator[str, None, None]:
        for i in range(3):
            yield f"sync chunk {i}"
    return agent


@pytest.fixture
def async_generator_agent():
    """异步生成器 Agent 函数"""
    async def agent(request: dict) -> AsyncGenerator[str, None]:
        for i in range(3):
            await asyncio.sleep(0.01)
            yield f"async chunk {i}"
    return agent


@pytest.fixture
def error_agent_function():
    """抛出异常的 Agent 函数"""
    def agent(request: dict) -> dict:
        raise ValueError("Test error")
    return agent


# =============================================================================
# Mock HTTP 和网络 Fixtures
# =============================================================================

@pytest.fixture
def mock_http_client():
    """Mock HTTP 客户端"""
    client = AsyncMock()
    
    # 配置默认响应
    client.post.return_value.status_code = 200
    client.post.return_value.json.return_value = {
        "result": "mock response",
        "status": "success"
    }
    client.get.return_value.status_code = 200
    client.get.return_value.json.return_value = {
        "status": "healthy"
    }
    
    return client


# =============================================================================
# 测试数据 Fixtures
# =============================================================================

@pytest.fixture
def large_request_data() -> Dict[str, Any]:
    """大型请求数据（用于集成测试）"""
    return {
        "prompt": "Process this large dataset",
        "data": {
            "items": [{"id": i, "value": f"item_{i}"} for i in range(1000)]
        },
        "metadata": {
            "batch_size": 1000,
            "processing_mode": "bulk"
        }
    }


@pytest.fixture
def concurrent_requests() -> list:
    """并发请求数据集"""
    return [
        {"prompt": f"Request {i}", "data": {"id": i}}
        for i in range(100)
    ]


# =============================================================================
# 测试工具函数
# =============================================================================

@pytest.fixture
def assert_response_format():
    """验证响应格式的工具函数"""
    def _assert_format(response: dict, expected_keys: list = None):
        if expected_keys is None:
            expected_keys = ["result", "status", "duration"]
        
        assert isinstance(response, dict)
        for key in expected_keys:
            assert key in response
        
        if "status" in response:
            assert response["status"] in ["success", "error"]
        
        if "duration" in response:
            assert isinstance(response["duration"], (int, float))
            assert response["duration"] >= 0
    
    return _assert_format


@pytest.fixture
def assert_ping_format():
    """验证健康检查响应格式的工具函数"""
    def _assert_format(response: dict):
        assert isinstance(response, dict)
        assert "status" in response
        assert response["status"] in ["Healthy", "HealthyBusy"]
        
        if "timestamp" in response:
            assert isinstance(response["timestamp"], str)
        
        if "message" in response:
            assert isinstance(response["message"], str)
    
    return _assert_format


# =============================================================================
# Pytest 配置
# =============================================================================

def pytest_configure(config):
    """Pytest 配置"""
    config.addinivalue_line(
        "markers", "unit: 单元测试"
    )
    config.addinivalue_line(
        "markers", "integration: 集成测试"
    )
    config.addinivalue_line(
        "markers", "network: 需要网络的测试"
    )
    config.addinivalue_line(
        "markers", "slow: 慢速测试"
    )
    config.addinivalue_line(
        "markers", "compatibility: 兼容性测试"
    )


# =============================================================================
# 异步测试支持
# =============================================================================

# 移除自定义的 event_loop fixture，让 pytest-asyncio 使用默认的
# @pytest.fixture(scope="session")
# def event_loop():
#     """提供事件循环给整个测试会话"""
#     policy = asyncio.get_event_loop_policy()
#     loop = policy.new_event_loop()
#     yield loop
#     loop.close()


# =============================================================================
# 测试环境清理
# =============================================================================

@pytest.fixture(autouse=True)
def cleanup_context():
    """自动清理请求上下文"""
    from ppio_sandbox.agent_runtime.runtime.context import AgentRuntimeContext
    
    yield
    
    # 测试后清理上下文
    AgentRuntimeContext.clear_current_context()


@pytest.fixture
def temp_server_port():
    """提供临时服务器端口"""
    import socket
    
    # 找一个可用端口
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        port = s.getsockname()[1]
    
    return port


# =============================================================================
# Agent Runtime Client Fixtures
# =============================================================================

@pytest.fixture
def client_config() -> ClientConfig:
    """提供测试用的客户端配置"""
    return ClientConfig(
        base_url="https://api.test.ppio.ai",
        timeout=30,
        max_retries=3,
        retry_delay=1.0,
        max_connections=50,
        max_keepalive_connections=10,
        keepalive_expiry=30.0
    )


@pytest.fixture
def sandbox_config() -> SandboxConfig:
    """提供测试用的 Sandbox 配置"""
    return SandboxConfig(
        timeout_seconds=300,
        memory_limit="1Gi",
        cpu_limit="1",
        env_vars={"TEST_MODE": "true"},
        volumes=[],
        ports=[8080]
    )


@pytest.fixture
def test_api_key() -> str:
    """提供测试用的 API Key"""
    return "test-api-key-12345678"


@pytest.fixture
def auth_manager(test_api_key: str) -> AuthManager:
    """提供测试用的认证管理器"""
    return AuthManager(api_key=test_api_key)


@pytest.fixture
def sample_template() -> AgentTemplate:
    """提供示例 Agent 模板"""
    from datetime import datetime
    return AgentTemplate(
        template_id="test-template-123",
        name="test-agent",
        version="1.0.0",
        description="Test Agent Template",
        author="test@example.com",
        tags=["test", "ai", "chat"],
        created_at=datetime.now(),
        updated_at=datetime.now(),
        status="active",
        metadata={
            "agent": {
                "apiVersion": "v1",
                "kind": "Agent",
                "metadata": {
                    "name": "test-agent",
                    "version": "1.0.0",
                    "author": "test@example.com",
                    "description": "Test Agent Template",
                    "created": "2024-01-01T00:00:00Z"
                },
                "spec": {
                    "entrypoint": "agent.py",
                    "runtime": {
                        "timeout": 60,
                        "memory_limit": "1Gi",
                        "cpu_limit": "1"
                    },
                    "sandbox": {
                        "template_id": "test-template-123"
                    }
                },
                "status": {
                    "phase": "deployed",
                    "template_id": "test-template-123",
                    "last_deployed": "2024-01-01T00:00:00Z",
                    "build_id": "build-123"
                }
            }
        },
        size=1024 * 1024,  # 1MB
        build_time=30.5,
        dependencies=["python:3.11", "pydantic"],
        runtime_info={"python_version": "3.11", "packages": ["pydantic"]}
    )


@pytest.fixture
def sample_templates(sample_template: AgentTemplate) -> List[AgentTemplate]:
    """提供示例模板列表"""
    from datetime import datetime
    
    templates = [sample_template]
    
    # 添加更多测试模板
    for i in range(2, 5):
        template = AgentTemplate(
            template_id=f"test-template-{i}",
            name=f"test-agent-{i}",
            version=f"{i}.0.0",
            description=f"Test Agent Template {i}",
            author="test@example.com",
            tags=["test", "ai"] if i % 2 == 0 else ["test", "chat"],
            created_at=datetime.now(),
            updated_at=datetime.now(),
            status="active",
            metadata={},
            size=1024 * 512 * i,
            build_time=15.0 + i,
            dependencies=[],
            runtime_info={}
        )
        templates.append(template)
    
    return templates


@pytest.fixture
def mock_sandbox():
    """Mock Sandbox 实例"""
    sandbox = Mock()
    sandbox.id = "sandbox-test-123"
    sandbox.sandbox_id = "sandbox-test-123"
    sandbox.get_host.return_value = "test-sandbox.ppio.ai"
    
    # Mock 异步方法
    sandbox.pause = AsyncMock()
    sandbox.resume = AsyncMock()
    sandbox.close = AsyncMock()
    sandbox.kill = AsyncMock()
    
    return sandbox


@pytest.fixture
def mock_template_manager(sample_templates: List[AgentTemplate], auth_manager: AuthManager):
    """Mock TemplateManager"""
    manager = Mock(spec=TemplateManager)
    manager.auth_manager = auth_manager
    
    # Mock 异步方法
    manager.list_templates = AsyncMock(return_value=sample_templates)
    manager.get_template = AsyncMock(return_value=sample_templates[0])
    manager.template_exists = AsyncMock(return_value=True)
    manager.close = AsyncMock()
    
    return manager


@pytest.fixture
async def mock_sandbox_session(mock_sandbox, sample_template: AgentTemplate):
    """Mock SandboxSession"""
    session = Mock(spec=SandboxSession)
    session.template_id = sample_template.template_id
    session.sandbox = mock_sandbox
    session.sandbox_id = mock_sandbox.id
    session.session_id = mock_sandbox.id
    session.status = SessionStatus.ACTIVE
    session.created_at = datetime.now()
    session.last_activity = datetime.now()
    session.host_url = "https://test-sandbox.ppio.ai"
    session.is_active = True
    session.is_paused = False
    session.age_seconds = 0.0
    session.idle_seconds = 0.0
    
    # Mock 异步方法
    session.invoke = AsyncMock(return_value={"result": "test response"})
    session.ping = AsyncMock(return_value=PingResponse(status="healthy"))
    session.get_status = AsyncMock(return_value=SessionStatus.ACTIVE)
    session.pause = AsyncMock()
    session.resume = AsyncMock()
    session.refresh = AsyncMock()
    session.close = AsyncMock()
    
    return session


@pytest.fixture
async def mock_agent_client(
    client_config: ClientConfig,
    auth_manager: AuthManager,
    mock_template_manager,
    mock_sandbox_session
):
    """Mock AgentRuntimeClient"""
    client = Mock(spec=AgentRuntimeClient)
    client.config = client_config
    client.auth_manager = auth_manager
    client.template_manager = mock_template_manager
    client._sessions = {mock_sandbox_session.sandbox_id: mock_sandbox_session}
    client._closed = False
    
    # Mock 异步方法
    client.create_session = AsyncMock(return_value=mock_sandbox_session)
    client.get_session = AsyncMock(return_value=mock_sandbox_session)
    client.list_sessions = AsyncMock(return_value=[mock_sandbox_session])
    client.close_session = AsyncMock()
    client.close_all_sessions = AsyncMock()
    client.list_templates = AsyncMock(return_value=[])
    client.get_template = AsyncMock()
    client.invoke_agent = AsyncMock(return_value=InvocationResponse(
        result="test response",
        status="success",
        duration=0.5
    ))
    client.invoke_agent_stream = AsyncMock()
    client.close = AsyncMock()
    
    return client


# =============================================================================
# HTTP Mock Fixtures for Client Testing
# =============================================================================

@pytest.fixture
def mock_httpx_client():
    """Mock httpx.AsyncClient for HTTP requests"""
    client = AsyncMock()
    
    # Mock 成功的模板查询响应
    templates_response = Mock()
    templates_response.status_code = 200
    templates_response.json.return_value = {
        "templates": [
            {
                "id": "test-template-123",
                "name": "test-agent",
                "version": "1.0.0",
                "description": "Test Agent",
                "author": "test@example.com",
                "tags": ["test"],
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "status": "active",
                "metadata": {},
                "size": 1024,
                "build_time": 30.0
            }
        ]
    }
    
    # Mock 成功的 Agent 调用响应
    invoke_response = Mock()
    invoke_response.status_code = 200
    invoke_response.json.return_value = {
        "result": "test response",
        "status": "success",
        "duration": 0.5
    }
    
    # Mock 健康检查响应
    ping_response = Mock()
    ping_response.status_code = 200
    ping_response.json.return_value = {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z"
    }
    
    # 配置默认响应
    client.get.return_value = templates_response
    client.post.return_value = invoke_response
    client.aclose = AsyncMock()
    
    return client


@pytest.fixture
def mock_streaming_response():
    """Mock 流式响应"""
    async def mock_stream():
        chunks = ["chunk 1", "chunk 2", "chunk 3"]
        for chunk in chunks:
            yield chunk
    
    response = Mock()
    response.status_code = 200
    response.aiter_text = mock_stream
    
    return response


# =============================================================================
# Environment and Integration Test Fixtures
# =============================================================================

@pytest.fixture
def real_api_key():
    """真实的 API Key（从环境变量读取）"""
    import os
    return os.getenv("PPIO_API_KEY")


@pytest.fixture
async def real_client(real_api_key: str):
    """真实的 AgentRuntimeClient（用于集成测试）"""
    if not real_api_key:
        pytest.skip("PPIO_API_KEY not set - skipping integration test")
    
    client = AgentRuntimeClient(api_key=real_api_key)
    yield client
    await client.close()


# =============================================================================
# Concurrent Test Fixtures
# =============================================================================

@pytest.fixture
def concurrent_requests_data():
    """并发请求测试数据"""
    return [
        InvocationRequest(
            prompt=f"Test request {i}",
            data={"id": i, "batch": "concurrent_test"},
            metadata={"test_id": i}
        )
        for i in range(50)
    ]


@pytest.fixture
def large_request_data_client():
    """大型请求数据（客户端集成测试用）"""
    return InvocationRequest(
        prompt="Process this large dataset",
        data={
            "items": [
                {"id": i, "value": f"item_{i}", "data": "x" * 100}
                for i in range(1000)
            ]
        },
        metadata={
            "batch_size": 1000,
            "processing_mode": "bulk",
            "test": True
        },
        timeout=300
    )


# =============================================================================
# Test Utilities for Client
# =============================================================================

@pytest.fixture
def assert_client_response_format():
    """验证客户端响应格式的工具函数"""
    def _assert_format(response: InvocationResponse):
        assert isinstance(response, InvocationResponse)
        assert hasattr(response, 'result')
        assert hasattr(response, 'status')
        assert hasattr(response, 'duration')
        assert response.status in ["success", "error"]
        assert isinstance(response.duration, (int, float))
        assert response.duration >= 0
    
    return _assert_format


@pytest.fixture
def assert_template_format():
    """验证模板格式的工具函数"""
    def _assert_format(template: AgentTemplate):
        assert isinstance(template, AgentTemplate)
        assert template.template_id
        assert template.name
        assert template.version
        assert isinstance(template.tags, list)
        assert template.status
        assert isinstance(template.metadata, dict)
    
    return _assert_format


# =============================================================================
# Error Simulation Fixtures
# =============================================================================

@pytest.fixture
def mock_network_error_client():
    """模拟网络错误的 HTTP 客户端"""
    client = AsyncMock()
    client.get.side_effect = Exception("Network connection failed")
    client.post.side_effect = Exception("Network connection failed")
    return client


@pytest.fixture
def mock_auth_error_client():
    """模拟认证错误的 HTTP 客户端"""
    client = AsyncMock()
    
    error_response = Mock()
    error_response.status_code = 401
    error_response.text = "Unauthorized"
    
    client.get.return_value = error_response
    client.post.return_value = error_response
    
    return client


@pytest.fixture
def mock_template_not_found_client():
    """模拟模板不存在的 HTTP 客户端"""
    client = AsyncMock()
    
    # 列表查询返回空
    list_response = Mock()
    list_response.status_code = 200
    list_response.json.return_value = {"templates": []}
    
    # 单个查询返回 404
    get_response = Mock()
    get_response.status_code = 404
    get_response.text = "Template not found"
    
    client.get.side_effect = [list_response, get_response]
    
    return client
