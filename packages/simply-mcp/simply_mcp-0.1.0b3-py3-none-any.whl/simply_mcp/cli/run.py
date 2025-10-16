"""Run command for Simply-MCP CLI.

This module implements the 'run' command which loads and executes
MCP servers from Python files. It supports auto-detection of API
styles and multiple transport types.
"""

import asyncio
import sys

import click
from rich.panel import Panel

from simply_mcp.cli.utils import (
    console,
    detect_api_style,
    format_error,
    format_info,
    format_success,
    load_python_module,
)
from simply_mcp.core.config import load_config
from simply_mcp.core.errors import SimplyMCPError


@click.command()
@click.argument("server_file", type=click.Path(exists=True))
@click.option(
    "--transport",
    type=click.Choice(["stdio", "http", "sse"], case_sensitive=False),
    default="stdio",
    help="Transport type to use (default: stdio)",
)
@click.option(
    "--port",
    type=int,
    default=3000,
    help="Port for network transports (default: 3000)",
)
@click.option(
    "--host",
    type=str,
    default="0.0.0.0",
    help="Host for network transports (default: 0.0.0.0)",
)
@click.option(
    "--cors/--no-cors",
    default=True,
    help="Enable/disable CORS for network transports (default: enabled)",
)
@click.option(
    "--config",
    type=click.Path(exists=True),
    default=None,
    help="Path to configuration file",
)
@click.option(
    "--watch",
    is_flag=True,
    help="Enable auto-reload on file changes (Phase 4)",
)
def run(
    server_file: str,
    transport: str,
    port: int,
    host: str,
    cors: bool,
    config: str | None,
    watch: bool,
) -> None:
    """Run an MCP server from a Python file.

    This command loads a Python file containing an MCP server definition
    and runs it with the specified transport. It automatically detects
    the API style (decorator, builder, or class-based) and initializes
    the server appropriately.

    Examples:

        \b
        # Run with stdio transport (default)
        simply-mcp run server.py

        \b
        # Run with explicit transport
        simply-mcp run server.py --transport stdio

        \b
        # Run with HTTP transport
        simply-mcp run server.py --transport http --port 8080

        \b
        # Run with SSE transport
        simply-mcp run server.py --transport sse --port 8080

        \b
        # Run with custom host and CORS disabled
        simply-mcp run server.py --transport http --host localhost --no-cors

        \b
        # Run with custom config
        simply-mcp run server.py --config myconfig.toml
    """
    if watch:
        format_error(
            "Auto-reload (--watch) is not yet implemented. This feature is planned for Phase 4.",
            "Not Implemented"
        )
        sys.exit(1)

    try:
        # Display startup info
        # Build transport info string
        transport_info = f"Transport: [yellow]{transport}[/yellow]"
        if transport in ["http", "sse"]:
            transport_info += f"\nHost: [yellow]{host}[/yellow]"
            transport_info += f"\nPort: [yellow]{port}[/yellow]"
            transport_info += f"\nCORS: [yellow]{'enabled' if cors else 'disabled'}[/yellow]"

        console.print(Panel(
            f"[bold cyan]Starting Simply-MCP Server[/bold cyan]\n\n"
            f"File: [green]{server_file}[/green]\n"
            f"{transport_info}",
            title="[bold blue]Simply-MCP[/bold blue]",
        ))

        # Load configuration if provided
        server_config = None
        if config:
            try:
                server_config = load_config(config)
                format_info(f"Loaded configuration from: {config}")
            except Exception as e:
                format_error(f"Failed to load configuration: {e}", "Configuration Error")
                sys.exit(1)

        # Update port if provided
        if port and server_config:
            server_config.transport.port = port

        # Load the Python module
        console.print("[dim]Loading server module...[/dim]")
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

        # Detect API style and get server instance
        console.print("[dim]Detecting API style...[/dim]")
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

        format_success(f"Detected {api_style} API style")

        # Display server info
        stats = server.registry.get_stats()
        console.print(Panel(
            f"[bold]Server:[/bold] [cyan]{server.config.server.name}[/cyan]\n"
            f"[bold]Version:[/bold] [cyan]{server.config.server.version}[/cyan]\n"
            f"[bold]Components:[/bold] [green]{stats['tools']} tools, "
            f"{stats['prompts']} prompts, {stats['resources']} resources[/green]",
            title="[bold green]Server Info[/bold green]",
        ))

        # Initialize server
        console.print("[dim]Initializing server...[/dim]")

        async def run_server() -> None:
            """Run the server asynchronously."""
            try:
                await server.initialize()
                format_success("Server initialized successfully")

                # Prepare running message
                if transport == "stdio":
                    running_msg = (
                        f"[bold green]Server is running on {transport} transport[/bold green]\n\n"
                        f"Press [bold]Ctrl+C[/bold] to stop the server."
                    )
                else:
                    running_msg = (
                        f"[bold green]Server is running on {transport} transport[/bold green]\n\n"
                        f"URL: [cyan]http://{host}:{port}[/cyan]\n"
                        f"Endpoints:\n"
                        f"  - [cyan]http://{host}:{port}/[/cyan] (info)\n"
                        f"  - [cyan]http://{host}:{port}/health[/cyan] (health check)\n"
                    )
                    if transport == "http":
                        running_msg += f"  - [cyan]http://{host}:{port}/mcp[/cyan] (JSON-RPC)\n"
                    elif transport == "sse":
                        running_msg += (
                            f"  - [cyan]http://{host}:{port}/sse[/cyan] (SSE stream)\n"
                            f"  - [cyan]http://{host}:{port}/mcp[/cyan] (JSON-RPC)\n"
                        )
                    running_msg += "\nPress [bold]Ctrl+C[/bold] to stop the server."

                console.print(Panel(
                    running_msg,
                    title="[bold cyan]Running[/bold cyan]",
                ))

                # Run with specified transport
                if transport == "stdio":
                    await server.run_stdio()
                elif transport == "http":
                    await server.run_http(
                        host=host,
                        port=port,
                        cors_enabled=cors,
                    )
                elif transport == "sse":
                    await server.run_sse(
                        host=host,
                        port=port,
                        cors_enabled=cors,
                    )

            except KeyboardInterrupt:
                console.print("\n[yellow]Received interrupt signal, shutting down...[/yellow]")
                await server.shutdown()
                format_info("Server stopped gracefully")
            except SimplyMCPError as e:
                format_error(f"MCP Error: {e}", "Server Error")
                sys.exit(1)
            except Exception as e:
                format_error(f"Unexpected error: {e}", "Fatal Error")
                import traceback
                console.print("[dim]" + traceback.format_exc() + "[/dim]")
                sys.exit(1)

        # Run the async server
        try:
            asyncio.run(run_server())
        except KeyboardInterrupt:
            console.print("\n[dim]Server stopped[/dim]")

    except Exception as e:
        format_error(f"Fatal error: {e}", "Error")
        import traceback
        console.print("[dim]" + traceback.format_exc() + "[/dim]")
        sys.exit(1)


__all__ = ["run"]
