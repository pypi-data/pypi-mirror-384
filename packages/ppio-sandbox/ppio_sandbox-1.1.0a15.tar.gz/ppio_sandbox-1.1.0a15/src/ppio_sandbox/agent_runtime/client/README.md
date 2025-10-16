# PPIO Agent Runtime Client

The Agent Runtime Client module provides backend developers with complete client functionality for interacting with the PPIO Agent Sandbox ecosystem.

## Overview

Agent Runtime Client is a client SDK for backend developers, specifically designed for:

- **Session Management**: Create, manage and destroy Sandbox sessions
- **Agent Invocation**: Synchronous and asynchronous invocation of Agents deployed in Sandbox
- **Template Management**: Query and manage available Agent templates
- **Streaming Response**: Support for real-time streaming Agent responses
- **Authentication & Authorization**: Secure API Key authentication mechanism

## Core Components

### 1. AgentRuntimeClient
Main client interface providing complete Agent invocation functionality.

```python
from ppio_sandbox.agent_runtime.client import AgentRuntimeClient

async with AgentRuntimeClient() as client:
    # Invoke Agent
    response = await client.invoke_agent(
        template_id="your-agent-template-id",
        request="Hello, world!"
    )
    print(response.result)
```

### 2. SandboxSession
Manages the lifecycle of a single Sandbox instance and Agent invocations.

```python
# Create session
session = await client.create_session("template-id")

# Multi-turn conversation
response1 = await session.invoke("First question")
response2 = await session.invoke("Follow-up question")

# Close session
await session.close()
```

### 3. AuthManager
Manages API Key authentication.

```python
from ppio_sandbox.agent_runtime.client import AuthManager

# Read from environment variable
auth = AuthManager()

# Or provide directly
auth = AuthManager(api_key="your-api-key")
```

### 4. TemplateManager
Manages Agent template queries.

```python
# List all templates
templates = await client.list_templates()

# Filter by tags
ai_templates = await client.list_templates(tags=["ai", "chat"])

# Get specific template
template = await client.get_template("template-id")
```

## Architecture Design

### Design Philosophy
- **One-to-One Relationship**: Each SandboxSession corresponds to an independent Sandbox instance
- **Complete Lifecycle**: Full management from creation, running, pause/resume to destruction
- **State Management**: Track Sandbox and Agent running states
- **Resource Control**: Ensure correct allocation and release of Sandbox resources
- **Simple Operations**: Avoid complex restart logic, create new session when state needs to be cleared

### Session States
- `ACTIVE`: Running, can process requests
- `PAUSED`: Paused, retains state but does not process requests
- `INACTIVE`: Inactive state
- `CLOSED`: Closed, resources released
- `ERROR`: Error state

## Usage Examples

### Environment Configuration
```bash
# Set API Key
export PPIO_API_KEY=your-api-key-here
```

### Basic Usage
```python
import asyncio
from ppio_sandbox.agent_runtime.client import AgentRuntimeClient, InvocationRequest

async def main():
    async with AgentRuntimeClient() as client:
        # List available templates
        templates = await client.list_templates()
        
        # Invoke Agent
        response = await client.invoke_agent(
            template_id="your-template-id",
            request=InvocationRequest(
                prompt="Analyze this data",
                data={"dataset": "sales_data.csv"}
            )
        )
        
        print(f"Result: {response.result}")
        print(f"Duration: {response.duration:.2f}s")

asyncio.run(main())
```

### Session Management
```python
async def session_example():
    async with AgentRuntimeClient() as client:
        # Create long-term session
        session = await client.create_session("chat-agent-v1")
        
        try:
            # Multi-turn conversation
            questions = ["Hello", "What can you do?", "Help me write code"]
            
            for question in questions:
                response = await session.invoke(question)
                print(f"Q: {question}")
                print(f"A: {response['result']}")
                
        finally:
            await session.close()
```

### Streaming Response
```python
async def streaming_example():
    async with AgentRuntimeClient() as client:
        # Streaming invocation
        stream = await client.invoke_agent_stream(
            template_id="writing-agent",
            request="Write a science fiction story"
        )
        
        async for chunk in stream:
            print(chunk, end="", flush=True)
```

### Sandbox Lifecycle Management
```python
async def lifecycle_example():
    async with AgentRuntimeClient() as client:
        session = await client.create_session("data-processor")
        
        # Process task
        await session.invoke("Start processing data")
        
        # Pause to save resources
        await session.pause()
        
        # Resume later
        await session.resume()
        
        # Continue processing
        await session.invoke("Continue processing")
        
        await session.close()
```

## Exception Handling

The module provides a detailed exception system:

```python
from ppio_sandbox.agent_runtime.client import (
    AuthenticationError,
    TemplateNotFoundError,
    SandboxCreationError,
    SessionNotFoundError,
    InvocationError,
    NetworkError
)

try:
    response = await client.invoke_agent(template_id, request)
except AuthenticationError:
    print("Authentication failed, please check API Key")
except TemplateNotFoundError:
    print("Template does not exist")
except InvocationError as e:
    print(f"Invocation failed: {e}")
```

## Performance and Best Practices

### Connection Pool Configuration
```python
from ppio_sandbox.agent_runtime.client import ClientConfig

config = ClientConfig(
    max_connections=200,
    max_keepalive_connections=50,
    timeout=300
)

client = AgentRuntimeClient(config=config)
```

### Batch Processing
```python
async def batch_process(requests):
    async with AgentRuntimeClient() as client:
        # Create sessions concurrently
        sessions = await asyncio.gather(*[
            client.create_session("batch-agent")
            for _ in range(len(requests))
        ])
        
        try:
            # Concurrent invocation
            results = await asyncio.gather(*[
                session.invoke(req)
                for session, req in zip(sessions, requests)
            ])
            return results
        finally:
            # Concurrent close
            await asyncio.gather(*[
                session.close() for session in sessions
            ])
```

### Error Retry
```python
async def robust_call(template_id, request, max_retries=3):
    for attempt in range(max_retries):
        try:
            async with AgentRuntimeClient() as client:
                return await client.invoke_agent(template_id, request)
        except NetworkError:
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                continue
            raise
```

## Framework Integration

### Django Integration
```python
from django.http import JsonResponse
from django.views import View

class AgentView(View):
    def __init__(self):
        self.client = AgentRuntimeClient()
    
    async def post(self, request):
        try:
            response = await self.client.invoke_agent(
                template_id="customer-service",
                request=request.POST.get("query")
            )
            return JsonResponse({"result": response.result})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
```

### FastAPI Integration
```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()
client = AgentRuntimeClient()

class ChatRequest(BaseModel):
    message: str
    template_id: str = "default-agent"

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        response = await client.invoke_agent(
            template_id=request.template_id,
            request=request.message
        )
        return {"response": response.result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## Module File Structure

```
client/
├── __init__.py          # Module exports
├── client.py           # AgentRuntimeClient main class
├── session.py          # SandboxSession session management
├── auth.py             # AuthManager authentication management
├── template.py         # TemplateManager template management
├── models.py           # Data model definitions
├── exceptions.py       # Exception class definitions
└── README.md           # This document
```

## Development and Testing

Run examples:
```bash
cd examples/agent_runtime
python client_example.py
```

Ensure correct environment variables are set:
```bash
export PPIO_API_KEY=your-api-key
```

## Version Information

- **Version**: 1.0.0
- **Python Requirements**: >= 3.8
- **Main Dependencies**: httpx, pydantic, asyncio
