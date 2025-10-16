"""Structured logging system for Simply-MCP.

This module provides a production-ready structured logging system with:
- JSON and text log formats
- Rich console formatting for text mode
- File logging with rotation
- Contextual logging (request_id, session_id, etc.)
- Thread-safe logging
- Sensitive data sanitization
"""

import logging
import re
import sys
import threading
from contextvars import ContextVar
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from pythonjsonlogger import jsonlogger
from rich.console import Console
from rich.logging import RichHandler
from rich.text import Text

from simply_mcp.core.config import LogConfigModel

# Context variables for contextual logging
_log_context: ContextVar[dict[str, Any]] = ContextVar("log_context", default={})  # noqa: B006, B039

# Singleton logger instance
_logger_instance: logging.Logger | None = None
_logger_lock = threading.Lock()

# Sensitive field patterns to sanitize
SENSITIVE_PATTERNS = [
    r"(?i)(password|passwd|pwd)",
    r"(?i)(api[_-]?key|apikey)",
    r"(?i)(secret|token)",
    r"(?i)(auth|authorization)",
    r"(?i)(credential|cred)",
]


class ContextualJSONFormatter(jsonlogger.JsonFormatter):  # type: ignore[misc, name-defined]
    """JSON formatter that includes contextual information.

    Formats log records as JSON with consistent fields including:
    - timestamp: ISO format timestamp
    - level: Log level (DEBUG, INFO, etc.)
    - message: Log message
    - logger: Logger name
    - request_id: Optional request ID from context
    - session_id: Optional session ID from context
    - context: Additional context data
    """

    def add_fields(
        self,
        log_record: dict[str, Any],
        record: logging.LogRecord,
        message_dict: dict[str, Any],
    ) -> None:
        """Add custom fields to log record.

        Args:
            log_record: Dictionary to add fields to
            record: Python logging record
            message_dict: Additional message dictionary
        """
        super().add_fields(log_record, record, message_dict)

        # Add standard fields
        log_record["timestamp"] = self.formatTime(record, self.datefmt)
        log_record["level"] = record.levelname
        log_record["logger"] = record.name

        # Add contextual information
        context = _log_context.get()
        if context:
            # Add request_id and session_id at top level
            if "request_id" in context:
                log_record["request_id"] = context["request_id"]
            if "session_id" in context:
                log_record["session_id"] = context["session_id"]

            # Add remaining context
            other_context = {
                k: v for k, v in context.items() if k not in ("request_id", "session_id")
            }
            if other_context:
                log_record["context"] = other_context

        # Add extra fields from record
        if hasattr(record, "context"):
            record_context = getattr(record, "context", None)
            if record_context:
                if "context" not in log_record:
                    log_record["context"] = {}
                if isinstance(log_record["context"], dict):
                    log_record["context"].update(record_context)

        # Sanitize sensitive data (update in place)
        sanitized = self._sanitize_dict(log_record)
        log_record.clear()
        log_record.update(sanitized)

    def _sanitize_dict(self, data: dict[str, Any]) -> dict[str, Any]:
        """Recursively sanitize sensitive data in dictionary.

        Args:
            data: Dictionary to sanitize

        Returns:
            Sanitized dictionary
        """
        sanitized: dict[str, Any] = {}
        for key, value in data.items():
            # Check if key matches sensitive pattern
            is_sensitive = any(re.search(pattern, key) for pattern in SENSITIVE_PATTERNS)

            if is_sensitive:
                # Redact sensitive string values
                if isinstance(value, str):
                    sanitized[key] = "***REDACTED***"
                else:
                    sanitized[key] = value
            elif isinstance(value, dict):
                # Recursively sanitize nested dicts
                sanitized[key] = self._sanitize_dict(value)
            elif isinstance(value, list):
                # Sanitize list items
                sanitized[key] = [
                    self._sanitize_dict(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                sanitized[key] = value

        return sanitized


class ContextualRichHandler(RichHandler):
    """Rich handler that includes contextual information in formatted output.

    Provides beautiful console output with:
    - Colored log levels
    - Timestamp
    - Logger name
    - Contextual information (request_id, session_id)
    - Message with syntax highlighting
    """

    def render_message(  # type: ignore[override]
        self, record: logging.LogRecord, message: str
    ) -> Text | str:
        """Render message with contextual information.

        Args:
            record: Python logging record
            message: Log message

        Returns:
            Rendered message with context
        """
        # Get base rendered message
        text = Text.from_markup(message)

        # Add contextual information
        context = _log_context.get()
        if context:
            context_parts = []
            if "request_id" in context:
                context_parts.append(f"request_id: {context['request_id']}")
            if "session_id" in context:
                context_parts.append(f"session_id: {context['session_id']}")

            # Add other context fields
            for key, value in context.items():
                if key not in ("request_id", "session_id"):
                    context_parts.append(f"{key}: {value}")

            if context_parts:
                text.append("\n")
                for i, part in enumerate(context_parts):
                    prefix = "├─" if i < len(context_parts) - 1 else "└─"
                    text.append(f"                      {prefix} ", style="dim")
                    text.append(part, style="cyan")
                    if i < len(context_parts) - 1:
                        text.append("\n")

        # Add extra context from record
        if hasattr(record, "context"):
            record_context = getattr(record, "context", None)
            if record_context and isinstance(record_context, dict):
                text.append("\n")
                extra_items = list(record_context.items())
                for i, (key, value) in enumerate(extra_items):
                    prefix = "├─" if i < len(extra_items) - 1 else "└─"
                    text.append(f"                      {prefix} ", style="dim")
                    text.append(f"{key}: {value}", style="cyan")
                    if i < len(extra_items) - 1:
                        text.append("\n")

        return text


def setup_logger(
    config: LogConfigModel,
    name: str = "simply_mcp",
) -> logging.Logger:
    """Initialize logger from configuration.

    Creates and configures a logger instance with the specified configuration,
    including console and/or file handlers with appropriate formatters.

    Args:
        config: Logging configuration
        name: Logger name (default: "simply_mcp")

    Returns:
        Configured logger instance

    Example:
        >>> config = LogConfigModel(level="INFO", format="json")
        >>> logger = setup_logger(config)
        >>> logger.info("Server started")
    """
    global _logger_instance

    with _logger_lock:
        # Get or create logger
        logger = logging.getLogger(name)

        # Clear existing handlers
        logger.handlers.clear()

        # Set log level
        level = getattr(logging, config.level)
        logger.setLevel(level)

        # Prevent propagation to root logger
        logger.propagate = False

        # Add console handler if enabled
        if config.enable_console:
            if config.format == "json":
                console_handler: logging.Handler = logging.StreamHandler(sys.stdout)
                console_formatter = ContextualJSONFormatter(
                    "%(timestamp)s %(level)s %(name)s %(message)s",
                    timestamp=True,
                )
                console_handler.setFormatter(console_formatter)
            else:  # text format
                console = Console(stderr=False)
                console_handler = ContextualRichHandler(
                    console=console,
                    show_time=True,
                    show_level=True,
                    show_path=True,
                    rich_tracebacks=True,
                    tracebacks_show_locals=True,
                )
                console_handler.setFormatter(logging.Formatter("%(message)s"))

            console_handler.setLevel(level)
            logger.addHandler(console_handler)

        # Add file handler if file path specified
        if config.file:
            log_file = Path(config.file)

            # Create parent directory if it doesn't exist
            log_file.parent.mkdir(parents=True, exist_ok=True)

            # Use rotating file handler (10MB max, 5 backups)
            # Convert Path to string for Windows compatibility
            file_handler: logging.Handler = RotatingFileHandler(
                str(log_file),
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5,
                encoding="utf-8",
            )

            if config.format == "json":
                file_formatter: logging.Formatter = ContextualJSONFormatter(
                    "%(timestamp)s %(level)s %(name)s %(message)s",
                    timestamp=True,
                )
            else:  # text format
                file_formatter = logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S",
                )

            file_handler.setFormatter(file_formatter)
            file_handler.setLevel(level)
            logger.addHandler(file_handler)

        _logger_instance = logger
        return logger


def get_logger(name: str | None = None) -> logging.Logger:
    """Get logger instance (singleton pattern).

    Returns the configured logger instance. If no logger has been set up,
    creates a default logger with INFO level and text format.

    Args:
        name: Optional logger name (default: uses configured logger or "simply_mcp")

    Returns:
        Logger instance

    Example:
        >>> logger = get_logger("my_module")
        >>> logger.info("Processing request")
    """
    global _logger_instance

    # If name is provided, return child logger
    if name is not None:
        if _logger_instance is None:
            # Setup default logger if not initialized
            default_config = LogConfigModel(
                level="INFO",
                format="text",
                enable_console=True,
            )
            setup_logger(default_config)

        assert _logger_instance is not None
        return _logger_instance.getChild(name)

    # Return singleton instance
    if _logger_instance is None:
        # Setup default logger if not initialized
        default_config = LogConfigModel(
            level="INFO",
            format="text",
            enable_console=True,
        )
        setup_logger(default_config)

    assert _logger_instance is not None
    return _logger_instance


class LoggerContext:
    """Context manager for contextual logging.

    Allows setting contextual information (like request_id, session_id) that will
    be automatically included in all log messages within the context.

    Attributes:
        context: Dictionary of context key-value pairs

    Example:
        >>> with LoggerContext(request_id="req-123", session_id="sess-456"):
        ...     logger.info("Processing request")
        # Log will include request_id and session_id

    Example (nested contexts):
        >>> with LoggerContext(session_id="sess-456"):
        ...     with LoggerContext(request_id="req-123"):
        ...         logger.info("Processing request")
        # Log will include both session_id and request_id
    """

    def __init__(self, **context: Any) -> None:
        """Initialize context manager.

        Args:
            **context: Context key-value pairs to set
        """
        self.context = context
        self.token: Any = None
        self.previous_context: dict[str, Any] = {}

    def __enter__(self) -> "LoggerContext":
        """Enter context and set contextual information.

        Returns:
            Self for use in with statement
        """
        # Get current context
        self.previous_context = _log_context.get().copy()

        # Merge with new context
        new_context = self.previous_context.copy()
        new_context.update(self.context)

        # Set new context
        self.token = _log_context.set(new_context)

        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context and restore previous contextual information.

        Args:
            exc_type: Exception type (if any)
            exc_val: Exception value (if any)
            exc_tb: Exception traceback (if any)
        """
        # Restore previous context
        if self.token is not None:
            _log_context.reset(self.token)


def log_with_context(logger: logging.Logger, level: str, message: str, **context: Any) -> None:
    """Log message with additional context.

    Convenience function for logging with extra context without using context manager.

    Args:
        logger: Logger instance
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        message: Log message
        **context: Additional context key-value pairs

    Example:
        >>> log_with_context(logger, "INFO", "User logged in", user_id="123")
    """
    # Get log level method
    log_method = getattr(logger, level.lower())

    # Create LogRecord with extra context
    log_method(message, extra={"context": context})


def sanitize_sensitive_data(data: dict[str, Any] | str, redact: bool = True) -> Any:
    """Sanitize sensitive data from log messages.

    Removes or redacts sensitive information like passwords, API keys, tokens, etc.

    Args:
        data: Data to sanitize (dict or string)
        redact: If True, replace with "***REDACTED***", otherwise remove field

    Returns:
        Sanitized data

    Example:
        >>> sanitize_sensitive_data({"password": "secret123", "user": "john"})
        {'password': '***REDACTED***', 'user': 'john'}
    """
    if isinstance(data, str):
        # Sanitize string by replacing sensitive patterns
        sanitized_str = data
        for pattern in SENSITIVE_PATTERNS:
            sanitized_str = re.sub(
                rf"{pattern}['\"]?\s*[:=]\s*['\"]?[\w\-]+['\"]?",
                r"\1='***REDACTED***'",
                sanitized_str,
                flags=re.IGNORECASE,
            )
        return sanitized_str

    if isinstance(data, dict):
        sanitized_dict: dict[str, Any] = {}
        for key, value in data.items():
            # Check if key matches sensitive pattern
            is_sensitive = any(re.search(pattern, key) for pattern in SENSITIVE_PATTERNS)

            # Recursively process dicts and lists even if key is sensitive
            if isinstance(value, dict):
                # Recursively sanitize nested dicts
                sanitized_dict[key] = sanitize_sensitive_data(value, redact)
            elif isinstance(value, list):
                # Sanitize list items
                sanitized_dict[key] = [
                    sanitize_sensitive_data(item, redact) if isinstance(item, dict) else item
                    for item in value
                ]
            elif is_sensitive:
                # Redact sensitive values (only for non-dict, non-list)
                if redact:
                    if isinstance(value, str):
                        sanitized_dict[key] = "***REDACTED***"
                    else:
                        sanitized_dict[key] = value
                # If not redact, skip the field
            else:
                sanitized_dict[key] = value

        return sanitized_dict

    return data


__all__ = [
    "setup_logger",
    "get_logger",
    "LoggerContext",
    "log_with_context",
    "sanitize_sensitive_data",
    "ContextualJSONFormatter",
    "ContextualRichHandler",
]
