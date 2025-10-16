# Agent Runtime Client 模块测试方案

## 🎯 测试目标

- 确保每个组件的功能正确性
- 验证模块间的集成和交互
- 测试异常处理和边界情况
- 验证异步操作的正确性
- 确保 API 兼容性和稳定性

## 📁 测试目录结构

```
tests/
├── agent_runtime/
│   ├── __init__.py
│   ├── conftest.py                    # 共享测试配置和 fixtures
│   ├── client/
│   │   ├── __init__.py
│   │   ├── unit/                      # 单元测试
│   │   │   ├── test_auth.py          # AuthManager 单元测试
│   │   │   ├── test_template.py      # TemplateManager 单元测试  
│   │   │   ├── test_session.py       # SandboxSession 单元测试
│   │   │   ├── test_client.py        # AgentRuntimeClient 单元测试
│   │   │   ├── test_models.py        # 数据模型测试
│   │   │   └── test_exceptions.py    # 异常类测试
│   │   ├── integration/               # 集成测试
│   │   │   ├── test_end_to_end.py    # 端到端测试
│   │   │   ├── test_session_lifecycle.py  # 会话生命周期测试
│   │   │   ├── test_streaming.py     # 流式响应测试
│   │   │   └── test_concurrent.py    # 并发测试
│   │   └── mocks/                     # Mock 和测试工具
│   │       ├── __init__.py
│   │       ├── mock_sandbox.py       # 模拟 Sandbox
│   │       ├── mock_api.py           # 模拟 API 响应
│   │       └── test_fixtures.py      # 测试数据
│   └── examples/                      # 示例和演示测试
│       └── test_client_example.py    # 验证示例代码
```

## 🧪 单元测试方案

### 1. AuthManager 测试 (`test_auth.py`)

**测试范围：**
- API Key 验证逻辑
- 环境变量读取
- 认证头生成
- 无效凭据处理

**测试用例：**
- ✅ 正确的 API Key 初始化
- ✅ 从环境变量读取 API Key
- ✅ API Key 格式验证
- ✅ 无效 API Key 抛出异常
- ✅ 认证头格式正确性
- ✅ API Key 更新功能
- ❌ 缺失 API Key 的错误处理
- ❌ 格式错误的 API Key

### 2. TemplateManager 测试 (`test_template.py`)

**测试范围：**
- 模板列表查询
- 模板详情获取
- 过滤和搜索功能
- API 错误处理

**测试用例：**
- ✅ 列出所有模板
- ✅ 获取特定模板详情
- ✅ 检查模板存在性
- ✅ HTTP 客户端正确关闭
- ❌ 网络错误处理
- ❌ 模板不存在错误
- ❌ 认证失败处理
- ❌ 无效响应格式处理

### 3. SandboxSession 测试 (`test_session.py`)

**测试范围：**
- 会话创建和初始化
- Agent 调用（同步/异步）
- 会话状态管理
- 生命周期操作

**测试用例：**
- ✅ 会话正确初始化
- ✅ 同步 Agent 调用
- ✅ 异步 Agent 调用
- ✅ 流式响应处理
- ✅ 会话暂停和恢复
- ✅ 健康检查 (ping)
- ✅ 会话状态跟踪
- ✅ 会话正确关闭
- ✅ 指定 Sandbox/会话 ID 调用
- ✅ 属性访问 (session_id 等)
- ❌ 无效请求格式
- ❌ 网络超时处理
- ❌ 会话关闭后调用
- ❌ Agent 调用失败

### 4. AgentRuntimeClient 测试 (`test_client.py`)

**测试范围：**
- 客户端初始化
- 会话管理功能
- 便捷调用方法
- 上下文管理器

**测试用例：**
- ✅ 客户端正确初始化
- ✅ 创建新会话
- ✅ 获取现有会话
- ✅ 列出所有会话
- ✅ 关闭特定会话
- ✅ 关闭所有会话
- ✅ 便捷 Agent 调用
- ✅ 流式 Agent 调用
- ✅ 模板管理代理
- ✅ 上下文管理器支持
- ❌ 无效配置处理
- ❌ 会话创建失败
- ❌ 会话不存在错误
- ❌ 客户端关闭后操作

### 5. 数据模型测试 (`test_models.py`)

**测试范围：**
- Pydantic 模型验证
- 数据序列化/反序列化
- 默认值和可选字段
- 模型关系和继承

**测试用例：**
- ✅ InvocationRequest 模型验证
- ✅ InvocationResponse 模型验证
- ✅ AgentTemplate 模型验证
- ✅ SessionStatus 枚举
- ✅ 向后兼容属性 (session_id)
- ✅ 模型序列化/反序列化
- ❌ 无效字段值验证
- ❌ 必填字段缺失

### 6. 异常类测试 (`test_exceptions.py`)

**测试范围：**
- 异常继承关系
- 异常信息和错误码
- 异常捕获和处理

**测试用例：**
- ✅ 异常类继承关系正确
- ✅ 异常信息设置和获取
- ✅ 错误码设置和获取
- ✅ 异常类型区分

## 🔗 集成测试方案

### 1. 端到端测试 (`test_end_to_end.py`)

**测试场景：**
- 完整的 Agent 调用流程
- 从模板查询到结果获取
- 多种调用方式验证

**测试流程：**
1. 初始化客户端
2. 查询可用模板
3. 创建会话
4. 调用 Agent
5. 处理响应
6. 清理资源

### 2. 会话生命周期测试 (`test_session_lifecycle.py`)

**测试场景：**
- 会话的完整生命周期
- 状态转换的正确性
- 资源管理

**测试流程：**
1. 创建会话 → ACTIVE
2. 执行调用 → 保持 ACTIVE
3. 暂停会话 → PAUSED
4. 恢复会话 → ACTIVE
5. 关闭会话 → CLOSED

### 3. 流式响应测试 (`test_streaming.py`)

**测试场景：**
- 流式 Agent 调用
- 数据流完整性
- 异常中断处理

## 🎭 Mock 和测试工具

### 1. Mock Sandbox (`mock_sandbox.py`)

模拟 Sandbox 实例的行为：
- 模拟启动、暂停、恢复操作
- 提供可控的响应数据
- 模拟各种错误情况

### 2. Mock API (`mock_api.py`)

模拟 HTTP API 响应：
- 模板查询 API
- Agent 调用 API
- 各种错误状态码

### 3. 测试数据 (`test_fixtures.py`)

提供测试用的固定数据：
- 示例模板数据
- 示例请求/响应
- 错误场景数据

## 📋 测试配置和工具

### 1. 共享配置 (`conftest.py`)

```python
# Fixtures 定义
@pytest.fixture
async def mock_client():
    """提供 Mock 的 AgentRuntimeClient"""

@pytest.fixture
async def real_client():
    """提供真实的客户端（需要环境变量）"""

@pytest.fixture
def sample_template():
    """提供示例模板数据"""

@pytest.fixture
def sample_request():
    """提供示例请求数据"""
```

### 2. 测试标记 (Markers)

```python
# 单元测试
@pytest.mark.unit

# 集成测试
@pytest.mark.integration

# 需要网络的测试
@pytest.mark.network

```

## 🔧 测试执行策略

### 1. 测试分层执行

```bash
# 仅单元测试（快速）
pytest tests/agent_runtime/client/unit/ -m unit

# 集成测试（需要环境）
pytest tests/agent_runtime/client/integration/ -m integration

# 完整测试套件
pytest tests/agent_runtime/client/
```

### 2. 环境要求

- **单元测试**：无外部依赖，纯 Mock
- **集成测试**：需要 `PPIO_API_KEY` 环境变量

### 3. CI/CD 集成

- **Pull Request**：运行单元测试 + 部分集成测试
- **主分支**：运行完整测试套件
- **发布前**：运行全部测试

## 📊 测试覆盖率目标

- **单元测试覆盖率**：≥ 90%
- **集成测试覆盖率**：≥ 80%
- **分支覆盖率**：≥ 85%
- **关键路径覆盖率**：100%

## 🛠️ 所需依赖

```toml
[tool.poetry.group.test.dependencies]
pytest = "^7.0.0"
pytest-asyncio = "^0.23.0"
pytest-mock = "^3.12.0"
pytest-cov = "^4.1.0"
aioresponses = "^0.7.4"
httpx = "^0.27.0"
pytest-xdist = "^3.3.0"  # 并行测试
```

## 📈 测试执行计划

### 阶段 1：核心单元测试
1. `test_auth.py` - AuthManager 基础功能
2. `test_models.py` - 数据模型验证
3. `test_exceptions.py` - 异常处理

### 阶段 2：组件单元测试
1. `test_template.py` - TemplateManager 功能
2. `test_session.py` - SandboxSession 功能
3. `test_client.py` - AgentRuntimeClient 功能

### 阶段 3：集成测试
1. `test_end_to_end.py` - 端到端流程
2. `test_session_lifecycle.py` - 会话生命周期
3. `test_streaming.py` - 流式响应
4. `test_concurrent.py` - 并发测试

## 🎯 质量保证

### 代码覆盖率要求
- 每个测试文件必须有对应的覆盖率报告
- 关键业务逻辑必须达到 100% 覆盖率
- 异常处理路径必须全部测试

### 测试数据管理
- 使用固定的测试数据集
- Mock 数据与真实 API 响应保持一致
- 敏感数据使用环境变量或加密存储

### 测试隔离
- 每个测试用例相互独立
- 不依赖外部状态或其他测试结果
- 适当的 setup 和 teardown

## 📝 测试报告

### 自动化报告
- 测试结果统计
- 覆盖率报告
- 失败用例详情

### 手动验证
- 关键功能手动验证
- 用户体验测试
- 文档示例验证

---

这个测试方案确保了 Agent Runtime Client 模块的质量和可靠性，覆盖了从单元测试到集成测试的完整测试体系。
