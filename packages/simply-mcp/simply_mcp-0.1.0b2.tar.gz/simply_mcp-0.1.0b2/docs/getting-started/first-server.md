# Building Your First Server

This tutorial walks you through building a complete MCP server with tools, resources, and prompts.

## What We'll Build

A file processing server that can:
- Read and write files
- List directory contents
- Provide file information resources
- Generate file processing prompts

## Prerequisites

- Simply-MCP-PY installed ([Installation Guide](installation.md))
- Python 3.10+
- Basic understanding of Python

## Step 1: Project Setup

Create a new directory for your project:

```bash
mkdir file-server
cd file-server
```

Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install simply-mcp
```

## Step 2: Basic Server Structure

Create `file_server.py`:

```python
from simply_mcp import mcp_server, tool, resource, prompt
from pathlib import Path
import json

@mcp_server(
    name="file-server",
    version="1.0.0",
    description="A file processing MCP server"
)
class FileServer:
    """MCP server for file operations."""

    def __init__(self):
        self.base_path = Path.cwd()
```

## Step 3: Add File Tools

Add tools for file operations:

```python
@mcp_server(name="file-server", version="1.0.0")
class FileServer:
    def __init__(self):
        self.base_path = Path.cwd()

    @tool(description="Read contents of a file")
    def read_file(self, path: str) -> str:
        """Read and return the contents of a file.

        Args:
            path: Path to the file to read

        Returns:
            File contents as string
        """
        file_path = self.base_path / path
        if not file_path.exists():
            return f"Error: File {path} not found"
        return file_path.read_text()

    @tool(description="Write contents to a file")
    def write_file(self, path: str, content: str) -> str:
        """Write content to a file.

        Args:
            path: Path to the file to write
            content: Content to write to the file

        Returns:
            Success message
        """
        file_path = self.base_path / path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)
        return f"Successfully wrote to {path}"

    @tool(description="List files in a directory")
    def list_files(self, path: str = ".") -> list[str]:
        """List all files in a directory.

        Args:
            path: Directory path (default: current directory)

        Returns:
            List of filenames
        """
        dir_path = self.base_path / path
        if not dir_path.exists():
            return [f"Error: Directory {path} not found"]
        return [f.name for f in dir_path.iterdir()]
```

## Step 4: Add Resources

Resources provide read-only data about files:

```python
    @resource(uri="file://stats/{path}", mime_type="application/json")
    def file_stats(self, path: str) -> dict:
        """Get statistics about a file.

        Args:
            path: Path to the file

        Returns:
            Dictionary with file statistics
        """
        file_path = self.base_path / path
        if not file_path.exists():
            return {"error": f"File {path} not found"}

        stat = file_path.stat()
        return {
            "path": path,
            "size": stat.st_size,
            "created": stat.st_ctime,
            "modified": stat.st_mtime,
            "is_file": file_path.is_file(),
            "is_dir": file_path.is_dir(),
        }

    @resource(uri="config://server", mime_type="application/json")
    def server_config(self) -> dict:
        """Get server configuration."""
        return {
            "name": "file-server",
            "version": "1.0.0",
            "base_path": str(self.base_path),
            "features": ["read", "write", "list"]
        }
```

## Step 5: Add Prompts

Prompts are reusable templates for common tasks:

```python
    @prompt(description="Generate file processing prompt")
    def process_files(self, operation: str = "analyze") -> str:
        """Generate a prompt for file processing operations.

        Args:
            operation: Type of operation (analyze, summarize, transform)

        Returns:
            Formatted prompt template
        """
        prompts = {
            "analyze": """Please analyze the files in this directory:
1. Count total files and directories
2. Identify file types and their distribution
3. Calculate total size
4. Detect any unusual patterns
""",
            "summarize": """Please create a summary of the files:
1. List main file categories
2. Highlight important files
3. Note any documentation files
4. Suggest organization improvements
""",
            "transform": """Please transform the files:
1. Suggest renaming conventions
2. Identify files that could be merged
3. Recommend directory structure
4. Note any redundant files
"""
        }
        return prompts.get(operation, prompts["analyze"])
```

## Step 6: Test Your Server

Run the server:

```bash
simply-mcp run file_server.py
```

## Step 7: Configuration

Create `simplymcp.config.toml`:

```toml
[server]
name = "file-server"
version = "1.0.0"

[transport]
type = "stdio"  # or "http", "sse"

[logging]
level = "INFO"
format = "json"
```

## Step 8: Add Error Handling

Improve error handling:

```python
from simply_mcp import mcp_server, tool, resource, prompt
from pathlib import Path
from typing import Union
import logging

logger = logging.getLogger(__name__)

@mcp_server(name="file-server", version="1.0.0")
class FileServer:
    def __init__(self):
        self.base_path = Path.cwd()
        logger.info(f"FileServer initialized with base_path: {self.base_path}")

    @tool(description="Read contents of a file")
    def read_file(self, path: str) -> Union[str, dict]:
        """Read file with error handling."""
        try:
            file_path = self.base_path / path
            if not file_path.exists():
                return {"error": f"File not found: {path}"}
            if not file_path.is_file():
                return {"error": f"Not a file: {path}"}
            return file_path.read_text()
        except Exception as e:
            logger.error(f"Error reading file {path}: {e}")
            return {"error": f"Failed to read file: {str(e)}"}
```

## Step 9: Run with Different Transports

### Stdio (Default)

```bash
simply-mcp run file_server.py
```

### HTTP

```bash
simply-mcp run file_server.py --transport http --port 3000
```

Test with curl:

```bash
curl http://localhost:3000/tools
```

### SSE

```bash
simply-mcp run file_server.py --transport sse --port 3000
```

## Step 10: Development Mode

Enable auto-reload:

```bash
simply-mcp run file_server.py --watch
```

Now any changes to `file_server.py` will automatically reload the server.

## Complete Code

Here's the complete server:

```python
from simply_mcp import mcp_server, tool, resource, prompt
from pathlib import Path
from typing import Union
import logging

logger = logging.getLogger(__name__)

@mcp_server(
    name="file-server",
    version="1.0.0",
    description="A complete file processing MCP server"
)
class FileServer:
    """MCP server for file operations with error handling."""

    def __init__(self):
        self.base_path = Path.cwd()
        logger.info(f"Initialized with base_path: {self.base_path}")

    @tool(description="Read contents of a file")
    def read_file(self, path: str) -> Union[str, dict]:
        """Read and return file contents."""
        try:
            file_path = self.base_path / path
            if not file_path.exists():
                return {"error": f"File not found: {path}"}
            return file_path.read_text()
        except Exception as e:
            return {"error": str(e)}

    @tool(description="Write contents to a file")
    def write_file(self, path: str, content: str) -> dict:
        """Write content to a file."""
        try:
            file_path = self.base_path / path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)
            return {"success": True, "path": path}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @tool(description="List files in a directory")
    def list_files(self, path: str = ".") -> list[str]:
        """List files in directory."""
        try:
            dir_path = self.base_path / path
            return [f.name for f in dir_path.iterdir()]
        except Exception as e:
            return [f"Error: {str(e)}"]

    @resource(uri="file://stats/{path}", mime_type="application/json")
    def file_stats(self, path: str) -> dict:
        """Get file statistics."""
        file_path = self.base_path / path
        if not file_path.exists():
            return {"error": "File not found"}

        stat = file_path.stat()
        return {
            "path": path,
            "size": stat.st_size,
            "is_file": file_path.is_file(),
            "modified": stat.st_mtime,
        }

    @prompt(description="File processing prompt")
    def process_files(self, operation: str = "analyze") -> str:
        """Generate file processing prompt."""
        return f"Please {operation} the files in this directory."
```

## Next Steps

Now that you've built your first server:

- [API Reference](../api/decorators.md) - Learn about all decorators
- [Configuration Guide](../guide/configuration.md) - Advanced configuration
- [Testing Guide](../guide/testing.md) - Write tests for your server
- [Deployment Guide](../guide/deployment.md) - Deploy to production
- [Examples](../examples/index.md) - See more examples

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure Simply-MCP-PY is installed
2. **Path Errors**: Check file paths are relative to base_path
3. **Permission Errors**: Ensure proper file permissions

For more help, visit our [Issue Tracker](https://github.com/Clockwork-Innovations/simply-mcp-py/issues).
