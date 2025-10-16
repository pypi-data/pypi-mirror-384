"""Config commands for Simply-MCP CLI.

This module implements configuration management commands including
initialization, validation, and display of server configurations.
"""

import json
import sys
from pathlib import Path

import click
from rich.syntax import Syntax
from rich.table import Table

from simply_mcp.cli.utils import console, format_error, format_success
from simply_mcp.core.config import SimplyMCPConfig, load_config, validate_config


@click.group()
def config() -> None:
    """Manage Simply-MCP server configuration.

    Initialize, validate, and display server configuration files.
    Configuration can be stored in TOML or JSON format.

    Examples:

        \b
        # Create a new config template
        simply-mcp config init

        \b
        # Validate existing config
        simply-mcp config validate

        \b
        # Show current config
        simply-mcp config show
    """
    pass


@config.command()
@click.option(
    "--output",
    type=click.Path(),
    default="simplymcp.config.toml",
    help="Output file path (default: simplymcp.config.toml)",
)
@click.option(
    "--format",
    type=click.Choice(["toml", "json"], case_sensitive=False),
    default="toml",
    help="Configuration file format (default: toml)",
)
@click.option(
    "--force",
    is_flag=True,
    help="Overwrite existing file",
)
def init(output: str, format: str, force: bool) -> None:
    """Initialize a new configuration file.

    Creates a configuration template with sensible defaults that you
    can customize for your MCP server.

    Examples:

        \b
        # Create TOML config (default)
        simply-mcp config init

        \b
        # Create JSON config
        simply-mcp config init --format json --output config.json

        \b
        # Overwrite existing file
        simply-mcp config init --force
    """
    output_path = Path(output)

    # Check if file exists
    if output_path.exists() and not force:
        format_error(
            f"File already exists: {output}\n\n"
            "Use --force to overwrite.",
            "File Exists"
        )
        sys.exit(1)

    # Create default config
    from simply_mcp.core.config import get_default_config

    config_obj = get_default_config()

    try:
        if format == "toml":
            # Write TOML format
            toml_content = _generate_toml_config(config_obj)
            output_path.write_text(toml_content)
        else:
            # Write JSON format
            config_dict = config_obj.model_dump()
            json_content = json.dumps(config_dict, indent=2)
            output_path.write_text(json_content)

        format_success(f"Configuration file created: {output}")

        # Display the created file
        console.print("\n[bold]Configuration contents:[/bold]\n")
        syntax = Syntax(
            output_path.read_text(),
            format,
            theme="monokai",
            line_numbers=True
        )
        console.print(syntax)

    except Exception as e:
        format_error(f"Failed to create configuration: {e}", "Error")
        sys.exit(1)


@config.command()
@click.argument(
    "config_file",
    type=click.Path(exists=True),
    required=False,
)
def validate(config_file: str | None) -> None:
    """Validate a configuration file.

    Checks that a configuration file is valid and displays any
    validation errors found.

    Examples:

        \b
        # Validate default config
        simply-mcp config validate

        \b
        # Validate specific file
        simply-mcp config validate myconfig.toml
    """
    # Determine config file to validate
    if config_file is None:
        # Look for default config files
        default_paths = [
            "simplymcp.config.toml",
            "simplymcp.config.json",
            ".simplymcp.toml",
            ".simplymcp.json",
        ]

        config_file_path = None
        for path_str in default_paths:
            path = Path(path_str)
            if path.exists():
                config_file_path = str(path)
                break

        if config_file_path is None:
            format_error(
                "No configuration file found.\n\n"
                "Looked for: " + ", ".join(default_paths),
                "File Not Found"
            )
            sys.exit(1)

        config_file = config_file_path

    console.print(f"[dim]Validating configuration: {config_file}[/dim]")

    try:
        # Load and validate
        config_obj = load_config(config_file)
        validate_config(config_obj)

        format_success(f"Configuration is valid: {config_file}")

        # Display summary
        table = Table(title="Configuration Summary", show_header=True)
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Server Name", config_obj.server.name)
        table.add_row("Server Version", config_obj.server.version)
        table.add_row("Transport", config_obj.transport.type)
        table.add_row("Port", str(config_obj.transport.port))
        table.add_row("Log Level", config_obj.logging.level)
        table.add_row("Log Format", config_obj.logging.format)

        console.print("\n")
        console.print(table)

    except FileNotFoundError:
        format_error(f"Configuration file not found: {config_file}", "File Not Found")
        sys.exit(1)
    except Exception as e:
        format_error(f"Configuration validation failed: {e}", "Validation Error")
        sys.exit(1)


@config.command()
@click.argument(
    "config_file",
    type=click.Path(exists=True),
    required=False,
)
@click.option(
    "--format",
    type=click.Choice(["table", "json", "toml"], case_sensitive=False),
    default="table",
    help="Output format (default: table)",
)
def show(config_file: str | None, format: str) -> None:
    """Display current configuration.

    Shows the active configuration with all settings.

    Examples:

        \b
        # Show default config as table
        simply-mcp config show

        \b
        # Show specific file as JSON
        simply-mcp config show myconfig.toml --format json

        \b
        # Show as TOML
        simply-mcp config show --format toml
    """
    # Determine config file
    if config_file is None:
        # Look for default config files
        default_paths = [
            "simplymcp.config.toml",
            "simplymcp.config.json",
            ".simplymcp.toml",
            ".simplymcp.json",
        ]

        config_file_path = None
        for path_str in default_paths:
            path = Path(path_str)
            if path.exists():
                config_file_path = str(path)
                break

        if config_file_path:
            config_file = config_file_path
            console.print(f"[dim]Using configuration: {config_file}[/dim]\n")

    try:
        # Load configuration
        config_obj = load_config(config_file) if config_file else load_config()

        if format == "json":
            # Display as JSON
            config_dict = config_obj.model_dump()
            json_str = json.dumps(config_dict, indent=2)
            syntax = Syntax(json_str, "json", theme="monokai", line_numbers=True)
            console.print(syntax)

        elif format == "toml":
            # Display as TOML
            toml_str = _generate_toml_config(config_obj)
            syntax = Syntax(toml_str, "toml", theme="monokai", line_numbers=True)
            console.print(syntax)

        else:
            # Display as table (default)
            _display_config_table(config_obj)

    except Exception as e:
        format_error(f"Failed to load configuration: {e}", "Error")
        sys.exit(1)


def _generate_toml_config(config_obj: SimplyMCPConfig) -> str:
    """Generate TOML configuration string.

    Args:
        config_obj: Configuration object

    Returns:
        TOML string
    """

    return f"""# Simply-MCP Configuration File
# This file configures your MCP server settings

[server]
name = "{config_obj.server.name}"
version = "{config_obj.server.version}"
description = "{config_obj.server.description or ''}"
author = "{config_obj.server.author or ''}"
homepage = "{config_obj.server.homepage or ''}"

[transport]
type = "{config_obj.transport.type}"
host = "{config_obj.transport.host}"
port = {config_obj.transport.port}
path = "{config_obj.transport.path or ''}"

[rate_limit]
enabled = {str(config_obj.rate_limit.enabled).lower()}
requests_per_minute = {config_obj.rate_limit.requests_per_minute}
burst_size = {config_obj.rate_limit.burst_size}

[auth]
type = "{config_obj.auth.type}"
enabled = {str(config_obj.auth.enabled).lower()}
api_keys = []

[logging]
level = "{config_obj.logging.level}"
format = "{config_obj.logging.format}"
file = "{config_obj.logging.file or ''}"
enable_console = {str(config_obj.logging.enable_console).lower()}

[features]
enable_progress = {str(config_obj.features.enable_progress).lower()}
enable_binary_content = {str(config_obj.features.enable_binary_content).lower()}
max_request_size = {config_obj.features.max_request_size}
"""


def _display_config_table(config_obj: SimplyMCPConfig) -> None:
    """Display configuration as a table.

    Args:
        config_obj: Configuration object
    """
    # Server section
    table = Table(title="Server Configuration", show_header=True)
    table.add_column("Setting", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")

    table.add_row("[bold]Server[/bold]", "")
    table.add_row("  Name", config_obj.server.name)
    table.add_row("  Version", config_obj.server.version)
    if config_obj.server.description:
        table.add_row("  Description", config_obj.server.description)

    table.add_row("", "")
    table.add_row("[bold]Transport[/bold]", "")
    table.add_row("  Type", config_obj.transport.type)
    table.add_row("  Host", config_obj.transport.host)
    table.add_row("  Port", str(config_obj.transport.port))

    table.add_row("", "")
    table.add_row("[bold]Logging[/bold]", "")
    table.add_row("  Level", config_obj.logging.level)
    table.add_row("  Format", config_obj.logging.format)
    table.add_row("  Console", str(config_obj.logging.enable_console))

    table.add_row("", "")
    table.add_row("[bold]Features[/bold]", "")
    table.add_row("  Progress", str(config_obj.features.enable_progress))
    table.add_row("  Binary Content", str(config_obj.features.enable_binary_content))
    table.add_row("  Max Request Size", f"{config_obj.features.max_request_size} bytes")

    console.print(table)


__all__ = ["config", "init", "validate", "show"]
