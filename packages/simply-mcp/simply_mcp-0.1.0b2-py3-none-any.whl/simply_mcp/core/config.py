"""Configuration management for Simply-MCP.

This module provides Pydantic models for configuration validation and loading
from multiple sources (files, environment variables) with proper precedence.
"""

import os
import sys
from pathlib import Path
from typing import Any

if sys.version_info < (3, 11):
    import tomli as tomllib  # type: ignore[import-not-found]
else:
    import tomllib

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from simply_mcp.core.types import AuthType, LogFormat, LogLevel, TransportType


class ServerMetadataModel(BaseModel):
    """Server metadata configuration.

    Attributes:
        name: Server name
        version: Server version (semver recommended)
        description: Optional server description
        author: Optional author information
        homepage: Optional homepage URL
    """

    name: str = Field(..., min_length=1, description="Server name")
    version: str = Field(..., min_length=1, description="Server version")
    description: str | None = Field(default=None, description="Server description")
    author: str | None = Field(default=None, description="Author information")
    homepage: str | None = Field(default=None, description="Homepage URL")


class TransportConfigModel(BaseModel):
    """Transport configuration.

    Attributes:
        type: Transport type (stdio, http, sse)
        host: Host address for network transports
        port: Port number for network transports
        path: Optional path prefix for HTTP endpoints
        cors_enabled: Whether CORS is enabled for network transports
        cors_origins: List of allowed CORS origins (default: ["*"] for all)
    """

    type: TransportType = Field(default="stdio", description="Transport type")
    host: str = Field(default="0.0.0.0", description="Host address")
    port: int = Field(default=3000, ge=1, le=65535, description="Port number")
    path: str | None = Field(default=None, description="Path prefix")
    cors_enabled: bool = Field(default=True, description="Enable CORS")
    cors_origins: list[str] | None = Field(default=None, description="Allowed CORS origins")


class RateLimitConfigModel(BaseModel):
    """Rate limiting configuration.

    Attributes:
        enabled: Whether rate limiting is enabled
        requests_per_minute: Maximum requests per minute
        burst_size: Maximum burst size (token bucket)
    """

    enabled: bool = Field(default=True, description="Enable rate limiting")
    requests_per_minute: int = Field(default=60, ge=1, description="Requests per minute")
    burst_size: int = Field(default=10, ge=1, description="Burst size")


class AuthConfigModel(BaseModel):
    """Authentication configuration.

    Attributes:
        type: Authentication type
        enabled: Whether authentication is enabled
        api_keys: List of valid API keys (for api_key type)
        oauth_config: OAuth configuration (for oauth type)
        jwt_config: JWT configuration (for jwt type)
    """

    type: AuthType = Field(default="none", description="Authentication type")
    enabled: bool = Field(default=False, description="Enable authentication")
    api_keys: list[str] = Field(default_factory=list, description="Valid API keys")
    oauth_config: dict[str, Any] = Field(default_factory=dict, description="OAuth config")
    jwt_config: dict[str, Any] = Field(default_factory=dict, description="JWT config")

    @field_validator("api_keys")
    @classmethod
    def validate_api_keys(cls, v: list[str], info: Any) -> list[str]:
        """Validate API keys are provided when type is api_key."""
        auth_type = info.data.get("type")
        enabled = info.data.get("enabled", False)
        if enabled and auth_type == "api_key" and not v:
            raise ValueError("api_keys must be provided when auth type is api_key")
        return v


class LogConfigModel(BaseModel):
    """Logging configuration.

    Attributes:
        level: Log level
        format: Log format (json or text)
        file: Optional log file path
        enable_console: Whether to log to console
    """

    level: LogLevel = Field(default="INFO", description="Log level")
    format: LogFormat = Field(default="json", description="Log format")
    file: str | None = Field(default=None, description="Log file path")
    enable_console: bool = Field(default=True, description="Enable console logging")


class FeatureFlagsModel(BaseModel):
    """Feature flags configuration.

    Attributes:
        enable_progress: Enable progress reporting
        enable_binary_content: Enable binary content support
        max_request_size: Maximum request size in bytes
    """

    enable_progress: bool = Field(default=True, description="Enable progress reporting")
    enable_binary_content: bool = Field(
        default=True, description="Enable binary content support"
    )
    max_request_size: int = Field(
        default=10485760, ge=1, description="Max request size (bytes)"
    )  # 10MB


class SimplyMCPConfig(BaseSettings):
    """Complete Simply-MCP configuration.

    This is the root configuration model that combines all subsystems.
    Can be loaded from TOML/JSON files and environment variables.

    Attributes:
        server: Server metadata
        transport: Transport configuration
        rate_limit: Rate limiting configuration
        auth: Authentication configuration
        logging: Logging configuration
        features: Feature flags
    """

    model_config = SettingsConfigDict(
        env_prefix="SIMPLY_MCP_",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )

    server: ServerMetadataModel = Field(
        default_factory=lambda: ServerMetadataModel(name="simply-mcp-server", version="0.1.0"),
        description="Server metadata",
    )
    transport: TransportConfigModel = Field(
        default_factory=lambda: TransportConfigModel(),
        description="Transport configuration",
    )
    rate_limit: RateLimitConfigModel = Field(
        default_factory=lambda: RateLimitConfigModel(),
        description="Rate limiting configuration",
    )
    auth: AuthConfigModel = Field(
        default_factory=lambda: AuthConfigModel(),
        description="Authentication configuration",
    )
    logging: LogConfigModel = Field(
        default_factory=lambda: LogConfigModel(),
        description="Logging configuration",
    )
    features: FeatureFlagsModel = Field(
        default_factory=lambda: FeatureFlagsModel(),
        description="Feature flags",
    )


def load_config_from_file(file_path: str | Path) -> SimplyMCPConfig:
    """Load configuration from a TOML or JSON file.

    Args:
        file_path: Path to configuration file (.toml or .json)

    Returns:
        Loaded and validated configuration

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file format is invalid
        ValidationError: If configuration is invalid

    Example:
        >>> config = load_config_from_file("simplymcp.config.toml")
        >>> print(config.server.name)
        my-mcp-server
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {file_path}")

    suffix = path.suffix.lower()

    if suffix == ".toml":
        with open(path, "rb") as f:
            data = tomllib.load(f)
    elif suffix == ".json":
        import json

        with open(path) as f:
            data = json.load(f)
    else:
        raise ValueError(f"Unsupported configuration file format: {suffix}")

    return SimplyMCPConfig(**data)


def load_config_from_env() -> SimplyMCPConfig:
    """Load configuration from environment variables.

    Environment variables should be prefixed with SIMPLY_MCP_ and use
    double underscores for nested values.

    Returns:
        Configuration loaded from environment

    Example:
        >>> # With env: SIMPLY_MCP_SERVER__NAME=my-server
        >>> config = load_config_from_env()
        >>> print(config.server.name)
        my-server
    """
    return SimplyMCPConfig()


def _merge_env_vars(config_data: dict[str, Any]) -> dict[str, Any]:
    """Merge environment variables into config data.

    Environment variables with SIMPLY_MCP_ prefix override config values.
    Uses double underscore (__) as delimiter for nested keys.

    Args:
        config_data: Base configuration dictionary from file

    Returns:
        Merged configuration dictionary with env vars applied

    Example:
        >>> # With env: SIMPLY_MCP_TRANSPORT__PORT=9999
        >>> config = {"transport": {"port": 3000}}
        >>> merged = _merge_env_vars(config)
        >>> merged["transport"]["port"]
        9999
    """
    import copy

    # Create a deep copy to avoid modifying the original
    merged = copy.deepcopy(config_data)

    # Parse environment variables with SIMPLY_MCP_ prefix
    prefix = "SIMPLY_MCP_"

    for env_key, env_value in os.environ.items():
        if not env_key.startswith(prefix):
            continue

        # Remove prefix and split by delimiter
        key_path = env_key[len(prefix):].lower().split("__")

        # Navigate/create nested structure
        current = merged
        for key_part in key_path[:-1]:
            if key_part not in current:
                current[key_part] = {}
            current = current[key_part]

        # Set the final value with type conversion
        final_key = key_path[-1]

        # Find reference type from original config to preserve types
        ref_value: Any = merged
        for key_part in key_path[:-1]:
            if isinstance(ref_value, dict) and key_part in ref_value:
                ref_value = ref_value[key_part]
            else:
                ref_value = None
                break

        # Convert based on reference type if available
        if isinstance(ref_value, dict) and final_key in ref_value:
            original_value = ref_value[final_key]

            if isinstance(original_value, bool):
                current[final_key] = env_value.lower() in ("true", "1", "yes", "on")
            elif isinstance(original_value, int):
                current[final_key] = int(env_value)
            elif isinstance(original_value, float):
                current[final_key] = float(env_value)
            else:
                current[final_key] = env_value
        else:
            # No reference type - try smart conversion
            try:
                current[final_key] = int(env_value)
            except ValueError:
                current[final_key] = env_value

    return merged


def load_config(
    file_path: str | Path | None = None,
    env_override: bool = True,
) -> SimplyMCPConfig:
    """Load configuration from file and/or environment with precedence.

    Precedence (highest to lowest):
    1. Environment variables
    2. Configuration file
    3. Defaults

    Args:
        file_path: Optional path to configuration file
        env_override: Whether environment variables override file config

    Returns:
        Merged and validated configuration

    Example:
        >>> # Load from file with env override
        >>> config = load_config("simplymcp.config.toml")
        >>>
        >>> # Load from env only
        >>> config = load_config()
        >>>
        >>> # Load from file only (no env override)
        >>> config = load_config("simplymcp.config.toml", env_override=False)
    """
    # Start with defaults
    if file_path is None:
        # Check for default config file
        default_paths = [
            Path("simplymcp.config.toml"),
            Path("simplymcp.config.json"),
            Path(".simplymcp.toml"),
            Path(".simplymcp.json"),
        ]

        for default_path in default_paths:
            if default_path.exists():
                file_path = default_path
                break

    # Load from file if provided
    if file_path is not None:
        config_data = load_config_from_file(file_path).model_dump()
    else:
        config_data = {}

    # Merge with environment variables if enabled
    if env_override:
        # Manually merge environment variables into config_data
        # Environment variables should override file values
        merged_data = _merge_env_vars(config_data)
        config = SimplyMCPConfig.model_validate(merged_data)
    else:
        # Construct without env override
        config = SimplyMCPConfig.model_validate(config_data)

    return config


def validate_config(config: SimplyMCPConfig | dict[str, Any]) -> bool:
    """Validate a configuration object or dictionary.

    Args:
        config: Configuration to validate

    Returns:
        True if valid

    Raises:
        ValidationError: If configuration is invalid

    Example:
        >>> config_dict = {"server": {"name": "test", "version": "1.0.0"}}
        >>> validate_config(config_dict)
        True
    """
    if isinstance(config, dict):
        SimplyMCPConfig(**config)
    elif isinstance(config, SimplyMCPConfig):
        # Already validated
        pass
    else:
        raise TypeError(f"Expected SimplyMCPConfig or dict, got {type(config)}")

    return True


def get_default_config() -> SimplyMCPConfig:
    """Get default configuration with all defaults filled in.

    Returns:
        Default configuration

    Example:
        >>> config = get_default_config()
        >>> print(config.server.name)
        simply-mcp-server
    """
    return SimplyMCPConfig()


__all__ = [
    # Models
    "ServerMetadataModel",
    "TransportConfigModel",
    "RateLimitConfigModel",
    "AuthConfigModel",
    "LogConfigModel",
    "FeatureFlagsModel",
    "SimplyMCPConfig",
    # Functions
    "load_config_from_file",
    "load_config_from_env",
    "load_config",
    "validate_config",
    "get_default_config",
]
