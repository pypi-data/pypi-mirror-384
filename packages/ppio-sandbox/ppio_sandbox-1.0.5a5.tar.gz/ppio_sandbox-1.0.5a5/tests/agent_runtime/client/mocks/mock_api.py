"""
Mock API 响应

模拟 HTTP API 响应，用于单元测试
"""

import asyncio
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, AsyncMock
from .test_fixtures import (
    create_mock_template_list_response,
    create_mock_template_response,
    create_mock_agent_response,
    create_mock_ping_response,
    create_auth_error_response,
    create_template_not_found_response,
    create_streaming_chunks
)


class MockHTTPClient:
    """Mock HTTP 客户端"""
    
    def __init__(self):
        self.request_history = []
        self.response_status = 200
        self.response_data = {}
        self.simulate_delay = 0.0
        self.simulate_error = None
    
    async def get(self, url: str, **kwargs) -> Mock:
        """Mock GET 请求"""
        await self._simulate_request_delay()
        
        if self.simulate_error:
            raise self.simulate_error
        
        # 记录请求历史
        self.request_history.append({
            "method": "GET",
            "url": url,
            "kwargs": kwargs
        })
        
        # 根据 URL 路径返回不同响应
        response = Mock()
        response.status_code = self.response_status
        
        if "/v1/templates/agents" in url and "templates" not in url.split("/")[-1]:
            # 单个模板查询
            template_id = url.split("/")[-1]
            if self.response_status == 404:
                response.text = "Template not found"
                response.json.side_effect = Exception("404 Not Found")
            else:
                response.json.return_value = create_mock_template_response(template_id)
        elif "/v1/templates/agents" in url:
            # 模板列表查询
            if self.response_status == 401:
                response.text = "Unauthorized"
                response.json.side_effect = Exception("401 Unauthorized")
            else:
                response.json.return_value = create_mock_template_list_response()
        elif "/ping" in url:
            # 健康检查
            response.json.return_value = create_mock_ping_response()
        else:
            # 默认响应
            response.json.return_value = self.response_data
        
        return response
    
    async def post(self, url: str, **kwargs) -> Mock:
        """Mock POST 请求"""
        await self._simulate_request_delay()
        
        if self.simulate_error:
            raise self.simulate_error
        
        # 记录请求历史
        self.request_history.append({
            "method": "POST",
            "url": url,
            "kwargs": kwargs
        })
        
        response = Mock()
        response.status_code = self.response_status
        
        if "/invocations" in url:
            # Agent 调用
            if self.response_status == 401:
                response.text = "Unauthorized"
                response.json.side_effect = Exception("401 Unauthorized")
            else:
                response.json.return_value = create_mock_agent_response()
        else:
            # 默认响应
            response.json.return_value = self.response_data
        
        return response
    
    async def stream(self, method: str, url: str, **kwargs):
        """Mock 流式请求"""
        await self._simulate_request_delay()
        
        if self.simulate_error:
            raise self.simulate_error
        
        # 记录请求历史
        self.request_history.append({
            "method": f"STREAM_{method}",
            "url": url,
            "kwargs": kwargs
        })
        
        return MockStreamingResponse()
    
    async def aclose(self):
        """Mock 关闭客户端"""
        pass
    
    async def _simulate_request_delay(self):
        """模拟请求延迟"""
        if self.simulate_delay > 0:
            await asyncio.sleep(self.simulate_delay)
    
    def set_response(self, status_code: int, data: Dict[str, Any]):
        """设置响应数据"""
        self.response_status = status_code
        self.response_data = data
    
    def set_error(self, error: Exception):
        """设置模拟错误"""
        self.simulate_error = error
    
    def set_delay(self, delay: float):
        """设置请求延迟"""
        self.simulate_delay = delay
    
    def clear_history(self):
        """清除请求历史"""
        self.request_history = []


class MockStreamingResponse:
    """Mock 流式响应"""
    
    def __init__(self):
        self.status_code = 200
        self.chunks = create_streaming_chunks()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
    
    async def aiter_text(self):
        """异步迭代文本块"""
        for chunk in self.chunks:
            await asyncio.sleep(0.01)  # 模拟网络延迟
            yield chunk
    
    async def aread(self):
        """读取完整响应"""
        return "Error response content"


# =============================================================================
# 预定义的 Mock 配置
# =============================================================================

def create_success_mock_client() -> MockHTTPClient:
    """创建成功响应的 Mock 客户端"""
    client = MockHTTPClient()
    client.set_response(200, {})
    return client


def create_auth_error_mock_client() -> MockHTTPClient:
    """创建认证错误的 Mock 客户端"""
    client = MockHTTPClient()
    client.set_response(401, create_auth_error_response())
    return client


def create_template_not_found_mock_client() -> MockHTTPClient:
    """创建模板不存在的 Mock 客户端"""
    client = MockHTTPClient()
    client.set_response(404, create_template_not_found_response())
    return client


def create_network_error_mock_client() -> MockHTTPClient:
    """创建网络错误的 Mock 客户端"""
    client = MockHTTPClient()
    client.set_error(Exception("Network connection failed"))
    return client


def create_slow_mock_client(delay: float = 1.0) -> MockHTTPClient:
    """创建慢速响应的 Mock 客户端"""
    client = MockHTTPClient()
    client.set_delay(delay)
    return client


# =============================================================================
# aioresponses 集成
# =============================================================================

def setup_template_responses(mock_client, base_url: str = "https://api.test.ppio.ai"):
    """设置模板相关的 Mock 响应"""
    # 模板列表
    mock_client.get(
        f"{base_url}/v1/templates/agents",
        payload=create_mock_template_list_response()
    )
    
    # 单个模板
    mock_client.get(
        f"{base_url}/v1/templates/agents/test-template-123",
        payload=create_mock_template_response("test-template-123")
    )
    
    # 模板不存在
    mock_client.get(
        f"{base_url}/v1/templates/agents/non-existent",
        status=404,
        payload=create_template_not_found_response()
    )


def setup_agent_responses(mock_client, base_url: str = "https://test-sandbox.ppio.ai"):
    """设置 Agent 相关的 Mock 响应"""
    # 成功调用
    mock_client.post(
        f"{base_url}/invocations",
        payload=create_mock_agent_response()
    )
    
    # 健康检查
    mock_client.get(
        f"{base_url}/ping",
        payload=create_mock_ping_response()
    )


def setup_error_responses(mock_client):
    """设置错误响应"""
    # 认证错误
    mock_client.get(
        "https://api.test.ppio.ai/v1/templates/agents",
        status=401,
        payload=create_auth_error_response()
    )
    
    # Agent 调用错误
    mock_client.post(
        "https://test-sandbox.ppio.ai/invocations",
        status=500,
        payload={
            "error": "Internal server error",
            "error_code": "AGENT_ERROR",
            "message": "Agent execution failed"
        }
    )
