"""Simply-MCP: A Pythonic framework for building MCP servers.

This package provides multiple API styles for building MCP servers:
- Builder API (SimplyMCP): Fluent, method-chaining interface
- Decorator API: Pythonic decorators (@tool, @prompt, @resource)
- Core API: Direct server and registry access

Example (Builder API):
    >>> from simply_mcp import SimplyMCP
    >>>
    >>> mcp = SimplyMCP(name="my-server", version="1.0.0")
    >>>
    >>> @mcp.tool()
    >>> def add(a: int, b: int) -> int:
    ...     return a + b
    >>>
    >>> await mcp.initialize()
    >>> await mcp.run()

Example (Decorator API):
    >>> from simply_mcp import tool, prompt, resource
    >>>
    >>> @tool()
    >>> def add(a: int, b: int) -> int:
    ...     '''Add two numbers.'''
    ...     return a + b
"""

# Builder API (primary interface)
from simply_mcp.api.builder import SimplyMCP

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

__version__ = "0.1.0b2"

__all__ = [
    # Builder API
    "SimplyMCP",
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
