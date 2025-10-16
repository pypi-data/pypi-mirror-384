# Pydantic Migration Guide

## Overview

Simply-MCP has upgraded from TypedDict-based type definitions to Pydantic BaseModel classes for improved runtime validation, better IDE support, and enhanced developer experience. This guide explains the changes and how to migrate your code.

## What Changed?

All configuration types in `simply_mcp.core.types` now have both:

1. **Pydantic BaseModel classes** (recommended) - with `Model` suffix
2. **TypedDict classes** (deprecated) - for backward compatibility

### Type Mapping

| Old (TypedDict) | New (Pydantic BaseModel) | Status |
|----------------|--------------------------|---------|
| `ToolConfig` | `ToolConfigModel` | Deprecated → Recommended |
| `PromptConfig` | `PromptConfigModel` | Deprecated → Recommended |
| `ResourceConfig` | `ResourceConfigModel` | Deprecated → Recommended |
| `ServerMetadata` | `ServerMetadataModel` | Deprecated → Recommended |
| `TransportConfig` | `TransportConfigModel` | Deprecated → Recommended |
| `ProgressUpdate` | `ProgressUpdateModel` | Deprecated → Recommended |
| `RequestContext` | `RequestContextModel` | Deprecated → Recommended |
| `APIStyleInfo` | `APIStyleInfoModel` | Deprecated → Recommended |
| `ValidationError` | `ValidationErrorModel` | Deprecated → Recommended |
| `ValidationResult` | `ValidationResultModel` | Deprecated → Recommended |
| `RateLimitConfig` | `RateLimitConfigModel` | Deprecated → Recommended |
| `AuthConfig` | `AuthConfigModel` | Deprecated → Recommended |
| `LogConfig` | `LogConfigModel` | Deprecated → Recommended |
| `FeatureFlags` | `FeatureFlagsModel` | Deprecated → Recommended |
| `ServerConfig` | `ServerConfigModel` | Deprecated → Recommended |

## Benefits of Pydantic Models

### 1. Runtime Validation

**Before (TypedDict):**
```python
# No validation - errors only caught at runtime
tool_config: ToolConfig = {
    "name": "",  # Empty string - invalid but not caught
    "description": "My tool",
    "input_schema": {},
    "handler": my_handler
}
```

**After (Pydantic):**
```python
# Automatic validation on creation
tool_config = ToolConfigModel(
    name="",  # ValidationError: String should have at least 1 character
    description="My tool",
    input_schema={},
    handler=my_handler
)
```

### 2. Better IDE Support

Pydantic models provide:
- Better autocomplete
- Type inference
- Field documentation in hover tooltips
- Validation error hints

### 3. Default Values

**Before (TypedDict with NotRequired):**
```python
config: ToolConfig = {
    "name": "my_tool",
    "description": "My tool",
    "input_schema": {},
    "handler": my_handler,
    # metadata is optional but no default provided
}
```

**After (Pydantic with defaults):**
```python
config = ToolConfigModel(
    name="my_tool",
    description="My tool",
    input_schema={},
    handler=my_handler
    # metadata automatically defaults to {}
)
```

### 4. Serialization/Deserialization

Pydantic provides built-in serialization:
```python
# Convert to dict
config_dict = tool_config.model_dump()

# Convert to JSON
config_json = tool_config.model_dump_json()

# Load from dict
config = ToolConfigModel.model_validate(config_dict)

# Load from JSON
config = ToolConfigModel.model_validate_json(config_json)
```

## Migration Steps

### Step 1: Update Imports

**Before:**
```python
from simply_mcp.core.types import (
    ToolConfig,
    PromptConfig,
    ResourceConfig,
)
```

**After:**
```python
from simply_mcp.core.types import (
    ToolConfigModel,
    PromptConfigModel,
    ResourceConfigModel,
)
```

### Step 2: Update Type Annotations

**Before:**
```python
def register_tool(config: ToolConfig) -> None:
    ...
```

**After:**
```python
def register_tool(config: ToolConfigModel) -> None:
    ...
```

### Step 3: Update Config Creation

**Before (dict-based):**
```python
config: ToolConfig = {
    "name": "calculate",
    "description": "Perform calculation",
    "input_schema": {"type": "object"},
    "handler": calculate_handler,
}
```

**After (Pydantic-based):**
```python
config = ToolConfigModel(
    name="calculate",
    description="Perform calculation",
    input_schema={"type": "object"},
    handler=calculate_handler,
)
```

### Step 4: Update Field Access

**Before (dict access):**
```python
tool_name = config["name"]
description = config.get("description", "")
```

**After (attribute access):**
```python
tool_name = config.name
description = config.description  # Always present (no need for .get())
```

## Backward Compatibility

### TypedDict Still Works

All existing code using TypedDict will continue to work:

```python
# This still works!
config: ToolConfig = {
    "name": "my_tool",
    "description": "My tool",
    "input_schema": {},
    "handler": my_handler,
}

server.register_tool(config)  # Accepts both dict and Pydantic model
```

### Internal Conversion

The framework automatically handles conversion between dict and Pydantic models:

```python
# Server methods accept both
server.register_tool(dict_config)       # TypedDict
server.register_tool(pydantic_config)   # Pydantic model

# Registry accepts both
registry.register_tool(dict_config)     # TypedDict
registry.register_tool(pydantic_config) # Pydantic model
```

### Mixed Usage

You can mix both approaches during migration:

```python
# Some configs as dicts
tool_config = {
    "name": "tool1",
    "description": "Tool 1",
    "input_schema": {},
    "handler": handler1,
}

# Some configs as Pydantic models
prompt_config = PromptConfigModel(
    name="prompt1",
    description="Prompt 1",
    template="Hello {name}!"
)

# Both work together
server.register_tool(tool_config)
server.register_prompt(prompt_config)
```

## Advanced Features

### Field Validation

Pydantic models include validation:

```python
# Port validation
transport = TransportConfigModel(
    type="http",
    host="0.0.0.0",
    port=70000  # ValidationError: Input should be less than or equal to 65535
)

# String length validation
tool = ToolConfigModel(
    name="",  # ValidationError: String should have at least 1 character
    description="Tool",
    input_schema={},
    handler=my_handler
)

# Progress percentage validation
progress = ProgressUpdateModel(
    percentage=150.0  # ValidationError: Input should be less than or equal to 100
)
```

### Custom Validators

You can extend Pydantic models with custom validation:

```python
from pydantic import field_validator

class CustomToolConfig(ToolConfigModel):
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v.startswith('tool_'):
            raise ValueError('Tool name must start with "tool_"')
        return v
```

### Model Configuration

Pydantic models support extra configuration:

```python
# Forbid extra fields (strict mode)
class StrictConfig(ServerMetadataModel):
    model_config = ConfigDict(extra="forbid")

# Allow extra fields
class FlexibleConfig(ServerMetadataModel):
    model_config = ConfigDict(extra="allow")
```

## Common Patterns

### Pattern 1: Builder Pattern

**Before:**
```python
config: ToolConfig = {
    "name": "calculate",
    "description": "Calculate",
    "input_schema": generate_schema(calculate),
    "handler": calculate,
}
server.register_tool(config)
```

**After:**
```python
config = ToolConfigModel(
    name="calculate",
    description="Calculate",
    input_schema=generate_schema(calculate),
    handler=calculate,
)
server.register_tool(config)
```

### Pattern 2: Decorator Pattern

No changes needed! Decorators work with both:

```python
@tool()
def calculate(a: int, b: int) -> int:
    return a + b
```

### Pattern 3: Dynamic Configuration

**Before:**
```python
configs: list[ToolConfig] = []
for name, handler in tools.items():
    configs.append({
        "name": name,
        "description": f"Tool: {name}",
        "input_schema": {},
        "handler": handler,
    })
```

**After:**
```python
configs: list[ToolConfigModel] = []
for name, handler in tools.items():
    configs.append(ToolConfigModel(
        name=name,
        description=f"Tool: {name}",
        input_schema={},
        handler=handler,
    ))
```

### Pattern 4: Configuration from Dict

**Before:**
```python
config_dict = load_config_from_file("config.json")
tool_config: ToolConfig = config_dict["tool"]
```

**After:**
```python
config_dict = load_config_from_file("config.json")
tool_config = ToolConfigModel.model_validate(config_dict["tool"])
```

## Testing

### Testing with Pydantic Models

```python
import pytest
from pydantic import ValidationError
from simply_mcp.core.types import ToolConfigModel

def test_tool_config_validation():
    # Valid config
    config = ToolConfigModel(
        name="test_tool",
        description="Test",
        input_schema={},
        handler=lambda: None,
    )
    assert config.name == "test_tool"

    # Invalid config - empty name
    with pytest.raises(ValidationError) as exc_info:
        ToolConfigModel(
            name="",
            description="Test",
            input_schema={},
            handler=lambda: None,
        )
    assert "at least 1 character" in str(exc_info.value)
```

### Testing Backward Compatibility

```python
def test_dict_config_still_works():
    # Dict-based config (TypedDict)
    config: ToolConfig = {
        "name": "test_tool",
        "description": "Test",
        "input_schema": {},
        "handler": lambda: None,
    }

    # Should still work with server
    server.register_tool(config)
    assert server.registry.has_tool("test_tool")
```

## Deprecation Timeline

| Version | Status | Action |
|---------|--------|--------|
| 0.1.0 | Current | Both TypedDict and Pydantic supported |
| 0.2.0 | Next | TypedDict marked as deprecated (warnings) |
| 1.0.0 | Future | TypedDict may be removed |

### Deprecation Warnings

Starting in version 0.2.0, you may see warnings:

```python
DeprecationWarning: ToolConfig is deprecated. Use ToolConfigModel instead.
```

To migrate and remove warnings, update to Pydantic models.

## Troubleshooting

### Issue: ValidationError on valid data

**Problem:**
```python
config = ToolConfigModel(name="")  # ValidationError
```

**Solution:**
Pydantic validates field constraints. Ensure your data meets requirements:
```python
config = ToolConfigModel(name="tool_name")  # name must be at least 1 character
```

### Issue: AttributeError on dict

**Problem:**
```python
config = {"name": "tool"}
print(config.name)  # AttributeError: 'dict' object has no attribute 'name'
```

**Solution:**
Convert dict to Pydantic model first:
```python
config = ToolConfigModel(name="tool")
print(config.name)  # Works!

# Or validate existing dict
config = ToolConfigModel.model_validate({"name": "tool", ...})
```

### Issue: Can't serialize Callable

**Problem:**
```python
config.model_dump_json()  # Error: can't serialize function
```

**Solution:**
Exclude non-serializable fields:
```python
config.model_dump(exclude={"handler"})
config.model_dump_json(exclude={"handler"})
```

### Issue: Type checker errors

**Problem:**
```python
# mypy error: Incompatible types
config: ToolConfig = ToolConfigModel(...)
```

**Solution:**
Use correct type annotation:
```python
config: ToolConfigModel = ToolConfigModel(...)

# Or use union type during migration
config: ToolConfig | ToolConfigModel = ToolConfigModel(...)
```

## Best Practices

### 1. Use Pydantic for New Code

Always use Pydantic models in new code:
```python
# Good
config = ToolConfigModel(...)

# Avoid (unless maintaining legacy code)
config: ToolConfig = {...}
```

### 2. Migrate Gradually

Migrate one module at a time:
1. Update imports
2. Update type annotations
3. Update config creation
4. Test thoroughly
5. Move to next module

### 3. Leverage Validation

Take advantage of Pydantic's validation:
```python
# Add custom validation
class StrictToolConfig(ToolConfigModel):
    @field_validator('name')
    @classmethod
    def validate_name_format(cls, v: str) -> str:
        if not v.replace('_', '').isalnum():
            raise ValueError('Name must be alphanumeric with underscores')
        return v
```

### 4. Document Your Models

Use Pydantic's Field for documentation:
```python
class CustomConfig(BaseModel):
    name: str = Field(..., description="Unique tool name", min_length=1)
    timeout: int = Field(30, description="Timeout in seconds", gt=0, le=300)
```

### 5. Use Type Hints

Combine Pydantic with type hints:
```python
def register_tools(configs: list[ToolConfigModel]) -> None:
    for config in configs:
        server.register_tool(config)
```

## Resources

- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Simply-MCP API Reference](https://simply-mcp-py.readthedocs.io)
- [GitHub Repository](https://github.com/Clockwork-Innovations/simply-mcp-py)

## Questions?

If you have questions about the migration:

1. Open an issue on [GitHub](https://github.com/Clockwork-Innovations/simply-mcp-py/issues)
2. Check the documentation for more information

## Summary

The migration to Pydantic provides:
- Runtime validation
- Better IDE support
- Default values
- Serialization/deserialization
- Full backward compatibility

Start migrating today by updating imports and using the new `*Model` classes!
