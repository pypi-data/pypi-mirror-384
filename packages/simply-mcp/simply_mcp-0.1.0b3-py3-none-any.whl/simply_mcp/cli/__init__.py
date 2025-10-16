"""Simply-MCP CLI module.

This module provides the command-line interface for Simply-MCP,
enabling users to run, configure, and inspect MCP servers from
the command line.

Commands:
    run: Run an MCP server from a Python file
    config: Manage server configuration (init, validate, show)
    list: List server components (tools, prompts, resources)
"""

from simply_mcp.cli.main import cli

__all__ = ["cli"]
