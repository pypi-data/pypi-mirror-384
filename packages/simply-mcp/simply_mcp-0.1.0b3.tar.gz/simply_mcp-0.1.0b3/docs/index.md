# Simply-MCP-PY Documentation

> A modern, Pythonic framework for building Model Context Protocol (MCP) servers with multiple API styles

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](https://github.com/Clockwork-Innovations/simply-mcp-py/blob/main/LICENSE)
[![Version](https://img.shields.io/badge/version-0.1.0b1-orange.svg)]()
[![Status](https://img.shields.io/badge/status-beta-yellow.svg)]()

Welcome to Simply-MCP-PY, the Python implementation of [simply-mcp-ts](https://github.com/Clockwork-Innovations/simply-mcp-ts). This framework brings ease-of-use and flexibility to building Model Context Protocol servers in Python, with a focus on developer experience and productivity.

**Current Status:** Beta v0.1.0b1 - Internal testing phase. Core features are stable and functional.

---

## Quick Start

### Installation

**Option 1: Try without installing (uvx)**
```bash
# Install uvx
pip install uv

# Run commands directly from PyPI
uvx simply-mcp --version
```

**Option 2: Install permanently (pip)**
```bash
pip install simply-mcp
```

[Full Installation Guide →](getting-started/installation.md)

### Your First Server in 10 Lines

```python
from simply_mcp import mcp_server, tool

@mcp_server(name="my-server", version="1.0.0")
class MyServer:
    @tool()
    def add(self, a: int, b: int) -> int:
        """Add two numbers together."""
        return a + b
```

### Run It

```bash
# With pip install
simply-mcp run server.py

# Or with uvx (no install needed)
uvx simply-mcp run server.py
```

That's it! You now have a working MCP server. [Continue to Full Quickstart →](getting-started/quickstart.md)

---

## What is Simply-MCP-PY?

Simply-MCP-PY is a high-level framework built on top of the [Anthropic MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) that makes building MCP servers intuitive and productive. It provides:

- **Multiple API styles** to match your coding preferences
- **Zero configuration** with automatic schema generation
- **Full type safety** with mypy support
- **Production-ready features** including auth, rate limiting, and progress reporting
- **Powerful CLI** for development, testing, and deployment

---

## Key Features

### Multiple API Styles

Choose the approach that fits your workflow:

- **Decorator API** - Clean, declarative class-based approach (Recommended)
- **Builder/Functional API** - Programmatic server construction with method chaining
- **Interface API** - Pure type-annotated interfaces (Coming soon)

[Learn More About API Styles →](guide/api-styles.md)

### Multiple Transports

Run your server anywhere:

- **stdio** - Standard I/O for Claude Desktop integration
- **HTTP** - RESTful server with JSON-RPC endpoints
- **SSE** - Server-Sent Events for real-time streaming

### Developer Experience

Built for productivity:

- Hot reload with watch mode
- Interactive development mode with live metrics
- Component inspection and validation
- Bundle to standalone executables
- Comprehensive error messages

### Production Ready

Enterprise-grade features:

- API key authentication
- Token bucket rate limiting
- Progress reporting for long operations
- Binary content support
- Structured JSON logging
- Health checks and metrics

---

## Documentation Navigation

### Getting Started

Perfect for new users - get up and running in minutes:

- [**Installation Guide**](getting-started/installation.md) - Detailed installation instructions for all platforms
- [**Quickstart Tutorial**](getting-started/quickstart.md) - 5-minute walkthrough to build your first server
- [**First Server Guide**](getting-started/first-server.md) - Step-by-step guide with explanations

**Start here if you're new!** → [Installation](getting-started/installation.md)

### User Guides

In-depth guides for building and deploying servers:

#### Core Guides
- [**API Styles Comparison**](guide/api-styles.md) - Choosing between Decorator and Builder APIs
- [**CLI Usage Guide**](guide/cli-usage.md) - Complete reference for the `simply-mcp` command
- [**Configuration Guide**](guide/configuration.md) - Configure your server with TOML or environment variables
- [**Testing Guide**](guide/testing.md) - Test your MCP servers effectively
- [**Deployment Guide**](guide/deployment.md) - Deploy to production with best practices

#### Troubleshooting
- [**Troubleshooting Guide**](guide/troubleshooting.md) - Solutions to common issues and debugging techniques

### API Reference

Complete technical documentation:

#### Core Components
- [**Server API**](api/core/server.md) - Core server implementation
- [**Types**](api/core/types.md) - Type definitions and schemas
- [**Configuration**](api/core/config.md) - Configuration options
- [**Registry**](api/core/registry.md) - Component registration system
- [**Errors**](api/core/errors.md) - Error handling and custom exceptions
- [**Logger**](api/core/logger.md) - Logging system

#### APIs
- [**Decorators**](api/decorators.md) - `@tool`, `@prompt`, `@resource`, `@mcp_server`
- [**Builder**](api/builder.md) - `SimplyMCP` class and builder pattern

#### Transports
- [**HTTP Transport**](api/transports/http.md) - HTTP server implementation
- [**SSE Transport**](api/transports/sse.md) - Server-Sent Events
- [**Stdio Transport**](api/transports/stdio.md) - Standard I/O transport
- [**Middleware**](api/transports/middleware.md) - Request/response middleware
- [**Factory**](api/transports/factory.md) - Transport factory pattern

#### Features
- [**Progress Reporting**](api/features/progress.md) - Long-running operation progress
- [**Binary Content**](api/features/binary.md) - Handle images, PDFs, and binary data

#### Security
- [**Authentication**](api/security/auth.md) - API key and token authentication
- [**Rate Limiting**](api/security/rate_limiter.md) - Token bucket rate limiting

#### CLI
- [**CLI Main**](api/cli/main.md) - CLI entry point
- [**Run Command**](api/cli/run.md) - Production server execution
- [**Config Command**](api/cli/config.md) - Configuration management
- [**Dev Command**](api/cli/dev.md) - Development mode
- [**Watch Command**](api/cli/watch.md) - File watching
- [**Bundle Command**](api/cli/bundle.md) - Executable bundling
- [**List Command**](api/cli/list_cmd.md) - Component inspection

#### Validation
- [**Schema Generation**](api/validation/schema.md) - Automatic JSON Schema generation

### Examples

17 working examples demonstrating all features:

[**Browse All Examples →**](examples/index.md)

**Featured Examples:**
- `simple_server.py` - Minimal working example
- `decorator_example.py` - Comprehensive decorator API showcase
- `http_server.py` - HTTP transport with REST endpoints
- `production_server.py` - Production-ready server with all best practices
- `data_analysis_server.py` - Real-world data processing example
- `authenticated_server.py` - API key authentication
- `rate_limited_server.py` - Rate limiting implementation
- `progress_example.py` - Progress reporting for long operations

---

## Common Tasks

### "I want to..."

**Create my first server**
→ [Quickstart Tutorial](getting-started/quickstart.md) | [First Server Guide](getting-started/first-server.md)

**Choose an API style**
→ [API Styles Comparison](guide/api-styles.md)

**Use the CLI effectively**
→ [CLI Usage Guide](guide/cli-usage.md)

**Configure my server**
→ [Configuration Guide](guide/configuration.md)

**Fix a problem**
→ [Troubleshooting Guide](guide/troubleshooting.md)

**Test my server**
→ [Testing Guide](guide/testing.md)

**Deploy to production**
→ [Deployment Guide](guide/deployment.md)

**See working examples**
→ [Examples Directory](examples/index.md)

**Add authentication**
→ [Authentication API](api/security/auth.md) | [Authenticated Server Example](examples/index.md#authentication)

**Report progress for long operations**
→ [Progress API](api/features/progress.md) | [Progress Example](examples/index.md#progress-reporting)

**Handle binary files**
→ [Binary Content API](api/features/binary.md) | [Binary Resources Example](examples/index.md#binary-resources)

**Use HTTP instead of stdio**
→ [HTTP Transport API](api/transports/http.md) | [HTTP Server Example](examples/index.md#http-server)

**Bundle to an executable**
→ [Bundle Command](api/cli/bundle.md)

---

## Feature Highlights

### Zero Configuration

Get started with sensible defaults:

```python
from simply_mcp import tool

@tool()
def greet(name: str) -> str:
    """Generate a greeting."""
    return f"Hello, {name}!"
```

No configuration needed! Simply-MCP automatically:
- Detects API style
- Generates JSON Schema from type hints
- Sets up stdio transport
- Configures logging

[Learn More →](getting-started/quickstart.md)

### Type Safety

Full mypy support with automatic schema generation:

```python
from pydantic import BaseModel, Field

class UserInput(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    age: int = Field(ge=0, le=150)
    email: str

@tool()
def create_user(user: UserInput) -> dict:
    """Create a user with validated input."""
    return user.model_dump()
```

[Learn More →](api/validation/schema.md)

### Development Mode

Rapid iteration with auto-reload and debugging:

```bash
# Start dev server with hot reload
simply-mcp dev server.py

# Interactive controls:
# - Press 'r' to reload
# - Press 'l' to list components
# - Press 'm' for metrics
# - Press 'q' to quit
```

[Learn More →](guide/cli-usage.md#dev-command)

### Progress Reporting

Keep users informed during long operations:

```python
from simply_mcp import tool, Progress

@tool()
async def process_data(items: list, progress: Progress) -> dict:
    """Process items with progress updates."""
    total = len(items)
    for i, item in enumerate(items):
        await progress.update(
            percentage=(i / total) * 100,
            message=f"Processing {i+1}/{total}"
        )
        # Process item...
    return {"processed": total}
```

[Learn More →](api/features/progress.md)

### Multiple Transports

Run your server anywhere:

```bash
# Claude Desktop integration (stdio)
simply-mcp run server.py

# Web server (HTTP)
simply-mcp run server.py --transport http --port 3000

# Real-time streaming (SSE)
simply-mcp run server.py --transport sse --port 3000
```

[Learn More →](guide/cli-usage.md#transport-options)

### Production Features

Enterprise-ready capabilities:

```toml
# simplymcp.config.toml
[server]
name = "production-server"
version = "1.0.0"

[auth]
enabled = true
type = "api_key"
api_keys = ["your-secret-key"]

[rate_limit]
enabled = true
requests_per_minute = 60
burst_size = 10

[logging]
level = "INFO"
format = "json"
```

[Learn More →](guide/configuration.md)

---

## Platform Support

Simply-MCP-PY works on all major platforms:

- **Linux** - Full support, all features
- **macOS** - Full support, all features
- **Windows** - Full support (tested and verified as of v0.1.0b1)

**Requirements:**
- Python 3.10 or higher
- pip for package management

---

## Examples Gallery

### Simple Server (Beginner)

```python
from simply_mcp import mcp_server, tool

@mcp_server(name="calculator", version="1.0.0")
class Calculator:
    @tool()
    def add(self, a: int, b: int) -> int:
        """Add two numbers."""
        return a + b

    @tool()
    def multiply(self, a: float, b: float) -> float:
        """Multiply two numbers."""
        return a * b
```

[View Full Example →](examples/index.md)

### HTTP Server (Intermediate)

```python
from simply_mcp import mcp_server, tool

@mcp_server(name="http-demo", version="1.0.0")
class HTTPDemo:
    @tool()
    def status(self) -> dict:
        """Get server status."""
        return {"status": "running", "transport": "http"}
```

Run with:
```bash
simply-mcp run server.py --transport http --port 3000
```

[View Full Example →](examples/index.md#http-server)

### Production Server (Advanced)

Complete production-ready server with:
- Environment-based configuration
- Structured JSON logging
- Error handling and validation
- Health checks
- Graceful shutdown
- Rate limiting and authentication

[View Full Example →](examples/index.md#production-server)

---

## CLI Overview

The `simply-mcp` CLI provides everything you need:

```bash
# Development with auto-reload
simply-mcp dev server.py

# Production execution
simply-mcp run server.py --transport http --port 3000

# Inspect components
simply-mcp list server.py --json

# Watch and reload on changes
simply-mcp watch server.py

# Bundle to executable
simply-mcp bundle server.py --output dist/

# Configuration management
simply-mcp config init
simply-mcp config validate
```

[Complete CLI Reference →](guide/cli-usage.md)

---

## Additional Resources

### GitHub Repository
[github.com/Clockwork-Innovations/simply-mcp-py](https://github.com/Clockwork-Innovations/simply-mcp-py)

### Examples Directory
[Browse 17 working examples](https://github.com/Clockwork-Innovations/simply-mcp-py/tree/main/examples)

### Issue Tracker
[Report bugs and request features](https://github.com/Clockwork-Innovations/simply-mcp-py/issues)

### Discussions
[Ask questions and share ideas](https://github.com/Clockwork-Innovations/simply-mcp-py/discussions)

### Related Projects
- [simply-mcp-ts](https://github.com/Clockwork-Innovations/simply-mcp-ts) - TypeScript version
- [Anthropic MCP SDK](https://github.com/modelcontextprotocol/python-sdk) - Official Python MCP SDK
- [Model Context Protocol](https://modelcontextprotocol.io) - Protocol specification

---

## Project Status

**Current Version:** 0.1.0b1 (Beta)

**Status:** Internal testing phase. Core features are implemented and stable:

- ✅ Decorator API (`@tool`, `@prompt`, `@resource`, `@mcp_server`)
- ✅ Builder/Functional API (`SimplyMCP`)
- ✅ Multiple transports (stdio, HTTP, SSE)
- ✅ CLI with dev mode, watch mode, bundling
- ✅ Authentication and rate limiting
- ✅ Progress reporting
- ✅ Binary content support
- ✅ Comprehensive documentation
- ✅ 17 working examples
- ✅ Cross-platform support (Linux, macOS, Windows)

**Coming Soon:**
- Interface API (pure type-annotated interfaces)
- Builder API (AI-powered tool development)
- Public beta release

[View Full Roadmap →](ROADMAP.md)

---

## Requirements

- **Python:** 3.10 or higher
- **Package Manager:** pip or poetry
- **Optional Dependencies:**
  - `pyinstaller` - For bundling executables
  - `pytest` - For running tests
  - `mypy` - For type checking

---

## Community and Support

We're here to help! Choose the best channel for your needs:

- **Documentation:** You're reading it! Browse the guides above
- **Examples:** Check the [examples directory](examples/index.md) for working code
- **Issues:** [Report bugs](https://github.com/Clockwork-Innovations/simply-mcp-py/issues) or request features
- **Discussions:** [Ask questions](https://github.com/Clockwork-Innovations/simply-mcp-py/discussions) and share ideas
- **Troubleshooting:** [Common problems and solutions](guide/troubleshooting.md)

---

## License

Simply-MCP-PY is open source software licensed under the MIT License.

See the [LICENSE](https://github.com/Clockwork-Innovations/simply-mcp-py/blob/main/LICENSE) file for details.

---

## Acknowledgments

Built with care by [Clockwork Innovations](https://clockwork-innovations.com)

- Based on the [Anthropic MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- Inspired by [simply-mcp-ts](https://github.com/Clockwork-Innovations/simply-mcp-ts)
- Community contributions welcome!

---

## Next Steps

Ready to get started? Here's what to do:

1. **[Install Simply-MCP →](getting-started/installation.md)**
2. **[Follow the Quickstart →](getting-started/quickstart.md)**
3. **[Build Your First Server →](getting-started/first-server.md)**
4. **[Explore Examples →](examples/index.md)**
5. **[Read the Guides →](#user-guides)**

Happy building! 🚀
