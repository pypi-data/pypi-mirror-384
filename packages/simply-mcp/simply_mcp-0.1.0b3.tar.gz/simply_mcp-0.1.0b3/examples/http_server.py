#!/usr/bin/env python3
"""HTTP Transport MCP Server Example

This example demonstrates an MCP server running over HTTP with JSON-RPC 2.0.
It shows the basics of HTTP transport without the advanced security features
(authentication, rate limiting) shown in production examples.

Features Demonstrated:
    - HTTP transport with JSON-RPC 2.0 protocol
    - CORS support for web clients
    - Multiple tools with different return types
    - Health check endpoint
    - Server info endpoint
    - Graceful shutdown handling
    - Custom port and host configuration
    - Command-line argument parsing

Installation:
    # Install with HTTP support
    pip install simply-mcp[http]

Usage:
    # Run with default settings (port 3000)
    python examples/http_server.py

    # Run with custom port
    python examples/http_server.py --port 8080

    # Run on localhost only
    python examples/http_server.py --host localhost --port 8080

    # Disable CORS
    python examples/http_server.py --no-cors

    # Development mode with auto-reload
    simply-mcp dev examples/http_server.py --transport http --port 3000

Testing:
    # Get server info
    curl http://localhost:3000/

    # Health check
    curl http://localhost:3000/health

    # List available tools
    curl -X POST http://localhost:3000/mcp \\
      -H "Content-Type: application/json" \\
      -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'

    # Call the add tool
    curl -X POST http://localhost:3000/mcp \\
      -H "Content-Type: application/json" \\
      -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"add","arguments":{"a":5,"b":3}}}'

Next Steps:
    For production deployments with authentication and rate limiting, see:
    - production_server.py - Full production features
    - authenticated_server.py - API key authentication
    - rate_limited_server.py - Rate limiting

Requirements:
    - simply-mcp[http]
    - aiohttp>=3.9.0
"""

import asyncio
import sys

from simply_mcp import BuildMCPServer


# ============================================================================
# Server Instance Creation
# ============================================================================
# Create the MCP server instance. This can be used with any transport
# (stdio, HTTP, SSE). The transport is specified when calling run methods.

mcp = BuildMCPServer(
    name="http-demo-server",
    version="1.0.0",
    description="Demo MCP server with HTTP transport",
)


# ============================================================================
# Tool Definitions
# ============================================================================
# These tools demonstrate different return types and error handling patterns
# that work seamlessly over HTTP with JSON-RPC 2.0 protocol.

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers together.

    Args:
        a: First number
        b: Second number

    Returns:
        Sum of a and b
    """
    return a + b


@mcp.tool()
def multiply(a: int, b: int) -> int:
    """Multiply two numbers together.

    Args:
        a: First number
        b: Second number

    Returns:
        Product of a and b
    """
    return a * b


@mcp.tool()
def divide(a: float, b: float) -> float:
    """Divide two numbers.

    This tool demonstrates error handling over HTTP. When a ValueError
    is raised, the framework automatically converts it to a JSON-RPC
    error response with appropriate status codes.

    Args:
        a: Numerator (dividend)
        b: Denominator (divisor)

    Returns:
        Result of a / b

    Raises:
        ValueError: If denominator is zero (becomes JSON-RPC error)
    """
    # Validate denominator before performing operation
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b


@mcp.tool()
def get_statistics() -> dict[str, int]:
    """Get server statistics.

    This demonstrates returning structured data (dictionaries) which
    are automatically serialized to JSON for HTTP responses.

    Returns:
        Dictionary with server statistics (mock data)
    """
    return {
        "tools_count": 5,
        "uptime_seconds": 3600,
        "requests_handled": 42,
    }


@mcp.tool()
def list_items() -> list[str]:
    """Get a list of sample items.

    This demonstrates returning lists, another common data structure
    that works seamlessly with JSON-RPC over HTTP.

    Returns:
        List of sample string items
    """
    return ["apple", "banana", "cherry", "date", "elderberry"]


# ============================================================================
# Command-Line Interface
# ============================================================================
# This section handles command-line arguments for flexible server configuration.

def main() -> None:
    """Run the HTTP server with configurable options.

    Parses command-line arguments and starts the server with the specified
    configuration. Handles graceful shutdown on Ctrl+C.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Run Simply-MCP HTTP server demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default settings
  python http_server.py

  # Run on custom port
  python http_server.py --port 8080

  # Run on localhost only
  python http_server.py --host localhost

  # Disable CORS
  python http_server.py --no-cors

  # Custom CORS origins
  python http_server.py --cors-origins http://localhost:3000 http://localhost:8080

Testing:
  # Get server info
  curl http://localhost:3000/

  # Check health
  curl http://localhost:3000/health

  # List tools
  curl -X POST http://localhost:3000/mcp \\
    -H "Content-Type: application/json" \\
    -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'

  # Call add tool
  curl -X POST http://localhost:3000/mcp \\
    -H "Content-Type: application/json" \\
    -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"add","arguments":{"a":5,"b":3}}}'
        """,
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=3000,
        help="Port to bind to (default: 3000)",
    )
    parser.add_argument(
        "--cors/--no-cors",
        default=True,
        help="Enable/disable CORS (default: enabled)",
    )
    parser.add_argument(
        "--cors-origins",
        type=str,
        nargs="*",
        default=None,
        help="Allowed CORS origins (default: all)",
    )

    args = parser.parse_args()

    # ========================================================================
    # Startup Information Display
    # ========================================================================
    # Display comprehensive server configuration to help users understand
    # what's running and how to access it.

    print("=" * 70)
    print(f"Simply-MCP HTTP Server - {mcp.server.config.server.name}")
    print("=" * 70)
    print(f"Version: {mcp.server.config.server.version}")
    print(f"Description: {mcp.server.config.server.description}")
    print("\nHTTP Server Configuration:")
    print(f"  Host: {args.host}")
    print(f"  Port: {args.port}")
    print(f"  CORS: {'enabled' if args.cors else 'disabled'}")
    if args.cors and args.cors_origins:
        print(f"  CORS Origins: {', '.join(args.cors_origins)}")
    print("\nEndpoints:")
    print(f"  - http://{args.host}:{args.port}/ (server info)")
    print(f"  - http://{args.host}:{args.port}/health (health check)")
    print(f"  - http://{args.host}:{args.port}/mcp (JSON-RPC 2.0)")
    print("\nTools Available:")
    for tool_name in ["add", "multiply", "divide", "get_statistics", "list_items"]:
        print(f"  - {tool_name}")
    print("\n" + "=" * 70)
    print("Server is starting... Press Ctrl+C to stop")
    print("=" * 70 + "\n")

    # ========================================================================
    # Server Execution
    # ========================================================================
    # Run the server with HTTP transport. The run_http() method handles:
    # - Creating an aiohttp web application
    # - Setting up JSON-RPC 2.0 endpoints
    # - Configuring CORS middleware
    # - Starting the HTTP server

    async def run_server() -> None:
        """Run the HTTP server asynchronously.

        This wrapper handles exceptions and provides clean shutdown.
        """
        try:
            # Start the HTTP server - this blocks until shutdown
            await mcp.run_http(
                host=args.host,
                port=args.port,
                cors_enabled=args.cors,
                cors_origins=args.cors_origins,
            )
        except KeyboardInterrupt:
            print("\n\nShutting down gracefully...")
        except Exception as e:
            print(f"\nError: {e}", file=sys.stderr)
            sys.exit(1)

    try:
        # Run the async server
        asyncio.run(run_server())
    except KeyboardInterrupt:
        print("\nServer stopped.")


if __name__ == "__main__":
    main()
