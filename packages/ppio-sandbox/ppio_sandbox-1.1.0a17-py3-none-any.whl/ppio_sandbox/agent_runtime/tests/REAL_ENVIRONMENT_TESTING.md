# Real Environment Testing Guide

## 📋 Overview

This project contains three types of tests:

1. **Unit Tests** (`unit/`) - Use Mock data for fast testing of individual components
2. **Integration Tests** (`integration/`) - Primarily use Mock data to test interactions between components
3. **Real Environment Tests** - Use real PPIO API to verify end-to-end functionality

## 🔧 Environment Variable Configuration

### Required Environment Variables

```bash
# Real PPIO API Key (required)
export PPIO_API_KEY="your-actual-api-key-here"

# Specify sandbox template ID for testing
export PPIO_TEST_TEMPLATE_ID="your-test-template-id"
```

### Optional Environment Variables

```bash
# Test timeout (seconds)
export TEST_TIMEOUT=30

# Debug mode
export TEST_DEBUG=false

# Custom API base URL
export TEST_BASE_URL=https://api.ppio.cloud
```

## 🚀 Running Real Environment Tests

### Method 1: Using Test Scripts

```bash
cd /Users/jason/Documents/work/PPLabs/Platform/agent-sandbox-sdks/sdk-python/tests/agent_runtime

# Set environment variable
export PPIO_API_KEY="your-actual-api-key"

# Run all integration tests (including real environment tests)
poetry run python run_tests.py --client-integration --verbose

# Or run only real environment tests
poetry run pytest client/test_real_e2e.py -v
```

### Method 2: Using pytest Markers

```bash
cd /Users/jason/Documents/work/PPLabs/Platform/agent-sandbox-sdks/sdk-python

# Set environment variable
export PPIO_API_KEY="your-actual-api-key"

# Run only tests requiring network
poetry run pytest . -m network -v

# Run real environment tests
poetry run pytest client/test_real_e2e.py -v

# Exclude slow tests
poetry run pytest . -m "network and not slow" -v
```

### Method 3: Temporarily Set Environment Variables

```bash
cd /Users/jason/Documents/work/PPLabs/Platform/agent-sandbox-sdks/sdk-python

# Temporarily set and run tests
PPIO_API_KEY="your-key" poetry run pytest client/test_real_e2e.py -v
```

## 📊 Test Marker Descriptions

- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.network` - Tests requiring network connection
- `@pytest.mark.slow` - Long-running tests
- `@pytest.mark.asyncio` - Asynchronous tests

## 🎯 Test Types

### 1. Basic Functionality Tests

```python
# Test template listing
test_real_template_listing()

# Test session creation and invocation
test_real_session_creation_and_invocation()

# Test convenience method
test_real_convenience_method()
```

### 2. Advanced Functionality Tests

```python
# Test streaming invocation
test_real_streaming_invocation()

# Test multiple session management
test_real_multiple_sessions()
```

### 3. Error Handling Tests

```python
# Test invalid template ID
test_invalid_template_id()

# Test invalid API Key
test_invalid_api_key()
```

## ⚠️ Important Notes

### Resource Consumption
- Real environment tests consume API quota
- Recommend limiting test frequency in development environments
- Use dedicated API Key for testing

### Test Data
- Tests create real sandbox sessions
- All sessions are automatically cleaned up after tests
- Manual resource cleanup may be needed if tests are interrupted

### Network Dependencies
- Real environment tests require stable network connection
- Tests may fail due to network issues
- Recommend setting up retry mechanisms in CI/CD

## 🔍 Debugging Real Environment Tests

### Enable Verbose Logging

```bash
# Enable debug output
TEST_DEBUG=true poetry run pytest client/test_real_e2e.py -v -s

# Display full output
poetry run pytest client/test_real_e2e.py -v -s --tb=long
```

### Run Specific Tests Individually

```bash
# Run a single test method
poetry run pytest client/test_real_e2e.py::TestRealEnvironmentE2E::test_real_template_listing -v -s
```

## 📝 Best Practices

### Development Phase
1. Primarily use Mock tests for quick verification
2. Regularly run real environment tests to verify integration
3. Run complete real environment tests before PR

### CI/CD Integration
1. Set up dedicated API Key in test environment
2. Securely pass credentials using environment variables
3. Set up reasonable timeout and retry mechanisms

### Before Production Deployment
1. Run complete real environment test suite
2. Verify all critical paths
3. Check performance and resource usage

## 🛠️ Troubleshooting

### Common Errors

1. **PPIO_API_KEY not set**
   ```bash
   export PPIO_API_KEY="your-key"
   ```

2. **Template unavailable**
   ```bash
   export PPIO_TEST_TEMPLATE_ID="valid-template-id"
   ```

3. **Network connection error**
   - Check network connection
   - Verify API endpoint accessibility

4. **API quota limit**
   - Check API quota usage
   - Reduce concurrent test count

## 🔗 Related Files

- `conftest.py` - Test configuration and fixtures
- `test_real_e2e.py` - Real environment end-to-end tests
- `run_tests.py` - Test execution script
- Existing `test_end_to_end.py` - Contains partial real environment tests
