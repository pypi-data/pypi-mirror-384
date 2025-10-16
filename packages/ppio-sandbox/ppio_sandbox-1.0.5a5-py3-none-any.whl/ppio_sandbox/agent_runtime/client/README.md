# PPIO Agent Runtime Client

Agent Runtime Client 模块为后端开发者提供了与 PPIO Agent Sandbox 生态交互的完整客户端功能。

## 概述

Agent Runtime Client 是面向后端开发者的客户端 SDK，专门用于：

- **会话管理**：创建、管理和销毁 Sandbox 会话
- **Agent 调用**：同步和异步调用部署在 Sandbox 中的 Agent
- **模板管理**：查询和管理可用的 Agent 模板
- **流式响应**：支持实时的流式 Agent 响应
- **认证授权**：安全的 API Key 认证机制

## 核心组件

### 1. AgentRuntimeClient
主要的客户端接口，提供完整的 Agent 调用功能。

```python
from ppio_sandbox.agent_runtime.client import AgentRuntimeClient

async with AgentRuntimeClient() as client:
    # 调用 Agent
    response = await client.invoke_agent(
        template_id="your-agent-template-id",
        request="Hello, world!"
    )
    print(response.result)
```

### 2. SandboxSession
管理单个 Sandbox 实例的生命周期和 Agent 调用。

```python
# 创建会话
session = await client.create_session("template-id")

# 多轮对话
response1 = await session.invoke("First question")
response2 = await session.invoke("Follow-up question")

# 关闭会话
await session.close()
```

### 3. AuthManager
管理 API Key 认证。

```python
from ppio_sandbox.agent_runtime.client import AuthManager

# 从环境变量读取
auth = AuthManager()

# 或直接提供
auth = AuthManager(api_key="your-api-key")
```

### 4. TemplateManager
管理 Agent 模板查询。

```python
# 列出所有模板
templates = await client.list_templates()

# 按标签过滤
ai_templates = await client.list_templates(tags=["ai", "chat"])

# 获取特定模板
template = await client.get_template("template-id")
```

## 架构设计

### 设计理念
- **一对一关系**：每个 SandboxSession 对应一个独立的 Sandbox 实例
- **完整生命周期**：从创建、运行、暂停/恢复到销毁的完整管理
- **状态管理**：跟踪 Sandbox 和 Agent 的运行状态
- **资源控制**：确保 Sandbox 资源的正确分配和释放
- **简洁操作**：避免复杂的重启逻辑，需要清除状态时直接创建新会话

### 会话状态
- `ACTIVE`: 正在运行，可以处理请求
- `PAUSED`: 已暂停，保留状态但不处理请求
- `INACTIVE`: 非活跃状态
- `CLOSED`: 已关闭，资源已释放
- `ERROR`: 错误状态

## 使用示例

### 环境配置
```bash
# 设置 API Key
export PPIO_API_KEY=your-api-key-here
```

### 基础使用
```python
import asyncio
from ppio_sandbox.agent_runtime.client import AgentRuntimeClient, InvocationRequest

async def main():
    async with AgentRuntimeClient() as client:
        # 列出可用模板
        templates = await client.list_templates()
        
        # 调用 Agent
        response = await client.invoke_agent(
            template_id="your-template-id",
            request=InvocationRequest(
                prompt="分析这个数据",
                data={"dataset": "sales_data.csv"}
            )
        )
        
        print(f"结果: {response.result}")
        print(f"耗时: {response.duration:.2f}s")

asyncio.run(main())
```

### 会话管理
```python
async def session_example():
    async with AgentRuntimeClient() as client:
        # 创建长期会话
        session = await client.create_session("chat-agent-v1")
        
        try:
            # 多轮对话
            questions = ["你好", "你能做什么？", "帮我写代码"]
            
            for question in questions:
                response = await session.invoke(question)
                print(f"Q: {question}")
                print(f"A: {response['result']}")
                
        finally:
            await session.close()
```

### 流式响应
```python
async def streaming_example():
    async with AgentRuntimeClient() as client:
        # 流式调用
        stream = await client.invoke_agent_stream(
            template_id="writing-agent",
            request="写一个科幻故事"
        )
        
        async for chunk in stream:
            print(chunk, end="", flush=True)
```

### Sandbox 生命周期管理
```python
async def lifecycle_example():
    async with AgentRuntimeClient() as client:
        session = await client.create_session("data-processor")
        
        # 处理任务
        await session.invoke("开始处理数据")
        
        # 暂停以节省资源
        await session.pause()
        
        # 稍后恢复
        await session.resume()
        
        # 继续处理
        await session.invoke("继续处理")
        
        await session.close()
```

## 异常处理

模块提供了详细的异常体系：

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
    print("认证失败，请检查 API Key")
except TemplateNotFoundError:
    print("模板不存在")
except InvocationError as e:
    print(f"调用失败: {e}")
```

## 性能和最佳实践

### 连接池配置
```python
from ppio_sandbox.agent_runtime.client import ClientConfig

config = ClientConfig(
    max_connections=200,
    max_keepalive_connections=50,
    timeout=300
)

client = AgentRuntimeClient(config=config)
```

### 批量处理
```python
async def batch_process(requests):
    async with AgentRuntimeClient() as client:
        # 并发创建会话
        sessions = await asyncio.gather(*[
            client.create_session("batch-agent")
            for _ in range(len(requests))
        ])
        
        try:
            # 并发调用
            results = await asyncio.gather(*[
                session.invoke(req)
                for session, req in zip(sessions, requests)
            ])
            return results
        finally:
            # 并发关闭
            await asyncio.gather(*[
                session.close() for session in sessions
            ])
```

### 错误重试
```python
async def robust_call(template_id, request, max_retries=3):
    for attempt in range(max_retries):
        try:
            async with AgentRuntimeClient() as client:
                return await client.invoke_agent(template_id, request)
        except NetworkError:
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # 指数退避
                continue
            raise
```

## 集成框架

### Django 集成
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

### FastAPI 集成
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

## 模块文件结构

```
client/
├── __init__.py          # 模块导出
├── client.py           # AgentRuntimeClient 主类
├── session.py          # SandboxSession 会话管理
├── auth.py             # AuthManager 认证管理
├── template.py         # TemplateManager 模板管理
├── models.py           # 数据模型定义
├── exceptions.py       # 异常类定义
└── README.md           # 本文档
```

## 开发和测试

运行示例：
```bash
cd examples/agent_runtime
python client_example.py
```

确保设置了正确的环境变量：
```bash
export PPIO_API_KEY=your-api-key
```

## 版本信息

- **版本**: 1.0.0
- **Python 要求**: >= 3.8
- **主要依赖**: httpx, pydantic, asyncio
