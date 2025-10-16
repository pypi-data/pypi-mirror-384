"""Shared utilities for Simply-MCP CLI.

This module provides common utilities for CLI operations including:
- Module loading and introspection
- API style detection (decorator, builder, class-based)
- Rich formatting helpers
- Error handling utilities
"""

import importlib.util
import inspect
import sys
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from simply_mcp.api.programmatic import BuildMCPServer
from simply_mcp.api.decorators import get_global_server
from simply_mcp.core.server import SimplyMCPServer

# Rich console for output
console = Console()


def load_python_module(file_path: str) -> Any:
    """Load a Python module from a file path.

    Args:
        file_path: Path to Python file

    Returns:
        Loaded module object

    Raises:
        FileNotFoundError: If file doesn't exist
        ImportError: If module can't be loaded
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if not path.suffix == ".py":
        raise ValueError(f"Not a Python file: {file_path}")

    # Create module spec
    module_name = path.stem
    spec = importlib.util.spec_from_file_location(module_name, path)

    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module from: {file_path}")

    # Add parent directory to sys.path to support local imports
    parent_dir = str(path.parent.absolute())
    path_modified = False

    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
        path_modified = True

    try:
        # Load module
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module
    finally:
        # Clean up sys.path to avoid pollution
        if path_modified and parent_dir in sys.path:
            sys.path.remove(parent_dir)


def detect_api_style(module: Any) -> tuple[str, Any | None]:
    """Detect the API style used in a module.

    Detects:
    - Decorator API: Module-level @tool, @prompt, @resource decorators
    - Programmatic API: BuildMCPServer instance created in module
    - Class-based API: Class decorated with @mcp_server

    Args:
        module: Loaded Python module

    Returns:
        Tuple of (api_style, server_instance)
        - api_style: "decorator", "builder", "class", or "unknown"
        - server_instance: Server instance if found, None otherwise
    """
    # Check for programmatic API (BuildMCPServer instance)
    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        if isinstance(attr, BuildMCPServer):
            return ("builder", attr.get_server())

    # Check for class-based API (@mcp_server decorated class)
    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        if inspect.isclass(attr) and hasattr(attr, '_mcp_server'):
            server = attr._mcp_server
            if isinstance(server, SimplyMCPServer):
                return ("class", server)

    # Check for decorator API (global server with components)
    try:
        global_server = get_global_server()
        stats = global_server.registry.get_stats()
        if stats['total'] > 0:
            return ("decorator", global_server)
    except Exception:
        pass

    return ("unknown", None)


def get_server_instance(module: Any) -> SimplyMCPServer | None:
    """Get the server instance from a loaded module.

    Args:
        module: Loaded Python module

    Returns:
        Server instance if found, None otherwise
    """
    api_style, server = detect_api_style(module)
    return server


def format_error(message: str, title: str = "Error") -> None:
    """Display a formatted error message.

    Args:
        message: Error message to display
        title: Panel title (default: "Error")
    """
    console.print(Panel(f"[red]{message}[/red]", title=f"[bold red]{title}[/bold red]"))


def format_success(message: str, title: str = "Success") -> None:
    """Display a formatted success message.

    Args:
        message: Success message to display
        title: Panel title (default: "Success")
    """
    console.print(Panel(f"[green]{message}[/green]", title=f"[bold green]{title}[/bold green]"))


def format_info(message: str, title: str = "Info") -> None:
    """Display a formatted info message.

    Args:
        message: Info message to display
        title: Panel title (default: "Info")
    """
    console.print(Panel(f"[blue]{message}[/blue]", title=f"[bold blue]{title}[/bold blue]"))


def create_components_table(
    tools: list[dict[str, Any]],
    prompts: list[dict[str, Any]],
    resources: list[dict[str, Any]],
    filter_type: str | None = None
) -> Table:
    """Create a Rich table displaying components.

    Args:
        tools: List of tool configurations
        prompts: List of prompt configurations
        resources: List of resource configurations
        filter_type: Optional filter ("tools", "prompts", "resources")

    Returns:
        Rich Table object
    """
    table = Table(title="MCP Server Components", show_header=True, header_style="bold magenta")
    table.add_column("Type", style="cyan", no_wrap=True)
    table.add_column("Name", style="green")
    table.add_column("Description", style="white")

    # Add tools
    if filter_type is None or filter_type == "tools":
        for tool in tools:
            table.add_row(
                "[cyan]Tool[/cyan]",
                tool["name"],
                tool.get("description", "")
            )

    # Add prompts
    if filter_type is None or filter_type == "prompts":
        for prompt in prompts:
            table.add_row(
                "[yellow]Prompt[/yellow]",
                prompt["name"],
                prompt.get("description", "")
            )

    # Add resources
    if filter_type is None or filter_type == "resources":
        for resource in resources:
            table.add_row(
                "[magenta]Resource[/magenta]",
                resource["name"],
                resource.get("description", "")
            )

    return table


def validate_python_file(file_path: str) -> bool:
    """Validate that a file exists and is a Python file.

    Args:
        file_path: Path to file

    Returns:
        True if valid, False otherwise
    """
    path = Path(file_path)
    return path.exists() and path.suffix == ".py"


__all__ = [
    "console",
    "load_python_module",
    "detect_api_style",
    "get_server_instance",
    "format_error",
    "format_success",
    "format_info",
    "create_components_table",
    "validate_python_file",
]
