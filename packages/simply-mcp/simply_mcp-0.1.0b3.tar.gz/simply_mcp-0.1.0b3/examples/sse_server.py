#!/usr/bin/env python3
"""SSE (Server-Sent Events) Server Example for Simply-MCP.

This example demonstrates how to create an MCP server that runs over SSE
transport for real-time event streaming. It includes multiple tools, CORS
configuration, and demonstrates real-time updates to connected clients.

Usage:
    # Run with default settings (port 3000)
    python examples/sse_server.py

    # Run with custom port
    python examples/sse_server.py --port 8080

    # Run with custom host
    python examples/sse_server.py --host localhost --port 8080

    # Test the server:
    # 1. Connect to SSE stream (in a browser or with curl):
    curl -N http://localhost:3000/sse

    # 2. In another terminal, send requests:
    curl http://localhost:3000/
    curl http://localhost:3000/health
    curl -X POST http://localhost:3000/mcp \\
      -H "Content-Type: application/json" \\
      -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"echo","arguments":{"message":"Hello SSE!"}}}'

Requirements:
    - simply-mcp (with SSE transport dependencies)
    - aiohttp>=3.9.0

Features Demonstrated:
    - SSE transport for real-time streaming
    - CORS support for web clients
    - Multiple concurrent connections
    - Keep-alive mechanism
    - Event broadcasting to all clients
    - JSON-RPC 2.0 endpoint
    - Health check endpoint
    - Graceful shutdown handling
"""

import asyncio
import sys
from datetime import datetime

from simply_mcp import BuildMCPServer

# Create MCP server with SSE transport
mcp = BuildMCPServer(
    name="sse-demo-server",
    version="1.0.0",
    description="Demo MCP server with SSE transport for real-time streaming",
)


@mcp.tool()
def echo(message: str) -> str:
    """Echo a message back.

    This tool demonstrates basic SSE functionality. When called,
    the result is broadcast to all connected SSE clients.

    Args:
        message: Message to echo

    Returns:
        The same message
    """
    return f"Echo: {message}"


@mcp.tool()
def get_timestamp() -> str:
    """Get current server timestamp.

    Returns:
        Current timestamp in ISO format
    """
    return datetime.now().isoformat()


@mcp.tool()
def calculate(expression: str) -> str:
    """Evaluate a simple mathematical expression.

    Warning: Uses eval() - in production, use a proper parser.

    Args:
        expression: Mathematical expression to evaluate

    Returns:
        Result of the expression
    """
    try:
        # Note: In production, use a proper math parser instead of eval
        result = eval(expression, {"__builtins__": {}}, {})
        return f"{expression} = {result}"
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
def count_words(text: str) -> dict[str, int]:
    """Count words in a text.

    Args:
        text: Text to analyze

    Returns:
        Dictionary with word count statistics
    """
    words = text.split()
    return {
        "total_words": len(words),
        "unique_words": len(set(words)),
        "total_chars": len(text),
    }


@mcp.tool()
def generate_sequence(start: int, end: int, step: int = 1) -> list[int]:
    """Generate a sequence of numbers.

    Args:
        start: Start of sequence
        end: End of sequence
        step: Step size (default: 1)

    Returns:
        List of numbers in the sequence
    """
    return list(range(start, end, step))


def main() -> None:
    """Run the SSE server."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Run Simply-MCP SSE server demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default settings
  python sse_server.py

  # Run on custom port
  python sse_server.py --port 8080

  # Run on localhost only
  python sse_server.py --host localhost

  # Disable CORS
  python sse_server.py --no-cors

Testing with curl:
  # Connect to SSE stream (keep this running in one terminal)
  curl -N http://localhost:3000/sse

  # In another terminal, make requests:
  # Get server info
  curl http://localhost:3000/

  # Check health
  curl http://localhost:3000/health

  # Call echo tool (result will be broadcast to SSE clients)
  curl -X POST http://localhost:3000/mcp \\
    -H "Content-Type: application/json" \\
    -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"echo","arguments":{"message":"Hello SSE!"}}}'

Testing with JavaScript in browser:
  const eventSource = new EventSource('http://localhost:3000/sse');

  eventSource.addEventListener('connected', (e) => {
    console.log('Connected:', JSON.parse(e.data));
  });

  eventSource.addEventListener('mcp_result', (e) => {
    console.log('MCP Result:', JSON.parse(e.data));
  });

  eventSource.onerror = (error) => {
    console.error('SSE Error:', error);
  };
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

    # Display startup information
    print("=" * 70)
    print(f"Simply-MCP SSE Server - {mcp.server.config.server.name}")
    print("=" * 70)
    print(f"Version: {mcp.server.config.server.version}")
    print(f"Description: {mcp.server.config.server.description}")
    print("\nSSE Server Configuration:")
    print(f"  Host: {args.host}")
    print(f"  Port: {args.port}")
    print(f"  CORS: {'enabled' if args.cors else 'disabled'}")
    if args.cors and args.cors_origins:
        print(f"  CORS Origins: {', '.join(args.cors_origins)}")
    print("\nEndpoints:")
    print(f"  - http://{args.host}:{args.port}/ (server info)")
    print(f"  - http://{args.host}:{args.port}/health (health check)")
    print(f"  - http://{args.host}:{args.port}/sse (SSE stream)")
    print(f"  - http://{args.host}:{args.port}/mcp (JSON-RPC 2.0)")
    print("\nTools Available:")
    tools = ["echo", "get_timestamp", "calculate", "count_words", "generate_sequence"]
    for tool_name in tools:
        print(f"  - {tool_name}")
    print("\n" + "=" * 70)
    print("SSE Features:")
    print("  - Real-time event streaming to connected clients")
    print("  - Keep-alive pings every 30 seconds")
    print("  - Automatic reconnection support")
    print("  - Multiple concurrent connections")
    print("  - Event broadcasting for MCP results")
    print("=" * 70)
    print("\nServer is starting... Press Ctrl+C to stop")
    print("\nTo test SSE streaming:")
    print(f"  1. Run: curl -N http://{args.host}:{args.port}/sse")
    print("  2. In another terminal, make requests to /mcp")
    print("  3. See events appear in real-time!")
    print("=" * 70 + "\n")

    # Run server
    async def run_server() -> None:
        """Run the SSE server asynchronously."""
        try:
            await mcp.run_sse(
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
        asyncio.run(run_server())
    except KeyboardInterrupt:
        print("\nServer stopped.")


if __name__ == "__main__":
    main()
