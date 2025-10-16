"""Simply-MCP: A Pythonic framework for building MCP servers.

This package provides multiple API styles for building MCP servers,
mirroring the TypeScript implementation for cross-language consistency:

- Programmatic API (BuildMCPServer): Explicit server construction
- Functional API: Config-based definitions (define_mcp, MCPBuilder)
- Decorator API: Pythonic decorators (@tool, @prompt, @resource)
- Core API: Direct server and registry access

Example (Programmatic API - mirrors TypeScript BuildMCPServer):
    >>> from simply_mcp import BuildMCPServer
    >>>
    >>> server = BuildMCPServer(name="my-server", version="1.0.0")
    >>>
    >>> @server.tool()
    >>> def add(a: int, b: int) -> int:
    ...     return a + b
    >>>
    >>> await server.initialize()
    >>> await server.run()

Example (Functional API - mirrors TypeScript functional API):
    >>> from simply_mcp import create_mcp
    >>>
    >>> mcp = create_mcp(name="my-server", version="1.0.0")
    >>> mcp.tool({"name": "add", "handler": lambda a, b: a + b})
    >>> config = mcp.build()

Example (Decorator API):
    >>> from simply_mcp import tool, prompt, resource
    >>>
    >>> @tool()
    >>> def add(a: int, b: int) -> int:
    ...     '''Add two numbers.'''
    ...     return a + b
"""

# Programmatic API (BuildMCPServer - mirrors TypeScript)
from simply_mcp.api.programmatic import BuildMCPServer

# Functional API (config-based, mirrors TypeScript)
from simply_mcp.api.functional import (
    MCPBuilder,
    MCPConfig,
    PromptConfig,
    ResourceConfig,
    ToolConfig,
    create_mcp,
    define_mcp,
    define_prompt,
    define_resource,
    define_tool,
)

# Decorator API
from simply_mcp.api.decorators import (
    get_global_server,
    mcp_server,
    prompt,
    resource,
    set_global_server,
    tool,
)

# Core components
from simply_mcp.core.config import SimplyMCPConfig, get_default_config, load_config

# Error types
from simply_mcp.core.errors import (
    ConfigurationError,
    HandlerError,
    HandlerExecutionError,
    HandlerNotFoundError,
    SimplyMCPError,
    ValidationError,
)
from simply_mcp.core.server import SimplyMCPServer

__version__ = "0.1.0b3"

__all__ = [
    # Programmatic API (mirrors TypeScript BuildMCPServer)
    "BuildMCPServer",
    # Functional API (mirrors TypeScript functional API)
    "MCPBuilder",
    "create_mcp",
    "define_mcp",
    "define_tool",
    "define_prompt",
    "define_resource",
    "MCPConfig",
    "ToolConfig",
    "PromptConfig",
    "ResourceConfig",
    # Decorator API
    "tool",
    "prompt",
    "resource",
    "mcp_server",
    "get_global_server",
    "set_global_server",
    # Core
    "SimplyMCPServer",
    "SimplyMCPConfig",
    "get_default_config",
    "load_config",
    # Errors
    "SimplyMCPError",
    "ConfigurationError",
    "ValidationError",
    "HandlerError",
    "HandlerNotFoundError",
    "HandlerExecutionError",
    # Metadata
    "__version__",
]
