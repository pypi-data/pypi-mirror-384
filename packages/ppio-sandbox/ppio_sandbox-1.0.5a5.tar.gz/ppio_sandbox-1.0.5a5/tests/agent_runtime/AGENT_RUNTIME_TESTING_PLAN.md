# Agent Runtime 模块测试方案

## 🎯 测试目标

- 确保重新实现的 Runtime 模块功能正确性
- 验证基于 Starlette 的服务器性能和稳定性
- 测试 Pydantic 数据模型的验证和序列化
- 验证异步操作和流式响应的正确性
- 确保与设计文档的完全符合性
- 测试装饰器 API 的易用性和正确性

## 📁 测试目录结构

```
tests/
├── agent_runtime/
│   ├── __init__.py
│   ├── conftest.py                    # 共享测试配置和 fixtures
│   ├── runtime/                       # Runtime 模块测试
│   │   ├── __init__.py
│   │   ├── unit/                      # 单元测试
│   │   │   ├── test_models.py         # 数据模型测试
│   │   │   ├── test_context.py        # 上下文管理测试
│   │   │   ├── test_server.py         # HTTP 服务器测试
│   │   │   ├── test_app.py            # AgentRuntimeApp 测试
│   │   │   └── test_decorators.py     # 装饰器功能测试
│   │   ├── integration/               # 集成测试
│   │   │   ├── test_end_to_end.py     # 端到端 Agent 运行测试
│   │   │   ├── test_server_app.py     # 服务器与应用集成测试
│   │   │   ├── test_streaming.py      # 流式响应集成测试
│   │   │   ├── test_middleware.py     # 中间件集成测试
│   │   │   └── test_error_handling.py # 错误处理集成测试
│   │   ├── performance/               # 性能测试
│   │   │   ├── test_load.py           # 负载测试
│   │   │   ├── test_concurrent.py     # 并发测试
│   │   │   ├── test_memory.py         # 内存使用测试
│   │   │   └── test_latency.py        # 延迟测试
│   │   ├── compatibility/             # 兼容性测试
│   │   │   ├── test_api_compatibility.py  # API 兼容性测试
│   │   │   └── test_legacy_support.py     # 向后兼容性测试
│   │   └── mocks/                     # Mock 和测试工具
│   │       ├── __init__.py
│   │       ├── mock_agent.py          # 模拟 Agent 函数
│   │       ├── mock_server.py         # 模拟服务器
│   │       └── test_fixtures.py       # 测试数据和 fixtures
│   ├── examples/                      # 示例测试
│   │   ├── test_basic_agent.py        # 基础 Agent 示例测试
│   │   └── test_streaming_agent.py    # 流式 Agent 示例测试
│   └── AGENT_RUNTIME_CLIENT_TESTING_PLAN.md  # 现有的 Client 测试计划
```

## 🧪 单元测试方案

### 1. 数据模型测试 (`test_models.py`)

**测试范围：**
- Pydantic 模型验证和序列化
- Kubernetes 风格的 AgentConfig
- 枚举类型和常量
- 向后兼容性属性

**测试用例：**

#### AgentConfig 相关
- ✅ AgentConfig 完整配置验证
- ✅ AgentMetadata 必填字段验证
- ✅ RuntimeSpec 资源限制验证
- ✅ SandboxSpec 模板ID验证
- ✅ AgentStatus 阶段枚举
- ✅ 配置序列化/反序列化
- ❌ 无效邮箱格式拒绝
- ❌ 无效文件扩展名拒绝
- ❌ 超出范围的资源限制拒绝

#### RuntimeConfig 相关
- ✅ 默认配置值正确性
- ✅ 端口范围验证
- ✅ CORS 配置正确性
- ❌ 无效端口号拒绝
- ❌ 无效主机地址拒绝

#### 请求/响应模型
- ✅ InvocationRequest 创建和验证
- ✅ InvocationResponse 结构正确性
- ✅ PingResponse 状态枚举
- ✅ 向后兼容属性 (session_id)
- ❌ 无效请求数据拒绝

### 2. 上下文管理测试 (`test_context.py`)

**测试范围：**
- RequestContext 模型功能
- AgentRuntimeContext 上下文管理
- 线程安全性
- 向后兼容性

**测试用例：**
- ✅ RequestContext 创建和属性访问
- ✅ 向后兼容的 session_id 属性
- ✅ AgentRuntimeContext 设置/获取
- ✅ 上下文清除功能
- ✅ 多线程环境下的上下文隔离
- ✅ ContextVar 正确使用
- ❌ 无效上下文数据处理

### 3. HTTP 服务器测试 (`test_server.py`)

**测试范围：**
- AgentRuntimeServer 初始化
- Starlette 应用配置
- 路由处理
- 中间件支持

**测试用例：**

#### 服务器初始化
- ✅ 服务器正确初始化
- ✅ 配置参数应用
- ✅ Starlette 应用创建
- ✅ CORS 中间件配置
- ✅ 路由注册正确性

#### 端点处理
- ✅ 根端点 (/) 响应
- ✅ 健康检查端点 (/ping)
- ✅ 调用端点 (/invocations)
- ✅ OPTIONS 请求处理
- ❌ 不存在端点返回 404

#### 请求处理
- ✅ JSON 请求解析
- ✅ 请求大小限制
- ✅ 请求头处理
- ✅ 上下文创建和设置
- ❌ 无效 JSON 格式拒绝
- ❌ 超大请求拒绝

#### Agent 函数执行
- ✅ 同步函数执行
- ✅ 异步函数执行
- ✅ 函数签名自动检测
- ✅ 参数传递正确性
- ❌ 函数执行异常处理

#### 流式响应
- ✅ 同步生成器处理
- ✅ 异步生成器处理
- ✅ 普通迭代器处理
- ✅ 流式数据格式
- ❌ 流式响应异常处理

### 4. AgentRuntimeApp 测试 (`test_app.py`)

**测试范围：**
- 应用初始化和配置
- 装饰器功能
- 服务器启动和停止
- 属性访问

**测试用例：**

#### 应用初始化
- ✅ 默认配置初始化
- ✅ 自定义配置初始化
- ✅ 调试模式启用
- ✅ 配置参数覆盖

#### 装饰器功能
- ✅ @entrypoint 装饰器注册
- ✅ @ping 装饰器注册
- ✅ @middleware 装饰器注册
- ✅ 多个装饰器共存
- ❌ 重复注册处理

#### 运行控制
- ✅ 服务器启动流程
- ✅ 端口和主机配置
- ✅ 入口点函数验证
- ❌ 未注册入口点报错

#### 上下文访问
- ✅ context 属性访问
- ✅ 上下文状态正确性

### 5. 装饰器功能测试 (`test_decorators.py`)

**测试范围：**
- 装饰器语法糖
- 函数类型检测
- 参数传递
- 返回值处理

**测试用例：**

#### entrypoint 装饰器
- ✅ 同步函数装饰
- ✅ 异步函数装饰
- ✅ 单参数函数 (request only)
- ✅ 双参数函数 (request + context)
- ✅ 生成器函数装饰
- ✅ 异步生成器函数装饰
- ✅ 返回值保持不变

#### ping 装饰器
- ✅ 同步健康检查函数
- ✅ 异步健康检查函数
- ✅ 返回字典格式
- ✅ 返回 PingResponse 对象
- ✅ 自定义健康检查逻辑

#### middleware 装饰器
- ✅ 中间件函数注册
- ✅ 执行顺序正确性
- ✅ 请求/响应处理
- ✅ 异常传播

## 🔗 集成测试方案

### 1. 端到端测试 (`test_end_to_end.py`)

**测试场景：**
- 完整的 Agent 应用运行流程
- 真实 HTTP 请求/响应
- 多种调用方式验证

**测试流程：**
1. 创建 AgentRuntimeApp
2. 注册 Agent 函数
3. 启动服务器
4. 发送 HTTP 请求
5. 验证响应格式
6. 关闭服务器

**测试用例：**
- ✅ 基础 Agent 调用完整流程
- ✅ 带参数的 Agent 调用
- ✅ 自定义健康检查流程
- ✅ 异步 Agent 调用流程
- ✅ 错误响应格式验证

### 2. 服务器应用集成测试 (`test_server_app.py`)

**测试场景：**
- AgentRuntimeApp 与 AgentRuntimeServer 集成
- 配置传递和应用
- 生命周期管理

**测试用例：**
- ✅ 应用配置正确传递到服务器
- ✅ 装饰器注册的函数正确调用
- ✅ 中间件链正确执行
- ✅ 服务器启动状态同步

### 3. 流式响应集成测试 (`test_streaming.py`)

**测试场景：**
- 端到端流式响应
- 不同类型生成器的处理
- 流式数据完整性

**测试用例：**
- ✅ 同步生成器端到端流式响应
- ✅ 异步生成器端到端流式响应
- ✅ 大量数据流式传输
- ✅ 流式响应中断处理
- ✅ 客户端流式数据接收

### 4. 中间件集成测试 (`test_middleware.py`)

**测试场景：**
- 多个中间件的协同工作
- 中间件执行顺序
- 异常在中间件链中的传播

**测试用例：**
- ✅ 多个中间件按顺序执行
- ✅ 中间件修改请求/响应
- ✅ 中间件异常处理
- ✅ 中间件与 Agent 函数交互

### 5. 错误处理集成测试 (`test_error_handling.py`)

**测试场景：**
- 各层级的错误处理
- 错误响应格式标准化
- 异常传播和转换

**测试用例：**
- ✅ Agent 函数异常处理
- ✅ 服务器层异常处理
- ✅ 中间件异常处理
- ✅ 网络层异常处理
- ✅ 标准化错误响应格式

## 🚀 性能测试方案

### 1. 负载测试 (`test_load.py`)

**测试场景：**
- 高并发请求处理
- 长时间运行稳定性
- 资源使用监控

**测试指标：**
- 每秒请求数 (RPS)
- 平均响应时间
- 99% 响应时间
- 错误率

**测试用例：**
- ✅ 100 并发用户负载测试
- ✅ 1000 并发用户负载测试
- ✅ 长时间运行稳定性测试
- ✅ 逐步增加负载测试

### 2. 并发测试 (`test_concurrent.py`)

**测试场景：**
- 并发请求处理正确性
- 上下文隔离验证
- 线程安全性

**测试用例：**
- ✅ 多线程并发调用
- ✅ 上下文数据隔离
- ✅ 共享资源访问安全
- ✅ 竞态条件检测

### 3. 内存使用测试 (`test_memory.py`)

**测试场景：**
- 内存泄漏检测
- 资源清理验证
- 大数据处理内存管理

**测试用例：**
- ✅ 长时间运行内存稳定性
- ✅ 大请求处理内存使用
- ✅ 流式响应内存管理
- ✅ 垃圾回收有效性

### 4. 延迟测试 (`test_latency.py`)

**测试场景：**
- 请求处理延迟分析
- 不同负载下的延迟变化
- 延迟分布统计

**测试用例：**
- ✅ 低负载延迟基准
- ✅ 高负载延迟变化
- ✅ 延迟分布分析
- ✅ 尾延迟监控

## 🔄 兼容性测试方案

### 1. API 兼容性测试 (`test_api_compatibility.py`)

**测试场景：**
- 与设计文档 API 的符合性
- 不同 Python 版本兼容性
- 依赖库版本兼容性

**测试用例：**
- ✅ 设计文档 API 完全符合
- ✅ Python 3.9+ 兼容性
- ✅ Pydantic 2.x 兼容性
- ✅ Starlette 最新版本兼容性

### 2. 向后兼容性测试 (`test_legacy_support.py`)

**测试场景：**
- 旧版本 API 的支持
- 迁移路径验证
- 废弃警告

**测试用例：**
- ✅ session_id 属性向后兼容
- ✅ 旧配置格式支持
- ✅ 迁移警告正确显示

## 🎭 Mock 和测试工具

### 1. Mock Agent (`mock_agent.py`)

提供各种类型的 Mock Agent 函数：
- 同步/异步 Agent 函数
- 流式响应 Agent 函数
- 异常抛出 Agent 函数
- 不同参数签名的函数

### 2. Mock Server (`mock_server.py`)

模拟外部依赖：
- HTTP 客户端模拟
- 网络错误模拟
- 超时模拟

### 3. 测试数据 (`test_fixtures.py`)

提供标准化测试数据：
- 示例配置数据
- 示例请求/响应数据
- 错误场景数据
- 性能测试数据

## 📋 测试配置和工具

### 1. 共享配置 (`conftest.py`)

```python
# 主要 Fixtures
@pytest.fixture
def runtime_config():
    """提供测试用的运行时配置"""

@pytest.fixture
def agent_config():
    """提供测试用的 Agent 配置"""

@pytest.fixture
async def mock_app():
    """提供 Mock 的 AgentRuntimeApp"""

@pytest.fixture
async def test_server():
    """提供测试服务器实例"""

@pytest.fixture
def sample_agent_function():
    """提供示例 Agent 函数"""

@pytest.fixture
def mock_request_context():
    """提供 Mock 的请求上下文"""
```

### 2. 测试标记 (Markers)

```python
# 单元测试
@pytest.mark.unit

# 集成测试
@pytest.mark.integration

# 性能测试
@pytest.mark.performance

# 需要网络的测试
@pytest.mark.network

# 慢速测试
@pytest.mark.slow

# 兼容性测试
@pytest.mark.compatibility
```

## 🔧 测试执行策略

### 1. 测试分层执行

```bash
# 仅单元测试（快速）
pytest tests/agent_runtime/runtime/unit/ -m unit

# 集成测试
pytest tests/agent_runtime/runtime/integration/ -m integration

# 性能测试（耗时）
pytest tests/agent_runtime/runtime/performance/ -m performance

# 兼容性测试
pytest tests/agent_runtime/runtime/compatibility/ -m compatibility

# 完整测试套件
pytest tests/agent_runtime/runtime/
```

### 2. 环境要求

- **单元测试**：无外部依赖，纯 Mock
- **集成测试**：需要启动真实服务器
- **性能测试**：需要充足计算资源
- **兼容性测试**：需要多 Python 版本环境

### 3. CI/CD 集成

- **Pull Request**：运行单元测试 + 基础集成测试
- **主分支**：运行完整测试套件（除性能测试）
- **发布前**：运行包括性能测试的全部测试

## 📊 测试覆盖率目标

- **单元测试覆盖率**：≥ 95%
- **集成测试覆盖率**：≥ 85%
- **分支覆盖率**：≥ 90%
- **关键路径覆盖率**：100%

## 🛠️ 所需依赖

```toml
[tool.poetry.group.test.dependencies]
# 测试框架
pytest = "^7.0.0"
pytest-asyncio = "^0.23.0"
pytest-mock = "^3.12.0"
pytest-cov = "^4.1.0"
pytest-xdist = "^3.3.0"

# HTTP 测试
httpx = "^0.27.0"
aioresponses = "^0.7.4"
starlette = "^0.46.2"

# 性能测试
pytest-benchmark = "^4.0.0"
locust = "^2.17.0"
memory-profiler = "^0.61.0"

# Mock 和工具
responses = "^0.24.0"
freezegun = "^1.2.0"
```

## 📈 测试执行计划

### 阶段 1：数据模型和基础组件（第1周）
1. `test_models.py` - Pydantic 模型验证
2. `test_context.py` - 上下文管理功能
3. `test_decorators.py` - 装饰器功能

### 阶段 2：服务器和应用组件（第2周）
1. `test_server.py` - HTTP 服务器功能
2. `test_app.py` - 应用类功能
3. Mock 工具开发

### 阶段 3：集成测试（第3周）
1. `test_end_to_end.py` - 端到端流程
2. `test_server_app.py` - 服务器应用集成
3. `test_streaming.py` - 流式响应
4. `test_middleware.py` - 中间件集成
5. `test_error_handling.py` - 错误处理

### 阶段 4：性能和兼容性测试（第4周）
1. `test_load.py` - 负载测试
2. `test_concurrent.py` - 并发测试
3. `test_memory.py` - 内存测试
4. `test_latency.py` - 延迟测试
5. `test_api_compatibility.py` - API 兼容性
6. `test_legacy_support.py` - 向后兼容性

## 🎯 质量保证

### 代码覆盖率要求
- 每个模块必须有对应的单元测试
- 关键业务逻辑必须达到 100% 覆盖率
- 异常处理路径必须全部测试
- 边界条件必须充分测试

### 测试数据管理
- 使用标准化的测试数据集
- Mock 数据与真实场景保持一致
- 测试数据版本控制
- 敏感配置使用环境变量

### 测试隔离
- 每个测试用例相互独立
- 不依赖外部状态或其他测试结果
- 适当的 setup 和 teardown
- 并行测试兼容

## 📝 测试报告

### 自动化报告
- 测试结果统计和趋势
- 代码覆盖率报告和变化
- 性能基准对比和回归检测
- 失败用例详情和根因分析

### 质量指标
- 测试通过率 ≥ 99%
- 代码覆盖率达标情况
- 性能指标达标情况
- 兼容性支持情况

---

这个测试方案确保了重新实现的 Agent Runtime 模块的质量和可靠性，覆盖了从单元测试到性能测试的完整测试体系，并与设计文档保持完全一致。
