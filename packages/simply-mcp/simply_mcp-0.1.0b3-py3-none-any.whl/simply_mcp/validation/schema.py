"""Schema generation from Python type hints and Pydantic models.

This module provides automatic JSON Schema generation from various Python sources:
- Function signatures with type hints
- Pydantic BaseModel classes
- Dataclasses
- TypedDict classes

The generated schemas are compatible with MCP tool input schemas.
"""

import dataclasses
import inspect
import re
from collections.abc import Callable
from typing import (
    Any,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

try:
    from pydantic import BaseModel
    from pydantic.fields import FieldInfo
    PYDANTIC_AVAILABLE = True
except ImportError:
    BaseModel = object  # type: ignore[assignment,misc]
    FieldInfo = object  # type: ignore[assignment,misc]
    PYDANTIC_AVAILABLE = False


class SchemaGenerationError(Exception):
    """Raised when schema generation fails."""
    pass


def python_type_to_json_schema_type(python_type: Any) -> dict[str, Any]:
    """Convert Python type to JSON Schema type.

    Args:
        python_type: Python type annotation

    Returns:
        JSON Schema type definition

    Examples:
        >>> python_type_to_json_schema_type(int)
        {'type': 'integer'}
        >>> python_type_to_json_schema_type(Optional[str])
        {'type': ['string', 'null']}
    """
    origin = get_origin(python_type)
    args = get_args(python_type)

    # Handle None type
    if python_type is type(None):
        return {"type": "null"}

    # Handle basic types
    if python_type is int:
        return {"type": "integer"}
    elif python_type is float:
        return {"type": "number"}
    elif python_type is str:
        return {"type": "string"}
    elif python_type is bool:
        return {"type": "boolean"}
    elif python_type is list or origin is list:
        if args:
            return {"type": "array", "items": python_type_to_json_schema_type(args[0])}
        return {"type": "array"}
    elif python_type is dict or origin is dict:
        if args and len(args) == 2:
            return {
                "type": "object",
                "additionalProperties": python_type_to_json_schema_type(args[1])
            }
        return {"type": "object"}
    elif python_type is tuple or origin is tuple:
        if args:
            return {
                "type": "array",
                "items": [python_type_to_json_schema_type(arg) for arg in args]
            }
        return {"type": "array"}

    # Handle Optional (Union with None)
    if origin is Union:
        # Check if this is Optional[T] (Union[T, None])
        non_none_args = [arg for arg in args if arg is not type(None)]
        if len(args) == 2 and type(None) in args:
            # This is Optional[T]
            base_schema = python_type_to_json_schema_type(non_none_args[0])
            if "type" in base_schema and isinstance(base_schema["type"], str):
                base_schema["type"] = [base_schema["type"], "null"]
            return base_schema
        else:
            # This is a true Union
            return {"anyOf": [python_type_to_json_schema_type(arg) for arg in args]}

    # Handle Literal
    if origin is getattr(__builtins__, 'Literal', None) or str(origin) == "typing.Literal":
        return {"enum": list(args)}

    # Handle Any
    if python_type is Any:
        return {}

    # Handle dataclasses
    if dataclasses.is_dataclass(python_type) and isinstance(python_type, type):
        return generate_schema_from_dataclass(python_type)

    # Handle Pydantic models
    if PYDANTIC_AVAILABLE and isinstance(python_type, type) and issubclass(python_type, BaseModel):
        return generate_schema_from_pydantic(python_type)

    # Unknown type - return empty schema
    return {}


def extract_description_from_docstring(func: Callable[..., Any]) -> str | None:
    """Extract description from function docstring.

    Supports Google-style and NumPy-style docstrings.

    Args:
        func: Function to extract docstring from

    Returns:
        Extracted description or None

    Examples:
        >>> def add(a: int, b: int) -> int:
        ...     '''Add two numbers.
        ...
        ...     Args:
        ...         a: First number
        ...         b: Second number
        ...     '''
        ...     return a + b
        >>> extract_description_from_docstring(add)
        'Add two numbers.'
    """
    if not func.__doc__:
        return None

    # Get the first line or paragraph as description
    docstring = inspect.cleandoc(func.__doc__)

    # Split by common section markers
    sections = re.split(r'\n\s*(?:Args?|Parameters?|Returns?|Raises?|Examples?|Note|Notes):', docstring)

    # Take the first section (before any Args/Returns/etc)
    description = sections[0].strip()

    # Take first paragraph if multiple paragraphs
    paragraphs = description.split('\n\n')
    if paragraphs:
        return paragraphs[0].strip()

    return description if description else None


def extract_param_descriptions_from_docstring(func: Callable[..., Any]) -> dict[str, str]:
    """Extract parameter descriptions from function docstring.

    Supports Google-style and NumPy-style docstrings.

    Args:
        func: Function to extract parameter descriptions from

    Returns:
        Dictionary mapping parameter names to their descriptions
    """
    if not func.__doc__:
        return {}

    docstring = inspect.cleandoc(func.__doc__)
    descriptions: dict[str, str] = {}

    # Google-style: Args: or Arguments:
    google_match = re.search(r'(?:Args?|Arguments?):\s*\n((?:.*\n?)*?)(?=\n(?:Returns?|Raises?|Examples?|Note|Notes):|$)', docstring, re.DOTALL)
    if google_match:
        args_section = google_match.group(1)
        # Match "param_name: description" or "param_name (type): description"
        for match in re.finditer(r'^\s+(\w+)\s*(?:\([^)]+\))?\s*:\s*(.+?)(?=^\s+\w+\s*(?:\([^)]+\))?\s*:|$)', args_section, re.MULTILINE | re.DOTALL):
            param_name = match.group(1)
            description = match.group(2).strip().replace('\n', ' ').replace('  ', ' ')
            descriptions[param_name] = description

    # NumPy-style: Parameters with dashes
    numpy_match = re.search(r'Parameters?\s*\n\s*-+\s*\n((?:.*\n)*?)(?:\n\s*(?:Returns?|Raises?|Examples?|Note|Notes)\s*\n\s*-+|$)', docstring)
    if numpy_match:
        params_section = numpy_match.group(1)
        # Match "param_name : type\n    description"
        for match in re.finditer(r'(\w+)\s*:\s*[^\n]+\n\s+(.+?)(?=\n\w+\s*:|$)', params_section, re.DOTALL):
            param_name = match.group(1)
            description = match.group(2).strip().replace('\n', ' ')
            descriptions[param_name] = description

    return descriptions


def generate_schema_from_function(func: Callable[..., Any]) -> dict[str, Any]:
    """Generate JSON schema from function signature.

    Inspects function parameters, type hints, and docstring to generate
    an MCP-compatible input schema.

    Args:
        func: Function to generate schema from

    Returns:
        JSON Schema dictionary

    Raises:
        SchemaGenerationError: If schema generation fails

    Examples:
        >>> def greet(name: str, age: int = 25) -> str:
        ...     '''Greet a person.
        ...
        ...     Args:
        ...         name: Person's name
        ...         age: Person's age
        ...     '''
        ...     return f"Hello {name}, you are {age}"
        >>> schema = generate_schema_from_function(greet)
        >>> schema['properties']['name']['type']
        'string'
        >>> 'age' not in schema['required']
        True
    """
    try:
        sig = inspect.signature(func)
        type_hints = get_type_hints(func)
    except Exception as e:
        raise SchemaGenerationError(f"Failed to inspect function {func.__name__}: {e}") from e

    properties: dict[str, Any] = {}
    required: list[str] = []

    # Extract parameter descriptions from docstring
    param_descriptions = extract_param_descriptions_from_docstring(func)

    for param_name, param in sig.parameters.items():
        # Skip self, cls, *args, **kwargs
        if param_name in ('self', 'cls'):
            continue
        if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
            continue

        # Get type hint
        param_type = type_hints.get(param_name, Any)

        # Convert to JSON Schema
        param_schema = python_type_to_json_schema_type(param_type)

        # Add description if available
        if param_name in param_descriptions:
            param_schema["description"] = param_descriptions[param_name]

        # Add default value if present
        if param.default is not inspect.Parameter.empty:
            if param.default is not None:
                param_schema["default"] = param.default
        else:
            # No default means required (unless Optional)
            origin = get_origin(param_type)
            args = get_args(param_type)
            is_optional = origin is Union and type(None) in args

            if not is_optional:
                required.append(param_name)

        properties[param_name] = param_schema

    schema: dict[str, Any] = {
        "type": "object",
        "properties": properties
    }

    if required:
        schema["required"] = required

    return schema


def generate_schema_from_pydantic(model: type[BaseModel]) -> dict[str, Any]:
    """Generate JSON schema from Pydantic model.

    Uses Pydantic's built-in schema generation with proper field metadata.

    Args:
        model: Pydantic BaseModel class

    Returns:
        JSON Schema dictionary

    Raises:
        SchemaGenerationError: If Pydantic is not available or schema generation fails

    Examples:
        >>> from pydantic import BaseModel, Field
        >>> class User(BaseModel):
        ...     name: str = Field(description="User's name")
        ...     age: int = Field(ge=0, le=150, description="User's age")
        >>> schema = generate_schema_from_pydantic(User)
        >>> schema['properties']['age']['minimum']
        0
    """
    if not PYDANTIC_AVAILABLE:
        raise SchemaGenerationError("Pydantic is not installed")

    try:
        # Use Pydantic's schema generation
        json_schema = model.model_json_schema()

        # Remove $defs if empty
        if "$defs" in json_schema and not json_schema["$defs"]:
            del json_schema["$defs"]

        # Remove title if it's just the class name
        if "title" in json_schema and json_schema["title"] == model.__name__:
            del json_schema["title"]

        return json_schema
    except Exception as e:
        raise SchemaGenerationError(f"Failed to generate schema from Pydantic model {model.__name__}: {e}") from e


def generate_schema_from_dataclass(cls: type[Any]) -> dict[str, Any]:
    """Generate JSON schema from dataclass.

    Args:
        cls: Dataclass to generate schema from

    Returns:
        JSON Schema dictionary

    Raises:
        SchemaGenerationError: If input is not a dataclass or schema generation fails

    Examples:
        >>> from dataclasses import dataclass
        >>> @dataclass
        ... class Point:
        ...     x: int
        ...     y: int
        ...     label: str = "origin"
        >>> schema = generate_schema_from_dataclass(Point)
        >>> 'label' not in schema['required']
        True
        >>> schema['properties']['label']['default']
        'origin'
    """
    if not dataclasses.is_dataclass(cls):
        raise SchemaGenerationError(f"{cls.__name__} is not a dataclass")

    try:
        fields = dataclasses.fields(cls)
        type_hints = get_type_hints(cls)

        properties: dict[str, Any] = {}
        required: list[str] = []

        for field in fields:
            field_type = type_hints.get(field.name, Any)
            field_schema = python_type_to_json_schema_type(field_type)

            # Add default value if present
            if field.default is not dataclasses.MISSING:
                field_schema["default"] = field.default
            elif field.default_factory is not dataclasses.MISSING:
                # We can't serialize the factory, so just note it has a default
                pass
            else:
                # No default means required (unless Optional)
                origin = get_origin(field_type)
                args = get_args(field_type)
                is_optional = origin is Union and type(None) in args

                if not is_optional:
                    required.append(field.name)

            properties[field.name] = field_schema

        schema: dict[str, Any] = {
            "type": "object",
            "properties": properties
        }

        if required:
            schema["required"] = required

        return schema
    except Exception as e:
        raise SchemaGenerationError(f"Failed to generate schema from dataclass {cls.__name__}: {e}") from e


def generate_schema_from_typeddict(cls: type[Any]) -> dict[str, Any]:
    """Generate JSON schema from TypedDict.

    Args:
        cls: TypedDict class to generate schema from

    Returns:
        JSON Schema dictionary

    Raises:
        SchemaGenerationError: If input is not a TypedDict or schema generation fails

    Examples:
        >>> from typing import TypedDict
        >>> class UserDict(TypedDict):
        ...     name: str
        ...     age: int
        >>> schema = generate_schema_from_typeddict(UserDict)
        >>> schema['type']
        'object'
    """
    # Check if it's a TypedDict by looking for __annotations__ and __total__
    if not (hasattr(cls, '__annotations__') and hasattr(cls, '__total__')):
        raise SchemaGenerationError(f"{cls.__name__} is not a TypedDict")

    try:
        type_hints = get_type_hints(cls)
        required_keys: set[str] = getattr(cls, '__required_keys__', set())
        optional_keys: set[str] = getattr(cls, '__optional_keys__', set())

        properties: dict[str, Any] = {}
        required: list[str] = []

        for field_name, field_type in type_hints.items():
            field_schema = python_type_to_json_schema_type(field_type)
            properties[field_name] = field_schema

            # Determine if required
            if required_keys and field_name in required_keys:
                required.append(field_name)
            elif not optional_keys and field_name not in optional_keys:
                # If no __required_keys__ attribute, check if field is Optional
                origin = get_origin(field_type)
                args = get_args(field_type)
                is_optional = origin is Union and type(None) in args

                if not is_optional:
                    required.append(field_name)

        schema: dict[str, Any] = {
            "type": "object",
            "properties": properties
        }

        if required:
            schema["required"] = required

        return schema
    except Exception as e:
        raise SchemaGenerationError(f"Failed to generate schema from TypedDict {cls.__name__}: {e}") from e


def auto_generate_schema(source: Callable[..., Any] | type[Any]) -> dict[str, Any]:
    """Auto-detect source type and generate schema.

    Smart detection that supports:
    - Pydantic BaseModel
    - Dataclass
    - TypedDict
    - Function with type hints

    Args:
        source: Source to generate schema from

    Returns:
        JSON Schema dictionary

    Raises:
        SchemaGenerationError: If source type is unsupported

    Examples:
        >>> def add(a: int, b: int) -> int:
        ...     return a + b
        >>> schema = auto_generate_schema(add)
        >>> schema['properties']['a']['type']
        'integer'

        >>> from dataclasses import dataclass
        >>> @dataclass
        ... class Point:
        ...     x: int
        ...     y: int
        >>> schema = auto_generate_schema(Point)
        >>> len(schema['required'])
        2
    """
    # Check if it's a Pydantic model
    if PYDANTIC_AVAILABLE and isinstance(source, type) and issubclass(source, BaseModel):
        return generate_schema_from_pydantic(source)

    # Check if it's a dataclass
    if dataclasses.is_dataclass(source):
        return generate_schema_from_dataclass(source)

    # Check if it's a TypedDict
    if isinstance(source, type) and hasattr(source, '__annotations__') and hasattr(source, '__total__'):
        return generate_schema_from_typeddict(source)

    # Check if it's a callable (function or method) but not a class
    if callable(source) and not isinstance(source, type):
        return generate_schema_from_function(source)

    # Unsupported type
    raise SchemaGenerationError(
        f"Unsupported source type: {type(source).__name__}. "
        "Supported types: Pydantic BaseModel, dataclass, TypedDict, or function with type hints."
    )


__all__ = [
    "SchemaGenerationError",
    "python_type_to_json_schema_type",
    "extract_description_from_docstring",
    "extract_param_descriptions_from_docstring",
    "generate_schema_from_function",
    "generate_schema_from_pydantic",
    "generate_schema_from_dataclass",
    "generate_schema_from_typeddict",
    "auto_generate_schema",
]
