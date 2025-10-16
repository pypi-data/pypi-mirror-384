# Testing Guide

Comprehensive guide to testing Simply-MCP-PY servers.

## Testing Framework

Simply-MCP-PY uses pytest for testing. Install testing dependencies:

```bash
pip install simply-mcp[dev]
```

## Basic Testing

### Test Structure

Create a `tests/` directory:

```
tests/
├── __init__.py
├── conftest.py
├── test_tools.py
├── test_resources.py
└── test_integration.py
```

### Simple Test

```python
# tests/test_tools.py
import pytest
from server import MyServer

def test_add_tool():
    server = MyServer()
    result = server.add(2, 3)
    assert result == 5

def test_greet_tool():
    server = MyServer()
    result = server.greet("Alice", formal=False)
    assert result == "Hey Alice!"

    result = server.greet("Bob", formal=True)
    assert result == "Good day, Bob."
```

## Testing Tools

### Sync Tools

```python
from simply_mcp import mcp_server, tool

@mcp_server(name="test-server")
class TestServer:
    @tool(description="Add numbers")
    def add(self, a: int, b: int) -> int:
        return a + b

# Test
def test_add():
    server = TestServer()
    assert server.add(2, 3) == 5
    assert server.add(-1, 1) == 0
```

### Async Tools

```python
import pytest
from simply_mcp import mcp_server, tool

@mcp_server(name="async-server")
class AsyncServer:
    @tool(description="Async operation")
    async def async_add(self, a: int, b: int) -> int:
        return a + b

# Test
@pytest.mark.asyncio
async def test_async_add():
    server = AsyncServer()
    result = await server.async_add(2, 3)
    assert result == 5
```

## Testing Resources

```python
from simply_mcp import mcp_server, resource

@mcp_server(name="resource-server")
class ResourceServer:
    @resource(uri="config://app", mime_type="application/json")
    def app_config(self) -> dict:
        return {"name": "test", "version": "1.0.0"}

# Test
def test_resource():
    server = ResourceServer()
    config = server.app_config()
    assert config["name"] == "test"
    assert config["version"] == "1.0.0"
```

## Testing Prompts

```python
from simply_mcp import mcp_server, prompt

@mcp_server(name="prompt-server")
class PromptServer:
    @prompt(description="Code review")
    def code_review(self, language: str = "python") -> str:
        return f"Review this {language} code"

# Test
def test_prompt():
    server = PromptServer()
    result = server.code_review("python")
    assert "python" in result.lower()
```

## Fixtures

### Basic Fixture

```python
# tests/conftest.py
import pytest
from server import MyServer

@pytest.fixture
def server():
    """Provide a fresh server instance for each test."""
    return MyServer()

# tests/test_tools.py
def test_with_fixture(server):
    result = server.add(1, 2)
    assert result == 3
```

### Async Fixture

```python
import pytest

@pytest.fixture
async def async_server():
    """Async server fixture."""
    server = AsyncServer()
    yield server
    # Cleanup code here

@pytest.mark.asyncio
async def test_with_async_fixture(async_server):
    result = await async_server.async_add(1, 2)
    assert result == 3
```

## Mocking

### Mocking External Services

```python
from unittest.mock import Mock, patch

def test_with_mock(server):
    with patch('server.external_api') as mock_api:
        mock_api.return_value = {"data": "test"}
        result = server.call_external_api()
        assert result["data"] == "test"
        mock_api.assert_called_once()
```

### Mocking File I/O

```python
from unittest.mock import mock_open, patch

def test_read_file(server):
    mock_data = "test content"
    with patch("builtins.open", mock_open(read_data=mock_data)):
        result = server.read_file("test.txt")
        assert result == mock_data
```

## Testing HTTP Transport

```python
import pytest
import httpx

@pytest.fixture
async def http_server():
    """Start HTTP server for testing."""
    from server import MyServer
    server = MyServer()
    # Start server on test port
    await server.start(transport="http", port=5000)
    yield server
    await server.stop()

@pytest.mark.asyncio
async def test_http_endpoint(http_server):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:5000/tools/add",
            json={"a": 2, "b": 3}
        )
        assert response.status_code == 200
        assert response.json()["result"] == 5
```

## Testing Error Handling

```python
import pytest

def test_error_handling(server):
    # Test invalid input
    with pytest.raises(ValueError):
        server.divide(10, 0)

    # Test error response
    result = server.safe_divide(10, 0)
    assert result["success"] is False
    assert "error" in result
```

## Testing Progress

```python
import pytest
from simply_mcp import tool, Progress

@tool(description="Process with progress")
async def process_data(data: list, progress: Progress) -> dict:
    for i, item in enumerate(data):
        await progress.update(
            percentage=(i / len(data)) * 100,
            message=f"Processing {i+1}/{len(data)}"
        )
    return {"processed": len(data)}

@pytest.mark.asyncio
async def test_progress():
    progress = Progress()
    data = list(range(10))
    result = await process_data(data, progress)
    assert result["processed"] == 10
```

## Integration Tests

### Full Server Test

```python
import pytest
from simply_mcp import BuildMCPServer

@pytest.fixture
def full_server():
    """Create complete server instance."""
    mcp = BuildMCPServer(name="test-server", version="1.0.0")

    @mcp.add_tool(description="Test tool")
    def test_tool(param: str) -> str:
        return f"Result: {param}"

    return mcp

def test_full_server(full_server):
    # Test server metadata
    assert full_server.name == "test-server"
    assert full_server.version == "1.0.0"

    # Test tools are registered
    tools = full_server.list_tools()
    assert len(tools) == 1
    assert tools[0]["name"] == "test_tool"
```

### End-to-End Test

```python
@pytest.mark.asyncio
async def test_e2e():
    """End-to-end test of complete workflow."""
    # Create server
    server = MyServer()

    # Call multiple tools
    result1 = server.add(1, 2)
    assert result1 == 3

    result2 = server.multiply(result1, 2)
    assert result2 == 6

    # Check resource
    config = server.get_config()
    assert config["status"] == "running"
```

## Test Coverage

### Run with Coverage

```bash
pytest --cov=simply_mcp --cov-report=html
```

### View Report

```bash
open htmlcov/index.html
```

### Coverage Configuration

Create `.coveragerc`:

```ini
[run]
source = simply_mcp
omit =
    tests/*
    */test_*.py

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
```

## Parametrized Tests

```python
@pytest.mark.parametrize("a,b,expected", [
    (1, 2, 3),
    (0, 0, 0),
    (-1, 1, 0),
    (100, 200, 300),
])
def test_add_parametrized(server, a, b, expected):
    result = server.add(a, b)
    assert result == expected
```

## Testing Configuration

```python
def test_config():
    from simply_mcp.core.config import ServerConfig

    config = ServerConfig(
        name="test-server",
        version="1.0.0"
    )

    assert config.name == "test-server"
    assert config.version == "1.0.0"
```

## Performance Testing

```python
import time

def test_performance(server):
    """Test tool execution time."""
    start = time.time()
    for _ in range(1000):
        server.add(1, 2)
    duration = time.time() - start

    # Should complete 1000 calls in under 1 second
    assert duration < 1.0
```

## Testing Best Practices

### 1. One Assertion Per Test

```python
# Good
def test_add_positive():
    assert server.add(1, 2) == 3

def test_add_negative():
    assert server.add(-1, -2) == -3

# Avoid
def test_add_all_cases():
    assert server.add(1, 2) == 3
    assert server.add(-1, -2) == -3
    assert server.add(0, 0) == 0
```

### 2. Use Fixtures for Setup

```python
@pytest.fixture
def configured_server():
    server = MyServer()
    server.setup()
    yield server
    server.teardown()
```

### 3. Test Edge Cases

```python
def test_edge_cases(server):
    # Empty string
    assert server.process("") == ""

    # Very long string
    long_str = "a" * 10000
    result = server.process(long_str)
    assert len(result) <= 10000

    # Special characters
    assert server.process("!@#$%") is not None
```

### 4. Mock External Dependencies

```python
@patch('server.database')
def test_with_db_mock(mock_db, server):
    mock_db.query.return_value = [{"id": 1}]
    result = server.get_data()
    assert len(result) == 1
```

## Continuous Integration

### GitHub Actions

Create `.github/workflows/test.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.10'
    - name: Install dependencies
      run: |
        pip install -e .[dev]
    - name: Run tests
      run: |
        pytest --cov=simply_mcp --cov-report=xml
    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

## Next Steps

- [Configuration Guide](configuration.md) - Configure for testing
- [Deployment Guide](deployment.md) - Deploy tested servers
- [API Reference](../api/core/server.md) - Server API details
