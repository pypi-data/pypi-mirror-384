"""List command for Simply-MCP CLI.

This module implements the 'list' command which displays all registered
components (tools, prompts, resources) from an MCP server file.
"""

import json
import sys
from typing import Any

import click
from rich.table import Table

from simply_mcp.cli.utils import (
    console,
    detect_api_style,
    format_error,
    format_info,
    load_python_module,
)


@click.command(name="list")
@click.argument("server_file", type=click.Path(exists=True))
@click.option(
    "--tools",
    is_flag=True,
    help="List only tools",
)
@click.option(
    "--prompts",
    is_flag=True,
    help="List only prompts",
)
@click.option(
    "--resources",
    is_flag=True,
    help="List only resources",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output as JSON",
)
def list_components(
    server_file: str,
    tools: bool,
    prompts: bool,
    resources: bool,
    output_json: bool,
) -> None:
    """List all components in an MCP server file.

    Loads a server file and displays all registered tools, prompts,
    and resources. Supports filtering by component type and JSON output.

    Examples:

        \b
        # List all components
        simply-mcp list server.py

        \b
        # List only tools
        simply-mcp list server.py --tools

        \b
        # List as JSON
        simply-mcp list server.py --json

        \b
        # List multiple types
        simply-mcp list server.py --tools --prompts
    """
    try:
        # Load the Python module
        console.print(f"[dim]Loading server file: {server_file}[/dim]")

        try:
            module = load_python_module(server_file)
        except FileNotFoundError as e:
            format_error(str(e), "File Not Found")
            sys.exit(1)
        except ImportError as e:
            format_error(f"Failed to import module: {e}", "Import Error")
            sys.exit(1)
        except Exception as e:
            format_error(f"Error loading module: {e}", "Load Error")
            sys.exit(1)

        # Detect API style and get server
        api_style, server = detect_api_style(module)

        if server is None:
            format_error(
                "No MCP server found in the file.\n\n"
                "Make sure your file uses one of:\n"
                "  - Decorator API: @tool(), @prompt(), @resource()\n"
                "  - Builder API: SimplyMCP(...)\n"
                "  - Class API: @mcp_server class",
                "No Server Found"
            )
            sys.exit(1)

        console.print(f"[dim]Detected {api_style} API style[/dim]")

        # Get components from registry
        tools_list = server.registry.list_tools()
        prompts_list = server.registry.list_prompts()
        resources_list = server.registry.list_resources()

        # Determine what to show
        filter_type: str | None = None
        if tools and not prompts and not resources:
            filter_type = "tools"
            components_to_show = tools_list
        elif prompts and not tools and not resources:
            filter_type = "prompts"
            components_to_show = prompts_list
        elif resources and not tools and not prompts:
            filter_type = "resources"
            components_to_show = resources_list
        else:
            # Show all or multiple types
            components_to_show = []
            if tools or (not tools and not prompts and not resources):
                components_to_show.extend(tools_list)
            if prompts or (not tools and not prompts and not resources):
                components_to_show.extend(prompts_list)
            if resources or (not tools and not prompts and not resources):
                components_to_show.extend(resources_list)

        # Output as JSON
        if output_json:
            _output_json(tools_list, prompts_list, resources_list, filter_type)
            return

        # Output as table
        _output_table(
            tools_list if (tools or filter_type is None) else [],
            prompts_list if (prompts or filter_type is None) else [],
            resources_list if (resources or filter_type is None) else [],
            filter_type
        )

        # Display summary
        total = len(components_to_show)
        if total == 0:
            format_info("No components found", "Empty Server")
        else:
            console.print(
                f"\n[bold]Total:[/bold] [green]{total} component(s)[/green]"
            )

    except Exception as e:
        format_error(f"Error listing components: {e}", "Error")
        import traceback
        console.print("[dim]" + traceback.format_exc() + "[/dim]")
        sys.exit(1)


def _output_json(
    tools_list: list[Any],
    prompts_list: list[Any],
    resources_list: list[Any],
    filter_type: str | None
) -> None:
    """Output components as JSON.

    Args:
        tools_list: List of tool configs
        prompts_list: List of prompt configs
        resources_list: List of resource configs
        filter_type: Optional filter type
    """
    output = {}

    if filter_type is None or filter_type == "tools":
        output["tools"] = [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema,
            }
            for tool in tools_list
        ]

    if filter_type is None or filter_type == "prompts":
        output["prompts"] = [
            {
                "name": prompt.name,
                "description": prompt.description,
                "arguments": prompt.arguments,
            }
            for prompt in prompts_list
        ]

    if filter_type is None or filter_type == "resources":
        output["resources"] = [
            {
                "uri": resource.uri,
                "name": resource.name,
                "description": resource.description,
                "mime_type": resource.mime_type,
            }
            for resource in resources_list
        ]

    # Output JSON
    console.print(json.dumps(output, indent=2))


def _output_table(
    tools_list: list[Any],
    prompts_list: list[Any],
    resources_list: list[Any],
    filter_type: str | None
) -> None:
    """Output components as a Rich table.

    Args:
        tools_list: List of tool configs
        prompts_list: List of prompt configs
        resources_list: List of resource configs
        filter_type: Optional filter type
    """
    # Create table with proper title
    title = "MCP Server Components"
    if filter_type == "tools":
        title = "Tools"
    elif filter_type == "prompts":
        title = "Prompts"
    elif filter_type == "resources":
        title = "Resources"

    table = Table(title=title, show_header=True, header_style="bold magenta")
    table.add_column("Type", style="cyan", no_wrap=True)
    table.add_column("Name", style="green")
    table.add_column("Description", style="white")

    # Add tools
    for tool in tools_list:
        table.add_row(
            "[cyan]Tool[/cyan]",
            tool.name,
            tool.description[:80] if tool.description else ""  # Truncate long descriptions
        )

    # Add prompts
    for prompt in prompts_list:
        args_str = ""
        if prompt.arguments:
            args_str = f" ({', '.join(prompt.arguments)})"

        table.add_row(
            "[yellow]Prompt[/yellow]",
            prompt.name + args_str,
            prompt.description[:80] if prompt.description else ""
        )

    # Add resources
    for resource in resources_list:
        table.add_row(
            "[magenta]Resource[/magenta]",
            f"{resource.name} [{resource.mime_type}]",
            resource.description[:80] if resource.description else ""
        )

    console.print("\n")
    console.print(table)


__all__ = ["list_components"]
