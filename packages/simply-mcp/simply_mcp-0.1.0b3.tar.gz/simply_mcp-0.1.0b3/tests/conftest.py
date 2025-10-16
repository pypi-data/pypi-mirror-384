"""Pytest configuration and shared fixtures for Simply-MCP tests.

This module provides common test configuration and fixtures to ensure
proper test isolation, especially for global state management.
"""

import pytest


@pytest.fixture(autouse=True)
def reset_global_state():
    """Automatically reset global decorator state before each test.

    This fixture ensures that the global server singleton used by the
    decorator API is cleared before each test, preventing test pollution
    and "duplicate registration" errors when tests import modules that
    use @tool, @prompt, or @resource decorators.
    """
    # Reset global server state before test
    from simply_mcp.api.decorators import reset_global_server
    reset_global_server()

    yield

    # Reset again after test for cleanliness
    reset_global_server()
