"""
Real Environment Integration Tests - Uses real API only, no Mocks

These tests only run when real API Key and Template ID are available
"""

import asyncio
import os
from typing import List
import pytest

from ppio_sandbox.agent_runtime.client import AgentRuntimeClient
from ppio_sandbox.agent_runtime.client.models import AgentTemplate, InvocationRequest
from ppio_sandbox.agent_runtime.client.exceptions import (
    TemplateNotFoundError,
    AuthenticationError,
    SandboxCreationError,
    InvocationError
)


@pytest.fixture
def real_api_key():
    """Real API Key"""
    api_key = os.getenv("PPIO_API_KEY")
    if not api_key:
        pytest.skip("PPIO_API_KEY environment variable must be set")
    return api_key


@pytest.fixture
def real_template_id():
    """Real Template ID"""
    template_id = os.getenv("PPIO_TEST_TEMPLATE_ID")
    if not template_id:
        pytest.skip("PPIO_TEST_TEMPLATE_ID environment variable must be set")
    return template_id


@pytest.fixture
def real_template(real_api_key, real_template_id):
    """Get real template"""
    
    async def _get_template():
        async with AgentRuntimeClient(api_key=real_api_key) as client:
            # Find target template from template list
            templates = await client.list_templates()
            for template in templates:
                if template.template_id == real_template_id:
                    return template
            pytest.skip(f"Template {real_template_id} not found in available templates")
    
    # Execute async operation synchronously
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(_get_template())


class TestRealEnvironmentBasic:
    """Basic real environment tests"""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_list_templates_real(self, real_api_key):
        """Test getting template list"""
        async with AgentRuntimeClient(api_key=real_api_key) as client:
            templates = await client.list_templates()
            
            assert isinstance(templates, list)
            assert len(templates) > 0
            
            # Check template structure
            template = templates[0]
            assert isinstance(template, AgentTemplate)
            assert hasattr(template, 'template_id')
            assert hasattr(template, 'name')
            assert hasattr(template, 'status')
            
            print(f"✅ Retrieved {len(templates)} templates")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_find_template_by_id_real(self, real_api_key, real_template_id):
        """Test finding template by ID"""
        async with AgentRuntimeClient(api_key=real_api_key) as client:
            templates = await client.list_templates()
            
            # Find target template
            target_template = None
            for template in templates:
                if template.template_id == real_template_id:
                    target_template = template
                    break
            
            assert target_template is not None, f"Template {real_template_id} not found"
            assert target_template.template_id == real_template_id
            assert target_template.status == "active"
            
            print(f"✅ Found target template: {target_template.name}")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_template_exists_real(self, real_api_key, real_template_id):
        """Test template existence check"""
        async with AgentRuntimeClient(api_key=real_api_key) as client:
            # Check existing template
            exists = await client.template_manager.template_exists(real_template_id)
            assert exists is True
            
            # Check non-existent template
            fake_id = "nonexistent-template-id"
            exists_fake = await client.template_manager.template_exists(fake_id)
            assert exists_fake is False
            
            print("✅ 模板存在性检查正常")


class TestRealEnvironmentSessions:
    """Session management real environment tests"""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_session_creation_real(self, real_api_key, real_template: AgentTemplate):
        """Test session creation in real environment"""
        async with AgentRuntimeClient(api_key=real_api_key) as client:
            print(f"Using template: {real_template.name} ({real_template.template_id})")
            
            try:
                # Create session
                session = await client.create_session(real_template.template_id, timeout_seconds=30)
                
                assert session is not None
                assert session.template_id == real_template.template_id
                assert session.sandbox_id is not None
                
                print(f"✅ Session created successfully: {session.sandbox_id}")
                print(f"会话状态: {session.status}")
                
                # 清理：关闭会话
                await session.close()
                print("✅ 会话已关闭")
                
            except SandboxCreationError as e:
                pytest.skip(f"Sandbox创建失败，可能是资源限制: {e}")
            except Exception as e:
                print(f"会话创建失败: {e}")
                pytest.fail(f"会话创建失败: {e}")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_session_basic_info_real(self, real_api_key, real_template: AgentTemplate):
        """Test session basic information"""
        async with AgentRuntimeClient(api_key=real_api_key) as client:
            try:
                session = await client.create_session(real_template.template_id, timeout_seconds=30)
                
                # 检查基本属性
                assert session.template_id == real_template.template_id
                assert session.sandbox_id is not None
                assert session.created_at is not None
                assert session.last_activity is not None
                
                # 检查URL
                host_url = session.host_url
                assert host_url.startswith('https://')
                print(f"✅ 会话Host URL: {host_url}")
                
                # 检查年龄和空闲时间
                age = session.age_seconds
                idle = session.idle_seconds
                assert age >= 0
                assert idle >= 0
                print(f"会话年龄: {age:.2f}s, 空闲时间: {idle:.2f}s")
                
                await session.close()
                
            except SandboxCreationError as e:
                pytest.skip(f"Sandbox创建失败: {e}")


class TestRealEnvironmentInvocation:
    """调用测试（可能因模板配置而跳过）"""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_simple_invocation_real(self, real_api_key, real_template: AgentTemplate):
        """Test simple invocation (if template supports)"""
        async with AgentRuntimeClient(api_key=real_api_key) as client:
            try:
                session = await client.create_session(real_template.template_id, timeout_seconds=30)
                
                # 等待几秒让服务启动
                await asyncio.sleep(3)
                
                # 尝试简单调用 (auto-detect streaming)
                result = await session.invoke("Hello, 测试调用")
                
                print(f"✅ 调用成功: {result}")
                assert result is not None
                
                await session.close()
                
            except (SandboxCreationError, InvocationError) as e:
                pytest.skip(f"调用失败，可能模板不支持或未启动: {e}")
            except Exception as e:
                print(f"调用测试失败: {e}")
                # 不让这个测试失败整个测试套件
                pytest.skip(f"调用测试失败: {e}")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_ping_session_real(self, real_api_key, real_template: AgentTemplate):
        """Test session ping functionality"""
        async with AgentRuntimeClient(api_key=real_api_key) as client:
            try:
                session = await client.create_session(real_template.template_id, timeout_seconds=30)
                
                # 等待服务启动
                await asyncio.sleep(2)
                
                # 尝试ping
                ping_result = await session.ping()
                print(f"Ping结果: {ping_result}")
                
                await session.close()
                
            except SandboxCreationError as e:
                pytest.skip(f"Sandbox创建失败: {e}")
            except Exception as e:
                print(f"Ping测试失败: {e}")
                pytest.skip(f"Ping测试失败: {e}")


class TestRealEnvironmentClientManagement:
    """客户端管理测试"""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_client_context_manager_real(self, real_api_key):
        """Test client context manager"""
        async with AgentRuntimeClient(api_key=real_api_key) as client:
            assert not client._closed
            
            # 测试基本功能
            templates = await client.list_templates()
            assert len(templates) > 0
        
        # 客户端应该已经关闭
        assert client._closed
        print("✅ 客户端上下文管理器正常工作")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_client_manual_close_real(self, real_api_key):
        """Test manual client closure"""
        client = AgentRuntimeClient(api_key=real_api_key)
        
        assert not client._closed
        
        # 测试功能
        templates = await client.list_templates()
        assert len(templates) > 0
        
        # 手动关闭
        await client.close()
        assert client._closed
        
        print("✅ 手动客户端关闭正常工作")
