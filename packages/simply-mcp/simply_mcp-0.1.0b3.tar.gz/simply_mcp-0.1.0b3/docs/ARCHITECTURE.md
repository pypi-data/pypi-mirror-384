# Simply-MCP-PY: Architecture Document

**Version:** 0.1.0
**Last Updated:** 2025-10-12
**Status:** Planning Phase

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Architectural Layers](#2-architectural-layers)
3. [Component Architecture](#3-component-architecture)
4. [Data Flow](#4-data-flow)
5. [Design Patterns](#5-design-patterns)
6. [API Style Architecture](#6-api-style-architecture)
7. [Transport Architecture](#7-transport-architecture)
8. [Security Architecture](#8-security-architecture)
9. [Error Handling Architecture](#9-error-handling-architecture)
10. [Extension Points](#10-extension-points)
11. [Deployment Architecture](#11-deployment-architecture)

---

## 1. System Overview

### 1.1 High-Level Architecture

Simply-MCP-PY is built as a layered architecture that sits on top of the Anthropic MCP Python SDK, providing multiple high-level API abstractions while maintaining flexibility and extensibility.

```
┌──────────────────────────────────────────────────────────┐
│                     User Application                      │
│              (Decorator / Functional / Interface)          │
└────────────────────────┬─────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────┐
│                  Simply-MCP API Layer                     │
│    ┌──────────┬──────────────┬──────────────┬─────────┐ │
│    │Decorator │  Functional  │  Interface   │ Builder │ │
│    │   API    │     API      │     API      │   API   │ │
│    └──────────┴──────────────┴──────────────┴─────────┘ │
└────────────────────────┬─────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────┐
│               Simply-MCP Core Layer                       │
│  ┌──────────┬───────────┬──────────────┬──────────────┐ │
│  │  Server  │  Config   │  Validation  │   Registry   │ │
│  │ Manager  │  Loader   │   Engine     │   System     │ │
│  └──────────┴───────────┴──────────────┴──────────────┘ │
│  ┌──────────┬───────────┬──────────────┬──────────────┐ │
│  │ Handler  │   Error   │   Logger     │   Security   │ │
│  │ Manager  │  Handler  │              │              │ │
│  └──────────┴───────────┴──────────────┴──────────────┘ │
└────────────────────────┬─────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────┐
│              Transport Adapter Layer                      │
│    ┌──────────┬──────────────┬──────────────┐           │
│    │  Stdio   │     HTTP     │     SSE      │           │
│    │ Adapter  │   Adapter    │   Adapter    │           │
│    └──────────┴──────────────┴──────────────┘           │
└────────────────────────┬─────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────┐
│            Anthropic MCP Python SDK                       │
│  ┌───────────────────────────────────────────────────┐  │
│  │  MCP Protocol Implementation                       │  │
│  │  (Tools, Prompts, Resources, Sessions)            │  │
│  └───────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

### 1.2 Design Principles

1. **Separation of Concerns**: Each layer has a distinct responsibility
2. **Dependency Inversion**: High-level modules don't depend on low-level modules
3. **Open/Closed Principle**: Open for extension, closed for modification
4. **Interface Segregation**: Multiple specific interfaces over one general interface
5. **Single Responsibility**: Each class/module has one reason to change
6. **DRY (Don't Repeat Yourself)**: Code reuse through abstraction
7. **YAGNI (You Aren't Gonna Need It)**: Implement features when needed
8. **Pythonic**: Follow Python idioms and conventions

---

## 2. Architectural Layers

### 2.1 Layer Responsibilities

#### User Application Layer
- **Responsibility**: User code defining tools, prompts, and resources
- **Dependencies**: Simply-MCP API Layer
- **Outputs**: Server definitions using chosen API style

#### API Layer
- **Responsibility**: Provide multiple API styles for defining servers
- **Dependencies**: Core Layer
- **Components**: Decorator API, Functional API, Interface API, Builder API
- **Outputs**: Normalized server configuration

#### Core Layer
- **Responsibility**: Core business logic and server management
- **Dependencies**: Transport Layer, MCP SDK (indirect)
- **Components**: Server Manager, Config Loader, Validation, Registry, Handlers
- **Outputs**: Configured server ready for transport

#### Transport Adapter Layer
- **Responsibility**: Adapt different transport mechanisms to core layer
- **Dependencies**: MCP SDK
- **Components**: Stdio, HTTP, SSE adapters
- **Outputs**: Transport-specific server instances

#### MCP SDK Layer
- **Responsibility**: Low-level MCP protocol implementation
- **Dependencies**: External (Anthropic MCP SDK)
- **Components**: Protocol handlers, session management, serialization
- **Outputs**: MCP-compliant communication

### 2.2 Layer Communication

```
User Code ──[function calls]──▶ API Layer
                                     │
                                     │ [converts to]
                                     ▼
                                Core Layer
                                     │
                                     │ [configures]
                                     ▼
                            Transport Adapters
                                     │
                                     │ [uses]
                                     ▼
                                  MCP SDK
                                     │
                                     │ [communicates via]
                                     ▼
                              Stdio/HTTP/SSE
```

---

## 3. Component Architecture

### 3.1 API Layer Components

#### Decorator API (`src/simply_mcp/api/decorator.py`)

```python
┌─────────────────────────────────────┐
│       Decorator API Module          │
├─────────────────────────────────────┤
│                                     │
│  @mcp_server()                      │
│    ├─ Class metadata extractor      │
│    ├─ Server config builder         │
│    └─ Registration trigger          │
│                                     │
│  @tool()                            │
│    ├─ Method metadata extractor     │
│    ├─ Type hint parser              │
│    ├─ Schema generator              │
│    └─ Handler wrapper               │
│                                     │
│  @prompt()                          │
│    ├─ Prompt metadata extractor     │
│    ├─ Template parser               │
│    └─ Argument validator            │
│                                     │
│  @resource()                        │
│    ├─ Resource metadata extractor   │
│    ├─ URI template parser           │
│    └─ Content type handler          │
│                                     │
└─────────────────────────────────────┘
```

**Key Responsibilities:**
- Extract metadata from decorated classes and methods
- Generate Pydantic schemas from type hints
- Register tools/prompts/resources with core registry
- Validate decorator arguments
- Provide runtime reflection capabilities

**Design Pattern**: Decorator Pattern, Metadata Programming

#### Functional API (`src/simply_mcp/api/functional.py`)

```python
┌─────────────────────────────────────┐
│     Functional API Module           │
├─────────────────────────────────────┤
│                                     │
│  BuildMCPServer                          │
│    ├─ __init__(config)              │
│    ├─ add_tool(fn, **opts)          │
│    ├─ add_prompt(fn, **opts)        │
│    ├─ add_resource(fn, **opts)      │
│    ├─ configure(**opts)             │
│    ├─ run()                         │
│    └─ _registry: Registry           │
│                                     │
│  ToolBuilder                        │
│    ├─ Schema validation             │
│    ├─ Handler wrapping              │
│    └─ Metadata construction         │
│                                     │
└─────────────────────────────────────┘
```

**Key Responsibilities:**
- Provide fluent interface for server building
- Enable dynamic tool/prompt/resource registration
- Support method chaining for ergonomics
- Validate configurations programmatically
- Manage internal registry

**Design Pattern**: Builder Pattern, Fluent Interface

#### Interface API (`src/simply_mcp/api/interface.py`)

```python
┌─────────────────────────────────────┐
│      Interface API Module           │
├─────────────────────────────────────┤
│                                     │
│  MCPServerProtocol                  │
│    ├─ Type definitions              │
│    └─ Protocol specification        │
│                                     │
│  InterfaceInspector                 │
│    ├─ Class introspection           │
│    ├─ Type hint extraction          │
│    ├─ Docstring parsing             │
│    └─ Schema generation             │
│                                     │
│  AutoSchemaBuilder                  │
│    ├─ Type → Schema mapping         │
│    ├─ Pydantic model generation     │
│    └─ JSON Schema export            │
│                                     │
└─────────────────────────────────────┘
```

**Key Responsibilities:**
- Define type-based interfaces (Protocol)
- Automatically discover tools from type annotations
- Generate schemas without decorators
- Support static type checking
- Enable IDE autocomplete

**Design Pattern**: Protocol Pattern, Introspection

### 3.2 Core Layer Components

#### Server Manager (`src/simply_mcp/core/server.py`)

```python
┌─────────────────────────────────────┐
│       SimplyMCPServer               │
├─────────────────────────────────────┤
│  Properties:                        │
│    - config: ServerConfig           │
│    - registry: Registry             │
│    - handler_manager: HandlerMgr    │
│    - transport: Transport           │
│                                     │
│  Methods:                           │
│    - __init__(config)               │
│    - register_tool(metadata)        │
│    - register_prompt(metadata)      │
│    - register_resource(metadata)    │
│    - start()                        │
│    - stop()                         │
│    - handle_request(request)        │
│    - _initialize_transport()        │
│    - _setup_handlers()              │
│                                     │
│  Lifecycle:                         │
│    CREATED → INITIALIZED →          │
│    RUNNING → STOPPED                │
└─────────────────────────────────────┘
```

**Key Responsibilities:**
- Manage server lifecycle
- Coordinate between components
- Handle requests/responses
- Initialize and configure transport
- Manage tool/prompt/resource registry

#### Registry System (`src/simply_mcp/core/registry.py`)

```python
┌─────────────────────────────────────┐
│          Registry                   │
├─────────────────────────────────────┤
│  Storage:                           │
│    - tools: Dict[str, ToolConfig]   │
│    - prompts: Dict[str, PromptCfg]  │
│    - resources: Dict[str, ResCfg]   │
│    - metadata: Dict[str, Any]       │
│                                     │
│  Methods:                           │
│    - register_tool(name, config)    │
│    - register_prompt(name, config)  │
│    - register_resource(name, cfg)   │
│    - get_tool(name)                 │
│    - get_all_tools()                │
│    - validate_registration()        │
│    - check_duplicates()             │
│                                     │
│  Features:                          │
│    - Name conflict detection        │
│    - Schema validation              │
│    - Metadata storage               │
│    - Query interface                │
└─────────────────────────────────────┘
```

**Key Responsibilities:**
- Store registered tools/prompts/resources
- Prevent name collisions
- Validate configurations
- Provide lookup interface
- Maintain metadata

#### Configuration Loader (`src/simply_mcp/core/config.py`)

```python
┌─────────────────────────────────────┐
│       Configuration System          │
├─────────────────────────────────────┤
│  Models (Pydantic):                 │
│    - ServerConfig                   │
│    - TransportConfig                │
│    - LoggingConfig                  │
│    - SecurityConfig                 │
│    - SimplyMCPConfig (root)         │
│                                     │
│  Loader:                            │
│    - load_from_file(path)           │
│    - load_from_env()                │
│    - load_from_dict(data)           │
│    - merge_configs(configs)         │
│    - validate_config(config)        │
│                                     │
│  Formats:                           │
│    - TOML (primary)                 │
│    - JSON (secondary)               │
│    - Environment variables          │
│    - Python dict                    │
└─────────────────────────────────────┘
```

**Key Responsibilities:**
- Load configuration from multiple sources
- Validate configuration schemas
- Merge configurations (precedence: env > file > defaults)
- Provide type-safe access
- Handle configuration errors

#### Handler Manager (`src/simply_mcp/handlers/manager.py`)

```python
┌─────────────────────────────────────┐
│        Handler Manager              │
├─────────────────────────────────────┤
│  Request Pipeline:                  │
│    1. Authentication                │
│    2. Rate Limiting                 │
│    3. Request Validation            │
│    4. Handler Execution             │
│    5. Response Formatting           │
│    6. Error Handling                │
│                                     │
│  Methods:                           │
│    - handle_tool_call(request)      │
│    - handle_prompt(request)         │
│    - handle_resource(request)       │
│    - execute_handler(handler, ctx)  │
│    - handle_error(exception)        │
│                                     │
│  Context:                           │
│    - request: Request               │
│    - session: Session               │
│    - server: SimplyMCPServer        │
│    - logger: Logger                 │
└─────────────────────────────────────┘
```

**Key Responsibilities:**
- Execute request pipeline
- Manage handler lifecycle
- Provide request context
- Handle errors gracefully
- Apply middleware

### 3.3 Transport Layer Components

#### Base Transport (`src/simply_mcp/transports/base.py`)

```python
┌─────────────────────────────────────┐
│      Transport (ABC)                │
├─────────────────────────────────────┤
│  Abstract Methods:                  │
│    - start()                        │
│    - stop()                         │
│    - send_message(msg)              │
│    - receive_message()              │
│    - handle_connection()            │
│                                     │
│  Hooks:                             │
│    - on_connect()                   │
│    - on_disconnect()                │
│    - on_error(error)                │
│                                     │
│  Properties:                        │
│    - is_running: bool               │
│    - config: TransportConfig        │
└─────────────────────────────────────┘
```

#### Stdio Transport

```python
┌─────────────────────────────────────┐
│       StdioTransport                │
├─────────────────────────────────────┤
│  Components:                        │
│    - stdin: TextIO                  │
│    - stdout: TextIO                 │
│    - stderr: TextIO                 │
│    - message_framer: Framer         │
│                                     │
│  Message Flow:                      │
│    stdin → parse → validate →       │
│    handle → format → stdout         │
│                                     │
│  Error Handling:                    │
│    errors → stderr                  │
└─────────────────────────────────────┘
```

#### HTTP Transport

```python
┌─────────────────────────────────────┐
│        HTTPTransport                │
├─────────────────────────────────────┤
│  Components:                        │
│    - app: aiohttp.Application       │
│    - session_store: SessionStore    │
│    - cors_handler: CORSHandler      │
│    - middleware: List[Middleware]   │
│                                     │
│  Endpoints:                         │
│    POST /tools/{tool_name}          │
│    POST /prompts/{prompt_name}      │
│    GET  /resources/{resource_uri}   │
│    GET  /health                     │
│    GET  /openapi.json               │
│                                     │
│  Features:                          │
│    - Stateful sessions              │
│    - CORS support                   │
│    - OpenAPI docs                   │
│    - Health checks                  │
└─────────────────────────────────────┘
```

#### SSE Transport

```python
┌─────────────────────────────────────┐
│         SSETransport                │
├─────────────────────────────────────┤
│  Components:                        │
│    - event_stream: EventStream      │
│    - connection_pool: ConnPool      │
│    - heartbeat: Heartbeat           │
│                                     │
│  Event Types:                       │
│    - tool_result                    │
│    - progress_update                │
│    - error                          │
│    - keepalive                      │
│                                     │
│  Features:                          │
│    - Auto-reconnection              │
│    - Event history                  │
│    - Progress streaming             │
│    - Connection management          │
└─────────────────────────────────────┘
```

---

## 4. Data Flow

### 4.1 Server Initialization Flow

```
User Code
    │
    ├─ Defines server (via Decorator/Functional/Interface API)
    │
    ▼
API Layer
    │
    ├─ Extracts metadata
    ├─ Generates schemas
    ├─ Validates configuration
    │
    ▼
Core Layer (Server Manager)
    │
    ├─ Creates Registry
    ├─ Registers tools/prompts/resources
    ├─ Loads configuration
    ├─ Initializes handlers
    │
    ▼
Transport Layer
    │
    ├─ Selects transport (stdio/http/sse)
    ├─ Initializes transport
    ├─ Binds to address/streams
    │
    ▼
MCP SDK
    │
    └─ Starts MCP protocol handler
    │
    ▼
Server Running (Ready to accept requests)
```

### 4.2 Tool Call Request Flow

```
Client Request
    │
    ▼
Transport Layer
    │
    ├─ Receive message (stdio/http/sse)
    ├─ Parse request
    │
    ▼
Security Layer
    │
    ├─ Authenticate request
    ├─ Check rate limits
    ├─ Validate permissions
    │
    ▼
Validation Layer
    │
    ├─ Validate request schema
    ├─ Parse parameters
    ├─ Type checking
    │
    ▼
Handler Manager
    │
    ├─ Lookup tool in registry
    ├─ Create execution context
    ├─ Apply middleware (pre)
    │
    ▼
Tool Execution
    │
    ├─ Execute user handler
    ├─ Capture result/error
    ├─ Report progress (if applicable)
    │
    ▼
Handler Manager
    │
    ├─ Apply middleware (post)
    ├─ Format response
    ├─ Log execution
    │
    ▼
Transport Layer
    │
    ├─ Serialize response
    ├─ Send to client
    │
    ▼
Client receives result
```

### 4.3 Configuration Loading Flow

```
Start
    │
    ▼
Load from file (simplymcp.config.toml)
    │
    ├─ Parse TOML
    ├─ Validate with Pydantic
    │
    ▼
Merge with environment variables
    │
    ├─ SIMPLY_MCP_* env vars
    ├─ Override file config
    │
    ▼
Apply defaults
    │
    ├─ Fill missing values
    ├─ Set sensible defaults
    │
    ▼
Final validated configuration
```

---

## 5. Design Patterns

### 5.1 Creational Patterns

#### Factory Pattern
**Location**: `src/simply_mcp/core/server.py`

```python
class ServerFactory:
    @staticmethod
    def create(api_style: str, config: ServerConfig) -> SimplyMCPServer:
        """Create server based on API style"""
        if api_style == "decorator":
            return DecoratorServer(config)
        elif api_style == "functional":
            return FunctionalServer(config)
        # ...
```

**Usage**: Creating servers based on detected API style

#### Builder Pattern
**Location**: `src/simply_mcp/api/functional.py`

```python
mcp = (BuildMCPServer("my-server")
    .add_tool(add, description="Add numbers")
    .add_prompt(greet, description="Greet user")
    .configure(port=3000)
    .run())
```

**Usage**: Fluent interface for programmatic server building

### 5.2 Structural Patterns

#### Adapter Pattern
**Location**: `src/simply_mcp/transports/`

```python
class StdioTransport(Transport):
    """Adapts MCP SDK stdio to Simply-MCP interface"""

class HTTPTransport(Transport):
    """Adapts HTTP requests to MCP protocol"""
```

**Usage**: Adapting different transports to unified interface

#### Decorator Pattern
**Location**: `src/simply_mcp/api/decorator.py`

```python
@tool(description="Add two numbers")
def add(a: int, b: int) -> int:
    return a + b
```

**Usage**: Adding metadata to functions without modifying them

#### Facade Pattern
**Location**: `src/simply_mcp/__init__.py`

```python
# Simplified public API
from simply_mcp import BuildMCPServer, tool, prompt, resource
```

**Usage**: Providing simple interface to complex subsystems

### 5.3 Behavioral Patterns

#### Strategy Pattern
**Location**: `src/simply_mcp/transports/`

```python
class Transport(ABC):
    """Strategy interface for different transports"""

class StdioTransport(Transport):
    """Stdio strategy"""

class HTTPTransport(Transport):
    """HTTP strategy"""
```

**Usage**: Swappable transport implementations

#### Observer Pattern
**Location**: `src/simply_mcp/core/events.py` (future)

```python
server.on("tool_call", lambda event: log(event))
```

**Usage**: Event system for logging, metrics, debugging

#### Template Method Pattern
**Location**: `src/simply_mcp/transports/base.py`

```python
class Transport(ABC):
    def start(self):
        self._pre_start()
        self._do_start()  # Implemented by subclass
        self._post_start()
```

**Usage**: Defining skeleton of transport initialization

### 5.4 Architectural Patterns

#### Layered Architecture
- API Layer
- Core Layer
- Transport Layer
- MCP SDK Layer

#### Dependency Injection
```python
class SimplyMCPServer:
    def __init__(
        self,
        config: ServerConfig,
        registry: Registry = None,
        logger: Logger = None,
    ):
        self.registry = registry or Registry()
        self.logger = logger or get_logger(__name__)
```

#### Registry Pattern
```python
registry.register_tool("add", tool_config)
tool = registry.get_tool("add")
```

---

## 6. API Style Architecture

### 6.1 API Style Detection

```python
def detect_api_style(entry_point: Any) -> APIStyle:
    """
    Auto-detect which API style is being used

    Priority:
    1. Check for @mcp_server decorator → Decorator API
    2. Check for BuildMCPServer instance → Functional API
    3. Check for Protocol subclass → Interface API
    4. Fallback to default (Decorator)
    """
    if hasattr(entry_point, "__mcp_server__"):
        return APIStyle.DECORATOR
    elif isinstance(entry_point, BuildMCPServer):
        return APIStyle.FUNCTIONAL
    elif is_protocol_subclass(entry_point):
        return APIStyle.INTERFACE
    else:
        return APIStyle.DECORATOR  # Default
```

### 6.2 Unified Internal Representation

All API styles convert to a common internal format:

```python
@dataclass
class ToolDefinition:
    name: str
    description: str
    input_schema: dict
    handler: Callable
    metadata: dict

@dataclass
class ServerDefinition:
    name: str
    version: str
    tools: List[ToolDefinition]
    prompts: List[PromptDefinition]
    resources: List[ResourceDefinition]
    config: ServerConfig
```

---

## 7. Transport Architecture

### 7.1 Transport Abstraction

```python
class Transport(ABC):
    """Base class for all transports"""

    @abstractmethod
    async def start(self) -> None:
        """Start the transport"""

    @abstractmethod
    async def stop(self) -> None:
        """Stop the transport"""

    @abstractmethod
    async def send(self, message: Message) -> None:
        """Send a message"""

    @abstractmethod
    async def receive(self) -> Message:
        """Receive a message"""
```

### 7.2 Transport Selection

```python
def select_transport(config: TransportConfig) -> Transport:
    transports = {
        "stdio": StdioTransport,
        "http": HTTPTransport,
        "sse": SSETransport,
    }
    transport_class = transports[config.type]
    return transport_class(config)
```

---

## 8. Security Architecture

### 8.1 Security Layers

```
Request
    │
    ▼
┌─────────────────────────┐
│  Transport Layer TLS    │ (HTTPS/TLS)
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  Authentication         │ (OAuth/API Key/JWT)
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  Authorization          │ (Permissions)
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  Rate Limiting          │ (Token Bucket)
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  Input Validation       │ (Pydantic)
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  Handler Execution      │
└─────────────────────────┘
```

### 8.2 Rate Limiting Architecture

```python
class RateLimiter:
    """Token bucket rate limiter"""

    def __init__(self, rate: int, burst: int):
        self.rate = rate  # tokens per minute
        self.burst = burst  # max burst size
        self.buckets = {}  # client_id -> bucket

    async def check_limit(self, client_id: str) -> bool:
        bucket = self.buckets.setdefault(client_id, TokenBucket(self.rate, self.burst))
        return await bucket.consume(1)
```

---

## 9. Error Handling Architecture

### 9.1 Error Hierarchy

```
SimplyMCPError (base)
    │
    ├─ ConfigurationError
    │   ├─ InvalidConfigError
    │   └─ MissingConfigError
    │
    ├─ ValidationError
    │   ├─ SchemaValidationError
    │   └─ TypeValidationError
    │
    ├─ TransportError
    │   ├─ ConnectionError
    │   └─ MessageError
    │
    ├─ HandlerError
    │   ├─ HandlerNotFoundError
    │   ├─ HandlerExecutionError
    │   └─ HandlerTimeoutError
    │
    └─ SecurityError
        ├─ AuthenticationError
        ├─ AuthorizationError
        └─ RateLimitError
```

### 9.2 Error Flow

```
Exception Raised
    │
    ▼
Handler Manager
    │
    ├─ Capture exception
    ├─ Log error with context
    ├─ Determine error type
    │
    ▼
Error Formatter
    │
    ├─ Format for transport
    ├─ Sanitize sensitive info
    ├─ Add error code
    │
    ▼
Transport Layer
    │
    ├─ Send error response
    │
    ▼
Client receives error
```

---

## 10. Extension Points

### 10.1 Custom Transport

```python
from simply_mcp.transports import Transport

class WebSocketTransport(Transport):
    async def start(self):
        # Implementation
        pass
```

### 10.2 Custom Middleware

```python
from simply_mcp.handlers import Middleware

class LoggingMiddleware(Middleware):
    async def process_request(self, request, handler):
        log.info(f"Request: {request}")
        response = await handler(request)
        log.info(f"Response: {response}")
        return response
```

### 10.3 Custom Validators

```python
from simply_mcp.validation import Validator

class CustomValidator(Validator):
    def validate(self, value, schema):
        # Custom validation logic
        pass
```

---

## 11. Deployment Architecture

### 11.1 Standalone Executable

```
PyInstaller/Nuitka
    │
    ├─ Bundle Python interpreter
    ├─ Bundle dependencies
    ├─ Bundle user code
    │
    ▼
Single executable
    │
    └─ simply-mcp-server
```

### 11.2 Container Deployment

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY src/ src/
CMD ["simply-mcp", "run", "server.py"]
```

### 11.3 Process Model

```
┌─────────────────────────────┐
│     Main Process            │
│                             │
│  ┌─────────────────────┐   │
│  │  Server Thread      │   │
│  └─────────────────────┘   │
│                             │
│  ┌─────────────────────┐   │
│  │  Transport Thread   │   │
│  └─────────────────────┘   │
│                             │
│  ┌─────────────────────┐   │
│  │  Worker Pool        │   │
│  │  (for handlers)     │   │
│  └─────────────────────┘   │
└─────────────────────────────┘
```

---

## Appendix: Architectural Decision Records (ADRs)

### ADR-001: Use Src Layout

**Status**: Accepted
**Decision**: Use src/ layout for package structure
**Rationale**:
- Prevents accidental imports from working directory
- Ensures tests run against installed package
- Industry standard for modern Python projects

### ADR-002: Use Pydantic for Validation

**Status**: Accepted
**Decision**: Use Pydantic v2 for all validation and configuration
**Rationale**:
- Already used by MCP SDK
- Excellent type safety and validation
- JSON Schema generation
- Good performance

### ADR-003: Use Click for CLI

**Status**: Accepted
**Decision**: Use Click instead of argparse
**Rationale**:
- Better UX for complex CLIs
- Nested commands support
- Rich integration for beautiful output
- Decorator-based API

### ADR-004: Async by Default

**Status**: Accepted
**Decision**: Use async/await for all I/O operations
**Rationale**:
- MCP SDK is async-first
- Better performance for I/O-bound operations
- Consistent with TypeScript version (Promise-based)
- Enables concurrent request handling

### ADR-005: Multiple API Styles

**Status**: Accepted
**Decision**: Support Decorator, Functional, and Interface APIs
**Rationale**:
- Flexibility for different use cases
- Match simply-mcp-ts feature set
- Cater to different developer preferences
- Enable gradual adoption

---

**End of Architecture Document**
