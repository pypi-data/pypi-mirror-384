"""
认证管理器

管理客户端认证，使用 API Key 进行 Bearer Token 认证
"""

import os
import re
from typing import Dict, Optional

from .exceptions import AuthenticationError


class AuthManager:
    """认证管理器 - 简化版本，仅支持 API Key"""
    
    def __init__(self, api_key: Optional[str] = None):
        """初始化认证管理器
        
        Args:
            api_key: API 密钥，如果不提供则从环境变量 PPIO_API_KEY 读取
            
        Raises:
            AuthenticationError: API Key 未提供且环境变量不存在时抛出
        """
        # 区分 None 和空字符串：None 时使用环境变量，空字符串时直接使用
        if api_key is None:
            self._api_key = os.getenv("PPIO_API_KEY")
        else:
            self._api_key = api_key
        
        if not self._api_key:
            raise AuthenticationError(
                "API Key is required. Please provide it directly or set the PPIO_API_KEY environment variable."
            )
        
        # 验证 API Key 格式
        if not self._is_valid_api_key_format(self._api_key):
            raise AuthenticationError(
                "Invalid API Key format. API Key should be a non-empty string."
            )
    
    def _is_valid_api_key_format(self, api_key: str) -> bool:
        """验证 API Key 格式
        
        Args:
            api_key: 要验证的 API Key
            
        Returns:
            API Key 格式是否有效
        """
        if not api_key or not isinstance(api_key, str):
            return False
        
        # 基础验证：非空且长度合理
        if len(api_key.strip()) < 8:
            return False
        
        # 可以根据实际的 API Key 格式添加更多验证规则
        # 例如：特定前缀、长度、字符集等
        return True
    
    def validate_credentials(self) -> bool:
        """验证凭据有效性
        
        Returns:
            凭据是否有效（检查 API Key 是否存在且格式正确）
        """
        try:
            return bool(self._api_key and self._is_valid_api_key_format(self._api_key))
        except Exception:
            return False
    
    def get_auth_headers(self) -> Dict[str, str]:
        """获取认证头
        
        Returns:
            包含 Bearer Token 的认证头字典
            
        Example:
            {"Authorization": "Bearer your-api-key"}
        """
        if not self.validate_credentials():
            raise AuthenticationError("Invalid or missing API Key")
        
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json"
        }
    
    @property
    def api_key(self) -> str:
        """获取当前使用的 API Key"""
        if not self._api_key:
            raise AuthenticationError("API Key not available")
        return self._api_key
    
    def update_api_key(self, new_api_key: str) -> None:
        """更新 API Key
        
        Args:
            new_api_key: 新的 API Key
            
        Raises:
            AuthenticationError: 新 API Key 格式无效时抛出
        """
        if not self._is_valid_api_key_format(new_api_key):
            raise AuthenticationError("Invalid API Key format")
        
        self._api_key = new_api_key