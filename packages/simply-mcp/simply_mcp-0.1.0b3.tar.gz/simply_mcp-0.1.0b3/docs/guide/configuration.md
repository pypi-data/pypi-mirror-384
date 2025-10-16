# Configuration Guide

Comprehensive guide to configuring Simply-MCP-PY servers.

## Configuration Methods

Simply-MCP-PY supports multiple configuration methods:

1. **TOML Configuration Files**
2. **Environment Variables**
3. **Python Configuration Objects**
4. **Command-Line Arguments**

Configuration is loaded in this priority order (highest to lowest):
1. Command-line arguments
2. Environment variables
3. Configuration file
4. Defaults

## TOML Configuration

### Basic Configuration

Create `simplymcp.config.toml` in your project root:

```toml
[server]
name = "my-mcp-server"
version = "1.0.0"
description = "My awesome MCP server"

[transport]
type = "stdio"  # or "http", "sse"

[logging]
level = "INFO"
format = "json"
```

### Complete Configuration

Full configuration example with all options:

```toml
[server]
name = "my-mcp-server"
version = "1.0.0"
description = "Complete MCP server configuration"

[transport]
type = "http"  # "stdio", "http", or "sse"
host = "0.0.0.0"
port = 3000

[transport.http]
cors_enabled = true
cors_origins = ["http://localhost:3000", "https://example.com"]
session_enabled = true
session_timeout = 3600

[logging]
level = "INFO"  # "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
format = "json"  # "json" or "text"
output = "stdout"  # "stdout", "stderr", or file path

[security]
enable_auth = true
enable_rate_limiting = true

[security.auth]
type = "api_key"  # "api_key", "bearer", "basic"
api_keys = ["your-secret-key-1", "your-secret-key-2"]

[security.rate_limit]
enabled = true
requests_per_minute = 60
burst_size = 10

[features]
enable_progress = true
enable_binary = true

[development]
watch_enabled = false
auto_reload = false
debug = false
```

## Environment Variables

All configuration can be set via environment variables using the `SIMPLY_MCP_` prefix:

### Server Configuration

```bash
export SIMPLY_MCP_SERVER_NAME="my-server"
export SIMPLY_MCP_SERVER_VERSION="1.0.0"
export SIMPLY_MCP_SERVER_DESCRIPTION="My server"
```

### Transport Configuration

```bash
export SIMPLY_MCP_TRANSPORT_TYPE="http"
export SIMPLY_MCP_TRANSPORT_HOST="0.0.0.0"
export SIMPLY_MCP_TRANSPORT_PORT="3000"
```

### Logging Configuration

```bash
export SIMPLY_MCP_LOGGING_LEVEL="DEBUG"
export SIMPLY_MCP_LOGGING_FORMAT="json"
export SIMPLY_MCP_LOGGING_OUTPUT="stdout"
```

### Security Configuration

```bash
export SIMPLY_MCP_SECURITY_ENABLE_AUTH="true"
export SIMPLY_MCP_SECURITY_AUTH_TYPE="api_key"
export SIMPLY_MCP_SECURITY_AUTH_API_KEYS="key1,key2,key3"
export SIMPLY_MCP_SECURITY_RATE_LIMIT_ENABLED="true"
export SIMPLY_MCP_SECURITY_RATE_LIMIT_PER_MINUTE="60"
```

## Python Configuration

### Using Config Objects

```python
from simply_mcp import BuildMCPServer, ServerConfig, TransportConfig

config = ServerConfig(
    name="my-server",
    version="1.0.0",
    description="Programmatic configuration"
)

transport = TransportConfig(
    type="http",
    port=3000
)

mcp = BuildMCPServer(config=config, transport=transport)
```

### Direct Configuration

```python
from simply_mcp import BuildMCPServer

mcp = BuildMCPServer(
    name="my-server",
    version="1.0.0"
)

# Configure transport
mcp.configure(
    transport="http",
    port=3000,
    host="0.0.0.0"
)
```

## Command-Line Arguments

Override any configuration via CLI:

```bash
# Basic options
simply-mcp run server.py --name my-server --version 1.0.0

# Transport options
simply-mcp run server.py --transport http --port 3000 --host 0.0.0.0
simply-mcp run server.py --transport sse --port 8080

# Logging options
simply-mcp run server.py --log-level DEBUG --log-format text

# Development options
simply-mcp run server.py --watch --debug
```

## Configuration by Environment

### Development

```toml
[server]
name = "dev-server"
version = "0.1.0"

[logging]
level = "DEBUG"
format = "text"

[development]
watch_enabled = true
auto_reload = true
debug = true
```

### Production

```toml
[server]
name = "prod-server"
version = "1.0.0"

[transport]
type = "http"
host = "0.0.0.0"
port = 8080

[logging]
level = "WARNING"
format = "json"
output = "/var/log/mcp/server.log"

[security]
enable_auth = true
enable_rate_limiting = true

[security.auth]
type = "api_key"
# Load from environment variable
api_keys = ["${MCP_API_KEY}"]

[security.rate_limit]
enabled = true
requests_per_minute = 100
```

## .env Files

Use `.env` files for sensitive configuration:

```bash
# .env
SIMPLY_MCP_SECURITY_AUTH_API_KEYS="secret-key-1,secret-key-2"
SIMPLY_MCP_DATABASE_URL="postgresql://user:pass@localhost/db"
SIMPLY_MCP_SECRET_KEY="your-secret-key"
```

Load with python-dotenv:

```python
from dotenv import load_dotenv
from simply_mcp import BuildMCPServer

load_dotenv()  # Load .env file

mcp = BuildMCPServer(name="my-server")
```

## Configuration Validation

Validate your configuration:

```bash
simply-mcp config validate
```

Show current configuration:

```bash
simply-mcp config show
```

## Configuration Schema

For IDE autocomplete and validation, use the configuration schema:

```python
from simply_mcp.core.config import ServerConfig

# Your IDE will provide autocomplete
config = ServerConfig(
    name="my-server",
    version="1.0.0"
)
```

## Best Practices

### 1. Use Configuration Files for Defaults

Keep common settings in `simplymcp.config.toml`.

### 2. Use Environment Variables for Secrets

Never commit secrets to version control:

```bash
# Good
export SIMPLY_MCP_SECURITY_AUTH_API_KEYS="secret"

# Bad - in config file
api_keys = ["hardcoded-secret"]
```

### 3. Use CLI Arguments for Overrides

Override config for testing:

```bash
simply-mcp run server.py --port 3001 --log-level DEBUG
```

### 4. Environment-Specific Configs

Create different config files:

```
simplymcp.dev.toml
simplymcp.staging.toml
simplymcp.prod.toml
```

Load with environment variable:

```bash
export SIMPLY_MCP_CONFIG_FILE="simplymcp.prod.toml"
```

### 5. Validate Configuration

Always validate before deployment:

```bash
simply-mcp config validate --config simplymcp.prod.toml
```

## Configuration Examples

### Minimal Configuration

```toml
[server]
name = "minimal-server"
version = "1.0.0"
```

### HTTP Server with CORS

```toml
[server]
name = "web-server"
version = "1.0.0"

[transport]
type = "http"
port = 3000

[transport.http]
cors_enabled = true
cors_origins = ["http://localhost:3000"]
```

### Authenticated API Server

```toml
[server]
name = "api-server"
version = "1.0.0"

[transport]
type = "http"
port = 8080

[security]
enable_auth = true

[security.auth]
type = "api_key"
api_keys = ["${API_KEY_1}", "${API_KEY_2}"]

[logging]
level = "INFO"
format = "json"
```

## Next Steps

- [Deployment Guide](deployment.md) - Deploy your configured server
- [Testing Guide](testing.md) - Test different configurations
- [API Reference](../api/core/config.md) - Configuration API details
