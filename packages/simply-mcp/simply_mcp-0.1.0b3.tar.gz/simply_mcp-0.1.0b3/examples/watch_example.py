"""Example server for testing watch mode and development mode.

This is a simple MCP server that demonstrates the watch mode and dev mode functionality.
You can modify this file while the server is running to see automatic reloading in action.

Usage:
    # Start in development mode (recommended for development)
    simply-mcp dev examples/watch_example.py

    # Dev mode features:
    # - Auto-reload on file changes
    # - DEBUG level logging
    # - Component listing on startup
    # - Performance metrics
    # - Keyboard shortcuts (r=reload, l=list, m=metrics, q=quit)

    # Or use basic watch mode
    simply-mcp watch examples/watch_example.py

    # With custom options
    simply-mcp dev examples/watch_example.py --transport http --port 8080
    simply-mcp watch examples/watch_example.py --debounce 2.0 --clear

    # Disable auto-reload in dev mode
    simply-mcp dev examples/watch_example.py --no-reload

Try making changes to this file while it's running:
1. Add new tools or prompts
2. Modify existing tool implementations
3. Change descriptions or return values
4. The server will automatically reload!

Note: Make sure you have the simply-mcp package installed:
    pip install -e .
"""

from simply_mcp import prompt, resource, tool


# Tool examples
@tool()
def greet(name: str = "World") -> str:
    """Greet someone by name.

    Args:
        name: The name to greet (default: "World")

    Returns:
        A greeting message
    """
    return f"Hello, {name}! 👋"


@tool()
def add_numbers(a: int, b: int) -> int:
    """Add two numbers together.

    Args:
        a: First number
        b: Second number

    Returns:
        The sum of a and b
    """
    return a + b


@tool()
def get_current_time() -> str:
    """Get the current time.

    Returns:
        The current time as a formatted string
    """
    from datetime import datetime

    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# Prompt examples
@prompt()
def code_review_prompt(code: str, language: str = "python") -> str:
    """Generate a code review prompt.

    Args:
        code: The code to review
        language: Programming language (default: "python")

    Returns:
        A formatted code review prompt
    """
    return f"""Please review the following {language} code:

```{language}
{code}
```

Focus on:
1. Code quality and best practices
2. Potential bugs or issues
3. Performance considerations
4. Security concerns
5. Suggestions for improvement
"""


@prompt()
def explain_concept(concept: str, level: str = "beginner") -> str:
    """Generate a prompt to explain a concept.

    Args:
        concept: The concept to explain
        level: Difficulty level (beginner, intermediate, advanced)

    Returns:
        A formatted explanation prompt
    """
    return f"""Please explain the concept of '{concept}' at a {level} level.

Include:
1. A clear, concise definition
2. Real-world examples
3. Common use cases
4. Key points to remember
"""


# Resource examples
@resource(uri="config://settings")
def get_config() -> dict[str, str | dict[str, bool]]:
    """Get application configuration.

    Returns:
        Configuration dictionary
    """
    return {
        "app_name": "Watch Mode Demo",
        "version": "1.0.0",
        "environment": "development",
        "features": {
            "auto_reload": True,
            "hot_reload": True,
            "debug_mode": True,
        },
    }


@resource(uri="info://stats")
def get_stats() -> dict[str, str | int]:
    """Get server statistics.

    Returns:
        Statistics dictionary
    """
    return {
        "uptime": "00:00:00",  # Would be calculated in real implementation
        "requests_handled": 0,
        "tools_count": 3,
        "prompts_count": 2,
        "resources_count": 2,
    }


# Try modifying the code above while in watch mode!
# For example:
# - Change the greeting message in greet()
# - Add a new tool like multiply_numbers()
# - Modify a prompt template
# - Add more configuration options

if __name__ == "__main__":
    print("This server is meant to be run with: simply-mcp dev examples/watch_example.py")
    print("Or alternatively with: simply-mcp watch examples/watch_example.py")
    print("See the docstring at the top of this file for usage instructions.")
