# Quick Start

Get up and running with Simply-MCP-PY in 5 minutes.

## Prerequisites

You can use Simply-MCP-PY in two ways:

**Option 1: Try without installing (uvx)**
```bash
# Install uvx if you don't have it
pip install uv

# No further installation needed!
```

**Option 2: Install permanently (pip)**
```bash
pip install simply-mcp
```

See the [Installation Guide](installation.md) for detailed instructions.

## Your First Server

Let's create a simple MCP server with two tools using the Decorator API.

### Step 1: Create a Server File

Create a new file called `server.py`:

```python
from simply_mcp import mcp_server, tool

@mcp_server(name="hello-server", version="1.0.0")
class HelloServer:
    @tool(description="Add two numbers")
    def add(self, a: int, b: int) -> int:
        """Add two numbers together."""
        return a + b

    @tool(description="Greet a user")
    def greet(self, name: str, formal: bool = False) -> str:
        """Generate a personalized greeting."""
        if formal:
            return f"Good day, {name}."
        return f"Hey {name}!"
```

### Step 2: Run Your Server

Run the server using the CLI:

**With pip install:**
```bash
simply-mcp run server.py
```

**With uvx (no installation):**
```bash
uvx simply-mcp run server.py
```

**Note:** First `uvx` run takes ~7-30 seconds to download packages. Subsequent runs are near-instant.

You should see output indicating the server is running:

```
Starting MCP server: hello-server v1.0.0
Transport: stdio
Registered 2 tools
Server ready and listening...
```

### Step 3: Test Your Server

The server is now running and waiting for MCP protocol messages on stdin/stdout. You can connect to it using any MCP client (like Claude Desktop).

## Different Transports

### HTTP Server

Run your server over HTTP:

```bash
simply-mcp run server.py --transport http --port 3000
```

Visit `http://localhost:3000` to see your server running.

### SSE (Server-Sent Events)

For real-time streaming:

```bash
simply-mcp run server.py --transport sse --port 3000
```

## Development Mode

Enable auto-reload when you change your code:

```bash
simply-mcp run server.py --watch
```

Now any changes to `server.py` will automatically reload the server.

## Try the Functional API

If you prefer a functional approach, here's the same server using the Functional API:

```python
from simply_mcp import BuildMCPServer

mcp = BuildMCPServer(name="hello-server", version="1.0.0")

@mcp.add_tool(description="Add two numbers")
def add(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b

@mcp.add_tool(description="Greet a user")
def greet(name: str, formal: bool = False) -> str:
    """Generate a personalized greeting."""
    if formal:
        return f"Good day, {name}."
    return f"Hey {name}!"
```

Run it the same way:

```bash
simply-mcp run server.py
```

## Adding Resources

Resources provide read-only data. Let's add a configuration resource:

```python
from simply_mcp import mcp_server, tool, resource

@mcp_server(name="hello-server", version="1.0.0")
class HelloServer:
    @tool(description="Add two numbers")
    def add(self, a: int, b: int) -> int:
        return a + b

    @resource(uri="config://server", mime_type="application/json")
    def server_config(self) -> dict:
        """Get server configuration."""
        return {
            "name": "hello-server",
            "version": "1.0.0",
            "status": "running"
        }
```

## Adding Prompts

Prompts are reusable templates. Let's add a code review prompt:

```python
from simply_mcp import mcp_server, tool, prompt

@mcp_server(name="hello-server", version="1.0.0")
class HelloServer:
    @tool(description="Add two numbers")
    def add(self, a: int, b: int) -> int:
        return a + b

    @prompt(description="Generate a code review template")
    def code_review(self, language: str = "python") -> str:
        """Generate a code review prompt for the specified language."""
        return f"""Please review this {language} code for:
- Code quality and best practices
- Potential bugs or issues
- Performance considerations
- Security vulnerabilities
- Documentation completeness
"""
```

## List Available Components

To see all registered tools, resources, and prompts:

**With pip install:**
```bash
simply-mcp list server.py
```

**With uvx:**
```bash
uvx simply-mcp list server.py
```

Output:

```
                         MCP Server Components
┏━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Type     ┃ Name                   ┃ Description                     ┃
┡━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Tool     │ add                    │ Add two numbers                 │
│ Tool     │ greet                  │ Greet a user                    │
│ Prompt   │ code_review (language) │ Generate a code review template │
│ Resource │ server_config          │ Server configuration            │
└──────────┴────────────────────────┴─────────────────────────────────┘

Total: 4 component(s)
```

## Configuration

Create a `simplymcp.config.toml` file for persistent configuration:

```toml
[server]
name = "hello-server"
version = "1.0.0"

[transport]
type = "http"
port = 3000

[logging]
level = "INFO"
format = "json"
```

Now run without flags:

```bash
simply-mcp run server.py
```

The server will use settings from the config file.

## Next Steps

Now that you have a basic server running, explore more:

- [First Server Tutorial](first-server.md) - Build a more complete server
- [API Reference](../api/decorators.md) - Learn about all available decorators
- [Examples](../examples/index.md) - See real-world examples
- [Configuration Guide](../guide/configuration.md) - Advanced configuration options
- [Deployment Guide](../guide/deployment.md) - Deploy to production

## Common Commands

```bash
# Run server
simply-mcp run server.py

# Run with HTTP
simply-mcp run server.py --transport http --port 3000

# Run with auto-reload
simply-mcp run server.py --watch

# List components
simply-mcp list server.py

# Create config file
simply-mcp config init

# Bundle to executable
simply-mcp bundle server.py --output dist/
```

## Troubleshooting

### Server Won't Start

Make sure you have Python 3.10+ and all dependencies installed:

```bash
python --version
pip list | grep simply-mcp
```

### Import Errors

Ensure Simply-MCP-PY is installed:

```bash
pip install --upgrade simply-mcp
```

### Port Already in Use

Change the port:

```bash
simply-mcp run server.py --transport http --port 3001
```

For more help, visit our [Issue Tracker](https://github.com/Clockwork-Innovations/simply-mcp-py/issues).
