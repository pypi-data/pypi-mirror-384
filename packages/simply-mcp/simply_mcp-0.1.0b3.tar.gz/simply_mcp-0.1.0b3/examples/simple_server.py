#!/usr/bin/env python3
"""Simple MCP Server Example - Getting Started

This is the most basic example of a Simply-MCP server. It demonstrates:
- Creating a BuildMCPServer instance with name and version
- Registering tools using the builder API pattern
- Running with stdio transport (standard input/output)
- Basic tool implementation with type annotations

This example uses the builder API for registering tools. For alternative approaches:
- decorator_example.py - Pythonic decorator-based API (@tool, @prompt, @resource)
- builder_basic.py - Fluent builder API with method chaining
- builder_chaining.py - Advanced method chaining patterns

Key Concepts:
    MCP Server: The core server instance that manages tools, prompts, and resources
    Stdio Transport: Communication via standard input/output (used by MCP clients)
    Tool Registration: Adding callable functions as tools with automatic schema generation
    Initialization: Required setup step before running the server

Installation:
    pip install simply-mcp

Usage:
    # Run with stdio transport (for MCP clients like Claude Desktop)
    python examples/simple_server.py

    # Test with MCP Inspector (official testing tool)
    npx @anthropic-ai/mcp-inspector python examples/simple_server.py

    # Use with Claude Desktop (add to config)
    # See: https://modelcontextprotocol.io/quickstart/user

Available Tools:
    - add(a, b): Add two integers and return the sum
    - greet(name, formal): Generate a greeting message (casual or formal)

Expected Output:
    When run with stdio transport, the server waits for JSON-RPC messages
    from an MCP client. With MCP Inspector, you'll see a web interface to
    test the tools interactively.

Learning Path:
    1. Start here: simple_server.py (you are here)
    2. Try: decorator_example.py (easier syntax with decorators)
    3. Explore: builder_basic.py (fluent API patterns)
    4. Advanced: production_server.py (all features enabled)

See Also:
    - http_server.py - HTTP transport example
    - authenticated_server.py - Adding authentication
    - production_server.py - Production-ready server

Requirements:
    - Python 3.10+
    - simply-mcp
"""

import asyncio
from simply_mcp import BuildMCPServer


# ============================================================================
# Tool Implementations
# ============================================================================
# These are regular Python functions that will be exposed as MCP tools.
# Type annotations are used for automatic JSON Schema generation.
# Docstrings become tool descriptions in the MCP protocol.

def add_numbers(a: int, b: int) -> int:
    """Add two numbers together.

    This is a simple tool that demonstrates basic parameter handling.
    The type annotations (int) are used to generate JSON Schema, which
    tells MCP clients what types of arguments to provide.

    Args:
        a: First number to add
        b: Second number to add

    Returns:
        Sum of a and b

    Example:
        >>> add_numbers(5, 3)
        8
    """
    # Simple arithmetic - no validation needed as types are enforced by MCP
    return a + b


def greet(name: str, formal: bool = False) -> str:
    """Generate a greeting message.

    This tool demonstrates optional parameters with default values.
    The 'formal' parameter defaults to False, making it optional for clients.

    Args:
        name: Person's name to greet
        formal: If True, use formal greeting style. Defaults to False.

    Returns:
        A greeting message string (formal or casual style)

    Examples:
        >>> greet("Alice")
        'Hey Alice!'
        >>> greet("Bob", formal=True)
        'Good day, Bob.'
    """
    # Choose greeting style based on formality parameter
    if formal:
        return f"Good day, {name}."
    return f"Hey {name}!"


async def main():
    """Main entry point for the simple server.

    This function:
    1. Creates a BuildMCPServer server instance
    2. Registers tool handlers
    3. Initializes the server
    4. Runs with stdio transport
    """
    # ========================================================================
    # Server Creation
    # ========================================================================
    # Create a BuildMCPServer instance with identifying information.
    # The name and version are sent to clients during initialization.
    mcp = BuildMCPServer(
        name="simple-server",
        version="1.0.0",
        description="Simple MCP server example"
    )

    # ========================================================================
    # Tool Registration
    # ========================================================================
    # Register Python functions as MCP tools using the builder API.
    # The framework automatically generates JSON Schema from type annotations.
    # The function name becomes the tool name, or you can specify a custom name.
    mcp.add_tool("add", add_numbers, description="Add two numbers together")
    mcp.add_tool("greet", greet, description="Generate a greeting message")

    # ========================================================================
    # Server Initialization and Execution
    # ========================================================================
    # Initialize the server (prepares internal state, validates configuration)
    await mcp.initialize()

    # Run with stdio transport - this blocks until the server is stopped
    # The server communicates via stdin/stdout using JSON-RPC 2.0 protocol
    await mcp.run_stdio()


if __name__ == "__main__":
    # Entry point: run the async main function
    asyncio.run(main())
