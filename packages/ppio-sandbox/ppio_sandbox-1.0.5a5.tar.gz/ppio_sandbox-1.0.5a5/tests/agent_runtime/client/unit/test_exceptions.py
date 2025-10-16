"""
异常类单元测试

测试客户端异常类的继承关系和功能
"""

import pytest

from ppio_sandbox.agent_runtime.client.exceptions import (
    AgentClientError,
    AuthenticationError,
    TemplateNotFoundError,
    SandboxCreationError,
    SessionNotFoundError,
    InvocationError,
    NetworkError,
    RateLimitError,
    QuotaExceededError,
    SandboxOperationError
)


class TestExceptionHierarchy:
    """异常继承关系测试"""
    
    @pytest.mark.unit
    def test_base_exception_inheritance(self):
        """测试基础异常继承"""
        error = AgentClientError("Test error")
        
        assert isinstance(error, Exception)
        assert isinstance(error, AgentClientError)
        assert str(error) == "Test error"
    
    @pytest.mark.unit
    def test_all_exceptions_inherit_from_base(self):
        """测试所有异常都继承自基础异常"""
        exception_classes = [
            AuthenticationError,
            TemplateNotFoundError,
            SandboxCreationError,
            SessionNotFoundError,
            InvocationError,
            NetworkError,
            RateLimitError,
            QuotaExceededError,
            SandboxOperationError
        ]
        
        for exc_class in exception_classes:
            error = exc_class("Test error")
            assert isinstance(error, AgentClientError)
            assert isinstance(error, Exception)
    
    @pytest.mark.unit
    def test_exception_inheritance_chain(self):
        """测试异常继承链"""
        error = AuthenticationError("Auth failed")
        
        # 验证继承链
        assert isinstance(error, AuthenticationError)
        assert isinstance(error, AgentClientError)
        assert isinstance(error, Exception)
        
        # 验证类型检查
        assert type(error) == AuthenticationError
        assert issubclass(AuthenticationError, AgentClientError)
        assert issubclass(AgentClientError, Exception)


class TestAgentClientError:
    """AgentClientError 基础异常测试"""
    
    @pytest.mark.unit
    def test_basic_creation(self):
        """测试基础创建"""
        message = "Test error message"
        error = AgentClientError(message)
        
        assert error.message == message
        assert error.error_code is None
        assert str(error) == message
    
    @pytest.mark.unit
    def test_creation_with_error_code(self):
        """测试带错误码的创建"""
        message = "Test error message"
        error_code = "TEST_ERROR"
        error = AgentClientError(message, error_code)
        
        assert error.message == message
        assert error.error_code == error_code
        assert str(error) == message
    
    @pytest.mark.unit
    def test_empty_message(self):
        """测试空错误消息"""
        error = AgentClientError("")
        
        assert error.message == ""
        assert str(error) == ""
    
    @pytest.mark.unit
    def test_none_error_code(self):
        """测试 None 错误码"""
        error = AgentClientError("Test", None)
        
        assert error.error_code is None


class TestSpecificExceptions:
    """特定异常类测试"""
    
    @pytest.mark.unit
    def test_authentication_error(self):
        """测试认证错误"""
        error = AuthenticationError("Invalid API key", "AUTH_FAILED")
        
        assert isinstance(error, AuthenticationError)
        assert isinstance(error, AgentClientError)
        assert error.message == "Invalid API key"
        assert error.error_code == "AUTH_FAILED"
    
    @pytest.mark.unit
    def test_template_not_found_error(self):
        """测试模板不存在错误"""
        template_id = "non-existent-template"
        error = TemplateNotFoundError(f"Template {template_id} not found", "TEMPLATE_NOT_FOUND")
        
        assert isinstance(error, TemplateNotFoundError)
        assert template_id in error.message
        assert error.error_code == "TEMPLATE_NOT_FOUND"
    
    @pytest.mark.unit
    def test_sandbox_creation_error(self):
        """测试 Sandbox 创建错误"""
        error = SandboxCreationError("Failed to create sandbox", "CREATION_FAILED")
        
        assert isinstance(error, SandboxCreationError)
        assert "create sandbox" in error.message
        assert error.error_code == "CREATION_FAILED"
    
    @pytest.mark.unit
    def test_session_not_found_error(self):
        """测试会话不存在错误"""
        session_id = "non-existent-session"
        error = SessionNotFoundError(f"Session {session_id} not found", "SESSION_NOT_FOUND")
        
        assert isinstance(error, SessionNotFoundError)
        assert session_id in error.message
        assert error.error_code == "SESSION_NOT_FOUND"
    
    @pytest.mark.unit
    def test_invocation_error(self):
        """测试调用错误"""
        error = InvocationError("Agent execution failed", "EXECUTION_FAILED")
        
        assert isinstance(error, InvocationError)
        assert "execution failed" in error.message.lower()
        assert error.error_code == "EXECUTION_FAILED"
    
    @pytest.mark.unit
    def test_network_error(self):
        """测试网络错误"""
        error = NetworkError("Connection timeout", "NETWORK_TIMEOUT")
        
        assert isinstance(error, NetworkError)
        assert "timeout" in error.message.lower()
        assert error.error_code == "NETWORK_TIMEOUT"
    
    @pytest.mark.unit
    def test_rate_limit_error(self):
        """测试限流错误"""
        error = RateLimitError("Rate limit exceeded", "RATE_LIMIT_EXCEEDED")
        
        assert isinstance(error, RateLimitError)
        assert "rate limit" in error.message.lower()
        assert error.error_code == "RATE_LIMIT_EXCEEDED"
    
    @pytest.mark.unit
    def test_quota_exceeded_error(self):
        """测试配额超限错误"""
        error = QuotaExceededError("Monthly quota exceeded", "QUOTA_EXCEEDED")
        
        assert isinstance(error, QuotaExceededError)
        assert "quota" in error.message.lower()
        assert error.error_code == "QUOTA_EXCEEDED"
    
    @pytest.mark.unit
    def test_sandbox_operation_error(self):
        """测试 Sandbox 操作错误"""
        error = SandboxOperationError("Failed to pause sandbox", "OPERATION_FAILED")
        
        assert isinstance(error, SandboxOperationError)
        assert "sandbox" in error.message.lower()
        assert error.error_code == "OPERATION_FAILED"


class TestExceptionCatching:
    """异常捕获测试"""
    
    @pytest.mark.unit
    def test_catch_specific_exception(self):
        """测试捕获特定异常"""
        with pytest.raises(AuthenticationError) as exc_info:
            raise AuthenticationError("Auth failed")
        
        assert exc_info.value.message == "Auth failed"
        assert isinstance(exc_info.value, AuthenticationError)
        assert isinstance(exc_info.value, AgentClientError)
    
    @pytest.mark.unit
    def test_catch_base_exception(self):
        """测试捕获基础异常"""
        with pytest.raises(AgentClientError) as exc_info:
            raise TemplateNotFoundError("Template not found")
        
        assert isinstance(exc_info.value, TemplateNotFoundError)
        assert isinstance(exc_info.value, AgentClientError)
    
    @pytest.mark.unit
    def test_catch_multiple_exception_types(self):
        """测试捕获多种异常类型"""
        exceptions_to_test = [
            AuthenticationError("Auth error"),
            NetworkError("Network error"),
            InvocationError("Invocation error")
        ]
        
        for exc in exceptions_to_test:
            with pytest.raises(AgentClientError) as exc_info:
                raise exc
            
            assert isinstance(exc_info.value, type(exc))
            assert isinstance(exc_info.value, AgentClientError)
    
    @pytest.mark.unit
    def test_exception_distinction(self):
        """测试异常区分"""
        auth_error = AuthenticationError("Auth failed")
        network_error = NetworkError("Network failed")
        
        # 它们都是 AgentClientError，但类型不同
        assert isinstance(auth_error, AgentClientError)
        assert isinstance(network_error, AgentClientError)
        assert type(auth_error) != type(network_error)
        assert not isinstance(auth_error, NetworkError)
        assert not isinstance(network_error, AuthenticationError)


class TestExceptionProperties:
    """异常属性测试"""
    
    @pytest.mark.unit
    def test_exception_message_property(self):
        """测试异常消息属性"""
        message = "Detailed error message"
        error = AgentClientError(message)
        
        assert error.message == message
        assert str(error) == message
        assert repr(error)  # 确保 repr 不会出错
    
    @pytest.mark.unit
    def test_exception_error_code_property(self):
        """测试异常错误码属性"""
        error_code = "SPECIFIC_ERROR_CODE"
        error = AgentClientError("Error", error_code)
        
        assert error.error_code == error_code
    
    @pytest.mark.unit
    def test_exception_args_compatibility(self):
        """测试异常参数兼容性"""
        message = "Test message"
        error = AgentClientError(message)
        
        # 验证 args 属性（Python 标准异常接口）
        assert error.args == (message,)
        assert len(error.args) == 1
        assert error.args[0] == message
    
    @pytest.mark.unit
    def test_exception_with_different_message_types(self):
        """测试不同消息类型的异常"""
        # 字符串消息
        str_error = AgentClientError("String message")
        assert str_error.message == "String message"
        
        # None 消息（虽然不推荐）
        none_error = AgentClientError(None)
        assert none_error.message is None


class TestExceptionIntegration:
    """异常集成测试"""
    
    @pytest.mark.unit
    def test_exception_in_try_except_chains(self):
        """测试异常在 try-except 链中的行为"""
        def raise_auth_error():
            raise AuthenticationError("Auth failed", "AUTH_ERROR")
        
        def raise_network_error():
            raise NetworkError("Network failed", "NETWORK_ERROR")
        
        # 测试特定异常捕获
        with pytest.raises(AuthenticationError):
            raise_auth_error()
        
        # 测试基类异常捕获
        with pytest.raises(AgentClientError):
            raise_network_error()
        
        # 测试异常链
        with pytest.raises(NetworkError) as exc_info:
            try:
                raise_auth_error()
            except AuthenticationError as e:
                assert e.error_code == "AUTH_ERROR"
                # 重新抛出为不同类型的异常
                raise NetworkError(f"Network issue caused by: {e.message}")
        
        # 验证链式异常信息
        assert "Network issue caused by: Auth failed" in str(exc_info.value)
    
    @pytest.mark.unit
    def test_exception_information_preservation(self):
        """测试异常信息保持"""
        original_message = "Original error message"
        original_code = "ORIGINAL_CODE"
        
        # 创建异常
        error = InvocationError(original_message, original_code)
        
        # 验证信息保持
        assert error.message == original_message
        assert error.error_code == original_code
        assert str(error) == original_message
        
        # 重新抛出和捕获
        with pytest.raises(InvocationError) as exc_info:
            raise error
        
        caught_error = exc_info.value
        assert caught_error.message == original_message
        assert caught_error.error_code == original_code
        assert caught_error is error  # 同一个对象
