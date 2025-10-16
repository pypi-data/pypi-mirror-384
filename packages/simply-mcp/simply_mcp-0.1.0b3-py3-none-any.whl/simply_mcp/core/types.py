"""Core type definitions for Simply-MCP.

This module defines the fundamental types used throughout the Simply-MCP framework,
including tool configurations, prompt definitions, resource specifications, and
server metadata.

All types are defined as Pydantic BaseModel classes providing runtime validation,
type safety, and excellent IDE support.
"""

from collections.abc import Callable
from typing import Any, Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field

# Type aliases for common patterns
JSONValue = str | int | float | bool | None | dict[str, Any] | list[Any]
JSONDict = dict[str, JSONValue]
HandlerFunction = Callable[..., Any]


# =============================================================================
# Pydantic Models
# =============================================================================


class ToolConfigModel(BaseModel):
    """Configuration for a tool with runtime validation.

    Tools are executable functions that the MCP server exposes to clients.
    They can perform actions, computations, and have side effects.

    Attributes:
        name: Unique identifier for the tool
        description: Human-readable description of what the tool does
        input_schema: JSON Schema defining the tool's input parameters
        handler: The function that implements the tool's logic
        metadata: Optional additional metadata about the tool
    """

    name: str = Field(..., min_length=1, description="Tool name")
    description: str = Field(..., min_length=1, description="Tool description")
    input_schema: dict[str, Any] = Field(..., description="JSON Schema for tool inputs")
    handler: Callable[..., Any] = Field(..., description="Tool handler function")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Extra metadata")

    model_config = ConfigDict(arbitrary_types_allowed=True)


class PromptConfigModel(BaseModel):
    """Configuration for a prompt template with runtime validation.

    Prompts define interaction templates that help structure communication
    with language models.

    Attributes:
        name: Unique identifier for the prompt
        description: Human-readable description of the prompt's purpose
        arguments: Optional list of argument names the prompt accepts
        template: The prompt template string (may include placeholders)
        handler: Optional function to dynamically generate the prompt
        metadata: Optional additional metadata about the prompt
    """

    name: str = Field(..., min_length=1, description="Prompt name")
    description: str = Field(..., min_length=1, description="Prompt description")
    arguments: list[str] = Field(default_factory=list, description="Prompt arguments")
    template: str | None = Field(None, description="Prompt template string")
    handler: Callable[..., Any] | None = Field(None, description="Dynamic prompt handler")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Extra metadata")

    model_config = ConfigDict(arbitrary_types_allowed=True)


class ResourceConfigModel(BaseModel):
    """Configuration for a resource with runtime validation.

    Resources represent data or content that the server can provide,
    such as files, configurations, or computed values.

    Attributes:
        uri: Unique URI identifying the resource (e.g., "file:///path", "config://name")
        name: Human-readable name for the resource
        description: Human-readable description of what the resource provides
        mime_type: MIME type of the resource content (e.g., "application/json")
        handler: Function that returns the resource content
        metadata: Optional additional metadata about the resource
    """

    uri: str = Field(..., min_length=1, description="Resource URI")
    name: str = Field(..., min_length=1, description="Resource name")
    description: str = Field(..., min_length=1, description="Resource description")
    mime_type: str = Field(..., description="MIME type")
    handler: Callable[..., Any] = Field(..., description="Resource handler function")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Extra metadata")

    model_config = ConfigDict(arbitrary_types_allowed=True)


class ServerMetadataModel(BaseModel):
    """Metadata about the MCP server with runtime validation.

    Attributes:
        name: Server name
        version: Server version (semver format recommended)
        description: Optional description of the server's purpose
        author: Optional author information
        homepage: Optional homepage URL
    """

    name: str = Field(..., min_length=1, description="Server name")
    version: str = Field(..., min_length=1, description="Server version")
    description: str | None = Field(None, description="Server description")
    author: str | None = Field(None, description="Author information")
    homepage: str | None = Field(None, description="Homepage URL")

    model_config = ConfigDict(extra="forbid")


# Transport types
TransportType = Literal["stdio", "http", "sse"]


class TransportConfigModel(BaseModel):
    """Configuration for a transport layer with runtime validation.

    Attributes:
        type: Type of transport to use
        host: Host address for network transports (http/sse)
        port: Port number for network transports (http/sse)
        path: Optional path prefix for HTTP endpoints
    """

    type: TransportType = Field(..., description="Transport type")
    host: str | None = Field(None, description="Host address")
    port: int | None = Field(None, ge=1, le=65535, description="Port number")
    path: str | None = Field(None, description="Path prefix")

    model_config = ConfigDict(extra="forbid")


# Progress reporting types
class ProgressUpdateModel(BaseModel):
    """Progress update information with runtime validation.

    Attributes:
        percentage: Progress as a percentage (0-100)
        message: Optional human-readable status message
        current: Optional current step number
        total: Optional total number of steps
    """

    percentage: float = Field(..., ge=0.0, le=100.0, description="Progress percentage")
    message: str | None = Field(None, description="Status message")
    current: int | None = Field(None, ge=0, description="Current step")
    total: int | None = Field(None, ge=0, description="Total steps")

    model_config = ConfigDict(extra="forbid")


class ProgressReporter(Protocol):
    """Protocol for progress reporting.

    This defines the interface for reporting progress during long-running operations.
    """

    async def update(
        self,
        percentage: float,
        message: str | None = None,
        current: int | None = None,
        total: int | None = None,
    ) -> None:
        """Update progress.

        Args:
            percentage: Progress as a percentage (0-100)
            message: Optional status message
            current: Optional current step number
            total: Optional total number of steps
        """
        ...


# Context types
class RequestContextModel(BaseModel):
    """Context information for a request with runtime validation.

    Attributes:
        request_id: Unique identifier for the request
        session_id: Optional session identifier
        user_id: Optional user identifier
        metadata: Additional request metadata
    """

    request_id: str = Field(..., min_length=1, description="Request ID")
    session_id: str | None = Field(None, description="Session ID")
    user_id: str | None = Field(None, description="User ID")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Request metadata")

    model_config = ConfigDict(extra="forbid")


class HandlerContext(Protocol):
    """Protocol for handler execution context.

    This provides handlers with access to request information, progress reporting,
    and server utilities.
    """

    @property
    def request(self) -> RequestContextModel:
        """Get the current request context."""
        ...

    @property
    def progress(self) -> ProgressReporter | None:
        """Get the progress reporter if available."""
        ...

    @property
    def server(self) -> Any:  # Avoid circular import
        """Get reference to the server instance."""
        ...


# API Style detection
APIStyle = Literal["decorator", "functional", "interface", "builder"]


class APIStyleInfoModel(BaseModel):
    """Information about detected API style with runtime validation.

    Attributes:
        style: The detected API style
        confidence: Confidence level (0.0-1.0)
        indicators: List of indicators that led to this detection
    """

    style: APIStyle = Field(..., description="Detected API style")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence level")
    indicators: list[str] = Field(default_factory=list, description="Detection indicators")

    model_config = ConfigDict(extra="forbid")


# Validation types
class ValidationErrorModel(BaseModel):
    """Validation error information with runtime validation.

    Attributes:
        field: Field name that failed validation
        message: Error message
        code: Optional error code
        context: Optional additional context
    """

    field: str = Field(..., min_length=1, description="Field name")
    message: str = Field(..., min_length=1, description="Error message")
    code: str | None = Field(None, description="Error code")
    context: dict[str, Any] = Field(default_factory=dict, description="Additional context")

    model_config = ConfigDict(extra="forbid")


class ValidationResultModel(BaseModel):
    """Result of a validation operation with runtime validation.

    Attributes:
        valid: Whether validation passed
        errors: List of validation errors (if any)
    """

    valid: bool = Field(..., description="Validation status")
    errors: list[ValidationErrorModel] = Field(
        default_factory=list, description="Validation errors"
    )

    model_config = ConfigDict(extra="forbid")


# Security types
class RateLimitConfigModel(BaseModel):
    """Rate limiting configuration with runtime validation.

    Attributes:
        enabled: Whether rate limiting is enabled
        requests_per_minute: Maximum requests per minute
        burst_size: Maximum burst size (token bucket)
    """

    enabled: bool = Field(..., description="Enable rate limiting")
    requests_per_minute: int = Field(..., gt=0, description="Max requests per minute")
    burst_size: int | None = Field(None, gt=0, description="Burst size")

    model_config = ConfigDict(extra="forbid")


AuthType = Literal["api_key", "oauth", "jwt", "none"]


class AuthConfigModel(BaseModel):
    """Authentication configuration with runtime validation.

    Attributes:
        type: Type of authentication
        enabled: Whether authentication is enabled
        api_keys: List of valid API keys (for api_key type)
        oauth_config: OAuth configuration (for oauth type)
        jwt_config: JWT configuration (for jwt type)
    """

    type: AuthType = Field(..., description="Authentication type")
    enabled: bool = Field(..., description="Enable authentication")
    api_keys: list[str] = Field(default_factory=list, description="API keys")
    oauth_config: dict[str, Any] = Field(default_factory=dict, description="OAuth config")
    jwt_config: dict[str, Any] = Field(default_factory=dict, description="JWT config")

    model_config = ConfigDict(extra="forbid")


# Logging types
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
LogFormat = Literal["json", "text"]


class LogConfigModel(BaseModel):
    """Logging configuration with runtime validation.

    Attributes:
        level: Log level
        format: Log format
        file: Optional log file path
        enable_console: Whether to log to console
    """

    level: LogLevel = Field(..., description="Log level")
    format: LogFormat = Field(..., description="Log format")
    file: str | None = Field(None, description="Log file path")
    enable_console: bool = Field(True, description="Enable console logging")

    model_config = ConfigDict(extra="forbid")


# Feature flags
class FeatureFlagsModel(BaseModel):
    """Feature flags configuration with runtime validation.

    Attributes:
        enable_progress: Enable progress reporting
        enable_binary_content: Enable binary content support
        max_request_size: Maximum request size in bytes
    """

    enable_progress: bool = Field(..., description="Enable progress reporting")
    enable_binary_content: bool = Field(..., description="Enable binary content")
    max_request_size: int = Field(..., gt=0, description="Max request size in bytes")

    model_config = ConfigDict(extra="forbid")


# Complete server configuration
class ServerConfigModel(BaseModel):
    """Complete server configuration with runtime validation.

    Attributes:
        metadata: Server metadata
        transport: Transport configuration
        rate_limit: Rate limiting configuration
        auth: Authentication configuration
        logging: Logging configuration
        features: Feature flags
    """

    metadata: ServerMetadataModel = Field(..., description="Server metadata")
    transport: TransportConfigModel = Field(..., description="Transport configuration")
    rate_limit: RateLimitConfigModel | None = Field(None, description="Rate limit config")
    auth: AuthConfigModel | None = Field(None, description="Auth config")
    logging: LogConfigModel | None = Field(None, description="Logging config")
    features: FeatureFlagsModel | None = Field(None, description="Feature flags")

    model_config = ConfigDict(extra="forbid")


__all__ = [
    # Type aliases
    "JSONValue",
    "JSONDict",
    "HandlerFunction",
    # Pydantic Models
    "ToolConfigModel",
    "PromptConfigModel",
    "ResourceConfigModel",
    "ServerMetadataModel",
    "TransportConfigModel",
    "ProgressUpdateModel",
    "RequestContextModel",
    "APIStyleInfoModel",
    "ValidationErrorModel",
    "ValidationResultModel",
    "RateLimitConfigModel",
    "AuthConfigModel",
    "LogConfigModel",
    "FeatureFlagsModel",
    "ServerConfigModel",
    # Enums and Protocols
    "TransportType",
    "ProgressReporter",
    "HandlerContext",
    "APIStyle",
    "AuthType",
    "LogLevel",
    "LogFormat",
]
