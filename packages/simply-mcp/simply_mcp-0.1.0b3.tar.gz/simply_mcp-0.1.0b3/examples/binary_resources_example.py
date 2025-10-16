#!/usr/bin/env python3
"""Example demonstrating binary content support in MCP resources.

This example shows how to:
- Serve image files as binary resources
- Serve PDF documents as binary resources
- Handle binary data with proper encoding
- Use BinaryContent class for automatic base64 encoding
- Configure binary content size limits

Run with:
    python examples/binary_resources_example.py

Or test with MCP Inspector:
    npx @anthropic-ai/mcp-inspector python examples/binary_resources_example.py
"""

import asyncio
import tempfile
from pathlib import Path

from simply_mcp.api.decorators import mcp_server, resource, tool, prompt
from simply_mcp.features.binary import BinaryContent, read_image, read_pdf


# Create sample binary files for demonstration
def create_sample_files() -> tuple[Path, Path, Path]:
    """Create sample binary files for the demo."""
    temp_dir = Path(tempfile.mkdtemp())

    # Create a sample PNG image (1x1 red pixel)
    png_file = temp_dir / "sample.png"
    png_data = (
        b"\x89PNG\r\n\x1a\n"
        b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x02\x00\x00\x00\x90wS\xde"
        b"\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0\x00\x00\x00\x03\x00\x01\x00\x18\xdd\x8d\xb4"
        b"\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    png_file.write_bytes(png_data)

    # Create a sample PDF document
    pdf_file = temp_dir / "sample.pdf"
    pdf_data = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Count 1
/Kids [3 0 R]
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Hello, Binary Content!) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000214 00000 n
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
310
%%EOF
"""
    pdf_file.write_bytes(pdf_data)

    # Create a sample data file
    data_file = temp_dir / "data.bin"
    data_file.write_bytes(b"\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09")

    return png_file, pdf_file, data_file


# Create sample files
PNG_FILE, PDF_FILE, DATA_FILE = create_sample_files()


# Use the decorator API with a class-based server
@mcp_server(
    name="binary-resources-server",
    version="1.0.0",
    description="Example server demonstrating binary content support",
)
class BinaryResourcesServer:
    """Server demonstrating binary content support."""


# Example 1: Serve an image resource
@resource(uri="image://sample-png")
def get_sample_image() -> BinaryContent:
    """Return a sample PNG image as binary content.

    This demonstrates:
    - Reading an image file with read_image()
    - Automatic MIME type detection
    - Binary content encoding
    """
    return read_image(PNG_FILE)


# Example 2: Serve a PDF document
@resource(uri="document://sample-pdf")
def get_sample_pdf() -> BinaryContent:
    """Return a sample PDF document as binary content.

    This demonstrates:
    - Reading a PDF file with read_pdf()
    - Proper PDF MIME type handling
    """
    return read_pdf(PDF_FILE)


# Example 3: Serve binary data with explicit MIME type
@resource(uri="data://sample-binary")
def get_binary_data() -> BinaryContent:
    """Return binary data with explicit MIME type.

    This demonstrates:
    - Creating BinaryContent from file
    - Setting custom MIME type
    """
    return BinaryContent.from_file(DATA_FILE, mime_type="application/octet-stream")


# Example 4: Generate binary content dynamically
@resource(uri="image://generated-pixel")
def generate_pixel() -> BinaryContent:
    """Generate a 1x1 blue pixel dynamically.

    This demonstrates:
    - Creating BinaryContent from bytes
    - Dynamic binary content generation
    """
    # 1x1 blue pixel PNG
    blue_pixel = (
        b"\x89PNG\r\n\x1a\n"
        b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x02\x00\x00\x00\x90wS\xde"
        b"\x00\x00\x00\x0cIDATx\x9cc\x00\x00\xff\xff\x00\x00\x00\x03\x00\x01\x9a\x7f\xc7\xe6"
        b"\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    return BinaryContent(blue_pixel, mime_type="image/png", filename="blue.png")


# Example 5: Serve base64-encoded data
@resource(uri="data://base64-example")
def get_base64_data() -> str:
    """Return base64-encoded data as a string.

    This demonstrates:
    - Converting binary content to base64 string
    - Direct base64 encoding for transport
    """
    data = b"Hello, this is binary data!"
    content = BinaryContent(data, mime_type="application/octet-stream")
    return content.to_base64()


# Example 6: Handle binary content with size limits
@resource(uri="data://size-limited")
def get_size_limited_data() -> BinaryContent:
    """Return binary data with size validation.

    This demonstrates:
    - Size limit enforcement
    - Configuration-based max_request_size
    """
    # Create some data (will be checked against config limits)
    data = b"x" * 1024  # 1KB of data
    return BinaryContent(data, mime_type="application/octet-stream")


# Example 7: Resource that returns raw bytes (auto-converted)
@resource(uri="data://raw-bytes")
def get_raw_bytes() -> bytes:
    """Return raw bytes (automatically converted to base64).

    This demonstrates:
    - Returning bytes directly from handler
    - Automatic base64 encoding by server
    """
    return b"Raw bytes content"


# Example 8: Tool that processes images
@tool()
def analyze_image(image_base64: str) -> dict:
    """Analyze a base64-encoded image.

    This demonstrates:
    - Accepting base64-encoded images in tools
    - Processing binary data
    - Returning analysis results

    Args:
        image_base64: Base64-encoded image data

    Returns:
        Analysis results including size and type
    """
    try:
        # Decode the base64 image
        content = BinaryContent.from_base64(image_base64)

        # Analyze the image
        return {
            "success": True,
            "size_bytes": content.size,
            "mime_type": content.mime_type,
            "is_image": content.is_image(),
            "is_png": content.mime_type == "image/png",
            "is_jpeg": content.mime_type == "image/jpeg",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# Example 9: Tool that creates thumbnail (simulated)
@tool()
def create_thumbnail(image_base64: str, max_size: int = 100) -> dict:
    """Create a thumbnail from an image (simulated).

    This demonstrates:
    - Processing binary content in tools
    - Size validation
    - Returning binary data from tools

    Args:
        image_base64: Base64-encoded image data
        max_size: Maximum dimension for thumbnail

    Returns:
        Result with thumbnail data or error
    """
    try:
        # Decode the image
        content = BinaryContent.from_base64(image_base64)

        # Validate it's an image
        if not content.is_image():
            return {
                "success": False,
                "error": f"Not an image: {content.mime_type}",
            }

        # In a real implementation, you would use PIL/Pillow here to resize
        # For demo purposes, we'll just return the original with a note
        return {
            "success": True,
            "message": f"Would create {max_size}x{max_size} thumbnail",
            "original_size": content.size,
            "mime_type": content.mime_type,
            # In real implementation: "thumbnail_base64": thumbnail.to_base64()
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# Example 10: Prompt that references binary resources
@prompt()
def image_analysis_prompt(image_uri: str) -> str:
    """Generate a prompt for image analysis.

    This demonstrates:
    - Creating prompts that reference binary resources
    - Instructing LLMs to work with binary content

    Args:
        image_uri: URI of the image resource (e.g., "image://sample-png")

    Returns:
        Prompt text for image analysis
    """
    return f"""Analyze the image at {image_uri}.

Please describe:
1. What you see in the image
2. The dominant colors
3. Any text or symbols present
4. The overall composition

Provide a detailed analysis of the image content."""


async def main():
    """Run the binary resources server."""
    from simply_mcp.api.decorators import get_global_server

    print("=" * 60)
    print("Binary Resources Example Server")
    print("=" * 60)
    print()
    print("This server demonstrates binary content support including:")
    print("  - Image resources (PNG)")
    print("  - PDF documents")
    print("  - Binary data with custom MIME types")
    print("  - Dynamic binary generation")
    print("  - Binary content in tools")
    print()
    print("Available resources:")
    print("  - image://sample-png       - Sample PNG image")
    print("  - document://sample-pdf    - Sample PDF document")
    print("  - data://sample-binary     - Binary data file")
    print("  - image://generated-pixel  - Dynamically generated image")
    print("  - data://base64-example    - Base64-encoded data")
    print("  - data://size-limited      - Size-validated data")
    print("  - data://raw-bytes         - Raw bytes (auto-encoded)")
    print()
    print("Available tools:")
    print("  - analyze_image      - Analyze base64-encoded images")
    print("  - create_thumbnail   - Create image thumbnails (simulated)")
    print()
    print("Available prompts:")
    print("  - image_analysis_prompt - Generate image analysis prompts")
    print()
    print("Configuration:")
    print("  - Binary content: Enabled")
    print("  - Max request size: 10 MB (configurable)")
    print()
    print("Starting server...")
    print("=" * 60)
    print()

    # Get and run the global server (used by module-level decorators)
    server = get_global_server()
    await server.initialize()
    await server.run_stdio()


if __name__ == "__main__":
    asyncio.run(main())
