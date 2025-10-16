"""Middleware for HTTP and SSE transports.

This module provides middleware components for request processing in
HTTP and SSE transports, including CORS support, logging, and rate limiting.
"""

import time
from collections.abc import Awaitable, Callable
from typing import Any

from aiohttp import web

from simply_mcp.core.logger import get_logger

logger = get_logger(__name__)

# Type alias for middleware handler
Handler = Callable[[web.Request], Awaitable[web.StreamResponse]]


class CORSMiddleware:
    """CORS middleware for HTTP/SSE transports.

    Handles Cross-Origin Resource Sharing (CORS) headers to allow
    web browsers to make requests to the MCP server from different origins.

    Attributes:
        enabled: Whether CORS is enabled
        allowed_origins: List of allowed origins or ["*"] for all
        allow_credentials: Whether to allow credentials
        allow_methods: List of allowed HTTP methods
        allow_headers: List of allowed headers
        max_age: Maximum age for preflight cache (seconds)

    Example:
        >>> middleware = CORSMiddleware(
        ...     enabled=True,
        ...     allowed_origins=["http://localhost:3000"]
        ... )
        >>> app.middlewares.append(middleware)
    """

    def __init__(
        self,
        enabled: bool = True,
        allowed_origins: list[str] | None = None,
        allow_credentials: bool = True,
        allow_methods: list[str] | None = None,
        allow_headers: list[str] | None = None,
        max_age: int = 86400,
    ) -> None:
        """Initialize CORS middleware.

        Args:
            enabled: Whether CORS is enabled
            allowed_origins: List of allowed origins or None for ["*"]
            allow_credentials: Whether to allow credentials
            allow_methods: List of allowed methods or None for defaults
            allow_headers: List of allowed headers or None for defaults
            max_age: Maximum age for preflight cache (seconds)
        """
        self.enabled = enabled
        self.allowed_origins = allowed_origins or ["*"]
        self.allow_credentials = allow_credentials
        self.allow_methods = allow_methods or ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        self.allow_headers = allow_headers or [
            "Content-Type",
            "Authorization",
            "X-Requested-With",
        ]
        self.max_age = max_age

    @web.middleware
    async def __call__(
        self,
        request: web.Request,
        handler: Handler,
    ) -> web.StreamResponse:
        """Process request with CORS headers.

        Args:
            request: Incoming request
            handler: Next handler in chain

        Returns:
            Response with CORS headers
        """
        if not self.enabled:
            return await handler(request)

        # Handle preflight OPTIONS requests
        if request.method == "OPTIONS":
            return await self._handle_preflight(request)

        # Process normal request
        response = await handler(request)

        # Add CORS headers to response
        self._add_cors_headers(request, response)

        return response

    async def _handle_preflight(self, request: web.Request) -> web.Response:
        """Handle CORS preflight OPTIONS request.

        Args:
            request: OPTIONS request

        Returns:
            Response with CORS preflight headers
        """
        response = web.Response(status=204)
        self._add_cors_headers(request, response)
        return response

    def _add_cors_headers(
        self,
        request: web.Request,
        response: web.StreamResponse,
    ) -> None:
        """Add CORS headers to response.

        Args:
            request: Incoming request
            response: Response to add headers to
        """
        origin = request.headers.get("Origin")

        # Check if origin is allowed
        if origin and (
            "*" in self.allowed_origins or origin in self.allowed_origins
        ):
            response.headers["Access-Control-Allow-Origin"] = origin
        elif "*" in self.allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = "*"

        # Add other CORS headers
        if self.allow_credentials:
            response.headers["Access-Control-Allow-Credentials"] = "true"

        response.headers["Access-Control-Allow-Methods"] = ", ".join(
            self.allow_methods
        )
        response.headers["Access-Control-Allow-Headers"] = ", ".join(
            self.allow_headers
        )
        response.headers["Access-Control-Max-Age"] = str(self.max_age)


class LoggingMiddleware:
    """Request/response logging middleware.

    Logs HTTP requests and responses with timing information for
    debugging and monitoring purposes.

    Example:
        >>> middleware = LoggingMiddleware()
        >>> app.middlewares.append(middleware)
    """

    def __init__(self, verbose: bool = False) -> None:
        """Initialize logging middleware.

        Args:
            verbose: Whether to log request/response bodies
        """
        self.verbose = verbose

    @web.middleware
    async def __call__(
        self,
        request: web.Request,
        handler: Handler,
    ) -> web.StreamResponse:
        """Process request with logging.

        Args:
            request: Incoming request
            handler: Next handler in chain

        Returns:
            Response from handler
        """
        start_time = time.time()

        # Log request
        logger.info(
            f"Request: {request.method} {request.path}",
            extra={
                "context": {
                    "method": request.method,
                    "path": request.path,
                    "remote": request.remote or "unknown",
                    "headers": dict(request.headers) if self.verbose else None,
                }
            },
        )

        try:
            # Process request
            response = await handler(request)

            # Calculate elapsed time
            elapsed_ms = round((time.time() - start_time) * 1000, 2)

            # Log response
            logger.info(
                f"Response: {response.status} ({elapsed_ms}ms)",
                extra={
                    "context": {
                        "method": request.method,
                        "path": request.path,
                        "status": response.status,
                        "elapsed_ms": elapsed_ms,
                    }
                },
            )

            return response

        except Exception as e:
            # Calculate elapsed time
            elapsed_ms = round((time.time() - start_time) * 1000, 2)

            # Log error
            logger.error(
                f"Request failed: {e} ({elapsed_ms}ms)",
                extra={
                    "context": {
                        "method": request.method,
                        "path": request.path,
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "elapsed_ms": elapsed_ms,
                    }
                },
            )

            raise


class RateLimitMiddleware:
    """Rate limiting middleware using token bucket algorithm.

    Provides production-ready rate limiting to prevent abuse using the
    token bucket algorithm. Integrates with the RateLimiter class for
    per-client rate limiting.

    Example:
        >>> from simply_mcp.security import RateLimiter
        >>> limiter = RateLimiter(requests_per_minute=60, burst_size=10)
        >>> middleware = RateLimitMiddleware(rate_limiter=limiter)
        >>> app.middlewares.append(middleware)
    """

    def __init__(
        self,
        rate_limiter: Any | None = None,
        requests_per_minute: int = 60,
        burst_size: int = 10,
        client_key_extractor: Any = None,
    ) -> None:
        """Initialize rate limit middleware.

        Args:
            rate_limiter: Optional RateLimiter instance (creates one if not provided)
            requests_per_minute: Requests per minute (used if rate_limiter not provided)
            burst_size: Burst size (used if rate_limiter not provided)
            client_key_extractor: Optional function to extract client key from request
        """
        if rate_limiter is not None:
            self.rate_limiter = rate_limiter
        else:
            # Import here to avoid circular dependency
            from simply_mcp.security import RateLimiter

            self.rate_limiter = RateLimiter(
                requests_per_minute=requests_per_minute,
                burst_size=burst_size,
            )

        self.client_key_extractor = client_key_extractor or self._default_key_extractor

    def _default_key_extractor(self, request: web.Request) -> str:
        """Default client key extractor (uses IP address).

        Args:
            request: HTTP request

        Returns:
            Client key (IP address)
        """
        return request.remote or "unknown"

    @web.middleware
    async def __call__(
        self,
        request: web.Request,
        handler: Handler,
    ) -> web.StreamResponse:
        """Process request with rate limiting.

        Args:
            request: Incoming request
            handler: Next handler in chain

        Returns:
            Response from handler or 429 if rate limited
        """
        # Import here to avoid circular dependency
        from simply_mcp.core.errors import RateLimitExceededError

        # Extract client key
        client_key = self.client_key_extractor(request)

        # Check rate limit
        try:
            await self.rate_limiter.enforce_rate_limit(client_key)
        except RateLimitExceededError as e:
            # Get retry-after information
            retry_after = e.context.get("retry_after", 60)

            # Log rate limit violation
            logger.warning(
                f"Rate limit exceeded for {client_key}",
                extra={
                    "context": {
                        "client_key": client_key,
                        "retry_after": retry_after,
                    }
                },
            )

            # Return 429 Too Many Requests
            response = web.json_response(
                {
                    "error": "Rate limit exceeded",
                    "code": "RATE_LIMIT_EXCEEDED",
                    "retry_after": retry_after,
                },
                status=429,
            )

            # Add Retry-After header
            response.headers["Retry-After"] = str(retry_after)

            return response

        # Process request
        return await handler(request)


class AuthMiddleware:
    """Authentication middleware.

    Validates requests using a configured authentication provider.
    Sets authenticated client information in request context for
    downstream handlers to use.

    Attributes:
        auth_provider: The authentication provider to use
        rate_limiter: Optional rate limiter for auth failures

    Example:
        >>> from simply_mcp.security.auth import APIKeyAuthProvider
        >>> provider = APIKeyAuthProvider(api_keys=["secret-123"])
        >>> middleware = AuthMiddleware(provider)
        >>> app.middlewares.append(middleware)
    """

    def __init__(
        self,
        auth_provider: Any,  # AuthProvider type hint causes circular import
        rate_limit_failures: bool = True,
        max_failures: int = 10,
        failure_window: int = 60,
    ) -> None:
        """Initialize authentication middleware.

        Args:
            auth_provider: Authentication provider to use
            rate_limit_failures: Whether to rate limit auth failures
            max_failures: Maximum auth failures per window
            failure_window: Time window for failure tracking (seconds)
        """
        self.auth_provider = auth_provider
        self.rate_limit_failures = rate_limit_failures
        self.max_failures = max_failures
        self.failure_window = failure_window
        self._failures: dict[str, list[float]] = {}

    @web.middleware
    async def __call__(
        self,
        request: web.Request,
        handler: Handler,
    ) -> web.StreamResponse:
        """Process request with authentication.

        Args:
            request: Incoming request
            handler: Next handler in chain

        Returns:
            Response from handler or 401 if authentication fails
        """
        # Import here to avoid circular dependency
        from simply_mcp.core.errors import AuthenticationError

        try:
            # Check rate limit for auth failures (if enabled)
            if self.rate_limit_failures:
                client_ip = request.remote or "unknown"
                if self._is_rate_limited(client_ip):
                    logger.warning(
                        f"Auth failure rate limit exceeded for {client_ip}",
                        extra={
                            "context": {
                                "client_ip": client_ip,
                                "failures": len(self._failures.get(client_ip, [])),
                            }
                        },
                    )
                    return web.json_response(
                        {
                            "error": "Too many authentication failures",
                            "code": "RATE_LIMIT_EXCEEDED",
                        },
                        status=429,
                    )

            # Authenticate request
            client_info = await self.auth_provider.authenticate(request)

            # Store client info in request for downstream handlers
            request["client_info"] = client_info

            # Clear failures for this client on successful auth
            if self.rate_limit_failures:
                client_ip = request.remote or "unknown"
                if client_ip in self._failures:
                    del self._failures[client_ip]

            # Continue to next handler
            return await handler(request)

        except AuthenticationError as e:
            # Track authentication failure
            if self.rate_limit_failures:
                client_ip = request.remote or "unknown"
                self._record_failure(client_ip)

            # Log authentication failure (without sensitive info)
            logger.warning(
                f"Authentication failed: {e.message}",
                extra={
                    "context": {
                        "remote": request.remote or "unknown",
                        "path": request.path,
                        "auth_type": e.context.get("auth_type", "unknown"),
                    }
                },
            )

            # Return 401 Unauthorized
            return web.json_response(
                {
                    "error": e.message,
                    "code": e.code,
                },
                status=401,
            )

        except Exception as e:
            # Log unexpected error
            logger.error(
                f"Unexpected error in authentication: {e}",
                extra={
                    "context": {
                        "error": str(e),
                        "error_type": type(e).__name__,
                    }
                },
            )

            # Return 500 Internal Server Error
            return web.json_response(
                {
                    "error": "Internal authentication error",
                    "code": "INTERNAL_ERROR",
                },
                status=500,
            )

    def _is_rate_limited(self, client_ip: str) -> bool:
        """Check if client has exceeded auth failure rate limit.

        Args:
            client_ip: Client IP address

        Returns:
            True if rate limited, False otherwise
        """
        if client_ip not in self._failures:
            return False

        current_time = time.time()

        # Remove old failures outside window
        self._failures[client_ip] = [
            failure_time
            for failure_time in self._failures[client_ip]
            if current_time - failure_time < self.failure_window
        ]

        # Check if limit exceeded
        return len(self._failures[client_ip]) >= self.max_failures

    def _record_failure(self, client_ip: str) -> None:
        """Record an authentication failure.

        Args:
            client_ip: Client IP address
        """
        current_time = time.time()

        if client_ip not in self._failures:
            self._failures[client_ip] = []

        self._failures[client_ip].append(current_time)


def create_middleware_stack(
    cors_enabled: bool = True,
    cors_origins: list[str] | None = None,
    logging_enabled: bool = True,
    rate_limit_enabled: bool = False,
) -> list[Any]:
    """Create a middleware stack for HTTP/SSE transports.

    This is a convenience function that creates commonly used middleware
    configurations.

    Args:
        cors_enabled: Whether to enable CORS middleware
        cors_origins: Allowed CORS origins or None for all (*)
        logging_enabled: Whether to enable logging middleware
        rate_limit_enabled: Whether to enable rate limiting

    Returns:
        List of middleware instances

    Example:
        >>> middlewares = create_middleware_stack(
        ...     cors_enabled=True,
        ...     cors_origins=["http://localhost:3000"],
        ...     logging_enabled=True,
        ... )
        >>> app = web.Application(middlewares=middlewares)
    """
    middlewares: list[Any] = []

    # Add logging first for complete request/response tracking
    if logging_enabled:
        logging_middleware = LoggingMiddleware()
        middlewares.append(logging_middleware)

    # Add CORS support
    if cors_enabled:
        cors_middleware = CORSMiddleware(
            enabled=True,
            allowed_origins=cors_origins,
        )
        middlewares.append(cors_middleware)

    # Add rate limiting (placeholder for Phase 4)
    if rate_limit_enabled:
        rate_limit_middleware = RateLimitMiddleware()
        middlewares.append(rate_limit_middleware)

    return middlewares


__all__ = [
    "CORSMiddleware",
    "LoggingMiddleware",
    "RateLimitMiddleware",
    "AuthMiddleware",
    "create_middleware_stack",
]
