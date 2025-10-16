"""Authentication providers for Simply-MCP.

This module provides authentication support for MCP servers, including
API key authentication, OAuth 2.0, and JWT (JSON Web Token) authentication.
"""

import hmac
import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any
from urllib.parse import urlencode

import aiohttp
import jwt
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
    """OAuth 2.0 authentication provider.

    Implements OAuth 2.0 Authorization Code Flow with token validation,
    token refresh, and proper error handling. This provider validates
    access tokens received in the Authorization header.

    Supported header format:
    - Authorization: Bearer <access_token>

    Attributes:
        client_id: OAuth client ID
        client_secret: OAuth client secret
        authorization_url: OAuth authorization endpoint
        token_url: OAuth token endpoint
        userinfo_url: Optional URL to fetch user information
        redirect_uri: OAuth redirect URI for authorization flow
        scope: OAuth scope (space-separated string)
        token_cache: Cache of validated tokens with metadata

    Example:
        >>> provider = OAuthProvider(
        ...     client_id="your-client-id",
        ...     client_secret="your-client-secret",
        ...     authorization_url="https://provider.com/oauth/authorize",
        ...     token_url="https://provider.com/oauth/token",
        ...     userinfo_url="https://provider.com/oauth/userinfo"
        ... )
        >>> client = await provider.authenticate(request)
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        authorization_url: str,
        token_url: str,
        userinfo_url: str | None = None,
        redirect_uri: str | None = None,
        scope: str = "openid profile email",
        **kwargs: Any,
    ) -> None:
        """Initialize OAuth provider.

        Args:
            client_id: OAuth client ID
            client_secret: OAuth client secret
            authorization_url: OAuth authorization endpoint
            token_url: OAuth token endpoint
            userinfo_url: Optional URL to fetch user information
            redirect_uri: OAuth redirect URI for authorization flow
            scope: OAuth scope (space-separated string)
            **kwargs: Additional OAuth configuration
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.authorization_url = authorization_url
        self.token_url = token_url
        self.userinfo_url = userinfo_url
        self.redirect_uri = redirect_uri
        self.scope = scope
        self.config = kwargs

        # Token cache: {access_token: (client_info, expiry_time)}
        self.token_cache: dict[str, tuple[ClientInfo, float]] = {}

        logger.info(
            "Initialized OAuth provider",
            extra={
                "context": {
                    "client_id": client_id,
                    "authorization_url": authorization_url,
                    "token_url": token_url,
                }
            },
        )

    async def authenticate(self, request: web.Request) -> ClientInfo:
        """Authenticate request using OAuth 2.0 access token.

        Args:
            request: The incoming HTTP request

        Returns:
            ClientInfo with authenticated client details

        Raises:
            AuthenticationError: If authentication fails
        """
        # Extract access token from Authorization header
        access_token = self._extract_token(request)

        if not access_token:
            logger.warning(
                "OAuth authentication failed: No access token provided",
                extra={
                    "context": {
                        "remote": request.remote or "unknown",
                        "path": request.path,
                    }
                },
            )
            raise AuthenticationError(
                "Authentication required. Provide OAuth access token in "
                "Authorization header (Bearer <token>)",
                auth_type="oauth",
            )

        # Check token cache first
        cached_info = self._get_cached_token(access_token)
        if cached_info:
            logger.debug(
                f"OAuth token cache hit for client {cached_info.client_id}",
                extra={"context": {"client_id": cached_info.client_id}},
            )
            return cached_info

        # Validate token by fetching user info
        try:
            user_info = await self._fetch_user_info(access_token)
        except Exception as e:
            logger.warning(
                "OAuth authentication failed: Token validation error",
                extra={
                    "context": {
                        "remote": request.remote or "unknown",
                        "path": request.path,
                        "error": str(e),
                    }
                },
            )
            raise AuthenticationError(
                f"Invalid OAuth access token: {str(e)}",
                auth_type="oauth",
            ) from e

        # Extract user ID from user info
        user_id = user_info.get("sub") or user_info.get("id") or user_info.get("user_id")
        if not user_id:
            raise AuthenticationError(
                "Could not extract user ID from OAuth user info",
                auth_type="oauth",
            )

        # Create client info
        client_info = ClientInfo(
            client_id=str(user_id),
            auth_type="oauth",
            metadata={
                "remote": request.remote or "unknown",
                "email": user_info.get("email"),
                "name": user_info.get("name"),
                "user_info": user_info,
            },
        )

        # Cache the token (cache for 5 minutes by default)
        cache_duration = self.config.get("token_cache_duration", 300)
        self._cache_token(access_token, client_info, cache_duration)

        logger.info(
            f"OAuth authentication successful for user {user_id}",
            extra={
                "context": {
                    "client_id": client_info.client_id,
                    "remote": request.remote or "unknown",
                }
            },
        )

        return client_info

    def _extract_token(self, request: web.Request) -> str | None:
        """Extract OAuth access token from request headers.

        Args:
            request: The incoming HTTP request

        Returns:
            Access token if found, None otherwise
        """
        auth_header = request.headers.get("Authorization")
        if auth_header:
            parts = auth_header.strip().split()
            if len(parts) == 2 and parts[0].lower() == "bearer":
                return parts[1]
        return None

    async def _fetch_user_info(self, access_token: str) -> dict[str, Any]:
        """Fetch user information using access token.

        Args:
            access_token: OAuth access token

        Returns:
            User information dictionary

        Raises:
            AuthenticationError: If user info fetch fails
        """
        if not self.userinfo_url:
            raise AuthenticationError(
                "OAuth userinfo_url not configured",
                auth_type="oauth",
            )

        headers = {"Authorization": f"Bearer {access_token}"}

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    self.userinfo_url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise AuthenticationError(
                            f"OAuth userinfo request failed: {response.status} - {error_text}",
                            auth_type="oauth",
                        )
                    result: dict[str, Any] = await response.json()
                    return result
            except aiohttp.ClientError as e:
                raise AuthenticationError(
                    f"OAuth userinfo request error: {str(e)}",
                    auth_type="oauth",
                ) from e

    def _get_cached_token(self, access_token: str) -> ClientInfo | None:
        """Get cached token info if valid.

        Args:
            access_token: OAuth access token

        Returns:
            ClientInfo if token is cached and not expired, None otherwise
        """
        if access_token in self.token_cache:
            client_info, expiry_time = self.token_cache[access_token]
            if time.time() < expiry_time:
                return client_info
            else:
                # Token expired, remove from cache
                del self.token_cache[access_token]
        return None

    def _cache_token(
        self, access_token: str, client_info: ClientInfo, duration: int
    ) -> None:
        """Cache token validation result.

        Args:
            access_token: OAuth access token
            client_info: Client information
            duration: Cache duration in seconds
        """
        expiry_time = time.time() + duration
        self.token_cache[access_token] = (client_info, expiry_time)

    def get_authorization_url(self, state: str | None = None) -> str:
        """Generate OAuth authorization URL.

        Args:
            state: Optional state parameter for CSRF protection

        Returns:
            Authorization URL

        Raises:
            ValueError: If redirect_uri is not configured
        """
        if not self.redirect_uri:
            raise ValueError("redirect_uri must be configured to generate authorization URL")

        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": self.scope,
        }

        if state:
            params["state"] = state

        return f"{self.authorization_url}?{urlencode(params)}"

    async def exchange_code_for_token(self, code: str) -> dict[str, Any]:
        """Exchange authorization code for access token.

        Args:
            code: Authorization code from OAuth callback

        Returns:
            Token response dictionary containing access_token, etc.

        Raises:
            AuthenticationError: If token exchange fails
            ValueError: If redirect_uri is not configured
        """
        if not self.redirect_uri:
            raise ValueError("redirect_uri must be configured to exchange code")

        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": self.redirect_uri,
            "grant_type": "authorization_code",
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    self.token_url, data=data, timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise AuthenticationError(
                            f"OAuth token exchange failed: {response.status} - {error_text}",
                            auth_type="oauth",
                        )
                    result: dict[str, Any] = await response.json()
                    return result
            except aiohttp.ClientError as e:
                raise AuthenticationError(
                    f"OAuth token exchange error: {str(e)}",
                    auth_type="oauth",
                ) from e

    async def refresh_token(self, refresh_token: str) -> dict[str, Any]:
        """Refresh an OAuth access token.

        Args:
            refresh_token: OAuth refresh token

        Returns:
            Token response dictionary containing new access_token, etc.

        Raises:
            AuthenticationError: If token refresh fails
        """
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    self.token_url, data=data, timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise AuthenticationError(
                            f"OAuth token refresh failed: {response.status} - {error_text}",
                            auth_type="oauth",
                        )
                    result: dict[str, Any] = await response.json()
                    return result
            except aiohttp.ClientError as e:
                raise AuthenticationError(
                    f"OAuth token refresh error: {str(e)}",
                    auth_type="oauth",
                ) from e


class JWTProvider(AuthProvider):
    """JWT (JSON Web Token) authentication provider.

    Implements JWT token validation with support for multiple signing algorithms,
    claims validation (audience, issuer, expiration), and optional token generation.

    Supported header format:
    - Authorization: Bearer <jwt_token>

    Attributes:
        secret_key: JWT secret key for verification (for HS256/HS384/HS512)
        public_key: Optional public key for verification (for RS256/RS384/RS512/ES256/ES384/ES512)
        algorithm: JWT signing algorithm (HS256, HS384, HS512, RS256, RS384, RS512, ES256, ES384, ES512)
        audience: Expected JWT audience (optional)
        issuer: Expected JWT issuer (optional)
        leeway: Time leeway in seconds for expiration validation (default: 0)

    Example:
        >>> # Symmetric key (HS256)
        >>> provider = JWTProvider(
        ...     secret_key="your-secret-key",
        ...     algorithm="HS256",
        ...     audience="my-app",
        ...     issuer="auth-server"
        ... )
        >>> client = await provider.authenticate(request)
        >>>
        >>> # Asymmetric key (RS256)
        >>> with open("public_key.pem") as f:
        ...     public_key = f.read()
        >>> provider = JWTProvider(
        ...     secret_key="",  # Not used for RS256
        ...     public_key=public_key,
        ...     algorithm="RS256"
        ... )
    """

    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        audience: str | None = None,
        issuer: str | None = None,
        public_key: str | None = None,
        leeway: int = 0,
        **kwargs: Any,
    ) -> None:
        """Initialize JWT provider.

        Args:
            secret_key: JWT secret key for verification (required for symmetric algorithms)
            algorithm: JWT signing algorithm (default: HS256)
            audience: Expected JWT audience (optional)
            issuer: Expected JWT issuer (optional)
            public_key: Optional public key for asymmetric algorithms (RS256, ES256, etc.)
            leeway: Time leeway in seconds for expiration validation (default: 0)
            **kwargs: Additional JWT configuration
        """
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.audience = audience
        self.issuer = issuer
        self.public_key = public_key
        self.leeway = leeway
        self.config = kwargs

        # Validate algorithm
        valid_algorithms = [
            "HS256",
            "HS384",
            "HS512",
            "RS256",
            "RS384",
            "RS512",
            "ES256",
            "ES384",
            "ES512",
        ]
        if algorithm not in valid_algorithms:
            raise ValueError(
                f"Invalid JWT algorithm: {algorithm}. Supported: {', '.join(valid_algorithms)}"
            )

        # Validate configuration
        if algorithm.startswith("HS") and not secret_key:
            raise ValueError(f"secret_key is required for {algorithm} algorithm")

        if algorithm.startswith(("RS", "ES")) and not public_key:
            logger.warning(
                f"{algorithm} algorithm specified but no public_key provided. "
                "Using secret_key for verification (not recommended for production)."
            )

        logger.info(
            "Initialized JWT provider",
            extra={
                "context": {
                    "algorithm": algorithm,
                    "has_audience": audience is not None,
                    "has_issuer": issuer is not None,
                }
            },
        )

    async def authenticate(self, request: web.Request) -> ClientInfo:
        """Authenticate request using JWT token.

        Args:
            request: The incoming HTTP request

        Returns:
            ClientInfo with authenticated client details

        Raises:
            AuthenticationError: If authentication fails
        """
        # Extract JWT token from Authorization header
        token = self._extract_token(request)

        if not token:
            logger.warning(
                "JWT authentication failed: No token provided",
                extra={
                    "context": {
                        "remote": request.remote or "unknown",
                        "path": request.path,
                    }
                },
            )
            raise AuthenticationError(
                "Authentication required. Provide JWT token in "
                "Authorization header (Bearer <token>)",
                auth_type="jwt",
            )

        # Validate and decode JWT token
        try:
            payload = self._decode_token(token)
        except jwt.ExpiredSignatureError:
            logger.warning(
                "JWT authentication failed: Token expired",
                extra={
                    "context": {
                        "remote": request.remote or "unknown",
                        "path": request.path,
                    }
                },
            )
            raise AuthenticationError(
                "JWT token has expired",
                auth_type="jwt",
            ) from None
        except jwt.InvalidAudienceError:
            logger.warning(
                "JWT authentication failed: Invalid audience",
                extra={
                    "context": {
                        "remote": request.remote or "unknown",
                        "path": request.path,
                    }
                },
            )
            raise AuthenticationError(
                "JWT token has invalid audience",
                auth_type="jwt",
            ) from None
        except jwt.InvalidIssuerError:
            logger.warning(
                "JWT authentication failed: Invalid issuer",
                extra={
                    "context": {
                        "remote": request.remote or "unknown",
                        "path": request.path,
                    }
                },
            )
            raise AuthenticationError(
                "JWT token has invalid issuer",
                auth_type="jwt",
            ) from None
        except jwt.InvalidTokenError as e:
            logger.warning(
                f"JWT authentication failed: {str(e)}",
                extra={
                    "context": {
                        "remote": request.remote or "unknown",
                        "path": request.path,
                        "error": str(e),
                    }
                },
            )
            raise AuthenticationError(
                f"Invalid JWT token: {str(e)}",
                auth_type="jwt",
            ) from e

        # Extract user ID from token claims
        user_id = payload.get("sub") or payload.get("user_id") or payload.get("uid")
        if not user_id:
            raise AuthenticationError(
                "JWT token missing subject (sub) claim",
                auth_type="jwt",
            )

        # Create client info
        client_info = ClientInfo(
            client_id=str(user_id),
            auth_type="jwt",
            metadata={
                "remote": request.remote or "unknown",
                "claims": payload,
                "email": payload.get("email"),
                "name": payload.get("name"),
            },
        )

        logger.info(
            f"JWT authentication successful for user {user_id}",
            extra={
                "context": {
                    "client_id": client_info.client_id,
                    "remote": request.remote or "unknown",
                }
            },
        )

        return client_info

    def _extract_token(self, request: web.Request) -> str | None:
        """Extract JWT token from request headers.

        Args:
            request: The incoming HTTP request

        Returns:
            JWT token if found, None otherwise
        """
        auth_header = request.headers.get("Authorization")
        if auth_header:
            parts = auth_header.strip().split()
            if len(parts) == 2 and parts[0].lower() == "bearer":
                return parts[1]
        return None

    def _decode_token(self, token: str) -> dict[str, Any]:
        """Decode and validate JWT token.

        Args:
            token: JWT token string

        Returns:
            Decoded token payload

        Raises:
            jwt.InvalidTokenError: If token is invalid
        """
        # Determine which key to use for verification
        if self.algorithm.startswith(("RS", "ES")):
            # Use public key for asymmetric algorithms
            verify_key = self.public_key or self.secret_key
        else:
            # Use secret key for symmetric algorithms
            verify_key = self.secret_key

        # Build options for validation
        options: dict[str, Any] = {
            "verify_signature": True,
            "verify_exp": True,
            "verify_aud": self.audience is not None,
            "verify_iss": self.issuer is not None,
        }

        # Decode and validate token
        payload: dict[str, Any] = jwt.decode(
            token,
            verify_key,
            algorithms=[self.algorithm],
            audience=self.audience,
            issuer=self.issuer,
            leeway=self.leeway,
            options=options,
        )

        return payload

    def generate_token(
        self,
        user_id: str,
        expires_in: int = 3600,
        additional_claims: dict[str, Any] | None = None,
    ) -> str:
        """Generate a JWT token.

        Args:
            user_id: User ID to include in token (sub claim)
            expires_in: Token expiration time in seconds (default: 3600 = 1 hour)
            additional_claims: Additional claims to include in token

        Returns:
            Encoded JWT token string

        Raises:
            ValueError: If algorithm requires public/private key pair but only secret_key is set
        """
        if self.algorithm.startswith(("RS", "ES")):
            # For asymmetric algorithms, we need the private key to sign
            # The secret_key field should contain the private key in this case
            if not self.secret_key:
                raise ValueError(
                    f"Private key required in secret_key field to generate tokens with {self.algorithm}"
                )
            signing_key = self.secret_key
        else:
            # For symmetric algorithms, use secret_key
            signing_key = self.secret_key

        # Build token payload
        now = datetime.utcnow()
        payload: dict[str, Any] = {
            "sub": user_id,
            "iat": now,
            "exp": now + timedelta(seconds=expires_in),
        }

        if self.audience:
            payload["aud"] = self.audience

        if self.issuer:
            payload["iss"] = self.issuer

        if additional_claims:
            payload.update(additional_claims)

        # Encode token
        token = jwt.encode(payload, signing_key, algorithm=self.algorithm)

        return token


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
