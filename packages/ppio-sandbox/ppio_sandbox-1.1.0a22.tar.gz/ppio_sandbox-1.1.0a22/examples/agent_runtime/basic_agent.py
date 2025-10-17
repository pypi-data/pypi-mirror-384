"""
基础 Agent Runtime 使用示例

这个示例展示了如何使用重新实现的 PPIO Agent Runtime 模块。
"""

from ppio_sandbox.agent_runtime import AgentRuntimeApp, RequestContext

# 创建应用实例
app = AgentRuntimeApp(debug=True)


@app.entrypoint
def my_agent(request: dict, context: RequestContext) -> dict:
    """基础 Agent 实现"""
    query = request.get("query", "")
    sandbox_id = context.sandbox_id
    
    # Agent 处理逻辑
    result = f"处理查询: {query}, Sandbox: {sandbox_id}"
    
    return {
        "response": result,
        "sandbox_id": context.sandbox_id,
        "metadata": {"request_id": context.request_id}
    }


@app.ping
def health_check() -> dict:
    """自定义健康检查"""
    return {"status": "healthy", "service": "basic-agent"}


if __name__ == "__main__":
    app.run(port=8080)
