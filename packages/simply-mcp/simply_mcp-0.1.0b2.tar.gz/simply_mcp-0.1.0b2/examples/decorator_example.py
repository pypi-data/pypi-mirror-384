#!/usr/bin/env python3
"""Decorator API Example - Pythonic MCP Server Development

This example demonstrates the decorator API, which provides the most Pythonic
and intuitive way to create MCP servers. It showcases:

- Tool Registration: @tool() decorator for exposing functions as tools
- Prompt Templates: @prompt() decorator for creating reusable prompts
- Resource Publishing: @resource() decorator for serving data and content
- Pydantic Integration: Type-safe input validation with Pydantic models
- Class-Based Servers: @mcp_server decorator for organizing related tools
- Auto-Schema Generation: Automatic JSON Schema from Python type hints

Key Concepts:
    Decorator Pattern: Apply @tool() to any function to expose it as an MCP tool
    Global Server: Module-level decorators register to a global server instance
    Class-Based Server: @mcp_server creates an isolated server from a class
    Schema Generation: Type annotations automatically create JSON Schema
    Pydantic Models: Use for complex validation and nested data structures

Installation:
    # Basic installation
    pip install simply-mcp

    # With Pydantic for advanced validation
    pip install simply-mcp pydantic

Usage:
    # Run as a demo (shows registered tools)
    python examples/decorator_example.py

    # Run as an MCP server with stdio transport
    # (Modify main() to call run_stdio() instead of demo)

    # Test with MCP Inspector
    npx @anthropic-ai/mcp-inspector python examples/decorator_example.py

Examples Demonstrated:
    1. Simple tools with automatic schema generation
    2. Tools with Pydantic models for complex inputs
    3. Prompt templates with parameters
    4. Resources with different MIME types
    5. Class-based server organization with state

Expected Output:
    The demo prints information about registered tools, prompts, and resources,
    then tests some tool functionality to show how they work.

Learning Path:
    - Previous: simple_server.py (basic builder API)
    - Current: decorator_example.py (you are here)
    - Next: builder_chaining.py (advanced builder patterns)

See Also:
    - builder_basic.py - Builder API alternative
    - builder_pydantic.py - More Pydantic examples
    - production_server.py - Production-ready implementation

Requirements:
    - Python 3.10+
    - simply-mcp
    - pydantic (optional, for Pydantic examples)
"""

import asyncio
from typing import Optional

try:
    from pydantic import BaseModel, Field
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    print("Note: Pydantic not available. Pydantic examples will be skipped.")

from simply_mcp.api.decorators import tool, prompt, resource, mcp_server


# =============================================================================
# Example 1: Simple Tools with Auto-Schema Generation
# =============================================================================
# The @tool() decorator automatically:
# 1. Registers the function as an MCP tool
# 2. Generates JSON Schema from type annotations
# 3. Extracts description from the docstring
# 4. Handles parameter validation
#
# These tools register to the global server instance created by the framework.

@tool()
def add(a: int, b: int) -> int:
    """Add two numbers together.

    Args:
        a: First number
        b: Second number

    Returns:
        Sum of a and b
    """
    return a + b


@tool()
def multiply(x: float, y: float) -> float:
    """Multiply two numbers.

    Args:
        x: First number
        y: Second number

    Returns:
        Product of x and y
    """
    return x * y


@tool(name="custom_greet", description="Generate a custom greeting")
def greet(name: str, title: Optional[str] = None) -> str:
    """Generate a greeting with optional title.

    This demonstrates customizing tool name and description in the decorator.
    """
    if title:
        return f"Hello, {title} {name}!"
    return f"Hello, {name}!"


# =============================================================================
# Example 2: Pydantic Model Integration
# =============================================================================
# Pydantic models provide advanced validation features:
# - Field-level validation with min/max constraints
# - Custom validation logic
# - Nested models
# - Clear error messages for invalid inputs
#
# When using Pydantic models, the tool receives a validated model instance
# instead of raw parameters. This ensures data quality before processing.

if PYDANTIC_AVAILABLE:
    class SearchQuery(BaseModel):
        """Search query with validation."""
        query: str = Field(description="Search query text", min_length=1)
        limit: int = Field(default=10, ge=1, le=100, description="Maximum results")
        include_archived: bool = Field(default=False, description="Include archived items")

    @tool(input_schema=SearchQuery)
    def search(input: SearchQuery) -> list:
        """Search for items with advanced filtering.

        The input_schema parameter tells the framework to use a Pydantic model.
        All validation happens automatically before this function is called.

        Args:
            input: Validated SearchQuery model instance

        Returns:
            List of search results (limited by query.limit)
        """
        # Construct mock results - in production, this would query a database
        results = [
            f"Result 1 for '{input.query}'",
            f"Result 2 for '{input.query}'",
        ]

        # Conditionally include archived items based on the model field
        if input.include_archived:
            results.append("Archived result")

        # The limit constraint (1-100) is already validated by Pydantic
        return results[:input.limit]


# =============================================================================
# Example 3: Prompts with Auto-Detection
# =============================================================================
# Prompts are reusable templates that clients can retrieve and use.
# They're useful for:
# - Providing pre-configured instructions to LLMs
# - Standardizing common queries across applications
# - Offering guided workflows to users
#
# Parameters in prompts allow customization while maintaining structure.

@prompt()
def code_review(language: str = "python", style: str = "detailed") -> str:
    """Generate a code review prompt.

    Args:
        language: Programming language
        style: Review style (detailed, brief, security)

    Returns:
        Code review prompt text
    """
    return f"""Please review this {language} code with a {style} style.

Focus on:
- Code quality and best practices
- Potential bugs or issues
- Performance considerations
- Security implications

Provide constructive feedback and suggestions for improvement."""


@prompt(name="writing_prompt", description="Generate creative writing prompts")
def generate_writing_prompt(genre: str, word_count: int = 500) -> str:
    """Generate a creative writing prompt."""
    return f"""Write a {word_count}-word {genre} story that includes:
- An unexpected twist
- A character facing a moral dilemma
- A setting that influences the plot

Begin your story now..."""


# =============================================================================
# Example 4: Resources
# =============================================================================
# Resources expose data that clients can read via URI patterns.
# Common use cases:
# - Configuration data
# - Static content
# - API schemas
# - System statistics
#
# The uri parameter defines how clients access the resource.
# The mime_type helps clients understand how to process the content.

@resource(uri="config://app")
def get_config() -> dict:
    """Get application configuration.

    Returns:
        Application configuration dictionary
    """
    return {
        "version": "1.0.0",
        "debug": False,
        "features": {
            "advanced_search": True,
            "analytics": True,
        }
    }


@resource(uri="data://statistics", mime_type="text/plain")
def get_statistics() -> str:
    """Get system statistics.

    Returns:
        Statistics as plain text
    """
    return """System Statistics:
CPU Usage: 45%
Memory Usage: 62%
Disk Usage: 78%
Active Users: 42
Requests/min: 1,234
"""


@resource(uri="file:///schema.json", mime_type="application/json")
def get_schema() -> dict:
    """Get API schema.

    Returns:
        JSON Schema for the API
    """
    return {
        "type": "object",
        "properties": {
            "id": {"type": "integer"},
            "name": {"type": "string"},
            "email": {"type": "string", "format": "email"}
        },
        "required": ["id", "name"]
    }


# =============================================================================
# Example 5: Class-Based Server
# =============================================================================
# The @mcp_server decorator creates an isolated server from a class.
# Benefits of class-based servers:
# - State management: Instance variables persist across tool calls
# - Code organization: Related tools grouped together
# - Multiple servers: Each class creates a separate server instance
# - Cleaner architecture: Encapsulation and object-oriented design
#
# Class methods decorated with @tool(), @prompt(), or @resource()
# become part of that server's capabilities.

@mcp_server(name="calculator-server", version="2.0.0")
class CalculatorServer:
    """A calculator MCP server using class-based organization.

    This demonstrates how to:
    - Maintain state (calculation history) across tool calls
    - Organize related functionality in a class
    - Use instance methods as tools
    - Provide class-specific resources and prompts
    """

    def __init__(self):
        """Initialize the calculator with empty history.

        The history list persists across tool invocations, allowing
        the calculator to remember past calculations.
        """
        self.history = []

    @tool()
    def calculate(self, operation: str, a: float, b: float) -> float:
        """Perform a calculation and store in history.

        This tool demonstrates stateful operations - each calculation
        is recorded in the instance's history.

        Args:
            operation: Operation to perform (add, subtract, multiply, divide)
            a: First operand
            b: Second operand

        Returns:
            Result of the calculation

        Raises:
            ValueError: If operation is unknown or division by zero
        """
        # Perform the requested operation
        if operation == "add":
            result = a + b
        elif operation == "subtract":
            result = a - b
        elif operation == "multiply":
            result = a * b
        elif operation == "divide":
            if b == 0:
                raise ValueError("Division by zero")
            result = a / b
        else:
            raise ValueError(f"Unknown operation: {operation}")

        # Store this calculation in history (instance state)
        self.history.append({
            "operation": operation,
            "operands": [a, b],
            "result": result
        })
        return result

    @tool()
    def get_history(self) -> list:
        """Get calculation history.

        Returns:
            List of previous calculations
        """
        return self.history

    @tool()
    def clear_history(self) -> str:
        """Clear calculation history.

        Returns:
            Confirmation message
        """
        count = len(self.history)
        self.history.clear()
        return f"Cleared {count} calculations from history"

    @prompt()
    def help_prompt(self) -> str:
        """Generate help prompt for the calculator."""
        return """Calculator Server Help:

Available operations:
- add: Add two numbers
- subtract: Subtract second number from first
- multiply: Multiply two numbers
- divide: Divide first number by second

Example usage:
calculate("add", 5, 3) -> 8
calculate("multiply", 4, 7) -> 28

Use get_history() to view past calculations.
Use clear_history() to reset the history."""

    @resource(uri="config://calculator")
    def get_calculator_config(self) -> dict:
        """Get calculator configuration."""
        return {
            "precision": 10,
            "allow_complex": False,
            "history_limit": 100
        }


# =============================================================================
# Main Function - Demonstration Mode
# =============================================================================
# This main function demonstrates the decorator API by showing what was
# registered and testing some functionality. In a production environment,
# you would call initialize() and run_stdio() or run_http() instead.

async def main():
    """Main function to demonstrate the decorator API.

    This demo shows:
    - How to access the global server created by module-level decorators
    - How to retrieve registration statistics
    - How to list registered tools, prompts, and resources
    - How to test tool functionality directly
    - How to access class-based servers
    """
    print("=" * 80)
    print("Simply-MCP Decorator API Example")
    print("=" * 80)
    print()

    # Access the global server (used by module-level decorators)
    from simply_mcp.api.decorators import get_global_server

    global_server = get_global_server()
    print(f"Global Server: {global_server.config.server.name}")
    print()

    # Show registered components
    stats = global_server.registry.get_stats()
    print("Registered Components (Global Server):")
    print(f"  Tools: {stats['tools']}")
    print(f"  Prompts: {stats['prompts']}")
    print(f"  Resources: {stats['resources']}")
    print()

    # Show some tools
    print("Sample Tools:")
    for tool_config in global_server.registry.list_tools()[:3]:
        print(f"  - {tool_config.name}: {tool_config.description}")
    print()

    # Show prompts
    print("Sample Prompts:")
    for prompt_config in global_server.registry.list_prompts():
        print(f"  - {prompt_config.name}: {prompt_config.description}")
    print()

    # Show resources
    print("Sample Resources:")
    for resource_config in global_server.registry.list_resources():
        print(f"  - {resource_config.name} ({resource_config.uri})")
    print()

    # Access the class-based server
    calc_server = CalculatorServer.get_server()
    print(f"\nClass-Based Server: {calc_server.config.server.name}")
    calc_stats = calc_server.registry.get_stats()
    print(f"  Tools: {calc_stats['tools']}")
    print(f"  Prompts: {calc_stats['prompts']}")
    print(f"  Resources: {calc_stats['resources']}")
    print()

    # Test some tool functionality
    print("Testing Tools:")
    print(f"  add(5, 3) = {add(5, 3)}")
    print(f"  multiply(4.5, 2.0) = {multiply(4.5, 2.0)}")
    print(f"  greet('Alice', 'Dr') = {greet('Alice', 'Dr')}")
    print()

    if PYDANTIC_AVAILABLE:
        print("Testing Pydantic Tool:")
        query = SearchQuery(query="test", limit=5, include_archived=True)
        results = search(query)
        print(f"  search(query='test', limit=5, include_archived=True):")
        for result in results:
            print(f"    - {result}")
        print()

    # Test prompt generation
    print("Testing Prompts:")
    review_prompt = code_review("python", "security")
    print(f"  code_review('python', 'security'):")
    print(f"    {review_prompt[:100]}...")
    print()

    # Test resource access
    print("Testing Resources:")
    config = get_config()
    print(f"  get_config(): {config}")
    print()

    print("=" * 80)
    print("Example complete!")
    print()
    print("To use these servers, initialize and run with:")
    print("  await global_server.initialize()")
    print("  await global_server.run_stdio()")
    print()
    print("Or for the class-based server:")
    print("  calc_server = CalculatorServer.get_server()")
    print("  await calc_server.initialize()")
    print("  await calc_server.run_stdio()")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
