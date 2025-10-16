"""
AuthManager 单元测试

测试 API Key 认证管理器的功能
"""

import os
import pytest
from unittest.mock import patch

from ppio_sandbox.agent_runtime.client.auth import AuthManager
from ppio_sandbox.agent_runtime.client.exceptions import AuthenticationError


class TestAuthManager:
    """AuthManager 测试类"""
    
    @pytest.mark.unit
    def test_init_with_api_key(self, test_api_key: str):
        """测试使用 API Key 初始化"""
        auth = AuthManager(api_key=test_api_key)
        assert auth.api_key == test_api_key
        assert auth.validate_credentials() is True
    
    @pytest.mark.unit
    def test_init_with_env_var(self, test_api_key: str):
        """测试从环境变量读取 API Key"""
        with patch.dict(os.environ, {"PPIO_API_KEY": test_api_key}):
            auth = AuthManager()
            assert auth.api_key == test_api_key
            assert auth.validate_credentials() is True
    
    @pytest.mark.unit
    def test_init_without_api_key(self):
        """测试没有 API Key 时抛出异常"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(AuthenticationError) as exc_info:
                AuthManager()
            
            assert "API Key is required" in str(exc_info.value)
    
    @pytest.mark.unit
    def test_init_with_empty_api_key(self):
        """测试空 API Key 时抛出异常"""
        with pytest.raises(AuthenticationError):
            AuthManager(api_key="")
    
    @pytest.mark.unit
    def test_init_with_short_api_key(self):
        """测试过短的 API Key 时抛出异常"""
        with pytest.raises(AuthenticationError):
            AuthManager(api_key="short")
    
    @pytest.mark.unit
    def test_validate_credentials_valid(self, auth_manager: AuthManager):
        """测试有效凭据验证"""
        assert auth_manager.validate_credentials() is True
    
    @pytest.mark.unit
    def test_validate_credentials_invalid(self):
        """测试无效凭据验证"""
        auth = AuthManager.__new__(AuthManager)  # 绕过 __init__
        auth._api_key = None
        assert auth.validate_credentials() is False
    
    @pytest.mark.unit
    def test_get_auth_headers_valid(self, auth_manager: AuthManager, test_api_key: str):
        """测试获取认证头"""
        headers = auth_manager.get_auth_headers()
        
        assert isinstance(headers, dict)
        assert "Authorization" in headers
        assert "Content-Type" in headers
        assert headers["Authorization"] == f"Bearer {test_api_key}"
        assert headers["Content-Type"] == "application/json"
    
    @pytest.mark.unit
    def test_get_auth_headers_invalid(self):
        """测试无效凭据时获取认证头抛出异常"""
        auth = AuthManager.__new__(AuthManager)  # 绕过 __init__
        auth._api_key = None
        
        with pytest.raises(AuthenticationError) as exc_info:
            auth.get_auth_headers()
        
        assert "Invalid or missing API Key" in str(exc_info.value)
    
    @pytest.mark.unit
    def test_api_key_property(self, auth_manager: AuthManager, test_api_key: str):
        """测试 API Key 属性访问"""
        assert auth_manager.api_key == test_api_key
    
    @pytest.mark.unit
    def test_api_key_property_unavailable(self):
        """测试 API Key 不可用时属性访问抛出异常"""
        auth = AuthManager.__new__(AuthManager)  # 绕过 __init__
        auth._api_key = None
        
        with pytest.raises(AuthenticationError) as exc_info:
            _ = auth.api_key
        
        assert "API Key not available" in str(exc_info.value)
    
    @pytest.mark.unit
    def test_update_api_key_valid(self, auth_manager: AuthManager):
        """测试更新有效的 API Key"""
        new_key = "new-test-api-key-87654321"
        auth_manager.update_api_key(new_key)
        
        assert auth_manager.api_key == new_key
        assert auth_manager.validate_credentials() is True
        
        headers = auth_manager.get_auth_headers()
        assert headers["Authorization"] == f"Bearer {new_key}"
    
    @pytest.mark.unit
    def test_update_api_key_invalid(self, auth_manager: AuthManager):
        """测试更新无效的 API Key"""
        with pytest.raises(AuthenticationError) as exc_info:
            auth_manager.update_api_key("short")
        
        assert "Invalid API Key format" in str(exc_info.value)
        
        # 原 API Key 应该保持不变
        assert auth_manager.validate_credentials() is True
    
    @pytest.mark.unit
    def test_update_api_key_empty(self, auth_manager: AuthManager):
        """测试更新空 API Key"""
        with pytest.raises(AuthenticationError):
            auth_manager.update_api_key("")
    
    @pytest.mark.unit
    def test_api_key_format_validation(self):
        """测试 API Key 格式验证逻辑"""
        auth = AuthManager.__new__(AuthManager)  # 绕过 __init__
        
        # 有效格式
        assert auth._is_valid_api_key_format("valid-api-key-12345678") is True
        assert auth._is_valid_api_key_format("sk-1234567890abcdef") is True
        assert auth._is_valid_api_key_format("a" * 20) is True
        
        # 无效格式
        assert auth._is_valid_api_key_format("") is False
        assert auth._is_valid_api_key_format("short") is False
        assert auth._is_valid_api_key_format("   ") is False
        assert auth._is_valid_api_key_format(None) is False
        assert auth._is_valid_api_key_format(123) is False
    
    @pytest.mark.unit
    def test_environment_variable_priority(self, test_api_key: str):
        """测试环境变量优先级"""
        env_key = "env-api-key-from-environment"
        
        with patch.dict(os.environ, {"PPIO_API_KEY": env_key}):
            # 直接提供的 API Key 应该优先于环境变量
            auth = AuthManager(api_key=test_api_key)
            assert auth.api_key == test_api_key
            
            # 不提供 API Key 时应该使用环境变量
            auth_env = AuthManager()
            assert auth_env.api_key == env_key
    
    @pytest.mark.unit
    def test_multiple_auth_headers_calls(self, auth_manager: AuthManager):
        """测试多次调用认证头获取的一致性"""
        headers1 = auth_manager.get_auth_headers()
        headers2 = auth_manager.get_auth_headers()
        
        assert headers1 == headers2
        assert headers1["Authorization"] == headers2["Authorization"]
    
    @pytest.mark.unit
    def test_auth_manager_immutable_headers(self, auth_manager: AuthManager):
        """测试认证头的不可变性"""
        headers = auth_manager.get_auth_headers()
        original_auth = headers["Authorization"]
        
        # 修改返回的字典不应该影响后续调用
        headers["Authorization"] = "modified"
        
        new_headers = auth_manager.get_auth_headers()
        assert new_headers["Authorization"] == original_auth
    
    @pytest.mark.unit
    def test_credentials_validation_edge_cases(self):
        """测试凭据验证的边界情况"""
        auth = AuthManager.__new__(AuthManager)  # 绕过 __init__
        
        # 异常情况
        auth._api_key = "valid-key-12345678"
        
        # Mock _is_valid_api_key_format 抛出异常
        with patch.object(auth, '_is_valid_api_key_format', side_effect=Exception("Test error")):
            assert auth.validate_credentials() is False


class TestAuthManagerIntegration:
    """AuthManager 集成测试"""
    
    @pytest.mark.unit
    def test_auth_manager_lifecycle(self):
        """测试认证管理器的完整生命周期"""
        # 1. 创建
        initial_key = "initial-api-key-12345678"
        auth = AuthManager(api_key=initial_key)
        
        # 2. 验证初始状态
        assert auth.validate_credentials() is True
        assert auth.api_key == initial_key
        
        # 3. 获取认证头
        headers = auth.get_auth_headers()
        assert headers["Authorization"] == f"Bearer {initial_key}"
        
        # 4. 更新 API Key
        new_key = "updated-api-key-87654321"
        auth.update_api_key(new_key)
        
        # 5. 验证更新后状态
        assert auth.api_key == new_key
        new_headers = auth.get_auth_headers()
        assert new_headers["Authorization"] == f"Bearer {new_key}"
        
        # 6. 验证旧的认证头不受影响
        assert headers["Authorization"] == f"Bearer {initial_key}"
    
    @pytest.mark.unit
    def test_concurrent_access_simulation(self, auth_manager: AuthManager):
        """模拟并发访问认证管理器"""
        import threading
        import time
        
        results = []
        
        def access_auth():
            """模拟访问认证管理器"""
            time.sleep(0.01)  # 模拟一些处理时间
            try:
                headers = auth_manager.get_auth_headers()
                results.append(headers["Authorization"])
            except Exception as e:
                results.append(f"Error: {e}")
        
        # 创建多个线程同时访问
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=access_auth)
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 验证所有结果都相同且正确
        assert len(results) == 10
        expected_auth = f"Bearer {auth_manager.api_key}"
        assert all(result == expected_auth for result in results)
