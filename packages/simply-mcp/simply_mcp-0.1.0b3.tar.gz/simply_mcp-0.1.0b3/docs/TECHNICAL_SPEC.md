# Simply-MCP-PY: Technical Specification

**Version:** 0.1.0
**Last Updated:** 2025-10-12
**Status:** Planning Phase

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Core Features](#2-core-features)
3. [Python Project Structure](#3-python-project-structure)
4. [Key Modules & Responsibilities](#4-key-modules--responsibilities)
5. [Configuration Schema](#5-configuration-schema)
6. [API Comparison: TypeScript vs Python](#6-api-comparison-typescript-vs-python)
7. [Dependencies](#7-dependencies)
8. [pyproject.toml Structure](#8-pyprojecttoml-structure)

---

## 1. Project Overview

### 1.1 Project Information

- **Name:** simply-mcp-py
- **Purpose:** A modern, Pythonic framework for building Model Context Protocol (MCP) servers with multiple API styles and transport options
- **Base SDK:** Anthropic MCP Python SDK (`mcp`)
- **License:** MIT
- **Python Version:** >=3.10
- **Author:** Clockwork Innovations
- **Repository:** https://github.com/Clockwork-Innovations/simply-mcp-py

### 1.2 Design Philosophy

Simply-MCP-PY brings the flexibility and ease-of-use of simply-mcp-ts to the Python ecosystem, providing:

- **Zero Boilerplate:** Start building MCP servers with minimal setup
- **Type Safety:** Full type hints and Pydantic validation
- **Flexibility:** Multiple API styles to match your coding preferences
- **Pythonic:** Follows Python best practices and idioms
- **Modern:** Uses src layout, pyproject.toml, and current Python standards

### 1.3 Relationship to simply-mcp-ts

This project is a Python port of [simply-mcp-ts](https://github.com/Clockwork-Innovations/simply-mcp-ts), maintaining feature parity while adapting to Python conventions and ecosystem.

---

## 2. Core Features

### 2.1 Multiple API Styles

#### 2.1.1 Decorator API (Primary)
Class-based approach using Python decorators for clean, declarative syntax.

**Features:**
- `@mcp_server()` class decorator for server configuration
- `@tool()` method decorator for tool registration
- `@prompt()` method decorator for prompt templates
- `@resource()` method decorator for resource exposure
- Automatic metadata extraction
- Type-safe parameter validation

#### 2.1.2 Functional API
Programmatic server building with method chaining for maximum control.

**Features:**
- `BuildMCPServer` builder class
- `.add_tool()`, `.add_prompt()`, `.add_resource()` methods
- Fluent interface with method chaining
- Dynamic tool registration
- Runtime configuration

#### 2.1.3 Interface API
Type-annotated pure Python interfaces using Protocol and TypedDict.

**Features:**
- Zero decorators approach
- Pure type annotations
- Protocol-based interfaces
- Automatic schema generation from types
- Static type checking friendly

#### 2.1.4 Builder API (Future Phase)
AI-powered tool development using MCP itself.

**Features:**
- Build MCP tools using MCP
- AI-assisted validation
- Schema generation
- Template library

### 2.2 Transport Support

#### 2.2.1 Stdio (Standard Input/Output)
Default transport for command-line usage and process-based communication.

**Features:**
- Zero configuration
- Process-based isolation
- Standard streams communication
- Compatible with all MCP clients

#### 2.2.2 HTTP (Stateful & Stateless)
Full-featured HTTP server with session management.

**Features:**
- RESTful endpoint exposure
- Session management for stateful mode
- CORS support
- Middleware support
- WebSocket upgrade path (future)

#### 2.2.3 SSE (Server-Sent Events)
Real-time event streaming for live updates.

**Features:**
- Real-time communication
- Automatic reconnection
- Event streaming
- Progress updates
- Long-running operation support

### 2.3 CLI Features

#### 2.3.1 Run Command
```bash
simply-mcp run server.py                            # Run with stdio
simply-mcp run server.py --transport http           # Run with HTTP on default port
simply-mcp run server.py --transport http --port 3000 # Run with HTTP on port 3000
simply-mcp run server.py --transport sse            # Run with SSE
simply-mcp run server.py --watch                    # Watch mode with auto-reload
```

#### 2.3.2 Bundle Command
```bash
simply-mcp bundle server.py                 # Create standalone executable
simply-mcp bundle server.py --output dist/  # Specify output directory
```

#### 2.3.3 List Command
```bash
simply-mcp list                             # List all available servers
simply-mcp list --json                      # Output as JSON
```

#### 2.3.4 Config Command
```bash
simply-mcp config init                      # Initialize configuration
simply-mcp config validate                  # Validate configuration
simply-mcp config show                      # Display current configuration
```

### 2.4 Advanced Features

#### 2.4.1 Auto API Detection
Automatically detects which API style is being used:
- Scans for class decorators → Decorator API
- Detects BuildMCPServer instance → Functional API
- Analyzes type annotations → Interface API

#### 2.4.2 Validation
- Pydantic-based schema validation
- Automatic schema generation from type hints
- Runtime type checking
- Custom validators support

#### 2.4.3 Error Handling
- Comprehensive error messages
- Error context and stack traces
- Custom exception hierarchy
- Graceful degradation

#### 2.4.4 Session Management
- Stateful HTTP sessions
- Session storage backends (memory, redis)
- Session timeout management
- Session data encryption

#### 2.4.5 Binary Content
- Binary resource support
- MIME type detection
- Streaming support
- Efficient memory handling

#### 2.4.6 Progress Reporting
- Real-time progress updates
- Percentage and message-based progress
- Async progress reporting
- Progress event streaming

#### 2.4.7 Handler System
- Extensible handler architecture
- Handler lifecycle management
- Middleware support
- Error recovery

#### 2.4.8 Security
- Rate limiting (token bucket algorithm)
- Authentication (OAuth 2.1, API keys, JWT)
- CORS configuration
- Input sanitization
- SQL injection prevention

---

## 3. Python Project Structure

Following Python best practices with **src layout**:

```
simply-mcp-py/
├── .github/
│   └── workflows/
│       ├── ci.yml                  # CI pipeline
│       ├── release.yml             # Release automation
│       └── docs.yml                # Documentation build
├── docs/
│   ├── TECHNICAL_SPEC.md           # This file
│   ├── ARCHITECTURE.md             # Architecture document
│   ├── ROADMAP.md                  # Implementation roadmap
│   ├── getting-started.md          # Getting started guide
│   ├── api-reference.md            # API reference
│   ├── examples.md                 # Examples documentation
│   └── configuration.md            # Configuration guide
├── examples/
│   ├── simple_server.py            # Simplest possible server
│   ├── decorator_basic.py          # Basic decorator API
│   ├── decorator_advanced.py       # Advanced decorator features
│   ├── functional_api.py           # Functional API example
│   ├── interface_api.py            # Interface API example
│   ├── http_server.py              # HTTP transport example
│   ├── sse_server.py               # SSE transport example
│   └── advanced_features.py        # Progress, binary, etc.
├── src/
│   └── simply_mcp/
│       ├── __init__.py             # Public API exports
│       ├── py.typed                # PEP 561 marker
│       │
│       ├── api/                    # API Styles
│       │   ├── __init__.py
│       │   ├── decorator.py        # Decorator API implementation
│       │   ├── functional.py       # Functional API implementation
│       │   ├── interface.py        # Interface API implementation
│       │   └── builder.py          # Builder API (future)
│       │
│       ├── cli/                    # CLI Commands
│       │   ├── __init__.py
│       │   ├── main.py             # CLI entry point
│       │   ├── run.py              # Run command
│       │   ├── bundle.py           # Bundle command
│       │   ├── list.py             # List command
│       │   ├── watch.py            # Watch mode implementation
│       │   └── config_cmd.py       # Config management commands
│       │
│       ├── core/                   # Core Infrastructure
│       │   ├── __init__.py
│       │   ├── server.py           # SimplyMCPServer core class
│       │   ├── config.py           # Configuration loader & schemas
│       │   ├── errors.py           # Error classes & handlers
│       │   ├── logger.py           # Logging utilities
│       │   ├── types.py            # Core type definitions
│       │   └── registry.py         # Tool/prompt/resource registry
│       │
│       ├── transports/             # Transport Implementations
│       │   ├── __init__.py
│       │   ├── base.py             # Base transport class
│       │   ├── stdio.py            # Stdio transport adapter
│       │   ├── http.py             # HTTP transport adapter
│       │   └── sse.py              # SSE transport adapter
│       │
│       ├── handlers/               # Handler Management
│       │   ├── __init__.py
│       │   ├── manager.py          # Handler lifecycle manager
│       │   └── middleware.py       # Middleware system
│       │
│       ├── validation/             # Validation & Schemas
│       │   ├── __init__.py
│       │   ├── schema.py           # Pydantic schemas
│       │   └── validators.py       # Custom validators
│       │
│       └── security/               # Security Features
│           ├── __init__.py
│           ├── rate_limit.py       # Rate limiting
│           ├── auth.py             # Authentication
│           └── cors.py             # CORS handling
├── tests/
│   ├── unit/
│   │   ├── test_api/
│   │   ├── test_core/
│   │   ├── test_transports/
│   │   └── test_validation/
│   ├── integration/
│   │   ├── test_decorator_api.py
│   │   ├── test_functional_api.py
│   │   └── test_transports.py
│   └── fixtures/
│       ├── servers.py
│       └── configs.py
├── scripts/
│   ├── dev_setup.sh                # Development environment setup
│   └── build.sh                    # Build script
├── .gitignore
├── .python-version                  # Python version (3.10)
├── .pre-commit-config.yaml          # Pre-commit hooks
├── CHANGELOG.md
├── CODE_OF_CONDUCT.md
├── CONTRIBUTING.md
├── LICENSE
├── README.md
├── pyproject.toml                   # Modern Python project config
└── simplymcp.config.example.toml    # Example configuration
```

---

## 4. Key Modules & Responsibilities

### 4.1 API Layer (`src/simply_mcp/api/`)

#### decorator.py
**Responsibility:** Implements decorator-based API

**Key Components:**
- `@mcp_server()` - Class decorator for server configuration
- `@tool()` - Method decorator for tool registration
- `@prompt()` - Method decorator for prompt templates
- `@resource()` - Method decorator for resource exposure
- Metadata extraction and validation
- Automatic schema generation from type hints

**Example:**
```python
from simply_mcp import mcp_server, tool

@mcp_server(name="my-server", version="1.0.0")
class MyServer:
    @tool(description="Add two numbers")
    def add(self, a: int, b: int) -> int:
        return a + b
```

#### functional.py
**Responsibility:** Implements functional/builder API

**Key Components:**
- `BuildMCPServer` - Main builder class
- `.add_tool()` - Dynamic tool registration
- `.add_prompt()` - Dynamic prompt registration
- `.add_resource()` - Dynamic resource registration
- `.configure()` - Configuration method
- `.run()` - Server execution

**Example:**
```python
from simply_mcp import BuildMCPServer

mcp = BuildMCPServer(name="my-server", version="1.0.0")

@mcp.add_tool(description="Add two numbers")
def add(a: int, b: int) -> int:
    return a + b

mcp.run()
```

#### interface.py
**Responsibility:** Implements interface-based API

**Key Components:**
- `MCPServerProtocol` - Protocol for type checking
- Type-based schema generation
- Automatic tool discovery from type annotations
- Zero-decorator approach

**Example:**
```python
from simply_mcp.api.interface import MCPServerProtocol
from typing import Protocol

class MyServer(MCPServerProtocol):
    def add(self, a: int, b: int) -> int:
        """Add two numbers"""
        return a + b
```

#### builder.py (Future)
**Responsibility:** AI-powered tool builder

**Key Components:**
- `MCPBuilder` - Builder class
- AI-assisted schema generation
- Template library
- Validation tools

### 4.2 CLI Layer (`src/simply_mcp/cli/`)

#### main.py
**Responsibility:** CLI entry point and router

**Key Components:**
- Click-based CLI application
- Command routing
- Global options handling
- Help text and documentation

#### run.py
**Responsibility:** Server execution

**Key Components:**
- API style auto-detection
- Transport selection
- Configuration loading
- Server lifecycle management
- Error handling and reporting

#### bundle.py
**Responsibility:** Create standalone executables

**Key Components:**
- PyInstaller integration
- Nuitka support
- Dependency bundling
- Platform-specific builds

#### watch.py
**Responsibility:** File watching and auto-reload

**Key Components:**
- Watchdog integration
- File change detection
- Server restart logic
- Debouncing

#### config_cmd.py
**Responsibility:** Configuration management

**Key Components:**
- Config initialization
- Config validation
- Config display
- Schema generation

### 4.3 Core Layer (`src/simply_mcp/core/`)

#### server.py
**Responsibility:** Core server implementation

**Key Components:**
- `SimplyMCPServer` - Main server class
- MCP SDK integration
- Tool/prompt/resource registry
- Lifecycle management
- Event handling

#### config.py
**Responsibility:** Configuration management

**Key Components:**
- `ServerConfig` - Pydantic model for server config
- `TransportConfig` - Transport configuration
- `SecurityConfig` - Security configuration
- Config file loading (TOML/JSON)
- Environment variable support
- Config validation

#### errors.py
**Responsibility:** Error handling

**Key Components:**
- `SimplyMCPError` - Base exception class
- `ConfigurationError` - Config-related errors
- `ValidationError` - Validation errors
- `TransportError` - Transport errors
- Error formatting
- Error logging

#### logger.py
**Responsibility:** Logging infrastructure

**Key Components:**
- Structured logging
- Log level configuration
- JSON/text formatters
- Context injection
- Performance logging

#### types.py
**Responsibility:** Type definitions

**Key Components:**
- `ToolConfig` - TypedDict for tool config
- `PromptConfig` - TypedDict for prompt config
- `ResourceConfig` - TypedDict for resource config
- Protocol definitions
- Type aliases

#### registry.py
**Responsibility:** Component registry

**Key Components:**
- Tool registry
- Prompt registry
- Resource registry
- Component lookup
- Metadata storage

### 4.4 Transport Layer (`src/simply_mcp/transports/`)

#### base.py
**Responsibility:** Base transport interface

**Key Components:**
- `Transport` - Abstract base class
- Transport lifecycle hooks
- Request/response handling
- Error handling

#### stdio.py
**Responsibility:** Stdio transport

**Key Components:**
- Standard input/output handling
- Process communication
- Message framing
- Error stream handling

#### http.py
**Responsibility:** HTTP transport

**Key Components:**
- aiohttp server
- RESTful endpoints
- Session management
- CORS handling
- Middleware support

#### sse.py
**Responsibility:** SSE transport

**Key Components:**
- Server-Sent Events implementation
- Event streaming
- Connection management
- Heartbeat/keepalive

---

## 5. Configuration Schema

### 5.1 simplymcp.config.toml

```toml
[server]
name = "my-mcp-server"
version = "1.0.0"
description = "My MCP server"

[transport]
type = "stdio"      # Options: "stdio", "http", "sse"
port = 3000         # For HTTP/SSE transports
host = "0.0.0.0"    # Bind address

[transport.http]
enable_stateful = true
session_timeout = 3600
cors_enabled = true
cors_origins = ["*"]

[logging]
level = "INFO"      # Options: "DEBUG", "INFO", "WARNING", "ERROR"
format = "json"     # Options: "json", "text"
file = "server.log" # Optional log file

[security]
enable_rate_limiting = true
rate_limit_per_minute = 60
rate_limit_burst = 10

[security.auth]
enabled = false
type = "api_key"    # Options: "api_key", "oauth", "jwt"
api_keys = []

[features]
enable_progress = true
enable_binary_content = true
max_request_size = 10485760  # 10MB

[development]
debug = false
auto_reload = false
```

### 5.2 Environment Variables

```bash
SIMPLY_MCP_CONFIG_FILE=./simplymcp.config.toml
SIMPLY_MCP_LOG_LEVEL=INFO
SIMPLY_MCP_PORT=3000
SIMPLY_MCP_TRANSPORT=stdio
SIMPLY_MCP_DEBUG=false
```

### 5.3 Pydantic Config Models

```python
from pydantic import BaseModel, Field
from typing import Literal, Optional

class ServerConfig(BaseModel):
    name: str = Field(..., description="Server name")
    version: str = Field(..., description="Server version")
    description: Optional[str] = None

class TransportConfig(BaseModel):
    type: Literal["stdio", "http", "sse"] = "stdio"
    port: int = Field(default=3000, ge=1, le=65535)
    host: str = "0.0.0.0"

class LoggingConfig(BaseModel):
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    format: Literal["json", "text"] = "json"
    file: Optional[str] = None

class SecurityConfig(BaseModel):
    enable_rate_limiting: bool = True
    rate_limit_per_minute: int = 60
    rate_limit_burst: int = 10

class SimplyMCPConfig(BaseModel):
    server: ServerConfig
    transport: TransportConfig
    logging: LoggingConfig = LoggingConfig()
    security: SecurityConfig = SecurityConfig()
```

---

## 6. API Comparison: TypeScript vs Python

### 6.1 Decorator API

#### TypeScript
```typescript
import { MCPServer, tool, prompt, resource } from 'simply-mcp';

@MCPServer({ name: 'my-server', version: '1.0.0' })
export default class MyServer {
  @tool('Add two numbers')
  add(a: number, b: number): number {
    return a + b;
  }

  @prompt('Generate greeting')
  greet(name: string): string {
    return `Hello, ${name}!`;
  }

  @resource('config://server', { mimeType: 'application/json' })
  config() {
    return { status: 'running' };
  }
}
```

#### Python
```python
from simply_mcp import mcp_server, tool, prompt, resource

@mcp_server(name='my-server', version='1.0.0')
class MyServer:
    @tool(description='Add two numbers')
    def add(self, a: int, b: int) -> int:
        return a + b

    @prompt(description='Generate greeting')
    def greet(self, name: str) -> str:
        return f"Hello, {name}!"

    @resource(uri='config://server', mime_type='application/json')
    def config(self) -> dict:
        return {"status": "running"}
```

### 6.2 Functional API

#### TypeScript
```typescript
import { BuildMCPServer } from 'simply-mcp';

const mcp = BuildMCPServer({ name: 'my-server', version: '1.0.0' });

mcp.addTool({
  name: 'add',
  description: 'Add two numbers',
  execute: (a: number, b: number) => a + b,
});

mcp.run();
```

#### Python
```python
from simply_mcp import BuildMCPServer

mcp = BuildMCPServer(name='my-server', version='1.0.0')

@mcp.add_tool(description='Add two numbers')
def add(a: int, b: int) -> int:
    return a + b

mcp.run()
```

### 6.3 Schema Validation

#### TypeScript (Zod)
```typescript
import { z } from 'zod';

@tool('Add numbers', {
  schema: z.object({
    a: z.number(),
    b: z.number(),
  }),
})
add(params: { a: number; b: number }): number {
  return params.a + params.b;
}
```

#### Python (Pydantic)
```python
from pydantic import BaseModel

class AddParams(BaseModel):
    a: int
    b: int

@tool(description='Add numbers')
def add(params: AddParams) -> int:
    return params.a + params.b
```

---

## 7. Dependencies

### 7.1 Core Dependencies

```toml
[project.dependencies]
# MCP SDK
"mcp" = ">=0.1.0"

# Validation & Serialization
"pydantic" = ">=2.0.0"
"pydantic-settings" = ">=2.0.0"

# CLI Framework
"click" = ">=8.0.0"
"rich" = ">=13.0.0"

# File Watching
"watchdog" = ">=3.0.0"

# HTTP Server
"aiohttp" = ">=3.9.0"
"aiohttp-cors" = ">=0.7.0"

# Configuration
"tomli" = ">=2.0.0; python_version < '3.11'"  # TOML parsing
"python-dotenv" = ">=1.0.0"

# Utilities
"typing-extensions" = ">=4.0.0"
```

### 7.2 Development Dependencies

```toml
[project.optional-dependencies]
dev = [
    # Testing
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.0.0",
    "pytest-mock>=3.10.0",
    "httpx>=0.24.0",  # For testing HTTP transport

    # Code Quality
    "black>=23.0.0",
    "ruff>=0.1.0",
    "mypy>=1.0.0",
    "pre-commit>=3.0.0",

    # Documentation
    "mkdocs>=1.5.0",
    "mkdocs-material>=9.0.0",
    "mkdocstrings[python]>=0.24.0",

    # Build
    "build>=1.0.0",
    "twine>=4.0.0",
]

bundling = [
    "pyinstaller>=5.0.0",
    "nuitka>=1.8.0",
]
```

### 7.3 Minimum Python Version

- **Python 3.10+** (for modern type hints, pattern matching, better asyncio)

---

## 8. pyproject.toml Structure

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "simply-mcp"
version = "0.1.0"
description = "A modern Python framework for building MCP servers with multiple API styles"
authors = [
    {name = "Clockwork Innovations", email = "info@clockwork-innovations.com"}
]
license = {text = "MIT"}
readme = "README.md"
requires-python = ">=3.10"
keywords = [
    "mcp",
    "model-context-protocol",
    "ai",
    "llm",
    "anthropic",
    "server",
    "framework"
]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Topic :: Scientific/Engineering :: Artificial Intelligence",
]

dependencies = [
    "mcp>=0.1.0",
    "pydantic>=2.0.0",
    "pydantic-settings>=2.0.0",
    "click>=8.0.0",
    "rich>=13.0.0",
    "watchdog>=3.0.0",
    "aiohttp>=3.9.0",
    "aiohttp-cors>=0.7.0",
    "tomli>=2.0.0; python_version < '3.11'",
    "python-dotenv>=1.0.0",
    "typing-extensions>=4.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.0.0",
    "pytest-mock>=3.10.0",
    "httpx>=0.24.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
    "mypy>=1.0.0",
    "pre-commit>=3.0.0",
    "mkdocs>=1.5.0",
    "mkdocs-material>=9.0.0",
    "mkdocstrings[python]>=0.24.0",
    "build>=1.0.0",
    "twine>=4.0.0",
]

bundling = [
    "pyinstaller>=5.0.0",
]

[project.scripts]
simply-mcp = "simply_mcp.cli.main:cli"

[project.urls]
Homepage = "https://github.com/Clockwork-Innovations/simply-mcp-py"
Documentation = "https://simply-mcp-py.readthedocs.io"
Repository = "https://github.com/Clockwork-Innovations/simply-mcp-py"
Issues = "https://github.com/Clockwork-Innovations/simply-mcp-py/issues"
Changelog = "https://github.com/Clockwork-Innovations/simply-mcp-py/blob/main/CHANGELOG.md"

[tool.hatch.build.targets.wheel]
packages = ["src/simply_mcp"]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
addopts = [
    "--cov=simply_mcp",
    "--cov-report=term-missing",
    "--cov-report=html",
    "--cov-report=xml",
]

[tool.coverage.run]
source = ["src"]
omit = ["tests/*", "*/test_*.py"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
]

[tool.black]
line-length = 100
target-version = ['py310']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | build
  | dist
)/
'''

[tool.ruff]
line-length = 100
target-version = "py310"
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
]
ignore = [
    "E501",  # line too long, handled by black
    "B008",  # do not perform function calls in argument defaults
]

[tool.ruff.per-file-ignores]
"__init__.py" = ["F401"]  # imported but unused

[tool.mypy]
python_version = "3.10"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_any_unimported = false
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
check_untyped_defs = true
strict_equality = true

[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false

[[tool.mypy.overrides]]
module = "mcp.*"
ignore_missing_imports = true
```

---

## 9. Success Metrics

### 9.1 Feature Completeness
- [ ] All 4 API styles implemented
- [ ] All 3 transports functional
- [ ] CLI feature parity with TypeScript version
- [ ] Security features implemented

### 9.2 Quality Metrics
- [ ] >85% test coverage
- [ ] 100% mypy strict mode compliance
- [ ] 100% of public API documented
- [ ] Zero critical security vulnerabilities

### 9.3 Performance Metrics
- [ ] <100ms overhead vs raw MCP SDK
- [ ] <500MB memory for basic server
- [ ] <2s startup time for bundled executable

### 9.4 Documentation Metrics
- [ ] Complete API reference
- [ ] 10+ working examples
- [ ] Getting started guide
- [ ] Migration guide from TypeScript

---

## Appendix A: Glossary

- **MCP**: Model Context Protocol
- **Tool**: An executable function exposed by the server
- **Prompt**: A template for generating context for LLMs
- **Resource**: Data exposed by the server (files, configurations, etc.)
- **Transport**: Communication mechanism (stdio, HTTP, SSE)
- **Handler**: Code that processes requests for tools/prompts/resources
- **Session**: Stateful connection context for HTTP transport

## Appendix B: References

- [simply-mcp-ts Repository](https://github.com/Clockwork-Innovations/simply-mcp-ts)
- [Anthropic MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [Model Context Protocol Specification](https://modelcontextprotocol.io)
- [Python Packaging Guide](https://packaging.python.org)
- [Pydantic Documentation](https://docs.pydantic.dev)
