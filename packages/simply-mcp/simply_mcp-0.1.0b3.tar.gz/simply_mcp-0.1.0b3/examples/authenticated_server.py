#!/usr/bin/env python3
"""Authenticated MCP Server Example - API Key Authentication

This example demonstrates how to secure an MCP server with API key authentication.
It shows the complete setup for:

- API Key Authentication: Secure endpoints with API keys
- Multiple Authentication Methods: Support Bearer tokens and X-API-Key headers
- HTTP Transport: Serve MCP over HTTP with authentication middleware
- Error Handling: Proper 401 Unauthorized responses for invalid/missing keys
- Best Practices: Environment-based configuration for production

Key Features Demonstrated:
    - Creating an APIKeyAuthProvider with multiple valid keys
    - Integrating authentication with HTTPTransport
    - Two authentication header formats (Authorization: Bearer and X-API-Key)
    - Automatic request validation and rejection
    - Security logging for authentication events

Installation:
    # Install with HTTP and security support
    pip install simply-mcp[http,security]

Usage:
    # Start the server (binds to 0.0.0.0:8000)
    python examples/authenticated_server.py

    # Test with valid API key (Bearer token)
    curl -X POST http://localhost:8000/mcp \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer test-key-12345" \
      -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}'

    # Test with X-API-Key header (alternative format)
    curl -X POST http://localhost:8000/mcp \
      -H "Content-Type: application/json" \
      -H "X-API-Key: test-key-12345" \
      -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}'

    # Test with invalid key (returns 401 Unauthorized)
    curl -X POST http://localhost:8000/mcp \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer wrong-key" \
      -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}'

    # Test without authentication (returns 401 Unauthorized)
    curl -X POST http://localhost:8000/mcp \
      -H "Content-Type: application/json" \
      -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}'

Production Deployment:
    # Use environment variables for API keys (recommended)
    export MCP_API_KEYS="key1,key2,key3"
    python examples/authenticated_server.py

Security Notes:
    - Never hardcode API keys in production code
    - Use environment variables or secure configuration management
    - Rotate API keys regularly
    - Use HTTPS in production to encrypt keys in transit
    - Consider rate limiting alongside authentication (see rate_limited_server.py)
    - Log authentication failures for security monitoring

Expected Output:
    Server starts and displays valid API keys for testing.
    Returns 200 OK for authenticated requests, 401 for unauthenticated.

Learning Path:
    - Previous: http_server.py (basic HTTP transport)
    - Current: authenticated_server.py (you are here)
    - Next: rate_limited_server.py (rate limiting)

See Also:
    - rate_limited_server.py - Add rate limiting
    - production_server.py - Combined security features
    - http_server.py - HTTP basics without auth

Requirements:
    - Python 3.10+
    - simply-mcp[http,security]
    - aiohttp>=3.9.0
"""

import asyncio
import logging

from simply_mcp import BuildMCPServer
from simply_mcp.security.auth import APIKeyAuthProvider
from simply_mcp.transports.http import HTTPTransport


# ============================================================================
# Logging Configuration
# ============================================================================
# Configure logging to track authentication events and server operations.
# In production, consider using structured logging (JSON format).

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


# ============================================================================
# Main Server Setup
# ============================================================================

def main() -> None:
    """Run authenticated MCP server example.

    This function demonstrates the complete lifecycle:
    1. Create MCP server instance
    2. Register tools
    3. Initialize server
    4. Create authentication provider
    5. Create HTTP transport with authentication
    6. Start server and handle shutdown
    """

    async def run() -> None:
        """Async server runner with authentication setup."""

        # ====================================================================
        # Server Creation and Tool Registration
        # ====================================================================
        # Create the MCP server instance with identifying information

        mcp = BuildMCPServer(
            name="authenticated-mcp-server",
            version="1.0.0",
            description="Example server with API key authentication"
        )

        # Register example tools - these will be protected by authentication
        @mcp.tool()
        def greet(name: str = "World") -> str:
            """Greet a user by name.

            Args:
                name: Name to greet

            Returns:
                Greeting message
            """
            return f"Hello, {name}!"

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

        # ====================================================================
        # Server Initialization
        # ====================================================================
        await mcp.initialize()

        # ====================================================================
        # Authentication Provider Setup
        # ====================================================================
        # Create the API key authentication provider with valid keys.
        # IMPORTANT: In production, NEVER hardcode keys in source code.
        # Instead, load from environment variables:
        #   import os
        #   api_keys = os.getenv("MCP_API_KEYS", "").split(",")

        api_keys = [
            "test-key-12345",  # Development key (example only)
            "prod-key-67890",  # Production key (example only)
        ]

        auth_provider = APIKeyAuthProvider(api_keys=api_keys)

        logger.info("=" * 60)
        logger.info("MCP Server with API Key Authentication")
        logger.info("=" * 60)
        logger.info("")
        logger.info("Valid API keys for testing:")
        for key in api_keys:
            logger.info(f"  - {key}")
        logger.info("")
        logger.info("Use one of these keys in your requests:")
        logger.info("  Authorization: Bearer <api_key>")
        logger.info("  OR")
        logger.info("  X-API-Key: <api_key>")
        logger.info("")
        logger.info("=" * 60)

        # ====================================================================
        # HTTP Transport with Authentication Middleware
        # ====================================================================
        # Create HTTP transport and inject the authentication provider.
        # The transport will automatically validate API keys for all requests
        # before passing them to the MCP server.

        transport = HTTPTransport(
            server=mcp.server,
            host="0.0.0.0",  # Bind to all interfaces
            port=8000,
            cors_enabled=True,  # Enable CORS for web clients
            auth_provider=auth_provider,  # Inject authentication
        )

        # ====================================================================
        # Server Startup
        # ====================================================================
        await transport.start()

        logger.info("")
        logger.info("Server started successfully!")
        logger.info("")
        logger.info("Test commands:")
        logger.info("")
        logger.info("1. List tools (with valid key):")
        logger.info('   curl -X POST http://localhost:8000/mcp \\')
        logger.info('     -H "Content-Type: application/json" \\')
        logger.info('     -H "Authorization: Bearer test-key-12345" \\')
        logger.info('     -d \'{"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}\'')
        logger.info("")
        logger.info("2. Call greet tool:")
        logger.info('   curl -X POST http://localhost:8000/mcp \\')
        logger.info('     -H "Content-Type: application/json" \\')
        logger.info('     -H "X-API-Key: test-key-12345" \\')
        logger.info(
            '     -d \'{"jsonrpc": "2.0", "id": 2, "method": "tools/call", '
            '"params": {"name": "greet", "arguments": {"name": "Alice"}}}\''
        )
        logger.info("")
        logger.info("3. Test without authentication (should fail):")
        logger.info('   curl -X POST http://localhost:8000/mcp \\')
        logger.info('     -H "Content-Type: application/json" \\')
        logger.info('     -d \'{"jsonrpc": "2.0", "id": 3, "method": "tools/list", "params": {}}\'')
        logger.info("")
        logger.info("Press Ctrl+C to stop the server")
        logger.info("=" * 60)

        # ====================================================================
        # Server Runtime Loop
        # ====================================================================
        # Keep the server running until interrupted by the user

        try:
            # Infinite loop - server handles requests in background
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            # Graceful shutdown on Ctrl+C
            logger.info("\nShutting down server...")
            await transport.stop()
            logger.info("Server stopped")

    # ========================================================================
    # Entry Point
    # ========================================================================
    # Run the async server function
    asyncio.run(run())


if __name__ == "__main__":
    main()
