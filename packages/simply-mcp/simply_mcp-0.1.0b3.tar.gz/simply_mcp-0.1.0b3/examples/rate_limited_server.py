#!/usr/bin/env python3
"""Example MCP server with rate limiting enabled.

This example demonstrates:
1. Creating an MCP server with rate limiting
2. Configuring rate limits (requests per minute and burst size)
3. Testing rate limiting with a client script
4. Handling rate limit errors (429 Too Many Requests)

Usage:
    # Start the server
    python examples/rate_limited_server.py

    # In another terminal, test with the client
    python examples/rate_limited_server.py --test

Rate Limiting Configuration:
    - Requests per minute: 30 (low for demonstration)
    - Burst size: 10 (allows 10 rapid requests before limiting)
    - Algorithm: Token bucket (smooth rate enforcement)
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add src to path for examples
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import aiohttp

from simply_mcp import BuildMCPServer
from simply_mcp.security.rate_limiter import RateLimiter
from simply_mcp.transports.http import HTTPTransport


# Define some example tools
def add(a: int, b: int) -> int:
    """Add two numbers together.

    Args:
        a: First number
        b: Second number

    Returns:
        Sum of a and b
    """
    return a + b


def multiply(a: int, b: int) -> int:
    """Multiply two numbers.

    Args:
        a: First number
        b: Second number

    Returns:
        Product of a and b
    """
    return a * b


def greet(name: str) -> str:
    """Greet someone by name.

    Args:
        name: Name to greet

    Returns:
        Greeting message
    """
    return f"Hello, {name}!"


async def run_server() -> None:
    """Run the MCP server with rate limiting enabled."""
    print("=" * 70)
    print("Rate-Limited MCP Server Example")
    print("=" * 70)

    # Create server using builder API
    mcp = BuildMCPServer(
        name="rate-limited-server",
        version="1.0.0",
        description="Example server with rate limiting",
    )

    # Register tools using builder API
    mcp.add_tool("add", add, description="Add two numbers")
    mcp.add_tool("multiply", multiply, description="Multiply two numbers")
    mcp.add_tool("greet", greet, description="Greet someone by name")

    # Initialize server
    await mcp.initialize()

    # Create rate limiter with aggressive limits for demonstration
    rate_limiter = RateLimiter(
        requests_per_minute=30,  # 30 requests per minute
        burst_size=10,  # Allow burst of 10 requests
        max_clients=100,  # Track up to 100 clients
        cleanup_interval=60,  # Cleanup every 60 seconds
        client_ttl=120,  # Keep client data for 2 minutes
    )

    print("\nRate Limiting Configuration:")
    print(f"  Requests per minute: {rate_limiter.requests_per_minute}")
    print(f"  Burst size: {rate_limiter.burst_size}")
    print(f"  Refill rate: {rate_limiter.refill_rate:.2f} requests/second")

    # Create HTTP transport with rate limiting
    transport = HTTPTransport(
        server=mcp.server,
        host="127.0.0.1",
        port=8080,
        cors_enabled=True,
        rate_limiter=rate_limiter,
    )

    print("\nStarting server...")
    await transport.start()

    print("\nServer is running on http://127.0.0.1:8080")
    print("\nAvailable endpoints:")
    print("  POST http://127.0.0.1:8080/mcp - MCP JSON-RPC endpoint")
    print("  GET  http://127.0.0.1:8080/health - Health check")
    print("  GET  http://127.0.0.1:8080/ - Server info")

    print("\nAvailable tools:")
    print("  - add(a, b) - Add two numbers")
    print("  - multiply(a, b) - Multiply two numbers")
    print("  - greet(name) - Greet someone")

    print("\nRate Limit Testing:")
    print("  1. First 10 requests will succeed (burst capacity)")
    print("  2. After burst, limited to ~0.5 requests/second (30/min)")
    print("  3. Rate-limited requests return 429 Too Many Requests")
    print("  4. Retry-After header indicates when to retry")

    print("\nTest with: python examples/rate_limited_server.py --test")
    print("\nPress Ctrl+C to stop...")

    try:
        # Keep server running
        while True:
            await asyncio.sleep(1)

            # Print stats every 10 seconds
            if asyncio.get_event_loop().time() % 10 < 1:
                stats = await rate_limiter.get_stats()
                if stats["total_requests"] > 0:
                    print(
                        f"\nRate Limiter Stats: "
                        f"Requests={stats['total_requests']}, "
                        f"Limited={stats['total_limited']} "
                        f"({stats['limit_rate']:.1f}%), "
                        f"Clients={stats['active_clients']}"
                    )

    except KeyboardInterrupt:
        print("\n\nShutting down...")

    finally:
        await transport.stop()
        print("Server stopped.")


async def test_rate_limiting() -> None:
    """Test the rate limiting by making rapid requests."""
    print("=" * 70)
    print("Rate Limiting Test Client")
    print("=" * 70)

    server_url = "http://127.0.0.1:8080/mcp"

    # Test 1: Burst capacity
    print("\nTest 1: Burst Capacity (should allow 10 rapid requests)")
    print("-" * 70)

    async with aiohttp.ClientSession() as session:
        success_count = 0
        rate_limited_count = 0

        for i in range(15):
            try:
                request = {
                    "jsonrpc": "2.0",
                    "id": i,
                    "method": "tools/call",
                    "params": {
                        "name": "add",
                        "arguments": {"a": i, "b": 1},
                    },
                }

                async with session.post(server_url, json=request) as resp:
                    if resp.status == 200:
                        success_count += 1
                        result = await resp.json()
                        print(f"  Request {i+1}: SUCCESS - Result: {result['result']}")
                    elif resp.status == 429:
                        rate_limited_count += 1
                        retry_after = resp.headers.get("Retry-After", "?")
                        print(
                            f"  Request {i+1}: RATE LIMITED "
                            f"(Retry-After: {retry_after}s)"
                        )
                    else:
                        print(f"  Request {i+1}: ERROR - Status {resp.status}")

            except Exception as e:
                print(f"  Request {i+1}: EXCEPTION - {e}")

        print(f"\nResults: {success_count} success, {rate_limited_count} rate limited")

    # Test 2: Steady state rate
    print("\n\nTest 2: Steady State Rate (spacing requests)")
    print("-" * 70)
    print("Making requests every 2.5 seconds (within rate limit)...")

    async with aiohttp.ClientSession() as session:
        for i in range(5):
            request = {
                "jsonrpc": "2.0",
                "id": 100 + i,
                "method": "tools/call",
                "params": {
                    "name": "greet",
                    "arguments": {"name": f"User{i}"},
                },
            }

            async with session.post(server_url, json=request) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    print(f"  Request {i+1}: SUCCESS - {result['result']}")
                else:
                    print(f"  Request {i+1}: Status {resp.status}")

            if i < 4:  # Don't sleep after last request
                await asyncio.sleep(2.5)

    # Test 3: List tools (should work normally)
    print("\n\nTest 3: List Tools (checking non-rate-limited endpoint)")
    print("-" * 70)

    async with aiohttp.ClientSession() as session:
        request = {
            "jsonrpc": "2.0",
            "id": 200,
            "method": "tools/list",
            "params": {},
        }

        async with session.post(server_url, json=request) as resp:
            if resp.status == 200:
                result = await resp.json()
                tools = result["result"]["tools"]
                print(f"  Found {len(tools)} tools:")
                for tool in tools:
                    print(f"    - {tool['name']}: {tool['description']}")
            else:
                print(f"  ERROR: Status {resp.status}")

    print("\n" + "=" * 70)
    print("Test completed!")
    print("=" * 70)


async def show_info() -> None:
    """Show server information."""
    print("=" * 70)
    print("Rate-Limited Server Info")
    print("=" * 70)

    server_url = "http://127.0.0.1:8080"

    try:
        async with aiohttp.ClientSession() as session:
            # Get server info
            async with session.get(f"{server_url}/") as resp:
                if resp.status == 200:
                    info = await resp.json()
                    print("\nServer Info:")
                    print(f"  Name: {info.get('name')}")
                    print(f"  Version: {info.get('version')}")
                    print(f"  Description: {info.get('description')}")
                    print(f"  Transport: {info.get('transport')}")
                    print(f"  Status: {info.get('status')}")

            # Get health
            async with session.get(f"{server_url}/health") as resp:
                if resp.status == 200:
                    health = await resp.json()
                    print("\nHealth Status:")
                    print(f"  Status: {health.get('status')}")
                    print(f"  Initialized: {health.get('initialized')}")
                    print(f"  Running: {health.get('running')}")
                    print(f"  Requests Handled: {health.get('requests_handled')}")

    except aiohttp.ClientConnectionError:
        print("\nERROR: Could not connect to server")
        print("Make sure the server is running:")
        print("  python examples/rate_limited_server.py")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Rate-limited MCP server example",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--test",
        action="store_true",
        help="Run test client instead of server",
    )

    parser.add_argument(
        "--info",
        action="store_true",
        help="Show server information",
    )

    args = parser.parse_args()

    if args.test:
        asyncio.run(test_rate_limiting())
    elif args.info:
        asyncio.run(show_info())
    else:
        asyncio.run(run_server())


if __name__ == "__main__":
    main()
