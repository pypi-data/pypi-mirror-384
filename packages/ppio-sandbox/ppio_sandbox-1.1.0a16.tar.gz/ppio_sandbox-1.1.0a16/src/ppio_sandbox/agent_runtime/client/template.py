"""
Template Manager

Manages Agent template queries, focused on core functionality
"""

import asyncio
import os
from datetime import datetime
from typing import List, Optional

from ppio_sandbox.core.connection_config import ConnectionConfig
from ppio_sandbox.core.api import AsyncApiClient, handle_api_exception
from .auth import AuthManager
from .exceptions import TemplateNotFoundError, NetworkError, AuthenticationError
from .models import AgentTemplate


class TemplateManager:
    """Template Manager - Simplified version"""
    
    def __init__(self, auth_manager: AuthManager):
        """Initialize template manager
        
        Args:
            auth_manager: Authentication manager
        """
        self.auth_manager = auth_manager
        
        # Create connection config - following CLI project, use access_token
        self.connection_config = ConnectionConfig(
            access_token=self.auth_manager.api_key
        )
        self._client = None
    
    async def _get_client(self) -> AsyncApiClient:
        """Get API client"""
        if self._client is None:
            # Import httpx.Limits for connection pool configuration
            import httpx
            self._client = AsyncApiClient(
                self.connection_config, 
                require_api_key=False, 
                require_access_token=True,
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
            )
        return self._client
    
    async def close(self):
        """Close HTTP client"""
        if self._client:
            await self._client.get_async_httpx_client().aclose()
            self._client = None
    
    def _map_template_data_to_model(self, template_data: dict) -> AgentTemplate:
        """Map API returned template data to AgentTemplate model
        
        Args:
            template_data: Template data dictionary returned by API
            
        Returns:
            AgentTemplate object
        """
        return AgentTemplate(
            template_id=template_data.get("templateID") or template_data.get("id"),
            name=template_data.get("aliases", [None])[0] if template_data.get("aliases") else "Unknown",
            version=template_data.get("version", "1.0.0"),
            description=template_data.get("description"),
            author=template_data.get("createdBy", {}).get("email") if template_data.get("createdBy") else None,
            tags=template_data.get("tags", []),
            created_at=datetime.fromisoformat(
                template_data.get("createdAt", datetime.now().isoformat()).replace('Z', '+00:00')
            ) if template_data.get("createdAt") else datetime.now(),
            updated_at=datetime.fromisoformat(
                template_data.get("updatedAt", datetime.now().isoformat()).replace('Z', '+00:00')
            ) if template_data.get("updatedAt") else datetime.now(),
            status="active",  # CLI doesn't have status field, default to active
            metadata=template_data.get("metadata", {}),
            size=None,  # CLI doesn't have size field
            build_time=None,  # CLI doesn't have build_time field
            dependencies=[],  # CLI doesn't have dependencies field
            runtime_info=None  # CLI doesn't have runtime_info field
        )
    
    async def list_templates(
        self, 
        tags: Optional[List[str]] = None,
        name_filter: Optional[str] = None
    ) -> List[AgentTemplate]:
        """List templates
        
        Args:
            tags: Tag filter
            name_filter: Name filter
            
        Returns:
            Template list, each template's metadata field contains Agent metadata
        """
        try:
            client = await self._get_client()
            
            # Build query parameters
            params = {}
            if tags:
                params["tags"] = ",".join(tags)
            if name_filter:
                params["name"] = name_filter
            
            # Use ApiClient to make HTTP request
            response = await client.get_async_httpx_client().request(
                method="GET",
                url="/templates",
                params=params
            )
            
            # Handle response status code
            if response.status_code == 401:
                raise AuthenticationError("Invalid or expired API Key")
            elif response.status_code != 200:
                # Use handle_api_exception to handle errors
                from ppio_sandbox.core.api.client.types import Response as PPIOResponse
                ppio_response = PPIOResponse(
                    status_code=response.status_code,
                    content=response.content,
                    headers=response.headers,
                    parsed=None
                )
                raise handle_api_exception(ppio_response)
            
            data = response.json()
            templates = []
            
            # Process response data - based on CLI pattern, data should be template array directly
            template_list = data if isinstance(data, list) else data.get("templates", [])
            
            for template_data in template_list:
                try:
                    # Use private method to map template data
                    template = self._map_template_data_to_model(template_data)
                    templates.append(template)
                except Exception as e:
                    # Skip invalid template data, log error but don't interrupt processing
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
        """Get specific template
        
        Args:
            template_id: Template ID
            
        Returns:
            Template object containing complete Agent metadata
            
        Raises:
            TemplateNotFoundError: Raised when template does not exist
        """
        try:
            client = await self._get_client()
            
            # Use ApiClient to make HTTP request
            response = await client.get_async_httpx_client().request(
                method="GET",
                url=f"/templates/{template_id}"
            )
            
            # Handle response status code
            if response.status_code == 401:
                raise AuthenticationError("Invalid or expired API Key")
            elif response.status_code == 404:
                raise TemplateNotFoundError(f"Template {template_id} not found")
            elif response.status_code != 200:
                # Use handle_api_exception to handle errors
                from ppio_sandbox.core.api.client.types import Response as PPIOResponse
                ppio_response = PPIOResponse(
                    status_code=response.status_code,
                    content=response.content,
                    headers=response.headers,
                    parsed=None
                )
                raise handle_api_exception(ppio_response)
            
            template_data = response.json()
            
            # Use private method to map template data
            return self._map_template_data_to_model(template_data)
            
        except AuthenticationError:
            raise
        except TemplateNotFoundError:
            raise
        except NetworkError:
            raise
        except Exception as e:
            # Fallback: if direct template retrieval fails, try to find from list
            try:
                templates = await self.list_templates()
                for template in templates:
                    if template.template_id == template_id:
                        return template
                raise TemplateNotFoundError(f"Template {template_id} not found after fallback: {str(e)}")
            except (AuthenticationError, TemplateNotFoundError, NetworkError):
                raise
            except Exception as fallback_e:
                raise NetworkError(f"Failed to get template: {str(e)}. Fallback also failed: {str(fallback_e)}")
    
    async def template_exists(self, template_id: str) -> bool:
        """Check if template exists
        
        Args:
            template_id: Template ID
            
        Returns:
            Whether template exists
        """
        try:
            # Since single template API has issues, use list method to check
            templates = await self.list_templates()
            return any(template.template_id == template_id for template in templates)
        except Exception:
            # Consider template non-existent on network errors, etc.
            return False