# Schema Generation Guide

Quick reference for using the automatic JSON Schema generation system in simply-mcp-py.

## Installation

The schema generation system is included in simply-mcp-py. For Pydantic model support, install with:

```bash
pip install "simply-mcp[pydantic]"
```

## Basic Usage

### Import

```python
from simply_mcp.validation.schema import (
    auto_generate_schema,  # Auto-detect and generate
    generate_schema_from_function,  # From function
    generate_schema_from_pydantic,  # From Pydantic model
    generate_schema_from_dataclass,  # From dataclass
    generate_schema_from_typeddict,  # From TypedDict
)
```

## Quick Examples

### 1. Function with Type Hints

```python
def greet(name: str, age: int = 25) -> str:
    """Greet a person.

    Args:
        name: Person's name
        age: Person's age
    """
    return f"Hello {name}, age {age}"

schema = generate_schema_from_function(greet)
# or
schema = auto_generate_schema(greet)
```

**Output:**
```json
{
  "type": "object",
  "properties": {
    "name": {
      "type": "string",
      "description": "Person's name"
    },
    "age": {
      "type": "integer",
      "description": "Person's age",
      "default": 25
    }
  },
  "required": ["name"]
}
```

### 2. Pydantic Model

```python
from pydantic import BaseModel, Field

class User(BaseModel):
    username: str = Field(description="Unique username", min_length=3)
    email: str = Field(description="Email address", pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$")
    age: int = Field(description="User age", ge=0, le=150)
    active: bool = Field(default=True)

schema = generate_schema_from_pydantic(User)
# or
schema = auto_generate_schema(User)
```

**Output:**
```json
{
  "type": "object",
  "properties": {
    "username": {
      "type": "string",
      "description": "Unique username",
      "minLength": 3
    },
    "email": {
      "type": "string",
      "description": "Email address",
      "pattern": "^[\\w\\.-]+@[\\w\\.-]+\\.\\w+$"
    },
    "age": {
      "type": "integer",
      "description": "User age",
      "minimum": 0,
      "maximum": 150
    },
    "active": {
      "type": "boolean",
      "default": true
    }
  },
  "required": ["username", "email", "age"]
}
```

### 3. Dataclass

```python
from dataclasses import dataclass
from typing import Optional, List

@dataclass
class Config:
    host: str
    port: int
    debug: bool = False
    tags: Optional[List[str]] = None

schema = generate_schema_from_dataclass(Config)
# or
schema = auto_generate_schema(Config)
```

**Output:**
```json
{
  "type": "object",
  "properties": {
    "host": {"type": "string"},
    "port": {"type": "integer"},
    "debug": {"type": "boolean", "default": false},
    "tags": {
      "type": ["array", "null"],
      "items": {"type": "string"}
    }
  },
  "required": ["host", "port"]
}
```

### 4. TypedDict

```python
from typing import TypedDict

class RequestData(TypedDict):
    method: str
    url: str
    headers: dict
    timeout: int

schema = generate_schema_from_typeddict(RequestData)
# or
schema = auto_generate_schema(RequestData)
```

**Output:**
```json
{
  "type": "object",
  "properties": {
    "method": {"type": "string"},
    "url": {"type": "string"},
    "headers": {"type": "object"},
    "timeout": {"type": "integer"}
  },
  "required": ["method", "url", "headers", "timeout"]
}
```

## Type Mapping Reference

| Python Type | JSON Schema Type | Notes |
|------------|------------------|-------|
| `int` | `"integer"` | Whole numbers |
| `float` | `"number"` | Decimal numbers |
| `str` | `"string"` | Text |
| `bool` | `"boolean"` | True/False |
| `list`, `List[T]` | `"array"` | With items type |
| `dict`, `Dict[K,V]` | `"object"` | With additionalProperties |
| `tuple`, `Tuple[...]` | `"array"` | With specific items |
| `Optional[T]` | `["type", "null"]` | Nullable |
| `Union[T1, T2]` | `anyOf` | Multiple types |
| `Literal["a", "b"]` | `enum` | Fixed values |
| `Any` | `{}` | No constraints |

## Advanced Features

### Nested Types

```python
def process(data: List[Dict[str, int]]) -> None:
    """Process nested data."""
    pass

schema = auto_generate_schema(process)
# Generates: array of objects with integer values
```

### Optional Parameters

```python
def search(
    query: str,
    limit: Optional[int] = None,
    offset: int = 0
) -> List[str]:
    """Search with optional parameters."""
    return []

schema = auto_generate_schema(search)
# Only 'query' is required
```

### Pydantic Constraints

```python
from pydantic import BaseModel, Field

class Product(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    price: float = Field(gt=0, description="Price in USD")
    quantity: int = Field(ge=0, le=10000)
    sku: str = Field(pattern=r"^[A-Z]{3}-\d{4}$")

schema = auto_generate_schema(Product)
# All constraints preserved in schema
```

### Docstring Integration

Supports Google-style and NumPy-style docstrings:

**Google Style:**
```python
def example(param1: str, param2: int) -> None:
    """Function description.

    Args:
        param1: Description of param1
        param2: Description of param2
    """
    pass
```

**NumPy Style:**
```python
def example(param1: str, param2: int) -> None:
    """Function description.

    Parameters
    ----------
    param1 : str
        Description of param1
    param2 : int
        Description of param2
    """
    pass
```

## Integration with MCP Tools

### Basic Tool

```python
from simply_mcp.validation.schema import auto_generate_schema

def my_tool(query: str, limit: int = 10) -> dict:
    """Search tool implementation."""
    return {"results": []}

# Generate schema for tool registration
tool_schema = auto_generate_schema(my_tool)

@server.tool(input_schema=tool_schema)
def search_handler(query: str, limit: int = 10) -> dict:
    return my_tool(query, limit)
```

### Pydantic Tool

```python
from pydantic import BaseModel, Field

class SearchInput(BaseModel):
    query: str = Field(description="Search query")
    filters: dict = Field(default_factory=dict)
    limit: int = Field(default=10, ge=1, le=100)

@server.tool(input_schema=SearchInput)
def search_tool(input: SearchInput) -> dict:
    """Automatic validation and schema generation."""
    return perform_search(input.query, input.filters, input.limit)
```

## Error Handling

```python
from simply_mcp.validation.schema import SchemaGenerationError

try:
    schema = auto_generate_schema(unsupported_type)
except SchemaGenerationError as e:
    print(f"Cannot generate schema: {e}")
```

## Best Practices

1. **Use Type Hints:** Always add type hints for accurate schema generation
2. **Add Docstrings:** Include parameter descriptions in docstrings
3. **Use Pydantic for Validation:** Leverage Pydantic's validators for complex rules
4. **Default Values:** Provide sensible defaults for optional parameters
5. **Keep It Simple:** Complex nested types can be hard to understand
6. **Test Your Schemas:** Validate generated schemas with actual data

## Troubleshooting

### Schema is Empty

**Problem:** Generated schema has no properties
**Solution:** Ensure function has type hints on parameters

```python
# Bad
def func(a, b):
    return a + b

# Good
def func(a: int, b: int) -> int:
    return a + b
```

### Missing Descriptions

**Problem:** Schema properties lack descriptions
**Solution:** Add docstrings with Args section

```python
def func(x: int, y: int) -> int:
    """Add numbers.

    Args:
        x: First number
        y: Second number
    """
    return x + y
```

### Pydantic Constraints Not Applied

**Problem:** Min/max constraints not in schema
**Solution:** Use Field() with constraints

```python
from pydantic import BaseModel, Field

class Model(BaseModel):
    # Bad
    age: int

    # Good
    age: int = Field(ge=0, le=150, description="Age in years")
```

## Performance Tips

1. **Cache Schemas:** Generate once, reuse many times
2. **Use Auto-Detection:** `auto_generate_schema()` is fast and convenient
3. **Avoid Deep Nesting:** Keep type hierarchies shallow for better performance

## Examples

See `examples/schema_generation_demo.py` for complete working examples covering:
- Function schemas
- Pydantic models
- Dataclasses
- TypedDict
- Auto-detection
- Complex nested types
- Advanced Pydantic features

## API Reference

### `auto_generate_schema(source)`
Auto-detect source type and generate appropriate schema.

**Parameters:**
- `source`: Function, Pydantic model, dataclass, or TypedDict

**Returns:** JSON Schema dictionary

**Raises:** `SchemaGenerationError` if source type is unsupported

### `generate_schema_from_function(func)`
Generate schema from function with type hints.

### `generate_schema_from_pydantic(model)`
Generate schema from Pydantic BaseModel.

### `generate_schema_from_dataclass(cls)`
Generate schema from dataclass.

### `generate_schema_from_typeddict(cls)`
Generate schema from TypedDict.

## Support

For issues or questions:
- GitHub Issues: https://github.com/Clockwork-Innovations/simply-mcp-py/issues
- Documentation: https://simply-mcp-py.readthedocs.io

---

*Part of simply-mcp-py Phase 2 - Developer Experience Enhancements*
