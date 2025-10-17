# Agent Runtime Module Tests

This directory contains a complete test suite for the reimplemented PPIO Agent Runtime module.

## 📁 Directory Structure

```
tests/
├── README.md                          # This file
├── AGENT_RUNTIME_TESTING_PLAN.md      # Detailed test plan
├── conftest.py                        # Shared test configuration and fixtures
├── pytest.ini                        # Pytest configuration
├── run_tests.py                       # Test execution script
├── setup_test_structure.py            # Test structure initialization script
├── Makefile                           # Quick test commands
├── runtime/                           # Runtime module tests
│   ├── unit/                          # Unit tests
│   │   ├── test_models.py             # Data model tests
│   │   ├── test_context.py            # Context management tests
│   │   ├── test_server.py             # HTTP server tests
│   │   ├── test_app.py                # AgentRuntimeApp tests
│   │   └── test_decorators.py         # Decorator functionality tests
│   ├── integration/                   # Integration tests
│   │   ├── test_end_to_end.py         # End-to-end tests
│   │   ├── test_server_app.py         # Server application integration tests
│   │   ├── test_streaming.py          # Streaming response tests
│   │   ├── test_middleware.py         # Middleware tests
│   │   └── test_error_handling.py     # Error handling tests
│   ├── performance/                   # Performance tests
│   │   ├── test_load.py               # Load tests
│   │   ├── test_concurrent.py         # Concurrency tests
│   │   ├── test_memory.py             # Memory tests
│   │   └── test_latency.py            # Latency tests
│   ├── compatibility/                 # Compatibility tests
│   │   ├── test_api_compatibility.py  # API compatibility tests
│   │   └── test_legacy_support.py     # Backward compatibility tests
│   └── mocks/                         # Mocks and test utilities
│       ├── mock_agent.py              # Mock Agent functions
│       ├── mock_server.py             # Mock server
│       └── test_fixtures.py           # Test data
├── examples/                          # Example tests
│   ├── test_basic_agent.py            # Basic Agent example tests
│   └── test_streaming_agent.py        # Streaming Agent example tests
└── AGENT_RUNTIME_CLIENT_TESTING_PLAN.md  # Existing Client test plan
```

## 🚀 Quick Start

### 1. Initialize Test Structure

```bash
# Create test directory structure and placeholder files
poetry run python setup_test_structure.py
```

### 2. Install Test Dependencies

```bash
# Using Makefile
make install-deps

# Or manual installation
pip install pytest pytest-asyncio pytest-mock pytest-cov
pip install pytest-xdist pytest-benchmark pytest-html
pip install aioresponses httpx responses
```

### 3. Run Tests

```bash
# Using Makefile (recommended)
make test-unit          # Unit tests
make test-integration   # Integration tests
make test-all           # All tests
make test-coverage      # Tests with coverage

# Using test script
poetry run python run_tests.py --unit --verbose
poetry run python run_tests.py --all --coverage
poetry run python run_tests.py --report

# Run directly with pytest
poetry run pytest runtime/ -m unit -v
poetry run pytest runtime/ -m integration -v
```

## 🧪 Test Types

### Unit Tests
- **Goal**: Test functionality of individual components
- **Features**: Fast execution, no external dependencies, uses Mocks
- **Coverage**: Data models, context management, decorators, etc.

```bash
# Run unit tests
make test-unit
python run_tests.py --unit --verbose
```

### Integration Tests
- **Goal**: Test interactions between components
- **Features**: Requires starting real server, testing complete workflows
- **Coverage**: End-to-end workflows, server application integration, streaming responses, etc.

```bash
# Run integration tests
make test-integration
poetry run python run_tests.py --integration --verbose
```

### Performance Tests
- **Goal**: Test system performance and resource usage
- **Features**: Time-consuming, requires sufficient computing resources
- **Coverage**: Load testing, concurrency testing, memory usage, latency analysis

```bash
# Run performance tests
make test-performance
poetry run python run_tests.py --performance --verbose
```

### Compatibility Tests
- **Goal**: Ensure backward compatibility and API compliance
- **Features**: Verify compatibility between different versions
- **Coverage**: API compatibility, backward compatibility support

```bash
# Run compatibility tests
make test-compatibility
poetry run python run_tests.py --compatibility --verbose
```

## 📊 Test Reports

### Generate Coverage Report

```bash
# Generate HTML coverage report
make test-coverage

# View report
open htmlcov/index.html
```

### Generate Complete Test Report

```bash
# Generate complete report including HTML and XML formats
make test-report
python run_tests.py --report

# Report locations
reports/agent_runtime_report.html     # HTML test report
reports/coverage_html/index.html      # Coverage report
reports/agent_runtime_junit.xml       # JUnit XML report
reports/coverage.xml                  # Coverage XML report
```

## 🎯 Test Markers

Tests use markers for classification and filtering:

```python
@pytest.mark.unit           # Unit tests
@pytest.mark.integration    # Integration tests
@pytest.mark.performance    # Performance tests
@pytest.mark.compatibility  # Compatibility tests
@pytest.mark.network        # Tests requiring network
@pytest.mark.slow           # Slow tests
```

### Run Tests by Marker

```bash
# Run only unit tests
poetry run pytest -m unit

# Exclude performance tests
poetry run pytest -m "not performance"

# Run unit and integration tests
poetry run pytest -m "unit or integration"
```

## 🔧 Advanced Usage

### Parallel Testing

```bash
# Run tests in parallel using 4 processes
make test-parallel
poetry run python run_tests.py --parallel --workers 4
```

### Run Specific Test File

```bash
# Run specific file
poetry run python run_tests.py --file runtime/test_models.py

# Run specific test method
poetry run pytest runtime/test_models.py::TestAgentConfig::test_valid_config -v
```

### Debugging Tests

```bash
# Verbose output
poetry run pytest -v -s

# Show local variables
poetry run pytest --tb=long

# Stop at first failure
poetry run pytest -x

# Enter debugger
poetry run pytest --pdb
```

## 📋 Test Writing Guide

### 1. Test File Naming

- Unit tests: `test_<module_name>.py`
- Class name: `Test<ClassName>`
- Method name: `test_<functionality>`

### 2. Using Fixtures

```python
def test_agent_app_creation(runtime_config, mock_agent_function):
    """Test Agent application creation"""
    app = AgentRuntimeApp(config=runtime_config)
    app.entrypoint(mock_agent_function)
    assert app._entrypoint_func is not None
```

### 3. Asynchronous Tests

```python
@pytest.mark.asyncio
async def test_async_agent_execution():
    """Test asynchronous Agent execution"""
    # Test async function
    pass
```

### 4. Parameterized Tests

```python
@pytest.mark.parametrize("input_data,expected", [
    ({"prompt": "test"}, {"response": "processed"}),
    ({"prompt": ""}, {"response": "empty"}),
])
def test_agent_responses(input_data, expected):
    """Parameterized test for Agent responses"""
    # Test responses for different inputs
    pass
```

## 🛠️ Development Workflow

### 1. Add Tests for New Features

1. Create test file in corresponding test directory
2. Write test cases
3. Run tests to ensure they pass
4. Check coverage report

### 2. Fix Failing Tests

1. Run specific failing test
2. Use debug mode to analyze issue
3. Fix code or test
4. Rerun test suite

### 3. Performance Regression Detection

1. Run performance test benchmarks
2. Compare performance metrics
3. Analyze reasons for performance changes
4. Optimize code or adjust tests

## 📈 Quality Metrics

### Coverage Goals
- **Unit Test Coverage**: ≥ 95%
- **Integration Test Coverage**: ≥ 85%
- **Branch Coverage**: ≥ 90%
- **Critical Path Coverage**: 100%

### Performance Benchmarks
- **Response Time**: < 50ms (P99)
- **Concurrent Processing**: 1000+ RPS
- **Memory Usage**: < 100MB
- **Error Rate**: < 0.1%

## 🚨 FAQ

### Q: What if tests run slowly?
A: Use parallel testing `make test-parallel` or exclude performance tests `poetry run pytest -m "not performance"`

### Q: How to debug failing tests?
A: Use `poetry run pytest --pdb -s` to enter debugger, or use `poetry run pytest -v --tb=long` to view detailed error information

### Q: How to add new test dependencies?
A: Add new fixtures in `conftest.py`, or add dependency packages in `requirements-test.txt`

### Q: What if test coverage is insufficient?
A: Run `make test-coverage` to view coverage report, then add tests for uncovered code

## 📞 Contact and Support

- Detailed test plan: [AGENT_RUNTIME_TESTING_PLAN.md](./AGENT_RUNTIME_TESTING_PLAN.md)
- Report issues: Please submit test-related issues in project Issues
- Contribute code: Please ensure new code has corresponding test coverage

---

This test suite ensures the quality and reliability of the Agent Runtime module. Follow best practices and write clear, maintainable test code.
