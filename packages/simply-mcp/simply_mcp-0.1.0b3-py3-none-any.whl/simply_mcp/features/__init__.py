"""Feature modules for Simply-MCP.

This package contains feature modules that extend the core functionality
of Simply-MCP with additional capabilities.
"""

from simply_mcp.features.binary import (
    BinaryContent,
    create_binary_resource,
    is_binary_mime_type,
    read_binary_file,
    read_image,
    read_pdf,
)
from simply_mcp.features.progress import (
    ProgressContext,
    ProgressReporterImpl,
    ProgressTracker,
)

__all__ = [
    # Binary content
    "BinaryContent",
    "read_image",
    "read_pdf",
    "read_binary_file",
    "create_binary_resource",
    "is_binary_mime_type",
    # Progress reporting
    "ProgressReporterImpl",
    "ProgressTracker",
    "ProgressContext",
]
