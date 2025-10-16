"""Programmatic API for Simply-MCP server construction.

This module provides the BuildMCPServer class for programmatic MCP server construction.
It offers explicit control over server configuration and component registration,
mirroring the TypeScript implementation's BuildMCPServer class.

The programmatic API supports:
- Explicit server construction with full control
- Method chaining for ergonomic server configuration
- Dual registration (add_* methods and @decorator style)
- Auto-schema generation from type hints
- Pydantic model integration
- Full integration with SimplyMCPServer

Example:
    Basic programmatic pattern:
    >>> from simply_mcp import BuildMCPServer
    >>>
    >>> server = BuildMCPServer(name="my-server", version="1.0.0")
    >>>
    >>> # Register tools with decorator
    >>> @server.tool()
    >>> def add(a: int, b: int) -> int:
    ...     '''Add two numbers.'''
    ...     return a + b
    >>>
    >>> # Or register directly
    >>> def multiply(a: float, b: float) -> float:
    ...     return a * b
    >>>
    >>> server.add_tool("multiply", multiply, description="Multiply numbers")
    >>>
    >>> # Method chaining for configuration
    >>> await server.configure(log_level="DEBUG").initialize().run()
"""

import functools
import inspect
from collections.abc import Callable
from typing import Any, TypeVar

try:
    from pydantic import BaseModel
    PYDANTIC_AVAILABLE = True
except ImportError:
    BaseModel = object  # type: ignore[assignment,misc]
    PYDANTIC_AVAILABLE = False

from simply_mcp.core.config import (
    ServerMetadataModel,
    SimplyMCPConfig,
    get_default_config,
)
from simply_mcp.core.server import SimplyMCPServer
from simply_mcp.core.types import PromptConfigModel, ResourceConfigModel, ToolConfigModel
from simply_mcp.validation.schema import (
    auto_generate_schema,
    extract_description_from_docstring,
    generate_schema_from_pydantic,
)

# Type variables
F = TypeVar('F', bound=Callable[..., Any])


class BuildMCPServer:
    """Programmatic API for MCP server construction.

    Provides explicit control over MCP server construction and configuration.
    Supports method chaining for ergonomic server building.

    This class wraps SimplyMCPServer and provides the programmatic API
    for building servers. It supports both direct registration (add_tool)
    and decorator-style registration (@server.tool).

    Mirrors the TypeScript BuildMCPServer class for cross-language consistency.

    Attributes:
        name: Server name
        version: Server version
        description: Server description
        config: Server configuration
        server: Underlying SimplyMCPServer instance

    Example:
        >>> server = BuildMCPServer(name="calc", version="1.0.0")
        >>>
        >>> @server.tool()
        >>> def add(a: int, b: int) -> int:
        ...     return a + b
        >>>
        >>> server.add_prompt("greet", lambda name: f"Hello {name}")
        >>> await server.initialize().run()
    """

    def __init__(
        self,
        name: str = "simply-mcp-server",
        version: str = "0.1.0",
        description: str | None = None,
        config: SimplyMCPConfig | None = None,
    ) -> None:
        """Initialize a new MCP server builder.

        Args:
            name: Server name
            version: Server version
            description: Server description
            config: Optional configuration (creates default if not provided)

        Example:
            >>> server = BuildMCPServer(name="my-server", version="1.0.0")
            >>> server = BuildMCPServer()  # Use defaults
        """
        # Create or update config
        if config is not None:
            self.config = config
        else:
            # Create default config with custom metadata
            self.config = get_default_config()
            self.config.server = ServerMetadataModel(
                name=name,
                version=version,
                description=description,
            )

        # Store metadata for easy access
        self.name = name
        self.version = version
        self.description = description

        # Create underlying server instance
        self.server = SimplyMCPServer(self.config)

    # Tool Management

    def add_tool(
        self,
        name: str,
        handler: Callable[..., Any],
        description: str | None = None,
        input_schema: dict[str, Any] | type[BaseModel] | None = None,
    ) -> "BuildMCPServer":
        """Add a tool to the server.

        Args:
            name: Tool name
            handler: Tool handler function
            description: Tool description (auto-extracted if not provided)
            input_schema: Input schema (auto-generated if not provided)

        Returns:
            Self for method chaining

        Raises:
            ValidationError: If a tool with the same name already exists

        Example:
            >>> def add(a: int, b: int) -> int:
            ...     return a + b
            >>>
            >>> mcp.add_tool("add", add, description="Add two numbers")
        """
        # Determine description
        tool_description = description
        if tool_description is None:
            tool_description = extract_description_from_docstring(handler)
        if tool_description is None:
            tool_description = f"Tool: {name}"

        # Determine input schema
        schema: dict[str, Any]
        if input_schema is not None:
            # Check if it's a Pydantic model
            if PYDANTIC_AVAILABLE and isinstance(input_schema, type) and issubclass(
                input_schema, BaseModel
            ):
                schema = generate_schema_from_pydantic(input_schema)
            elif isinstance(input_schema, type):
                # It's a type but not Pydantic - try to generate schema
                schema = auto_generate_schema(input_schema)
            else:
                # Assume it's a dict schema
                schema = input_schema
        else:
            # Auto-generate from function signature
            schema = auto_generate_schema(handler)

        # Create tool configuration
        config = ToolConfigModel(
            name=name,
            description=tool_description,
            input_schema=schema,
            handler=handler,
        )

        # Register with server
        self.server.register_tool(config)

        return self

    def tool(
        self,
        name: str | None = None,
        description: str | None = None,
        input_schema: dict[str, Any] | type[BaseModel] | None = None,
    ) -> Callable[[F], F]:
        """Decorator to add a tool to the server.

        Can be used as @mcp.tool() or @mcp.tool(name="custom")

        Args:
            name: Tool name (defaults to function name)
            description: Tool description (defaults to function docstring)
            input_schema: Input schema (auto-generated if not provided)

        Returns:
            Decorator function

        Example:
            >>> @mcp.tool()
            >>> def add(a: int, b: int) -> int:
            ...     '''Add two numbers.'''
            ...     return a + b
            >>>
            >>> @mcp.tool(name="custom_add")
            >>> def add(a: int, b: int) -> int:
            ...     return a + b
        """

        def decorator(func: F) -> F:
            # Determine tool name
            tool_name = name or func.__name__

            # Register the tool
            self.add_tool(tool_name, func, description=description, input_schema=input_schema)

            # Preserve function metadata
            functools.update_wrapper(func, func)

            return func

        return decorator

    # Prompt Management

    def add_prompt(
        self,
        name: str,
        handler: Callable[..., Any],
        description: str | None = None,
        arguments: list[str] | None = None,
    ) -> "BuildMCPServer":
        """Add a prompt to the server.

        Args:
            name: Prompt name
            handler: Prompt handler function
            description: Prompt description (auto-extracted if not provided)
            arguments: List of prompt arguments (auto-detected if not provided)

        Returns:
            Self for method chaining

        Raises:
            ValidationError: If a prompt with the same name already exists

        Example:
            >>> def greet(name: str) -> str:
            ...     return f"Hello, {name}!"
            >>>
            >>> mcp.add_prompt("greet", greet, description="Greeting prompt")
        """
        # Determine description
        prompt_description = description
        if prompt_description is None:
            prompt_description = extract_description_from_docstring(handler)
        if prompt_description is None:
            prompt_description = f"Prompt: {name}"

        # Determine arguments from function signature if not provided
        prompt_arguments = arguments
        if prompt_arguments is None:
            sig = inspect.signature(handler)
            prompt_arguments = [
                param_name
                for param_name, param in sig.parameters.items()
                if param_name not in ('self', 'cls')
                and param.kind
                not in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
            ]

        # Create prompt configuration
        config = PromptConfigModel(
            name=name,
            description=prompt_description,
            handler=handler,
            arguments=prompt_arguments or [],
            template=None,
        )

        # Register with server
        self.server.register_prompt(config)

        return self

    def prompt(
        self,
        name: str | None = None,
        description: str | None = None,
        arguments: list[str] | None = None,
    ) -> Callable[[F], F]:
        """Decorator to add a prompt to the server.

        Can be used as @mcp.prompt() or @mcp.prompt(name="custom")

        Args:
            name: Prompt name (defaults to function name)
            description: Prompt description (defaults to function docstring)
            arguments: List of prompt arguments (auto-detected if not provided)

        Returns:
            Decorator function

        Example:
            >>> @mcp.prompt()
            >>> def code_review(language: str = "python") -> str:
            ...     '''Generate a code review prompt.'''
            ...     return f"Review this {language} code..."
        """

        def decorator(func: F) -> F:
            # Determine prompt name
            prompt_name = name or func.__name__

            # Register the prompt
            self.add_prompt(prompt_name, func, description=description, arguments=arguments)

            # Preserve function metadata
            functools.update_wrapper(func, func)

            return func

        return decorator

    # Resource Management

    def add_resource(
        self,
        uri: str,
        handler: Callable[..., Any],
        name: str | None = None,
        description: str | None = None,
        mime_type: str = "application/json",
    ) -> "BuildMCPServer":
        """Add a resource to the server.

        Args:
            uri: Resource URI
            handler: Resource handler function
            name: Resource name (defaults to handler function name)
            description: Resource description (auto-extracted if not provided)
            mime_type: MIME type (default: "application/json")

        Returns:
            Self for method chaining

        Raises:
            ValidationError: If a resource with the same URI already exists
            ValueError: If URI is empty

        Example:
            >>> def get_config() -> dict:
            ...     return {"version": "1.0.0"}
            >>>
            >>> mcp.add_resource("config://app", get_config, mime_type="application/json")
        """
        if not uri:
            raise ValueError("Resource URI is required")

        # Determine resource name
        resource_name = name or handler.__name__

        # Determine description
        resource_description = description
        if resource_description is None:
            resource_description = extract_description_from_docstring(handler)
        if resource_description is None:
            resource_description = f"Resource: {resource_name}"

        # Create resource configuration
        config = ResourceConfigModel(
            uri=uri,
            name=resource_name,
            description=resource_description,
            mime_type=mime_type,
            handler=handler,
        )

        # Register with server
        self.server.register_resource(config)

        return self

    def resource(
        self,
        uri: str,
        name: str | None = None,
        description: str | None = None,
        mime_type: str = "application/json",
    ) -> Callable[[F], F]:
        """Decorator to add a resource to the server.

        Args:
            uri: Resource URI (required)
            name: Resource name (defaults to function name)
            description: Resource description (defaults to function docstring)
            mime_type: MIME type (default: "application/json")

        Returns:
            Decorator function

        Raises:
            ValueError: If URI is empty

        Example:
            >>> @mcp.resource(uri="config://app")
            >>> def get_config() -> dict:
            ...     '''Get application configuration.'''
            ...     return {"version": "1.0.0"}
        """
        if not uri:
            raise ValueError("Resource URI is required")

        def decorator(func: F) -> F:
            # Determine resource name
            resource_name = name or func.__name__

            # Register the resource
            self.add_resource(uri, func, name=resource_name, description=description, mime_type=mime_type)

            # Preserve function metadata
            functools.update_wrapper(func, func)

            return func

        return decorator

    # Configuration

    def configure(
        self,
        port: int | None = None,
        log_level: str | None = None,
        **kwargs: Any,
    ) -> "BuildMCPServer":
        """Configure the server.

        Args:
            port: Server port (for network transports)
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            **kwargs: Additional configuration options

        Returns:
            Self for method chaining

        Example:
            >>> mcp.configure(port=3000, log_level="DEBUG")
        """
        # Update transport config if port provided
        if port is not None:
            self.config.transport.port = port

        # Update logging config if log_level provided
        if log_level is not None:

            # Validate log level
            valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
            if log_level.upper() not in valid_levels:
                raise ValueError(
                    f"Invalid log level: {log_level}. Must be one of {valid_levels}"
                )
            self.config.logging.level = log_level.upper()  # type: ignore[assignment]

        # Handle additional kwargs (extend as needed)
        for _key, _value in kwargs.items():
            # You can add more configuration options here
            # For now, we'll just ignore unknown options
            pass

        return self

    # Lifecycle

    async def initialize(self) -> "SimplyMCP":
        """Initialize the server.

        Must be called before running the server.

        Returns:
            Self for method chaining

        Example:
            >>> await mcp.initialize()
        """
        await self.server.initialize()
        return self

    async def run(self, transport: str = "stdio") -> None:
        """Run the server with specified transport.

        Args:
            transport: Transport type (stdio, http, sse)

        Raises:
            RuntimeError: If server is not initialized
            ValueError: If transport type is unsupported

        Example:
            >>> await mcp.run()  # stdio
            >>> await mcp.run("stdio")
        """
        if transport == "stdio":
            await self.server.run_stdio()
        else:
            # For now, only stdio is implemented
            # Future: support http, sse
            raise ValueError(f"Unsupported transport: {transport}. Only 'stdio' is currently supported.")

    async def run_stdio(self) -> None:
        """Run the server with stdio transport.

        Convenience method for run("stdio").

        Raises:
            RuntimeError: If server is not initialized

        Example:
            >>> await mcp.run_stdio()
        """
        await self.server.run_stdio()

    # Server Access

    def get_server(self) -> SimplyMCPServer:
        """Get the underlying server instance.

        Returns:
            The underlying SimplyMCPServer instance

        Example:
            >>> server = mcp.get_server()
            >>> print(server.config.server.name)
        """
        return self.server

    # Component Query

    def list_tools(self) -> list[str]:
        """List registered tool names.

        Returns:
            List of tool names

        Example:
            >>> tools = mcp.list_tools()
            >>> print(tools)
            ['add', 'multiply']
        """
        tool_configs = self.server.registry.list_tools()
        return [config.name for config in tool_configs]

    def list_prompts(self) -> list[str]:
        """List registered prompt names.

        Returns:
            List of prompt names

        Example:
            >>> prompts = mcp.list_prompts()
            >>> print(prompts)
            ['greet', 'code_review']
        """
        prompt_configs = self.server.registry.list_prompts()
        return [config.name for config in prompt_configs]

    def list_resources(self) -> list[str]:
        """List registered resource URIs.

        Returns:
            List of resource URIs

        Example:
            >>> resources = mcp.list_resources()
            >>> print(resources)
            ['config://app', 'data://stats']
        """
        resource_configs = self.server.registry.list_resources()
        return [config.uri for config in resource_configs]


__all__ = ["BuildMCPServer"]
