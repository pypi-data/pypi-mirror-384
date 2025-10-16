#!/usr/bin/env python3
"""Production-Ready MCP Server Example

This example demonstrates a production-ready MCP server with all Phase 4 advanced features:
- API key authentication for secure access
- Rate limiting to prevent abuse (60 requests/minute)
- Progress reporting for long-running operations
- Binary content support for file uploads and downloads
- HTTP transport with CORS enabled
- Structured logging with JSON output
- Comprehensive error handling
- Health checks and monitoring

This server is production-ready and demonstrates best practices for deploying
MCP servers in real-world scenarios.

Installation:
    # Install with all optional dependencies
    pip install simply-mcp[http,security]

    # Or install from source
    pip install -e ".[http,security]"

Usage:
    # Development mode with auto-reload
    simply-mcp dev examples/production_server.py --transport http --port 8000

    # Production mode
    simply-mcp run examples/production_server.py --transport http --port 8000

    # Or run directly
    python examples/production_server.py

Configuration:
    Set these environment variables for production:
    - MCP_API_KEYS: Comma-separated list of valid API keys
    - MCP_PORT: Port to listen on (default: 8000)
    - MCP_HOST: Host to bind to (default: 0.0.0.0)
    - MCP_LOG_LEVEL: Logging level (default: INFO)
    - MCP_RATE_LIMIT_RPM: Requests per minute (default: 60)

Testing:
    # Health check
    curl http://localhost:8000/health

    # List available tools (requires authentication)
    curl -X POST http://localhost:8000/mcp \\
      -H "Authorization: Bearer test-key-prod-123" \\
      -H "Content-Type: application/json" \\
      -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}'

    # Call a tool with progress reporting
    curl -X POST http://localhost:8000/mcp \\
      -H "Authorization: Bearer test-key-prod-123" \\
      -H "Content-Type: application/json" \\
      -d '{
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
          "name": "process_batch",
          "arguments": {"items": 10}
        }
      }'

    # Upload binary content
    curl -X POST http://localhost:8000/mcp \\
      -H "Authorization: Bearer test-key-prod-123" \\
      -H "Content-Type: application/json" \\
      -d '{
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
          "name": "upload_file",
          "arguments": {
            "filename": "data.txt",
            "content_base64": "SGVsbG8sIFdvcmxkIQ=="
          }
        }
      }'

Deployment Notes:
    1. Always use HTTPS in production (use a reverse proxy like nginx)
    2. Store API keys securely (use environment variables or secrets manager)
    3. Enable rate limiting to prevent abuse
    4. Monitor health endpoint for service availability
    5. Use structured logging for better observability
    6. Set appropriate CORS origins for your use case
    7. Configure appropriate request size limits
    8. Use a process manager (systemd, supervisor, or docker)
    9. Set up log rotation for production deployments
    10. Monitor rate limiter stats for capacity planning
"""

import asyncio
import base64
import logging
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

from simply_mcp import BuildMCPServer
from simply_mcp.core.types import ProgressReporter
from simply_mcp.features.binary import BinaryContent
from simply_mcp.security.auth import APIKeyAuthProvider
from simply_mcp.security.rate_limiter import RateLimiter
from simply_mcp.transports.http import HTTPTransport

# Configure structured logging for production
logging.basicConfig(
    level=os.getenv("MCP_LOG_LEVEL", "INFO"),
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "name": "%(name)s", "message": "%(message)s"}',
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


# Simulated data store (in production, use a real database)
DATA_STORE: dict[str, Any] = {}
FILE_STORE = Path(tempfile.mkdtemp()) / "uploads"
FILE_STORE.mkdir(parents=True, exist_ok=True)


def create_production_server() -> BuildMCPServer:
    """Create and configure the production MCP server.

    Returns:
        Configured BuildMCPServer instance with all production features
    """
    # Create server with production configuration
    mcp = BuildMCPServer(
        name="production-mcp-server",
        version="1.0.0",
        description="Production-ready MCP server with advanced features",
    )

    # ===================================================================
    # Tool 1: System Information (demonstrates basic tool)
    # ===================================================================

    @mcp.tool(
        name="get_system_info",
        description="Get system information and server status",
    )
    def get_system_info() -> dict[str, Any]:
        """Return system information and server statistics.

        Returns:
            Dictionary with system information
        """
        return {
            "server": "production-mcp-server",
            "version": "1.0.0",
            "uptime": "running",
            "timestamp": datetime.utcnow().isoformat(),
            "features": [
                "authentication",
                "rate_limiting",
                "progress_reporting",
                "binary_content",
            ],
            "data_store_size": len(DATA_STORE),
            "file_store_size": len(list(FILE_STORE.glob("*"))) if FILE_STORE.exists() else 0,
        }

    # ===================================================================
    # Tool 2: Process Batch (demonstrates progress reporting)
    # ===================================================================

    @mcp.tool(
        name="process_batch",
        description="Process a batch of items with progress reporting",
    )
    async def process_batch(
        items: int,
        delay: float = 0.5,
        progress: ProgressReporter | None = None,
    ) -> dict[str, Any]:
        """Process multiple items with progress updates.

        This demonstrates long-running operations with progress reporting.
        Perfect for batch jobs, data processing, or any operation that
        takes significant time.

        Args:
            items: Number of items to process
            delay: Delay per item in seconds (for demonstration)
            progress: Progress reporter for tracking

        Returns:
            Processing results and statistics
        """
        results = []
        start_time = datetime.utcnow()

        for i in range(items):
            # Calculate and report progress
            if progress:
                percentage = ((i + 1) / items) * 100
                await progress.update(
                    percentage=percentage,
                    message=f"Processing item {i + 1} of {items}",
                    current=i + 1,
                    total=items,
                )

            # Simulate processing work
            await asyncio.sleep(delay)

            # Store result
            result = {
                "item_id": i + 1,
                "status": "completed",
                "timestamp": datetime.utcnow().isoformat(),
            }
            results.append(result)

            logger.info(
                f"Processed item {i + 1}/{items}",
                extra={"item_id": i + 1, "total": items},
            )

        end_time = datetime.utcnow()
        elapsed = (end_time - start_time).total_seconds()

        return {
            "success": True,
            "items_processed": len(results),
            "elapsed_seconds": elapsed,
            "items_per_second": len(results) / elapsed if elapsed > 0 else 0,
            "results": results,
        }

    # ===================================================================
    # Tool 3: Upload File (demonstrates binary content input)
    # ===================================================================

    @mcp.tool(
        name="upload_file",
        description="Upload a file to the server",
    )
    def upload_file(
        filename: str,
        content_base64: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Upload a file with binary content.

        This demonstrates handling binary content in tool inputs.
        Files are stored securely and can be retrieved later.

        Args:
            filename: Name of the file
            content_base64: Base64-encoded file content
            metadata: Optional metadata for the file

        Returns:
            Upload confirmation with file details
        """
        try:
            # Decode base64 content
            content = base64.b64decode(content_base64)

            # Save file
            file_path = FILE_STORE / filename
            file_path.write_bytes(content)

            # Store metadata
            file_id = f"file_{len(DATA_STORE)}"
            DATA_STORE[file_id] = {
                "filename": filename,
                "size": len(content),
                "path": str(file_path),
                "uploaded_at": datetime.utcnow().isoformat(),
                "metadata": metadata or {},
            }

            logger.info(
                f"File uploaded: {filename}",
                extra={
                    "file_id": file_id,
                    "size": len(content),
                    "filename": filename,
                },
            )

            return {
                "success": True,
                "file_id": file_id,
                "filename": filename,
                "size": len(content),
                "message": f"File uploaded successfully: {filename}",
            }

        except Exception as e:
            logger.error(f"Upload failed: {e}", extra={"filename": filename})
            return {
                "success": False,
                "error": str(e),
                "message": "File upload failed",
            }

    # ===================================================================
    # Tool 4: Data Storage (demonstrates data management)
    # ===================================================================

    @mcp.tool(
        name="store_data",
        description="Store data in the server's data store",
    )
    def store_data(
        key: str,
        value: Any,
        ttl_seconds: int | None = None,
    ) -> dict[str, Any]:
        """Store data with optional TTL.

        Args:
            key: Storage key
            value: Data to store
            ttl_seconds: Optional time-to-live in seconds

        Returns:
            Storage confirmation
        """
        DATA_STORE[key] = {
            "value": value,
            "stored_at": datetime.utcnow().isoformat(),
            "ttl": ttl_seconds,
        }

        logger.info(
            f"Data stored: {key}",
            extra={"key": key, "ttl": ttl_seconds},
        )

        return {
            "success": True,
            "key": key,
            "message": "Data stored successfully",
        }

    @mcp.tool(
        name="retrieve_data",
        description="Retrieve data from the server's data store",
    )
    def retrieve_data(key: str) -> dict[str, Any]:
        """Retrieve stored data.

        Args:
            key: Storage key

        Returns:
            Stored data or error
        """
        if key not in DATA_STORE:
            return {
                "success": False,
                "error": "Key not found",
                "key": key,
            }

        data = DATA_STORE[key]
        return {
            "success": True,
            "key": key,
            "value": data["value"],
            "stored_at": data["stored_at"],
        }

    # ===================================================================
    # Tool 5: List Resources (demonstrates resource management)
    # ===================================================================

    @mcp.tool(
        name="list_uploads",
        description="List all uploaded files",
    )
    def list_uploads() -> dict[str, Any]:
        """List all files in the upload store.

        Returns:
            List of uploaded files with metadata
        """
        files = [
            {
                "file_id": file_id,
                **file_data,
            }
            for file_id, file_data in DATA_STORE.items()
            if file_id.startswith("file_")
        ]

        return {
            "success": True,
            "count": len(files),
            "files": files,
        }

    # ===================================================================
    # Tool 6: Multi-Stage Operation (demonstrates complex progress)
    # ===================================================================

    @mcp.tool(
        name="multi_stage_process",
        description="Execute a multi-stage process with detailed progress",
    )
    async def multi_stage_process(
        stages: int = 3,
        progress: ProgressReporter | None = None,
    ) -> dict[str, Any]:
        """Execute multi-stage processing with progress reporting.

        This demonstrates complex operations with multiple stages,
        each with its own progress tracking.

        Args:
            stages: Number of stages to execute
            progress: Progress reporter

        Returns:
            Results from all stages
        """
        stage_results = []

        for stage_num in range(1, stages + 1):
            base_progress = ((stage_num - 1) / stages) * 100
            stage_progress = 100 / stages

            # Stage initialization
            if progress:
                await progress.update(
                    percentage=base_progress,
                    message=f"Initializing stage {stage_num}/{stages}",
                )
            await asyncio.sleep(0.2)

            # Stage processing
            if progress:
                await progress.update(
                    percentage=base_progress + (stage_progress * 0.5),
                    message=f"Processing stage {stage_num}/{stages}",
                )
            await asyncio.sleep(0.3)

            # Stage completion
            if progress:
                await progress.update(
                    percentage=base_progress + stage_progress,
                    message=f"Completed stage {stage_num}/{stages}",
                )

            stage_results.append({
                "stage": stage_num,
                "status": "completed",
                "timestamp": datetime.utcnow().isoformat(),
            })

            logger.info(f"Completed stage {stage_num}/{stages}")

        return {
            "success": True,
            "stages_completed": len(stage_results),
            "results": stage_results,
        }

    # ===================================================================
    # Resource 1: Download File (demonstrates binary content output)
    # ===================================================================

    @mcp.resource(
        uri="file://{file_id}",
        name="Download uploaded file",
        description="Download a previously uploaded file",
    )
    def download_file(file_id: str) -> BinaryContent | dict[str, Any]:
        """Download a file as binary content.

        This demonstrates serving binary content through resources.

        Args:
            file_id: ID of the file to download

        Returns:
            Binary content or error
        """
        if file_id not in DATA_STORE:
            return {
                "error": "File not found",
                "file_id": file_id,
            }

        file_data = DATA_STORE[file_id]
        file_path = Path(file_data["path"])

        if not file_path.exists():
            return {
                "error": "File not found on disk",
                "file_id": file_id,
            }

        # Return binary content
        content = BinaryContent.from_file(file_path)
        # Update filename to match original
        content.filename = file_data["filename"]
        return content

    # ===================================================================
    # Prompt 1: System Status (demonstrates prompt templates)
    # ===================================================================

    @mcp.prompt(
        name="system_status_report",
        description="Generate a system status report prompt",
    )
    def system_status_report(
        include_files: bool = True,
        include_data: bool = True,
    ) -> str:
        """Generate a prompt for system status reporting.

        Args:
            include_files: Include file storage information
            include_data: Include data store information

        Returns:
            Formatted prompt text
        """
        sections = ["Generate a comprehensive system status report."]

        if include_files:
            sections.append("Include information about uploaded files and storage usage.")

        if include_data:
            sections.append("Include information about the data store and cached values.")

        sections.extend([
            "",
            "Please analyze:",
            "1. Server health and uptime",
            "2. Resource utilization",
            "3. Performance metrics",
            "4. Any potential issues or concerns",
            "",
            "Format the report in a clear, structured manner.",
        ])

        return "\n".join(sections)

    return mcp


async def main() -> None:
    """Main entry point for the production server."""
    logger.info("Starting production MCP server...")

    # Create server
    mcp = create_production_server()

    # Get configuration from environment
    api_keys = os.getenv("MCP_API_KEYS", "test-key-prod-123,test-key-prod-456").split(",")
    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_PORT", "8000"))
    rate_limit_rpm = int(os.getenv("MCP_RATE_LIMIT_RPM", "60"))

    # Initialize server
    await mcp.initialize()

    logger.info(
        "Server initialized",
        extra={
            "name": "production-mcp-server",
            "version": "1.0.0",
            "features": ["auth", "rate_limiting", "progress", "binary"],
        },
    )

    # Create authentication provider
    auth_provider = APIKeyAuthProvider(api_keys=api_keys)

    logger.info(
        f"API key authentication enabled with {len(api_keys)} key(s)",
        extra={"num_keys": len(api_keys)},
    )

    # Create rate limiter
    rate_limiter = RateLimiter(
        requests_per_minute=rate_limit_rpm,
        burst_size=10,
        max_clients=100,
    )

    logger.info(
        f"Rate limiting enabled: {rate_limit_rpm} requests/minute",
        extra={"rpm": rate_limit_rpm, "burst": 10},
    )

    # Create HTTP transport with all features
    transport = HTTPTransport(
        server=mcp.server,
        host=host,
        port=port,
        cors_enabled=True,
        cors_origins=["*"],  # In production, specify exact origins
        auth_provider=auth_provider,
        rate_limiter=rate_limiter,
    )

    # Print startup information
    print("=" * 70)
    print("Production MCP Server")
    print("=" * 70)
    print()
    print("Server: production-mcp-server v1.0.0")
    print(f"Listening: http://{host}:{port}")
    print()
    print("Features:")
    print(f"  - API Key Authentication: {len(api_keys)} key(s) configured")
    print(f"  - Rate Limiting: {rate_limit_rpm} requests/minute (burst: 10)")
    print("  - Progress Reporting: Enabled")
    print("  - Binary Content: Enabled")
    print("  - CORS: Enabled")
    print()
    print("Endpoints:")
    print(f"  POST http://{host}:{port}/mcp - MCP JSON-RPC endpoint")
    print(f"  GET  http://{host}:{port}/health - Health check")
    print(f"  GET  http://{host}:{port}/ - Server info")
    print()
    print("Valid API Keys (for development):")
    for key in api_keys:
        print(f"  - {key}")
    print()
    print("Example Request:")
    print(f'  curl -X POST http://{host}:{port}/mcp \\')
    print('    -H "Authorization: Bearer test-key-prod-123" \\')
    print('    -H "Content-Type: application/json" \\')
    print('    -d \'{"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}\'')
    print()
    print("=" * 70)
    print()
    print("Server is running. Press Ctrl+C to stop.")
    print()

    # Start server
    try:
        await transport.start()

        # Keep running
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        logger.info("Shutdown signal received")
        print("\nShutting down gracefully...")

    finally:
        await transport.stop()
        logger.info("Server stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer stopped by user")
