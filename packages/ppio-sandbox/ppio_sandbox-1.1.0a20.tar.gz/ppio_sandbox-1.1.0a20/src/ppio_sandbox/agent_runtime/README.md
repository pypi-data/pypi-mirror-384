# PPIO Agent Runtime SDK

A lightweight AI agent runtime framework designed for the PPIO Agent Sandbox ecosystem.

## Overview

The PPIO Agent Runtime SDK provides two core modules:

1. **Agent Runtime Module**: For AI Agent developers to wrap Agent logic as standard HTTP services
2. **Agent Client Module**: For backend developers to call Agents deployed in Sandbox

## Features

- ✅ **Simple Agent Development**: Use decorators to create agents
- ✅ **Async/Sync Support**: Works with both synchronous and asynchronous functions
- ✅ **Streaming Responses**: Support for real-time streaming outputs
- ✅ **Session Management**: Automatic session lifecycle management
- ✅ **Authentication**: Built-in support for API key and HMAC authentication
- ✅ **Template Management**: Easy discovery and management of agent templates
- ✅ **Error Handling**: Comprehensive error handling and logging
- ✅ **Context Management**: Request context with metadata tracking
- ✅ **Health Checks**: Built-in health monitoring

## Quick Start

### Agent Development (Runtime Module)

```python
from ppio_sandbox.agent_runtime import PPIOAgentRuntimeApp, RequestContext

app = PPIOAgentRuntimeApp(debug=True)

@app.entrypoint
async def my_agent(request: dict, context: RequestContext) -> dict:
    query = request.get("query", "")
    
    # Your AI/ML logic here
    result = f"Processed: {query}"
    
    return {
        "response": result,
        "session_id": context.session_id,
        "timestamp": context.timestamp.isoformat()
    }

@app.ping
def health_check() -> dict:
    return {"status": "healthy", "service": "My Agent"}

if __name__ == "__main__":
    app.run(port=8080)
```

### Agent Client (Client Module)

```python
import asyncio
from ppio_sandbox.agent_runtime import AgentRuntimeClient, InvocationRequest

async def main():
    async with AgentRuntimeClient(
        api_key="your-api-key",
        api_secret="your-api-secret"
    ) as client:
        
        # Simple invocation
        response = await client.invoke_agent(
            template_id="your-template-id",
            request=InvocationRequest(
                prompt="Hello, world!",
                data={"user_id": "123"}
            )
        )
        
        print(f"Response: {response.result}")

asyncio.run(main())
```

## Architecture

```
PPIO Agent Runtime SDK
├── Agent Runtime Module
│   ├── PPIOAgentRuntimeApp (Main app class)
│   ├── PPIOAgentRuntimeServer (HTTP server)
│   ├── RequestContext (Context management)
│   └── Models (Data structures)
└── Agent Client Module
    ├── AgentRuntimeClient (Main client class)
    ├── SandboxSession (Session management)
    ├── AuthManager (Authentication)
    └── TemplateManager (Template discovery)
```

## Advanced Usage

### Streaming Responses

```python
@app.entrypoint
async def streaming_agent(request: dict, context: RequestContext):
    for i in range(10):
        await asyncio.sleep(0.1)
        yield f"Chunk {i + 1}"
```

### Session Management

```python
# Create and manage sessions manually
session = await client.create_session(
    template_id="your-template-id",
    timeout_seconds=600
)

try:
    response = await session.invoke(request)
    print(response.result)
finally:
    await session.close()
```

### Custom Authentication

```python
# Using HMAC authentication
client = AgentRuntimeClient(
    api_key="your-access-key",
    api_secret="your-secret-key"
)

# Using Bearer token
client = AgentRuntimeClient(api_key="your-bearer-token")
```

### Middleware

```python
@app.middleware
async def auth_middleware(context: RequestContext, request: InvocationRequest):
    # Custom authentication/validation logic
    if not request.metadata.get("user_id"):
        raise ValidationError("User ID required")
```

## Configuration

### Agent Configuration

```python
from ppio_sandbox.agent_runtime import AgentConfig

config = AgentConfig(
    host="0.0.0.0",
    port=8080,
    timeout=300,
    max_request_size=1024*1024,  # 1MB
    cors_origins=["*"],
    debug=False,
    log_level="INFO"
)

app = PPIOAgentRuntimeApp(config=config)
```

### Client Configuration

```python
from ppio_sandbox.agent_runtime import ClientConfig

config = ClientConfig(
    base_url="https://api.ppio.com",
    timeout=300,
    max_retries=3,
    enable_cache=True,
    cache_ttl=300
)

client = AgentRuntimeClient(
    api_key="your-key",
    config=config
)
```

## Error Handling

The SDK provides comprehensive error handling:

```python
from ppio_sandbox.agent_runtime import (
    PPIOAgentRuntimeError,
    AuthenticationError,
    TemplateNotFoundError,
    InvocationError,
    SessionNotFoundError
)

try:
    response = await client.invoke_agent(template_id, request)
except AuthenticationError:
    print("Authentication failed")
except TemplateNotFoundError:
    print("Template not found")
except InvocationError as e:
    print(f"Invocation failed: {e}")
```

## Examples

See the `examples/agent_runtime/` directory for complete examples:

- `simple_agent.py` - Basic agent implementation
- `streaming_agent.py` - Streaming response example
- `client_example.py` - Client usage examples

## Integration with PPIO Sandbox CLI

The Agent Runtime SDK integrates with the PPIO Sandbox CLI for deployment:

```bash
# Deploy an agent
ppio-sandbox-cli agent deploy --config .ppio-agent.yaml

# Test an agent
ppio-sandbox-cli agent invoke --template-id xxx --input "test query"

# List agent templates
ppio-sandbox-cli agent list
```

## Requirements

- Python 3.9+
- httpx>=0.27.0
- PPIO Sandbox SDK

## License

MIT License. See LICENSE file for details.
