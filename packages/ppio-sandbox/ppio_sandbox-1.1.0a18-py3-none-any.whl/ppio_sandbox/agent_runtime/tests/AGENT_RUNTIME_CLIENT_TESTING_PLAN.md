# Agent Runtime Client Module Testing Plan

## 🎯 Testing Goals

- Ensure functional correctness of each component
- Verify integration and interaction between modules
- Test exception handling and edge cases
- Verify correctness of asynchronous operations
- Ensure API compatibility and stability

## 📁 Test Directory Structure

```
tests/
├── agent_runtime/
│   ├── __init__.py
│   ├── conftest.py                    # Shared test configuration and fixtures
│   ├── client/
│   │   ├── __init__.py
│   │   ├── unit/                      # Unit tests
│   │   │   ├── test_auth.py          # AuthManager unit tests
│   │   │   ├── test_template.py      # TemplateManager unit tests  
│   │   │   ├── test_session.py       # SandboxSession unit tests
│   │   │   ├── test_client.py        # AgentRuntimeClient unit tests
│   │   │   ├── test_models.py        # Data model tests
│   │   │   └── test_exceptions.py    # Exception class tests
│   │   ├── integration/               # Integration tests
│   │   │   ├── test_end_to_end.py    # End-to-end tests
│   │   │   ├── test_session_lifecycle.py  # Session lifecycle tests
│   │   │   ├── test_streaming.py     # Streaming response tests
│   │   │   └── test_concurrent.py    # Concurrent tests
│   │   └── mocks/                     # Mocks and test utilities
│   │       ├── __init__.py
│   │       ├── mock_sandbox.py       # Mock Sandbox
│   │       ├── mock_api.py           # Mock API responses
│   │       └── test_fixtures.py      # Test data
│   └── examples/                      # Examples and demonstration tests
│       └── test_client_example.py    # Verify example code
```

## 🧪 Unit Testing Plan

### 1. AuthManager Tests (`test_auth.py`)

**Test Scope:**
- API Key validation logic
- Environment variable reading
- Authentication header generation
- Invalid credential handling

**Test Cases:**
- ✅ Correct API Key initialization
- ✅ Read API Key from environment variable
- ✅ API Key format validation
- ✅ Invalid API Key throws exception
- ✅ Authentication header format correctness
- ✅ API Key update functionality
- ❌ Error handling for missing API Key
- ❌ Incorrectly formatted API Key

### 2. TemplateManager Tests (`test_template.py`)

**Test Scope:**
- Template list query
- Template details retrieval
- Filtering and search functionality
- API error handling

**Test Cases:**
- ✅ List all templates
- ✅ Get specific template details
- ✅ Check template existence
- ✅ HTTP client closes correctly
- ❌ Network error handling
- ❌ Template not found error
- ❌ Authentication failure handling
- ❌ Invalid response format handling

### 3. SandboxSession Tests (`test_session.py`)

**Test Scope:**
- Session creation and initialization
- Agent invocation (synchronous/asynchronous)
- Session state management
- Lifecycle operations

**Test Cases:**
- ✅ Session initialized correctly
- ✅ Synchronous Agent invocation
- ✅ Asynchronous Agent invocation
- ✅ Streaming response handling
- ✅ Session pause and resume
- ✅ Health check (ping)
- ✅ Session state tracking
- ✅ Session closed correctly
- ✅ Specified Sandbox/session ID invocation
- ✅ Property access (session_id etc.)
- ❌ Invalid request format
- ❌ Network timeout handling
- ❌ Invocation after session closed
- ❌ Agent invocation failure

### 4. AgentRuntimeClient Tests (`test_client.py`)

**Test Scope:**
- Client initialization
- Session management functionality
- Convenience invocation methods
- Context manager

**Test Cases:**
- ✅ Client initialized correctly
- ✅ Create new session
- ✅ Get existing session
- ✅ List all sessions
- ✅ Close specific session
- ✅ Close all sessions
- ✅ Convenience Agent invocation
- ✅ Streaming Agent invocation
- ✅ Template management delegation
- ✅ Context manager support
- ❌ Invalid configuration handling
- ❌ Session creation failure
- ❌ Session not found error
- ❌ Operations after client closed

### 5. Data Model Tests (`test_models.py`)

**Test Scope:**
- Pydantic model validation
- Data serialization/deserialization
- Default values and optional fields
- Model relationships and inheritance

**Test Cases:**
- ✅ InvocationRequest model validation
- ✅ InvocationResponse model validation
- ✅ AgentTemplate model validation
- ✅ SessionStatus enum
- ✅ Backward compatible properties (session_id)
- ✅ Model serialization/deserialization
- ❌ Invalid field value validation
- ❌ Missing required fields

### 6. Exception Class Tests (`test_exceptions.py`)

**Test Scope:**
- Exception inheritance hierarchy
- Exception messages and error codes
- Exception catching and handling

**Test Cases:**
- ✅ Exception class inheritance hierarchy correct
- ✅ Exception message setting and retrieval
- ✅ Error code setting and retrieval
- ✅ Exception type differentiation

## 🔗 Integration Testing Plan

### 1. End-to-End Tests (`test_end_to_end.py`)

**Test Scenarios:**
- Complete Agent invocation workflow
- From template query to result retrieval
- Multiple invocation method validation

**Test Flow:**
1. Initialize client
2. Query available templates
3. Create session
4. Invoke Agent
5. Process response
6. Clean up resources

### 2. Session Lifecycle Tests (`test_session_lifecycle.py`)

**Test Scenarios:**
- Complete session lifecycle
- State transition correctness
- Resource management

**Test Flow:**
1. Create session → ACTIVE
2. Execute invocation → Remain ACTIVE
3. Pause session → PAUSED
4. Resume session → ACTIVE
5. Close session → CLOSED

### 3. Streaming Response Tests (`test_streaming.py`)

**Test Scenarios:**
- Streaming Agent invocation
- Data stream integrity
- Exception interruption handling

## 🎭 Mocks and Test Utilities

### 1. Mock Sandbox (`mock_sandbox.py`)

Simulates Sandbox instance behavior:
- Simulate start, pause, resume operations
- Provide controllable response data
- Simulate various error conditions

### 2. Mock API (`mock_api.py`)

Simulates HTTP API responses:
- Template query API
- Agent invocation API
- Various error status codes

### 3. Test Data (`test_fixtures.py`)

Provides fixed test data:
- Sample template data
- Sample requests/responses
- Error scenario data

## 📋 Test Configuration and Utilities

### 1. Shared Configuration (`conftest.py`)

```python
# Fixtures definition
@pytest.fixture
async def mock_client():
    """Provide Mock AgentRuntimeClient"""

@pytest.fixture
async def real_client():
    """Provide real client (requires environment variables)"""

@pytest.fixture
def sample_template():
    """Provide sample template data"""

@pytest.fixture
def sample_request():
    """Provide sample request data"""
```

### 2. Test Markers

```python
# Unit tests
@pytest.mark.unit

# Integration tests
@pytest.mark.integration

# Tests requiring network
@pytest.mark.network

```

## 🔧 Test Execution Strategy

### 1. Layered Test Execution

```bash
# Unit tests only (fast)
pytest tests/agent_runtime/client/unit/ -m unit

# Integration tests (requires environment)
pytest tests/agent_runtime/client/integration/ -m integration

# Complete test suite
pytest tests/agent_runtime/client/
```

### 2. Environment Requirements

- **Unit Tests**: No external dependencies, pure Mocks
- **Integration Tests**: Requires `PPIO_API_KEY` environment variable

### 3. CI/CD Integration

- **Pull Request**: Run unit tests + partial integration tests
- **Main Branch**: Run complete test suite
- **Pre-release**: Run all tests

## 📊 Test Coverage Goals

- **Unit Test Coverage**: ≥ 90%
- **Integration Test Coverage**: ≥ 80%
- **Branch Coverage**: ≥ 85%
- **Critical Path Coverage**: 100%

## 🛠️ Required Dependencies

```toml
[tool.poetry.group.test.dependencies]
pytest = "^7.0.0"
pytest-asyncio = "^0.23.0"
pytest-mock = "^3.12.0"
pytest-cov = "^4.1.0"
aioresponses = "^0.7.4"
httpx = "^0.27.0"
pytest-xdist = "^3.3.0"  # Parallel testing
```

## 📈 Test Execution Plan

### Phase 1: Core Unit Tests
1. `test_auth.py` - AuthManager basic functionality
2. `test_models.py` - Data model validation
3. `test_exceptions.py` - Exception handling

### Phase 2: Component Unit Tests
1. `test_template.py` - TemplateManager functionality
2. `test_session.py` - SandboxSession functionality
3. `test_client.py` - AgentRuntimeClient functionality

### Phase 3: Integration Tests
1. `test_end_to_end.py` - End-to-end workflow
2. `test_session_lifecycle.py` - Session lifecycle
3. `test_streaming.py` - Streaming response
4. `test_concurrent.py` - Concurrent testing

## 🎯 Quality Assurance

### Code Coverage Requirements
- Each test file must have corresponding coverage report
- Critical business logic must achieve 100% coverage
- Exception handling paths must all be tested

### Test Data Management
- Use fixed test data sets
- Mock data consistent with real API responses
- Sensitive data stored using environment variables or encryption

### Test Isolation
- Each test case independent of others
- No dependency on external state or other test results
- Appropriate setup and teardown

## 📝 Test Reports

### Automated Reports
- Test result statistics
- Coverage reports
- Failed case details

### Manual Verification
- Critical functionality manual verification
- User experience testing
- Documentation example verification

---

This testing plan ensures the quality and reliability of the Agent Runtime Client module, covering a complete testing system from unit tests to integration tests.
