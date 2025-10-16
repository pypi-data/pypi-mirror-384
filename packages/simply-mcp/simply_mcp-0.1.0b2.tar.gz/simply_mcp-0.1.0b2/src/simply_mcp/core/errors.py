"""Exception hierarchy for Simply-MCP framework.

This module defines a comprehensive exception hierarchy for all error scenarios
in the Simply-MCP framework. All exceptions are designed to be:
- User-friendly with clear error messages
- Serializable to JSON for MCP protocol error responses
- Structured with error codes for programmatic handling
- Suitable for logging and debugging

The hierarchy follows Python exception best practices and provides specific
exceptions for different subsystems (configuration, transport, handlers, etc.).
"""

from typing import Any


class SimplyMCPError(Exception):
    """Base exception for all Simply-MCP errors.

    This is the root of the exception hierarchy. All Simply-MCP exceptions
    inherit from this class, allowing for easy catching of framework errors.

    Attributes:
        message: Human-readable error message
        code: Machine-readable error code (e.g., "CONFIG_NOT_FOUND")
        context: Optional additional context about the error
    """

    def __init__(
        self,
        message: str,
        code: str = "SIMPLY_MCP_ERROR",
        context: dict[str, Any] | None = None,
    ) -> None:
        """Initialize a Simply-MCP error.

        Args:
            message: Human-readable error message
            code: Machine-readable error code
            context: Optional additional context dictionary
        """
        super().__init__(message)
        self.message = message
        self.code = code
        self.context = context or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert error to dictionary for JSON serialization.

        Returns:
            Dictionary representation suitable for JSON serialization
        """
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "code": self.code,
            "context": self.context,
        }

    def __str__(self) -> str:
        """Return string representation of error."""
        return f"[{self.code}] {self.message}"

    def __repr__(self) -> str:
        """Return detailed representation of error."""
        return f"{self.__class__.__name__}(message={self.message!r}, code={self.code!r})"


# Configuration Errors


class ConfigurationError(SimplyMCPError):
    """Base exception for configuration-related errors.

    Raised when there are issues with server configuration, including
    loading, parsing, or validating configuration files.
    """

    def __init__(
        self,
        message: str,
        code: str = "CONFIG_ERROR",
        context: dict[str, Any] | None = None,
    ) -> None:
        """Initialize a configuration error."""
        super().__init__(message, code, context)


class ConfigFileNotFoundError(ConfigurationError):
    """Exception raised when configuration file cannot be found.

    This error occurs when the specified configuration file path does not exist
    or is not accessible.
    """

    def __init__(
        self,
        file_path: str,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Initialize a config file not found error.

        Args:
            file_path: Path to the missing configuration file
            context: Optional additional context
        """
        message = f"Configuration file not found: {file_path}"
        context = context or {}
        context["file_path"] = file_path
        super().__init__(message, "CONFIG_NOT_FOUND", context)


class ConfigValidationError(ConfigurationError):
    """Exception raised when configuration validation fails.

    This error occurs when configuration values fail Pydantic validation
    or business logic validation.
    """

    def __init__(
        self,
        message: str,
        field: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Initialize a config validation error.

        Args:
            message: Validation error message
            field: Optional field name that failed validation
            context: Optional additional context
        """
        context = context or {}
        if field:
            context["field"] = field
        super().__init__(message, "CONFIG_VALIDATION_FAILED", context)


class ConfigFormatError(ConfigurationError):
    """Exception raised when configuration file format is unsupported.

    This error occurs when trying to load a configuration file with an
    unsupported format (e.g., not TOML or JSON).
    """

    def __init__(
        self,
        file_format: str,
        supported_formats: list[str] | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Initialize a config format error.

        Args:
            file_format: The unsupported file format
            supported_formats: Optional list of supported formats
            context: Optional additional context
        """
        formats = supported_formats or [".toml", ".json"]
        message = f"Unsupported configuration format: {file_format}. Supported: {', '.join(formats)}"
        context = context or {}
        context["file_format"] = file_format
        context["supported_formats"] = formats
        super().__init__(message, "CONFIG_FORMAT_UNSUPPORTED", context)


# Transport Errors


class TransportError(SimplyMCPError):
    """Base exception for transport-related errors.

    Raised when there are issues with transport initialization, connection,
    or message handling.
    """

    def __init__(
        self,
        message: str,
        code: str = "TRANSPORT_ERROR",
        context: dict[str, Any] | None = None,
    ) -> None:
        """Initialize a transport error."""
        super().__init__(message, code, context)


class ConnectionError(TransportError):
    """Exception raised when transport connection fails.

    This error occurs when establishing or maintaining a connection fails,
    such as network errors, timeout, or connection refused.
    """

    def __init__(
        self,
        message: str,
        host: str | None = None,
        port: int | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Initialize a connection error.

        Args:
            message: Connection error message
            host: Optional host address
            port: Optional port number
            context: Optional additional context
        """
        context = context or {}
        if host:
            context["host"] = host
        if port:
            context["port"] = port
        super().__init__(message, "CONNECTION_FAILED", context)


class TransportNotSupportedError(TransportError):
    """Exception raised when transport type is not supported.

    This error occurs when trying to use a transport type that is not
    implemented or recognized.
    """

    def __init__(
        self,
        transport_type: str,
        supported_types: list[str] | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Initialize a transport not supported error.

        Args:
            transport_type: The unsupported transport type
            supported_types: Optional list of supported transport types
            context: Optional additional context
        """
        types = supported_types or ["stdio", "http", "sse"]
        message = f"Transport type not supported: {transport_type}. Supported: {', '.join(types)}"
        context = context or {}
        context["transport_type"] = transport_type
        context["supported_types"] = types
        super().__init__(message, "TRANSPORT_NOT_SUPPORTED", context)


class MessageError(TransportError):
    """Exception raised when message encoding/decoding fails.

    This error occurs when there are issues with message serialization,
    deserialization, or protocol violations.
    """

    def __init__(
        self,
        message: str,
        message_type: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Initialize a message error.

        Args:
            message: Message error description
            message_type: Optional message type
            context: Optional additional context
        """
        context = context or {}
        if message_type:
            context["message_type"] = message_type
        super().__init__(message, "MESSAGE_ERROR", context)


# Handler Errors


class HandlerError(SimplyMCPError):
    """Base exception for handler-related errors.

    Raised when there are issues with tool, prompt, or resource handlers,
    including registration, lookup, and execution errors.
    """

    def __init__(
        self,
        message: str,
        code: str = "HANDLER_ERROR",
        context: dict[str, Any] | None = None,
    ) -> None:
        """Initialize a handler error."""
        super().__init__(message, code, context)


class HandlerNotFoundError(HandlerError):
    """Exception raised when a handler cannot be found.

    This error occurs when trying to execute a tool, prompt, or resource
    that has not been registered.
    """

    def __init__(
        self,
        handler_name: str,
        handler_type: str = "handler",
        context: dict[str, Any] | None = None,
    ) -> None:
        """Initialize a handler not found error.

        Args:
            handler_name: Name of the missing handler
            handler_type: Type of handler (tool, prompt, resource)
            context: Optional additional context
        """
        message = f"{handler_type.capitalize()} not found: {handler_name}"
        context = context or {}
        context["handler_name"] = handler_name
        context["handler_type"] = handler_type
        super().__init__(message, "HANDLER_NOT_FOUND", context)


class HandlerExecutionError(HandlerError):
    """Exception raised when handler execution fails.

    This error wraps exceptions that occur during tool, prompt, or
    resource handler execution.
    """

    def __init__(
        self,
        handler_name: str,
        original_error: Exception,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Initialize a handler execution error.

        Args:
            handler_name: Name of the handler that failed
            original_error: The original exception that was raised
            context: Optional additional context
        """
        message = f"Handler execution failed: {handler_name} - {str(original_error)}"
        context = context or {}
        context["handler_name"] = handler_name
        context["original_error"] = str(original_error)
        context["error_type"] = type(original_error).__name__
        super().__init__(message, "HANDLER_EXECUTION_FAILED", context)
        self.original_error = original_error


class InvalidHandlerSignatureError(HandlerError):
    """Exception raised when handler function signature is invalid.

    This error occurs when a handler function does not match the expected
    signature or type hints.
    """

    def __init__(
        self,
        handler_name: str,
        expected_signature: str,
        actual_signature: str,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Initialize an invalid handler signature error.

        Args:
            handler_name: Name of the handler with invalid signature
            expected_signature: Description of expected signature
            actual_signature: Description of actual signature
            context: Optional additional context
        """
        message = (
            f"Invalid handler signature for {handler_name}. "
            f"Expected: {expected_signature}, Got: {actual_signature}"
        )
        context = context or {}
        context["handler_name"] = handler_name
        context["expected_signature"] = expected_signature
        context["actual_signature"] = actual_signature
        super().__init__(message, "INVALID_HANDLER_SIGNATURE", context)


# Validation Errors


class ValidationError(SimplyMCPError):
    """Base exception for validation-related errors.

    Raised when data validation fails, including schema validation,
    type checking, and business logic validation.
    """

    def __init__(
        self,
        message: str,
        code: str = "VALIDATION_ERROR",
        context: dict[str, Any] | None = None,
    ) -> None:
        """Initialize a validation error."""
        super().__init__(message, code, context)


class SchemaValidationError(ValidationError):
    """Exception raised when JSON schema validation fails.

    This error occurs when data does not conform to its JSON schema,
    typically for tool inputs or resource content.
    """

    def __init__(
        self,
        message: str,
        schema_path: str | None = None,
        validation_errors: list[str] | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Initialize a schema validation error.

        Args:
            message: Validation error message
            schema_path: Optional JSON path to the failing schema element
            validation_errors: Optional list of specific validation errors
            context: Optional additional context
        """
        context = context or {}
        if schema_path:
            context["schema_path"] = schema_path
        if validation_errors:
            context["validation_errors"] = validation_errors
        super().__init__(message, "SCHEMA_VALIDATION_FAILED", context)


class TypeValidationError(ValidationError):
    """Exception raised when type checking fails.

    This error occurs when a value does not match its expected type,
    such as passing a string where an integer is required.
    """

    def __init__(
        self,
        field_name: str,
        expected_type: str,
        actual_type: str,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Initialize a type validation error.

        Args:
            field_name: Name of the field with type error
            expected_type: Expected type name
            actual_type: Actual type name
            context: Optional additional context
        """
        message = (
            f"Type validation failed for '{field_name}': "
            f"expected {expected_type}, got {actual_type}"
        )
        context = context or {}
        context["field_name"] = field_name
        context["expected_type"] = expected_type
        context["actual_type"] = actual_type
        super().__init__(message, "TYPE_VALIDATION_FAILED", context)


class RequiredFieldError(ValidationError):
    """Exception raised when a required field is missing.

    This error occurs when a required parameter or field is not provided.
    """

    def __init__(
        self,
        field_name: str,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Initialize a required field error.

        Args:
            field_name: Name of the missing required field
            context: Optional additional context
        """
        message = f"Required field missing: {field_name}"
        context = context or {}
        context["field_name"] = field_name
        super().__init__(message, "REQUIRED_FIELD_MISSING", context)


# Security Errors


class SecurityError(SimplyMCPError):
    """Base exception for security-related errors.

    Raised when there are security violations, including authentication
    failures, authorization errors, and rate limiting.
    """

    def __init__(
        self,
        message: str,
        code: str = "SECURITY_ERROR",
        context: dict[str, Any] | None = None,
    ) -> None:
        """Initialize a security error."""
        super().__init__(message, code, context)


class AuthenticationError(SecurityError):
    """Exception raised when authentication fails.

    This error occurs when credentials are invalid, missing, or expired.
    """

    def __init__(
        self,
        message: str = "Authentication failed",
        auth_type: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Initialize an authentication error.

        Args:
            message: Authentication error message
            auth_type: Optional authentication type (api_key, oauth, jwt)
            context: Optional additional context
        """
        context = context or {}
        if auth_type:
            context["auth_type"] = auth_type
        super().__init__(message, "AUTHENTICATION_FAILED", context)


class AuthorizationError(SecurityError):
    """Exception raised when authorization fails.

    This error occurs when a user does not have sufficient permissions
    to perform an action.
    """

    def __init__(
        self,
        message: str = "Insufficient permissions",
        required_permission: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Initialize an authorization error.

        Args:
            message: Authorization error message
            required_permission: Optional required permission
            context: Optional additional context
        """
        context = context or {}
        if required_permission:
            context["required_permission"] = required_permission
        super().__init__(message, "AUTHORIZATION_FAILED", context)


class RateLimitExceededError(SecurityError):
    """Exception raised when rate limit is exceeded.

    This error occurs when a client exceeds the configured rate limit
    for requests.
    """

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        limit: int | None = None,
        retry_after: int | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Initialize a rate limit exceeded error.

        Args:
            message: Rate limit error message
            limit: Optional rate limit (requests per minute)
            retry_after: Optional seconds until retry is allowed
            context: Optional additional context
        """
        context = context or {}
        if limit:
            context["limit"] = limit
        if retry_after:
            context["retry_after"] = retry_after
        super().__init__(message, "RATE_LIMIT_EXCEEDED", context)


__all__ = [
    # Base error
    "SimplyMCPError",
    # Configuration errors
    "ConfigurationError",
    "ConfigFileNotFoundError",
    "ConfigValidationError",
    "ConfigFormatError",
    # Transport errors
    "TransportError",
    "ConnectionError",
    "TransportNotSupportedError",
    "MessageError",
    # Handler errors
    "HandlerError",
    "HandlerNotFoundError",
    "HandlerExecutionError",
    "InvalidHandlerSignatureError",
    # Validation errors
    "ValidationError",
    "SchemaValidationError",
    "TypeValidationError",
    "RequiredFieldError",
    # Security errors
    "SecurityError",
    "AuthenticationError",
    "AuthorizationError",
    "RateLimitExceededError",
]
