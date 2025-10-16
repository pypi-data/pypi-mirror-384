"""API interfaces for Simply-MCP.

This module provides multiple API styles mirroring the TypeScript implementation:
- Programmatic API (BuildMCPServer): Explicit server construction
- Functional API: Config-based definitions (define_mcp, MCPBuilder)
- Decorator API: Pythonic decorators for registering components
"""

# Programmatic API
from simply_mcp.api.programmatic import BuildMCPServer

# Functional API
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
]
