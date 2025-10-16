"""Main CLI entry point for Simply-MCP.

This module provides the main command-line interface for Simply-MCP,
enabling users to run, configure, and inspect MCP servers.

Commands:
    run: Run an MCP server from a Python file
    config: Manage server configuration
    list: List server components (tools, prompts, resources)
"""

import click

from simply_mcp import __version__


@click.group()
@click.version_option(version=__version__, prog_name="simply-mcp")
def cli() -> None:
    """Simply-MCP: Easy MCP server development for Python.

    Build and run MCP servers with minimal boilerplate using
    decorators, builders, or class-based APIs.

    Examples:

        \b
        # Run a server in dev mode
        simply-mcp dev server.py

        \b
        # Run a server
        simply-mcp run server.py

        \b
        # List components
        simply-mcp list server.py

        \b
        # Initialize config
        simply-mcp config init
    """
    pass


# Import and register commands
# Lazy imports to improve startup time
def _register_commands() -> None:
    """Register CLI commands."""
    from simply_mcp.cli import bundle, dev, list_cmd, run, watch
    from simply_mcp.cli import config as config_module

    cli.add_command(dev.dev)
    cli.add_command(run.run)
    cli.add_command(config_module.config)
    cli.add_command(list_cmd.list_components)
    cli.add_command(watch.watch)
    cli.add_command(bundle.bundle)


_register_commands()


__all__ = ["cli"]
