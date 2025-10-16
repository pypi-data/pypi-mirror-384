# Simply-MCP Examples

This directory contains comprehensive examples demonstrating the features and capabilities of the Simply-MCP framework. Examples range from basic "Hello World" servers to production-ready applications with authentication, rate limiting, and advanced features.

## Table of Contents

- [Quick Start](#quick-start)
- [Example Categories](#example-categories)
- [Feature Matrix](#feature-matrix)
- [Getting Started](#getting-started)
- [Development Tips](#development-tips)
- [Production Examples](#production-examples)

## Quick Start

```bash
# Install Simply-MCP with all optional dependencies
pip install simply-mcp[http,security]

# Run a basic example
python examples/simple_server.py

# Run with development mode (auto-reload)
simply-mcp dev examples/simple_server.py

# Run a production server
python examples/production_server.py
```

## Example Categories

### 1. Basic Examples

**Purpose:** Learn the fundamentals of Simply-MCP

#### [`simple_server.py`](./simple_server.py)
- **Level:** Beginner
- **Features:** Basic tool registration, simple decorator usage
- **Use Case:** Getting started, learning basics
- **Run:** `python examples/simple_server.py`

#### [`decorator_example.py`](./decorator_example.py)
- **Level:** Beginner
- **Features:** Decorator API (@tool, @prompt, @resource)
- **Use Case:** Pythonic server development
- **Run:** `python examples/decorator_example.py`

#### [`builder_basic.py`](./builder_basic.py)
- **Level:** Beginner
- **Features:** Builder API pattern
- **Use Case:** Fluent server construction
- **Run:** `python examples/builder_basic.py`

### 2. API Style Examples

**Purpose:** Explore different ways to build servers

#### [`builder_chaining.py`](./builder_chaining.py)
- **Level:** Intermediate
- **Features:** Method chaining, fluent API
- **Use Case:** Clean, readable server configuration
- **Run:** `python examples/builder_chaining.py`

#### [`builder_pydantic.py`](./builder_pydantic.py)
- **Level:** Intermediate
- **Features:** Pydantic models for validation
- **Use Case:** Type-safe data handling
- **Run:** `python examples/builder_pydantic.py`

### 3. Advanced Feature Examples

**Purpose:** Showcase Phase 4 advanced features

#### [`authenticated_server.py`](./authenticated_server.py)
- **Level:** Intermediate
- **Features:** API key authentication
- **Use Case:** Secure API access
- **Run:** `python examples/authenticated_server.py`
- **Test:**
  ```bash
  curl -X POST http://localhost:8000/mcp \
    -H "Authorization: Bearer test-key-12345" \
    -H "Content-Type: application/json" \
    -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}'
  ```

#### [`rate_limited_server.py`](./rate_limited_server.py)
- **Level:** Intermediate
- **Features:** Rate limiting, burst capacity
- **Use Case:** API protection, abuse prevention
- **Run:** `python examples/rate_limited_server.py`
- **Test:** `python examples/rate_limited_server.py --test`

#### [`progress_example.py`](./progress_example.py)
- **Level:** Intermediate
- **Features:** Progress reporting for long operations
- **Use Case:** Batch processing, long-running tasks
- **Run:** `python examples/progress_example.py`

#### [`binary_resources_example.py`](./binary_resources_example.py)
- **Level:** Intermediate
- **Features:** Binary content, image/PDF handling
- **Use Case:** File serving, media content
- **Run:** `python examples/binary_resources_example.py`

### 4. Transport Examples

**Purpose:** Different transport mechanisms

#### [`http_server.py`](./http_server.py)
- **Level:** Intermediate
- **Features:** HTTP transport, CORS
- **Use Case:** Web-accessible MCP servers
- **Run:** `python examples/http_server.py`

#### [`sse_server.py`](./sse_server.py)
- **Level:** Advanced
- **Features:** Server-Sent Events, streaming
- **Use Case:** Real-time updates
- **Run:** `python examples/sse_server.py`

### 5. Production Examples

**Purpose:** Production-ready servers with all features

#### [`production_server.py`](./production_server.py) ⭐
- **Level:** Advanced
- **Features:**
  - API key authentication
  - Rate limiting (60 req/min)
  - Progress reporting
  - Binary content support
  - Structured logging
  - Health checks
  - Complete error handling
- **Use Case:** Production deployments
- **Run:** `python examples/production_server.py`
- **Documentation:** See file header for detailed usage

#### [`file_processor_server.py`](./file_processor_server.py) ⭐
- **Level:** Advanced
- **Features:**
  - Image processing (resize, convert, thumbnail)
  - PDF generation
  - Binary uploads/downloads
  - Progress tracking
  - Authentication & rate limiting
- **Use Case:** File processing services, media APIs
- **Run:** `python examples/file_processor_server.py`
- **Requirements:** `pip install pillow reportlab` (optional but recommended)

#### [`data_analysis_server.py`](./data_analysis_server.py) ⭐
- **Level:** Advanced
- **Features:**
  - CSV/JSON dataset loading
  - Statistical analysis
  - Data visualization (charts)
  - PDF report generation
  - Progress tracking
  - Prompt templates for analysis
- **Use Case:** Data science workflows, analytics APIs
- **Run:** `python examples/data_analysis_server.py`
- **Requirements:** `pip install pandas numpy matplotlib seaborn reportlab`

### 6. Utility Examples

#### [`schema_generation_demo.py`](./schema_generation_demo.py)
- **Level:** Intermediate
- **Features:** Automatic JSON Schema generation
- **Use Case:** Understanding type validation
- **Run:** `python examples/schema_generation_demo.py`

#### [`watch_example.py`](./watch_example.py)
- **Level:** Intermediate
- **Features:** File watching, auto-reload
- **Use Case:** Development workflow
- **Run:** `simply-mcp dev examples/watch_example.py`

## Feature Matrix

| Example | Auth | Rate Limit | Progress | Binary | HTTP | CORS | Logging | Production Ready |
|---------|------|------------|----------|--------|------|------|---------|------------------|
| simple_server.py | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ⚠️ | ❌ |
| decorator_example.py | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ⚠️ | ❌ |
| authenticated_server.py | ✅ | ❌ | ❌ | ❌ | ✅ | ✅ | ⚠️ | ⚠️ |
| rate_limited_server.py | ❌ | ✅ | ❌ | ❌ | ✅ | ✅ | ⚠️ | ⚠️ |
| progress_example.py | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ⚠️ | ❌ |
| binary_resources_example.py | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ⚠️ | ❌ |
| http_server.py | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ⚠️ | ⚠️ |
| **production_server.py** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **file_processor_server.py** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **data_analysis_server.py** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

**Legend:**
- ✅ Fully implemented
- ⚠️ Partially implemented or basic
- ❌ Not included

## Getting Started

### 1. Install Dependencies

```bash
# Minimal installation
pip install simply-mcp

# With HTTP support
pip install simply-mcp[http]

# With security features
pip install simply-mcp[security]

# All features
pip install simply-mcp[http,security]

# Optional for specific examples
pip install pillow reportlab pandas numpy matplotlib seaborn
```

### 2. Run Your First Server

```bash
# Run a basic example
python examples/simple_server.py

# Test with MCP Inspector
npx @anthropic-ai/mcp-inspector python examples/simple_server.py
```

### 3. Test HTTP Servers

```bash
# Start an HTTP server
python examples/http_server.py

# In another terminal, test with curl
curl http://localhost:8000/health

curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}'
```

### 4. Test Authenticated Servers

```bash
# Start authenticated server
python examples/authenticated_server.py

# Test with API key
curl -X POST http://localhost:8000/mcp \
  -H "Authorization: Bearer test-key-12345" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}'
```

## Development Tips

### Using Development Mode

Development mode enables auto-reload when you modify files:

```bash
# Basic dev mode
simply-mcp dev examples/simple_server.py

# With HTTP transport
simply-mcp dev examples/http_server.py --transport http --port 8000

# With custom configuration
simply-mcp dev examples/production_server.py --config config.json
```

### Debugging

```bash
# Enable debug logging
export MCP_LOG_LEVEL=DEBUG
python examples/production_server.py

# Use Python debugger
python -m pdb examples/simple_server.py
```

### Testing Tools

1. **MCP Inspector** (Official Anthropic tool):
   ```bash
   npx @anthropic-ai/mcp-inspector python examples/simple_server.py
   ```

2. **curl** (for HTTP servers):
   ```bash
   # Health check
   curl http://localhost:8000/health

   # List tools
   curl -X POST http://localhost:8000/mcp \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}'

   # Call a tool
   curl -X POST http://localhost:8000/mcp \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "greet", "arguments": {"name": "World"}}}'
   ```

3. **httpie** (more user-friendly):
   ```bash
   pip install httpie

   http http://localhost:8000/health
   http POST http://localhost:8000/mcp jsonrpc=2.0 id=1 method=tools/list
   ```

### Common Patterns

#### 1. Basic Tool Registration

```python
from simply_mcp import SimplyMCP

mcp = SimplyMCP(name="my-server", version="1.0.0")

@mcp.tool()
def my_tool(arg: str) -> str:
    """Tool description."""
    return f"Result: {arg}"

await mcp.initialize()
await mcp.run()
```

#### 2. With Progress Reporting

```python
from simply_mcp.core.types import ProgressReporter

@mcp.tool()
async def long_operation(
    items: int,
    progress: ProgressReporter | None = None,
) -> str:
    for i in range(items):
        if progress:
            await progress.update(
                percentage=(i + 1) / items * 100,
                message=f"Processing {i + 1}/{items}",
            )
        # Do work...
    return "Done"
```

#### 3. With Binary Content

```python
from simply_mcp.features.binary import BinaryContent

@mcp.resource(uri="file://{filename}")
def get_file(filename: str) -> BinaryContent:
    return BinaryContent.from_file(f"path/to/{filename}")

@mcp.tool()
def process_image(image_base64: str) -> dict:
    content = BinaryContent.from_base64(image_base64)
    # Process image...
    return {"size": content.size}
```

#### 4. Production Setup

```python
from simply_mcp import SimplyMCP
from simply_mcp.security.auth import APIKeyAuthProvider
from simply_mcp.security.rate_limiter import RateLimiter
from simply_mcp.transports.http import HTTPTransport

# Create server
mcp = SimplyMCP(name="prod-server", version="1.0.0")

# Register tools...

await mcp.initialize()

# Setup security
auth = APIKeyAuthProvider(api_keys=["your-secret-key"])
limiter = RateLimiter(requests_per_minute=60, burst_size=10)

# Create transport
transport = HTTPTransport(
    server=mcp.server,
    host="0.0.0.0",
    port=8000,
    cors_enabled=True,
    auth_provider=auth,
    rate_limiter=limiter,
)

await transport.start()
```

## Production Examples

The three production examples demonstrate complete, real-world applications:

### Production Server (`production_server.py`)

A general-purpose production server showcasing all Phase 4 features:

**Features:**
- Complete authentication system
- Rate limiting with configurable limits
- Progress reporting for batch operations
- Binary file uploads and downloads
- Structured JSON logging
- Health monitoring
- Data storage with TTL
- Multi-stage processing

**Use Cases:**
- API gateways
- Microservices
- File storage services
- General-purpose backends

**Configuration:**
```bash
export MCP_API_KEYS=key1,key2
export MCP_PORT=8000
export MCP_RATE_LIMIT_RPM=60
python examples/production_server.py
```

### File Processor Server (`file_processor_server.py`)

Specialized server for file and image processing:

**Features:**
- Image upload and storage
- Image resizing with aspect ratio
- Format conversion (PNG, JPEG, GIF, etc.)
- Thumbnail generation
- PDF document creation
- Progress tracking for processing
- Resource endpoints for downloads

**Use Cases:**
- Image processing services
- Media conversion APIs
- Document generation services
- Content management systems

**Dependencies:**
```bash
pip install pillow reportlab
```

### Data Analysis Server (`data_analysis_server.py`)

Server for data analysis and visualization:

**Features:**
- CSV/JSON dataset loading
- Statistical summaries
- Data visualization (bar, line, scatter, etc.)
- PDF report generation
- Prompt templates for analysis
- Progress tracking for computations

**Use Cases:**
- Data science platforms
- Analytics APIs
- Automated reporting systems
- Research data processing

**Dependencies:**
```bash
pip install pandas numpy matplotlib seaborn reportlab
```

## Environment Variables

Many examples support configuration via environment variables:

```bash
# Common variables
export MCP_LOG_LEVEL=INFO          # DEBUG, INFO, WARNING, ERROR
export MCP_HOST=0.0.0.0            # Bind address
export MCP_PORT=8000               # Port number

# Security
export MCP_API_KEYS=key1,key2      # API keys (comma-separated)
export MCP_RATE_LIMIT_RPM=60       # Rate limit (requests per minute)

# Features
export MCP_ENABLE_PROGRESS=true    # Enable progress reporting
export MCP_MAX_REQUEST_SIZE=10485760  # 10 MB
```

## Troubleshooting

### Common Issues

1. **"Module not found" errors:**
   ```bash
   # Install missing dependencies
   pip install simply-mcp[http,security]
   pip install pillow reportlab pandas matplotlib
   ```

2. **Port already in use:**
   ```bash
   # Use a different port
   export MCP_PORT=8001
   python examples/production_server.py
   ```

3. **Authentication failures:**
   ```bash
   # Check your API key matches
   curl -H "Authorization: Bearer YOUR_KEY" ...
   # Look for valid keys in server startup logs
   ```

4. **Rate limiting:**
   ```bash
   # Wait for rate limit window to reset
   # Or increase limits in code/environment
   export MCP_RATE_LIMIT_RPM=120
   ```

### Getting Help

- **Documentation:** [Simply-MCP Docs](https://github.com/yourusername/simply-mcp)
- **Issues:** [GitHub Issues](https://github.com/yourusername/simply-mcp/issues)
- **Examples:** Check example source code for inline comments
- **Logs:** Enable DEBUG logging for detailed information

## Next Steps

1. **Start Simple:** Begin with `simple_server.py`
2. **Learn Features:** Work through feature examples (auth, rate limiting, etc.)
3. **Study Production:** Examine the three production examples
4. **Build Your Own:** Adapt examples to your use case
5. **Deploy:** Use production patterns for real deployments

## Contributing Examples

Have a great example? Consider contributing:

1. Follow existing example patterns
2. Include comprehensive docstrings
3. Add usage instructions
4. Include test commands
5. Update this README
6. Submit a pull request

## License

All examples are provided under the same license as Simply-MCP. See the main project LICENSE file.
