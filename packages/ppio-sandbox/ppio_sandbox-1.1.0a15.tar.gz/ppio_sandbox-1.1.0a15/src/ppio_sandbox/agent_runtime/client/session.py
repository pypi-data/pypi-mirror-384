"""
Sandbox Session Management

Manages the lifecycle of a single Sandbox instance and Agent invocations
"""

from datetime import datetime
from typing import Any, AsyncIterator, Dict, Optional, Union
import httpx
from ppio_sandbox.core import AsyncSandbox

from .exceptions import (
    InvocationError, 
    NetworkError, 
    SandboxOperationError, 
    SessionNotFoundError
)
from .models import InvocationRequest, PingResponse, PingStatus, SessionStatus


class SandboxSession:
    """Sandbox session management"""
    
    def __init__(
        self,
        template_id: str,
        sandbox: AsyncSandbox,  # PPIO Sandbox instance
        client: "AgentRuntimeClient",
        agent_id: Optional[str] = None  # Optional agent_id for AWS compatibility
    ):
        """Initialize session
        
        Args:
            template_id: Template ID (internal identifier)
            sandbox: PPIO Sandbox instance (one-to-one relationship)
            client: Agent Runtime client reference
            agent_id: Optional agent_id for AWS Agentcore compatibility
        """
        self.template_id = template_id
        self.agent_id = agent_id  # AWS Agentcore compatible agent identifier
        self.sandbox = sandbox
        self._client_ref = client  # Avoid circular reference
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.status = SessionStatus.ACTIVE
        self._host_url: Optional[str] = None
        self._http_client: Optional[httpx.AsyncClient] = None
    
    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get HTTP client"""
        if self._http_client is None:
            # Get authentication headers from client reference
            auth_headers = self._client_ref.auth_manager.get_auth_headers()
            self._http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0),
                headers=auth_headers  # Use complete authentication headers, including Authorization
            )
        return self._http_client
    
    async def _close_http_client(self):
        """Close HTTP client"""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
    
    # === Core Invocation Methods ===
    async def invoke(
        self,
        request: Union[InvocationRequest, Dict[str, Any], str]
    ) -> Union[Dict[str, Any], AsyncIterator[str]]:
        """Invoke Agent (AWS Agentcore compatible - auto-detect streaming)
        
        The method automatically detects whether the Agent returns streaming or non-streaming
        response based on the Content-Type header:
        - Content-Type: application/json -> Returns Dict
        - Content-Type: text/event-stream -> Returns AsyncIterator
        
        Args:
            request: Invocation request (supports multiple formats: str, dict, InvocationRequest)
            
        Returns:
            Dict[str, Any] for non-streaming responses
            AsyncIterator[str] for streaming responses (auto-detected)
            
        Raises:
            InvocationError: Raised when invocation fails
            SessionNotFoundError: Raised when session does not exist
            NetworkError: Raised on network error
        """
        if self.status not in [SessionStatus.ACTIVE]:
            raise SessionNotFoundError(f"Session {self.sandbox_id} is not active (status: {self.status})")
        
        # Normalize request format
        if isinstance(request, str):
            request_data = InvocationRequest(input=request)
        elif isinstance(request, dict):
            request_data = InvocationRequest(**request)
        elif isinstance(request, InvocationRequest):
            request_data = request
        else:
            raise InvocationError("Invalid request format")
        
        try:
            self.last_activity = datetime.now()
            
            # Build request body
            request_body = self._build_request_body(request_data)
            request_url = f"{self.host_url}/invocations"
            client = await self._get_http_client()
            
            # Send request and get initial response to check Content-Type
            response = await client.post(
                request_url,
                json=request_body,
                timeout=httpx.Timeout(request_data.timeout or 300)
            )
            
            if response.status_code != 200:
                raise InvocationError(
                    f"Agent returned status {response.status_code} from URL [{request_url}]: {response.text}"
                )
            
            # Auto-detect response type based on Content-Type
            content_type = response.headers.get("content-type", "").lower()
            
            if self._is_streaming_response(content_type):
                # Streaming response - return async iterator
                return self._handle_streaming_response(response)
            else:
                # Non-streaming response - return JSON
                return response.json()
                
        except Exception as e:
            if "connection" in str(e).lower() or "timeout" in str(e).lower():
                raise NetworkError(f"Network error during invocation: {str(e)}")
            else:
                raise InvocationError(f"Agent invocation failed: {str(e)}")
    
    def _build_request_body(self, request: InvocationRequest) -> Dict[str, Any]:
        """Build request body for Agent invocation"""
        request_body = {}
        if request.input:
            request_body["prompt"] = request.input
        elif request.prompt:  # Backward compatibility
            request_body["prompt"] = request.prompt
        return request_body
    
    def _is_streaming_response(self, content_type: str) -> bool:
        """Check if response is streaming based on Content-Type header
        
        Args:
            content_type: Content-Type header value (lowercased)
            
        Returns:
            True if streaming, False otherwise
        """
        return "text/event-stream" in content_type or "application/x-ndjson" in content_type
    
    async def _handle_streaming_response(self, response: httpx.Response) -> AsyncIterator[str]:
        """Handle streaming response (SSE format)
        
        Args:
            response: httpx Response object
            
        Yields:
            Streamed data chunks
        """
        async for line in response.aiter_lines():
            # SSE format: "data: {json_content}"
            if line.startswith("data: "):
                data = line[6:]  # Remove "data: " prefix
                if data.strip():
                    yield data
            elif line.strip() and not line.startswith(":"):  # Not empty line or comment
                # Plain text chunk (not SSE format)
                yield line
    
    # === Sandbox Lifecycle Management ===
    async def pause(self) -> None:
        """Pause Sandbox instance
        
        After pausing:
        - Sandbox enters sleep state, retains memory state
        - Stops CPU computation, saves resources
        - Can resume execution via resume()
        
        Raises:
            SandboxOperationError: Raised when pause fails
        """
        try:
            if hasattr(self.sandbox, 'pause'):
                await self.sandbox.pause()
            else:
                # If sandbox doesn't have pause method, use API call
                await self._call_sandbox_api("pause")
            
            self.status = SessionStatus.PAUSED
            
        except Exception as e:
            raise SandboxOperationError(f"Failed to pause sandbox: {str(e)}")
    
    async def resume(self) -> None:
        """Resume Sandbox instance
        
        After resuming:
        - Sandbox recovers from paused state
        - Maintains previous memory state and context
        - Can continue processing requests
        
        Raises:
            SandboxOperationError: Raised when resume fails
        """
        try:
            if hasattr(self.sandbox, 'resume'):
                await self.sandbox.resume()
            else:
                # If sandbox doesn't have resume method, use API call
                await self._call_sandbox_api("resume")
            
            self.status = SessionStatus.ACTIVE
            
        except Exception as e:
            raise SandboxOperationError(f"Failed to resume sandbox: {str(e)}")
    
    async def _call_sandbox_api(self, action: str) -> None:
        """Call Sandbox API to execute operation"""
        # This needs to be implemented based on actual Sandbox API
        # Using mock implementation for now
        pass
    
    # === Session Management ===
    async def ping(self) -> PingResponse:
        """Health check
        
        Returns:
            Health check response
            
        Raises:
            NetworkError: Raised on network error
            InvocationError: Raised when check fails
        """
        try:
            client = await self._get_http_client()
            
            response = await client.get(
                f"{self.host_url}/ping",
                timeout=httpx.Timeout(10.0)
            )
            
            if response.status_code == 200:
                data = response.json()
                return PingResponse(
                    status=data.get("status", "healthy"),
                    message=data.get("message"),
                    timestamp=data.get("timestamp", datetime.now().isoformat())
                )
            else:
                return PingResponse(
                    status=PingStatus.HEALTHY_BUSY,  # Use enum value to represent error state
                    message=f"HTTP {response.status_code}: {response.text}",
                    timestamp=datetime.now().isoformat()
                )
                
        except Exception as e:
            if "connection" in str(e).lower() or "timeout" in str(e).lower():
                raise NetworkError(f"Network error during ping: {str(e)}")
            else:
                raise InvocationError(f"Ping failed: {str(e)}")
    
    async def get_status(self) -> SessionStatus:
        """Get session status
        
        Returns:
            Session status (ACTIVE, PAUSED, INACTIVE, CLOSED, ERROR)
        """
        # Can add actual status check logic
        try:
            # Try ping to confirm status
            ping_response = await self.ping()
            # Support multiple healthy status formats (case insensitive)
            healthy_statuses = ["healthy", "Healthy", "HealthyBusy", "healthybusy"]
            if ping_response.status in healthy_statuses:
                if self.status == SessionStatus.PAUSED:
                    return SessionStatus.PAUSED
                else:
                    return SessionStatus.ACTIVE
            else:
                return SessionStatus.ERROR
        except Exception:
            return SessionStatus.ERROR
    
    async def refresh(self) -> None:
        """Refresh session (reset timeout)"""
        self.last_activity = datetime.now()
        # Can add actual refresh logic, such as sending keepalive signal to Sandbox
    
    async def close(self) -> None:
        """Close session and destroy Sandbox
        
        Execution steps:
        1. Stop Agent service
        2. Destroy Sandbox instance
        3. Release all resources
        4. Update session status to CLOSED
        """
        try:
            # Close HTTP client
            await self._close_http_client()
            
            # Destroy Sandbox instance
            if hasattr(self.sandbox, 'close'):
                await self.sandbox.close()
            elif hasattr(self.sandbox, 'kill'):
                await self.sandbox.kill()
            
            self.status = SessionStatus.CLOSED
            
        except Exception as e:
            self.status = SessionStatus.ERROR
            raise SandboxOperationError(f"Failed to close session: {str(e)}")
    
    # === Properties ===
    @property
    def host_url(self) -> str:
        """Get Sandbox host URL"""
        if not self._host_url:
            if self.sandbox and hasattr(self.sandbox, 'get_host'):
                # Use actual Sandbox API
                host = self.sandbox.get_host(8080)
                self._host_url = f"https://{host}"
            else:
                # Mock URL (for testing)
                self._host_url = f"https://session-{self.sandbox_id}.ppio.sandbox"
        return self._host_url
    
    @property
    def is_active(self) -> bool:
        """Check if session is active"""
        return self.status == SessionStatus.ACTIVE
    
    @property
    def is_paused(self) -> bool:
        """Check if session is paused"""
        return self.status == SessionStatus.PAUSED
    
    @property
    def sandbox_id(self) -> str:
        """Get Sandbox instance ID (also session ID)"""
        if hasattr(self.sandbox, 'id'):
            return self.sandbox.id
        elif hasattr(self.sandbox, 'sandbox_id'):
            return self.sandbox.sandbox_id
        else:
            return f"sandbox-{id(self.sandbox)}"
    
    @property
    def session_id(self) -> str:
        """Get session ID (equivalent to sandbox_id)"""
        return self.sandbox_id
    
    @property
    def runtime_session_id(self) -> str:
        """Get runtime session ID (AWS Agentcore compatible)
        
        This property provides AWS-compatible session identification.
        In most cases, this is the same as sandbox_id, but may differ
        when user provides custom runtimeSessionId.
        """
        return self.sandbox_id
    
    @property
    def age_seconds(self) -> float:
        """Get session age in seconds"""
        return (datetime.now() - self.created_at).total_seconds()
    
    @property
    def idle_seconds(self) -> float:
        """Get session idle time in seconds"""
        return (datetime.now() - self.last_activity).total_seconds()
    
    def __repr__(self) -> str:
        agent_info = f", agent={self.agent_id}" if self.agent_id else ""
        return f"SandboxSession(id={self.sandbox_id}, status={self.status}, template={self.template_id}{agent_info})"