"""Example demonstrating schema generation from various sources.

This example shows how to use the schema generation system with:
- Regular Python functions with type hints
- Pydantic models
- Dataclasses
- TypedDict
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, TypedDict

from pydantic import BaseModel, Field

from simply_mcp.validation.schema import (
    auto_generate_schema,
    generate_schema_from_dataclass,
    generate_schema_from_function,
    generate_schema_from_pydantic,
    generate_schema_from_typeddict,
)


def example_function_schema() -> None:
    """Example 1: Generate schema from function with type hints."""
    print("\n=== Example 1: Function with Type Hints ===\n")

    def search_files(
        query: str,
        path: str = "/",
        max_results: int = 100,
        include_hidden: bool = False
    ) -> List[str]:
        """Search for files matching a query.

        Args:
            query: Search query string
            path: Directory path to search in
            max_results: Maximum number of results to return
            include_hidden: Whether to include hidden files
        """
        return []

    schema = generate_schema_from_function(search_files)
    print(f"Function: {search_files.__name__}")
    print(f"Schema: {schema}")
    print(f"Required fields: {schema.get('required', [])}")


def example_pydantic_schema() -> None:
    """Example 2: Generate schema from Pydantic model."""
    print("\n=== Example 2: Pydantic Model ===\n")

    class SearchRequest(BaseModel):
        """Search request with validation."""
        query: str = Field(description="Search query", min_length=1, max_length=500)
        filters: Optional[Dict[str, str]] = Field(
            default=None,
            description="Optional filters"
        )
        limit: int = Field(default=10, ge=1, le=1000, description="Result limit")
        offset: int = Field(default=0, ge=0, description="Result offset")

    schema = generate_schema_from_pydantic(SearchRequest)
    print(f"Pydantic Model: {SearchRequest.__name__}")
    print(f"Schema: {schema}")
    print(f"Query constraints: {schema['properties']['query']}")


def example_dataclass_schema() -> None:
    """Example 3: Generate schema from dataclass."""
    print("\n=== Example 3: Dataclass ===\n")

    @dataclass
    class Configuration:
        """Application configuration."""
        host: str
        port: int
        debug: bool = False
        max_connections: int = 100
        allowed_origins: Optional[List[str]] = None

    schema = generate_schema_from_dataclass(Configuration)
    print(f"Dataclass: {Configuration.__name__}")
    print(f"Schema: {schema}")
    print(f"Required fields: {schema.get('required', [])}")


def example_typeddict_schema() -> None:
    """Example 4: Generate schema from TypedDict."""
    print("\n=== Example 4: TypedDict ===\n")

    class UserData(TypedDict):
        """User data structure."""
        username: str
        email: str
        age: int
        is_active: bool

    schema = generate_schema_from_typeddict(UserData)
    print(f"TypedDict: {UserData.__name__}")
    print(f"Schema: {schema}")
    print(f"Properties: {list(schema['properties'].keys())}")


def example_auto_detect() -> None:
    """Example 5: Auto-detect source type and generate schema."""
    print("\n=== Example 5: Auto-Detection ===\n")

    # Define various sources
    def add(a: int, b: int) -> int:
        """Add two numbers."""
        return a + b

    class Point(BaseModel):
        """2D point."""
        x: float
        y: float

    @dataclass
    class Color:
        """RGB color."""
        r: int
        g: int
        b: int

    sources = [
        ("Function", add),
        ("Pydantic", Point),
        ("Dataclass", Color),
    ]

    for name, source in sources:
        schema = auto_generate_schema(source)
        print(f"{name}: {source.__name__ if hasattr(source, '__name__') else source}")
        print(f"  Type: {schema.get('type', 'N/A')}")
        print(f"  Properties: {list(schema.get('properties', {}).keys())}")
        print()


def example_complex_types() -> None:
    """Example 6: Complex nested types."""
    print("\n=== Example 6: Complex Nested Types ===\n")

    def process_data(
        items: List[Dict[str, str]],
        metadata: Optional[Dict[str, List[int]]] = None,
        options: Optional[Dict[str, bool]] = None
    ) -> Dict[str, List[str]]:
        """Process data with complex nested types.

        Args:
            items: List of item dictionaries
            metadata: Optional metadata with integer lists
            options: Optional boolean options
        """
        return {}

    schema = generate_schema_from_function(process_data)
    print(f"Function: {process_data.__name__}")
    print(f"Schema properties:")
    for prop_name, prop_schema in schema['properties'].items():
        print(f"  {prop_name}: {prop_schema}")


def example_pydantic_advanced() -> None:
    """Example 7: Advanced Pydantic features."""
    print("\n=== Example 7: Advanced Pydantic ===\n")

    class DatabaseConfig(BaseModel):
        """Database configuration with advanced validation."""
        host: str = Field(description="Database host", min_length=1)
        port: int = Field(default=5432, ge=1, le=65535, description="Database port")
        database: str = Field(description="Database name", pattern=r"^[a-zA-Z0-9_]+$")
        username: str = Field(description="Database username")
        password: str = Field(description="Database password", min_length=8)
        max_connections: int = Field(default=10, ge=1, le=100)
        ssl_enabled: bool = Field(default=True, description="Enable SSL connection")
        connect_timeout: float = Field(default=30.0, gt=0, description="Connection timeout in seconds")

    schema = generate_schema_from_pydantic(DatabaseConfig)
    print(f"Pydantic Model: {DatabaseConfig.__name__}")
    print(f"\nProperties with constraints:")
    for prop_name, prop_schema in schema['properties'].items():
        constraints = {
            k: v for k, v in prop_schema.items()
            if k in ('minimum', 'maximum', 'minLength', 'maxLength', 'pattern', 'default')
        }
        if constraints:
            print(f"  {prop_name}: {constraints}")


if __name__ == "__main__":
    print("=" * 70)
    print("Schema Generation Examples")
    print("=" * 70)

    example_function_schema()
    example_pydantic_schema()
    example_dataclass_schema()
    example_typeddict_schema()
    example_auto_detect()
    example_complex_types()
    example_pydantic_advanced()

    print("\n" + "=" * 70)
    print("All examples completed successfully!")
    print("=" * 70)
