"""Authentication providers for Simply-MCP.

This module provides authentication support for MCP servers, including
API key authentication and extensibility for OAuth and JWT in the future.
"""

import hmac
from abc import ABC, abstractmethod
from typing import Any

from aiohttp import web

from simply_mcp.core.errors import AuthenticationError
from simply_mcp.core.logger import get_logger

logger = get_logger(__name__)


class ClientInfo:
    """Information about an authenticated client.

    Attributes:
        client_id: Unique identifier for the client
        auth_type: Type of authentication used
        metadata: Additional client metadata
    """

    def __init__(
        self,
        client_id: str,
        auth_type: str = "none",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Initialize client info.

        Args:
            client_id: Unique identifier for the client
            auth_type: Type of authentication used
            metadata: Optional additional metadata
        """
        self.client_id = client_id
        self.auth_type = auth_type
        self.metadata = metadata or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation.

        Returns:
            Dictionary with client information
        """
        return {
            "client_id": self.client_id,
            "auth_type": self.auth_type,
            "metadata": self.metadata,
        }

    def __repr__(self) -> str:
        """Return string representation."""
        return f"ClientInfo(client_id={self.client_id!r}, auth_type={self.auth_type!r})"


class AuthProvider(ABC):
    """Abstract base class for authentication providers.

    All authentication providers must implement the authenticate method
    which validates incoming requests and returns client information.
    """

    @abstractmethod
    async def authenticate(self, request: web.Request) -> ClientInfo:
        """Authenticate a request.

        Args:
            request: The incoming HTTP request

        Returns:
            ClientInfo with authenticated client details

        Raises:
            AuthenticationError: If authentication fails
        """
        pass


class NoAuthProvider(AuthProvider):
    """Pass-through authentication provider that allows all requests.

    This provider is used when authentication is disabled. It assigns
    a generic client ID to all requests.

    Example:
        >>> provider = NoAuthProvider()
        >>> client = await provider.authenticate(request)
        >>> print(client.client_id)
        anonymous
    """

    async def authenticate(self, request: web.Request) -> ClientInfo:
        """Allow all requests without authentication.

        Args:
            request: The incoming HTTP request

        Returns:
            ClientInfo with anonymous client ID
        """
        return ClientInfo(
            client_id="anonymous",
            auth_type="none",
            metadata={"remote": request.remote or "unknown"},
        )


class APIKeyAuthProvider(AuthProvider):
    """API key authentication provider.

    Validates requests using API keys from Authorization header or X-API-Key header.
    Uses constant-time comparison to prevent timing attacks.

    Supported header formats:
    - Authorization: Bearer <api_key>
    - X-API-Key: <api_key>

    Attributes:
        api_keys: Set of valid API keys
        header_name: Name of the header to check for API key

    Example:
        >>> provider = APIKeyAuthProvider(api_keys=["secret-key-123"])
        >>> client = await provider.authenticate(request)
        >>> print(client.client_id)
        api-key-abc123def
    """

    def __init__(
        self,
        api_keys: list[str],
        header_name: str = "Authorization",
    ) -> None:
        """Initialize API key authentication provider.

        Args:
            api_keys: List of valid API keys
            header_name: Header name to check (default: Authorization)

        Raises:
            ValueError: If no API keys are provided
        """
        if not api_keys:
            raise ValueError("At least one API key must be provided")

        self.api_keys = set(api_keys)
        self.header_name = header_name

        # Log initialization (without exposing keys)
        logger.info(
            f"Initialized API key auth provider with {len(api_keys)} key(s)",
            extra={
                "context": {
                    "num_keys": len(api_keys),
                    "header_name": header_name,
                }
            },
        )

    async def authenticate(self, request: web.Request) -> ClientInfo:
        """Authenticate request using API key.

        Args:
            request: The incoming HTTP request

        Returns:
            ClientInfo with authenticated client details

        Raises:
            AuthenticationError: If authentication fails
        """
        # Extract API key from headers
        api_key = self._extract_api_key(request)

        if not api_key:
            logger.warning(
                "Authentication failed: No API key provided",
                extra={
                    "context": {
                        "remote": request.remote or "unknown",
                        "path": request.path,
                    }
                },
            )
            raise AuthenticationError(
                "Authentication required. Provide API key in Authorization header "
                "(Bearer <key>) or X-API-Key header",
                auth_type="api_key",
            )

        # Validate API key using constant-time comparison
        if not self._validate_api_key(api_key):
            logger.warning(
                "Authentication failed: Invalid API key",
                extra={
                    "context": {
                        "remote": request.remote or "unknown",
                        "path": request.path,
                        # Don't log the actual key for security
                        "key_prefix": api_key[:8] + "..." if len(api_key) > 8 else "***",
                    }
                },
            )
            raise AuthenticationError(
                "Invalid API key",
                auth_type="api_key",
            )

        # Create client ID from API key hash (for tracking without exposing key)
        client_id = self._create_client_id(api_key)

        logger.debug(
            f"API key authentication successful for client {client_id}",
            extra={
                "context": {
                    "client_id": client_id,
                    "remote": request.remote or "unknown",
                }
            },
        )

        return ClientInfo(
            client_id=client_id,
            auth_type="api_key",
            metadata={
                "remote": request.remote or "unknown",
                "key_prefix": api_key[:8] + "..." if len(api_key) > 8 else "***",
            },
        )

    def _extract_api_key(self, request: web.Request) -> str | None:
        """Extract API key from request headers.

        Supports both Authorization: Bearer <key> and X-API-Key: <key> formats.

        Args:
            request: The incoming HTTP request

        Returns:
            API key if found, None otherwise
        """
        # Check X-API-Key header first (simpler format)
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return api_key.strip()

        # Check Authorization header with Bearer scheme
        auth_header = request.headers.get("Authorization")
        if auth_header:
            parts = auth_header.strip().split()
            if len(parts) == 2 and parts[0].lower() == "bearer":
                return parts[1]

        return None

    def _validate_api_key(self, api_key: str) -> bool:
        """Validate API key using constant-time comparison.

        Uses hmac.compare_digest for constant-time comparison to prevent
        timing attacks.

        Args:
            api_key: The API key to validate

        Returns:
            True if valid, False otherwise
        """
        # Check against all valid keys using constant-time comparison
        for valid_key in self.api_keys:
            if hmac.compare_digest(api_key, valid_key):
                return True
        return False

    def _create_client_id(self, api_key: str) -> str:
        """Create a client ID from API key.

        Creates a deterministic but non-reversible client ID from the API key
        for logging and tracking purposes.

        Args:
            api_key: The API key

        Returns:
            Client ID string
        """
        # Use a simple hash-based approach for client ID
        # In production, you might want to use a more sophisticated method
        import hashlib

        hash_obj = hashlib.sha256(api_key.encode())
        hash_hex = hash_obj.hexdigest()
        return f"api-key-{hash_hex[:16]}"


class OAuthProvider(AuthProvider):
    """OAuth authentication provider (stub for future implementation).

    This is a placeholder for OAuth 2.0 authentication support.
    Implementation will be added in a future phase.

    Attributes:
        client_id: OAuth client ID
        client_secret: OAuth client secret
        authorization_url: OAuth authorization endpoint
        token_url: OAuth token endpoint
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        authorization_url: str,
        token_url: str,
        **kwargs: Any,
    ) -> None:
        """Initialize OAuth provider (stub).

        Args:
            client_id: OAuth client ID
            client_secret: OAuth client secret
            authorization_url: OAuth authorization endpoint
            token_url: OAuth token endpoint
            **kwargs: Additional OAuth configuration
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.authorization_url = authorization_url
        self.token_url = token_url
        self.config = kwargs

        logger.info("Initialized OAuth provider (stub - not yet implemented)")

    async def authenticate(self, request: web.Request) -> ClientInfo:
        """Authenticate request using OAuth (not yet implemented).

        Args:
            request: The incoming HTTP request

        Returns:
            ClientInfo with authenticated client details

        Raises:
            NotImplementedError: OAuth is not yet implemented
        """
        raise NotImplementedError(
            "OAuth authentication is not yet implemented. "
            "This is a placeholder for future Phase 4 Week 8+ development."
        )


class JWTProvider(AuthProvider):
    """JWT authentication provider (stub for future implementation).

    This is a placeholder for JWT (JSON Web Token) authentication support.
    Implementation will be added in a future phase.

    Attributes:
        secret_key: JWT secret key for verification
        algorithm: JWT signing algorithm (e.g., HS256, RS256)
        audience: Expected JWT audience
        issuer: Expected JWT issuer
    """

    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        audience: str | None = None,
        issuer: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize JWT provider (stub).

        Args:
            secret_key: JWT secret key for verification
            algorithm: JWT signing algorithm
            audience: Expected JWT audience
            issuer: Expected JWT issuer
            **kwargs: Additional JWT configuration
        """
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.audience = audience
        self.issuer = issuer
        self.config = kwargs

        logger.info("Initialized JWT provider (stub - not yet implemented)")

    async def authenticate(self, request: web.Request) -> ClientInfo:
        """Authenticate request using JWT (not yet implemented).

        Args:
            request: The incoming HTTP request

        Returns:
            ClientInfo with authenticated client details

        Raises:
            NotImplementedError: JWT is not yet implemented
        """
        raise NotImplementedError(
            "JWT authentication is not yet implemented. "
            "This is a placeholder for future Phase 4 Week 8+ development."
        )


def create_auth_provider(
    auth_type: str,
    **config: Any,
) -> AuthProvider:
    """Factory function to create authentication providers.

    Args:
        auth_type: Type of authentication (none, api_key, oauth, jwt)
        **config: Configuration for the authentication provider

    Returns:
        Configured authentication provider

    Raises:
        ValueError: If auth_type is not supported

    Example:
        >>> provider = create_auth_provider("api_key", api_keys=["secret-123"])
        >>> provider = create_auth_provider("none")
    """
    if auth_type == "none":
        return NoAuthProvider()

    elif auth_type == "api_key":
        api_keys = config.get("api_keys", [])
        if not api_keys:
            raise ValueError("api_keys must be provided for api_key auth type")
        return APIKeyAuthProvider(api_keys=api_keys)

    elif auth_type == "oauth":
        client_id = config.get("client_id")
        client_secret = config.get("client_secret")
        authorization_url = config.get("authorization_url")
        token_url = config.get("token_url")

        if not all([client_id, client_secret, authorization_url, token_url]):
            raise ValueError(
                "OAuth requires: client_id, client_secret, authorization_url, token_url"
            )

        # Filter out the keys we already extracted
        extra_config = {k: v for k, v in config.items()
                       if k not in ["client_id", "client_secret", "authorization_url", "token_url"]}

        # Type assertions since we checked above
        assert isinstance(client_id, str)
        assert isinstance(client_secret, str)
        assert isinstance(authorization_url, str)
        assert isinstance(token_url, str)

        return OAuthProvider(
            client_id=client_id,
            client_secret=client_secret,
            authorization_url=authorization_url,
            token_url=token_url,
            **extra_config,
        )

    elif auth_type == "jwt":
        secret_key = config.get("secret_key")
        if not secret_key:
            raise ValueError("JWT requires: secret_key")

        # Filter out the keys we already extracted
        extra_config = {k: v for k, v in config.items()
                       if k not in ["secret_key", "algorithm", "audience", "issuer"]}

        return JWTProvider(
            secret_key=secret_key,
            algorithm=config.get("algorithm", "HS256"),
            audience=config.get("audience"),
            issuer=config.get("issuer"),
            **extra_config,
        )

    else:
        raise ValueError(
            f"Unsupported auth type: {auth_type}. "
            f"Supported types: none, api_key, oauth, jwt"
        )


__all__ = [
    "AuthProvider",
    "NoAuthProvider",
    "APIKeyAuthProvider",
    "OAuthProvider",
    "JWTProvider",
    "ClientInfo",
    "create_auth_provider",
]
