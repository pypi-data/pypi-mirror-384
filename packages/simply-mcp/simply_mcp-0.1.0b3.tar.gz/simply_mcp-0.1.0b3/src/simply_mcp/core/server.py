"""Core MCP server implementation for Simply-MCP.

This module provides the SimplyMCPServer class, which serves as the central
integration point for the Simply-MCP framework. It wraps the Anthropic MCP SDK
server and integrates with all foundation layers (config, registry, logging, errors).

The server provides:
- Full integration with MCP SDK (Server, stdio_server)
- Component registration (tools, prompts, resources)
- Handler execution with error handling
- Request context tracking
- Lifecycle management (initialize, start, stop, shutdown)
- Performance timing and structured logging
"""

import asyncio
import inspect
import time
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import mcp.types as types
from anyio.streams.memory import MemoryObjectReceiveStream, MemoryObjectSendStream
from mcp.server.lowlevel.server import NotificationOptions
from mcp.server.lowlevel.server import Server as MCPServer
from mcp.server.stdio import stdio_server
from mcp.shared.message import SessionMessage
from pydantic import AnyUrl

from simply_mcp.core.config import SimplyMCPConfig, get_default_config
from simply_mcp.core.errors import (
    HandlerExecutionError,
    HandlerNotFoundError,
    ValidationError,
)
from simply_mcp.core.logger import LoggerContext, get_logger
from simply_mcp.core.registry import ComponentRegistry
from simply_mcp.core.types import (
    HandlerFunction,
    PromptConfigModel,
    ResourceConfigModel,
    ToolConfigModel,
)

# Module-level logger
logger = get_logger(__name__)


class SimplyMCPServer:
    """Core MCP server that integrates with Anthropic's MCP Python SDK.

    This class provides the main server implementation for Simply-MCP, wrapping
    the MCP SDK server and integrating with all foundation layers. It manages
    component registration, handler execution, and the complete server lifecycle.

    The server follows this lifecycle:
    1. __init__: Create server instance with configuration
    2. initialize(): Setup MCP server and register handlers
    3. start(): Start accepting requests (via run_stdio or run_with_transport)
    4. [Handle requests...]
    5. stop(): Graceful shutdown
    6. shutdown(): Cleanup and final teardown

    Attributes:
        config: Server configuration
        registry: Component registry for tools/prompts/resources
        mcp_server: Underlying MCP SDK server instance
        _initialized: Whether server has been initialized
        _running: Whether server is currently running
        _request_count: Total number of requests handled

    Example:
        >>> config = get_default_config()
        >>> server = SimplyMCPServer(config)
        >>> await server.initialize()
        >>>
        >>> # Register a tool
        >>> def add_numbers(a: int, b: int) -> int:
        ...     return a + b
        >>>
        >>> server.register_tool({
        ...     "name": "add",
        ...     "description": "Add two numbers",
        ...     "input_schema": {
        ...         "type": "object",
        ...         "properties": {
        ...             "a": {"type": "integer"},
        ...             "b": {"type": "integer"}
        ...         },
        ...         "required": ["a", "b"]
        ...     },
        ...     "handler": add_numbers
        ... })
        >>>
        >>> # Run server
        >>> await server.run_stdio()
    """

    def __init__(self, config: SimplyMCPConfig | None = None) -> None:
        """Initialize the Simply-MCP server.

        Args:
            config: Optional server configuration. If not provided, uses default config.

        Example:
            >>> server = SimplyMCPServer()  # Use defaults
            >>> # Or with custom config:
            >>> config = SimplyMCPConfig(...)
            >>> server = SimplyMCPServer(config)
        """
        self.config = config or get_default_config()
        self.registry = ComponentRegistry()
        self._initialized = False
        self._running = False
        self._request_count = 0

        # Initialize progress tracker if progress is enabled
        self.progress_tracker: Any = None
        if self.config.features.enable_progress:
            from simply_mcp.features.progress import ProgressTracker

            # Create progress tracker with notification callback
            self.progress_tracker = ProgressTracker(
                default_callback=self._send_progress_notification
            )

        # Create MCP server instance with lifespan
        self.mcp_server: MCPServer[dict[str, Any], Any] = MCPServer(
            name=self.config.server.name,
            version=self.config.server.version,
            instructions=self.config.server.description,
            website_url=self.config.server.homepage,
            lifespan=self._lifespan,
        )

        logger.info(
            f"Created SimplyMCPServer: {self.config.server.name} v{self.config.server.version}",
            extra={
                "context": {
                    "server_name": self.config.server.name,
                    "server_version": self.config.server.version,
                    "progress_enabled": self.config.features.enable_progress,
                }
            },
        )

    async def _send_progress_notification(
        self, update: dict[str, Any]
    ) -> None:
        """Send progress notification to MCP client.

        This method sends progress updates via the MCP protocol's progress
        notification mechanism.

        Args:
            update: Progress update dict containing percentage, message, etc.
        """
        try:
            # Send progress notification via MCP server
            # Note: The MCP SDK doesn't yet have built-in progress notification support,
            # so we log it for now and prepare the structure for when it's available
            logger.debug(
                "Progress update",
                extra={
                    "context": {
                        "percentage": update.get("percentage"),
                        "message": update.get("message"),
                        "current": update.get("current"),
                        "total": update.get("total"),
                    }
                },
            )

            # When MCP SDK adds progress notification support, use:
            # await self.mcp_server.send_progress_notification(
            #     progress_token=update.get("operation_id"),
            #     progress=update["percentage"],
            #     total=100.0,
            #     message=update.get("message"),
            # )

        except Exception as e:
            logger.error(
                f"Error sending progress notification: {e}",
                extra={"context": {"error": str(e)}},
            )

    @asynccontextmanager
    async def _lifespan(
        self, server: MCPServer[dict[str, Any], Any]
    ) -> AsyncIterator[dict[str, Any]]:
        """Lifespan context manager for MCP server.

        This is called by the MCP SDK during server startup and shutdown.
        It provides a place for initialization and cleanup logic.

        Args:
            server: The MCP server instance

        Yields:
            Context dictionary that will be available during request handling
        """
        logger.info("Server lifespan starting")
        self._running = True

        # Yield context that will be available to handlers
        context = {
            "registry": self.registry,
            "config": self.config,
            "server": self,
            "progress_tracker": self.progress_tracker,
        }

        try:
            yield context
        finally:
            self._running = False

            # Clean up progress operations if tracker exists
            if self.progress_tracker:
                try:
                    await self.progress_tracker.cleanup_completed()
                except Exception as e:
                    logger.warning(f"Error cleaning up progress operations: {e}")

            logger.info(
                "Server lifespan ending",
                extra={"context": {"requests_handled": self._request_count}},
            )

    async def initialize(self) -> None:
        """Initialize the MCP server and register all handlers.

        This method sets up the MCP SDK server with handlers for tools, prompts,
        and resources. It must be called before starting the server.

        Raises:
            RuntimeError: If server is already initialized

        Example:
            >>> server = SimplyMCPServer()
            >>> await server.initialize()
        """
        if self._initialized:
            raise RuntimeError("Server already initialized")

        logger.info("Initializing MCP server")

        # Register MCP handlers
        self._register_list_tools_handler()
        self._register_call_tool_handler()
        self._register_list_prompts_handler()
        self._register_get_prompt_handler()
        self._register_list_resources_handler()
        self._register_read_resource_handler()

        self._initialized = True
        logger.info("MCP server initialized successfully")

    def _register_list_tools_handler(self) -> None:
        """Register handler for listing tools."""

        @self.mcp_server.list_tools()  # type: ignore[misc, no-untyped-call]
        async def handle_list_tools() -> list[types.Tool]:
            """Handle list_tools request from MCP client."""
            request_id = f"req-{uuid.uuid4().hex[:8]}"

            with LoggerContext(request_id=request_id):
                logger.debug("Handling list_tools request")
                start_time = time.time()

                try:
                    # Get all registered tools from registry
                    tool_configs = self.registry.list_tools()

                    # Convert to MCP Tool types
                    tools = [
                        types.Tool(
                            name=config.name,
                            description=config.description,
                            inputSchema=config.input_schema,
                        )
                        for config in tool_configs
                    ]

                    elapsed = time.time() - start_time
                    logger.info(
                        f"Listed {len(tools)} tools",
                        extra={
                            "context": {
                                "tool_count": len(tools),
                                "elapsed_ms": round(elapsed * 1000, 2),
                            }
                        },
                    )

                    return tools

                except Exception as e:
                    elapsed = time.time() - start_time
                    logger.error(
                        f"Error listing tools: {e}",
                        extra={
                            "context": {
                                "error": str(e),
                                "elapsed_ms": round(elapsed * 1000, 2),
                            }
                        },
                    )
                    raise

    def _register_call_tool_handler(self) -> None:
        """Register handler for calling tools."""

        @self.mcp_server.call_tool()  # type: ignore[misc]
        async def handle_call_tool(
            name: str, arguments: dict[str, Any]
        ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
            """Handle call_tool request from MCP client."""
            request_id = f"req-{uuid.uuid4().hex[:8]}"

            with LoggerContext(request_id=request_id, tool_name=name):
                logger.info(f"Handling call_tool request: {name}")
                start_time = time.time()

                try:
                    self._request_count += 1

                    # Look up tool in registry
                    tool_config = self.registry.get_tool(name)
                    if not tool_config:
                        raise HandlerNotFoundError(name, "tool")

                    # Get handler function
                    handler: HandlerFunction = tool_config.handler

                    # Check if handler accepts a progress parameter
                    progress_reporter = None
                    sig = inspect.signature(handler)
                    if "progress" in sig.parameters and self.progress_tracker:
                        # Create a progress reporter for this operation
                        operation_id = f"{name}-{request_id}"
                        progress_reporter = await self.progress_tracker.create_operation(
                            operation_id=operation_id
                        )
                        arguments["progress"] = progress_reporter

                    # Execute handler
                    logger.debug(f"Executing tool handler: {name}")
                    try:
                        result = handler(**arguments)
                        # Handle async handlers
                        if asyncio.iscoroutine(result):
                            result = await result

                        # Complete progress if reporter was created
                        if progress_reporter and not progress_reporter.is_completed:
                            await progress_reporter.complete()

                    except Exception as e:
                        # Fail progress if reporter was created
                        if progress_reporter and not progress_reporter.is_completed:
                            await progress_reporter.fail(str(e))
                        raise HandlerExecutionError(name, e) from e
                    finally:
                        # Clean up progress operation
                        if progress_reporter and self.progress_tracker:
                            await self.progress_tracker.remove_operation(
                                progress_reporter.operation_id
                            )

                    # Convert result to MCP content
                    content: list[
                        types.TextContent | types.ImageContent | types.EmbeddedResource
                    ]
                    if isinstance(result, str):
                        content = [types.TextContent(type="text", text=result)]
                    elif isinstance(result, dict):
                        import json

                        content = [
                            types.TextContent(
                                type="text", text=json.dumps(result, indent=2)
                            )
                        ]
                    elif isinstance(result, list):
                        content = [
                            types.TextContent(type="text", text=str(item))
                            for item in result
                        ]
                    else:
                        content = [types.TextContent(type="text", text=str(result))]

                    elapsed = time.time() - start_time
                    logger.info(
                        f"Tool execution completed: {name}",
                        extra={
                            "context": {
                                "tool_name": name,
                                "elapsed_ms": round(elapsed * 1000, 2),
                                "success": True,
                            }
                        },
                    )

                    return content

                except HandlerNotFoundError as e:
                    elapsed = time.time() - start_time
                    logger.error(
                        f"Tool not found: {name}",
                        extra={
                            "context": {
                                "tool_name": name,
                                "error": str(e),
                                "elapsed_ms": round(elapsed * 1000, 2),
                            }
                        },
                    )
                    raise

                except HandlerExecutionError as e:
                    elapsed = time.time() - start_time
                    logger.error(
                        f"Tool execution failed: {name}",
                        extra={
                            "context": {
                                "tool_name": name,
                                "error": str(e),
                                "original_error": str(e.original_error),
                                "elapsed_ms": round(elapsed * 1000, 2),
                            }
                        },
                    )
                    raise

                except Exception as e:
                    elapsed = time.time() - start_time
                    logger.error(
                        f"Unexpected error calling tool: {name}",
                        extra={
                            "context": {
                                "tool_name": name,
                                "error": str(e),
                                "error_type": type(e).__name__,
                                "elapsed_ms": round(elapsed * 1000, 2),
                            }
                        },
                    )
                    raise

    def _register_list_prompts_handler(self) -> None:
        """Register handler for listing prompts."""

        @self.mcp_server.list_prompts()  # type: ignore[misc, no-untyped-call]
        async def handle_list_prompts() -> list[types.Prompt]:
            """Handle list_prompts request from MCP client."""
            request_id = f"req-{uuid.uuid4().hex[:8]}"

            with LoggerContext(request_id=request_id):
                logger.debug("Handling list_prompts request")
                start_time = time.time()

                try:
                    # Get all registered prompts from registry
                    prompt_configs = self.registry.list_prompts()

                    # Convert to MCP Prompt types
                    prompts = [
                        types.Prompt(
                            name=config.name,
                            description=config.description,
                            arguments=[
                                types.PromptArgument(name=arg, required=True)
                                for arg in config.arguments
                            ]
                            if config.arguments
                            else None,
                        )
                        for config in prompt_configs
                    ]

                    elapsed = time.time() - start_time
                    logger.info(
                        f"Listed {len(prompts)} prompts",
                        extra={
                            "context": {
                                "prompt_count": len(prompts),
                                "elapsed_ms": round(elapsed * 1000, 2),
                            }
                        },
                    )

                    return prompts

                except Exception as e:
                    elapsed = time.time() - start_time
                    logger.error(
                        f"Error listing prompts: {e}",
                        extra={
                            "context": {
                                "error": str(e),
                                "elapsed_ms": round(elapsed * 1000, 2),
                            }
                        },
                    )
                    raise

    def _register_get_prompt_handler(self) -> None:
        """Register handler for getting prompts."""

        @self.mcp_server.get_prompt()  # type: ignore[misc, no-untyped-call]
        async def handle_get_prompt(
            name: str, arguments: dict[str, str] | None
        ) -> types.GetPromptResult:
            """Handle get_prompt request from MCP client."""
            request_id = f"req-{uuid.uuid4().hex[:8]}"

            with LoggerContext(request_id=request_id, prompt_name=name):
                logger.info(f"Handling get_prompt request: {name}")
                start_time = time.time()

                try:
                    self._request_count += 1

                    # Look up prompt in registry
                    prompt_config = self.registry.get_prompt(name)
                    if not prompt_config:
                        raise HandlerNotFoundError(name, "prompt")

                    # Generate prompt content
                    if prompt_config.handler:
                        # Dynamic prompt with handler
                        handler: HandlerFunction = prompt_config.handler
                        try:
                            result = handler(**(arguments or {}))
                            # Handle async handlers
                            if asyncio.iscoroutine(result):
                                result = await result
                            prompt_text = str(result)
                        except Exception as e:
                            raise HandlerExecutionError(name, e) from e
                    elif prompt_config.template:
                        # Static template
                        template = prompt_config.template
                        if arguments:
                            # Simple template substitution
                            prompt_text = template.format(**arguments)
                        else:
                            prompt_text = template
                    else:
                        raise ValidationError(
                            f"Prompt '{name}' has neither handler nor template",
                            code="INVALID_PROMPT_CONFIG",
                        )

                    # Create prompt result
                    result = types.GetPromptResult(
                        description=prompt_config.description,
                        messages=[
                            types.PromptMessage(
                                role="user",
                                content=types.TextContent(type="text", text=prompt_text),
                            )
                        ],
                    )

                    elapsed = time.time() - start_time
                    logger.info(
                        f"Prompt retrieved: {name}",
                        extra={
                            "context": {
                                "prompt_name": name,
                                "elapsed_ms": round(elapsed * 1000, 2),
                            }
                        },
                    )

                    return result

                except HandlerNotFoundError as e:
                    elapsed = time.time() - start_time
                    logger.error(
                        f"Prompt not found: {name}",
                        extra={
                            "context": {
                                "prompt_name": name,
                                "error": str(e),
                                "elapsed_ms": round(elapsed * 1000, 2),
                            }
                        },
                    )
                    raise

                except Exception as e:
                    elapsed = time.time() - start_time
                    logger.error(
                        f"Error getting prompt: {name}",
                        extra={
                            "context": {
                                "prompt_name": name,
                                "error": str(e),
                                "error_type": type(e).__name__,
                                "elapsed_ms": round(elapsed * 1000, 2),
                            }
                        },
                    )
                    raise

    def _register_list_resources_handler(self) -> None:
        """Register handler for listing resources."""

        @self.mcp_server.list_resources()  # type: ignore[misc, no-untyped-call]
        async def handle_list_resources() -> list[types.Resource]:
            """Handle list_resources request from MCP client."""
            request_id = f"req-{uuid.uuid4().hex[:8]}"

            with LoggerContext(request_id=request_id):
                logger.debug("Handling list_resources request")
                start_time = time.time()

                try:
                    # Get all registered resources from registry
                    resource_configs = self.registry.list_resources()

                    # Convert to MCP Resource types
                    resources = [
                        types.Resource(
                            uri=AnyUrl(config.uri),
                            name=config.name,
                            description=config.description,
                            mimeType=config.mime_type,
                        )
                        for config in resource_configs
                    ]

                    elapsed = time.time() - start_time
                    logger.info(
                        f"Listed {len(resources)} resources",
                        extra={
                            "context": {
                                "resource_count": len(resources),
                                "elapsed_ms": round(elapsed * 1000, 2),
                            }
                        },
                    )

                    return resources

                except Exception as e:
                    elapsed = time.time() - start_time
                    logger.error(
                        f"Error listing resources: {e}",
                        extra={
                            "context": {
                                "error": str(e),
                                "elapsed_ms": round(elapsed * 1000, 2),
                            }
                        },
                    )
                    raise

    def _register_read_resource_handler(self) -> None:
        """Register handler for reading resources."""

        @self.mcp_server.read_resource()  # type: ignore[misc, no-untyped-call]
        async def handle_read_resource(uri: AnyUrl) -> str:
            """Handle read_resource request from MCP client."""
            request_id = f"req-{uuid.uuid4().hex[:8]}"

            with LoggerContext(request_id=request_id, resource_uri=str(uri)):
                logger.info(f"Handling read_resource request: {uri}")
                start_time = time.time()

                try:
                    self._request_count += 1

                    # Look up resource in registry
                    resource_config = self.registry.get_resource(str(uri))
                    if not resource_config:
                        raise HandlerNotFoundError(str(uri), "resource")

                    # Get handler function
                    handler: HandlerFunction = resource_config.handler

                    # Execute handler
                    logger.debug(f"Executing resource handler: {uri}")
                    try:
                        result = handler()
                        # Handle async handlers
                        if asyncio.iscoroutine(result):
                            result = await result
                    except Exception as e:
                        raise HandlerExecutionError(str(uri), e) from e

                    # Convert result to string, handling binary content
                    if isinstance(result, str):
                        content = result
                    elif isinstance(result, bytes):
                        # Check if binary content is enabled
                        if self.config.features.enable_binary_content:
                            # Import here to avoid circular dependency
                            from simply_mcp.features.binary import BinaryContent

                            # Wrap bytes in BinaryContent and encode
                            binary = BinaryContent(
                                result,
                                mime_type=resource_config.mime_type,
                            )
                            content = binary.to_base64()
                            logger.debug(
                                f"Encoded binary resource as base64: {len(content)} chars"
                            )
                        else:
                            # Try UTF-8 decode for backwards compatibility
                            content = result.decode("utf-8")
                    elif isinstance(result, dict):
                        import json

                        content = json.dumps(result, indent=2)
                    else:
                        # Check if it's a BinaryContent instance
                        try:
                            from simply_mcp.features.binary import BinaryContent

                            if isinstance(result, BinaryContent):
                                if self.config.features.enable_binary_content:
                                    content = result.to_base64()
                                    logger.debug(
                                        f"Encoded BinaryContent as base64: {len(content)} chars"
                                    )
                                else:
                                    raise ValidationError(
                                        "Binary content is disabled in configuration",
                                        code="BINARY_CONTENT_DISABLED",
                                    )
                            else:
                                content = str(result)
                        except ImportError:
                            content = str(result)

                    elapsed = time.time() - start_time
                    logger.info(
                        f"Resource read completed: {uri}",
                        extra={
                            "context": {
                                "resource_uri": str(uri),
                                "content_length": len(content),
                                "elapsed_ms": round(elapsed * 1000, 2),
                            }
                        },
                    )

                    return content

                except HandlerNotFoundError as e:
                    elapsed = time.time() - start_time
                    logger.error(
                        f"Resource not found: {uri}",
                        extra={
                            "context": {
                                "resource_uri": str(uri),
                                "error": str(e),
                                "elapsed_ms": round(elapsed * 1000, 2),
                            }
                        },
                    )
                    raise

                except Exception as e:
                    elapsed = time.time() - start_time
                    logger.error(
                        f"Error reading resource: {uri}",
                        extra={
                            "context": {
                                "resource_uri": str(uri),
                                "error": str(e),
                                "error_type": type(e).__name__,
                                "elapsed_ms": round(elapsed * 1000, 2),
                            }
                        },
                    )
                    raise

    def register_tool(self, config: ToolConfigModel) -> None:
        """Register a tool with the server.

        Args:
            config: Tool configuration containing name, description, schema, and handler

        Raises:
            ValidationError: If a tool with the same name already exists

        Example:
            >>> def add_numbers(a: int, b: int) -> int:
            ...     return a + b
            >>>
            >>> server.register_tool({
            ...     "name": "add",
            ...     "description": "Add two numbers",
            ...     "input_schema": {
            ...         "type": "object",
            ...         "properties": {
            ...             "a": {"type": "integer"},
            ...             "b": {"type": "integer"}
            ...         },
            ...         "required": ["a", "b"]
            ...     },
            ...     "handler": add_numbers
            ... })
        """
        self.registry.register_tool(config)
        logger.info(
            f"Registered tool: {config.name}",
            extra={"context": {"tool_name": config.name}},
        )

    def register_prompt(self, config: PromptConfigModel) -> None:
        """Register a prompt with the server.

        Args:
            config: Prompt configuration containing name, description, and template/handler

        Raises:
            ValidationError: If a prompt with the same name already exists

        Example:
            >>> server.register_prompt({
            ...     "name": "greeting",
            ...     "description": "Generate a greeting",
            ...     "template": "Hello, {name}!"
            ... })
        """
        self.registry.register_prompt(config)
        logger.info(
            f"Registered prompt: {config.name}",
            extra={"context": {"prompt_name": config.name}},
        )

    def register_resource(self, config: ResourceConfigModel) -> None:
        """Register a resource with the server.

        Args:
            config: Resource configuration containing uri, name, description, and handler

        Raises:
            ValidationError: If a resource with the same URI already exists

        Example:
            >>> def load_config() -> dict:
            ...     return {"key": "value"}
            >>>
            >>> server.register_resource({
            ...     "uri": "config://app",
            ...     "name": "config",
            ...     "description": "Application configuration",
            ...     "mime_type": "application/json",
            ...     "handler": load_config
            ... })
        """
        self.registry.register_resource(config)
        logger.info(
            f"Registered resource: {config.uri}",
            extra={
                "context": {
                    "resource_uri": config.uri,
                    "resource_name": config.name,
                }
            },
        )

    def get_mcp_server(self) -> MCPServer[dict[str, Any], Any]:
        """Get the underlying MCP SDK server instance.

        Returns:
            The MCP server instance

        Example:
            >>> mcp_server = server.get_mcp_server()
            >>> # Can use for advanced MCP SDK features
        """
        return self.mcp_server

    async def run_stdio(self) -> None:
        """Run the server with stdio transport.

        This is the most common way to run an MCP server, using standard input/output
        for communication. The server will run until interrupted.

        Raises:
            RuntimeError: If server is not initialized

        Example:
            >>> server = SimplyMCPServer()
            >>> await server.initialize()
            >>> await server.run_stdio()  # Runs until interrupted
        """
        if not self._initialized:
            raise RuntimeError("Server not initialized. Call initialize() first.")

        logger.info("Starting MCP server with stdio transport")

        # Create initialization options
        init_options = self.mcp_server.create_initialization_options(
            notification_options=NotificationOptions(),
            experimental_capabilities={},
        )

        # Run with stdio transport
        async with stdio_server() as (read_stream, write_stream):
            await self.mcp_server.run(
                read_stream,
                write_stream,
                init_options,
                raise_exceptions=False,
            )

    async def run_with_transport(
        self,
        read_stream: MemoryObjectReceiveStream[SessionMessage | Exception],
        write_stream: MemoryObjectSendStream[SessionMessage],
    ) -> None:
        """Run the server with a custom transport.

        This allows using custom transports (HTTP, SSE, etc.) instead of stdio.

        Args:
            read_stream: Input stream for receiving messages
            write_stream: Output stream for sending messages

        Raises:
            RuntimeError: If server is not initialized

        Example:
            >>> server = SimplyMCPServer()
            >>> await server.initialize()
            >>> # Create custom streams...
            >>> await server.run_with_transport(read_stream, write_stream)
        """
        if not self._initialized:
            raise RuntimeError("Server not initialized. Call initialize() first.")

        logger.info("Starting MCP server with custom transport")

        # Create initialization options
        init_options = self.mcp_server.create_initialization_options(
            notification_options=NotificationOptions(),
            experimental_capabilities={},
        )

        # Run with custom transport
        await self.mcp_server.run(
            read_stream,
            write_stream,
            init_options,
            raise_exceptions=False,
        )

    async def run_http(
        self,
        host: str = "0.0.0.0",
        port: int = 3000,
        cors_enabled: bool = True,
        cors_origins: list[str] | None = None,
    ) -> None:
        """Run the server with HTTP transport.

        This method starts an HTTP server that accepts MCP requests
        via RESTful HTTP endpoints using JSON-RPC 2.0 protocol.

        Args:
            host: Host to bind to (default: 0.0.0.0)
            port: Port to bind to (default: 3000)
            cors_enabled: Whether to enable CORS (default: True)
            cors_origins: Allowed CORS origins or None for all (default: None)

        Raises:
            RuntimeError: If server is not initialized

        Example:
            >>> server = SimplyMCPServer()
            >>> await server.initialize()
            >>> await server.run_http(port=8080)
        """
        if not self._initialized:
            raise RuntimeError("Server not initialized. Call initialize() first.")

        logger.info(f"Starting MCP server with HTTP transport on {host}:{port}")

        # Import here to avoid circular dependency
        from simply_mcp.transports.http import HTTPTransport

        # Create and start HTTP transport
        transport = HTTPTransport(
            server=self,
            host=host,
            port=port,
            cors_enabled=cors_enabled,
            cors_origins=cors_origins,
        )

        try:
            await transport.start()

            # Keep running until interrupted
            while self._running:
                await asyncio.sleep(1)

        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
            raise

        finally:
            await transport.stop()

    async def run_sse(
        self,
        host: str = "0.0.0.0",
        port: int = 3000,
        cors_enabled: bool = True,
        cors_origins: list[str] | None = None,
    ) -> None:
        """Run the server with SSE transport.

        This method starts a Server-Sent Events (SSE) server that provides
        real-time event streaming to web clients.

        Args:
            host: Host to bind to (default: 0.0.0.0)
            port: Port to bind to (default: 3000)
            cors_enabled: Whether to enable CORS (default: True)
            cors_origins: Allowed CORS origins or None for all (default: None)

        Raises:
            RuntimeError: If server is not initialized

        Example:
            >>> server = SimplyMCPServer()
            >>> await server.initialize()
            >>> await server.run_sse(port=8080)
        """
        if not self._initialized:
            raise RuntimeError("Server not initialized. Call initialize() first.")

        logger.info(f"Starting MCP server with SSE transport on {host}:{port}")

        # Import here to avoid circular dependency
        from simply_mcp.transports.sse import SSETransport

        # Create and start SSE transport
        transport = SSETransport(
            server=self,
            host=host,
            port=port,
            cors_enabled=cors_enabled,
            cors_origins=cors_origins,
        )

        try:
            await transport.start()

            # Keep running until interrupted
            while self._running:
                await asyncio.sleep(1)

        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
            raise

        finally:
            await transport.stop()

    async def start(self) -> None:
        """Start the server (alias for run_stdio).

        This is a convenience method that calls run_stdio().

        Raises:
            RuntimeError: If server is not initialized

        Example:
            >>> server = SimplyMCPServer()
            >>> await server.initialize()
            >>> await server.start()
        """
        await self.run_stdio()

    async def stop(self) -> None:
        """Stop the server gracefully.

        This method signals the server to stop accepting new requests and
        complete any in-progress requests before shutting down.

        Example:
            >>> await server.stop()
        """
        logger.info("Stopping MCP server")
        self._running = False
        logger.info("MCP server stopped")

    async def shutdown(self) -> None:
        """Shutdown the server and cleanup resources.

        This method performs final cleanup, including closing connections
        and releasing resources.

        Example:
            >>> await server.shutdown()
        """
        logger.info("Shutting down MCP server")
        await self.stop()
        self._initialized = False
        logger.info("MCP server shutdown complete")

    @property
    def is_initialized(self) -> bool:
        """Check if server is initialized.

        Returns:
            True if server is initialized, False otherwise
        """
        return self._initialized

    @property
    def is_running(self) -> bool:
        """Check if server is running.

        Returns:
            True if server is running, False otherwise
        """
        return self._running

    @property
    def request_count(self) -> int:
        """Get total number of requests handled.

        Returns:
            Total request count
        """
        return self._request_count


__all__ = ["SimplyMCPServer"]
