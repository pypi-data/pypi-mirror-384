"""Rate limiting implementation using token bucket algorithm.

This module provides a production-ready rate limiter for MCP servers that:
- Uses token bucket algorithm for flexible rate limiting
- Supports per-client tracking (by IP, session ID, or custom key)
- Thread-safe implementation using asyncio locks
- Memory-efficient with automatic cleanup of expired entries
- Configurable rates and burst sizes

The token bucket algorithm allows for:
- Steady-state rate limiting (tokens refill at constant rate)
- Burst capacity (accumulate tokens up to burst_size)
- Smooth rate enforcement without blocking peaks
"""

import asyncio
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from simply_mcp.core.errors import RateLimitExceededError
from simply_mcp.core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class TokenBucket:
    """Token bucket for a single client.

    The token bucket algorithm maintains a bucket of tokens that refills
    at a constant rate. Each request consumes one token. If no tokens
    are available, the request is rate limited.

    Attributes:
        capacity: Maximum number of tokens (burst size)
        tokens: Current number of tokens
        refill_rate: Tokens added per second
        last_refill: Timestamp of last refill
    """

    capacity: float
    tokens: float
    refill_rate: float
    last_refill: float = field(default_factory=time.time)

    def refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill

        # Calculate tokens to add based on elapsed time
        tokens_to_add = elapsed * self.refill_rate

        # Update tokens (cap at capacity)
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now

    def consume(self, tokens: float = 1.0) -> bool:
        """Attempt to consume tokens.

        Args:
            tokens: Number of tokens to consume

        Returns:
            True if tokens were consumed, False if insufficient tokens
        """
        self.refill()

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True

        return False

    def get_retry_after(self) -> float:
        """Calculate seconds until next token is available.

        Returns:
            Seconds until at least one token is available
        """
        if self.tokens >= 1.0:
            return 0.0

        # Calculate time needed to refill to 1 token
        tokens_needed = 1.0 - self.tokens
        return tokens_needed / self.refill_rate


@dataclass
class ClientEntry:
    """Entry tracking a client's rate limit state.

    Attributes:
        bucket: Token bucket for this client
        last_seen: Timestamp of last request
        request_count: Total requests from this client
    """

    bucket: TokenBucket
    last_seen: float = field(default_factory=time.time)
    request_count: int = 0


class RateLimiter:
    """Production-ready rate limiter using token bucket algorithm.

    This rate limiter provides:
    - Per-client rate limiting with configurable keys
    - Token bucket algorithm for smooth rate enforcement
    - Automatic cleanup of expired client entries
    - Thread-safe async implementation
    - Memory limits to prevent resource exhaustion
    - Detailed logging and metrics

    Example:
        >>> limiter = RateLimiter(requests_per_minute=60, burst_size=10)
        >>> await limiter.check_rate_limit("client-123")  # Returns True if allowed
        >>>
        >>> # With custom client key extractor
        >>> async def get_client_key(request):
        ...     return request.headers.get("X-Client-ID", request.remote)
        >>> limiter = RateLimiter(
        ...     requests_per_minute=100,
        ...     burst_size=20,
        ...     key_extractor=get_client_key,
        ... )
    """

    def __init__(
        self,
        requests_per_minute: int = 60,
        burst_size: int = 10,
        max_clients: int = 10000,
        cleanup_interval: int = 300,
        client_ttl: int = 600,
        key_extractor: Callable[[Any], Awaitable[str]] | None = None,
    ) -> None:
        """Initialize rate limiter.

        Args:
            requests_per_minute: Maximum requests per minute per client
            burst_size: Maximum burst size (token bucket capacity)
            max_clients: Maximum number of clients to track
            cleanup_interval: Interval between cleanup runs (seconds)
            client_ttl: Time to live for inactive clients (seconds)
            key_extractor: Optional async function to extract client key
        """
        if requests_per_minute <= 0:
            raise ValueError("requests_per_minute must be positive")
        if burst_size <= 0:
            raise ValueError("burst_size must be positive")
        if max_clients <= 0:
            raise ValueError("max_clients must be positive")

        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self.max_clients = max_clients
        self.cleanup_interval = cleanup_interval
        self.client_ttl = client_ttl
        self.key_extractor = key_extractor

        # Calculate refill rate (tokens per second)
        self.refill_rate = requests_per_minute / 60.0

        # Client tracking
        self._clients: dict[str, ClientEntry] = {}
        self._lock = asyncio.Lock()

        # Cleanup task
        self._cleanup_task: asyncio.Task[None] | None = None

        # Metrics
        self._total_requests = 0
        self._total_limited = 0

        logger.info(
            "Rate limiter initialized",
            extra={
                "context": {
                    "requests_per_minute": requests_per_minute,
                    "burst_size": burst_size,
                    "max_clients": max_clients,
                    "refill_rate": self.refill_rate,
                }
            },
        )

    def start_cleanup(self) -> None:
        """Start automatic cleanup task.

        This should be called when the rate limiter is ready to start
        processing requests. It runs a background task to periodically
        clean up expired client entries.
        """
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            logger.info("Rate limiter cleanup task started")

    async def stop_cleanup(self) -> None:
        """Stop automatic cleanup task."""
        if self._cleanup_task is not None:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
            logger.info("Rate limiter cleanup task stopped")

    async def check_rate_limit(
        self,
        client_key: str,
        tokens: float = 1.0,
    ) -> bool:
        """Check if request is allowed under rate limit.

        This is the main method for rate limit enforcement. It:
        1. Gets or creates a token bucket for the client
        2. Attempts to consume tokens
        3. Returns True if allowed, False if rate limited
        4. Logs rate limit violations

        Args:
            client_key: Unique identifier for the client
            tokens: Number of tokens to consume (default: 1.0)

        Returns:
            True if request is allowed, False if rate limited

        Example:
            >>> limiter = RateLimiter(requests_per_minute=60)
            >>> if await limiter.check_rate_limit("client-ip"):
            ...     # Process request
            ...     pass
            ... else:
            ...     # Return 429 Too Many Requests
            ...     raise RateLimitExceededError()
        """
        self._total_requests += 1

        async with self._lock:
            # Get or create client entry
            if client_key not in self._clients:
                # Check if we're at max clients
                if len(self._clients) >= self.max_clients:
                    # Emergency cleanup of oldest clients
                    await self._emergency_cleanup()

                # Create new bucket for client
                bucket = TokenBucket(
                    capacity=self.burst_size,
                    tokens=self.burst_size,  # Start with full bucket
                    refill_rate=self.refill_rate,
                )

                self._clients[client_key] = ClientEntry(bucket=bucket)

                logger.debug(
                    f"New client tracked: {client_key}",
                    extra={
                        "context": {
                            "client_key": client_key,
                            "total_clients": len(self._clients),
                        }
                    },
                )

            # Get client entry
            entry = self._clients[client_key]
            entry.last_seen = time.time()
            entry.request_count += 1

            # Try to consume tokens
            allowed = entry.bucket.consume(tokens)

            if not allowed:
                self._total_limited += 1

                logger.warning(
                    f"Rate limit exceeded for {client_key}",
                    extra={
                        "context": {
                            "client_key": client_key,
                            "tokens": entry.bucket.tokens,
                            "requests": entry.request_count,
                            "retry_after": entry.bucket.get_retry_after(),
                        }
                    },
                )

            return allowed

    async def get_retry_after(self, client_key: str) -> float:
        """Get retry-after time for a rate-limited client.

        Args:
            client_key: Client identifier

        Returns:
            Seconds until client can retry (0 if not rate limited)
        """
        async with self._lock:
            if client_key not in self._clients:
                return 0.0

            entry = self._clients[client_key]
            return entry.bucket.get_retry_after()

    async def get_client_info(self, client_key: str) -> dict[str, Any]:
        """Get information about a client's rate limit state.

        Args:
            client_key: Client identifier

        Returns:
            Dictionary with client rate limit information
        """
        async with self._lock:
            if client_key not in self._clients:
                return {
                    "tracked": False,
                    "tokens": self.burst_size,
                    "capacity": self.burst_size,
                    "refill_rate": self.refill_rate,
                }

            entry = self._clients[client_key]
            entry.bucket.refill()  # Refill before reporting

            return {
                "tracked": True,
                "tokens": entry.bucket.tokens,
                "capacity": entry.bucket.capacity,
                "refill_rate": entry.bucket.refill_rate,
                "request_count": entry.request_count,
                "last_seen": entry.last_seen,
                "retry_after": entry.bucket.get_retry_after(),
            }

    async def reset_client(self, client_key: str) -> None:
        """Reset rate limit for a client.

        Args:
            client_key: Client identifier
        """
        async with self._lock:
            if client_key in self._clients:
                del self._clients[client_key]

                logger.info(
                    f"Rate limit reset for {client_key}",
                    extra={"context": {"client_key": client_key}},
                )

    async def get_stats(self) -> dict[str, Any]:
        """Get rate limiter statistics.

        Returns:
            Dictionary with rate limiter metrics
        """
        async with self._lock:
            return {
                "total_requests": self._total_requests,
                "total_limited": self._total_limited,
                "active_clients": len(self._clients),
                "max_clients": self.max_clients,
                "requests_per_minute": self.requests_per_minute,
                "burst_size": self.burst_size,
                "limit_rate": (
                    self._total_limited / self._total_requests * 100
                    if self._total_requests > 0
                    else 0.0
                ),
            }

    async def _cleanup_loop(self) -> None:
        """Background task to cleanup expired client entries."""
        logger.info("Rate limiter cleanup loop started")

        try:
            while True:
                await asyncio.sleep(self.cleanup_interval)
                await self._cleanup_expired_clients()

        except asyncio.CancelledError:
            logger.info("Rate limiter cleanup loop cancelled")
            raise

    async def _cleanup_expired_clients(self) -> None:
        """Remove clients that haven't been seen recently."""
        now = time.time()
        cutoff = now - self.client_ttl

        async with self._lock:
            expired = [
                key
                for key, entry in self._clients.items()
                if entry.last_seen < cutoff
            ]

            for key in expired:
                del self._clients[key]

            if expired:
                logger.info(
                    f"Cleaned up {len(expired)} expired clients",
                    extra={
                        "context": {
                            "expired_count": len(expired),
                            "remaining_clients": len(self._clients),
                        }
                    },
                )

    async def _emergency_cleanup(self) -> None:
        """Emergency cleanup when max_clients is reached.

        Removes the oldest 10% of clients to make room for new ones.
        """
        # Sort clients by last_seen
        sorted_clients = sorted(
            self._clients.items(),
            key=lambda x: x[1].last_seen,
        )

        # Remove oldest 10%
        remove_count = max(1, len(sorted_clients) // 10)
        for key, _ in sorted_clients[:remove_count]:
            del self._clients[key]

        logger.warning(
            f"Emergency cleanup: removed {remove_count} clients",
            extra={
                "context": {
                    "removed": remove_count,
                    "remaining": len(self._clients),
                }
            },
        )

    async def enforce_rate_limit(
        self,
        client_key: str,
        tokens: float = 1.0,
    ) -> None:
        """Check rate limit and raise exception if exceeded.

        This is a convenience method that combines check_rate_limit
        with exception raising.

        Args:
            client_key: Client identifier
            tokens: Number of tokens to consume

        Raises:
            RateLimitExceededError: If rate limit is exceeded
        """
        allowed = await self.check_rate_limit(client_key, tokens)

        if not allowed:
            retry_after = await self.get_retry_after(client_key)

            raise RateLimitExceededError(
                message=f"Rate limit exceeded for {client_key}",
                limit=self.requests_per_minute,
                retry_after=int(retry_after) + 1,  # Round up
                context={"client_key": client_key},
            )


__all__ = [
    "RateLimiter",
    "TokenBucket",
    "ClientEntry",
]
