# Examples

Explore working examples demonstrating various features of Simply-MCP-PY.

## Basic Examples

### Simple Server
A minimal MCP server demonstrating the basics.

**File**: `examples/simple_server.py`

```python
from simply_mcp import mcp_server, tool

@mcp_server(name="simple", version="1.0.0")
class SimpleServer:
    @tool(description="Add two numbers")
    def add(self, a: int, b: int) -> int:
        return a + b
```

**Run**: `simply-mcp run examples/simple_server.py`

### Decorator Example
Comprehensive example using the Decorator API.

**File**: `examples/decorator_example.py`

Demonstrates:
- Multiple tools with various parameter types
- Resources with different MIME types
- Prompts with template generation
- Error handling

**Run**: `simply-mcp run examples/decorator_example.py`

## Transport Examples

### HTTP Server
Running an MCP server over HTTP.

**File**: `examples/http_server.py`

```python
from simply_mcp import mcp_server, tool

@mcp_server(name="http-server", version="1.0.0")
class HTTPServer:
    @tool(description="Get server status")
    def status(self) -> dict:
        return {"status": "running", "transport": "http"}
```

**Run**: `simply-mcp run examples/http_server.py --transport http --port 3000`

## Advanced Features

### Progress Reporting
Long-running operations with progress updates.

**File**: `examples/progress_example.py`

Demonstrates:
- Async tools with progress tracking
- Progress percentage and messages
- Cancellation support

**Run**: `simply-mcp run examples/progress_example.py`

### Binary Resources
Serving binary content (images, PDFs, etc.).

**File**: `examples/binary_resources_example.py`

Demonstrates:
- Binary file resources
- Base64 encoding
- MIME type handling

**Run**: `simply-mcp run examples/binary_resources_example.py`

### Authentication
Securing your MCP server with authentication.

**File**: `examples/authenticated_server.py`

Demonstrates:
- API key authentication
- Request validation
- Security middleware

**Run**: `simply-mcp run examples/authenticated_server.py --transport http`

### Rate Limiting
Protecting your server from excessive requests.

**File**: `examples/rate_limited_server.py`

Demonstrates:
- Rate limiting per endpoint
- Token bucket algorithm
- Custom rate limit responses

**Run**: `simply-mcp run examples/rate_limited_server.py --transport http`

## Development Examples

### Watch Mode
Auto-reload during development.

**File**: `examples/watch_example.py`

**Run**: `simply-mcp run examples/watch_example.py --watch`

Make changes to the file and watch it automatically reload.

### Development Mode
Full development environment with hot reload and debugging.

**File**: `examples/dev_example.py`

**Run**: `simply-mcp dev examples/dev_example.py`

### Bundling
Create standalone executables.

**Run**: `simply-mcp bundle examples/simple_server.py --output dist/`

## Production Examples

### Production Server
Production-ready server with all best practices.

**File**: `examples/production_server.py`

Demonstrates:
- Environment-based configuration
- Structured logging
- Error handling
- Health checks
- Graceful shutdown

**Run**: `simply-mcp run examples/production_server.py`

### Data Analysis Server
Real-world example for data analysis.

**File**: `examples/data_analysis_server.py`

Demonstrates:
- Complex data processing
- Multiple tools working together
- Resource caching
- Progress reporting for long operations

**Run**: `simply-mcp run examples/data_analysis_server.py`

### File Processor Server
Complete file processing server.

**File**: `examples/file_processor_server.py`

Demonstrates:
- File I/O operations
- Directory traversal
- File metadata resources
- Batch processing

**Run**: `simply-mcp run examples/file_processor_server.py`

## API Style Examples

### Decorator API

```python
from simply_mcp import mcp_server, tool

@mcp_server(name="decorator-example")
class DecoratorServer:
    @tool(description="Example tool")
    def example(self, param: str) -> str:
        return f"Hello {param}"
```

### Functional API

```python
from simply_mcp import BuildMCPServer

mcp = BuildMCPServer(name="functional-example")

@mcp.add_tool(description="Example tool")
def example(param: str) -> str:
    return f"Hello {param}"
```

## Running Examples

All examples are in the `examples/` directory of the repository.

### Clone Repository

```bash
git clone https://github.com/Clockwork-Innovations/simply-mcp-py.git
cd simply-mcp-py
```

### Install Dependencies

```bash
pip install -e .
```

### Run an Example

```bash
simply-mcp run examples/simple_server.py
```

## Example Structure

Each example includes:

- **Source code** with comprehensive comments
- **README section** explaining the example
- **Configuration** showing best practices
- **Usage instructions** for running the example

## Example Categories

### By Difficulty

- **Beginner**: simple_server.py, decorator_example.py
- **Intermediate**: http_server.py, progress_example.py
- **Advanced**: authenticated_server.py, production_server.py

### By Feature

- **Tools**: decorator_example.py, simple_server.py
- **Resources**: binary_resources_example.py
- **Prompts**: decorator_example.py
- **Progress**: progress_example.py
- **Security**: authenticated_server.py, rate_limited_server.py
- **Transports**: http_server.py

### By Use Case

- **Web Services**: http_server.py
- **File Processing**: file_processor_server.py
- **Data Analysis**: data_analysis_server.py
- **Development**: dev_example.py, watch_example.py

## Contributing Examples

We welcome example contributions! To submit an example:

1. Create a well-documented Python file
2. Add comprehensive comments
3. Include a README section
4. Test thoroughly
5. Submit a PR

See our [Contributing Guide](https://github.com/Clockwork-Innovations/simply-mcp-py/blob/main/CONTRIBUTING.md).

## Next Steps

- [API Reference](../api/decorators.md) - Learn the APIs used in examples
- [Configuration Guide](../guide/configuration.md) - Configure your servers
- [Testing Guide](../guide/testing.md) - Test your servers
- [Deployment Guide](../guide/deployment.md) - Deploy to production
