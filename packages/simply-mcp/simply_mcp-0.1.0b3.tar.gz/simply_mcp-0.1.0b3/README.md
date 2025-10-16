# Simply-MCP-PY

> A modern, Pythonic framework for building Model Context Protocol (MCP) servers with multiple API styles

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-alpha-orange.svg)]()

Simply-MCP-PY is the Python implementation of [simply-mcp-ts](https://github.com/Clockwork-Innovations/simply-mcp-ts), bringing the same ease-of-use and flexibility to the Python ecosystem for building MCP servers.

## Features

- **Multiple API Styles** - Choose the style that fits your workflow:
  - 🎨 **Decorator API** - Clean, declarative class-based approach
  - 🔧 **Functional API** - Programmatic server building with method chaining
  - 📝 **Interface API** - Pure type-annotated interfaces (coming soon)
  - 🤖 **Builder API** - AI-powered tool development (future)

- **Multiple Transports** - Run your server anywhere:
  - 📟 **Stdio** - Standard input/output (default)
  - 🌐 **HTTP** - RESTful HTTP server with session support
  - 📡 **SSE** - Server-Sent Events for real-time streaming

- **Zero Configuration** - Get started instantly:
  - Auto-detect API style
  - Automatic schema generation from type hints
  - Sensible defaults for everything
  - Optional configuration for advanced use cases

- **Developer Experience**:
  - 🔥 Hot reload with watch mode
  - 📦 Bundle to standalone executable
  - 🎯 Type-safe with full mypy support
  - 📚 Comprehensive documentation

- **Production Ready**:
  - 🔒 Rate limiting and authentication
  - ⚡ Progress reporting for long operations
  - 📊 Binary content support
  - 🛡️ Security best practices

## Quick Start

### Installation

**Option 1: Try without installing (uvx)**
```bash
# Install uvx
pip install uv

# Run directly without installing simply-mcp
uvx simply-mcp --version
uvx simply-mcp run server.py
```

**Option 2: Install permanently (pip)**
```bash
pip install simply-mcp
```

### Your First Server (Decorator API)

```python
# server.py
from simply_mcp import mcp_server, tool

@mcp_server(name="my-server", version="1.0.0")
class MyServer:
    @tool(description="Add two numbers")
    def add(self, a: int, b: int) -> int:
        """Add two numbers together."""
        return a + b

    @tool(description="Greet a user")
    def greet(self, name: str, formal: bool = False) -> str:
        """Generate a greeting."""
        if formal:
            return f"Good day, {name}."
        return f"Hey {name}!"
```

### Run Your Server

```bash
# Run with stdio (default)
simply-mcp run server.py

# Run with HTTP on port 3000
simply-mcp run server.py --transport http --port 3000

# Run with auto-reload
simply-mcp run server.py --watch
```

**Note:** If using uvx, prefix commands with `uvx`: `uvx simply-mcp run server.py`. First run takes ~7-30 seconds to download packages, subsequent runs are near-instant.

## API Styles

### Decorator API (Recommended)

Clean, declarative class-based approach:

```python
from simply_mcp import mcp_server, tool, prompt, resource

@mcp_server(name="my-server", version="1.0.0")
class MyServer:
    @tool(description="Calculate sum")
    def add(self, a: int, b: int) -> int:
        return a + b

    @prompt(description="Generate code review")
    def code_review(self, language: str) -> str:
        return f"Please review this {language} code..."

    @resource(uri="config://server", mime_type="application/json")
    def get_config(self) -> dict:
        return {"status": "running", "version": "1.0.0"}
```

### Functional API

Programmatic server building:

```python
from simply_mcp import BuildMCPServer

mcp = BuildMCPServer(name="my-server", version="1.0.0")

@mcp.add_tool(description="Add two numbers")
def add(a: int, b: int) -> int:
    return a + b

@mcp.add_prompt(description="Generate greeting")
def greet(name: str) -> str:
    return f"Hello, {name}!"

# Method chaining
mcp.configure(port=3000).run()
```

## Configuration

Create a `simplymcp.config.toml` file:

```toml
[server]
name = "my-mcp-server"
version = "1.0.0"

[transport]
type = "http"  # or "stdio", "sse"
port = 3000

[logging]
level = "INFO"
format = "json"

[security]
enable_rate_limiting = true
rate_limit_per_minute = 60
```

Or use environment variables:

```bash
export SIMPLY_MCP_TRANSPORT=http
export SIMPLY_MCP_PORT=3000
export SIMPLY_MCP_LOG_LEVEL=DEBUG
```

## Advanced Features

### Progress Reporting

```python
from simply_mcp import tool, Progress

@tool(description="Process large dataset")
async def process_data(data: list, progress: Progress) -> dict:
    total = len(data)
    for i, item in enumerate(data):
        await progress.update(
            percentage=(i / total) * 100,
            message=f"Processing item {i+1}/{total}"
        )
        # Process item...
    return {"processed": total}
```

### Authentication

```python
# simplymcp.config.toml
[security.auth]
enabled = true
type = "api_key"
api_keys = ["your-secret-key"]
```

### Binary Content

```python
@resource(uri="file://document.pdf", mime_type="application/pdf")
def get_document(self) -> bytes:
    with open("document.pdf", "rb") as f:
        return f.read()
```

## CLI Commands

```bash
# Run a server
simply-mcp run server.py [--transport TYPE] [--port PORT] [--watch]

# Bundle to executable
simply-mcp bundle server.py --output dist/

# List available servers
simply-mcp list [--json]

# Configuration management
simply-mcp config init          # Create config file
simply-mcp config validate      # Validate config
simply-mcp config show          # Show current config
```

## Examples

Check out the `examples/` directory:

- `simple_server.py` - Minimal working example
- `decorator_basic.py` - Decorator API basics
- `functional_api.py` - Functional API usage
- `http_server.py` - HTTP transport example
- `advanced_features.py` - Progress, auth, binary content

## Documentation

- [Technical Specification](docs/TECHNICAL_SPEC.md) - Detailed technical specs
- [Architecture](docs/ARCHITECTURE.md) - System architecture
- [Implementation Roadmap](docs/ROADMAP.md) - Development plan
- [API Reference](https://simply-mcp-py.readthedocs.io) - Complete API docs
- [Migration Guide](docs/migration-from-typescript.md) - Coming from simply-mcp-ts?

## Comparison with simply-mcp-ts

| Feature | simply-mcp-ts | simply-mcp-py |
|---------|--------------|---------------|
| Decorator API | ✅ | ✅ |
| Functional API | ✅ | ✅ |
| Interface API | ✅ | 🚧 (planned) |
| Builder API | ✅ | 🚧 (future) |
| Stdio Transport | ✅ | ✅ |
| HTTP Transport | ✅ | ✅ |
| SSE Transport | ✅ | ✅ |
| Watch Mode | ✅ | ✅ |
| Bundling | ✅ | ✅ |
| Schema Validation | Zod | Pydantic |
| Type System | TypeScript | Python + mypy |

## Development Status

🚧 **Currently in Alpha** - Core features are implemented and functional, but the API may change. See [ROADMAP.md](docs/ROADMAP.md) for development progress.

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Requirements

- Python 3.10 or higher
- Dependencies managed via pip

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Related Projects

- [simply-mcp-ts](https://github.com/Clockwork-Innovations/simply-mcp-ts) - TypeScript version
- [Anthropic MCP SDK](https://github.com/modelcontextprotocol/python-sdk) - Official Python MCP SDK
- [Model Context Protocol](https://modelcontextprotocol.io) - Protocol specification

## Acknowledgments

- Built on top of the [Anthropic MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- Inspired by [simply-mcp-ts](https://github.com/Clockwork-Innovations/simply-mcp-ts)
- Created by [Clockwork Innovations](https://clockwork-innovations.com)

## Support

- 📖 [Documentation](https://simply-mcp-py.readthedocs.io)
- 🐛 [Issue Tracker](https://github.com/Clockwork-Innovations/simply-mcp-py/issues)
- 💬 [Discussions](https://github.com/Clockwork-Innovations/simply-mcp-py/discussions)

---

**Made with ❤️ by Clockwork Innovations**
