"""Functional API for Simply-MCP server construction.

This module provides a declarative, configuration-based API for building MCP servers,
inspired by the TypeScript implementation's functional API style.

The functional API supports:
- Type-safe helper functions (define_mcp, define_tool, etc.)
- Builder pattern for programmatic construction (MCPBuilder)
- Config-based server definitions
- Factory function for creating builders (create_mcp)

Example (Config-based):
    >>> from simply_mcp import define_mcp, define_tool
    >>>
    >>> server_config = define_mcp({
    ...     "name": "my-server",
    ...     "version": "1.0.0",
    ...     "tools": [
    ...         define_tool({
    ...             "name": "greet",
    ...             "description": "Greet a user",
    ...             "handler": lambda name: f"Hello, {name}!"
    ...         })
    ...     ]
    ... })

Example (Builder pattern):
    >>> from simply_mcp import create_mcp
    >>>
    >>> mcp = create_mcp(name="my-server", version="1.0.0")
    >>> mcp.tool({
    ...     "name": "greet",
    ...     "description": "Greet a user",
    ...     "handler": lambda name: f"Hello, {name}!"
    ... })
    >>> config = mcp.build()
"""

from collections.abc import Callable
from typing import Any, TypedDict, TypeVar

from simply_mcp.core.types import ToolConfigModel, PromptConfigModel, ResourceConfigModel


# Type definitions for config-based API

class ToolConfig(TypedDict, total=False):
    """Configuration for a tool in the functional API."""
    name: str
    description: str
    handler: Callable[..., Any]
    input_schema: dict[str, Any] | None


class PromptConfig(TypedDict, total=False):
    """Configuration for a prompt in the functional API."""
    name: str
    description: str
    handler: Callable[..., Any]
    arguments: list[str] | None
    template: str | None


class ResourceConfig(TypedDict, total=False):
    """Configuration for a resource in the functional API."""
    uri: str
    name: str
    description: str
    handler: Callable[..., Any]
    mime_type: str


class MCPConfig(TypedDict, total=False):
    """Complete configuration for an MCP server in the functional API."""
    name: str
    version: str
    description: str | None
    tools: list[ToolConfig] | None
    prompts: list[PromptConfig] | None
    resources: list[ResourceConfig] | None


# Type variables
T = TypeVar('T', bound=dict[str, Any])


# Helper functions for type-safe config definitions

def define_mcp(config: MCPConfig) -> MCPConfig:
    """Define an MCP server configuration with type safety.

    This is a type-safe helper function that returns the config as-is,
    providing IDE autocompletion and type checking for server configurations.

    Args:
        config: Server configuration dictionary

    Returns:
        The same configuration (provides type safety only)

    Example:
        >>> config = define_mcp({
        ...     "name": "my-server",
        ...     "version": "1.0.0",
        ...     "tools": [...]
        ... })
    """
    return config


def define_tool(tool: ToolConfig) -> ToolConfig:
    """Define a tool configuration with type safety.

    This is a type-safe helper function that returns the tool config as-is,
    providing IDE autocompletion and type checking.

    Args:
        tool: Tool configuration dictionary

    Returns:
        The same configuration (provides type safety only)

    Example:
        >>> tool = define_tool({
        ...     "name": "greet",
        ...     "description": "Greet a user",
        ...     "handler": lambda name: f"Hello, {name}!"
        ... })
    """
    return tool


def define_prompt(prompt: PromptConfig) -> PromptConfig:
    """Define a prompt configuration with type safety.

    This is a type-safe helper function that returns the prompt config as-is,
    providing IDE autocompletion and type checking.

    Args:
        prompt: Prompt configuration dictionary

    Returns:
        The same configuration (provides type safety only)

    Example:
        >>> prompt = define_prompt({
        ...     "name": "code_review",
        ...     "description": "Generate a code review template",
        ...     "handler": lambda lang: f"Review this {lang} code..."
        ... })
    """
    return prompt


def define_resource(resource: ResourceConfig) -> ResourceConfig:
    """Define a resource configuration with type safety.

    This is a type-safe helper function that returns the resource config as-is,
    providing IDE autocompletion and type checking.

    Args:
        resource: Resource configuration dictionary

    Returns:
        The same configuration (provides type safety only)

    Example:
        >>> resource = define_resource({
        ...     "uri": "config://app",
        ...     "name": "config",
        ...     "description": "Application configuration",
        ...     "handler": lambda: {"version": "1.0.0"},
        ...     "mime_type": "application/json"
        ... })
    """
    return resource


# Builder class

class MCPBuilder:
    """Builder class for constructing MCP server configurations.

    Provides a fluent interface for building MCP servers programmatically
    using method chaining. This mirrors the TypeScript MCPBuilder class.

    Attributes:
        config: The server configuration being built

    Example:
        >>> builder = MCPBuilder(name="my-server", version="1.0.0")
        >>> builder.tool({
        ...     "name": "greet",
        ...     "description": "Greet a user",
        ...     "handler": lambda name: f"Hello, {name}!"
        ... })
        >>> builder.prompt({
        ...     "name": "review",
        ...     "description": "Code review prompt",
        ...     "handler": lambda: "Review this code..."
        ... })
        >>> config = builder.build()
    """

    def __init__(
        self,
        name: str = "mcp-server",
        version: str = "0.1.0",
        description: str | None = None,
    ) -> None:
        """Initialize a new MCP builder.

        Args:
            name: Server name
            version: Server version
            description: Server description (optional)
        """
        self.config: MCPConfig = {
            "name": name,
            "version": version,
            "description": description,
            "tools": [],
            "prompts": [],
            "resources": [],
        }

    def tool(self, tool: ToolConfig) -> "MCPBuilder":
        """Add a tool to the server configuration.

        Args:
            tool: Tool configuration

        Returns:
            Self for method chaining

        Example:
            >>> builder.tool({
            ...     "name": "add",
            ...     "description": "Add two numbers",
            ...     "handler": lambda a, b: a + b
            ... })
        """
        if self.config["tools"] is None:
            self.config["tools"] = []
        self.config["tools"].append(tool)
        return self

    def prompt(self, prompt: PromptConfig) -> "MCPBuilder":
        """Add a prompt to the server configuration.

        Args:
            prompt: Prompt configuration

        Returns:
            Self for method chaining

        Example:
            >>> builder.prompt({
            ...     "name": "greet",
            ...     "description": "Greeting prompt",
            ...     "handler": lambda name: f"Hello, {name}!"
            ... })
        """
        if self.config["prompts"] is None:
            self.config["prompts"] = []
        self.config["prompts"].append(prompt)
        return self

    def resource(self, resource: ResourceConfig) -> "MCPBuilder":
        """Add a resource to the server configuration.

        Args:
            resource: Resource configuration

        Returns:
            Self for method chaining

        Example:
            >>> builder.resource({
            ...     "uri": "config://app",
            ...     "name": "config",
            ...     "description": "App config",
            ...     "handler": lambda: {"version": "1.0.0"},
            ...     "mime_type": "application/json"
            ... })
        """
        if self.config["resources"] is None:
            self.config["resources"] = []
        self.config["resources"].append(resource)
        return self

    def build(self) -> MCPConfig:
        """Build and return the final configuration.

        Returns:
            The complete MCP server configuration

        Example:
            >>> config = builder.build()
        """
        return self.config


def create_mcp(
    name: str = "mcp-server",
    version: str = "0.1.0",
    description: str | None = None,
) -> MCPBuilder:
    """Create a new MCP builder instance.

    Factory function for creating MCPBuilder instances with a fluent interface.
    This mirrors the TypeScript createMCP function.

    Args:
        name: Server name
        version: Server version
        description: Server description (optional)

    Returns:
        A new MCPBuilder instance

    Example:
        >>> mcp = create_mcp(name="my-server", version="1.0.0")
        >>> mcp.tool({...}).prompt({...}).build()
    """
    return MCPBuilder(name=name, version=version, description=description)


__all__ = [
    # Type definitions
    "ToolConfig",
    "PromptConfig",
    "ResourceConfig",
    "MCPConfig",
    # Helper functions
    "define_mcp",
    "define_tool",
    "define_prompt",
    "define_resource",
    # Builder
    "MCPBuilder",
    "create_mcp",
]
