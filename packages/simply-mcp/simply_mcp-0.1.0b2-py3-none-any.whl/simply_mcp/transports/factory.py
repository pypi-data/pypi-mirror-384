"""Transport factory for creating MCP transports.

This module provides a factory pattern for creating different types of
MCP transports (HTTP, SSE) based on configuration.
"""

from simply_mcp.core.config import SimplyMCPConfig
from simply_mcp.core.server import SimplyMCPServer
from simply_mcp.transports.http import HTTPTransport
from simply_mcp.transports.sse import SSETransport

# Type alias for transport types
Transport = HTTPTransport | SSETransport


def create_transport(
    transport_type: str,
    server: SimplyMCPServer,
    config: SimplyMCPConfig,
) -> Transport:
    """Create transport based on type.

    This factory function creates the appropriate transport implementation
    based on the transport_type parameter.

    Args:
        transport_type: Type of transport ("http" or "sse")
        server: MCP server instance
        config: Server configuration

    Returns:
        Transport instance (HTTPTransport or SSETransport)

    Raises:
        ValueError: If transport_type is not supported

    Example:
        >>> server = SimplyMCPServer()
        >>> config = get_default_config()
        >>> transport = create_transport("http", server, config)
        >>> await transport.start()
    """
    transport_type = transport_type.lower()

    if transport_type == "http":
        return HTTPTransport(
            server=server,
            host=config.transport.host,
            port=config.transport.port,
            cors_enabled=config.transport.cors_enabled,
            cors_origins=config.transport.cors_origins,
        )

    elif transport_type == "sse":
        return SSETransport(
            server=server,
            host=config.transport.host,
            port=config.transport.port,
            cors_enabled=config.transport.cors_enabled,
            cors_origins=config.transport.cors_origins,
        )

    else:
        raise ValueError(
            f"Unsupported transport type: {transport_type}. "
            f"Supported types: http, sse"
        )


__all__ = ["create_transport", "Transport"]
