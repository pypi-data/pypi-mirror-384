#!/usr/bin/env python3
"""Builder API Example - Creating MCP Servers with Method Chaining

This example demonstrates the BuildMCPServer builder API, which provides a clean
and intuitive way to construct MCP servers. The builder pattern offers:

- Fluent Interface: Create and configure servers in a readable flow
- Multiple Registration Methods: Use decorators OR direct registration
- Type Safety: Automatic JSON Schema generation from type hints
- Flexibility: Mix and match different registration styles

Key Features Demonstrated:
    - Creating a BuildMCPServer instance with configuration
    - Registering tools using @mcp.tool() decorator
    - Direct tool registration with add_tool()
    - Adding prompts with @mcp.prompt()
    - Publishing resources with @mcp.resource()
    - Server initialization and execution

Comparison with Other APIs:
    - Decorator API: Uses global @tool() decorators (see decorator_example.py)
    - Builder API: Instance-based decorators @mcp.tool() (this example)
    - Builder Chaining: Advanced method chaining (see builder_chaining.py)

Installation:
    pip install simply-mcp

Usage:
    # Run with stdio transport
    python examples/builder_basic.py

    # Test with MCP Inspector
    npx @anthropic-ai/mcp-inspector python examples/builder_basic.py

    # Use with HTTP transport
    simply-mcp run examples/builder_basic.py --http --port 3000

Available Tools:
    - add(a, b): Add two integers
    - multiply(a, b): Multiply two numbers
    - divide(a, b): Divide with zero-check

Available Prompts:
    - math_tutor(topic): Generate teaching prompts

Available Resources:
    - config://calculator: Server configuration

Expected Output:
    Prints registered tools, prompts, and resources, then starts
    the MCP server waiting for JSON-RPC requests.

Learning Path:
    - Previous: decorator_example.py (decorator pattern)
    - Current: builder_basic.py (you are here)
    - Next: builder_chaining.py (advanced chaining)

See Also:
    - simple_server.py - Minimal example
    - builder_chaining.py - Method chaining patterns
    - builder_pydantic.py - Pydantic integration

Requirements:
    - Python 3.10+
    - simply-mcp
"""

import asyncio
from simply_mcp import BuildMCPServer


# ============================================================================
# Server Instance Creation
# ============================================================================
# Create a BuildMCPServer instance that will hold all tools, prompts, and resources.
# This instance uses the builder pattern - you can add capabilities using
# either decorators (@mcp.tool) or direct methods (mcp.add_tool).

mcp = BuildMCPServer(
    name="calculator",
    version="1.0.0",
    description="A simple calculator server"
)


# ============================================================================
# Tool Registration - Method 1: Decorator Style
# ============================================================================
# Use @mcp.tool() to register functions as tools. The decorator approach
# keeps the tool definition and registration together, making code more readable.

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers together.

    Type annotations (int) are automatically converted to JSON Schema,
    ensuring clients send the correct data types.

    Args:
        a: First number to add
        b: Second number to add

    Returns:
        Sum of a and b

    Example:
        >>> add(5, 3)
        8
    """
    return a + b


@mcp.tool()
def multiply(a: float, b: float) -> float:
    """Multiply two numbers.

    Using float allows decimal numbers, giving more flexibility than int.

    Args:
        a: First number (multiplier)
        b: Second number (multiplicand)

    Returns:
        Product of a and b

    Example:
        >>> multiply(4.5, 2.0)
        9.0
    """
    return a * b


# ============================================================================
# Tool Registration - Method 2: Direct Registration
# ============================================================================
# Alternatively, define functions separately and register them explicitly.
# This is useful when:
# - The function comes from another module
# - You want to customize the tool name
# - You're registering third-party functions

def divide(a: float, b: float) -> float:
    """Divide a by b.

    This demonstrates error handling in tools. Raising exceptions
    is the correct way to handle invalid inputs - the framework
    will convert them to proper JSON-RPC error responses.

    Args:
        a: Numerator (dividend)
        b: Denominator (divisor)

    Returns:
        Result of division (a / b)

    Raises:
        ValueError: If denominator is zero

    Example:
        >>> divide(10, 2)
        5.0
        >>> divide(10, 0)
        ValueError: Cannot divide by zero
    """
    # Validate input before performing operation
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b


# Register the function with a custom description
mcp.add_tool("divide", divide, description="Divide two numbers")


# ============================================================================
# Prompt Registration
# ============================================================================
# Prompts are templates that guide LLM interactions. They can be retrieved
# by clients and used to standardize conversations.

@mcp.prompt()
def math_tutor(topic: str = "algebra") -> str:
    """Generate a math tutoring prompt.

    Prompts with parameters allow clients to customize the template.
    The default value makes the topic parameter optional.

    Args:
        topic: The math topic to focus on (default: "algebra")

    Returns:
        A formatted tutoring prompt string

    Example:
        >>> math_tutor("calculus")
        'You are a helpful math tutor specializing in calculus...'
    """
    return f"""You are a helpful math tutor specializing in {topic}.
Help the student understand concepts clearly with examples.
Be patient and encouraging."""


# ============================================================================
# Resource Registration
# ============================================================================
# Resources expose data via URIs. Clients can read resources to access
# configuration, schemas, or any other structured data.

@mcp.resource(uri="config://calculator")
def get_config() -> dict:
    """Get calculator configuration.

    Resources return structured data (dicts, lists) or strings.
    The URI scheme (config://) is just a convention - use any scheme
    that makes sense for your application.

    Returns:
        Configuration dictionary with server metadata

    Example:
        >>> get_config()
        {'name': 'calculator', 'version': '1.0.0', ...}
    """
    return {
        "name": "calculator",
        "version": "1.0.0",
        "supported_operations": ["add", "multiply", "divide"],
        "precision": 10
    }


# ============================================================================
# Server Execution
# ============================================================================

async def main():
    """Run the calculator server.

    This demonstrates the standard server lifecycle:
    1. Display server information
    2. Initialize the server (validates configuration)
    3. Run with a transport (stdio in this case)
    """
    # Display what was registered
    print("Starting Calculator MCP Server...")
    print(f"Registered tools: {mcp.list_tools()}")
    print(f"Registered prompts: {mcp.list_prompts()}")
    print(f"Registered resources: {mcp.list_resources()}")
    print()

    # Initialize the server - this must be called before running
    await mcp.initialize()

    # Run with stdio transport - blocks until server is stopped
    # The server will communicate via stdin/stdout using JSON-RPC 2.0
    await mcp.run_stdio()


if __name__ == "__main__":
    # Entry point - run the async main function
    asyncio.run(main())
