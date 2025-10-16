#!/usr/bin/env python3
"""Builder API Method Chaining Example.

This example demonstrates the fluent API style with method chaining
for building an MCP server.
"""

import asyncio
from simply_mcp import BuildMCPServer


async def main():
    """Run a server built with method chaining."""

    # Define handler functions
    def add(a: int, b: int) -> int:
        """Add two numbers."""
        return a + b

    def subtract(a: int, b: int) -> int:
        """Subtract b from a."""
        return a - b

    def greet(name: str, style: str = "formal") -> str:
        """Generate a greeting prompt."""
        if style == "formal":
            return f"Good day, {name}. How may I assist you?"
        else:
            return f"Hey {name}! What's up?"

    def get_status() -> dict:
        """Get server status."""
        return {
            "status": "running",
            "uptime": "1h 23m",
            "requests_handled": 42
        }

    # Build server with fluent API - everything chained!
    mcp = (
        BuildMCPServer(name="demo-server", version="2.0.0")
        .add_tool("add", add, description="Add two numbers")
        .add_tool("subtract", subtract, description="Subtract two numbers")
        .add_prompt("greet", greet, description="Generate a greeting", arguments=["name", "style"])
        .add_resource("status://server", get_status, name="server_status", mime_type="application/json")
        .configure(log_level="DEBUG")
    )

    print("Demo Server built with method chaining!")
    print(f"Tools: {', '.join(mcp.list_tools())}")
    print(f"Prompts: {', '.join(mcp.list_prompts())}")
    print(f"Resources: {', '.join(mcp.list_resources())}")
    print(f"Log level: {mcp.config.logging.level}")

    # Initialize and run (can also be chained!)
    await mcp.initialize()
    await mcp.run_stdio()


if __name__ == "__main__":
    asyncio.run(main())
