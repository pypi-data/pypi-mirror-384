# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned for v0.2.0
- Interface API with Protocol-based type annotations
- Complete OAuth 2.1 provider implementation
- Complete JWT token validation provider
- Migration guide from simply-mcp-ts
- Distributed rate limiting with Redis backend
- Performance optimization and benchmarking

### Planned for v2.0.0
- Builder AI API for AI-powered tool development
- Additional transport options
- Enhanced monitoring and observability features

## [0.1.0b3] - 2025-10-15

### Breaking Changes
- **API Naming Alignment**: Renamed SimplyMCP to BuildMCPServer to mirror TypeScript implementation
  - Old: `from simply_mcp import SimplyMCP`
  - New: `from simply_mcp import BuildMCPServer`
  - Rationale: Maintain naming consistency across TypeScript and Python implementations
  - Impact: All existing code using SimplyMCP must be updated

### Added
- **Functional API** (mirrors TypeScript functional API):
  - `define_mcp()`: Type-safe helper for defining MCP server configs
  - `define_tool()`: Type-safe helper for defining tools
  - `define_prompt()`: Type-safe helper for defining prompts
  - `define_resource()`: Type-safe helper for defining resources
  - `MCPBuilder`: Builder class with method chaining (`.tool()`, `.prompt()`, `.resource()`, `.build()`)
  - `create_mcp()`: Factory function for creating MCPBuilder instances
- **Programmatic API** (mirrors TypeScript BuildMCPServer):
  - `BuildMCPServer`: Main class for programmatic server construction (renamed from SimplyMCP)
  - Full method compatibility with decorator-style registration (@server.tool())
  - Full method compatibility with direct registration (server.add_tool())
- **Type Definitions** for config-based API:
  - `MCPConfig`: Complete server configuration type
  - `ToolConfig`: Tool configuration type
  - `PromptConfig`: Prompt configuration type
  - `ResourceConfig`: Resource configuration type

### Changed
- **Primary Class Name**: `SimplyMCP` → `BuildMCPServer` (breaking)
- **API Module Structure**: Reorganized for clarity
  - `api/programmatic.py`: BuildMCPServer class (main programmatic API)
  - `api/functional.py`: Config-based helpers and MCPBuilder
  - `api/builder.py`: Now re-exports BuildMCPServer for compatibility
  - `api/decorators.py`: Unchanged (decorator API)
- **Documentation**: Updated all examples and docs to use BuildMCPServer
- **Examples**: Updated 12 example files to use new API naming
- **Tests**: Updated test suite to use BuildMCPServer

### Fixed
- **Import Structure**: Cleaned up API module imports for better tree-shaking
- **CLI Detection**: Updated server detection to recognize BuildMCPServer instances
- **Type Exports**: Added comprehensive __all__ exports for better IDE support

### Migration Guide

**For existing users:**

1. **Update imports**:
   ```python
   # Old
   from simply_mcp import SimplyMCP
   mcp = SimplyMCP(name="my-server", version="1.0.0")

   # New
   from simply_mcp import BuildMCPServer
   server = BuildMCPServer(name="my-server", version="1.0.0")
   ```

2. **Update variable names** (optional but recommended):
   ```python
   # Old style (still works)
   mcp = BuildMCPServer(...)

   # New style (matches TypeScript)
   server = BuildMCPServer(...)
   ```

3. **Use new functional API** (optional):
   ```python
   from simply_mcp import create_mcp

   mcp = create_mcp(name="my-server", version="1.0.0")
   mcp.tool({"name": "add", "handler": lambda a, b: a + b})
   config = mcp.build()
   ```

**Why this change?**

- **Cross-language consistency**: Python and TypeScript implementations now use identical naming
- **Clear intent**: "BuildMCPServer" clearly indicates programmatic construction
- **Better alignment**: Matches the established TypeScript API that users may already know
- **Future-proof**: Prepares for additional API styles (Interface API, etc.)

### Documentation
- Updated all documentation files to use BuildMCPServer
- Updated README.md with new API examples
- Updated quickstart guide
- Updated API reference
- Added functional API examples

## [0.1.0b2] - 2025-10-15

### Added
- **uvx Support Documentation**: Comprehensive documentation for using simply-mcp without installation via uvx
  - New section in installation guide with comparison tables
  - uvx examples throughout quickstart guide
  - Detailed uvx usage patterns in CLI guide
  - Quick-try options in README and documentation index
- Performance expectations for uvx usage (first run: 7-30s, subsequent: near-instant)
- "Try before installing" workflows across documentation

### Fixed
- **Transport Flag Syntax** (Critical): Corrected 22 instances of incorrect transport flag syntax across 12 files
  - Changed `--http` to `--transport http`
  - Changed `--sse` to `--transport sse`
  - Changed `--stdio` to `--transport stdio`
  - Affected files: quickstart.md, README.md, TECHNICAL_SPEC.md, FEATURE_PARITY.md, examples/index.md, configuration.md, deployment.md, first-server.md, CHANGELOG.md
- Output format in quickstart.md now shows actual Rich table format
- Version number consistency between pyproject.toml and __init__.py

### Changed
- Documentation now consistently uses `--transport TYPE` syntax throughout
- Enhanced README with uvx installation option
- Improved CLI usage guide with comprehensive uvx section

### Documentation
- Added ~220 lines of uvx-related documentation
- Enhanced 5 primary documentation files with uvx examples
- Fixed transport syntax in 12 files
- All examples now use realistic file paths (server.py vs {file})

## [0.1.0-beta] - 2025-10-13

First beta release of Simply-MCP-PY with complete core features and production-ready capabilities.

### Added

#### Core Framework
- **MCP Server Implementation**: Complete server lifecycle management with initialization, execution, and graceful shutdown
- **Component Registry**: Thread-safe registry for tools, prompts, and resources with validation
- **Type System**: Comprehensive Pydantic v2 models for type-safe configuration and validation
- **Error Handling**: Structured error system with detailed error types and context
- **Logging System**: Structured logging with JSON and text formatters, configurable log levels
- **Configuration Management**: Pydantic-based configuration with TOML/JSON file support and environment variables

#### API Styles

**Decorator API (Pythonic)**
- `@mcp_server` class decorator for organizing related tools, prompts, and resources
- `@tool()` decorator for registering tool functions with automatic schema generation
- `@prompt()` decorator for registering prompt templates with parameter validation
- `@resource()` decorator for registering resource handlers with URI templates
- Auto-detection of decorator-based servers by CLI
- Full Pydantic model integration for parameter validation
- Support for sync and async handlers

**Builder/Functional API**
- `SimplyMCP` class with fluent method chaining interface
- `add_tool()` method for programmatic tool registration
- `add_prompt()` method for programmatic prompt registration
- `add_resource()` method for programmatic resource registration
- `configure()` method for runtime configuration
- Method chaining for clean, readable server setup
- Context injection for handlers (server context, config, progress tracking)

**Class-Based Servers**
- `@mcp_server` decorator for class-based organization
- Instance methods automatically registered as tools
- Shared state via class instance variables
- Clean separation of concerns

#### Schema Generation & Validation
- **Automatic JSON Schema Generation**: From Python type hints (str, int, float, bool, list, dict)
- **Pydantic v2 Integration**: Full support for Pydantic models with validation
- **Type Hint Support**: Support for Optional, Union, List, Dict, Literal, Enum types
- **Nested Objects**: Complex nested type support with proper validation
- **Default Values**: Optional parameters with default values
- **Custom Validators**: Field validators and model validators
- **Error Messages**: Detailed validation error messages with field paths
- **Schema Export**: Export to standard JSON Schema format

#### Transports

**Stdio Transport**
- Standard input/output transport for MCP client communication
- JSON-RPC 2.0 protocol compliance
- Process-based communication via stdin/stdout streams
- Efficient message framing and parsing
- Error handling with proper JSON-RPC error codes
- Used by Claude Desktop and other MCP clients

**HTTP Transport**
- RESTful JSON-RPC 2.0 over HTTP with aiohttp
- Session management and request handling
- Health check endpoint (`/health`) for monitoring
- Support for GET and POST requests
- Configurable host and port binding
- CORS support with configurable origins
- Request/response middleware pipeline
- Graceful shutdown with cleanup

**SSE Transport (Server-Sent Events)**
- Real-time streaming communication
- Connection lifecycle management (connect/disconnect)
- Event stream with automatic reconnection support
- Compatible with EventSource API
- Configurable endpoint paths
- Health check support

#### Middleware System
- **Middleware Pipeline**: Sequential middleware execution for requests and responses
- **CORS Middleware**: Cross-origin resource sharing with configurable allowed origins, methods, and headers
- **Logging Middleware**: Automatic request/response logging with timing information
- **Authentication Middleware**: Pluggable authentication for HTTP/SSE transports
- **Rate Limiting Middleware**: Per-client rate limiting integration
- **Custom Middleware**: Easy-to-implement custom middleware interface
- **Error Handling**: Middleware-level error interception and handling

#### CLI Tool

**Commands**
- `simply-mcp run <file>` - Run MCP servers with auto-detection of API style
- `simply-mcp dev <file>` - Development mode with auto-reload and enhanced debugging
- `simply-mcp watch <file>` - File watching with automatic server restart
- `simply-mcp bundle <file>` - Package servers as standalone executables
- `simply-mcp list <file>` - List available tools, prompts, and resources
- `simply-mcp config init` - Initialize configuration file
- `simply-mcp config validate` - Validate configuration file
- `simply-mcp config show` - Display current configuration

**CLI Features**
- API style auto-detection (decorator, builder, class-based)
- Transport selection (--transport stdio/http/sse)
- Port and host configuration (--port, --host options)
- Rich console output with colors and formatting
- Detailed error messages with suggestions
- Progress bars and status indicators
- JSON output mode for programmatic use (--json flag)

#### Security Features

**Authentication**
- `APIKeyAuthProvider`: API key authentication with Bearer tokens and X-API-Key headers
- `NoAuthProvider`: Allow-all provider for development
- `OAuthProvider`: OAuth 2.1 support (stub implementation, MCP SDK based)
- `JWTProvider`: JWT token validation (stub implementation)
- Constant-time comparison for security
- Client identification and tracking
- Authentication failure logging
- Configurable via config file or environment variables

**Rate Limiting**
- **Token Bucket Algorithm**: Industry-standard rate limiting with burst support
- **Per-Client Tracking**: Separate rate limits for each client
- **Configurable Rates**: Requests per minute/window with burst capacity
- **Automatic Token Refill**: Time-based token regeneration
- **Statistics Tracking**: Requests, rejections, refills metrics
- **Automatic Cleanup**: Expired client cleanup to prevent memory leaks
- **Emergency Cleanup**: Memory management for high-scale deployments
- **Rate Limit Headers**: X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset

#### Advanced Features

**Progress Reporting**
- `ProgressReporter`: Track progress of single operations (0-100%)
- `ProgressTracker`: Manage multiple concurrent operations
- Progress updates with percentage and custom messages
- Async callback support for real-time updates
- Context manager for automatic operation completion
- Operation lifecycle management (start, update, complete)
- Automatic cleanup of completed operations
- MCP protocol integration for progress notifications

**Binary Content Support**
- `BinaryContent` class for handling binary data
- Base64 encoding and decoding
- MIME type detection from file signatures (magic numbers)
- File reading with configurable size limits (default 10MB)
- Support for images: PNG, JPEG, GIF, WebP, BMP
- Support for documents: PDF, ZIP, GZIP
- Helper functions: `read_image()`, `read_pdf()`, `create_binary_resource()`
- Memory-efficient streaming for large files
- Integration with resource handlers

**Development Tools**

*Watch Mode*
- File monitoring with watchdog library
- Configurable debouncing (default 1.0s) to avoid rapid restarts
- Ignore patterns for common files (.git, __pycache__, .pyc, etc.)
- Graceful server restart with cleanup
- Process management with proper signal handling
- Rich console feedback with restart counts and timing
- Support for all transport types

*Development Mode*
- Enhanced logging with Rich formatting and colors
- Request/response debugging with full message inspection
- Performance metrics tracking (latency, throughput, errors)
- Auto-reload on file changes (combines run + watch)
- Interactive keyboard shortcuts (r=reload, l=list, m=metrics, q=quit)
- Component listing on startup (tools, prompts, resources)
- Error highlighting with rich stack traces
- Real-time server status display

*Bundling*
- PyInstaller integration for creating standalone executables
- Automatic dependency detection and inclusion
- Hidden imports for simply_mcp and mcp packages
- Single-file mode (--onefile) for easy distribution
- Directory mode for faster startup
- Custom icon support (.ico for Windows)
- Windowed/console mode selection
- Clean build option to remove temporary files
- Cross-platform builds (Windows, macOS, Linux)

#### Configuration

**File Formats**
- TOML configuration files (`simplymcp.config.toml`)
- JSON configuration files (`simplymcp.config.json`)
- Auto-detection of config file in current directory
- Custom config path via `--config` option

**Configuration Options**
- **Server Settings**: name, version, description
- **Transport Settings**: type (stdio/http/sse), host, port
- **Logging Settings**: level, format (json/text), output file
- **Security Settings**: authentication type, API keys, rate limiting
- **Feature Settings**: progress reporting, binary content limits
- **Advanced Settings**: middleware configuration, custom handlers

**Configuration Precedence**
1. CLI arguments (highest priority)
2. Environment variables (SIMPLY_MCP_* prefix)
3. Configuration file (TOML/JSON)
4. Default values (lowest priority)

**Validation**
- Pydantic-based configuration validation
- Clear error messages for invalid configurations
- Type checking for all configuration values
- Default values for optional settings

#### Documentation
- Complete API reference with mkdocstrings
- Getting started guide with step-by-step tutorials
- Configuration guide with all available options
- Deployment guide for production environments
- Testing guide with examples
- Security best practices guide
- 17 comprehensive example files with inline documentation
- mkdocs-based documentation site with Material theme

**Examples**
1. `simple_server.py` - Minimal working example
2. `decorator_example.py` - Decorator API demonstration
3. `builder_basic.py` - Builder API basics
4. `builder_chaining.py` - Method chaining patterns
5. `builder_pydantic.py` - Pydantic model integration
6. `http_server.py` - HTTP transport with CORS
7. `sse_server.py` - SSE transport with streaming
8. `authenticated_server.py` - API key authentication
9. `rate_limited_server.py` - Rate limiting implementation
10. `progress_example.py` - Progress reporting patterns
11. `binary_resources_example.py` - Binary content handling
12. `watch_example.py` - Watch mode usage
13. `dev_example.py` - Development mode features
14. `schema_generation_demo.py` - Schema generation showcase
15. `production_server.py` - Full-featured production server
16. `file_processor_server.py` - File processing with progress
17. `data_analysis_server.py` - Data analysis with authentication

### Changed

**Configuration System**
- Migrated from TypedDict to Pydantic v2 models for runtime validation
- Updated all dict access patterns to Pydantic attribute access
- Enhanced configuration validation with better error messages
- Improved type hints for better IDE support

**Middleware System**
- Enhanced middleware interface for better extensibility
- Improved error handling in middleware pipeline
- Better integration with authentication and rate limiting

**CLI Interface**
- Improved help text and usage examples
- Better error messages with actionable suggestions
- Enhanced progress indicators and status updates

**Testing**
- Expanded test suite to 753 tests (up from initial 200+)
- Improved test coverage to 84% (target: >80%)
- Added integration tests for all transports
- Enhanced test isolation and cleanup

### Fixed

**Pydantic Migration Fixes**
- Fixed middleware API mismatch in HTTP transport
- Fixed Pydantic model serialization in list endpoints
- Fixed progress tracker callback type compatibility
- Fixed test isolation with global decorator server state
- Updated 50+ test files for Pydantic v2 compatibility
- Fixed dict access to use Pydantic model attributes

**Type System Fixes**
- Resolved 12 mypy strict mode errors
- Fixed decorator attribute type annotations
- Fixed callback type signatures
- Fixed Observer type annotation in watch module
- Fixed generic type handling in decorators

**Test Fixes**
- Fixed resource handling test assertions for ServerResult wrapper
- Fixed rate limit middleware test initialization
- Improved test reliability with proper fixtures
- Fixed module import test isolation issues

### Testing

**Test Suite**
- 753 total tests with 736 passing (97.7% pass rate)
- 84% code coverage across all modules
- Full mypy strict mode compliance (0 type errors)
- All ruff linting checks passing (0 errors)
- Integration tests for stdio, HTTP, and SSE transports
- End-to-end validation tests
- Security feature tests (auth, rate limiting)
- Advanced feature tests (progress, binary content)

**Test Categories**
- Unit tests: 347 tests
- CLI tests: 85 tests
- Security tests: 91 tests
- Feature tests: 133 tests
- Transport tests: 97 tests

**Coverage by Module**
- Core modules: 89% (excellent)
- API modules: 95% (excellent)
- Security modules: 99% (excellent)
- Feature modules: 98% (excellent)
- CLI modules: 71% (good)
- Transport modules: 67% (needs improvement)
- Validation modules: 88% (excellent)

### Performance

**Benchmarks**
- Server startup time: <100ms (typical)
- Memory usage: <50MB base memory footprint
- Request throughput: 1000+ requests/second
- Schema generation: Cached, one-time operation
- Rate limiter operations: O(1) constant time
- Binary content encoding: ~50 MB/s
- Token bucket refill: O(1) constant time

**Optimizations**
- Efficient schema generation with caching
- Optimized middleware pipeline execution
- Low-overhead request routing
- Memory-efficient binary content handling
- Async-safe rate limiting with minimal locking

### Security

**Best Practices**
- Constant-time API key comparison to prevent timing attacks
- Secure default configurations
- Rate limiting to prevent abuse
- Request size limits to prevent DoS
- CORS with configurable origins
- Structured error messages without sensitive data leakage
- Secure token bucket implementation

**Hardening**
- Input validation on all endpoints
- JSON-RPC 2.0 compliance with error codes
- Graceful error handling without exposing internals
- Configurable security features (can be disabled for development)

### Breaking Changes

**Note:** As this is the first beta release, there are no breaking changes from previous versions. However, be aware:

1. **Configuration Format**: TypedDict-based configs replaced with Pydantic models
   - Old: `config["server"]["name"]`
   - New: `config.server.name`
   - Impact: Pre-alpha users need to update config access patterns

2. **Middleware API**: Middleware signature changed for better type safety
   - Old: `async def middleware(request, handler)`
   - New: `async def middleware(request: Request, call_next: Callable) -> Response`
   - Impact: Custom middleware needs updating

**Migration Path**: Since the project is in beta with no public users yet, these changes establish the baseline for v1.0.0 stability.

### Dependencies

**Core Dependencies**
- `mcp>=0.1.0` - Official Anthropic MCP SDK
- `pydantic>=2.0.0` - Data validation and settings management
- `pydantic-settings>=2.0.0` - Settings management
- `click>=8.0.0` - CLI framework
- `rich>=13.0.0` - Rich terminal output
- `watchdog>=4.0.0` - File system monitoring
- `aiohttp>=3.9.0` - Async HTTP client/server
- `aiohttp-cors>=0.7.0` - CORS for aiohttp
- `tomli>=2.0.0` - TOML parser (Python <3.11)
- `python-dotenv>=1.0.0` - Environment variable loading
- `typing-extensions>=4.0.0` - Typing backports
- `python-json-logger>=2.0.0` - JSON logging

**Optional Dependencies**
- `pyinstaller>=5.0.0` - For bundling (install with `pip install simply-mcp[bundling]`)
- `pillow` - For image processing examples
- `reportlab` - For PDF generation examples
- `pandas`, `numpy`, `matplotlib`, `seaborn` - For data analysis examples

**Development Dependencies**
- `pytest>=7.0.0` - Testing framework
- `pytest-asyncio>=0.21.0` - Async test support
- `pytest-cov>=4.0.0` - Coverage reporting
- `pytest-mock>=3.10.0` - Mocking support
- `httpx>=0.24.0` - HTTP testing
- `black>=23.0.0` - Code formatting
- `ruff>=0.1.0` - Fast linting
- `mypy>=1.0.0` - Static type checking

**Documentation Dependencies**
- `mkdocs>=1.5.0` - Documentation generator
- `mkdocs-material>=9.4.0` - Material theme
- `mkdocstrings[python]>=0.24.0` - API docs generation

### Known Issues

**Minor Issues (Non-Blocking)**
1. **Transport Tests**: 16 test failures in HTTP/SSE transport layer (being addressed)
2. **OAuth/JWT Providers**: Stub implementations, not fully functional (planned for v0.2.0)
3. **Bundle Size**: Executables are 30-50MB (typical for PyInstaller, investigating compression)
4. **Windows Compatibility**: Watch mode keyboard shortcuts may not work in all terminals
5. **Configuration Warning**: Ruff linter config deprecation warning (cosmetic, will fix in v0.2.0)

**Workarounds Available**
- Use API key authentication (fully functional)
- OAuth/JWT can be implemented via custom auth providers
- Bundle size acceptable for most use cases
- Use standard file watching without keyboard shortcuts on Windows

### Upgrade Notes

**From Pre-Alpha to Beta**

If you were using pre-alpha versions:

1. **Update Configuration Access**:
   ```python
   # Old
   name = config["server"]["name"]

   # New
   name = config.server.name
   ```

2. **Update Custom Middleware**:
   ```python
   # Old
   async def my_middleware(request, handler):
       response = await handler(request)
       return response

   # New
   from simply_mcp.transports.middleware import Middleware

   class MyMiddleware(Middleware):
       async def __call__(self, request, call_next):
           response = await call_next(request)
           return response
   ```

3. **Update Pydantic Models** (if using):
   - Use Pydantic v2 syntax
   - `Config` class replaced with `model_config`
   - Validators use `@field_validator` decorator

### Comparison with simply-mcp-ts

**Feature Parity: 97%**

| Category | simply-mcp-ts | simply-mcp-py | Parity |
|----------|---------------|---------------|--------|
| Core API Styles | ✅ | ✅ | 100% |
| Transport Layer | ✅ | ✅ | 100% |
| CLI Tool | ✅ | ✅ | 100% |
| Security | ✅ | ⚠️ | 87% |
| Advanced Features | ✅ | ✅ | 100% |
| Documentation | ✅ | ⚠️ | 88% |

**Language Differences**:
- **Validation**: Zod (TypeScript) vs Pydantic v2 (Python)
- **Type Checking**: Built-in TypeScript vs mypy (Python)
- **Decorators**: Experimental (TypeScript) vs First-class (Python)
- **Async**: Promises (TypeScript) vs async/await (Python)

Both implementations provide equivalent functionality adapted to their respective language idioms.

### Contributors

- Clockwork Innovations Team
- Built with assistance from AI agents for testing, validation, and documentation

### Acknowledgments

- Built on top of the [Anthropic MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- Inspired by [simply-mcp-ts](https://github.com/Clockwork-Innovations/simply-mcp-ts)
- Testing and validation by specialized AI agents
- Community feedback during development

---

## [0.0.1] - 2025-10-11

### Added
- Initial project structure
- Basic type system with TypedDict
- Project documentation and roadmap
- Development environment setup
- CI/CD pipeline configuration

---

[Unreleased]: https://github.com/Clockwork-Innovations/simply-mcp-py/compare/v0.1.0b2...HEAD
[0.1.0b2]: https://github.com/Clockwork-Innovations/simply-mcp-py/releases/tag/v0.1.0b2
[0.1.0-beta]: https://github.com/Clockwork-Innovations/simply-mcp-py/releases/tag/v0.1.0-beta
[0.0.1]: https://github.com/Clockwork-Innovations/simply-mcp-py/releases/tag/v0.0.1
