"""
TemplateManager 单元测试

测试模板管理器的功能
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime

from ppio_sandbox.agent_runtime.client.template import TemplateManager
from ppio_sandbox.agent_runtime.client.auth import AuthManager
from ppio_sandbox.agent_runtime.client.exceptions import (
    TemplateNotFoundError,
    NetworkError,
    AuthenticationError
)
from ppio_sandbox.agent_runtime.client.models import AgentTemplate

from ..mocks.mock_api import (
    create_success_mock_client,
    create_auth_error_mock_client,
    create_template_not_found_mock_client,
    create_network_error_mock_client
)
from ..mocks.test_fixtures import create_sample_template, create_template_list


class TestTemplateManagerInit:
    """TemplateManager 初始化测试"""
    
    @pytest.mark.unit
    def test_template_manager_init(self, auth_manager: AuthManager):
        """测试模板管理器初始化"""
        manager = TemplateManager(auth_manager)
        
        assert manager.auth_manager is auth_manager
        assert manager.base_url == "https://api.ppio.ai"  # 默认 URL
        assert manager._client is None
    
    @pytest.mark.unit
    def test_template_manager_init_custom_url(self, auth_manager: AuthManager):
        """测试自定义 URL 初始化"""
        custom_url = "https://custom.api.com"
        manager = TemplateManager(auth_manager, base_url=custom_url)
        
        assert manager.base_url == custom_url
    
    @pytest.mark.unit
    def test_template_manager_init_env_url(self, auth_manager: AuthManager):
        """测试从环境变量读取 URL"""
        env_url = "https://env.api.com"
        with patch.dict('os.environ', {'PPIO_API_BASE_URL': env_url}):
            manager = TemplateManager(auth_manager)
            assert manager.base_url == env_url


class TestTemplateManagerHTTPClient:
    """TemplateManager HTTP 客户端测试"""
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    @pytest.mark.asyncio

    async def test_get_client_creation(self, auth_manager: AuthManager):
        """测试 HTTP 客户端创建"""
        manager = TemplateManager(auth_manager)
        
        client = await manager._get_client()
        
        assert client is not None
        assert manager._client is client
        
        # 第二次调用应该返回同一个客户端
        client2 = await manager._get_client()
        assert client2 is client
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    @pytest.mark.asyncio

    async def test_close_client(self, auth_manager: AuthManager):
        """测试关闭 HTTP 客户端"""
        manager = TemplateManager(auth_manager)
        
        # 创建客户端
        await manager._get_client()
        assert manager._client is not None
        
        # 关闭客户端
        await manager.close()
        assert manager._client is None


class TestTemplateManagerListTemplates:
    """TemplateManager 列出模板测试"""
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    @pytest.mark.asyncio

    async def test_list_templates_success(self, auth_manager: AuthManager):
        """测试成功列出模板"""
        manager = TemplateManager(auth_manager)
        mock_client = create_success_mock_client()
        
        with patch.object(manager, '_get_client', return_value=mock_client):
            templates = await manager.list_templates()
        
        assert isinstance(templates, list)
        assert len(templates) > 0
        assert all(isinstance(t, AgentTemplate) for t in templates)
        
        # 验证 HTTP 请求
        assert mock_client.get.called
        call_args = mock_client.get.call_args
        assert "/v1/templates/agents" in call_args[0][0]
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    @pytest.mark.asyncio

    async def test_list_templates_with_tags_filter(self, auth_manager: AuthManager):
        """测试按标签过滤模板"""
        manager = TemplateManager(auth_manager)
        mock_client = create_success_mock_client()
        
        with patch.object(manager, '_get_client', return_value=mock_client):
            await manager.list_templates(tags=["ai", "chat"])
        
        # 验证请求参数
        call_args = mock_client.get.call_args
        assert call_args[1]['params']['tags'] == "ai,chat"
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    @pytest.mark.asyncio

    async def test_list_templates_with_name_filter(self, auth_manager: AuthManager):
        """测试按名称过滤模板"""
        manager = TemplateManager(auth_manager)
        mock_client = create_success_mock_client()
        
        with patch.object(manager, '_get_client', return_value=mock_client):
            await manager.list_templates(name_filter="test-agent")
        
        # 验证请求参数
        call_args = mock_client.get.call_args
        assert call_args[1]['params']['name'] == "test-agent"
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    @pytest.mark.asyncio

    async def test_list_templates_auth_error(self, auth_manager: AuthManager):
        """测试认证错误"""
        manager = TemplateManager(auth_manager)
        mock_client = create_auth_error_mock_client()
        
        with patch.object(manager, '_get_client', return_value=mock_client):
            with pytest.raises(AuthenticationError) as exc_info:
                await manager.list_templates()
        
        assert "Invalid or expired API Key" in str(exc_info.value)
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    @pytest.mark.asyncio

    async def test_list_templates_network_error(self, auth_manager: AuthManager):
        """测试网络错误"""
        manager = TemplateManager(auth_manager)
        mock_client = create_network_error_mock_client()
        
        with patch.object(manager, '_get_client', return_value=mock_client):
            with pytest.raises(NetworkError) as exc_info:
                await manager.list_templates()
        
        assert "Failed to list templates" in str(exc_info.value)
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    @pytest.mark.asyncio

    async def test_list_templates_invalid_response(self, auth_manager: AuthManager):
        """测试无效响应处理"""
        manager = TemplateManager(auth_manager)
        mock_client = Mock()
        
        # 模拟返回无效的模板数据
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "templates": [
                {
                    "id": "invalid-template",
                    # 缺少必需字段
                }
            ]
        }
        mock_client.get = AsyncMock(return_value=mock_response)
        
        with patch.object(manager, '_get_client', return_value=mock_client):
            templates = await manager.list_templates()
        
        # 应该跳过无效模板，不抛出异常
        assert isinstance(templates, list)


class TestTemplateManagerGetTemplate:
    """TemplateManager 获取单个模板测试"""
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    @pytest.mark.asyncio

    async def test_get_template_success(self, auth_manager: AuthManager):
        """测试成功获取模板"""
        manager = TemplateManager(auth_manager)
        mock_client = create_success_mock_client()
        template_id = "test-template-123"
        
        with patch.object(manager, '_get_client', return_value=mock_client):
            template = await manager.get_template(template_id)
        
        assert isinstance(template, AgentTemplate)
        assert template.template_id == template_id
        
        # 验证 HTTP 请求
        call_args = mock_client.get.call_args
        assert f"/v1/templates/agents/{template_id}" in call_args[0][0]
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    @pytest.mark.asyncio

    async def test_get_template_not_found(self, auth_manager: AuthManager):
        """测试模板不存在"""
        manager = TemplateManager(auth_manager)
        mock_client = create_template_not_found_mock_client()
        template_id = "non-existent-template"
        
        with patch.object(manager, '_get_client', return_value=mock_client):
            with pytest.raises(TemplateNotFoundError) as exc_info:
                await manager.get_template(template_id)
        
        assert template_id in str(exc_info.value)
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    @pytest.mark.asyncio

    async def test_get_template_auth_error(self, auth_manager: AuthManager):
        """测试获取模板时的认证错误"""
        manager = TemplateManager(auth_manager)
        mock_client = create_auth_error_mock_client()
        
        with patch.object(manager, '_get_client', return_value=mock_client):
            with pytest.raises(AuthenticationError):
                await manager.get_template("any-template")
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    @pytest.mark.asyncio

    async def test_get_template_network_error(self, auth_manager: AuthManager):
        """测试获取模板时的网络错误"""
        manager = TemplateManager(auth_manager)
        mock_client = create_network_error_mock_client()
        
        with patch.object(manager, '_get_client', return_value=mock_client):
            with pytest.raises(NetworkError):
                await manager.get_template("any-template")


class TestTemplateManagerTemplateExists:
    """TemplateManager 模板存在检查测试"""
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    @pytest.mark.asyncio

    async def test_template_exists_true(self, auth_manager: AuthManager):
        """测试模板存在"""
        manager = TemplateManager(auth_manager)
        
        with patch.object(manager, 'get_template', return_value=create_sample_template()):
            exists = await manager.template_exists("existing-template")
        
        assert exists is True
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    @pytest.mark.asyncio

    async def test_template_exists_false(self, auth_manager: AuthManager):
        """测试模板不存在"""
        manager = TemplateManager(auth_manager)
        
        with patch.object(manager, 'get_template', side_effect=TemplateNotFoundError("Not found")):
            exists = await manager.template_exists("non-existing-template")
        
        assert exists is False
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    @pytest.mark.asyncio

    async def test_template_exists_error_handling(self, auth_manager: AuthManager):
        """测试其他错误时的处理"""
        manager = TemplateManager(auth_manager)
        
        # 网络错误等其他异常应该返回 False
        with patch.object(manager, 'get_template', side_effect=NetworkError("Network error")):
            exists = await manager.template_exists("any-template")
        
        assert exists is False


class TestTemplateManagerIntegration:
    """TemplateManager 集成测试"""
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    @pytest.mark.asyncio

    async def test_template_manager_lifecycle(self, auth_manager: AuthManager):
        """测试模板管理器完整生命周期"""
        manager = TemplateManager(auth_manager)
        
        try:
            # 1. 确保初始状态
            assert manager._client is None
            
            # 2. 模拟列出模板（会创建客户端）
            with patch.object(manager, '_get_client') as mock_get_client:
                mock_client = create_success_mock_client()
                mock_get_client.return_value = mock_client
                
                templates = await manager.list_templates()
                assert isinstance(templates, list)
                assert mock_get_client.called
            
            # 3. 模拟获取特定模板
            with patch.object(manager, '_get_client') as mock_get_client:
                mock_client = create_success_mock_client()
                mock_get_client.return_value = mock_client
                
                template = await manager.get_template("test-template-123")
                assert isinstance(template, AgentTemplate)
            
            # 4. 检查模板存在性
            with patch.object(manager, 'get_template', return_value=create_sample_template()):
                exists = await manager.template_exists("test-template-123")
                assert exists is True
        
        finally:
            # 5. 清理
            await manager.close()
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    @pytest.mark.asyncio

    async def test_concurrent_requests(self, auth_manager: AuthManager):
        """测试并发请求"""
        import asyncio
        
        manager = TemplateManager(auth_manager)
        mock_client = create_success_mock_client()
        
        with patch.object(manager, '_get_client', return_value=mock_client):
            # 并发执行多个请求
            tasks = [
                manager.list_templates(),
                manager.get_template("template-1"),
                manager.get_template("template-2"),
                manager.template_exists("template-3")
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 验证结果
            assert len(results) == 4
            assert isinstance(results[0], list)  # list_templates
            assert isinstance(results[1], AgentTemplate)  # get_template
            assert isinstance(results[2], AgentTemplate)  # get_template
            assert isinstance(results[3], bool)  # template_exists
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    @pytest.mark.asyncio

    async def test_error_recovery(self, auth_manager: AuthManager):
        """测试错误恢复"""
        manager = TemplateManager(auth_manager)
        
        # 第一次请求失败
        error_client = create_network_error_mock_client()
        with patch.object(manager, '_get_client', return_value=error_client):
            with pytest.raises(NetworkError):
                await manager.list_templates()
        
        # 第二次请求成功
        success_client = create_success_mock_client()
        with patch.object(manager, '_get_client', return_value=success_client):
            templates = await manager.list_templates()
            assert isinstance(templates, list)
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    @pytest.mark.asyncio

    async def test_request_parameters_validation(self, auth_manager: AuthManager):
        """测试请求参数验证"""
        manager = TemplateManager(auth_manager)
        mock_client = create_success_mock_client()
        
        with patch.object(manager, '_get_client', return_value=mock_client):
            # 测试各种参数组合
            await manager.list_templates()  # 无参数
            await manager.list_templates(tags=["ai"])  # 仅标签
            await manager.list_templates(name_filter="test")  # 仅名称
            await manager.list_templates(tags=["ai", "chat"], name_filter="test")  # 组合
        
        # 验证所有请求都被正确执行
        assert mock_client.get.call_count == 4
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    @pytest.mark.asyncio

    async def test_template_data_consistency(self, auth_manager: AuthManager):
        """测试模板数据一致性"""
        manager = TemplateManager(auth_manager)
        mock_client = Mock()
        
        # 模拟一致的模板数据
        template_data = {
            "id": "consistent-template",
            "name": "consistent-agent",
            "version": "1.0.0",
            "description": "Consistent test template",
            "author": "test@example.com",
            "tags": ["test"],
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "status": "active",
            "metadata": {},
            "size": 1024,
            "build_time": 30.0
        }
        
        # 列表响应
        list_response = Mock()
        list_response.status_code = 200
        list_response.json.return_value = {"templates": [template_data]}
        
        # 单个模板响应
        single_response = Mock()
        single_response.status_code = 200
        single_response.json.return_value = template_data
        
        mock_client.get = AsyncMock(side_effect=[list_response, single_response])
        
        with patch.object(manager, '_get_client', return_value=mock_client):
            # 从列表获取
            templates = await manager.list_templates()
            template_from_list = templates[0]
            
            # 直接获取
            template_direct = await manager.get_template("consistent-template")
            
            # 验证数据一致性
            assert template_from_list.template_id == template_direct.template_id
            assert template_from_list.name == template_direct.name
            assert template_from_list.version == template_direct.version
            assert template_from_list.author == template_direct.author
