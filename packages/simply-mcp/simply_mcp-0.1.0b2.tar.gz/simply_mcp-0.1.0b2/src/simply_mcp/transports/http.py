"""HTTP transport for MCP servers.

This module provides an HTTP transport implementation for MCP servers,
allowing them to be accessed via RESTful HTTP endpoints with JSON-RPC 2.0
message handling.
"""

import asyncio
import json
from typing import Any

from aiohttp import web

from simply_mcp.core.config import SimplyMCPConfig
from simply_mcp.core.logger import get_logger
from simply_mcp.core.server import SimplyMCPServer
from simply_mcp.transports.middleware import create_middleware_stack

logger = get_logger(__name__)


class HTTPTransport:
    """HTTP transport for MCP servers.

    Provides a RESTful HTTP interface for MCP servers using JSON-RPC 2.0
    message protocol. Supports CORS, health checks, and graceful shutdown.

    Attributes:
        server: The MCP server instance
        host: Host to bind to (default: 0.0.0.0)
        port: Port to bind to (default: 3000)
        cors_enabled: Whether CORS is enabled
        cors_origins: Allowed CORS origins
        app: The aiohttp application
        runner: The aiohttp app runner

    Example:
        >>> server = SimplyMCPServer()
        >>> await server.initialize()
        >>> transport = HTTPTransport(server, port=8080)
        >>> await transport.start()
    """

    def __init__(
        self,
        server: SimplyMCPServer,
        host: str = "0.0.0.0",
        port: int = 3000,
        cors_enabled: bool = True,
        cors_origins: list[str] | None = None,
        auth_provider: Any | None = None,
        rate_limiter: Any | None = None,
    ) -> None:
        """Initialize HTTP transport.

        Args:
            server: The MCP server instance
            host: Host to bind to
            port: Port to bind to
            cors_enabled: Whether to enable CORS
            cors_origins: Allowed CORS origins or None for all (*)
            auth_provider: Optional authentication provider
            rate_limiter: Optional rate limiter
        """
        self.server = server
        self.host = host
        self.port = port
        self.cors_enabled = cors_enabled
        self.cors_origins = cors_origins
        self.auth_provider = auth_provider
        self.rate_limiter = rate_limiter
        self.app: web.Application | None = None
        self.runner: web.AppRunner | None = None
        self._site: web.TCPSite | None = None

        logger.info(
            f"Created HTTP transport: {host}:{port}",
            extra={
                "context": {
                    "host": host,
                    "port": port,
                    "cors_enabled": cors_enabled,
                    "auth_enabled": auth_provider is not None,
                    "rate_limit_enabled": rate_limiter is not None,
                }
            },
        )

    async def start(self) -> None:
        """Start HTTP server.

        Sets up the aiohttp application with middleware, routes, and
        starts listening for HTTP requests.

        Raises:
            RuntimeError: If server is already running
        """
        if self.app is not None:
            raise RuntimeError("HTTP transport already started")

        logger.info("Starting HTTP transport")

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
                "Rate limiting enabled for HTTP transport",
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
                "Authentication enabled for HTTP transport",
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
        self.app.router.add_post("/mcp", self.handle_mcp_request)
        self.app.router.add_get("/health", self.handle_health)
        self.app.router.add_get("/", self.handle_root)

        # Create and start runner
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()

        # Create TCP site
        self._site = web.TCPSite(self.runner, self.host, self.port)
        await self._site.start()

        logger.info(
            f"HTTP server started on http://{self.host}:{self.port}",
            extra={
                "context": {
                    "host": self.host,
                    "port": self.port,
                    "endpoints": ["/mcp", "/health", "/"],
                }
            },
        )

    async def stop(self) -> None:
        """Stop HTTP server gracefully.

        Closes all connections and cleans up resources.
        """
        logger.info("Stopping HTTP transport")

        # Stop rate limiter cleanup if enabled
        if self.rate_limiter is not None:
            await self.rate_limiter.stop_cleanup()

        if self._site:
            await self._site.stop()
            self._site = None

        if self.runner:
            await self.runner.cleanup()
            self.runner = None

        self.app = None

        logger.info("HTTP transport stopped")

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
            "transport": "http",
            "endpoints": {
                "/mcp": "MCP JSON-RPC 2.0 endpoint (POST)",
                "/health": "Health check endpoint (GET)",
            },
            "status": "running",
        }

        return web.json_response(info)

    async def handle_health(self, request: web.Request) -> web.Response:
        """Handle health check endpoint (/health).

        Returns server health status and basic metrics.

        Args:
            request: HTTP request

        Returns:
            JSON response with health status
        """
        # For HTTP transport, we consider the server healthy if it's initialized
        # (running state is only relevant for stdio transport with lifespan)
        is_healthy = self.server.is_initialized

        health = {
            "status": "healthy" if is_healthy else "stopped",
            "initialized": self.server.is_initialized,
            "running": self.server.is_running,
            "requests_handled": self.server.request_count,
            "components": self.server.registry.get_stats(),
        }

        status = 200 if is_healthy else 503

        return web.json_response(health, status=status)

    async def handle_mcp_request(self, request: web.Request) -> web.Response:
        """Handle MCP JSON-RPC 2.0 requests.

        This is the main endpoint for MCP communication. It accepts JSON-RPC
        2.0 formatted requests and returns JSON-RPC 2.0 formatted responses.

        Args:
            request: HTTP request with JSON-RPC 2.0 payload

        Returns:
            JSON-RPC 2.0 response

        Expected request format:
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "tool_name",
                    "arguments": {...}
                }
            }

        Response format:
            {
                "jsonrpc": "2.0",
                "id": 1,
                "result": {...}
            }

        Error response format:
            {
                "jsonrpc": "2.0",
                "id": 1,
                "error": {
                    "code": -32600,
                    "message": "Invalid Request"
                }
            }
        """
        try:
            # Parse JSON body
            try:
                body = await request.json()
            except json.JSONDecodeError as e:
                return self._create_error_response(
                    None,
                    -32700,
                    "Parse error",
                    str(e),
                )

            # Validate JSON-RPC 2.0 structure
            if not isinstance(body, dict):
                return self._create_error_response(
                    None,
                    -32600,
                    "Invalid Request",
                    "Request must be a JSON object",
                )

            jsonrpc = body.get("jsonrpc")
            if jsonrpc != "2.0":
                return self._create_error_response(
                    body.get("id"),
                    -32600,
                    "Invalid Request",
                    "jsonrpc must be '2.0'",
                )

            request_id = body.get("id")
            method = body.get("method")
            params = body.get("params", {})

            if not isinstance(method, str):
                return self._create_error_response(
                    request_id,
                    -32600,
                    "Invalid Request",
                    "method must be a string",
                )

            # Route method to appropriate handler
            result = await self._handle_method(method, params)

            # Return successful response
            return self._create_success_response(request_id, result)

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
            return self._create_error_response(
                None,
                -32603,
                "Internal error",
                str(e),
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
            # Convert Pydantic models to dicts for JSON serialization
            tools_data = [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.input_schema,
                }
                for tool in tools
            ]
            return {"tools": tools_data}

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

            # Handle async handlers
            if asyncio.iscoroutine(result):
                result = await result

            return {"result": result}

        elif method == "prompts/list":
            prompts = self.server.registry.list_prompts()
            # Convert Pydantic models to dicts for JSON serialization
            prompts_data = [
                {
                    "name": prompt.name,
                    "description": prompt.description,
                    "arguments": prompt.arguments or [],
                }
                for prompt in prompts
            ]
            return {"prompts": prompts_data}

        elif method == "prompts/get":
            prompt_name = params.get("name")
            arguments = params.get("arguments", {})

            if not prompt_name:
                raise ValueError("Prompt name is required")

            prompt_config = self.server.registry.get_prompt(prompt_name)
            if not prompt_config:
                raise ValueError(f"Prompt not found: {prompt_name}")

            if prompt_config.handler:
                handler = prompt_config.handler
                result = handler(**arguments)

                if asyncio.iscoroutine(result):
                    result = await result

                return {"prompt": str(result)}

            elif prompt_config.template:
                template = prompt_config.template
                if arguments:
                    result = template.format(**arguments)
                else:
                    result = template

                return {"prompt": result}

            else:
                raise ValueError(f"Invalid prompt configuration: {prompt_name}")

        elif method == "resources/list":
            resources = self.server.registry.list_resources()
            # Convert Pydantic models to dicts for JSON serialization
            resources_data = [
                {
                    "uri": resource.uri,
                    "name": resource.name,
                    "description": resource.description,
                    "mimeType": resource.mime_type,
                }
                for resource in resources
            ]
            return {"resources": resources_data}

        elif method == "resources/read":
            uri = params.get("uri")

            if not uri:
                raise ValueError("Resource URI is required")

            resource_config = self.server.registry.get_resource(uri)
            if not resource_config:
                raise ValueError(f"Resource not found: {uri}")

            handler = resource_config.handler
            result = handler()

            if asyncio.iscoroutine(result):
                result = await result

            return {"content": result}

        else:
            raise ValueError(f"Unknown method: {method}")

    def _create_success_response(
        self,
        request_id: Any,
        result: Any,
    ) -> web.Response:
        """Create JSON-RPC 2.0 success response.

        Args:
            request_id: Request ID
            result: Result data

        Returns:
            JSON response
        """
        response_body = {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result,
        }

        return web.json_response(response_body)

    def _create_error_response(
        self,
        request_id: Any,
        code: int,
        message: str,
        data: str | None = None,
    ) -> web.Response:
        """Create JSON-RPC 2.0 error response.

        Args:
            request_id: Request ID
            code: Error code
            message: Error message
            data: Optional error data

        Returns:
            JSON response with error
        """
        error: dict[str, Any] = {
            "code": code,
            "message": message,
        }

        if data:
            error["data"] = data

        response_body = {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": error,
        }

        # Map JSON-RPC error codes to HTTP status codes
        status_map = {
            -32700: 400,  # Parse error
            -32600: 400,  # Invalid Request
            -32601: 404,  # Method not found
            -32602: 400,  # Invalid params
            -32603: 500,  # Internal error
        }

        status = status_map.get(code, 500)

        return web.json_response(response_body, status=status)


async def create_http_transport(
    server: SimplyMCPServer,
    config: SimplyMCPConfig | None = None,
) -> HTTPTransport:
    """Create and configure HTTP transport.

    This is a convenience function that creates an HTTP transport
    with configuration from SimplyMCPConfig.

    Args:
        server: MCP server instance
        config: Optional configuration (uses server config if not provided)

    Returns:
        Configured HTTP transport

    Example:
        >>> server = SimplyMCPServer()
        >>> await server.initialize()
        >>> transport = await create_http_transport(server)
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

    transport = HTTPTransport(
        server=server,
        host=config.transport.host,
        port=config.transport.port,
        cors_enabled=config.transport.cors_enabled,
        cors_origins=config.transport.cors_origins,
        auth_provider=auth_provider,
        rate_limiter=rate_limiter,
    )

    return transport


__all__ = ["HTTPTransport", "create_http_transport"]
