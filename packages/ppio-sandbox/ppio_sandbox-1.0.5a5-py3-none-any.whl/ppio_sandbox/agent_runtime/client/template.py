"""
模板管理器

管理 Agent 模板的查询，专注核心功能
"""

import asyncio
import os
from datetime import datetime
from typing import List, Optional
import httpx
import json

from .auth import AuthManager
from .exceptions import TemplateNotFoundError, NetworkError, AuthenticationError
from .models import AgentTemplate


class TemplateManager:
    """模板管理器 - 简化版本"""
    
    def __init__(self, auth_manager: AuthManager, base_url: Optional[str] = None):
        """初始化模板管理器
        
        Args:
            auth_manager: 认证管理器
            base_url: API 基础 URL
        """
        self.auth_manager = auth_manager
        self.base_url = base_url or os.getenv("PPIO_API_BASE_URL", "https://api.ppio.ai")
        self._client = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """获取 HTTP 客户端"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0),
                headers=self.auth_manager.get_auth_headers()
            )
        return self._client
    
    async def close(self):
        """关闭 HTTP 客户端"""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def list_templates(
        self, 
        tags: Optional[List[str]] = None,
        name_filter: Optional[str] = None
    ) -> List[AgentTemplate]:
        """列出模板
        
        Args:
            tags: 标签过滤
            name_filter: 名称过滤
            
        Returns:
            模板列表，每个模板的 metadata 字段包含 Agent 元信息
        """
        try:
            client = await self._get_client()
            
            # 构建查询参数
            params = {}
            if tags:
                params["tags"] = ",".join(tags)
            if name_filter:
                params["name"] = name_filter
            
            response = await client.get(
                f"{self.base_url}/v1/templates/agents",
                params=params
            )
            
            if response.status_code == 401:
                raise AuthenticationError("Invalid or expired API Key")
            elif response.status_code != 200:
                raise NetworkError(f"Failed to list templates: {response.status_code} {response.text}")
            
            data = response.json()
            templates = []
            
            for template_data in data.get("templates", []):
                try:
                    template = AgentTemplate(
                        template_id=template_data["id"],
                        name=template_data.get("name", "Unknown"),
                        version=template_data.get("version", "1.0.0"),
                        description=template_data.get("description"),
                        author=template_data.get("author"),
                        tags=template_data.get("tags", []),
                        created_at=datetime.fromisoformat(
                            template_data.get("created_at", datetime.now().isoformat())
                        ),
                        updated_at=datetime.fromisoformat(
                            template_data.get("updated_at", datetime.now().isoformat())
                        ),
                        status=template_data.get("status", "active"),
                        metadata=template_data.get("metadata", {}),
                        size=template_data.get("size"),
                        build_time=template_data.get("build_time"),
                        dependencies=template_data.get("dependencies", []),
                        runtime_info=template_data.get("runtime_info")
                    )
                    templates.append(template)
                except Exception as e:
                    # 跳过无效的模板数据，记录错误但不中断处理
                    print(f"Warning: Failed to parse template data: {e}")
                    continue
            
            return templates
            
        except AuthenticationError:
            raise
        except NetworkError:
            raise
        except Exception as e:
            raise NetworkError(f"Failed to list templates: {str(e)}")
    
    async def get_template(self, template_id: str) -> AgentTemplate:
        """获取特定模板
        
        Args:
            template_id: 模板 ID
            
        Returns:
            模板对象，包含完整的 Agent 元信息
            
        Raises:
            TemplateNotFoundError: 模板不存在时抛出
        """
        try:
            client = await self._get_client()
            
            response = await client.get(
                f"{self.base_url}/v1/templates/agents/{template_id}"
            )
            
            if response.status_code == 401:
                raise AuthenticationError("Invalid or expired API Key")
            elif response.status_code == 404:
                raise TemplateNotFoundError(f"Template {template_id} not found")
            elif response.status_code != 200:
                raise NetworkError(f"Failed to get template: {response.status_code} {response.text}")
            
            template_data = response.json()
            
            return AgentTemplate(
                template_id=template_data["id"],
                name=template_data.get("name", "Unknown"),
                version=template_data.get("version", "1.0.0"),
                description=template_data.get("description"),
                author=template_data.get("author"),
                tags=template_data.get("tags", []),
                created_at=datetime.fromisoformat(
                    template_data.get("created_at", datetime.now().isoformat())
                ),
                updated_at=datetime.fromisoformat(
                    template_data.get("updated_at", datetime.now().isoformat())
                ),
                status=template_data.get("status", "active"),
                metadata=template_data.get("metadata", {}),
                size=template_data.get("size"),
                build_time=template_data.get("build_time"),
                dependencies=template_data.get("dependencies", []),
                runtime_info=template_data.get("runtime_info")
            )
            
        except AuthenticationError:
            raise
        except TemplateNotFoundError:
            raise
        except NetworkError:
            raise
        except Exception as e:
            raise NetworkError(f"Failed to get template: {str(e)}")
    
    async def template_exists(self, template_id: str) -> bool:
        """检查模板是否存在
        
        Args:
            template_id: 模板 ID
            
        Returns:
            模板是否存在
        """
        try:
            await self.get_template(template_id)
            return True
        except TemplateNotFoundError:
            return False
        except Exception:
            # 其他错误（如网络错误）时，保守地返回 False
            return False