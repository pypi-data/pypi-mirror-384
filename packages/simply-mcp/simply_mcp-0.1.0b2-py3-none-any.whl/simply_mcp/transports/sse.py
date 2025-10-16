"""Server-Sent Events (SSE) transport for MCP servers.

This module provides an SSE transport implementation for MCP servers,
allowing real-time event streaming to web clients using the SSE protocol.
"""

import asyncio
import json
import uuid
from typing import Any

from aiohttp import web

from simply_mcp.core.config import SimplyMCPConfig
from simply_mcp.core.logger import get_logger
from simply_mcp.core.server import SimplyMCPServer
from simply_mcp.transports.middleware import create_middleware_stack

logger = get_logger(__name__)


class SSEConnection:
    """Represents an SSE connection to a client.

    Manages a single SSE connection including message queue and
    connection state.

    Attributes:
        connection_id: Unique connection identifier
        response: The SSE response stream
        queue: Message queue for this connection
        connected: Whether the connection is active
    """

    def __init__(
        self,
        connection_id: str,
        response: web.StreamResponse,
    ) -> None:
        """Initialize SSE connection.

        Args:
            connection_id: Unique connection identifier
            response: The SSE stream response
        """
        self.connection_id = connection_id
        self.response = response
        self.queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self.connected = True

    async def send_event(
        self,
        event_type: str,
        data: Any,
        event_id: str | None = None,
    ) -> None:
        """Send an event to the client.

        Args:
            event_type: Event type (e.g., "message", "tool_result")
            data: Event data (will be JSON encoded)
            event_id: Optional event ID
        """
        if not self.connected:
            return

        try:
            # Format SSE event
            message = ""

            if event_id:
                message += f"id: {event_id}\n"

            message += f"event: {event_type}\n"

            # Encode data as JSON
            json_data = json.dumps(data)
            message += f"data: {json_data}\n\n"

            # Send to client
            await self.response.write(message.encode("utf-8"))

        except Exception as e:
            logger.error(
                f"Error sending SSE event: {e}",
                extra={
                    "context": {
                        "connection_id": self.connection_id,
                        "event_type": event_type,
                        "error": str(e),
                    }
                },
            )
            self.connected = False

    async def send_ping(self) -> None:
        """Send keep-alive ping to client."""
        if not self.connected:
            return

        try:
            # Send comment as keep-alive
            await self.response.write(b": ping\n\n")
        except Exception as e:
            logger.debug(
                f"Error sending ping: {e}",
                extra={
                    "context": {
                        "connection_id": self.connection_id,
                        "error": str(e),
                    }
                },
            )
            self.connected = False

    def close(self) -> None:
        """Close the connection."""
        self.connected = False


class SSETransport:
    """SSE transport for real-time MCP streaming.

    Provides Server-Sent Events (SSE) interface for MCP servers, enabling
    real-time event streaming to web clients. Supports multiple concurrent
    connections with keep-alive mechanisms.

    Attributes:
        server: The MCP server instance
        host: Host to bind to (default: 0.0.0.0)
        port: Port to bind to (default: 3000)
        cors_enabled: Whether CORS is enabled
        cors_origins: Allowed CORS origins
        app: The aiohttp application
        runner: The aiohttp app runner
        connections: Active SSE connections

    Example:
        >>> server = SimplyMCPServer()
        >>> await server.initialize()
        >>> transport = SSETransport(server, port=8080)
        >>> await transport.start()
    """

    def __init__(
        self,
        server: SimplyMCPServer,
        host: str = "0.0.0.0",
        port: int = 3000,
        cors_enabled: bool = True,
        cors_origins: list[str] | None = None,
        keepalive_interval: int = 30,
        auth_provider: Any | None = None,
        rate_limiter: Any | None = None,
    ) -> None:
        """Initialize SSE transport.

        Args:
            server: The MCP server instance
            host: Host to bind to
            port: Port to bind to
            cors_enabled: Whether to enable CORS
            cors_origins: Allowed CORS origins or None for all (*)
            keepalive_interval: Interval for keep-alive pings (seconds)
            auth_provider: Optional authentication provider
            rate_limiter: Optional rate limiter
        """
        self.server = server
        self.host = host
        self.port = port
        self.cors_enabled = cors_enabled
        self.cors_origins = cors_origins
        self.keepalive_interval = keepalive_interval
        self.auth_provider = auth_provider
        self.rate_limiter = rate_limiter
        self.app: web.Application | None = None
        self.runner: web.AppRunner | None = None
        self._site: web.TCPSite | None = None
        self.connections: set[SSEConnection] = set()
        self._keepalive_task: asyncio.Task[None] | None = None

        logger.info(
            f"Created SSE transport: {host}:{port}",
            extra={
                "context": {
                    "host": host,
                    "port": port,
                    "cors_enabled": cors_enabled,
                    "keepalive_interval": keepalive_interval,
                    "auth_enabled": auth_provider is not None,
                    "rate_limit_enabled": rate_limiter is not None,
                }
            },
        )

    async def start(self) -> None:
        """Start SSE server.

        Sets up the aiohttp application with middleware, routes, and
        starts listening for SSE connections.

        Raises:
            RuntimeError: If server is already running
        """
        if self.app is not None:
            raise RuntimeError("SSE transport already started")

        logger.info("Starting SSE transport")

        # Create middleware stack
        middlewares = create_middleware_stack(
            cors_enabled=self.cors_enabled,
            cors_origins=self.cors_origins,
            logging_enabled=True,
            rate_limit_enabled=False,
        )

        # Add rate limiting middleware if configured
        if self.rate_limiter is not None:
            from simply_mcp.transports.middleware import RateLimitMiddleware

            rate_middleware = RateLimitMiddleware(rate_limiter=self.rate_limiter)
            middlewares.append(rate_middleware)

            # Start cleanup task
            self.rate_limiter.start_cleanup()

            logger.info(
                "Rate limiting enabled for SSE transport",
                extra={
                    "context": {
                        "requests_per_minute": self.rate_limiter.requests_per_minute,
                        "burst_size": self.rate_limiter.burst_size,
                    }
                },
            )

        # Add authentication middleware if configured
        if self.auth_provider is not None:
            from simply_mcp.transports.middleware import AuthMiddleware

            auth_middleware = AuthMiddleware(self.auth_provider)
            middlewares.append(auth_middleware)

            logger.info(
                "Authentication enabled for SSE transport",
                extra={
                    "context": {
                        "auth_type": getattr(
                            self.auth_provider, "__class__", type(self.auth_provider)
                        ).__name__
                    }
                },
            )

        # Create aiohttp application
        self.app = web.Application(middlewares=middlewares)

        # Setup routes
        self.app.router.add_get("/sse", self.handle_sse)
        self.app.router.add_post("/mcp", self.handle_mcp_request)
        self.app.router.add_get("/health", self.handle_health)
        self.app.router.add_get("/", self.handle_root)

        # Create and start runner
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()

        # Create TCP site
        self._site = web.TCPSite(self.runner, self.host, self.port)
        await self._site.start()

        # Start keep-alive task
        self._keepalive_task = asyncio.create_task(self._keepalive_loop())

        logger.info(
            f"SSE server started on http://{self.host}:{self.port}",
            extra={
                "context": {
                    "host": self.host,
                    "port": self.port,
                    "endpoints": ["/sse", "/mcp", "/health", "/"],
                }
            },
        )

    async def stop(self) -> None:
        """Stop SSE server gracefully.

        Closes all connections and cleans up resources.
        """
        logger.info("Stopping SSE transport")

        # Stop rate limiter cleanup if enabled
        if self.rate_limiter is not None:
            await self.rate_limiter.stop_cleanup()

        # Cancel keep-alive task
        if self._keepalive_task:
            self._keepalive_task.cancel()
            try:
                await self._keepalive_task
            except asyncio.CancelledError:
                pass
            self._keepalive_task = None

        # Close all SSE connections
        for conn in list(self.connections):
            conn.close()
        self.connections.clear()

        # Stop site first
        if self._site:
            await self._site.stop()
            self._site = None

        # Then stop runner
        if self.runner:
            await self.runner.cleanup()
            self.runner = None

        self.app = None

        logger.info("SSE transport stopped")

    async def handle_root(self, request: web.Request) -> web.Response:
        """Handle root endpoint (/).

        Provides basic server information and API documentation.

        Args:
            request: HTTP request

        Returns:
            JSON response with server info
        """
        info = {
            "name": self.server.config.server.name,
            "version": self.server.config.server.version,
            "description": self.server.config.server.description,
            "transport": "sse",
            "endpoints": {
                "/sse": "Server-Sent Events stream (GET)",
                "/mcp": "MCP JSON-RPC endpoint (POST)",
                "/health": "Health check endpoint (GET)",
            },
            "status": "running",
            "active_connections": len(self.connections),
        }

        return web.json_response(info)

    async def handle_health(self, request: web.Request) -> web.Response:
        """Handle health check endpoint (/health).

        Returns server health status and connection metrics.

        Args:
            request: HTTP request

        Returns:
            JSON response with health status
        """
        # For SSE transport, we consider the server healthy if it's initialized
        # (running state is only relevant for stdio transport with lifespan)
        is_healthy = self.server.is_initialized

        health = {
            "status": "healthy" if is_healthy else "stopped",
            "initialized": self.server.is_initialized,
            "running": self.server.is_running,
            "requests_handled": self.server.request_count,
            "active_connections": len(self.connections),
            "components": self.server.registry.get_stats(),
        }

        status = 200 if is_healthy else 503

        return web.json_response(health, status=status)

    async def handle_sse(self, request: web.Request) -> web.StreamResponse:
        """Handle SSE connections.

        Establishes an SSE connection with the client and maintains it
        for real-time event streaming.

        Args:
            request: HTTP request

        Returns:
            SSE stream response
        """
        connection_id = f"sse-{uuid.uuid4().hex[:8]}"

        logger.info(
            f"New SSE connection: {connection_id}",
            extra={
                "context": {
                    "connection_id": connection_id,
                    "remote": request.remote or "unknown",
                }
            },
        )

        # Create SSE response
        response = web.StreamResponse()
        response.headers["Content-Type"] = "text/event-stream"
        response.headers["Cache-Control"] = "no-cache"
        response.headers["Connection"] = "keep-alive"

        await response.prepare(request)

        # Create connection object
        connection = SSEConnection(connection_id, response)
        self.connections.add(connection)

        try:
            # Send connection established event
            await connection.send_event(
                "connected",
                {
                    "connection_id": connection_id,
                    "server": self.server.config.server.name,
                    "version": self.server.config.server.version,
                },
            )

            # Keep connection alive
            while connection.connected:
                await asyncio.sleep(1)

        except asyncio.CancelledError:
            logger.debug(f"SSE connection cancelled: {connection_id}")

        except Exception as e:
            logger.error(
                f"Error in SSE connection: {e}",
                extra={
                    "context": {
                        "connection_id": connection_id,
                        "error": str(e),
                    }
                },
            )

        finally:
            # Clean up connection
            connection.close()
            self.connections.discard(connection)

            logger.info(
                f"SSE connection closed: {connection_id}",
                extra={
                    "context": {
                        "connection_id": connection_id,
                        "active_connections": len(self.connections),
                    }
                },
            )

        return response

    async def handle_mcp_request(self, request: web.Request) -> web.Response:
        """Handle MCP JSON-RPC requests and broadcast results.

        This endpoint accepts MCP requests and broadcasts the results
        to all connected SSE clients.

        Args:
            request: HTTP request with JSON-RPC payload

        Returns:
            JSON-RPC response
        """
        try:
            # Parse JSON body
            try:
                body = await request.json()
            except json.JSONDecodeError as e:
                return web.json_response(
                    {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {
                            "code": -32700,
                            "message": "Parse error",
                            "data": str(e),
                        },
                    },
                    status=400,
                )

            # Validate JSON-RPC structure
            request_id = body.get("id")
            method = body.get("method")
            params = body.get("params", {})

            # Process request
            result = await self._handle_method(method, params)

            # Broadcast result to SSE clients
            await self.broadcast_event(
                "mcp_result",
                {
                    "method": method,
                    "result": result,
                },
            )

            # Return response
            return web.json_response(
                {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": result,
                }
            )

        except Exception as e:
            logger.error(
                f"Error handling MCP request: {e}",
                extra={
                    "context": {
                        "error": str(e),
                        "error_type": type(e).__name__,
                    }
                },
            )

            return web.json_response(
                {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32603,
                        "message": "Internal error",
                        "data": str(e),
                    },
                },
                status=500,
            )

    async def _handle_method(self, method: str, params: dict[str, Any]) -> Any:
        """Route MCP method to appropriate handler.

        Args:
            method: MCP method name
            params: Method parameters

        Returns:
            Method result

        Raises:
            ValueError: If method is not supported
        """
        if method == "tools/list":
            tools = self.server.registry.list_tools()
            return {"tools": tools}

        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            if not tool_name:
                raise ValueError("Tool name is required")

            tool_config = self.server.registry.get_tool(tool_name)
            if not tool_config:
                raise ValueError(f"Tool not found: {tool_name}")

            handler = tool_config.handler
            result = handler(**arguments)

            if asyncio.iscoroutine(result):
                result = await result

            return {"result": result}

        else:
            raise ValueError(f"Unknown method: {method}")

    async def broadcast_event(
        self,
        event_type: str,
        data: Any,
        event_id: str | None = None,
    ) -> None:
        """Broadcast an event to all connected clients.

        Args:
            event_type: Event type
            data: Event data
            event_id: Optional event ID
        """
        if not self.connections:
            return

        # Send to all connections
        for connection in list(self.connections):
            try:
                await connection.send_event(event_type, data, event_id)
            except Exception as e:
                logger.error(
                    f"Error broadcasting to connection: {e}",
                    extra={
                        "context": {
                            "connection_id": connection.connection_id,
                            "error": str(e),
                        }
                    },
                )

    async def _keepalive_loop(self) -> None:
        """Keep-alive loop to ping all connections periodically."""
        logger.info("Keep-alive loop started")

        try:
            while True:
                await asyncio.sleep(self.keepalive_interval)

                # Ping all connections
                for connection in list(self.connections):
                    await connection.send_ping()

                # Remove disconnected connections
                disconnected = [c for c in self.connections if not c.connected]
                for conn in disconnected:
                    self.connections.discard(conn)

                if disconnected:
                    logger.debug(
                        f"Removed {len(disconnected)} disconnected connections",
                        extra={
                            "context": {
                                "removed": len(disconnected),
                                "active": len(self.connections),
                            }
                        },
                    )

        except asyncio.CancelledError:
            logger.info("Keep-alive loop cancelled")
            raise


async def create_sse_transport(
    server: SimplyMCPServer,
    config: SimplyMCPConfig | None = None,
) -> SSETransport:
    """Create and configure SSE transport.

    This is a convenience function that creates an SSE transport
    with configuration from SimplyMCPConfig.

    Args:
        server: MCP server instance
        config: Optional configuration (uses server config if not provided)

    Returns:
        Configured SSE transport

    Example:
        >>> server = SimplyMCPServer()
        >>> await server.initialize()
        >>> transport = await create_sse_transport(server)
        >>> await transport.start()
    """
    if config is None:
        config = server.config

    # Create rate limiter if configured
    rate_limiter = None
    if config.rate_limit.enabled:
        from simply_mcp.security import RateLimiter

        rate_limiter = RateLimiter(
            requests_per_minute=config.rate_limit.requests_per_minute,
            burst_size=config.rate_limit.burst_size,
        )

    # Create authentication provider if configured
    auth_provider = None
    if config.auth.enabled:
        from simply_mcp.security.auth import create_auth_provider

        auth_provider = create_auth_provider(
            auth_type=config.auth.type,
            api_keys=config.auth.api_keys,
            oauth_config=config.auth.oauth_config,
            jwt_config=config.auth.jwt_config,
        )

    transport = SSETransport(
        server=server,
        host=config.transport.host,
        port=config.transport.port,
        cors_enabled=config.transport.cors_enabled,
        cors_origins=config.transport.cors_origins,
        auth_provider=auth_provider,
        rate_limiter=rate_limiter,
    )

    return transport


__all__ = ["SSETransport", "SSEConnection", "create_sse_transport"]
