# Agent Runtime 模块测试

本目录包含了重新实现的 PPIO Agent Runtime 模块的完整测试套件。

## 📁 目录结构

```
tests/agent_runtime/
├── README.md                          # 本文件
├── AGENT_RUNTIME_TESTING_PLAN.md      # 详细测试计划
├── conftest.py                        # 共享测试配置和 fixtures
├── pytest.ini                        # Pytest 配置
├── run_tests.py                       # 测试执行脚本
├── setup_test_structure.py            # 测试结构初始化脚本
├── Makefile                           # 快速测试命令
├── runtime/                           # Runtime 模块测试
│   ├── unit/                          # 单元测试
│   │   ├── test_models.py             # 数据模型测试
│   │   ├── test_context.py            # 上下文管理测试
│   │   ├── test_server.py             # HTTP 服务器测试
│   │   ├── test_app.py                # AgentRuntimeApp 测试
│   │   └── test_decorators.py         # 装饰器功能测试
│   ├── integration/                   # 集成测试
│   │   ├── test_end_to_end.py         # 端到端测试
│   │   ├── test_server_app.py         # 服务器应用集成测试
│   │   ├── test_streaming.py          # 流式响应测试
│   │   ├── test_middleware.py         # 中间件测试
│   │   └── test_error_handling.py     # 错误处理测试
│   ├── performance/                   # 性能测试
│   │   ├── test_load.py               # 负载测试
│   │   ├── test_concurrent.py         # 并发测试
│   │   ├── test_memory.py             # 内存测试
│   │   └── test_latency.py            # 延迟测试
│   ├── compatibility/                 # 兼容性测试
│   │   ├── test_api_compatibility.py  # API 兼容性测试
│   │   └── test_legacy_support.py     # 向后兼容性测试
│   └── mocks/                         # Mock 和测试工具
│       ├── mock_agent.py              # Mock Agent 函数
│       ├── mock_server.py             # Mock 服务器
│       └── test_fixtures.py           # 测试数据
├── examples/                          # 示例测试
│   ├── test_basic_agent.py            # 基础 Agent 示例测试
│   └── test_streaming_agent.py        # 流式 Agent 示例测试
└── AGENT_RUNTIME_CLIENT_TESTING_PLAN.md  # 现有的 Client 测试计划
```

## 🚀 快速开始

### 1. 初始化测试结构

```bash
# 创建测试目录结构和占位符文件
python setup_test_structure.py
```

### 2. 安装测试依赖

```bash
# 使用 Makefile
make install-deps

# 或者手动安装
pip install pytest pytest-asyncio pytest-mock pytest-cov
pip install pytest-xdist pytest-benchmark pytest-html
pip install aioresponses httpx responses
```

### 3. 运行测试

```bash
# 使用 Makefile（推荐）
make test-unit          # 单元测试
make test-integration   # 集成测试
make test-all           # 所有测试
make test-coverage      # 带覆盖率的测试

# 使用测试脚本
python run_tests.py --unit --verbose
python run_tests.py --all --coverage
python run_tests.py --report

# 使用 pytest 直接运行
pytest runtime/unit/ -m unit -v
pytest runtime/integration/ -m integration -v
```

## 🧪 测试类型

### 单元测试 (Unit Tests)
- **目标**: 测试单个组件的功能
- **特点**: 快速执行，无外部依赖，使用 Mock
- **覆盖**: 数据模型、上下文管理、装饰器等

```bash
# 运行单元测试
make test-unit
python run_tests.py --unit --verbose
```

### 集成测试 (Integration Tests)
- **目标**: 测试组件间的交互
- **特点**: 需要启动真实服务器，测试完整流程
- **覆盖**: 端到端流程、服务器应用集成、流式响应等

```bash
# 运行集成测试
make test-integration
python run_tests.py --integration --verbose
```

### 性能测试 (Performance Tests)
- **目标**: 测试系统性能和资源使用
- **特点**: 耗时较长，需要充足计算资源
- **覆盖**: 负载测试、并发测试、内存使用、延迟分析

```bash
# 运行性能测试
make test-performance
python run_tests.py --performance --verbose
```

### 兼容性测试 (Compatibility Tests)
- **目标**: 确保向后兼容和 API 符合性
- **特点**: 验证不同版本间的兼容性
- **覆盖**: API 兼容性、向后兼容性支持

```bash
# 运行兼容性测试
make test-compatibility
python run_tests.py --compatibility --verbose
```

## 📊 测试报告

### 生成覆盖率报告

```bash
# 生成 HTML 覆盖率报告
make test-coverage

# 查看报告
open htmlcov/index.html
```

### 生成完整测试报告

```bash
# 生成包含 HTML 和 XML 格式的完整报告
make test-report
python run_tests.py --report

# 报告位置
reports/agent_runtime_report.html     # HTML 测试报告
reports/coverage_html/index.html      # 覆盖率报告
reports/agent_runtime_junit.xml       # JUnit XML 报告
reports/coverage.xml                  # 覆盖率 XML 报告
```

## 🎯 测试标记 (Markers)

测试使用标记来分类和过滤：

```python
@pytest.mark.unit           # 单元测试
@pytest.mark.integration    # 集成测试
@pytest.mark.performance    # 性能测试
@pytest.mark.compatibility  # 兼容性测试
@pytest.mark.network        # 需要网络的测试
@pytest.mark.slow           # 慢速测试
```

### 按标记运行测试

```bash
# 只运行单元测试
pytest -m unit

# 排除性能测试
pytest -m "not performance"

# 运行单元测试和集成测试
pytest -m "unit or integration"
```

## 🔧 高级用法

### 并行测试

```bash
# 使用 4 个进程并行运行测试
make test-parallel
python run_tests.py --parallel --workers 4
```

### 运行特定测试文件

```bash
# 运行特定文件
python run_tests.py --file runtime/unit/test_models.py

# 运行特定测试方法
pytest runtime/unit/test_models.py::TestAgentConfig::test_valid_config -v
```

### 调试测试

```bash
# 详细输出
pytest -v -s

# 显示局部变量
pytest --tb=long

# 在第一个失败处停止
pytest -x

# 进入调试器
pytest --pdb
```

## 📋 测试编写指南

### 1. 测试文件命名

- 单元测试: `test_<module_name>.py`
- 类名: `Test<ClassName>`
- 方法名: `test_<functionality>`

### 2. 使用 Fixtures

```python
def test_agent_app_creation(runtime_config, mock_agent_function):
    """测试 Agent 应用创建"""
    app = AgentRuntimeApp(config=runtime_config)
    app.entrypoint(mock_agent_function)
    assert app._entrypoint_func is not None
```

### 3. 异步测试

```python
@pytest.mark.asyncio
async def test_async_agent_execution():
    """测试异步 Agent 执行"""
    # 测试异步函数
    pass
```

### 4. 参数化测试

```python
@pytest.mark.parametrize("input_data,expected", [
    ({"prompt": "test"}, {"response": "processed"}),
    ({"prompt": ""}, {"response": "empty"}),
])
def test_agent_responses(input_data, expected):
    """参数化测试 Agent 响应"""
    # 测试不同输入的响应
    pass
```

## 🛠️ 开发工作流

### 1. 添加新功能测试

1. 在对应的测试目录中创建测试文件
2. 编写测试用例
3. 运行测试确保通过
4. 检查覆盖率报告

### 2. 修复失败的测试

1. 运行特定的失败测试
2. 使用调试模式分析问题
3. 修复代码或测试
4. 重新运行测试套件

### 3. 性能回归检测

1. 运行性能测试基准
2. 比较性能指标
3. 分析性能变化原因
4. 优化代码或调整测试

## 📈 质量指标

### 覆盖率目标
- **单元测试覆盖率**: ≥ 95%
- **集成测试覆盖率**: ≥ 85%
- **分支覆盖率**: ≥ 90%
- **关键路径覆盖率**: 100%

### 性能基准
- **响应时间**: < 50ms (P99)
- **并发处理**: 1000+ RPS
- **内存使用**: < 100MB
- **错误率**: < 0.1%

## 🚨 常见问题

### Q: 测试执行很慢怎么办？
A: 使用并行测试 `make test-parallel` 或排除性能测试 `pytest -m "not performance"`

### Q: 如何调试失败的测试？
A: 使用 `pytest --pdb -s` 进入调试器，或使用 `pytest -v --tb=long` 查看详细错误信息

### Q: 如何添加新的测试依赖？
A: 在 `conftest.py` 中添加新的 fixture，或在 `requirements-test.txt` 中添加依赖包

### Q: 测试覆盖率不够怎么办？
A: 运行 `make test-coverage` 查看覆盖率报告，然后为未覆盖的代码添加测试

## 📞 联系和支持

- 详细测试计划: [AGENT_RUNTIME_TESTING_PLAN.md](./AGENT_RUNTIME_TESTING_PLAN.md)
- 报告问题: 请在项目 Issue 中提交测试相关问题
- 贡献代码: 请确保新代码有相应的测试覆盖

---

这个测试套件确保了 Agent Runtime 模块的质量和可靠性。遵循最佳实践，编写清晰、可维护的测试代码。
