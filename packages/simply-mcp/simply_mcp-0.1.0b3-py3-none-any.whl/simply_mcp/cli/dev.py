"""Development server command for Simply-MCP CLI.

This module implements the 'dev' command which provides an enhanced
development experience with auto-reload, debug logging, and interactive features.

Features:
- Auto-reload on file changes (via watch mode)
- DEBUG level logging by default
- Pretty console output with Rich
- Request/response logging
- Performance metrics (request timing)
- Error highlighting
- Component listing on startup
- Keyboard shortcuts for common actions
"""

import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

# Unix-only modules (not available on Windows)
try:
    import select
    import termios
    import tty
    HAS_TERMIOS = True
except ImportError:
    HAS_TERMIOS = False

import click
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from watchdog.observers import Observer

from simply_mcp.cli.utils import (
    console,
    detect_api_style,
    format_error,
    format_info,
    format_success,
    load_python_module,
)
from simply_mcp.cli.watch import DEFAULT_IGNORE_PATTERNS, ServerReloadHandler


class DevServerHandler(ServerReloadHandler):
    """Enhanced server handler for development mode with logging and metrics."""

    def __init__(
        self,
        server_file: str,
        debounce_delay: float,
        ignore_patterns: list[str],
        clear_console: bool,
        additional_args: list[str],
        log_requests: bool = True,
        show_metrics: bool = True,
    ) -> None:
        """Initialize the dev server handler.

        Args:
            server_file: Path to the server file to run
            debounce_delay: Delay in seconds before restarting after a change
            ignore_patterns: List of patterns to ignore
            clear_console: Whether to clear console on reload
            additional_args: Additional arguments to pass to the server
            log_requests: Whether to log requests/responses
            show_metrics: Whether to show performance metrics
        """
        self.log_requests = log_requests
        self.show_metrics = show_metrics
        self.request_count = 0
        self.error_count = 0
        self.start_time = time.time()

        # Call parent initializer
        super().__init__(
            server_file=server_file,
            debounce_delay=debounce_delay,
            ignore_patterns=ignore_patterns,
            clear_console=clear_console,
            additional_args=additional_args,
        )

    def _display_metrics(self) -> None:
        """Display performance metrics."""
        if not self.show_metrics:
            return

        uptime = time.time() - self.start_time
        uptime_str = f"{int(uptime // 3600)}h {int((uptime % 3600) // 60)}m {int(uptime % 60)}s"

        metrics_table = Table(show_header=False, box=None)
        metrics_table.add_row("[cyan]Uptime:[/cyan]", f"[white]{uptime_str}[/white]")
        metrics_table.add_row("[cyan]Requests:[/cyan]", f"[green]{self.request_count}[/green]")
        metrics_table.add_row("[cyan]Errors:[/cyan]", f"[red]{self.error_count}[/red]")

        console.print(Panel(metrics_table, title="[bold cyan]Metrics[/bold cyan]"))

    def _start_server(self) -> None:
        """Start the server process with enhanced logging."""
        try:
            # Build command to run the server with debug logging
            cmd = [
                sys.executable,
                "-m",
                "simply_mcp.cli.main",
                "run",
                str(self.server_file),
            ] + self.additional_args

            # Start the process
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE,
                env={**os.environ, "SIMPLY_MCP_LOG_LEVEL": "DEBUG"},
            )

            format_success(
                f"Dev server started (PID: {self.process.pid})",
                title="Started",
            )

            # Reset metrics
            self.start_time = time.time()
            self.request_count = 0
            self.error_count = 0

        except Exception as e:
            format_error(f"Failed to start dev server: {e}", title="Start Error")


def _display_welcome_banner(
    server_file: str,
    transport: str,
    host: str,
    port: int,
    auto_reload: bool,
) -> None:
    """Display welcome banner with server info.

    Args:
        server_file: Path to server file
        transport: Transport type
        host: Host address
        port: Port number
        auto_reload: Whether auto-reload is enabled
    """
    banner = Text()
    banner.append("Simply-MCP Development Mode\n\n", style="bold cyan")
    banner.append("File: ", style="white")
    banner.append(f"{server_file}\n", style="green")
    banner.append("Transport: ", style="white")
    banner.append(f"{transport}\n", style="yellow")

    if transport in ["http", "sse"]:
        banner.append("Host: ", style="white")
        banner.append(f"{host}\n", style="yellow")
        banner.append("Port: ", style="white")
        banner.append(f"{port}\n", style="yellow")

    banner.append("Auto-reload: ", style="white")
    banner.append(f"{'enabled' if auto_reload else 'disabled'}\n\n", style="yellow")

    banner.append("Keyboard Shortcuts:\n", style="bold white")
    banner.append("  r - Reload server\n", style="dim")
    banner.append("  l - List components\n", style="dim")
    banner.append("  m - Show metrics\n", style="dim")
    banner.append("  q - Quit\n", style="dim")

    console.print(Panel(banner, title="[bold blue]Development Server[/bold blue]"))


def _display_components(server_file: str) -> None:
    """Display registered components.

    Args:
        server_file: Path to server file
    """
    try:
        # Load the module
        module = load_python_module(server_file)
        api_style, server = detect_api_style(module)

        if server is None:
            console.print("[yellow]No server found[/yellow]")
            return

        # Get components
        tools = server.registry.list_tools()
        prompts = server.registry.list_prompts()
        resources = server.registry.list_resources()

        # Create table
        table = Table(title="Registered Components", show_header=True, header_style="bold magenta")
        table.add_column("Type", style="cyan", no_wrap=True)
        table.add_column("Name", style="green")
        table.add_column("Description", style="white")

        # Add tools
        for tool in tools:
            table.add_row(
                "[cyan]Tool[/cyan]",
                tool.name,
                (tool.description or "")[:60],
            )

        # Add prompts
        for prompt in prompts:
            table.add_row(
                "[yellow]Prompt[/yellow]",
                prompt.name,
                (prompt.description or "")[:60],
            )

        # Add resources
        for resource in resources:
            table.add_row(
                "[magenta]Resource[/magenta]",
                resource.name,
                (resource.description or "")[:60],
            )

        console.print("\n")
        console.print(table)
        console.print(f"\n[bold]Total:[/bold] [green]{len(tools) + len(prompts) + len(resources)} component(s)[/green]\n")

    except Exception as e:
        format_error(f"Error listing components: {e}", title="Error")


def _handle_keyboard_input(handler: DevServerHandler | None, server_file: str) -> bool:
    """Handle keyboard input for interactive commands.

    Args:
        handler: Dev server handler (None if auto-reload disabled)
        server_file: Path to server file

    Returns:
        True if should continue, False if should quit
    """
    # Check if stdin has input available (non-blocking)
    # This only works on Unix systems with select module
    if HAS_TERMIOS and sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
        try:
            char = sys.stdin.read(1).lower()

            if char == "q":
                console.print("\n[yellow]Quitting...[/yellow]")
                return False
            elif char == "r":
                if handler:
                    console.print("\n[cyan]Reloading server...[/cyan]")
                    handler._reload_server(server_file)
                else:
                    console.print("\n[yellow]Auto-reload is disabled[/yellow]")
            elif char == "l":
                console.print("\n")
                _display_components(server_file)
            elif char == "m":
                if handler:
                    console.print("\n")
                    handler._display_metrics()
                else:
                    console.print("\n[yellow]Metrics not available without auto-reload[/yellow]")

        except Exception:
            # Ignore input errors
            pass

    return True


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
    "--no-reload",
    is_flag=True,
    help="Disable auto-reload on file changes",
)
@click.option(
    "--no-color",
    is_flag=True,
    help="Disable colored output",
)
@click.option(
    "--log-requests/--no-log-requests",
    default=True,
    help="Log all requests/responses (default: enabled)",
)
def dev(
    server_file: str,
    transport: str,
    port: int,
    host: str,
    no_reload: bool,
    no_color: bool,
    log_requests: bool,
) -> None:
    """Run MCP server in development mode with enhanced features.

    Development mode provides an enhanced development experience with:
    - Auto-reload on file changes (default: enabled)
    - DEBUG level logging
    - Pretty-printed console output
    - Request/response logging
    - Performance metrics
    - Interactive keyboard shortcuts

    The dev mode is perfect for rapid development and debugging.

    Keyboard Shortcuts:
        r - Reload server manually
        l - List registered components
        m - Show performance metrics
        q - Quit dev server

    Examples:

        \b
        # Start dev server with defaults
        simply-mcp dev server.py

        \b
        # Start with HTTP transport
        simply-mcp dev server.py --transport http --port 8080

        \b
        # Start without auto-reload
        simply-mcp dev server.py --no-reload

        \b
        # Start with SSE transport
        simply-mcp dev server.py --transport sse --port 8080

        \b
        # Disable request logging
        simply-mcp dev server.py --no-log-requests
    """
    try:
        # Validate server file
        server_path = Path(server_file).resolve()
        if not server_path.exists():
            format_error(f"File not found: {server_file}", title="File Error")
            sys.exit(1)

        if not server_path.suffix == ".py":
            format_error(f"Not a Python file: {server_file}", title="File Error")
            sys.exit(1)

        # Configure console
        if no_color:
            console._force_terminal = False

        # Display welcome banner
        _display_welcome_banner(
            server_file=str(server_path),
            transport=transport,
            host=host,
            port=port,
            auto_reload=not no_reload,
        )

        # Display components on startup
        console.print("\n[dim]Loading server components...[/dim]")
        _display_components(str(server_path))

        # Build additional arguments for the server
        additional_args = ["--transport", transport]
        if transport in ["http", "sse"]:
            additional_args.extend(["--host", host])
            additional_args.extend(["--port", str(port)])
            additional_args.append("--cors")  # Always enable CORS in dev mode

        handler: DevServerHandler | None = None
        observer: Any = None

        if not no_reload:
            # Build ignore patterns
            ignore_patterns = list(DEFAULT_IGNORE_PATTERNS)

            # Create dev server handler
            handler = DevServerHandler(
                server_file=str(server_path),
                debounce_delay=1.0,
                ignore_patterns=ignore_patterns,
                clear_console=True,
                additional_args=additional_args,
                log_requests=log_requests,
                show_metrics=True,
            )

            # Create and start observer
            observer = Observer()
            observer.schedule(handler, str(Path.cwd()), recursive=True)
            observer.start()

            console.print("\n[bold green]Dev server running with auto-reload[/bold green]")
            console.print("[dim]Press 'q' to quit, 'r' to reload, 'l' to list components, 'm' for metrics[/dim]\n")

        else:
            # Run without auto-reload
            console.print("\n[bold green]Dev server running (auto-reload disabled)[/bold green]")
            console.print("[dim]Press 'q' to quit, 'l' to list components[/dim]\n")

            # Start server manually
            cmd = [
                sys.executable,
                "-m",
                "simply_mcp.cli.main",
                "run",
                str(server_path),
            ] + additional_args

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE,
                env={**os.environ, "SIMPLY_MCP_LOG_LEVEL": "DEBUG"},
            )

            format_success(f"Dev server started (PID: {process.pid})", title="Started")

        # Set terminal to non-blocking mode for keyboard input
        old_settings = None
        if HAS_TERMIOS:
            try:
                old_settings = termios.tcgetattr(sys.stdin)
                tty.setcbreak(sys.stdin.fileno())
            except Exception:
                # Not a TTY, keyboard shortcuts won't work
                pass

        try:
            # Keep the main thread alive and handle keyboard input
            while True:
                if not _handle_keyboard_input(handler, str(server_path)):
                    break
                time.sleep(0.1)

        except KeyboardInterrupt:
            console.print("\n[yellow]Received interrupt signal, shutting down...[/yellow]")

        finally:
            # Restore terminal settings
            if HAS_TERMIOS and old_settings is not None:
                try:
                    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                except Exception:
                    pass

            # Cleanup
            if handler:
                handler.stop()
            if observer:
                observer.stop()
                observer.join()
            if not no_reload:
                format_info("Dev server stopped", title="Stopped")

    except Exception as e:
        format_error(f"Fatal error: {e}", title="Error")
        import traceback

        console.print("[dim]" + traceback.format_exc() + "[/dim]")
        sys.exit(1)


__all__ = ["dev", "DevServerHandler"]
