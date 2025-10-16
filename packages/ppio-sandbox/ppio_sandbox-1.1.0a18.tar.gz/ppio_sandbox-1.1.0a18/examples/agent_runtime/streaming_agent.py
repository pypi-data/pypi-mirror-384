"""
流式 Agent Runtime 使用示例

这个示例展示了如何实现支持流式响应的 Agent。
"""

import asyncio
from datetime import datetime
from ppio_sandbox.agent_runtime import AgentRuntimeApp, RequestContext, RuntimeConfig

# 自定义配置
config = RuntimeConfig(
    port=8080,
    timeout=600,
    max_request_size=2 * 1024 * 1024,  # 2MB
    cors_origins=["*"]
)

app = AgentRuntimeApp(config=config)


@app.entrypoint
async def streaming_agent(request: dict, context: RequestContext):
    """异步流式 Agent"""
    query = request.get("query", "")
    max_tokens = request.get("max_tokens", 100)
    
    # 模拟 LLM 流式响应
    for i in range(max_tokens // 10):
        await asyncio.sleep(0.1)  # 模拟处理时间
        yield f"Token {i}: 处理 '{query}' 的部分结果...\n"
    
    yield f"完成对 '{query}' 的处理。"


@app.ping
async def async_health_check() -> dict:
    """异步健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "streaming-agent"
    }


@app.middleware
async def logging_middleware(request, call_next):
    """日志中间件"""
    import time
    start_time = time.time()
    
    # 这里可以添加请求前的处理逻辑
    print(f"Request started at {datetime.now().isoformat()}")
    
    # 处理请求
    response = await call_next(request)
    
    process_time = time.time() - start_time
    print(f"Request completed in {process_time:.4f}s")
    
    return response


if __name__ == "__main__":
    app.run()