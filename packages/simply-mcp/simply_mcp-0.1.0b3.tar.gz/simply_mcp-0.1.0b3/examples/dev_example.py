"""Example demonstrating development mode features.

This example showcases the enhanced development experience provided by
the 'dev' command in Simply-MCP.

Development Mode Features:
--------------------------
1. Auto-reload: Automatically restarts server when files change
2. Debug Logging: Shows detailed DEBUG level logs
3. Component Listing: Displays all registered tools/prompts/resources on startup
4. Performance Metrics: Tracks request counts, errors, and uptime
5. Interactive Keyboard Shortcuts:
   - r: Manually reload the server
   - l: List all registered components
   - m: Show performance metrics
   - q: Quit the dev server
6. Pretty Console Output: Color-coded, formatted output with Rich

Usage:
------
    # Start in development mode
    simply-mcp dev examples/dev_example.py

    # With HTTP transport for testing with clients
    simply-mcp dev examples/dev_example.py --transport http --port 8080

    # Disable auto-reload if needed
    simply-mcp dev examples/dev_example.py --no-reload

    # Disable request logging for cleaner output
    simply-mcp dev examples/dev_example.py --no-log-requests

    # With SSE transport
    simply-mcp dev examples/dev_example.py --transport sse --port 8080

Development Workflow:
---------------------
1. Start the dev server with: simply-mcp dev examples/dev_example.py
2. The server will display all registered components
3. Make changes to this file (add tools, modify functions, etc.)
4. The server automatically reloads with your changes
5. Use keyboard shortcuts to interact with the server:
   - Press 'l' to list components at any time
   - Press 'm' to see performance metrics
   - Press 'r' to force a reload
   - Press 'q' to quit

Try These Development Tasks:
----------------------------
While the dev server is running:
1. Add a new tool function below
2. Modify the greeting message in greet_user()
3. Change a tool's description
4. Add new parameters to existing tools
5. Create a new prompt or resource
6. Watch the server automatically reload!

Note: Dev mode is perfect for rapid development and debugging.
For production, use: simply-mcp run examples/dev_example.py
"""

from simply_mcp import prompt, resource, tool


# Example Tools
@tool()
def greet_user(name: str, enthusiastic: bool = False) -> str:
    """Greet a user with a friendly message.

    Args:
        name: The user's name
        enthusiastic: Whether to be extra enthusiastic

    Returns:
        A greeting message
    """
    greeting = f"Hello, {name}!"
    if enthusiastic:
        greeting += " Great to see you! 🎉"
    return greeting


@tool()
def calculate(operation: str, a: float, b: float) -> float:
    """Perform a mathematical operation.

    Args:
        operation: The operation to perform (add, subtract, multiply, divide)
        a: First number
        b: Second number

    Returns:
        The result of the calculation

    Raises:
        ValueError: If operation is not supported or division by zero
    """
    operations = {
        "add": lambda x, y: x + y,
        "subtract": lambda x, y: x - y,
        "multiply": lambda x, y: x * y,
        "divide": lambda x, y: x / y if y != 0 else None,
    }

    if operation not in operations:
        raise ValueError(f"Unsupported operation: {operation}")

    result = operations[operation](a, b)
    if result is None:
        raise ValueError("Cannot divide by zero")

    return result


@tool()
def get_system_info() -> dict[str, str]:
    """Get information about the development environment.

    Returns:
        Dictionary with system information
    """
    import platform
    import sys

    return {
        "python_version": sys.version,
        "platform": platform.platform(),
        "architecture": platform.machine(),
        "processor": platform.processor(),
    }


@tool()
def debug_echo(message: str, metadata: dict[str, str] | None = None) -> dict[str, str | dict[str, str]]:
    """Echo a message with optional metadata (useful for debugging).

    Args:
        message: The message to echo
        metadata: Optional metadata dictionary

    Returns:
        Dictionary with echoed message and metadata
    """
    result: dict[str, str | dict[str, str]] = {"echoed_message": message}
    if metadata:
        result["metadata"] = metadata
    return result


# Example Prompts
@prompt()
def debug_prompt(code: str, issue: str) -> str:
    """Generate a debugging prompt for code.

    Args:
        code: The code to debug
        issue: Description of the issue

    Returns:
        A formatted debugging prompt
    """
    return f"""Debug the following code:

Issue: {issue}

Code:
```
{code}
```

Please:
1. Identify the root cause of the issue
2. Explain why the problem occurs
3. Provide a corrected version
4. Suggest how to prevent similar issues
"""


@prompt()
def test_generation_prompt(function_signature: str, description: str) -> str:
    """Generate a prompt for test generation.

    Args:
        function_signature: The function signature to test
        description: Description of what the function does

    Returns:
        A formatted test generation prompt
    """
    return f"""Generate comprehensive unit tests for this function:

Function: {function_signature}
Description: {description}

Please provide:
1. Test cases for normal inputs
2. Test cases for edge cases
3. Test cases for error conditions
4. Mock/patch suggestions if needed
"""


# Example Resources
@resource(uri="dev://config")
def dev_config() -> dict[str, str | bool | dict[str, bool]]:
    """Get development configuration.

    Returns:
        Development configuration dictionary
    """
    return {
        "mode": "development",
        "debug": True,
        "auto_reload": True,
        "log_level": "DEBUG",
        "features": {
            "hot_reload": True,
            "debug_toolbar": True,
            "profiling": True,
        },
    }


@resource(uri="dev://environment")
def dev_environment() -> dict[str, str | list[str]]:
    """Get development environment information.

    Returns:
        Environment information dictionary
    """
    return {
        "server_type": "MCP Development Server",
        "api_version": "1.0.0",
        "supported_transports": ["stdio", "http", "sse"],
        "features": [
            "Auto-reload",
            "Debug logging",
            "Performance metrics",
            "Interactive shortcuts",
        ],
    }


@resource(uri="dev://tips")
def dev_tips() -> dict[str, list[str]]:
    """Get development tips and best practices.

    Returns:
        Development tips dictionary
    """
    return {
        "shortcuts": [
            "Press 'r' to manually reload the server",
            "Press 'l' to list all components",
            "Press 'm' to show performance metrics",
            "Press 'q' to quit the server",
        ],
        "best_practices": [
            "Use type hints for better schema generation",
            "Add descriptive docstrings to all tools/prompts",
            "Test with different transports (stdio, http, sse)",
            "Monitor metrics to identify performance issues",
            "Use --no-reload when debugging startup issues",
        ],
        "debugging": [
            "Check DEBUG logs for detailed request/response info",
            "Use debug_echo tool to test data flow",
            "Monitor metrics to track request counts and errors",
            "Test error handling by triggering exceptions",
        ],
    }


# Development Notes
"""
Tips for Using Dev Mode:
------------------------
1. The dev server shows all components on startup - verify your tools are registered
2. Use keyboard shortcuts to interact without stopping the server
3. Metrics help identify which tools are being used most
4. Auto-reload saves time - no need to manually restart
5. DEBUG logging shows full request/response details
6. Test with HTTP/SSE transports to simulate real client interactions

Common Development Patterns:
---------------------------
- Start with 'simply-mcp dev' for rapid iteration
- Use 'simply-mcp list' to verify components without starting server
- Test with 'simply-mcp run' to simulate production environment
- Use 'simply-mcp watch' for basic auto-reload without extra features

Try adding your own tools below and watch them appear automatically!
"""

if __name__ == "__main__":
    print(__doc__)
    print("\nTo run this example:")
    print("  simply-mcp dev examples/dev_example.py")
