"""Thread-safe component registry for Simply-MCP.

This module provides a centralized registry for managing tools, prompts, and resources
in an MCP server. The registry ensures thread-safe operations, prevents naming conflicts,
and provides efficient O(1) lookups for registered components.

The registry follows the singleton pattern to ensure a single source of truth per server
instance, and integrates with the error handling and logging systems for robust operation.
"""

import threading

from simply_mcp.core.errors import ValidationError
from simply_mcp.core.logger import get_logger
from simply_mcp.core.types import PromptConfigModel, ResourceConfigModel, ToolConfigModel

# Module-level logger
logger = get_logger(__name__)


class ComponentRegistry:
    """Thread-safe registry for tools, prompts, and resources.

    This class provides a centralized registry for managing MCP server components
    with thread-safe operations. It supports registration, lookup, and management
    of tools, prompts, and resources.

    The registry uses a singleton pattern (one per server instance) and provides:
    - Thread-safe concurrent access using threading.Lock
    - O(1) lookups using dictionaries
    - Duplicate detection and conflict prevention
    - Case-insensitive lookups for tools and prompts
    - URI-based lookups for resources
    - Comprehensive logging of all operations

    Attributes:
        _tools: Dictionary mapping tool names to ToolConfigModel
        _prompts: Dictionary mapping prompt names to PromptConfigModel
        _resources: Dictionary mapping resource URIs to ResourceConfigModel
        _lock: Threading lock for thread-safe operations

    Example:
        >>> registry = ComponentRegistry()
        >>> tool_config = ToolConfigModel(
        ...     name="add",
        ...     description="Add two numbers",
        ...     input_schema={"type": "object"},
        ...     handler=lambda a, b: a + b
        ... )
        >>> registry.register_tool(tool_config)
        >>> tool = registry.get_tool("add")
        >>> print(tool.name)
        add
    """

    def __init__(self) -> None:
        """Initialize the component registry.

        Creates empty storage for tools, prompts, and resources, and initializes
        the threading lock for concurrent access control.
        """
        self._tools: dict[str, ToolConfigModel] = {}
        self._prompts: dict[str, PromptConfigModel] = {}
        self._resources: dict[str, ResourceConfigModel] = {}
        self._lock = threading.Lock()

        logger.debug("Initialized ComponentRegistry")

    def register_tool(self, config: ToolConfigModel) -> None:
        """Register a tool with the registry.

        Registers a tool configuration and validates for naming conflicts.
        Tool names are stored in lowercase for case-insensitive lookups.

        Args:
            config: Tool configuration containing name, description, schema, and handler

        Raises:
            ValidationError: If a tool with the same name already exists

        Example:
            >>> tool_config = ToolConfigModel(
            ...     name="calculate",
            ...     description="Perform calculations",
            ...     input_schema={"type": "object"},
            ...     handler=calculate_handler
            ... )
            >>> registry.register_tool(tool_config)
        """
        tool_name = config.name
        tool_name_lower = tool_name.lower()

        with self._lock:
            if tool_name_lower in self._tools:
                logger.error(
                    f"Attempted to register duplicate tool: {tool_name}",
                    extra={"context": {"tool_name": tool_name}},
                )
                raise ValidationError(
                    f"Tool '{tool_name}' is already registered",
                    code="DUPLICATE_TOOL",
                    context={"tool_name": tool_name},
                )

            self._tools[tool_name_lower] = config
            logger.info(
                f"Registered tool: {tool_name}",
                extra={"context": {"tool_name": tool_name}},
            )

    def register_prompt(self, config: PromptConfigModel) -> None:
        """Register a prompt with the registry.

        Registers a prompt configuration and validates for naming conflicts.
        Prompt names are stored in lowercase for case-insensitive lookups.

        Args:
            config: Prompt configuration containing name, description, and template/handler

        Raises:
            ValidationError: If a prompt with the same name already exists

        Example:
            >>> prompt_config = PromptConfigModel(
            ...     name="greeting",
            ...     description="Generate a greeting",
            ...     template="Hello, {name}!"
            ... )
            >>> registry.register_prompt(prompt_config)
        """
        prompt_name = config.name
        prompt_name_lower = prompt_name.lower()

        with self._lock:
            if prompt_name_lower in self._prompts:
                logger.error(
                    f"Attempted to register duplicate prompt: {prompt_name}",
                    extra={"context": {"prompt_name": prompt_name}},
                )
                raise ValidationError(
                    f"Prompt '{prompt_name}' is already registered",
                    code="DUPLICATE_PROMPT",
                    context={"prompt_name": prompt_name},
                )

            self._prompts[prompt_name_lower] = config
            logger.info(
                f"Registered prompt: {prompt_name}",
                extra={"context": {"prompt_name": prompt_name}},
            )

    def register_resource(self, config: ResourceConfigModel) -> None:
        """Register a resource with the registry.

        Registers a resource configuration and validates for URI conflicts.
        Resources are identified by their unique URI.

        Args:
            config: Resource configuration containing uri, name, description, and handler

        Raises:
            ValidationError: If a resource with the same URI already exists

        Example:
            >>> resource_config = ResourceConfigModel(
            ...     uri="file:///data/config.json",
            ...     name="config",
            ...     description="Configuration file",
            ...     mime_type="application/json",
            ...     handler=load_config
            ... )
            >>> registry.register_resource(resource_config)
        """
        resource_uri = config.uri

        with self._lock:
            if resource_uri in self._resources:
                logger.error(
                    f"Attempted to register duplicate resource: {resource_uri}",
                    extra={"context": {"resource_uri": resource_uri}},
                )
                raise ValidationError(
                    f"Resource with URI '{resource_uri}' is already registered",
                    code="DUPLICATE_RESOURCE",
                    context={"resource_uri": resource_uri},
                )

            self._resources[resource_uri] = config
            logger.info(
                f"Registered resource: {resource_uri}",
                extra={
                    "context": {
                        "resource_uri": resource_uri,
                        "resource_name": config.name,
                    }
                },
            )

    def get_tool(self, name: str) -> ToolConfigModel | None:
        """Get a tool by name.

        Performs case-insensitive lookup of a tool by name.

        Args:
            name: Tool name to lookup

        Returns:
            Tool configuration if found, None otherwise

        Example:
            >>> tool = registry.get_tool("calculate")
            >>> if tool:
            ...     print(tool.description)
            Perform calculations
        """
        name_lower = name.lower()

        with self._lock:
            tool = self._tools.get(name_lower)
            if tool:
                logger.debug(f"Retrieved tool: {name}")
            else:
                logger.debug(f"Tool not found: {name}")
            return tool

    def get_prompt(self, name: str) -> PromptConfigModel | None:
        """Get a prompt by name.

        Performs case-insensitive lookup of a prompt by name.

        Args:
            name: Prompt name to lookup

        Returns:
            Prompt configuration if found, None otherwise

        Example:
            >>> prompt = registry.get_prompt("greeting")
            >>> if prompt:
            ...     print(prompt.description)
            Generate a greeting
        """
        name_lower = name.lower()

        with self._lock:
            prompt = self._prompts.get(name_lower)
            if prompt:
                logger.debug(f"Retrieved prompt: {name}")
            else:
                logger.debug(f"Prompt not found: {name}")
            return prompt

    def get_resource(self, uri: str) -> ResourceConfigModel | None:
        """Get a resource by URI.

        Performs exact URI lookup of a resource.

        Args:
            uri: Resource URI to lookup

        Returns:
            Resource configuration if found, None otherwise

        Example:
            >>> resource = registry.get_resource("file:///data/config.json")
            >>> if resource:
            ...     print(resource.mime_type)
            application/json
        """
        with self._lock:
            resource = self._resources.get(uri)
            if resource:
                logger.debug(f"Retrieved resource: {uri}")
            else:
                logger.debug(f"Resource not found: {uri}")
            return resource

    def list_tools(self) -> list[ToolConfigModel]:
        """List all registered tools.

        Returns:
            List of all registered tool configurations

        Example:
            >>> tools = registry.list_tools()
            >>> for tool in tools:
            ...     print(tool.name)
            calculate
            add
        """
        with self._lock:
            tools = list(self._tools.values())
            logger.debug(f"Listed {len(tools)} tools")
            return tools

    def list_prompts(self) -> list[PromptConfigModel]:
        """List all registered prompts.

        Returns:
            List of all registered prompt configurations

        Example:
            >>> prompts = registry.list_prompts()
            >>> for prompt in prompts:
            ...     print(prompt.name)
            greeting
            farewell
        """
        with self._lock:
            prompts = list(self._prompts.values())
            logger.debug(f"Listed {len(prompts)} prompts")
            return prompts

    def list_resources(self) -> list[ResourceConfigModel]:
        """List all registered resources.

        Returns:
            List of all registered resource configurations

        Example:
            >>> resources = registry.list_resources()
            >>> for resource in resources:
            ...     print(resource.uri)
            file:///data/config.json
            file:///data/schema.json
        """
        with self._lock:
            resources = list(self._resources.values())
            logger.debug(f"Listed {len(resources)} resources")
            return resources

    def has_tool(self, name: str) -> bool:
        """Check if a tool is registered.

        Performs case-insensitive check for tool existence.

        Args:
            name: Tool name to check

        Returns:
            True if tool is registered, False otherwise

        Example:
            >>> if registry.has_tool("calculate"):
            ...     print("Tool is registered")
            Tool is registered
        """
        name_lower = name.lower()

        with self._lock:
            return name_lower in self._tools

    def has_prompt(self, name: str) -> bool:
        """Check if a prompt is registered.

        Performs case-insensitive check for prompt existence.

        Args:
            name: Prompt name to check

        Returns:
            True if prompt is registered, False otherwise

        Example:
            >>> if registry.has_prompt("greeting"):
            ...     print("Prompt is registered")
            Prompt is registered
        """
        name_lower = name.lower()

        with self._lock:
            return name_lower in self._prompts

    def has_resource(self, uri: str) -> bool:
        """Check if a resource is registered.

        Performs exact URI check for resource existence.

        Args:
            uri: Resource URI to check

        Returns:
            True if resource is registered, False otherwise

        Example:
            >>> if registry.has_resource("file:///data/config.json"):
            ...     print("Resource is registered")
            Resource is registered
        """
        with self._lock:
            return uri in self._resources

    def unregister_tool(self, name: str) -> bool:
        """Unregister a tool from the registry.

        Removes a tool from the registry by name (case-insensitive).

        Args:
            name: Tool name to unregister

        Returns:
            True if tool was unregistered, False if not found

        Example:
            >>> if registry.unregister_tool("calculate"):
            ...     print("Tool unregistered")
            Tool unregistered
        """
        name_lower = name.lower()

        with self._lock:
            if name_lower in self._tools:
                del self._tools[name_lower]
                logger.info(
                    f"Unregistered tool: {name}",
                    extra={"context": {"tool_name": name}},
                )
                return True
            else:
                logger.debug(f"Tool not found for unregister: {name}")
                return False

    def unregister_prompt(self, name: str) -> bool:
        """Unregister a prompt from the registry.

        Removes a prompt from the registry by name (case-insensitive).

        Args:
            name: Prompt name to unregister

        Returns:
            True if prompt was unregistered, False if not found

        Example:
            >>> if registry.unregister_prompt("greeting"):
            ...     print("Prompt unregistered")
            Prompt unregistered
        """
        name_lower = name.lower()

        with self._lock:
            if name_lower in self._prompts:
                del self._prompts[name_lower]
                logger.info(
                    f"Unregistered prompt: {name}",
                    extra={"context": {"prompt_name": name}},
                )
                return True
            else:
                logger.debug(f"Prompt not found for unregister: {name}")
                return False

    def unregister_resource(self, uri: str) -> bool:
        """Unregister a resource from the registry.

        Removes a resource from the registry by URI.

        Args:
            uri: Resource URI to unregister

        Returns:
            True if resource was unregistered, False if not found

        Example:
            >>> if registry.unregister_resource("file:///data/config.json"):
            ...     print("Resource unregistered")
            Resource unregistered
        """
        with self._lock:
            if uri in self._resources:
                resource_name = self._resources[uri].name
                del self._resources[uri]
                logger.info(
                    f"Unregistered resource: {uri}",
                    extra={
                        "context": {
                            "resource_uri": uri,
                            "resource_name": resource_name,
                        }
                    },
                )
                return True
            else:
                logger.debug(f"Resource not found for unregister: {uri}")
                return False

    def clear(self) -> None:
        """Clear all registered components.

        Removes all tools, prompts, and resources from the registry.
        Useful for testing or server reset operations.

        Example:
            >>> registry.clear()
            >>> stats = registry.get_stats()
            >>> print(stats)
            {'tools': 0, 'prompts': 0, 'resources': 0, 'total': 0}
        """
        with self._lock:
            tool_count = len(self._tools)
            prompt_count = len(self._prompts)
            resource_count = len(self._resources)

            self._tools.clear()
            self._prompts.clear()
            self._resources.clear()

            logger.info(
                "Cleared registry",
                extra={
                    "context": {
                        "tools_cleared": tool_count,
                        "prompts_cleared": prompt_count,
                        "resources_cleared": resource_count,
                    }
                },
            )

    def get_stats(self) -> dict[str, int]:
        """Get statistics about registered components.

        Returns:
            Dictionary with counts of tools, prompts, resources, and total

        Example:
            >>> stats = registry.get_stats()
            >>> print(f"Total components: {stats['total']}")
            Total components: 5
        """
        with self._lock:
            stats = {
                "tools": len(self._tools),
                "prompts": len(self._prompts),
                "resources": len(self._resources),
                "total": len(self._tools) + len(self._prompts) + len(self._resources),
            }
            logger.debug(f"Registry stats: {stats}")
            return stats


__all__ = ["ComponentRegistry"]
