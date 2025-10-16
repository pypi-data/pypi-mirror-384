"""Watch mode command for Simply-MCP CLI.

This module implements the 'watch' command which monitors file changes
and automatically restarts the MCP server during development.

Features:
- File system monitoring using watchdog
- Automatic server restart on file changes
- Debouncing to prevent excessive restarts
- Configurable ignore patterns
- Clear console output showing changes
- Graceful server shutdown and restart
"""

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import click
from rich.panel import Panel
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from simply_mcp.cli.utils import console, format_error, format_info, format_success

# Default ignore patterns
DEFAULT_IGNORE_PATTERNS = [
    ".git",
    ".git/*",
    "__pycache__",
    "__pycache__/*",
    "*.pyc",
    "*.pyo",
    "*.pyd",
    ".pytest_cache",
    ".pytest_cache/*",
    ".mypy_cache",
    ".mypy_cache/*",
    ".ruff_cache",
    ".ruff_cache/*",
    "*.egg-info",
    "*.egg-info/*",
    ".venv",
    ".venv/*",
    "venv",
    "venv/*",
    ".tox",
    ".tox/*",
    "build",
    "build/*",
    "dist",
    "dist/*",
    ".coverage",
    "htmlcov",
    "htmlcov/*",
    "*.swp",
    "*.swo",
    "*~",
    ".DS_Store",
]


class ServerReloadHandler(FileSystemEventHandler):
    """File system event handler that restarts the server on changes."""

    def __init__(
        self,
        server_file: str,
        debounce_delay: float,
        ignore_patterns: list[str],
        clear_console: bool,
        additional_args: list[str],
    ) -> None:
        """Initialize the reload handler.

        Args:
            server_file: Path to the server file to run
            debounce_delay: Delay in seconds before restarting after a change
            ignore_patterns: List of patterns to ignore
            clear_console: Whether to clear console on reload
            additional_args: Additional arguments to pass to the server
        """
        super().__init__()
        self.server_file = Path(server_file).resolve()
        self.debounce_delay = debounce_delay
        self.ignore_patterns = ignore_patterns
        self.clear_console = clear_console
        self.additional_args = additional_args
        self.last_reload = 0.0
        self.process: subprocess.Popen[bytes] | None = None
        self.should_stop = False

        # Start the server initially
        self._start_server()

    def _should_ignore(self, path: str) -> bool:
        """Check if a path should be ignored.

        Args:
            path: File path to check

        Returns:
            True if path should be ignored, False otherwise
        """
        path_obj = Path(path)

        # Check if path matches any ignore pattern
        for pattern in self.ignore_patterns:
            # Handle directory patterns
            if pattern.endswith("/*"):
                pattern_dir = pattern[:-2]
                if pattern_dir in path_obj.parts:
                    return True
            # Handle exact matches
            elif pattern in path_obj.parts:
                return True
            # Handle glob patterns
            elif path_obj.match(pattern):
                return True

        return False

    def _start_server(self) -> None:
        """Start the server process."""
        try:
            # Build command to run the server
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
            )

            format_success(
                f"Server started (PID: {self.process.pid})",
                title="Started",
            )

        except Exception as e:
            format_error(f"Failed to start server: {e}", title="Start Error")

    def _stop_server(self) -> None:
        """Stop the server process gracefully."""
        if self.process is None:
            return

        try:
            # Try graceful shutdown first
            if self.process.poll() is None:  # Process is still running
                console.print("[yellow]Stopping server...[/yellow]")

                # Send SIGTERM for graceful shutdown
                self.process.send_signal(signal.SIGTERM)

                # Wait up to 5 seconds for graceful shutdown
                try:
                    self.process.wait(timeout=5.0)
                except subprocess.TimeoutExpired:
                    # Force kill if graceful shutdown fails
                    console.print("[yellow]Forcing server shutdown...[/yellow]")
                    self.process.kill()
                    self.process.wait()

                format_info("Server stopped", title="Stopped")

        except Exception as e:
            format_error(f"Error stopping server: {e}", title="Stop Error")
        finally:
            self.process = None

    def _reload_server(self, changed_file: str) -> None:
        """Reload the server by stopping and starting it.

        Args:
            changed_file: Path to the file that changed
        """
        current_time = time.time()

        # Check if we're within debounce period
        if current_time - self.last_reload < self.debounce_delay:
            return

        self.last_reload = current_time

        # Clear console if requested
        if self.clear_console:
            os.system("cls" if os.name == "nt" else "clear")

        # Display reload message
        timestamp = time.strftime("%H:%M:%S")
        console.print(
            Panel(
                f"[bold cyan]File changed:[/bold cyan] [yellow]{changed_file}[/yellow]\n"
                f"[dim]Time: {timestamp}[/dim]",
                title="[bold blue]Reloading Server[/bold blue]",
            )
        )

        # Stop and restart server
        self._stop_server()
        if not self.should_stop:
            self._start_server()

    def on_modified(self, event: FileSystemEvent) -> None:
        """Handle file modification events.

        Args:
            event: File system event
        """
        if event.is_directory:
            return

        # Get the source path as a string
        src_path = str(event.src_path)

        # Check if file should be ignored
        if self._should_ignore(src_path):
            return

        # Only reload for Python files
        if not src_path.endswith(".py"):
            return

        self._reload_server(src_path)

    def on_created(self, event: FileSystemEvent) -> None:
        """Handle file creation events.

        Args:
            event: File system event
        """
        if event.is_directory:
            return

        # Get the source path as a string
        src_path = str(event.src_path)

        # Check if file should be ignored
        if self._should_ignore(src_path):
            return

        # Only reload for Python files
        if not src_path.endswith(".py"):
            return

        self._reload_server(src_path)

    def on_deleted(self, event: FileSystemEvent) -> None:
        """Handle file deletion events.

        Args:
            event: File system event
        """
        if event.is_directory:
            return

        # Get the source path as a string
        src_path = str(event.src_path)

        # Check if file should be ignored
        if self._should_ignore(src_path):
            return

        # Only reload for Python files
        if not src_path.endswith(".py"):
            return

        self._reload_server(src_path)

    def stop(self) -> None:
        """Stop the handler and server."""
        self.should_stop = True
        self._stop_server()


@click.command()
@click.argument("server_file", type=click.Path(exists=True))
@click.option(
    "--ignore",
    "-i",
    multiple=True,
    help="Additional ignore patterns (can be specified multiple times)",
)
@click.option(
    "--debounce",
    type=float,
    default=1.0,
    help="Debounce delay in seconds (default: 1.0)",
)
@click.option(
    "--clear/--no-clear",
    default=True,
    help="Clear console on reload (default: enabled)",
)
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
def watch(
    server_file: str,
    ignore: tuple[str, ...],
    debounce: float,
    clear: bool,
    transport: str,
    port: int,
    host: str,
    cors: bool,
) -> None:
    """Watch for file changes and auto-reload the MCP server.

    This command monitors Python files in the current directory and
    automatically restarts the server when changes are detected.
    Perfect for development workflows.

    The watch mode includes:
    - Automatic detection of Python file changes
    - Debouncing to prevent excessive restarts
    - Graceful server shutdown and restart
    - Configurable ignore patterns
    - Clear console output

    Examples:

        \b
        # Watch with default settings
        simply-mcp watch server.py

        \b
        # Watch with custom debounce delay
        simply-mcp watch server.py --debounce 2.0

        \b
        # Watch with additional ignore patterns
        simply-mcp watch server.py --ignore "tests/*" --ignore "docs/*"

        \b
        # Watch without clearing console
        simply-mcp watch server.py --no-clear

        \b
        # Watch with HTTP transport
        simply-mcp watch server.py --transport http --port 8080

        \b
        # Watch with SSE transport and custom host
        simply-mcp watch server.py --transport sse --host localhost --port 8080
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

        # Build ignore patterns
        ignore_patterns = list(DEFAULT_IGNORE_PATTERNS)
        ignore_patterns.extend(ignore)

        # Build additional arguments for the server
        additional_args = ["--transport", transport]
        if transport in ["http", "sse"]:
            additional_args.extend(["--host", host])
            additional_args.extend(["--port", str(port)])
            if cors:
                additional_args.append("--cors")
            else:
                additional_args.append("--no-cors")

        # Display watch mode info
        watch_info = (
            f"[bold cyan]Starting Watch Mode[/bold cyan]\n\n"
            f"File: [green]{server_file}[/green]\n"
            f"Directory: [yellow]{Path.cwd()}[/yellow]\n"
            f"Debounce: [yellow]{debounce}s[/yellow]\n"
            f"Transport: [yellow]{transport}[/yellow]"
        )

        if transport in ["http", "sse"]:
            watch_info += f"\nHost: [yellow]{host}[/yellow]"
            watch_info += f"\nPort: [yellow]{port}[/yellow]"

        watch_info += "\n\n[dim]Watching for Python file changes...[/dim]"
        watch_info += "\n[dim]Press Ctrl+C to stop[/dim]"

        console.print(
            Panel(
                watch_info,
                title="[bold blue]Simply-MCP Watch Mode[/bold blue]",
            )
        )

        # Create event handler
        handler = ServerReloadHandler(
            server_file=str(server_path),
            debounce_delay=debounce,
            ignore_patterns=ignore_patterns,
            clear_console=clear,
            additional_args=additional_args,
        )

        # Create and start observer
        observer = Observer()
        observer.schedule(handler, str(Path.cwd()), recursive=True)
        observer.start()

        try:
            # Keep the main thread alive
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            console.print("\n[yellow]Received interrupt signal, shutting down...[/yellow]")
            handler.stop()
            observer.stop()
            observer.join()
            format_info("Watch mode stopped", title="Stopped")

    except Exception as e:
        format_error(f"Fatal error: {e}", title="Error")
        import traceback

        console.print("[dim]" + traceback.format_exc() + "[/dim]")
        sys.exit(1)


__all__ = ["watch", "ServerReloadHandler"]
