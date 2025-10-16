# Agent Runtime 示例

这个目录包含了 PPIO Agent Runtime 模块的使用示例。

## 重新实现的功能

根据设计文档，Agent Runtime 模块已经重新实现，主要改进包括：

### 1. 架构改进
- **基于 Starlette**: 使用高性能异步 Web 框架替代原来的 HTTPServer
- **Pydantic 数据模型**: 使用现代数据验证和序列化库
- **Kubernetes 风格配置**: 支持完整的 Agent 配置结构
- **改进的上下文管理**: 线程安全的请求上下文管理

### 2. API 改进
- **正确的类名**: `AgentRuntimeApp` (而非 `PPIOAgentRuntimeApp`)
- **标准端点**: `/invocations` 和 `/ping`
- **流式响应**: 支持同步和异步生成器
- **中间件支持**: 完整的请求/响应中间件系统

### 3. 数据模型
- **AgentConfig**: Kubernetes 风格的 Agent 配置
- **RuntimeConfig**: 服务器运行时配置
- **RequestContext**: 改进的请求上下文模型
- **响应模型**: 标准化的请求/响应结构

## 示例文件

### basic_agent.py
展示基础的 Agent 实现：
- 简单的请求处理
- 自定义健康检查
- 上下文访问

```bash
python basic_agent.py
```

### streaming_agent.py
展示高级的流式 Agent 实现：
- 异步流式响应
- 中间件使用
- 自定义配置

```bash
python streaming_agent.py
```

## 测试端点

启动 Agent 后，可以通过以下端点进行测试：

### 健康检查
```bash
curl http://localhost:8080/ping
```

### Agent 调用
```bash
curl -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d '{"query": "Hello, World!"}'
```

### 流式调用
```bash
curl -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d '{"query": "Stream test", "stream": true, "max_tokens": 50}'
```

## 与设计文档的对应

这个实现完全符合设计文档中的要求：

1. **AgentRuntimeApp 类**: 面向 Agent 开发者的核心应用类 ✅
2. **装饰器 API**: 支持 `@app.entrypoint`, `@app.ping`, `@app.middleware` ✅
3. **同步/异步支持**: 自动检测并支持同步和异步函数 ✅
4. **流式响应**: 支持 Generator 和 AsyncGenerator ✅
5. **上下文管理**: 线程安全的请求上下文管理 ✅
6. **配置系统**: 完整的配置体系 ✅
7. **性能优化**: 基于 Starlette 的高性能实现 ✅

## 依赖更新

为了支持新的功能，已在 `pyproject.toml` 中添加了必要的依赖：
- `pydantic>=2.0.0,<3.0.0`: 数据验证和序列化
- `starlette>=0.46.2`: 高性能 Web 框架
- `uvicorn>=0.34.2`: ASGI 服务器
