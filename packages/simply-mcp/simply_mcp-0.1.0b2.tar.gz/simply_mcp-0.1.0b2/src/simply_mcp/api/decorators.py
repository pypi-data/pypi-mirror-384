"""Decorator-based API for Simply-MCP server development.

This module provides a beautiful, Pythonic decorator API that makes MCP server
development incredibly easy. Users can create MCP servers with simple decorators
on their functions and classes.

The decorators support:
- Automatic schema generation from type hints
- Pydantic model integration
- Function and method decorators
- Class-based server definitions
- Global server management

Example:
    >>> from simply_mcp.api.decorators import tool, prompt, resource, mcp_server
    >>>
    >>> @tool()
    >>> def add(a: int, b: int) -> int:
    ...     '''Add two numbers.'''
    ...     return a + b
    >>>
    >>> @prompt()
    >>> def greet(name: str) -> str:
    ...     '''Generate a greeting.'''
    ...     return f"Hello, {name}!"
    >>>
    >>> @resource(uri="config://app")
    >>> def get_config() -> dict:
    ...     '''Get application config.'''
    ...     return {"version": "1.0.0"}
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

from simply_mcp.core.config import SimplyMCPConfig, get_default_config
from simply_mcp.core.server import SimplyMCPServer
from simply_mcp.core.types import PromptConfigModel, ResourceConfigModel, ToolConfigModel
from simply_mcp.validation.schema import (
    auto_generate_schema,
    extract_description_from_docstring,
    generate_schema_from_pydantic,
)

# Type variables for generic decorators
F = TypeVar('F', bound=Callable[..., Any])
T = TypeVar('T')

# Module-level global server instance
_global_server: SimplyMCPServer | None = None


def get_global_server() -> SimplyMCPServer:
    """Get or create the global server instance.

    This returns a singleton server instance that is used by all module-level
    decorators (@tool, @prompt, @resource) for automatic registration.

    Returns:
        The global SimplyMCPServer instance

    Example:
        >>> server = get_global_server()
        >>> print(server.config.server.name)
        simply-mcp-server
    """
    global _global_server
    if _global_server is None:
        _global_server = SimplyMCPServer(get_default_config())
    return _global_server


def set_global_server(server: SimplyMCPServer) -> None:
    """Set a custom global server instance.

    This allows using a custom configured server instead of the default one.

    Args:
        server: Custom server instance to use globally

    Example:
        >>> from simply_mcp import SimplyMCPServer, SimplyMCPConfig
        >>> config = SimplyMCPConfig(...)
        >>> server = SimplyMCPServer(config)
        >>> set_global_server(server)
    """
    global _global_server
    _global_server = server


def reset_global_server() -> None:
    """Reset the global server instance.

    This clears the global server singleton, which is useful for testing
    or when you want to reinitialize the server with a fresh state.

    Example:
        >>> from simply_mcp.api.decorators import reset_global_server
        >>> reset_global_server()  # Clear global state
        >>> # Now next call to get_global_server() will create a new instance
    """
    global _global_server
    _global_server = None


def tool(
    name: str | None = None,
    description: str | None = None,
    input_schema: dict[str, Any] | type[BaseModel] | None = None,
) -> Callable[[F], F]:
    """Decorator to register a function as an MCP tool.

    This decorator can be used with or without arguments. It automatically generates
    a JSON schema from the function signature or uses a provided schema/Pydantic model.

    The decorated function is automatically registered with the global server instance.

    Args:
        name: Tool name (defaults to function name)
        description: Tool description (defaults to function docstring)
        input_schema: Input schema - can be:
            - None: Auto-generate from function signature (default)
            - Pydantic BaseModel class: Generate from Pydantic model
            - Dict: Use explicit JSON Schema

    Returns:
        Decorated function with _mcp_tool_config and _mcp_component_type attributes

    Raises:
        ValueError: If input_schema is a Pydantic model but pydantic is not installed
        ValueError: If schema generation fails

    Examples:
        Auto-generate schema from function:
        >>> @tool()
        >>> def add(a: int, b: int) -> int:
        ...     '''Add two numbers.'''
        ...     return a + b

        Override name and description:
        >>> @tool(name="custom_add", description="Custom addition tool")
        >>> def add(a: int, b: int) -> int:
        ...     return a + b

        Use Pydantic model:
        >>> from pydantic import BaseModel, Field
        >>> class SearchInput(BaseModel):
        ...     query: str = Field(description="Search query")
        ...     limit: int = Field(default=10, ge=1, le=100)
        >>>
        >>> @tool(input_schema=SearchInput)
        >>> def search(input: SearchInput) -> list:
        ...     '''Search with validation.'''
        ...     return [f"Result for {input.query}"]

        Use explicit schema:
        >>> @tool(input_schema={
        ...     "type": "object",
        ...     "properties": {"x": {"type": "integer"}},
        ...     "required": ["x"]
        ... })
        >>> def process(x: int) -> int:
        ...     return x * 2
    """
    def decorator(func: F) -> F:
        # Determine tool name
        tool_name = name or func.__name__

        # Determine description
        tool_description = description
        if tool_description is None:
            tool_description = extract_description_from_docstring(func)
        if tool_description is None:
            tool_description = f"Tool: {tool_name}"

        # Determine input schema
        schema: dict[str, Any]
        if input_schema is not None:
            # Check if it's a Pydantic model
            if PYDANTIC_AVAILABLE and isinstance(input_schema, type) and issubclass(input_schema, BaseModel):
                schema = generate_schema_from_pydantic(input_schema)
            elif isinstance(input_schema, type):
                # It's a type but not Pydantic - try to generate schema
                schema = auto_generate_schema(input_schema)
            else:
                # Assume it's a dict schema - input_schema is already Dict[str, Any]
                schema = input_schema
        else:
            # Auto-generate from function signature
            schema = auto_generate_schema(func)

        # Create tool configuration
        config = ToolConfigModel(
            name=tool_name,
            description=tool_description,
            input_schema=schema,
            handler=func,
        )

        # Store metadata on function - these are dynamic attributes added at runtime
        func._mcp_tool_config = config  # type: ignore[attr-defined]
        func._mcp_component_type = 'tool'  # type: ignore[attr-defined]

        # Auto-register with global server
        server = get_global_server()
        server.register_tool(config)

        # Preserve function metadata
        functools.update_wrapper(func, func)

        return func

    return decorator


def prompt(
    name: str | None = None,
    description: str | None = None,
    arguments: list[str] | None = None,
) -> Callable[[F], F]:
    """Decorator to register a function as an MCP prompt.

    This decorator automatically detects prompt arguments from the function signature
    and registers the function as a prompt generator with the global server.

    Args:
        name: Prompt name (defaults to function name)
        description: Prompt description (defaults to function docstring)
        arguments: List of argument names (auto-detected from function signature if not provided)

    Returns:
        Decorated function with _mcp_prompt_config and _mcp_component_type attributes

    Examples:
        Basic prompt with auto-detection:
        >>> @prompt()
        >>> def code_review(language: str = "python") -> str:
        ...     '''Generate a code review prompt.'''
        ...     return f"Review this {language} code..."

        Override name and description:
        >>> @prompt(name="custom_review", description="Custom code review prompt")
        >>> def code_review(language: str = "python") -> str:
        ...     return f"Review this {language} code..."

        Explicit arguments:
        >>> @prompt(arguments=["topic", "style"])
        >>> def generate_prompt(topic: str, style: str = "formal") -> str:
        ...     '''Generate a writing prompt.'''
        ...     return f"Write about {topic} in a {style} style"
    """
    def decorator(func: F) -> F:
        # Determine prompt name
        prompt_name = name or func.__name__

        # Determine description
        prompt_description = description
        if prompt_description is None:
            prompt_description = extract_description_from_docstring(func)
        if prompt_description is None:
            prompt_description = f"Prompt: {prompt_name}"

        # Determine arguments from function signature if not provided
        prompt_arguments = arguments
        if prompt_arguments is None:
            sig = inspect.signature(func)
            prompt_arguments = [
                param_name
                for param_name, param in sig.parameters.items()
                if param_name not in ('self', 'cls')
                and param.kind not in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
            ]

        # Create prompt configuration
        config = PromptConfigModel(
            name=prompt_name,
            description=prompt_description,
            handler=func,
            arguments=prompt_arguments or [],
            template=None,
        )

        # Store metadata on function - these are dynamic attributes added at runtime
        func._mcp_prompt_config = config  # type: ignore[attr-defined]
        func._mcp_component_type = 'prompt'  # type: ignore[attr-defined]

        # Auto-register with global server
        server = get_global_server()
        server.register_prompt(config)

        # Preserve function metadata
        functools.update_wrapper(func, func)

        return func

    return decorator


def resource(
    uri: str,
    name: str | None = None,
    description: str | None = None,
    mime_type: str = "application/json",
) -> Callable[[F], F]:
    """Decorator to register a function as an MCP resource.

    This decorator registers a function that provides resource content. The function
    should return the resource data (string, dict, bytes, etc.).

    Args:
        uri: Resource URI (required) - e.g., "config://app", "file:///path/to/file"
        name: Resource name (defaults to function name)
        description: Resource description (defaults to function docstring)
        mime_type: MIME type of resource content (default: "application/json")

    Returns:
        Decorated function with _mcp_resource_config and _mcp_component_type attributes

    Raises:
        ValueError: If uri is not provided

    Examples:
        Basic resource:
        >>> @resource(uri="config://app")
        >>> def get_config() -> dict:
        ...     '''Get application configuration.'''
        ...     return {"version": "1.0.0", "debug": False}

        Custom name and MIME type:
        >>> @resource(uri="data://stats", name="statistics", mime_type="text/plain")
        >>> def get_stats() -> str:
        ...     '''Get system statistics.'''
        ...     return "CPU: 50%, Memory: 70%"

        File resource:
        >>> @resource(uri="file:///app/schema.json", mime_type="application/json")
        >>> def get_schema() -> dict:
        ...     '''Get API schema.'''
        ...     return {"type": "object", "properties": {}}
    """
    if not uri:
        raise ValueError("Resource URI is required")

    def decorator(func: F) -> F:
        # Determine resource name
        resource_name = name or func.__name__

        # Determine description
        resource_description = description
        if resource_description is None:
            resource_description = extract_description_from_docstring(func)
        if resource_description is None:
            resource_description = f"Resource: {resource_name}"

        # Create resource configuration
        config = ResourceConfigModel(
            uri=uri,
            name=resource_name,
            description=resource_description,
            mime_type=mime_type,
            handler=func,
        )

        # Store metadata on function - these are dynamic attributes added at runtime
        func._mcp_resource_config = config  # type: ignore[attr-defined]
        func._mcp_component_type = 'resource'  # type: ignore[attr-defined]

        # Auto-register with global server
        server = get_global_server()
        server.register_resource(config)

        # Preserve function metadata
        functools.update_wrapper(func, func)

        return func

    return decorator


def mcp_server(
    name: str | None = None,
    version: str = "1.0.0",
    description: str | None = None,
    config: SimplyMCPConfig | None = None,
) -> Callable[[type[T]], type[T]]:
    """Class decorator to create an MCP server from a class.

    This decorator scans a class for methods decorated with @tool, @prompt, or @resource
    and automatically creates a server with all those components registered. The decorated
    class gets a `get_server()` class method that returns the configured server instance.

    Args:
        name: Server name (defaults to class name)
        version: Server version (default: "1.0.0")
        description: Server description (defaults to class docstring)
        config: Optional custom server configuration

    Returns:
        Decorated class with get_server() class method

    Examples:
        Basic class-based server:
        >>> @mcp_server(name="calculator", version="1.0.0")
        >>> class Calculator:
        ...     @tool()
        ...     def add(self, a: int, b: int) -> int:
        ...         '''Add two numbers.'''
        ...         return a + b
        ...
        ...     @tool()
        ...     def multiply(self, a: int, b: int) -> int:
        ...         '''Multiply two numbers.'''
        ...         return a * b
        >>>
        >>> server = Calculator.get_server()
        >>> await server.initialize()

        With prompts and resources:
        >>> @mcp_server(name="assistant", version="1.0.0")
        >>> class Assistant:
        ...     @tool()
        ...     def search(self, query: str) -> list:
        ...         return ["result1", "result2"]
        ...
        ...     @prompt()
        ...     def help_prompt(self) -> str:
        ...         return "How can I help you?"
        ...
        ...     @resource(uri="config://assistant")
        ...     def get_config(self) -> dict:
        ...         return {"mode": "helpful"}
    """
    def decorator(cls: type[T]) -> type[T]:
        # Determine server name
        server_name = name or cls.__name__

        # Determine description
        server_description = description
        if server_description is None and cls.__doc__:
            server_description = inspect.cleandoc(cls.__doc__).split('\n')[0]

        # Create server configuration
        if config is not None:
            server_config = config
        else:
            from simply_mcp.core.config import ServerMetadataModel, SimplyMCPConfig

            server_config = SimplyMCPConfig(
                server=ServerMetadataModel(
                    name=server_name,
                    version=version,
                    description=server_description,
                )
            )

        # Create server instance
        server = SimplyMCPServer(server_config)

        # Create an instance of the class for method binding
        instance = cls()

        # Scan class for decorated methods
        for attr_name in dir(cls):
            # Skip private attributes
            if attr_name.startswith('_'):
                continue

            attr = getattr(cls, attr_name)

            # Check if it's a callable method
            if not callable(attr):
                continue

            # Check for decorator metadata
            component_type = getattr(attr, '_mcp_component_type', None)

            if component_type == 'tool':
                # Get original config and create bound handler
                tool_config = attr._mcp_tool_config
                bound_method = getattr(instance, attr_name)

                # Create new config with bound method
                bound_config = ToolConfigModel(
                    name=tool_config.name,
                    description=tool_config.description,
                    input_schema=tool_config.input_schema,
                    handler=bound_method,
                )
                server.register_tool(bound_config)

            elif component_type == 'prompt':
                # Get original config and create bound handler
                prompt_config = attr._mcp_prompt_config
                bound_method = getattr(instance, attr_name)

                # Create new config with bound method
                bound_config_prompt = PromptConfigModel(
                    name=prompt_config.name,
                    description=prompt_config.description,
                    handler=bound_method,
                    arguments=prompt_config.arguments,
                    template=prompt_config.template,
                )

                server.register_prompt(bound_config_prompt)

            elif component_type == 'resource':
                # Get original config and create bound handler
                resource_config = attr._mcp_resource_config
                bound_method = getattr(instance, attr_name)

                # Create new config with bound method
                bound_config_resource = ResourceConfigModel(
                    uri=resource_config.uri,
                    name=resource_config.name,
                    description=resource_config.description,
                    mime_type=resource_config.mime_type,
                    handler=bound_method,
                )
                server.register_resource(bound_config_resource)

        # Add get_server class method - use regular function and make it classmethod via setattr
        def get_server_impl(cls_inner: type[T]) -> SimplyMCPServer:
            """Get the configured server instance.

            Returns:
                Configured SimplyMCPServer with all decorated methods registered
            """
            return server

        # Create classmethod and attach to class - dynamic attributes added at runtime
        cls.get_server = classmethod(get_server_impl)  # type: ignore[attr-defined]

        # Store server reference on class - dynamic attribute added at runtime
        cls._mcp_server = server  # type: ignore[attr-defined]

        return cls

    return decorator


__all__ = [
    "tool",
    "prompt",
    "resource",
    "mcp_server",
    "get_global_server",
    "set_global_server",
    "reset_global_server",
]
