# API Styles Comparison Guide

> Choosing the right API style for your MCP server

Simply-MCP-PY offers two powerful API styles for building MCP servers: the **Decorator API** and the **Builder/Functional API**. This guide helps you understand both approaches and choose the right one for your project.

## Table of Contents

- [Overview](#overview)
- [Decorator API Deep-Dive](#decorator-api-deep-dive)
- [Builder/Functional API Deep-Dive](#builderfunctional-api-deep-dive)
- [Side-by-Side Comparison](#side-by-side-comparison)
- [Migration Guide](#migration-guide)
- [Choosing Your Style](#choosing-your-style)

## Overview

### What Are the Different API Styles?

Simply-MCP-PY provides two complementary ways to build MCP servers:

**Decorator API** (`@tool`, `@prompt`, `@resource`, `@mcp_server`)
- Declarative, annotation-based approach
- Pythonic and intuitive
- Automatic registration via decorators
- Class-based organization with `@mcp_server`

**Builder/Functional API** (`BuildMCPServer`)
- Programmatic construction
- Explicit registration methods
- Method chaining support
- Instance-based decorators

### Philosophy Behind Each Style

#### Decorator API Philosophy

The Decorator API follows Python's philosophy of "there should be one obvious way to do it." It leverages Python's decorator syntax to make server development feel natural and expressive:

```python
@tool()
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b
```

Key principles:
- **Declarative**: What you see is what you get
- **Pythonic**: Feels like native Python code
- **Minimal boilerplate**: Decorators handle registration automatically
- **Organized**: Natural class-based grouping with `@mcp_server`

#### Builder/Functional API Philosophy

The Builder API provides explicit control over server construction. It's inspired by the builder pattern and supports both functional and object-oriented styles:

```python
mcp = BuildMCPServer(name="my-server")
mcp.add_tool("add", add_function)
```

Key principles:
- **Explicit**: Every action is visible in the code
- **Flexible**: Mix registration styles as needed
- **Chainable**: Fluent API for concise server building
- **Programmatic**: Easy to generate servers dynamically

### When to Use Which Style

| Use Case | Recommended Style | Why |
|----------|------------------|-----|
| Quick prototyping | Decorator API | Minimal boilerplate, fast to write |
| Class-based organization | Decorator API | `@mcp_server` provides natural grouping |
| Simple, standalone servers | Decorator API | Intuitive and self-documenting |
| Dynamic server generation | Builder API | Programmatic control over registration |
| Third-party function registration | Builder API | Can register external functions |
| Complex configuration | Builder API | Explicit configuration control |
| Multi-server applications | Builder API | Each instance is isolated |
| Team with OOP preference | Decorator API | Familiar class-based patterns |
| Team with FP preference | Builder API | Functional composition style |

## Decorator API Deep-Dive

### Module-Level Decorators

Module-level decorators (`@tool`, `@prompt`, `@resource`) automatically register with a global server instance:

```python
from simply_mcp.api.decorators import tool, prompt, resource

@tool()
def calculate(x: int, y: int, operation: str = "add") -> int:
    """Perform a calculation."""
    if operation == "add":
        return x + y
    elif operation == "multiply":
        return x * y
    raise ValueError(f"Unknown operation: {operation}")

@prompt()
def code_review(language: str = "python", style: str = "detailed") -> str:
    """Generate a code review prompt."""
    return f"Please review this {language} code with a {style} style..."

@resource(uri="config://app", mime_type="application/json")
def get_config() -> dict:
    """Get application configuration."""
    return {
        "version": "1.0.0",
        "features": {"advanced": True}
    }
```

**Key Features:**
- **Automatic registration**: Functions are registered immediately when decorated
- **Global server**: All decorators share a single server instance
- **Zero configuration**: No need to create a server object
- **Type inference**: JSON Schema generated from type hints

**Accessing the Global Server:**

```python
from simply_mcp.api.decorators import get_global_server

server = get_global_server()
await server.initialize()
await server.run_stdio()
```

### Class-Based Servers with `@mcp_server`

The `@mcp_server` decorator creates an isolated server from a class, perfect for organizing related functionality:

```python
from simply_mcp.api.decorators import mcp_server, tool, prompt, resource

@mcp_server(name="calculator-server", version="2.0.0")
class Calculator:
    """A stateful calculator with history tracking."""

    def __init__(self):
        self.history = []

    @tool()
    def calculate(self, operation: str, a: float, b: float) -> float:
        """Perform a calculation and store in history."""
        if operation == "add":
            result = a + b
        elif operation == "subtract":
            result = a - b
        elif operation == "multiply":
            result = a * b
        elif operation == "divide":
            if b == 0:
                raise ValueError("Division by zero")
            result = a / b
        else:
            raise ValueError(f"Unknown operation: {operation}")

        # Store in instance state
        self.history.append({
            "operation": operation,
            "operands": [a, b],
            "result": result
        })
        return result

    @tool()
    def get_history(self) -> list:
        """Get calculation history."""
        return self.history

    @prompt()
    def help_prompt(self) -> str:
        """Generate help prompt."""
        return """Calculator operations: add, subtract, multiply, divide"""

    @resource(uri="config://calculator")
    def get_config(self) -> dict:
        """Get calculator configuration."""
        return {"precision": 10, "history_limit": 100}

# Access the server
server = Calculator.get_server()
await server.initialize()
await server.run_stdio()
```

**Benefits:**
- **State management**: Instance variables persist across tool calls
- **Encapsulation**: Related tools grouped in a class
- **Isolation**: Each class creates a separate server
- **Organization**: Clean separation of concerns

### Pydantic Integration

Both module-level and class-based decorators support Pydantic models for advanced validation:

```python
from pydantic import BaseModel, Field

class SearchQuery(BaseModel):
    query: str = Field(description="Search query text", min_length=1)
    limit: int = Field(default=10, ge=1, le=100)
    include_archived: bool = Field(default=False)

@tool(input_schema=SearchQuery)
def search(input: SearchQuery) -> list:
    """Search with validated input."""
    results = [f"Result 1 for '{input.query}'", f"Result 2 for '{input.query}'"]
    if input.include_archived:
        results.append("Archived result")
    return results[:input.limit]
```

### Pros and Cons

**Pros:**
- Clean, declarative syntax
- Minimal boilerplate code
- Pythonic and intuitive
- Automatic schema generation
- Natural class-based organization
- Self-documenting code
- Fast to write and read

**Cons:**
- Global server can be limiting for multi-server apps
- Less explicit control over registration
- Harder to dynamically generate servers
- Cannot easily register third-party functions without wrapping

### Best Practices

1. **Use descriptive names**: Function names become tool names by default
   ```python
   @tool()  # Tool name: "calculate_statistics"
   def calculate_statistics(data: list) -> dict:
       pass
   ```

2. **Write clear docstrings**: First line becomes the tool description
   ```python
   @tool()
   def process_data(items: list) -> dict:
       """Process a list of items and return summary statistics.

       This tool analyzes the input data and computes various metrics.
       """
       pass
   ```

3. **Use type hints**: Enable automatic schema generation
   ```python
   @tool()
   def greet(name: str, formal: bool = False) -> str:  # Schema auto-generated
       pass
   ```

4. **Group related tools in classes**: Use `@mcp_server` for organization
   ```python
   @mcp_server(name="data-processor")
   class DataProcessor:
       @tool()
       def validate(self, data: dict) -> bool:
           pass

       @tool()
       def transform(self, data: dict) -> dict:
           pass
   ```

5. **Handle errors explicitly**: Raise exceptions for invalid inputs
   ```python
   @tool()
   def divide(a: float, b: float) -> float:
       if b == 0:
           raise ValueError("Cannot divide by zero")
       return a / b
   ```

## Builder/Functional API Deep-Dive

### BuildMCPServer Class

The `BuildMCPServer` class provides a builder interface for constructing servers programmatically:

```python
from simply_mcp import BuildMCPServer

# Create a server instance
mcp = BuildMCPServer(
    name="my-server",
    version="1.0.0",
    description="My MCP server"
)

# Register components
mcp.add_tool("add", add_function)
mcp.add_prompt("greet", greet_function)
mcp.add_resource("config://app", get_config)

# Configure
mcp.configure(log_level="DEBUG")

# Run
await mcp.initialize()
await mcp.run_stdio()
```

### Direct Registration Methods

The builder API provides explicit methods for registering components:

#### `add_tool(name, handler, description, input_schema)`

```python
def add_numbers(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

# Register with automatic schema generation
mcp.add_tool("add", add_numbers)

# Or provide explicit description
mcp.add_tool("add", add_numbers, description="Add two integers")

# Or provide explicit schema
mcp.add_tool("add", add_numbers, input_schema={
    "type": "object",
    "properties": {
        "a": {"type": "integer"},
        "b": {"type": "integer"}
    },
    "required": ["a", "b"]
})
```

#### `add_prompt(name, handler, description, arguments)`

```python
def generate_greeting(name: str, style: str = "formal") -> str:
    """Generate a greeting."""
    return f"Hello, {name}!" if style == "casual" else f"Good day, {name}."

# Register with automatic argument detection
mcp.add_prompt("greet", generate_greeting)

# Or provide explicit arguments
mcp.add_prompt("greet", generate_greeting,
               description="Generate a greeting",
               arguments=["name", "style"])
```

#### `add_resource(uri, handler, name, description, mime_type)`

```python
def get_app_config() -> dict:
    """Get application configuration."""
    return {"version": "1.0.0", "debug": False}

# Register with automatic name from function
mcp.add_resource("config://app", get_app_config)

# Or provide explicit metadata
mcp.add_resource(
    uri="config://app",
    handler=get_app_config,
    name="app_config",
    description="Application configuration",
    mime_type="application/json"
)
```

### Decorator Syntax on Builder (`@mcp.tool()`)

The builder also supports decorator syntax for a hybrid approach:

```python
mcp = BuildMCPServer(name="my-server")

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

@mcp.prompt()
def code_review(language: str = "python") -> str:
    """Generate a code review prompt."""
    return f"Please review this {language} code..."

@mcp.resource(uri="config://server")
def get_config() -> dict:
    """Get server configuration."""
    return {"status": "running"}
```

**Key difference from module-level decorators:**
- Instance-bound: `@mcp.tool()` registers with a specific `BuildMCPServer` instance
- Explicit: You control which server instance receives the registration
- Isolated: Multiple `BuildMCPServer` instances don't interfere with each other

### Method Chaining Patterns

The builder API supports method chaining for concise server construction:

```python
mcp = (
    BuildMCPServer(name="demo-server", version="2.0.0")
    .add_tool("add", add_function, description="Add two numbers")
    .add_tool("subtract", subtract_function, description="Subtract two numbers")
    .add_prompt("greet", greet_function, description="Generate a greeting")
    .add_resource("status://server", get_status, mime_type="application/json")
    .configure(log_level="DEBUG")
)

# Initialize and run can also be chained
await mcp.initialize()
await mcp.run_stdio()
```

**Complete chained example:**

```python
from simply_mcp import BuildMCPServer

async def main():
    def add(a: int, b: int) -> int:
        return a + b

    def subtract(a: int, b: int) -> int:
        return a - b

    def greet(name: str, style: str = "formal") -> str:
        if style == "formal":
            return f"Good day, {name}."
        return f"Hey {name}!"

    def get_status() -> dict:
        return {"status": "running", "uptime": "1h 23m"}

    # Build entire server in one expression
    mcp = (
        BuildMCPServer(name="demo-server", version="2.0.0")
        .add_tool("add", add, description="Add two numbers")
        .add_tool("subtract", subtract, description="Subtract two numbers")
        .add_prompt("greet", greet, description="Generate a greeting",
                    arguments=["name", "style"])
        .add_resource("status://server", get_status, name="server_status",
                      mime_type="application/json")
        .configure(log_level="DEBUG")
    )

    await mcp.initialize()
    await mcp.run_stdio()
```

### Configuration

The builder API provides explicit configuration methods:

```python
# During initialization
mcp = BuildMCPServer(
    name="my-server",
    version="1.0.0",
    description="My server",
    config=custom_config  # Optional custom SimplyMCPConfig
)

# Via configure method
mcp.configure(
    port=3000,
    log_level="DEBUG"
)

# Access underlying server
server = mcp.get_server()
print(server.config.server.name)
```

### Querying Components

The builder provides methods to query registered components:

```python
# List registered tools
tools = mcp.list_tools()
print(f"Tools: {tools}")  # ['add', 'subtract']

# List registered prompts
prompts = mcp.list_prompts()
print(f"Prompts: {prompts}")  # ['greet', 'help']

# List registered resources
resources = mcp.list_resources()
print(f"Resources: {resources}")  # ['config://app', 'status://server']
```

### Pros and Cons

**Pros:**
- Explicit control over registration
- Easy to register third-party functions
- Supports dynamic server generation
- Multiple isolated server instances
- Method chaining for concise code
- Programmatic configuration
- Query registered components

**Cons:**
- More boilerplate than decorator API
- Less "Pythonic" for simple cases
- Requires creating server instance
- More verbose for basic servers

### Best Practices

1. **Use method chaining for simple servers**: Keeps code concise
   ```python
   mcp = (
       BuildMCPServer(name="calc")
       .add_tool("add", add)
       .add_tool("multiply", multiply)
   )
   ```

2. **Use add_* methods for external functions**: When you can't modify the function
   ```python
   from third_party import process_data
   mcp.add_tool("process", process_data, description="Process data")
   ```

3. **Use @mcp.decorator() for internal functions**: Hybrid approach
   ```python
   mcp = BuildMCPServer(name="server")

   @mcp.tool()
   def internal_function(x: int) -> int:
       return x * 2

   mcp.add_tool("external", external_function)
   ```

4. **Query components for debugging**: Verify registration
   ```python
   print(f"Registered: {mcp.list_tools()}")
   ```

5. **Use multiple instances for multiple servers**: Isolation
   ```python
   public_api = BuildMCPServer(name="public-api")
   admin_api = BuildMCPServer(name="admin-api")
   ```

## Side-by-Side Comparison

### Same Server, Two Styles

Let's implement the same calculator server using both API styles:

#### Decorator API Version

```python
from simply_mcp.api.decorators import mcp_server, tool, prompt, resource

@mcp_server(name="calculator", version="1.0.0")
class Calculator:
    """A calculator MCP server."""

    def __init__(self):
        self.history = []

    @tool()
    def add(self, a: int, b: int) -> int:
        """Add two numbers."""
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        return result

    @tool()
    def multiply(self, a: float, b: float) -> float:
        """Multiply two numbers."""
        result = a * b
        self.history.append(f"{a} * {b} = {result}")
        return result

    @tool()
    def divide(self, a: float, b: float) -> float:
        """Divide two numbers."""
        if b == 0:
            raise ValueError("Cannot divide by zero")
        result = a / b
        self.history.append(f"{a} / {b} = {result}")
        return result

    @tool()
    def get_history(self) -> list[str]:
        """Get calculation history."""
        return self.history

    @prompt()
    def help_prompt(self) -> str:
        """Generate help prompt."""
        return "Calculator with add, multiply, divide operations."

    @resource(uri="config://calculator")
    def get_config(self) -> dict:
        """Get calculator configuration."""
        return {"precision": 10, "history_enabled": True}

# Usage
server = Calculator.get_server()
await server.initialize()
await server.run_stdio()
```

#### Builder API Version

```python
from simply_mcp import BuildMCPServer

class CalculatorState:
    """Shared state for calculator tools."""
    def __init__(self):
        self.history = []

# Create server and state
mcp = BuildMCPServer(name="calculator", version="1.0.0")
state = CalculatorState()

# Define tool handlers with access to state
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers."""
    result = a + b
    state.history.append(f"{a} + {b} = {result}")
    return result

@mcp.tool()
def multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    result = a * b
    state.history.append(f"{a} * {b} = {result}")
    return result

@mcp.tool()
def divide(a: float, b: float) -> float:
    """Divide two numbers."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    result = a / b
    state.history.append(f"{a} / {b} = {result}")
    return result

@mcp.tool()
def get_history() -> list[str]:
    """Get calculation history."""
    return state.history

@mcp.prompt()
def help_prompt() -> str:
    """Generate help prompt."""
    return "Calculator with add, multiply, divide operations."

@mcp.resource(uri="config://calculator")
def get_config() -> dict:
    """Get calculator configuration."""
    return {"precision": 10, "history_enabled": True}

# Usage
await mcp.initialize()
await mcp.run_stdio()
```

### Feature Parity Table

| Feature | Decorator API | Builder API | Notes |
|---------|--------------|-------------|-------|
| Tool registration | `@tool()` | `@mcp.tool()` or `add_tool()` | Both support auto-schema |
| Prompt registration | `@prompt()` | `@mcp.prompt()` or `add_prompt()` | Both auto-detect arguments |
| Resource registration | `@resource(uri)` | `@mcp.resource(uri)` or `add_resource()` | Both support MIME types |
| Pydantic support | Yes | Yes | Both generate schemas from models |
| Type hint schemas | Yes | Yes | Both use `auto_generate_schema()` |
| Custom schemas | Yes | Yes | Pass `input_schema` dict |
| Class-based organization | `@mcp_server` | Manual state object | Decorator more natural |
| Instance state | Class instance variables | Closure or external state | Decorator cleaner |
| Multiple servers | Multiple classes | Multiple `BuildMCPServer` instances | Builder more flexible |
| Global server | Yes (module-level) | No (instance-based) | Decorator convenience |
| Method chaining | No | Yes | Builder advantage |
| Dynamic registration | Limited | Easy | Builder advantage |
| Third-party functions | Requires wrapper | Direct registration | Builder advantage |
| Code readability | High | Medium-High | Decorator more declarative |
| Boilerplate | Minimal | Medium | Decorator advantage |
| Explicit control | Medium | High | Builder advantage |

### Performance Considerations

Both API styles have identical runtime performance:
- Same underlying `SimplyMCPServer` implementation
- Same schema generation logic
- Same validation and execution paths
- Same transport layer

**Performance differences:**
- **Startup time**: Negligible difference (< 1ms for typical servers)
- **Memory usage**: Decorator API slightly lower for class-based servers (single instance)
- **Registration overhead**: Identical (both call the same registration methods)

**Recommendation**: Choose based on developer experience and code organization, not performance.

### Type Safety Comparison

Both API styles provide full type safety with mypy:

#### Decorator API Type Safety

```python
from simply_mcp.api.decorators import tool

@tool()
def add(a: int, b: int) -> int:  # Full type checking
    return a + b

result: int = add(5, 3)  # Type-safe
# add("5", "3")  # mypy error: incompatible type
```

#### Builder API Type Safety

```python
from simply_mcp import BuildMCPServer

mcp = BuildMCPServer(name="server")

@mcp.tool()
def add(a: int, b: int) -> int:  # Full type checking
    return a + b

result: int = add(5, 3)  # Type-safe
# add("5", "3")  # mypy error: incompatible type
```

**Type safety features:**
- Full mypy support in both styles
- Type hints validated at registration time
- Pydantic models validated at runtime
- Generic types supported (List, Dict, Optional, etc.)

## Migration Guide

### Converting from Decorator to Builder

**Original (Decorator API):**

```python
from simply_mcp.api.decorators import tool, prompt, resource, get_global_server

@tool()
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

@prompt()
def greet(name: str) -> str:
    """Generate greeting."""
    return f"Hello, {name}!"

@resource(uri="config://app")
def get_config() -> dict:
    """Get configuration."""
    return {"version": "1.0.0"}

# Run
server = get_global_server()
await server.initialize()
await server.run_stdio()
```

**Converted (Builder API):**

```python
from simply_mcp import BuildMCPServer

# Create server instance
mcp = BuildMCPServer(name="simply-mcp-server", version="0.1.0")

# Option 1: Use decorator syntax on instance
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

@mcp.prompt()
def greet(name: str) -> str:
    """Generate greeting."""
    return f"Hello, {name}!"

@mcp.resource(uri="config://app")
def get_config() -> dict:
    """Get configuration."""
    return {"version": "1.0.0"}

# Option 2: Use add_* methods
# mcp.add_tool("add", add, description="Add two numbers")
# mcp.add_prompt("greet", greet, description="Generate greeting")
# mcp.add_resource("config://app", get_config)

# Run
await mcp.initialize()
await mcp.run_stdio()
```

**Migration steps:**
1. Replace `from simply_mcp.api.decorators import ...` with `from simply_mcp import BuildMCPServer`
2. Create a `BuildMCPServer` instance at the top
3. Change `@tool()` to `@mcp.tool()` (or use `add_tool()`)
4. Change `@prompt()` to `@mcp.prompt()` (or use `add_prompt()`)
5. Change `@resource()` to `@mcp.resource()` (or use `add_resource()`)
6. Replace `get_global_server()` with your `mcp` instance
7. Call `await mcp.initialize()` and `await mcp.run_stdio()`

### Converting from Builder to Decorator

**Original (Builder API):**

```python
from simply_mcp import BuildMCPServer

mcp = BuildMCPServer(name="my-server", version="1.0.0")

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

@mcp.prompt()
def greet(name: str) -> str:
    """Generate greeting."""
    return f"Hello, {name}!"

@mcp.resource(uri="config://app")
def get_config() -> dict:
    """Get configuration."""
    return {"version": "1.0.0"}

await mcp.initialize()
await mcp.run_stdio()
```

**Converted (Decorator API):**

```python
from simply_mcp.api.decorators import tool, prompt, resource, get_global_server

@tool()
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

@prompt()
def greet(name: str) -> str:
    """Generate greeting."""
    return f"Hello, {name}!"

@resource(uri="config://app")
def get_config() -> dict:
    """Get configuration."""
    return {"version": "1.0.0"}

# Run
server = get_global_server()
await server.initialize()
await server.run_stdio()
```

**Migration steps:**
1. Replace `from simply_mcp import BuildMCPServer` with `from simply_mcp.api.decorators import tool, prompt, resource, get_global_server`
2. Remove the `BuildMCPServer` instance creation
3. Change `@mcp.tool()` to `@tool()`
4. Change `@mcp.prompt()` to `@prompt()`
5. Change `@mcp.resource()` to `@resource()`
6. Replace `mcp` with `get_global_server()`
7. Use `server.initialize()` and `server.run_stdio()`

**Note for class-based organization:**

If you want class-based organization in Decorator API, use `@mcp_server`:

```python
from simply_mcp.api.decorators import mcp_server, tool, prompt, resource

@mcp_server(name="my-server", version="1.0.0")
class MyServer:
    @tool()
    def add(self, a: int, b: int) -> int:
        """Add two numbers."""
        return a + b

    @prompt()
    def greet(self, name: str) -> str:
        """Generate greeting."""
        return f"Hello, {name}!"

    @resource(uri="config://app")
    def get_config(self) -> dict:
        """Get configuration."""
        return {"version": "1.0.0"}

# Run
server = MyServer.get_server()
await server.initialize()
await server.run_stdio()
```

### Converting add_* Methods to Decorators

**Original (add_* methods):**

```python
def add(a: int, b: int) -> int:
    return a + b

def greet(name: str) -> str:
    return f"Hello, {name}!"

mcp = BuildMCPServer(name="server")
mcp.add_tool("add", add, description="Add two numbers")
mcp.add_prompt("greet", greet, description="Generate greeting")
```

**Converted (decorators):**

```python
mcp = BuildMCPServer(name="server")

@mcp.tool(description="Add two numbers")
def add(a: int, b: int) -> int:
    return a + b

@mcp.prompt(description="Generate greeting")
def greet(name: str) -> str:
    return f"Hello, {name}!"
```

**When to keep add_* methods:**
- Registering third-party functions
- Dynamic registration (in loops or conditionally)
- When function is defined elsewhere

## Choosing Your Style

### Decision Tree

```
Start here
    |
    v
Do you need multiple isolated servers?
    |
    +-- Yes --> Builder API (multiple BuildMCPServer instances)
    |
    +-- No
        |
        v
Is your server structure dynamic (runtime generation)?
        |
        +-- Yes --> Builder API (programmatic registration)
        |
        +-- No
            |
            v
Do you need to register third-party functions?
            |
            +-- Yes --> Builder API (direct registration)
            |
            +-- No
                |
                v
Do you prefer class-based organization?
                |
                +-- Yes --> Decorator API (@mcp_server)
                |
                +-- No --> Decorator API (module-level @tool/@prompt/@resource)
```

### Use Case Recommendations

#### 1. Simple, Standalone Server

**Recommended**: Decorator API (module-level)

```python
from simply_mcp.api.decorators import tool, prompt

@tool()
def search(query: str) -> list:
    return ["result1", "result2"]

@prompt()
def help() -> str:
    return "Use search to find items"
```

**Why**: Minimal boilerplate, fastest to write, self-documenting.

#### 2. Organized, Feature-Rich Server

**Recommended**: Decorator API (@mcp_server)

```python
@mcp_server(name="data-api", version="1.0.0")
class DataAPI:
    def __init__(self):
        self.db = Database()

    @tool()
    def query(self, sql: str) -> list:
        return self.db.execute(sql)

    @tool()
    def insert(self, table: str, data: dict) -> bool:
        return self.db.insert(table, data)
```

**Why**: Natural class organization, instance state, clean separation.

#### 3. Multi-Server Application

**Recommended**: Builder API

```python
# Public API
public = BuildMCPServer(name="public-api")

@public.tool()
def public_search(query: str) -> list:
    return search_public(query)

# Admin API
admin = BuildMCPServer(name="admin-api")

@admin.tool()
def admin_delete(id: int) -> bool:
    return delete_item(id)

# Run both
await public.initialize()
await admin.initialize()
```

**Why**: Complete isolation between servers, independent configuration.

#### 4. Dynamic Server Generation

**Recommended**: Builder API

```python
def create_server(name: str, tools_config: list) -> BuildMCPServer:
    mcp = BuildMCPServer(name=name)

    for config in tools_config:
        mcp.add_tool(
            name=config["name"],
            handler=import_function(config["module"], config["function"]),
            description=config["description"]
        )

    return mcp

# Generate servers from configuration
server = create_server("dynamic-server", load_config())
```

**Why**: Programmatic control, runtime generation, configuration-driven.

#### 5. Third-Party Integration

**Recommended**: Builder API

```python
from third_party_lib import process_data, validate_input

mcp = BuildMCPServer(name="integration")

# Register external functions directly
mcp.add_tool("process", process_data, description="Process data")
mcp.add_tool("validate", validate_input, description="Validate input")
```

**Why**: Can register external functions without modification.

### Team Size Considerations

**Small teams (1-3 developers):**
- Use Decorator API for simplicity
- `@mcp_server` for organization
- Less boilerplate means faster development

**Medium teams (4-10 developers):**
- Choose based on project complexity
- Decorator API for microservices
- Builder API for multi-server applications
- Consider consistency across projects

**Large teams (10+ developers):**
- Builder API for explicit control
- Easier to enforce patterns
- Better for code generation tools
- More explicit, easier to review

### Project Complexity Factors

| Complexity Factor | Simple | Medium | Complex |
|-------------------|--------|---------|---------|
| Number of tools | 1-5 | 6-20 | 20+ |
| Server instances | 1 | 1-3 | 3+ |
| State management | None | Simple | Complex |
| Dynamic behavior | None | Some | Extensive |
| **Recommended Style** | **Decorator** | **Either** | **Builder** |

### Summary Recommendations

Choose **Decorator API** when:
- Building standalone servers
- Prioritizing developer experience
- Using class-based organization
- Working on microservices
- Small to medium complexity

Choose **Builder API** when:
- Building multi-server applications
- Need dynamic server generation
- Registering third-party functions
- Require explicit control
- Medium to high complexity

**Remember**: Both styles are fully supported and can be mixed. Start with Decorator API for simplicity, migrate to Builder API if you need more control.

## See Also

- [Getting Started Guide](../getting-started/quickstart.md)
- [Configuration Guide](./configuration.md)
- [Examples](../examples/index.md)
- [API Reference - Decorators](../api/decorators.md)
- [API Reference - Builder](../api/builder.md)
