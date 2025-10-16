"""Core module for Simply-MCP framework.

This module contains the core functionality including:
- Type definitions
- Configuration management
- Error handling
"""

from simply_mcp.core.config import (
    AuthConfigModel,
    FeatureFlagsModel,
    LogConfigModel,
    RateLimitConfigModel,
    ServerMetadataModel,
    SimplyMCPConfig,
    TransportConfigModel,
    get_default_config,
    load_config,
    load_config_from_env,
    load_config_from_file,
    validate_config,
)
from simply_mcp.core.errors import (
    AuthenticationError,
    AuthorizationError,
    ConfigFileNotFoundError,
    ConfigFormatError,
    ConfigurationError,
    ConfigValidationError,
    ConnectionError,
    HandlerError,
    HandlerExecutionError,
    HandlerNotFoundError,
    InvalidHandlerSignatureError,
    MessageError,
    RateLimitExceededError,
    RequiredFieldError,
    SchemaValidationError,
    SecurityError,
    SimplyMCPError,
    TransportError,
    TransportNotSupportedError,
    TypeValidationError,
    ValidationError,
)
from simply_mcp.core.types import (
    APIStyle,
    APIStyleInfoModel,
    AuthType,
    HandlerContext,
    HandlerFunction,
    JSONDict,
    JSONValue,
    LogFormat,
    LogLevel,
    ProgressReporter,
    ProgressUpdateModel,
    PromptConfigModel,
    RequestContextModel,
    ResourceConfigModel,
    ToolConfigModel,
    TransportType,
    ValidationErrorModel,
    ValidationResultModel,
)

__all__ = [
    # Config
    "AuthConfigModel",
    "FeatureFlagsModel",
    "LogConfigModel",
    "RateLimitConfigModel",
    "ServerMetadataModel",
    "SimplyMCPConfig",
    "TransportConfigModel",
    "get_default_config",
    "load_config",
    "load_config_from_env",
    "load_config_from_file",
    "validate_config",
    # Errors - Base
    "SimplyMCPError",
    # Errors - Configuration
    "ConfigurationError",
    "ConfigFileNotFoundError",
    "ConfigValidationError",
    "ConfigFormatError",
    # Errors - Transport
    "TransportError",
    "ConnectionError",
    "TransportNotSupportedError",
    "MessageError",
    # Errors - Handlers
    "HandlerError",
    "HandlerNotFoundError",
    "HandlerExecutionError",
    "InvalidHandlerSignatureError",
    # Errors - Validation
    "ValidationError",
    "SchemaValidationError",
    "TypeValidationError",
    "RequiredFieldError",
    # Errors - Security
    "SecurityError",
    "AuthenticationError",
    "AuthorizationError",
    "RateLimitExceededError",
    # Types
    "APIStyle",
    "APIStyleInfoModel",
    "AuthType",
    "HandlerContext",
    "HandlerFunction",
    "JSONDict",
    "JSONValue",
    "LogFormat",
    "LogLevel",
    "ProgressReporter",
    "ProgressUpdateModel",
    "PromptConfigModel",
    "RequestContextModel",
    "ResourceConfigModel",
    "ToolConfigModel",
    "TransportType",
    "ValidationErrorModel",
    "ValidationResultModel",
]
