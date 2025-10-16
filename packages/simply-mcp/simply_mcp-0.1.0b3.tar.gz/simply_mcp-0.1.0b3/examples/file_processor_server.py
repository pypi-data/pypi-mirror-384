#!/usr/bin/env python3
"""File Processing MCP Server Example

This example demonstrates a realistic file processing server that showcases:
- Binary content handling (upload/download)
- Image processing (resize, format conversion)
- PDF generation
- Progress reporting for long operations
- Resource endpoints for processed files
- Authentication for secure file operations
- Rate limiting to prevent abuse

This is a practical example that could be adapted for real-world file processing
services, document conversion APIs, or media processing pipelines.

Installation:
    # Install with optional dependencies
    pip install simply-mcp[http,security]

    # For image processing (optional, enables actual processing)
    pip install pillow

    # For PDF generation (optional, enables PDF features)
    pip install reportlab

Usage:
    # Development mode
    simply-mcp dev examples/file_processor_server.py --transport http --port 8080

    # Production mode
    python examples/file_processor_server.py

Testing:
    # Upload an image
    curl -X POST http://localhost:8080/mcp \\
      -H "Authorization: Bearer file-processor-key" \\
      -H "Content-Type: application/json" \\
      -d '{
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
          "name": "upload_image",
          "arguments": {
            "filename": "test.png",
            "image_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
          }
        }
      }'

    # Resize an image
    curl -X POST http://localhost:8080/mcp \\
      -H "Authorization: Bearer file-processor-key" \\
      -H "Content-Type: application/json" \\
      -d '{
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
          "name": "resize_image",
          "arguments": {
            "image_id": "img_001",
            "width": 800,
            "height": 600
          }
        }
      }'

Features:
    - Upload images (PNG, JPEG, GIF, BMP)
    - Resize images with aspect ratio preservation
    - Convert image formats
    - Generate thumbnails
    - Create PDF documents
    - Process files with progress tracking
    - Download processed files
    - Secure authentication
    - Rate limiting for API protection
"""

import asyncio
import io
import logging
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

# Try to import optional dependencies
try:
    from PIL import Image

    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "name": "%(name)s", "message": "%(message)s"}',
)

logger = logging.getLogger(__name__)

# Storage for uploaded and processed files
UPLOAD_DIR = Path(tempfile.mkdtemp()) / "uploads"
PROCESSED_DIR = Path(tempfile.mkdtemp()) / "processed"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# File metadata store
FILE_REGISTRY: dict[str, dict[str, Any]] = {}


def create_file_processor_server() -> BuildMCPServer:
    """Create the file processing MCP server.

    Returns:
        Configured BuildMCPServer instance
    """
    mcp = BuildMCPServer(
        name="file-processor-server",
        version="1.0.0",
        description="File processing server with image manipulation and PDF generation",
    )

    # ===================================================================
    # Tool 1: Upload Image
    # ===================================================================

    @mcp.tool(
        name="upload_image",
        description="Upload an image file for processing",
    )
    def upload_image(
        filename: str,
        image_base64: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Upload an image file to the server.

        Args:
            filename: Name of the image file
            image_base64: Base64-encoded image data
            metadata: Optional metadata (tags, description, etc.)

        Returns:
            Upload confirmation with image ID and details
        """
        try:
            # Decode image
            content = BinaryContent.from_base64(image_base64)

            # Validate it's an image
            if not content.is_image():
                return {
                    "success": False,
                    "error": f"Not a valid image: {content.mime_type}",
                }

            # Generate image ID
            image_id = f"img_{len([k for k in FILE_REGISTRY if k.startswith('img_')]):03d}"

            # Save image
            file_path = UPLOAD_DIR / f"{image_id}_{filename}"
            file_path.write_bytes(content.data)

            # Detect image properties if Pillow is available
            properties = {}
            if PILLOW_AVAILABLE:
                try:
                    with Image.open(io.BytesIO(content.data)) as img:
                        properties = {
                            "width": img.width,
                            "height": img.height,
                            "format": img.format,
                            "mode": img.mode,
                        }
                except Exception as e:
                    logger.warning(f"Could not read image properties: {e}")

            # Store metadata
            FILE_REGISTRY[image_id] = {
                "type": "image",
                "filename": filename,
                "path": str(file_path),
                "size": content.size,
                "mime_type": content.mime_type,
                "uploaded_at": datetime.utcnow().isoformat(),
                "metadata": metadata or {},
                "properties": properties,
            }

            logger.info(f"Image uploaded: {image_id}", extra={"image_id": image_id})

            return {
                "success": True,
                "image_id": image_id,
                "filename": filename,
                "size": content.size,
                "mime_type": content.mime_type,
                "properties": properties,
                "message": f"Image uploaded successfully: {image_id}",
            }

        except Exception as e:
            logger.error(f"Upload failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    # ===================================================================
    # Tool 2: Resize Image
    # ===================================================================

    @mcp.tool(
        name="resize_image",
        description="Resize an uploaded image",
    )
    async def resize_image(
        image_id: str,
        width: int | None = None,
        height: int | None = None,
        maintain_aspect: bool = True,
        progress: ProgressReporter | None = None,
    ) -> dict[str, Any]:
        """Resize an image with optional aspect ratio preservation.

        Args:
            image_id: ID of the uploaded image
            width: Target width (optional if height provided)
            height: Target height (optional if width provided)
            maintain_aspect: Whether to maintain aspect ratio
            progress: Progress reporter

        Returns:
            Resized image details
        """
        if not PILLOW_AVAILABLE:
            return {
                "success": False,
                "error": "Image processing not available (Pillow not installed)",
                "install_hint": "pip install pillow",
            }

        if image_id not in FILE_REGISTRY:
            return {
                "success": False,
                "error": f"Image not found: {image_id}",
            }

        if width is None and height is None:
            return {
                "success": False,
                "error": "Must provide at least width or height",
            }

        try:
            # Load image data
            file_data = FILE_REGISTRY[image_id]
            original_path = Path(file_data["path"])

            if progress:
                await progress.update(10, message="Loading image")

            # Open and process image
            with Image.open(original_path) as img:
                original_size = img.size

                if progress:
                    await progress.update(30, message="Calculating dimensions")

                # Calculate target size
                if maintain_aspect:
                    if width and not height:
                        # Scale by width
                        ratio = width / img.width
                        height = int(img.height * ratio)
                    elif height and not width:
                        # Scale by height
                        ratio = height / img.height
                        width = int(img.width * ratio)
                    elif width and height:
                        # Fit within box
                        img.thumbnail((width, height), Image.Resampling.LANCZOS)
                        width, height = img.size
                else:
                    # Use exact dimensions
                    width = width or img.width
                    height = height or img.height

                if progress:
                    await progress.update(50, message=f"Resizing to {width}x{height}")

                # Resize image
                resized = img.resize((width, height), Image.Resampling.LANCZOS)

                if progress:
                    await progress.update(80, message="Saving resized image")

                # Save resized image
                output_id = f"{image_id}_resized_{width}x{height}"
                output_filename = f"{output_id}.png"
                output_path = PROCESSED_DIR / output_filename

                resized.save(output_path, format="PNG")

                if progress:
                    await progress.update(90, message="Updating registry")

                # Store metadata
                FILE_REGISTRY[output_id] = {
                    "type": "image",
                    "filename": output_filename,
                    "path": str(output_path),
                    "size": output_path.stat().st_size,
                    "mime_type": "image/png",
                    "created_at": datetime.utcnow().isoformat(),
                    "operation": "resize",
                    "source_image": image_id,
                    "properties": {
                        "width": width,
                        "height": height,
                        "original_width": original_size[0],
                        "original_height": original_size[1],
                    },
                }

                if progress:
                    await progress.update(100, message="Resize complete")

                logger.info(
                    f"Image resized: {image_id} -> {output_id}",
                    extra={"source": image_id, "output": output_id},
                )

                return {
                    "success": True,
                    "output_id": output_id,
                    "original_size": {"width": original_size[0], "height": original_size[1]},
                    "new_size": {"width": width, "height": height},
                    "file_size": output_path.stat().st_size,
                    "message": f"Image resized successfully: {output_id}",
                }

        except Exception as e:
            logger.error(f"Resize failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    # ===================================================================
    # Tool 3: Convert Image Format
    # ===================================================================

    @mcp.tool(
        name="convert_image",
        description="Convert an image to a different format",
    )
    async def convert_image(
        image_id: str,
        format: str,
        quality: int = 85,
        progress: ProgressReporter | None = None,
    ) -> dict[str, Any]:
        """Convert an image to a different format.

        Args:
            image_id: ID of the uploaded image
            format: Target format (png, jpeg, gif, bmp, webp)
            quality: Output quality for lossy formats (1-100)
            progress: Progress reporter

        Returns:
            Converted image details
        """
        if not PILLOW_AVAILABLE:
            return {
                "success": False,
                "error": "Image processing not available (Pillow not installed)",
            }

        if image_id not in FILE_REGISTRY:
            return {
                "success": False,
                "error": f"Image not found: {image_id}",
            }

        format = format.upper()
        valid_formats = ["PNG", "JPEG", "GIF", "BMP", "WEBP"]
        if format not in valid_formats:
            return {
                "success": False,
                "error": f"Unsupported format: {format}",
                "supported": valid_formats,
            }

        try:
            file_data = FILE_REGISTRY[image_id]
            original_path = Path(file_data["path"])

            if progress:
                await progress.update(20, message="Loading image")
                await asyncio.sleep(0.1)

            with Image.open(original_path) as img:
                # Convert mode if necessary
                if format == "JPEG" and img.mode in ("RGBA", "P"):
                    if progress:
                        await progress.update(40, message="Converting to RGB")
                    img = img.convert("RGB")

                if progress:
                    await progress.update(60, message=f"Converting to {format}")
                    await asyncio.sleep(0.2)

                # Save converted image
                output_id = f"{image_id}_converted_{format.lower()}"
                output_filename = f"{output_id}.{format.lower()}"
                output_path = PROCESSED_DIR / output_filename

                save_kwargs = {}
                if format == "JPEG":
                    save_kwargs["quality"] = quality
                elif format == "PNG":
                    save_kwargs["optimize"] = True

                img.save(output_path, format=format, **save_kwargs)

                if progress:
                    await progress.update(90, message="Updating registry")

                # Store metadata
                mime_types = {
                    "PNG": "image/png",
                    "JPEG": "image/jpeg",
                    "GIF": "image/gif",
                    "BMP": "image/bmp",
                    "WEBP": "image/webp",
                }

                FILE_REGISTRY[output_id] = {
                    "type": "image",
                    "filename": output_filename,
                    "path": str(output_path),
                    "size": output_path.stat().st_size,
                    "mime_type": mime_types[format],
                    "created_at": datetime.utcnow().isoformat(),
                    "operation": "convert",
                    "source_image": image_id,
                    "properties": {
                        "format": format,
                        "quality": quality if format == "JPEG" else None,
                    },
                }

                if progress:
                    await progress.update(100, message="Conversion complete")

                logger.info(f"Image converted: {image_id} -> {output_id} ({format})")

                return {
                    "success": True,
                    "output_id": output_id,
                    "format": format,
                    "file_size": output_path.stat().st_size,
                    "message": f"Image converted to {format}: {output_id}",
                }

        except Exception as e:
            logger.error(f"Conversion failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    # ===================================================================
    # Tool 4: Create Thumbnail
    # ===================================================================

    @mcp.tool(
        name="create_thumbnail",
        description="Create a thumbnail from an image",
    )
    def create_thumbnail(
        image_id: str,
        max_size: int = 200,
    ) -> dict[str, Any]:
        """Create a thumbnail from an uploaded image.

        Args:
            image_id: ID of the uploaded image
            max_size: Maximum dimension for thumbnail

        Returns:
            Thumbnail details
        """
        if not PILLOW_AVAILABLE:
            return {
                "success": False,
                "error": "Image processing not available (Pillow not installed)",
            }

        if image_id not in FILE_REGISTRY:
            return {
                "success": False,
                "error": f"Image not found: {image_id}",
            }

        try:
            file_data = FILE_REGISTRY[image_id]
            original_path = Path(file_data["path"])

            with Image.open(original_path) as img:
                # Create thumbnail
                img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

                # Save thumbnail
                output_id = f"{image_id}_thumb_{max_size}"
                output_filename = f"{output_id}.png"
                output_path = PROCESSED_DIR / output_filename

                img.save(output_path, format="PNG")

                # Store metadata
                FILE_REGISTRY[output_id] = {
                    "type": "image",
                    "filename": output_filename,
                    "path": str(output_path),
                    "size": output_path.stat().st_size,
                    "mime_type": "image/png",
                    "created_at": datetime.utcnow().isoformat(),
                    "operation": "thumbnail",
                    "source_image": image_id,
                    "properties": {
                        "width": img.width,
                        "height": img.height,
                        "max_dimension": max_size,
                    },
                }

                return {
                    "success": True,
                    "output_id": output_id,
                    "size": {"width": img.width, "height": img.height},
                    "file_size": output_path.stat().st_size,
                    "message": f"Thumbnail created: {output_id}",
                }

        except Exception as e:
            logger.error(f"Thumbnail creation failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    # ===================================================================
    # Tool 5: Generate PDF
    # ===================================================================

    @mcp.tool(
        name="generate_pdf",
        description="Generate a PDF document",
    )
    async def generate_pdf(
        title: str,
        content: list[str],
        progress: ProgressReporter | None = None,
    ) -> dict[str, Any]:
        """Generate a PDF document with text content.

        Args:
            title: Document title
            content: List of text paragraphs
            progress: Progress reporter

        Returns:
            PDF generation details
        """
        if not REPORTLAB_AVAILABLE:
            return {
                "success": False,
                "error": "PDF generation not available (reportlab not installed)",
                "install_hint": "pip install reportlab",
            }

        try:
            if progress:
                await progress.update(10, message="Initializing PDF")

            # Generate PDF ID
            pdf_id = f"pdf_{len([k for k in FILE_REGISTRY if k.startswith('pdf_')]):03d}"
            pdf_filename = f"{pdf_id}_{title.replace(' ', '_')}.pdf"
            pdf_path = PROCESSED_DIR / pdf_filename

            if progress:
                await progress.update(30, message="Creating PDF document")
                await asyncio.sleep(0.1)

            # Create PDF
            c = canvas.Canvas(str(pdf_path), pagesize=letter)
            width, height = letter

            # Title
            c.setFont("Helvetica-Bold", 16)
            c.drawString(72, height - 72, title)

            if progress:
                await progress.update(50, message="Adding content")
                await asyncio.sleep(0.1)

            # Content
            c.setFont("Helvetica", 12)
            y = height - 120

            for i, paragraph in enumerate(content):
                if y < 72:  # New page if needed
                    c.showPage()
                    c.setFont("Helvetica", 12)
                    y = height - 72

                # Wrap text
                lines = [paragraph[i:i + 80] for i in range(0, len(paragraph), 80)]
                for line in lines:
                    c.drawString(72, y, line)
                    y -= 20

                if progress:
                    pct = 50 + ((i + 1) / len(content)) * 40
                    await progress.update(pct, message=f"Processing paragraph {i + 1}/{len(content)}")

            if progress:
                await progress.update(95, message="Finalizing PDF")

            c.save()

            if progress:
                await progress.update(100, message="PDF generation complete")

            # Store metadata
            FILE_REGISTRY[pdf_id] = {
                "type": "pdf",
                "filename": pdf_filename,
                "path": str(pdf_path),
                "size": pdf_path.stat().st_size,
                "mime_type": "application/pdf",
                "created_at": datetime.utcnow().isoformat(),
                "operation": "generate",
                "properties": {
                    "title": title,
                    "paragraphs": len(content),
                },
            }

            logger.info(f"PDF generated: {pdf_id}")

            return {
                "success": True,
                "pdf_id": pdf_id,
                "filename": pdf_filename,
                "file_size": pdf_path.stat().st_size,
                "message": f"PDF generated successfully: {pdf_id}",
            }

        except Exception as e:
            logger.error(f"PDF generation failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    # ===================================================================
    # Tool 6: List Files
    # ===================================================================

    @mcp.tool(
        name="list_files",
        description="List all uploaded and processed files",
    )
    def list_files(file_type: str | None = None) -> dict[str, Any]:
        """List all files in the registry.

        Args:
            file_type: Optional filter by type (image, pdf)

        Returns:
            List of files with metadata
        """
        files = []
        for file_id, file_data in FILE_REGISTRY.items():
            if file_type is None or file_data["type"] == file_type:
                files.append({
                    "file_id": file_id,
                    **file_data,
                })

        return {
            "success": True,
            "count": len(files),
            "files": files,
        }

    # ===================================================================
    # Resource 1: Download File
    # ===================================================================

    @mcp.resource(
        uri="file://{file_id}",
        name="Download file",
        description="Download an uploaded or processed file",
    )
    def download_file(file_id: str) -> BinaryContent | dict[str, Any]:
        """Download a file as binary content.

        Args:
            file_id: ID of the file to download

        Returns:
            Binary content or error
        """
        if file_id not in FILE_REGISTRY:
            return {
                "error": "File not found",
                "file_id": file_id,
            }

        file_data = FILE_REGISTRY[file_id]
        file_path = Path(file_data["path"])

        if not file_path.exists():
            return {
                "error": "File not found on disk",
                "file_id": file_id,
            }

        content = BinaryContent.from_file(
            file_path,
            mime_type=file_data["mime_type"],
        )
        # Update filename to match original
        content.filename = file_data["filename"]
        return content

    return mcp


async def main() -> None:
    """Main entry point."""
    logger.info("Starting file processor server...")

    # Create server
    mcp = create_file_processor_server()

    # Configuration
    api_keys = ["file-processor-key", "dev-key-123"]
    host = "0.0.0.0"
    port = 8080

    # Initialize
    await mcp.initialize()

    # Setup authentication and rate limiting
    auth_provider = APIKeyAuthProvider(api_keys=api_keys)
    rate_limiter = RateLimiter(requests_per_minute=30, burst_size=10)

    # Create transport
    transport = HTTPTransport(
        server=mcp.server,
        host=host,
        port=port,
        cors_enabled=True,
        auth_provider=auth_provider,
        rate_limiter=rate_limiter,
    )

    # Print info
    print("=" * 70)
    print("File Processor MCP Server")
    print("=" * 70)
    print()
    print("Server: file-processor-server v1.0.0")
    print(f"Listening: http://{host}:{port}")
    print()
    print("Features:")
    print(f"  - Image Processing: {'Available' if PILLOW_AVAILABLE else 'Not available (install pillow)'}")
    print(f"  - PDF Generation: {'Available' if REPORTLAB_AVAILABLE else 'Not available (install reportlab)'}")
    print("  - Binary Content: Enabled")
    print("  - Authentication: Enabled")
    print("  - Rate Limiting: 30 req/min")
    print()
    print("API Keys:")
    for key in api_keys:
        print(f"  - {key}")
    print()
    print("=" * 70)
    print()
    print("Server is running. Press Ctrl+C to stop.")
    print()

    try:
        await transport.start()
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        await transport.stop()


if __name__ == "__main__":
    asyncio.run(main())
