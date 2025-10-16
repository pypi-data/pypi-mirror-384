# Installation

This guide covers all the ways to install Simply-MCP-PY and its optional dependencies.

## Requirements

- Python 3.10 or higher
- pip 21.0 or higher (for permanent installation)
- OR uv 0.1.0 or higher (for trying without installing)

## Try Without Installing (uvx)

Want to test Simply-MCP-PY before committing to a full installation? Use **uvx** to run commands directly from PyPI without installing anything permanently.

### What is uvx?

[uvx](https://github.com/astral-sh/uv) is a tool that lets you run Python packages instantly without installation. Think of it like `npx` for Python - it downloads and caches the package on first run, then executes it immediately.

### When to Use uvx

**Use uvx if you want to:**
- Try Simply-MCP-PY without installing it
- Run one-off commands without affecting your Python environment
- Test a specific version without switching virtual environments
- Avoid global package installation

**Use pip install if you want to:**
- Develop MCP servers regularly
- Import Simply-MCP in your Python code
- Customize or extend the framework
- Have faster command execution (no download delay)

### Installing uv/uvx

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# With pip
pip install uv
```

### Using uvx with Simply-MCP

Run any Simply-MCP command without installation:

```bash
# Check version
uvx simply-mcp --version

# Run a server
uvx simply-mcp run server.py

# List components
uvx simply-mcp list server.py

# Start development mode
uvx simply-mcp dev server.py
```

**First Run:** Downloads packages (~20-40MB total), takes ~7-30 seconds

**Subsequent Runs:** Nearly instant (uses cached packages)

### Comparison: uvx vs pip install

| Feature | uvx simply-mcp | pip install simply-mcp |
|---------|----------------|------------------------|
| Installation required | No | Yes |
| First run speed | 7-30 seconds (download) | Instant |
| Subsequent runs | Near-instant (cached) | Instant |
| Virtual environment | Not needed | Recommended |
| Package isolation | Automatic | Manual (via venv) |
| Import in Python code | No | Yes |
| Best for | Trying/testing | Development/production |

### Example: Try Before Installing

```bash
# Test Simply-MCP without installing
uvx simply-mcp --help

# Run an example server
uvx simply-mcp run examples/simple_server.py

# Like it? Install it permanently
pip install simply-mcp
```

## Permanent Installation (pip)

### Using pip

The simplest way to install Simply-MCP-PY:

```bash
pip install simply-mcp
```

### Using poetry

If you're using Poetry for dependency management:

```bash
poetry add simply-mcp
```

### From Source

To install the latest development version:

```bash
git clone https://github.com/Clockwork-Innovations/simply-mcp-py.git
cd simply-mcp-py
pip install -e .
```

## Optional Dependencies

### Development Tools

Install development dependencies (testing, linting, type checking):

```bash
pip install simply-mcp[dev]
```

This includes:
- pytest - Testing framework
- pytest-asyncio - Async test support
- pytest-cov - Coverage reporting
- black - Code formatter
- ruff - Linter
- mypy - Type checker
- pre-commit - Git hooks

### Documentation

Install documentation dependencies to build docs locally:

```bash
pip install simply-mcp[docs]
```

This includes:
- mkdocs - Documentation generator
- mkdocs-material - Material theme
- mkdocstrings - API documentation generator

### Bundling

Install PyInstaller for creating standalone executables:

```bash
pip install simply-mcp[bundling]
```

### All Optional Dependencies

Install everything:

```bash
pip install simply-mcp[dev,docs,bundling]
```

## Verify Installation

After installation, verify that Simply-MCP-PY is installed correctly:

```bash
simply-mcp --version
```

You should see output like:

```
simply-mcp, version 0.1.0
```

## Virtual Environment (Recommended)

We strongly recommend using a virtual environment:

### Using venv

```bash
# Create virtual environment
python -m venv venv

# Activate (Linux/macOS)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Install Simply-MCP-PY
pip install simply-mcp
```

### Using conda

```bash
# Create environment
conda create -n mcp-env python=3.10

# Activate environment
conda activate mcp-env

# Install Simply-MCP-PY
pip install simply-mcp
```

## Upgrading

To upgrade to the latest version:

```bash
pip install --upgrade simply-mcp
```

## Uninstalling

To remove Simply-MCP-PY:

```bash
pip uninstall simply-mcp
```

## Troubleshooting

### Python Version Issues

If you have multiple Python versions installed, use:

```bash
python3.10 -m pip install simply-mcp
```

### Permission Errors

If you encounter permission errors on Linux/macOS:

```bash
pip install --user simply-mcp
```

### Network Issues

If you're behind a proxy:

```bash
pip install --proxy http://user:pass@proxy:port simply-mcp
```

### Dependency Conflicts

If you have dependency conflicts, create a fresh virtual environment:

```bash
python -m venv fresh-env
source fresh-env/bin/activate
pip install simply-mcp
```

## Next Steps

Now that you have Simply-MCP-PY installed, continue to:

- [Quick Start](quickstart.md) - Get up and running in 5 minutes
- [First Server](first-server.md) - Build your first MCP server
- [Configuration Guide](../guide/configuration.md) - Configure your servers
