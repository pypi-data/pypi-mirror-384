# Troubleshooting Guide

This guide helps you diagnose and resolve common issues when working with simply-mcp-py.

## Table of Contents

- [Installation Issues](#installation-issues)
- [Import and Module Errors](#import-and-module-errors)
- [Server Startup Issues](#server-startup-issues)
- [Transport Configuration Issues](#transport-configuration-issues)
- [Runtime Errors](#runtime-errors)
- [Authentication and Security Issues](#authentication-and-security-issues)
- [Platform-Specific Issues](#platform-specific-issues)
- [Performance Issues](#performance-issues)
- [Debugging Techniques](#debugging-techniques)

---

## Installation Issues

### Python Version Incompatibility

**Problem:** Error about incompatible Python version during installation

```
ERROR: Package 'simply-mcp' requires a different Python: 3.9.0 not in '>=3.10'
```

**Solution:**

Simply-MCP-PY requires Python 3.10 or higher. Check your Python version:

```bash
python --version
# or
python3 --version
```

If you have multiple Python versions installed:

```bash
# Use specific Python version
python3.10 -m pip install simply-mcp

# Or use pyenv
pyenv local 3.10.0
pip install simply-mcp
```

> **Quick Fix:** Install Python 3.10+ from [python.org](https://python.org) or use a virtual environment with the correct version.

---

### Dependency Conflicts

**Problem:** Conflicting dependencies during installation

```
ERROR: Cannot install simply-mcp because these package versions have conflicting dependencies
```

**Solution:**

Create a fresh virtual environment:

```bash
# Create new virtual environment
python3.10 -m venv venv

# Activate it
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Install simply-mcp
pip install simply-mcp
```

If conflicts persist, try upgrading pip and setuptools:

```bash
pip install --upgrade pip setuptools wheel
pip install simply-mcp
```

---

### Missing Optional Dependencies

**Problem:** ImportError for optional features

```python
ImportError: No module named 'pyinstaller'
```

**Solution:**

Install the appropriate optional dependency group:

```bash
# For development tools
pip install simply-mcp[dev]

# For documentation building
pip install simply-mcp[docs]

# For bundling/packaging
pip install simply-mcp[bundling]

# Install all optional dependencies
pip install simply-mcp[dev,docs,bundling]
```

---

## Import and Module Errors

### Cannot Import simply_mcp

**Problem:** Module not found error

```python
ModuleNotFoundError: No module named 'simply_mcp'
```

**Solution:**

1. Verify installation:

```bash
pip show simply-mcp
```

2. Check if you're in the correct virtual environment:

```bash
which python  # Linux/macOS
where python  # Windows
```

3. Reinstall if necessary:

```bash
pip uninstall simply-mcp
pip install simply-mcp
```

---

### Cannot Import MCP SDK

**Problem:** Error importing underlying MCP library

```python
ModuleNotFoundError: No module named 'mcp'
```

**Solution:**

The `mcp` package should be installed automatically. If missing:

```bash
pip install mcp>=0.1.0
```

---

### Pydantic Import Errors

**Problem:** Pydantic version conflicts

```python
ImportError: cannot import name 'BaseModel' from 'pydantic'
```

**Solution:**

Simply-MCP-PY requires Pydantic v2:

```bash
pip install --upgrade "pydantic>=2.0.0" "pydantic-settings>=2.0.0"
```

If you have legacy code requiring Pydantic v1, use a separate virtual environment.

---

## Server Startup Issues

### Configuration File Not Found

**Problem:** Server can't find configuration file

```
[CONFIG_NOT_FOUND] Configuration file not found: simplymcp.config.toml
```

**Solution:**

1. Create configuration file in your project root:

```bash
touch simplymcp.config.toml
```

2. Or specify config path explicitly:

```bash
simply-mcp run server.py --config /path/to/config.toml
```

3. Configuration is optional - server runs with defaults if no config is found.

> **Quick Fix:** Simply-MCP works without a config file using sensible defaults. Only create one if you need custom settings.

---

### Invalid Configuration Format

**Problem:** Configuration validation fails

```
[CONFIG_VALIDATION_FAILED] Invalid configuration: field 'port' must be between 1 and 65535
```

**Solution:**

Check your configuration syntax:

```toml
# Correct configuration
[server]
name = "my-server"
version = "1.0.0"

[transport]
type = "http"
port = 3000  # Must be 1-65535

[logging]
level = "INFO"  # Must be DEBUG, INFO, WARNING, ERROR, or CRITICAL
```

Validate your config:

```bash
simply-mcp config validate
```

---

### Server Initialization Fails

**Problem:** Server fails to initialize

```python
RuntimeError: Server initialization failed
```

**Solution:**

Enable debug logging to see detailed error messages:

```bash
export SIMPLY_MCP_LOG_LEVEL=DEBUG
simply-mcp run server.py
```

Common causes:
- Invalid handler signatures
- Missing required parameters
- Circular imports in server file

---

### No Tools/Prompts/Resources Detected

**Problem:** Server starts but shows no components

```
Warning: No tools, prompts, or resources found in server.py
```

**Solution:**

1. Ensure you're using decorators correctly:

```python
from simply_mcp import mcp_server, tool

@mcp_server(name="my-server")  # Don't forget this!
class MyServer:
    @tool()  # Decorator with parentheses
    def my_tool(self) -> str:
        return "Hello"
```

2. For functional API, ensure methods are called:

```python
from simply_mcp import BuildMCPServer

mcp = BuildMCPServer("my-server")

@mcp.add_tool()  # Must use add_tool, not tool
def my_tool() -> str:
    return "Hello"
```

3. Verify file is being executed:

```bash
simply-mcp run server.py --verbose
```

---

## Transport Configuration Issues

### Port Already in Use

**Problem:** HTTP/SSE server can't bind to port

```
OSError: [Errno 48] Address already in use
# or on Windows
OSError: [WinError 10048] Only one usage of each socket address is normally permitted
```

**Solution:**

1. Find and kill the process using the port:

```bash
# Linux/macOS
lsof -i :3000
kill -9 <PID>

# Windows
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

2. Or use a different port:

```bash
simply-mcp run server.py --transport http --port 3001
```

3. Use port 0 to auto-assign an available port:

```bash
simply-mcp run server.py --transport http --port 0
```

---

### HTTP Transport Not Responding

**Problem:** HTTP server starts but doesn't respond to requests

```
Connection refused when accessing http://localhost:3000
```

**Solution:**

1. Check server is listening on correct interface:

```toml
[transport]
host = "0.0.0.0"  # Listen on all interfaces
port = 3000
```

2. Verify server is running:

```bash
# Test health endpoint
curl http://localhost:3000/health
```

3. Check firewall settings allow the port.

4. For Docker/containers, ensure port is properly mapped:

```bash
docker run -p 3000:3000 my-mcp-server
```

---

### CORS Issues with HTTP Transport

**Problem:** Browser requests blocked by CORS policy

```
Access to XMLHttpRequest blocked by CORS policy: No 'Access-Control-Allow-Origin' header
```

**Solution:**

Enable CORS in configuration:

```toml
[transport]
type = "http"
cors_enabled = true
cors_origins = ["http://localhost:3000", "https://myapp.com"]
```

Or allow all origins (development only):

```toml
[transport]
cors_enabled = true
cors_origins = ["*"]
```

---

### SSE Connection Drops

**Problem:** Server-Sent Events connection disconnects frequently

**Solution:**

1. Increase keepalive interval:

```toml
[transport]
type = "sse"
keepalive_interval = 30  # seconds
```

2. Check proxy/load balancer timeout settings.

3. Implement reconnection logic in client:

```javascript
const eventSource = new EventSource('/sse');
eventSource.onerror = () => {
  setTimeout(() => {
    // Reconnect after delay
    eventSource = new EventSource('/sse');
  }, 1000);
};
```

---

### Stdio Transport Encoding Issues

**Problem:** Garbled output or encoding errors with stdio transport

```
UnicodeDecodeError: 'utf-8' codec can't decode byte...
```

**Solution:**

1. Ensure environment uses UTF-8:

```bash
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8
```

2. On Windows, set console encoding:

```bash
chcp 65001  # UTF-8 code page
```

3. Specify encoding in configuration:

```toml
[transport]
type = "stdio"
encoding = "utf-8"
```

---

## Runtime Errors

### Tool Execution Failures

**Problem:** Tool call returns error

```
[HANDLER_EXECUTION_FAILED] Handler execution failed: my_tool - division by zero
```

**Solution:**

1. Add error handling to your tools:

```python
@tool()
def divide(self, a: float, b: float) -> float:
    """Divide two numbers."""
    try:
        return a / b
    except ZeroDivisionError:
        raise ValueError("Cannot divide by zero")
```

2. Check input validation:

```python
@tool()
def process_age(self, age: int) -> str:
    """Process user age."""
    if age < 0 or age > 150:
        raise ValueError("Age must be between 0 and 150")
    return f"Age is {age}"
```

3. Enable debug logging to see full stack trace:

```bash
export SIMPLY_MCP_LOG_LEVEL=DEBUG
```

---

### Schema Validation Errors

**Problem:** Input doesn't match expected schema

```
[SCHEMA_VALIDATION_FAILED] Validation error: field 'count' must be an integer
```

**Solution:**

1. Ensure type hints match expected inputs:

```python
@tool()
def repeat(self, text: str, count: int) -> str:  # count must be int
    """Repeat text."""
    return text * count
```

2. Use Pydantic models for complex inputs:

```python
from pydantic import BaseModel, Field

class UserInput(BaseModel):
    name: str = Field(..., min_length=1)
    age: int = Field(..., ge=0, le=150)
    email: str = Field(..., pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')

@tool()
def create_user(self, user: UserInput) -> dict:
    """Create a user."""
    return user.dict()
```

3. Review error message for specific field that failed validation.

---

### Async/Await Issues

**Problem:** Sync handler called with await or vice versa

```
TypeError: object NoneType can't be used in 'await' expression
```

**Solution:**

1. For async tools, use `async def`:

```python
@tool()
async def fetch_data(self, url: str) -> dict:
    """Fetch data from URL."""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()
```

2. For sync tools, use regular `def`:

```python
@tool()
def calculate(self, x: int) -> int:
    """Calculate value."""
    return x * 2
```

3. Simply-MCP handles both automatically - just use the appropriate function type.

---

### Progress Reporting Errors

**Problem:** Progress updates fail or aren't displayed

```
TypeError: progress.update() got an unexpected keyword argument 'percentage'
```

**Solution:**

1. Use correct Progress API:

```python
from simply_mcp import tool, Progress

@tool()
async def long_task(self, items: list, progress: Progress) -> dict:
    """Process items with progress."""
    total = len(items)
    for i, item in enumerate(items):
        # Correct usage
        await progress.update(
            percentage=(i / total) * 100,
            message=f"Processing {i+1}/{total}"
        )
        # Process item...
    return {"processed": total}
```

2. Progress only works with async handlers.

3. Progress parameter must be last in function signature.

---

### JSON-RPC Protocol Errors

**Problem:** Invalid JSON-RPC messages

```
[MESSAGE_ERROR] Invalid JSON-RPC request: missing 'method' field
```

**Solution:**

1. Ensure requests follow JSON-RPC 2.0 spec:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "my_tool",
    "arguments": {}
  }
}
```

2. Check client library is compatible with JSON-RPC 2.0.

3. Enable request/response logging:

```bash
simply-mcp run server.py --log-requests
```

---

## Authentication and Security Issues

### Authentication Failures

**Problem:** Requests rejected with authentication error

```
[AUTHENTICATION_FAILED] Authentication required. Provide API key in Authorization header
```

**Solution:**

1. Configure API key authentication:

```toml
[auth]
enabled = true
type = "api_key"
api_keys = ["your-secret-key-here"]
```

2. Include API key in requests:

```bash
# Using Authorization header
curl -H "Authorization: Bearer your-secret-key-here" \
  http://localhost:3000/mcp

# Using X-API-Key header
curl -H "X-API-Key: your-secret-key-here" \
  http://localhost:3000/mcp
```

3. Verify key is correct and hasn't expired.

> **Quick Fix:** Disable authentication temporarily for debugging: Set `auth.enabled = false` in config.

---

### Rate Limiting Issues

**Problem:** Requests throttled by rate limiter

```
[RATE_LIMIT_EXCEEDED] Rate limit exceeded. Retry after 5 seconds.
```

**Solution:**

1. Adjust rate limits in configuration:

```toml
[rate_limit]
enabled = true
requests_per_minute = 100  # Increase limit
burst_size = 20           # Allow bursts
```

2. Implement exponential backoff in client:

```python
import time

def call_with_retry(func, max_retries=3):
    for i in range(max_retries):
        try:
            return func()
        except RateLimitError as e:
            if i == max_retries - 1:
                raise
            wait_time = 2 ** i  # Exponential backoff
            time.sleep(wait_time)
```

3. Check `Retry-After` header in HTTP responses.

4. Disable rate limiting for testing:

```toml
[rate_limit]
enabled = false
```

---

### HTTPS/TLS Configuration Issues

**Problem:** Certificate errors or HTTPS not working

**Solution:**

Simply-MCP-PY doesn't include built-in TLS support. For production HTTPS:

1. Use a reverse proxy (recommended):

```nginx
# nginx configuration
server {
    listen 443 ssl;
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

2. Or use a Python WSGI server with TLS:

```bash
pip install gunicorn
gunicorn --certfile=cert.pem --keyfile=key.pem simply_mcp.wsgi:app
```

---

## Platform-Specific Issues

### Windows-Specific Issues

#### Logging Handler Errors

**Problem:** Warning about logging handlers on Windows

```
Warning: Logging handlers not properly cleaned up
```

**Solution:**

This was fixed in v0.1.0b1. Update to the latest version:

```bash
pip install --upgrade simply-mcp
```

#### Path Separator Issues

**Problem:** File path errors with backslashes

```
FileNotFoundError: [Errno 2] No such file or directory: 'C:\\Users\\...'
```

**Solution:**

Use `pathlib` for cross-platform paths:

```python
from pathlib import Path

@tool()
def read_file(self, filename: str) -> str:
    """Read file content."""
    path = Path(filename)  # Handles separators correctly
    return path.read_text()
```

#### Console Encoding Issues

**Problem:** Unicode characters not displaying correctly

```
UnicodeEncodeError: 'charmap' codec can't encode character...
```

**Solution:**

Set UTF-8 encoding in Windows terminal:

```bash
# PowerShell
$OutputEncoding = [console]::InputEncoding = [console]::OutputEncoding = New-Object System.Text.UTF8Encoding

# Command Prompt
chcp 65001
```

Or use Windows Terminal which has better UTF-8 support.

#### Watch Mode Not Working

**Problem:** File changes not detected in watch mode

**Solution:**

This was fixed in v0.1.0b1. Ensure you have the latest version:

```bash
pip install --upgrade simply-mcp
```

If issues persist:

```bash
# Use polling instead of native file events
simply-mcp run server.py --watch --poll-interval 1.0
```

---

### Linux-Specific Issues

#### Permission Denied on Port < 1024

**Problem:** Cannot bind to port 80 or 443

```
PermissionError: [Errno 13] Permission denied
```

**Solution:**

1. Use port >= 1024:

```bash
simply-mcp run server.py --port 8080
```

2. Or grant capability to Python:

```bash
sudo setcap 'cap_net_bind_service=+ep' $(which python3)
```

3. Or run with sudo (not recommended):

```bash
sudo simply-mcp run server.py --port 80
```

---

### macOS-Specific Issues

#### SSL Certificate Verification Errors

**Problem:** HTTPS requests fail with certificate errors

```
ssl.SSLCertVerificationError: certificate verify failed
```

**Solution:**

Install certificates for Python:

```bash
# Run the certificates installation script
/Applications/Python\ 3.10/Install\ Certificates.command
```

Or use certifi:

```bash
pip install --upgrade certifi
```

---

## Performance Issues

### Slow Server Startup

**Problem:** Server takes too long to start

**Solution:**

1. Profile startup time:

```bash
python -m cProfile -o startup.prof server.py
```

2. Common causes:
   - Heavy imports (move to lazy loading)
   - Expensive initialization in class constructors
   - Large data loading at module level

3. Optimize imports:

```python
# Instead of importing at module level
# import expensive_library

@tool()
def use_expensive_lib(self) -> str:
    # Import only when needed
    import expensive_library
    return expensive_library.do_something()
```

---

### High Memory Usage

**Problem:** Server consuming excessive memory

**Solution:**

1. Monitor memory usage:

```bash
# Install memory profiler
pip install memory-profiler

# Profile your code
python -m memory_profiler server.py
```

2. Common causes:
   - Large in-memory caches
   - Resource leaks in handlers
   - Not cleaning up connections

3. Implement resource cleanup:

```python
@tool()
async def fetch_large_data(self) -> dict:
    """Fetch data with proper cleanup."""
    client = None
    try:
        client = aiohttp.ClientSession()
        async with client.get(url) as response:
            return await response.json()
    finally:
        if client:
            await client.close()
```

---

### High CPU Usage

**Problem:** Server consuming excessive CPU

**Solution:**

1. Profile CPU usage:

```bash
python -m cProfile -s cumulative server.py
```

2. Common causes:
   - Inefficient algorithms in handlers
   - Tight loops without await points
   - Heavy JSON serialization

3. Add async yields in long operations:

```python
@tool()
async def process_large_list(self, items: list) -> dict:
    """Process items efficiently."""
    results = []
    for i, item in enumerate(items):
        results.append(process_item(item))
        # Yield control every 100 items
        if i % 100 == 0:
            await asyncio.sleep(0)
    return {"results": results}
```

---

### Request Timeouts

**Problem:** Requests timing out with no response

**Solution:**

1. Increase timeout in configuration:

```toml
[transport]
request_timeout = 60  # seconds
```

2. Use progress reporting for long operations:

```python
@tool()
async def long_operation(self, progress: Progress) -> dict:
    """Long running operation."""
    for i in range(100):
        await process_chunk(i)
        await progress.update(
            percentage=i,
            message=f"Processing chunk {i}/100"
        )
    return {"status": "complete"}
```

3. Consider breaking operation into smaller chunks.

---

## Debugging Techniques

### Enable Debug Logging

**Problem:** Need detailed diagnostic information

**Solution:**

Set debug log level via environment variable:

```bash
export SIMPLY_MCP_LOG_LEVEL=DEBUG
simply-mcp run server.py
```

Or in configuration:

```toml
[logging]
level = "DEBUG"
format = "text"  # Use 'json' for structured logging
```

View logs with timestamps and context:

```bash
simply-mcp run server.py 2>&1 | tee debug.log
```

---

### Use Development Mode

**Problem:** Need enhanced debugging experience

**Solution:**

Use dev mode with auto-reload and verbose logging:

```bash
simply-mcp dev server.py
```

Features:
- Automatic reload on file changes
- DEBUG logging by default
- Component inspection (press 'l')
- Request/response logging
- Metrics display

Keyboard shortcuts in dev mode:
- `l` - List registered components
- `m` - Show metrics
- `r` - Force reload
- `q` - Quit

---

### Inspect Requests and Responses

**Problem:** Need to see raw request/response data

**Solution:**

Enable request logging:

```bash
simply-mcp run server.py --log-requests
```

Or use middleware for HTTP/SSE:

```toml
[logging]
log_requests = true
log_responses = true
```

For stdio transport, use a proxy or wrapper:

```bash
# Create a logging wrapper
import sys
import json

for line in sys.stdin:
    print(f"REQUEST: {line}", file=sys.stderr)
    # Forward to actual server
    sys.stdout.write(line)
    sys.stdout.flush()
```

---

### Test Individual Components

**Problem:** Need to test tools in isolation

**Solution:**

Create a test script:

```python
# test_tools.py
import asyncio
from server import MyServer

async def test_tool():
    server = MyServer()
    result = await server.my_tool(param="test")
    print(f"Result: {result}")
    assert result == expected

asyncio.run(test_tool())
```

Or use pytest:

```python
# tests/test_server.py
import pytest
from server import MyServer

@pytest.mark.asyncio
async def test_my_tool():
    server = MyServer()
    result = await server.my_tool(param="test")
    assert result == expected
```

Run tests:

```bash
pytest tests/ -v
```

---

### Use Python Debugger

**Problem:** Need to step through code execution

**Solution:**

1. Use pdb (Python debugger):

```python
@tool()
def debug_tool(self, value: int) -> int:
    """Tool with debugging."""
    import pdb; pdb.set_trace()  # Breakpoint
    result = value * 2
    return result
```

2. Or use ipdb (enhanced debugger):

```bash
pip install ipdb

# In code
import ipdb; ipdb.set_trace()
```

3. For VSCode, add launch configuration:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Debug MCP Server",
      "type": "python",
      "request": "launch",
      "module": "simply_mcp.cli.main",
      "args": ["run", "server.py"],
      "console": "integratedTerminal"
    }
  ]
}
```

---

### Check Server Health

**Problem:** Need to verify server is running correctly

**Solution:**

1. Use health endpoint (HTTP/SSE):

```bash
curl http://localhost:3000/health
```

Response:

```json
{
  "status": "healthy",
  "initialized": true,
  "running": true,
  "requests_handled": 42,
  "components": {
    "tools": 5,
    "prompts": 2,
    "resources": 3
  }
}
```

2. Use CLI inspection:

```bash
simply-mcp list server.py
```

3. Monitor system metrics:

```bash
# Install psutil
pip install psutil

# Monitor process
python -c "
import psutil
import os
p = psutil.Process(os.getpid())
print(f'Memory: {p.memory_info().rss / 1024 / 1024:.2f} MB')
print(f'CPU: {p.cpu_percent()}%')
"
```

---

### Analyze Error Traces

**Problem:** Complex error traces are hard to understand

**Solution:**

1. Install rich for better error formatting:

```bash
pip install rich
```

2. Enable rich traceback in code:

```python
from rich.traceback import install
install(show_locals=True)
```

3. Use structured exception handling:

```python
@tool()
def robust_tool(self, value: str) -> dict:
    """Tool with proper error handling."""
    try:
        result = process(value)
        return {"result": result}
    except ValueError as e:
        logger.error(f"Validation error: {e}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise
```

---

## Getting Help

If you've tried these troubleshooting steps and still have issues:

1. Check the [GitHub Issues](https://github.com/Clockwork-Innovations/simply-mcp-py/issues) for similar problems
2. Join discussions on [GitHub Discussions](https://github.com/Clockwork-Innovations/simply-mcp-py/discussions)
3. Review the [API Reference](../api/index.md) for detailed documentation
4. Check the [Configuration Guide](configuration.md) for setup options
5. Look at [Examples](../../examples/) for working code

When reporting issues, include:
- Simply-MCP version (`pip show simply-mcp`)
- Python version (`python --version`)
- Operating system
- Full error message and stack trace
- Minimal reproducible example
- Steps to reproduce

---

## Related Documentation

- [Configuration Guide](configuration.md) - Server configuration options
- [Deployment Guide](deployment.md) - Production deployment best practices
- [Testing Guide](testing.md) - Testing your MCP servers
- [API Reference](../api/index.md) - Complete API documentation
