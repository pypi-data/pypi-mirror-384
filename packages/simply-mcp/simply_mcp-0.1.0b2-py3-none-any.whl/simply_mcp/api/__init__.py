"""API interfaces for Simply-MCP.

This module provides two API styles:
- Builder API (SimplyMCP): Fluent interface with method chaining
- Decorator API: Pythonic decorators for registering components
"""

from simply_mcp.api.builder import SimplyMCP
from simply_mcp.api.decorators import (
    get_global_server,
    mcp_server,
    prompt,
    resource,
    set_global_server,
    tool,
)

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
]
