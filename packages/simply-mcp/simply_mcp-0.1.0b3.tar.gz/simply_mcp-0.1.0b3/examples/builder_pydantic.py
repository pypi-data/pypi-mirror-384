#!/usr/bin/env python3
"""Builder API with Pydantic Integration Example.

This example demonstrates using Pydantic models for input validation
with the builder API.
"""

import asyncio
from typing import List, Optional
from pydantic import BaseModel, Field
from simply_mcp import BuildMCPServer


# Define Pydantic models for input validation
class SearchQuery(BaseModel):
    """Search query with validation."""
    query: str = Field(description="Search query string", min_length=1, max_length=100)
    limit: int = Field(default=10, ge=1, le=100, description="Maximum number of results")
    filter_type: Optional[str] = Field(default=None, description="Optional filter type")


class UserInput(BaseModel):
    """User creation input."""
    name: str = Field(description="User's full name", min_length=1)
    email: str = Field(description="User's email address")
    age: int = Field(ge=0, le=150, description="User's age")
    interests: List[str] = Field(default_factory=list, description="List of interests")


# Create server
mcp = BuildMCPServer(
    name="validated-server",
    version="1.0.0",
    description="Server with Pydantic validation"
)


# Register tool with Pydantic model
@mcp.tool(input_schema=SearchQuery)
def search(input: SearchQuery) -> dict:
    """Search with validated input.

    Args:
        input: Search query parameters

    Returns:
        Search results
    """
    results = [f"Result {i} for '{input.query}'" for i in range(1, input.limit + 1)]

    return {
        "query": input.query,
        "limit": input.limit,
        "filter": input.filter_type,
        "results": results,
        "total": len(results)
    }


@mcp.tool(input_schema=UserInput)
def create_user(input: UserInput) -> dict:
    """Create a user with validation.

    Args:
        input: User creation parameters

    Returns:
        Created user data
    """
    return {
        "id": "user_123",
        "name": input.name,
        "email": input.email,
        "age": input.age,
        "interests": input.interests,
        "status": "active"
    }


# Also works with direct registration
def update_user(user_id: str, name: Optional[str] = None, age: Optional[int] = None) -> dict:
    """Update user information.

    Args:
        user_id: User ID to update
        name: New name (optional)
        age: New age (optional)

    Returns:
        Updated user data
    """
    updates = {}
    if name:
        updates["name"] = name
    if age is not None:
        updates["age"] = age

    return {
        "id": user_id,
        "updates": updates,
        "status": "updated"
    }


mcp.add_tool("update_user", update_user, description="Update user information")


async def main():
    """Run the validated server."""
    print("Starting Validated MCP Server...")
    print(f"Tools: {mcp.list_tools()}")
    print("\nTools with Pydantic validation:")
    print("  - search: Uses SearchQuery model")
    print("  - create_user: Uses UserInput model")
    print("  - update_user: Uses auto-generated schema")

    # Initialize and run
    await mcp.initialize()
    await mcp.run_stdio()


if __name__ == "__main__":
    asyncio.run(main())
