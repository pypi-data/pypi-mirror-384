# CLI Usage Guide

A comprehensive reference for the `simply-mcp` command-line interface.

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Command Reference](#command-reference)
  - [run](#run-command)
  - [dev](#dev-command)
  - [watch](#watch-command)
  - [list](#list-command)
  - [bundle](#bundle-command)
  - [config](#config-command)
- [Transport Options](#transport-options)
- [Workflow Examples](#workflow-examples)
- [Tips and Best Practices](#tips-and-best-practices)
- [Troubleshooting](#troubleshooting)

## Overview

The `simply-mcp` CLI provides a complete toolkit for developing, testing, and deploying MCP servers. It supports multiple commands for different stages of development:

- **run** - Run an MCP server in production mode
- **dev** - Run with enhanced development features (auto-reload, debug logging, interactive controls)
- **watch** - Monitor files and auto-reload on changes
- **list** - Inspect server components (tools, prompts, resources)
- **bundle** - Package servers into standalone executables
- **config** - Manage server configuration files

## Trying Without Installation

Want to use the CLI without installing Simply-MCP? Use **uvx** to run commands directly from PyPI.

### What is uvx?

[uvx](https://github.com/astral-sh/uv) runs Python packages instantly without installation. It downloads and caches the package on first use, then executes it immediately.

### Installing uvx

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# With pip
pip install uv
```

### Using Simply-MCP with uvx

All CLI commands work with uvx - just prefix with `uvx`:

```bash
# Check version
uvx simply-mcp --version

# Run a server
uvx simply-mcp run server.py

# Development mode
uvx simply-mcp dev server.py

# List components
uvx simply-mcp list server.py

# Watch mode
uvx simply-mcp watch server.py
```

**Performance:**
- **First run:** ~7-30 seconds (downloads packages)
- **Subsequent runs:** Near-instant (uses cache)

### When to Use Each Approach

**Use uvx if you:**
- Want to try Simply-MCP before installing
- Need to run one-off commands
- Prefer not to install packages globally
- Don't need to import Simply-MCP in your code

**Use pip install if you:**
- Develop MCP servers regularly
- Need to import Simply-MCP modules
- Want the fastest possible execution
- Are building production servers

### Comparison Table

| Feature | uvx simply-mcp | pip install simply-mcp |
|---------|----------------|------------------------|
| Installation required | No | Yes |
| First run | 7-30 seconds | Instant |
| Subsequent runs | Near-instant | Instant |
| Import in Python | No | Yes |
| Virtual environment | Not needed | Recommended |
| Best for | Testing/one-off | Development/production |

## Installation for Development

To use Simply-MCP in your Python code or for regular development, install it with pip:

```bash
# Basic installation
pip install simply-mcp

# With all optional features
pip install simply-mcp[http,bundling]
```

Verify installation:

```bash
simply-mcp --version
```

## Quick Start

Create a simple server file and run it:

```python
# server.py
from simply_mcp import tool

@tool()
def add(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b
```

Run the server:

```bash
# Development mode with auto-reload
simply-mcp dev server.py

# Production mode
simply-mcp run server.py

# List components
simply-mcp list server.py
```

---

## Command Reference

### run Command

Run an MCP server in production mode with the specified transport.

#### Syntax

```bash
simply-mcp run SERVER_FILE [OPTIONS]
```

#### Arguments

| Argument | Description |
|----------|-------------|
| `SERVER_FILE` | Path to Python file containing MCP server (required) |

#### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--transport` | choice | `stdio` | Transport type: `stdio`, `http`, or `sse` |
| `--port` | int | `3000` | Port for network transports |
| `--host` | str | `0.0.0.0` | Host for network transports |
| `--cors/--no-cors` | flag | enabled | Enable/disable CORS for network transports |
| `--config` | path | None | Path to configuration file |
| `--watch` | flag | disabled | Enable auto-reload (planned for Phase 4) |

#### Examples

**Run with stdio transport (default)**

Default transport for MCP clients like Claude Desktop:

```bash
simply-mcp run examples/simple_server.py
```

**Run with HTTP transport**

Expose server via HTTP with JSON-RPC endpoint:

```bash
simply-mcp run examples/http_server.py --transport http --port 8080
```

**Run with SSE transport**

Use Server-Sent Events for real-time streaming:

```bash
simply-mcp run examples/sse_server.py --transport sse --port 8080
```

**Run with custom host and CORS disabled**

Restrict to localhost and disable CORS:

```bash
simply-mcp run examples/http_server.py --transport http --host localhost --no-cors
```

**Run with custom configuration file**

Use a custom TOML configuration:

```bash
simply-mcp run examples/production_server.py --config myconfig.toml
```

**Override config port**

Configuration file port can be overridden:

```bash
simply-mcp run server.py --config config.toml --port 9000
```

#### Output

The run command displays:
- Server startup information
- Detected API style (decorator, builder, or class-based)
- Component counts (tools, prompts, resources)
- Server endpoints (for HTTP/SSE)
- Running status

#### Notes

- Automatically detects API style from server file
- Supports decorator, builder, and class-based APIs
- Graceful shutdown on Ctrl+C
- stdio transport is recommended for Claude Desktop integration
- HTTP/SSE transports are useful for web applications and testing

---

### dev Command

Run an MCP server in development mode with enhanced features for rapid development.

#### Syntax

```bash
simply-mcp dev SERVER_FILE [OPTIONS]
```

#### Arguments

| Argument | Description |
|----------|-------------|
| `SERVER_FILE` | Path to Python file containing MCP server (required) |

#### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--transport` | choice | `stdio` | Transport type: `stdio`, `http`, or `sse` |
| `--port` | int | `3000` | Port for network transports |
| `--host` | str | `0.0.0.0` | Host for network transports |
| `--no-reload` | flag | disabled | Disable auto-reload on file changes |
| `--no-color` | flag | disabled | Disable colored output |
| `--log-requests/--no-log-requests` | flag | enabled | Log all requests/responses |

#### Features

Development mode provides:
- **Auto-reload** - Automatically restarts server when files change
- **Debug logging** - DEBUG level logs enabled by default
- **Interactive controls** - Keyboard shortcuts for common actions
- **Component listing** - Shows registered tools/prompts/resources on startup
- **Performance metrics** - Track uptime, request counts, and errors
- **Pretty output** - Rich terminal formatting with colors

#### Keyboard Shortcuts

When running in dev mode (Unix-like systems only):

| Key | Action |
|-----|--------|
| `r` | Reload server manually |
| `l` | List registered components |
| `m` | Show performance metrics |
| `q` | Quit dev server |

> **Note:** Keyboard shortcuts are only available on Unix-like systems (Linux, macOS) with TTY support.

#### Examples

**Start dev server with defaults**

Auto-reload enabled, stdio transport:

```bash
simply-mcp dev examples/decorator_example.py
```

**Dev mode with HTTP transport**

Develop with HTTP transport on custom port:

```bash
simply-mcp dev examples/http_server.py --transport http --port 8080
```

**Dev mode without auto-reload**

Disable file watching:

```bash
simply-mcp dev examples/simple_server.py --no-reload
```

**Dev mode with SSE transport**

Test SSE streaming in development:

```bash
simply-mcp dev examples/sse_server.py --transport sse --port 8080
```

**Disable request logging**

Reduce console noise by disabling request logs:

```bash
simply-mcp dev server.py --no-log-requests
```

**Development without colors**

For CI/CD or piping to files:

```bash
simply-mcp dev server.py --no-color > output.log
```

#### Output

The dev command displays:
- Welcome banner with server info
- Component listing on startup
- File change notifications
- Reload progress
- Request/response logs (if enabled)
- Interactive prompts for keyboard shortcuts

#### Notes

- Auto-reload watches all `.py` files in the current directory
- Ignores common directories (`.git`, `__pycache__`, `.venv`, etc.)
- CORS always enabled in dev mode for HTTP/SSE
- Sets `SIMPLY_MCP_LOG_LEVEL=DEBUG` environment variable
- Perfect for rapid iteration during development

---

### watch Command

Watch for file changes and automatically reload the MCP server.

#### Syntax

```bash
simply-mcp watch SERVER_FILE [OPTIONS]
```

#### Arguments

| Argument | Description |
|----------|-------------|
| `SERVER_FILE` | Path to Python file containing MCP server (required) |

#### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--ignore`, `-i` | str | None | Additional ignore patterns (can be repeated) |
| `--debounce` | float | `1.0` | Debounce delay in seconds |
| `--clear/--no-clear` | flag | enabled | Clear console on reload |
| `--transport` | choice | `stdio` | Transport type: `stdio`, `http`, or `sse` |
| `--port` | int | `3000` | Port for network transports |
| `--host` | str | `0.0.0.0` | Host for network transports |
| `--cors/--no-cors` | flag | enabled | Enable/disable CORS |

#### Default Ignore Patterns

The following patterns are ignored by default:
- `.git`, `.git/*`
- `__pycache__`, `__pycache__/*`
- `*.pyc`, `*.pyo`, `*.pyd`
- `.pytest_cache`, `.mypy_cache`, `.ruff_cache`
- `*.egg-info`, `.venv`, `venv`
- `.tox`, `build`, `dist`
- `.coverage`, `htmlcov`
- Temporary files: `*.swp`, `*.swo`, `*~`, `.DS_Store`

#### Examples

**Watch with default settings**

Monitor and auto-reload on any `.py` file change:

```bash
simply-mcp watch examples/simple_server.py
```

**Watch with custom debounce delay**

Wait 2 seconds after changes before reloading:

```bash
simply-mcp watch examples/simple_server.py --debounce 2.0
```

**Watch with additional ignore patterns**

Ignore specific directories:

```bash
simply-mcp watch server.py --ignore "tests/*" --ignore "docs/*"
```

**Watch with multiple ignore patterns**

Chain multiple `-i` flags:

```bash
simply-mcp watch server.py -i "tests/*" -i "*.json" -i "data/*"
```

**Watch without clearing console**

Keep history of reloads visible:

```bash
simply-mcp watch server.py --no-clear
```

**Watch with HTTP transport**

Watch mode works with all transports:

```bash
simply-mcp watch examples/http_server.py --transport http --port 8080
```

**Watch with SSE transport and custom host**

Useful for testing on localhost:

```bash
simply-mcp watch server.py --transport sse --host localhost --port 8080
```

#### Output

The watch command displays:
- Watch mode configuration
- Server restart notifications
- File change events with timestamps
- Server startup messages

#### Notes

- Only watches for `.py` file changes
- Recursive watching of current directory and subdirectories
- Graceful server shutdown before restart
- Debouncing prevents excessive restarts from multiple rapid changes
- Use `dev` command instead for additional development features

---

### list Command

List all components (tools, prompts, resources) in an MCP server file.

#### Syntax

```bash
simply-mcp list SERVER_FILE [OPTIONS]
```

#### Arguments

| Argument | Description |
|----------|-------------|
| `SERVER_FILE` | Path to Python file containing MCP server (required) |

#### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--tools` | flag | disabled | List only tools |
| `--prompts` | flag | disabled | List only prompts |
| `--resources` | flag | disabled | List only resources |
| `--json` | flag | disabled | Output as JSON |

#### Examples

**List all components**

Display all tools, prompts, and resources:

```bash
simply-mcp list examples/decorator_example.py
```

**List only tools**

Filter to show just tools:

```bash
simply-mcp list examples/simple_server.py --tools
```

**List only prompts**

Show prompt templates:

```bash
simply-mcp list examples/decorator_example.py --prompts
```

**List only resources**

Display available resources:

```bash
simply-mcp list examples/decorator_example.py --resources
```

**List as JSON**

Output structured JSON for programmatic use:

```bash
simply-mcp list examples/decorator_example.py --json
```

**List multiple types**

Combine flags to show specific component types:

```bash
simply-mcp list server.py --tools --prompts
```

**List and save to file**

Redirect JSON output to file:

```bash
simply-mcp list server.py --json > components.json
```

**List with jq filtering**

Use jq to filter JSON output:

```bash
simply-mcp list server.py --json | jq '.tools[] | {name, description}'
```

#### Output Formats

**Table Format (Default)**

```
┌─────────────────────────────────────────────────────┐
│            MCP Server Components                    │
├──────────┬─────────────┬─────────────────────────────┤
│ Type     │ Name        │ Description                 │
├──────────┼─────────────┼─────────────────────────────┤
│ Tool     │ add         │ Add two numbers together    │
│ Tool     │ greet       │ Generate a greeting         │
│ Prompt   │ code_review │ Generate code review prompt │
│ Resource │ config      │ Application configuration   │
└──────────┴─────────────┴─────────────────────────────┘

Total: 4 component(s)
```

**JSON Format**

```json
{
  "tools": [
    {
      "name": "add",
      "description": "Add two numbers together",
      "input_schema": {
        "type": "object",
        "properties": {
          "a": {"type": "integer"},
          "b": {"type": "integer"}
        },
        "required": ["a", "b"]
      }
    }
  ],
  "prompts": [
    {
      "name": "code_review",
      "description": "Generate code review prompt",
      "arguments": ["language", "style"]
    }
  ],
  "resources": [
    {
      "uri": "config://app",
      "name": "config",
      "description": "Application configuration",
      "mime_type": "application/json"
    }
  ]
}
```

#### Notes

- Automatically detects API style (decorator, builder, class-based)
- Shows input schemas for tools
- Displays argument lists for prompts
- Includes URIs and MIME types for resources
- JSON output is useful for automation and tooling

---

### bundle Command

Package an MCP server into a standalone executable using PyInstaller.

#### Syntax

```bash
simply-mcp bundle SERVER_FILE [OPTIONS]
```

#### Arguments

| Argument | Description |
|----------|-------------|
| `SERVER_FILE` | Path to Python file containing MCP server (required) |

#### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--name`, `-n` | str | server filename | Name for the executable |
| `--output`, `-o` | path | `./dist` | Output directory |
| `--onefile/--no-onefile`, `-F` | flag | enabled | Bundle as single file |
| `--windowed/--no-windowed`, `-w` | flag | disabled | No console window |
| `--icon`, `-i` | path | None | Custom icon file path |
| `--clean` | flag | disabled | Clean build artifacts after bundling |

#### Prerequisites

PyInstaller must be installed:

```bash
# Install bundling support
pip install simply-mcp[bundling]

# Or install PyInstaller separately
pip install pyinstaller
```

#### Examples

**Bundle with default settings**

Creates single-file executable in `./dist/`:

```bash
simply-mcp bundle examples/simple_server.py
```

**Bundle with custom name and output directory**

Specify executable name and location:

```bash
simply-mcp bundle server.py --name myserver --output ./build
```

**Bundle as directory (not single file)**

Create directory with executable and dependencies:

```bash
simply-mcp bundle server.py --no-onefile
```

**Bundle with custom icon**

Windows/Mac applications with custom icons:

```bash
simply-mcp bundle server.py --icon icon.ico
```

**Bundle and clean up build artifacts**

Remove temporary files after build:

```bash
simply-mcp bundle server.py --clean
```

**Bundle with all options**

Full customization:

```bash
simply-mcp bundle examples/http_server.py \
  --name http-server \
  --output ./release \
  --icon server.ico \
  --clean
```

#### Output

The bundle command:
1. Validates the server file
2. Detects dependencies
3. Generates PyInstaller spec file
4. Builds the executable
5. Displays output location and size

Example output:

```
┌────────────────────────────────────────────┐
│         Build Complete                     │
├────────────────────────────────────────────┤
│ Executable created successfully!           │
│                                            │
│ Location: ./dist/simple_server            │
│ Size: 45.32 MB                            │
└────────────────────────────────────────────┘
```

#### Platform-Specific Notes

**Windows**
- Executable has `.exe` extension
- Use `--icon` with `.ico` file
- `--windowed` hides console window
- Result is Windows-only

**macOS**
- No file extension
- Use `--icon` with `.icns` file
- May need to sign executable for distribution
- Result is macOS-only

**Linux**
- No file extension
- Icon support varies by desktop environment
- Result is Linux-only

#### Hidden Imports

The bundle command automatically includes:
- All simply-mcp modules
- MCP SDK dependencies
- Pydantic, Click, Rich
- Transport dependencies (aiohttp, etc.)

#### Notes

- Bundled executables are platform-specific
- Build process may take several minutes
- Single-file executables are larger but more portable
- Directory bundles start faster but require multiple files
- Use `--clean` to save disk space after build

---

### config Command

Manage Simply-MCP server configuration files.

#### Syntax

```bash
simply-mcp config SUBCOMMAND [OPTIONS]
```

#### Subcommands

- `init` - Create a new configuration file
- `validate` - Validate a configuration file
- `show` - Display current configuration

---

#### config init

Create a new configuration file with default settings.

##### Syntax

```bash
simply-mcp config init [OPTIONS]
```

##### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--output` | path | `simplymcp.config.toml` | Output file path |
| `--format` | choice | `toml` | Format: `toml` or `json` |
| `--force` | flag | disabled | Overwrite existing file |

##### Examples

**Create TOML config (default)**

```bash
simply-mcp config init
```

**Create JSON config**

```bash
simply-mcp config init --format json --output config.json
```

**Overwrite existing file**

```bash
simply-mcp config init --force
```

**Create in custom location**

```bash
simply-mcp config init --output configs/server.toml
```

##### Output

Displays the created configuration file with syntax highlighting.

---

#### config validate

Validate a configuration file for correctness.

##### Syntax

```bash
simply-mcp config validate [CONFIG_FILE]
```

##### Arguments

| Argument | Description |
|----------|-------------|
| `CONFIG_FILE` | Path to config file (optional, searches for defaults) |

##### Default Search Paths

When `CONFIG_FILE` is not provided, searches for:
1. `simplymcp.config.toml`
2. `simplymcp.config.json`
3. `.simplymcp.toml`
4. `.simplymcp.json`

##### Examples

**Validate default config**

Searches for config in default locations:

```bash
simply-mcp config validate
```

**Validate specific file**

```bash
simply-mcp config validate myconfig.toml
```

##### Output

Shows validation status and configuration summary:

```
┌────────────────────────────────────────────┐
│      Configuration Summary                 │
├─────────────────┬──────────────────────────┤
│ Setting         │ Value                    │
├─────────────────┼──────────────────────────┤
│ Server Name     │ my-mcp-server           │
│ Server Version  │ 1.0.0                   │
│ Transport       │ http                     │
│ Port            │ 3000                     │
│ Log Level       │ INFO                     │
│ Log Format      │ json                     │
└─────────────────┴──────────────────────────┘
```

---

#### config show

Display current configuration.

##### Syntax

```bash
simply-mcp config show [CONFIG_FILE] [OPTIONS]
```

##### Arguments

| Argument | Description |
|----------|-------------|
| `CONFIG_FILE` | Path to config file (optional, searches for defaults) |

##### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--format` | choice | `table` | Output format: `table`, `json`, or `toml` |

##### Examples

**Show default config as table**

```bash
simply-mcp config show
```

**Show specific file as JSON**

```bash
simply-mcp config show myconfig.toml --format json
```

**Show as TOML**

```bash
simply-mcp config show --format toml
```

**Save config to file**

```bash
simply-mcp config show --format json > exported-config.json
```

---

## Transport Options

Simply-MCP supports three transport types for different use cases.

### stdio (Standard I/O)

**Use Cases:**
- Claude Desktop integration
- MCP Inspector testing
- Command-line MCP clients

**Characteristics:**
- Communicates via stdin/stdout
- JSON-RPC 2.0 over stdio
- Default transport
- Best for local development

**Example:**

```bash
simply-mcp run server.py --transport stdio
```

### http (HTTP Server)

**Use Cases:**
- Web applications
- RESTful APIs
- Remote access
- Testing with curl

**Characteristics:**
- JSON-RPC 2.0 over HTTP
- CORS support
- Session management
- Health check endpoint

**Example:**

```bash
simply-mcp run server.py --transport http --port 8080
```

**Endpoints:**
- `/` - Server information
- `/health` - Health check
- `/mcp` - JSON-RPC 2.0 endpoint

### sse (Server-Sent Events)

**Use Cases:**
- Real-time streaming
- Event-driven applications
- Long-polling alternatives

**Characteristics:**
- Server-Sent Events stream
- JSON-RPC 2.0 endpoint
- Persistent connections
- Real-time updates

**Example:**

```bash
simply-mcp run server.py --transport sse --port 8080
```

**Endpoints:**
- `/` - Server information
- `/health` - Health check
- `/sse` - SSE stream
- `/mcp` - JSON-RPC 2.0 endpoint

---

## Workflow Examples

### Development Workflow

**1. Create and test server**

```bash
# Create server file
cat > server.py << 'EOF'
from simply_mcp import tool

@tool()
def add(a: int, b: int) -> int:
    return a + b
EOF

# Start dev mode with auto-reload
simply-mcp dev server.py
```

**2. Test with MCP Inspector**

```bash
# In another terminal
npx @anthropic-ai/mcp-inspector python -m simply_mcp.cli.main run server.py
```

**3. Iterate with watch mode**

```bash
# Auto-reload on changes
simply-mcp watch server.py
```

### Testing Different Transports

**Test with stdio (default)**

```bash
simply-mcp run examples/simple_server.py
```

**Test with HTTP and curl**

```bash
# Terminal 1: Start server
simply-mcp run examples/http_server.py --transport http --port 3000

# Terminal 2: Test endpoints
curl http://localhost:3000/health
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
```

**Test with SSE**

```bash
# Start SSE server
simply-mcp run examples/sse_server.py --transport sse --port 3000

# Connect with EventSource or curl
curl -N http://localhost:3000/sse
```

### Inspection and Debugging

**List all components**

```bash
simply-mcp list server.py
```

**List specific types**

```bash
# Just tools
simply-mcp list server.py --tools

# Just prompts
simply-mcp list server.py --prompts

# Tools and prompts
simply-mcp list server.py --tools --prompts
```

**Export component information**

```bash
# Export as JSON
simply-mcp list server.py --json > components.json

# Filter with jq
simply-mcp list server.py --json | jq '.tools[].name'
```

### Configuration Management

**Create config template**

```bash
# Create TOML config
simply-mcp config init

# Edit config
nano simplymcp.config.toml
```

**Validate configuration**

```bash
simply-mcp config validate
```

**Run with configuration**

```bash
simply-mcp run server.py --config simplymcp.config.toml
```

### Production Deployment

**1. Test configuration**

```bash
# Validate config
simply-mcp config validate production.toml

# Test server
simply-mcp run server.py --config production.toml
```

**2. Bundle for deployment**

```bash
# Create standalone executable
simply-mcp bundle server.py \
  --name production-server \
  --output ./release \
  --clean
```

**3. Deploy executable**

```bash
# Copy to server
scp ./release/production-server user@server:/opt/mcp/

# Run on server
ssh user@server '/opt/mcp/production-server'
```

### Multi-Server Development

**Develop multiple servers**

```bash
# Terminal 1: API server
simply-mcp dev api_server.py --transport http --port 3000

# Terminal 2: Worker server
simply-mcp dev worker_server.py --transport http --port 3001

# Terminal 3: Admin server
simply-mcp dev admin_server.py --transport http --port 3002
```

---

## Tips and Best Practices

### Development

**Use dev mode during development**

```bash
# Better than run for development
simply-mcp dev server.py
```

Benefits:
- Auto-reload on changes
- Debug logging enabled
- Interactive controls
- Component listing

**Watch mode for focused development**

```bash
# Simpler than dev mode
simply-mcp watch server.py --debounce 2.0
```

Use when:
- Don't need interactive features
- Want faster startup
- Piping output to files

**List components frequently**

```bash
# Quick check
simply-mcp list server.py

# Detailed JSON inspection
simply-mcp list server.py --json | jq
```

### Configuration

**Use configuration files for production**

```bash
# Create config
simply-mcp config init --output production.toml

# Validate before use
simply-mcp config validate production.toml

# Run with config
simply-mcp run server.py --config production.toml
```

**Override specific settings**

```bash
# Config sets defaults, CLI overrides
simply-mcp run server.py --config config.toml --port 9000
```

**Version control configurations**

```bash
# Keep configs in git
git add *.toml
git commit -m "Add server configurations"
```

### Transport Selection

**Use stdio for:**
- Claude Desktop integration
- Local MCP clients
- Development with MCP Inspector

**Use HTTP for:**
- Web applications
- REST API integration
- Remote access
- Testing with curl/Postman

**Use SSE for:**
- Real-time updates
- Event streaming
- Long-lived connections

### Bundling

**Test before bundling**

```bash
# Test thoroughly first
simply-mcp run server.py

# Then bundle
simply-mcp bundle server.py
```

**Use meaningful names**

```bash
# Good names
simply-mcp bundle server.py --name weather-mcp-server

# Not helpful
simply-mcp bundle server.py --name server
```

**Clean up build artifacts**

```bash
# Save disk space
simply-mcp bundle server.py --clean
```

### File Organization

**Recommended structure**

```
project/
├── server.py              # Main server file
├── simplymcp.config.toml  # Configuration
├── tools/                 # Tool implementations
│   ├── calculator.py
│   └── database.py
├── prompts/              # Prompt templates
│   └── templates.py
└── resources/            # Resource handlers
    └── data.py
```

**Use relative imports**

```python
# In server.py
from tools.calculator import CalculatorTools
from prompts.templates import get_prompts
```

### Debugging

**Enable debug logging**

```bash
# Set environment variable
export SIMPLY_MCP_LOG_LEVEL=DEBUG
simply-mcp run server.py

# Or use dev mode (auto-enables DEBUG)
simply-mcp dev server.py
```

**Check server components**

```bash
# Verify registration
simply-mcp list server.py

# Check JSON schema
simply-mcp list server.py --json | jq '.tools[0].input_schema'
```

**Test transports separately**

```bash
# Test stdio first
simply-mcp run server.py

# Then test HTTP
simply-mcp run server.py --transport http --port 3000
```

---

## Troubleshooting

### Common Issues

#### Server Not Found Error

**Problem:**

```
Error: No MCP server found in the file.
```

**Solutions:**

1. Check file uses decorator, builder, or class-based API:

```python
# Decorator API
from simply_mcp import tool

@tool()
def my_tool():
    pass

# Builder API
from simply_mcp import BuildMCPServer
mcp = BuildMCPServer(name="server")

# Class-based API
from simply_mcp import mcp_server

@mcp_server(name="server")
class MyServer:
    pass
```

2. Verify file imports correctly:

```bash
# Test import
python -c "import server"
```

#### Import Errors

**Problem:**

```
ImportError: Failed to import module: No module named 'xyz'
```

**Solutions:**

1. Install missing dependencies:

```bash
pip install xyz
```

2. Check PYTHONPATH:

```bash
export PYTHONPATH=/path/to/project:$PYTHONPATH
```

3. Use virtual environment:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Port Already in Use

**Problem:**

```
Error: Address already in use: 0.0.0.0:3000
```

**Solutions:**

1. Use different port:

```bash
simply-mcp run server.py --transport http --port 8080
```

2. Find and kill process:

```bash
# Linux/Mac
lsof -ti:3000 | xargs kill

# Or use different port
simply-mcp run server.py --port 3001
```

#### Auto-Reload Not Working

**Problem:**

Watch mode or dev mode not detecting changes.

**Solutions:**

1. Check file is Python:

```bash
# Only .py files trigger reload
mv server.txt server.py
```

2. Verify not in ignore patterns:

```bash
# Check current patterns
simply-mcp watch server.py

# Add custom ignore
simply-mcp watch server.py --ignore "tmp/*"
```

3. Increase debounce delay:

```bash
simply-mcp watch server.py --debounce 2.0
```

#### Configuration Not Loading

**Problem:**

```
Error: Failed to load configuration
```

**Solutions:**

1. Validate configuration:

```bash
simply-mcp config validate myconfig.toml
```

2. Check file format:

```bash
# TOML syntax
[server]
name = "my-server"

# Not JSON syntax in .toml file
```

3. Use absolute paths:

```bash
simply-mcp run server.py --config /absolute/path/to/config.toml
```

#### Bundling Fails

**Problem:**

```
Error: PyInstaller is not installed
```

**Solutions:**

1. Install bundling support:

```bash
pip install simply-mcp[bundling]
# or
pip install pyinstaller
```

2. Check Python version:

```bash
# Requires Python 3.10+
python --version
```

3. Clean previous builds:

```bash
rm -rf build/ dist/ *.spec
simply-mcp bundle server.py
```

#### Keyboard Shortcuts Not Working

**Problem:**

Dev mode keyboard shortcuts (r, l, m, q) not responding.

**Solutions:**

1. Check platform:

```bash
# Only works on Unix-like systems
# Windows doesn't support TTY shortcuts
```

2. Verify TTY:

```bash
# Must run in terminal, not piped
simply-mcp dev server.py  # Works
simply-mcp dev server.py > log.txt  # Shortcuts won't work
```

3. Use without TTY:

```bash
# On Windows or in non-TTY environments
simply-mcp run server.py
# or
simply-mcp watch server.py
```

### Error Messages

#### "File not found"

Check file path is correct:

```bash
# Use absolute path
simply-mcp run /absolute/path/to/server.py

# Or relative from current directory
cd /path/to/project
simply-mcp run server.py
```

#### "Not a Python file"

Ensure file has `.py` extension:

```bash
# Rename file
mv server server.py
simply-mcp run server.py
```

#### "Configuration validation failed"

Check TOML/JSON syntax:

```bash
# Validate syntax
simply-mcp config validate config.toml

# Show current config
simply-mcp config show config.toml
```

### Getting Help

**Check version**

```bash
simply-mcp --version
```

**View command help**

```bash
# Main help
simply-mcp --help

# Command-specific help
simply-mcp run --help
simply-mcp dev --help
simply-mcp bundle --help
```

**Enable verbose output**

```bash
# Set debug logging
export SIMPLY_MCP_LOG_LEVEL=DEBUG
simply-mcp run server.py
```

**Check examples**

```bash
# Run example servers
simply-mcp list examples/simple_server.py
simply-mcp dev examples/decorator_example.py
```

### Additional Resources

- **Documentation**: https://simply-mcp-py.readthedocs.io
- **Issue Tracker**: https://github.com/Clockwork-Innovations/simply-mcp-py/issues
- **Discussions**: https://github.com/Clockwork-Innovations/simply-mcp-py/discussions
- **Examples**: `/examples` directory in repository

---

## Summary

The `simply-mcp` CLI provides everything needed for MCP server development:

- **run** - Production server execution
- **dev** - Development with auto-reload and debugging
- **watch** - File monitoring and auto-reload
- **list** - Component inspection
- **bundle** - Standalone executable creation
- **config** - Configuration management

For most workflows:
1. Start with `dev` during development
2. Use `list` to verify components
3. Test with different transports using `run`
4. Bundle with `bundle` for deployment

See the [examples](/examples) directory for complete working examples of all CLI features.
