"""Security features for Simply-MCP.

This module provides security features including:
- Rate limiting using token bucket algorithm
- Authentication (API key, OAuth stub, JWT stub)
- Authorization (future)
- Request validation and sanitization (future)
"""

from simply_mcp.security.auth import (
    APIKeyAuthProvider,
    AuthProvider,
    ClientInfo,
    JWTProvider,
    NoAuthProvider,
    OAuthProvider,
    create_auth_provider,
)
from simply_mcp.security.rate_limiter import (
    ClientEntry,
    RateLimiter,
    TokenBucket,
)

__all__ = [
    # Rate limiting
    "RateLimiter",
    "TokenBucket",
    "ClientEntry",
    # Authentication
    "AuthProvider",
    "NoAuthProvider",
    "APIKeyAuthProvider",
    "OAuthProvider",
    "JWTProvider",
    "ClientInfo",
    "create_auth_provider",
]
