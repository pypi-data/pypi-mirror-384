"""Binary content support for MCP resources.

This module provides classes and utilities for handling binary content (images, files, etc.)
in MCP resources with proper encoding/decoding for transport.
"""

import base64
import mimetypes
from pathlib import Path
from typing import Any

from simply_mcp.core.errors import ValidationError


class BinaryContent:
    """Wrapper for binary data with automatic encoding/decoding.

    This class provides a convenient way to handle binary content in MCP resources,
    including automatic base64 encoding for transport, MIME type detection, and
    size validation.

    Attributes:
        data: The raw binary data
        mime_type: MIME type of the content
        size: Size of the content in bytes
        filename: Optional filename for reference

    Example:
        >>> # Create from file
        >>> content = BinaryContent.from_file("image.png")
        >>> print(content.mime_type)
        image/png
        >>>
        >>> # Create from bytes
        >>> content = BinaryContent(b"\\x89PNG...", mime_type="image/png")
        >>> encoded = content.to_base64()
        >>>
        >>> # Decode from base64
        >>> decoded = BinaryContent.from_base64(encoded, "image/png")
    """

    def __init__(
        self,
        data: bytes,
        mime_type: str | None = None,
        filename: str | None = None,
        max_size: int | None = None,
    ) -> None:
        """Initialize BinaryContent.

        Args:
            data: Raw binary data
            mime_type: MIME type of the content. If None, defaults to "application/octet-stream"
            filename: Optional filename for reference
            max_size: Optional maximum size in bytes. If provided, raises ValidationError
                     if data exceeds this size

        Raises:
            ValidationError: If data exceeds max_size
            TypeError: If data is not bytes
        """
        if not isinstance(data, bytes):
            raise TypeError(f"data must be bytes, got {type(data).__name__}")

        self.data = data
        self.size = len(data)
        self.filename = filename

        # Validate size if limit provided
        if max_size is not None and self.size > max_size:
            raise ValidationError(
                f"Binary content size ({self.size} bytes) exceeds maximum ({max_size} bytes)",
                code="CONTENT_TOO_LARGE",
            )

        # Detect or set MIME type
        if mime_type:
            self.mime_type = mime_type
        elif filename:
            detected_type = mimetypes.guess_type(filename)[0]
            self.mime_type = detected_type or "application/octet-stream"
        else:
            # Try to detect from content
            self.mime_type = self._detect_mime_type_from_content() or "application/octet-stream"

    def _detect_mime_type_from_content(self) -> str | None:
        """Detect MIME type from content magic bytes.

        Returns:
            Detected MIME type or None if unknown
        """
        # Common magic bytes patterns
        if self.data.startswith(b"\x89PNG\r\n\x1a\n"):
            return "image/png"
        elif self.data.startswith(b"\xff\xd8\xff"):
            return "image/jpeg"
        elif self.data.startswith(b"GIF87a") or self.data.startswith(b"GIF89a"):
            return "image/gif"
        elif self.data.startswith(b"RIFF") and self.data[8:12] == b"WEBP":
            return "image/webp"
        elif self.data.startswith(b"%PDF"):
            return "application/pdf"
        elif self.data.startswith(b"PK\x03\x04"):
            return "application/zip"
        elif self.data.startswith(b"\x1f\x8b\x08"):
            return "application/gzip"

        return None

    def to_base64(self) -> str:
        """Encode binary data to base64 string.

        Returns:
            Base64-encoded string representation of the data

        Example:
            >>> content = BinaryContent(b"Hello", mime_type="text/plain")
            >>> encoded = content.to_base64()
            >>> print(encoded)
            SGVsbG8=
        """
        return base64.b64encode(self.data).decode("utf-8")

    @classmethod
    def from_base64(
        cls,
        encoded: str,
        mime_type: str | None = None,
        filename: str | None = None,
        max_size: int | None = None,
    ) -> "BinaryContent":
        """Create BinaryContent from base64-encoded string.

        Args:
            encoded: Base64-encoded string
            mime_type: MIME type of the content
            filename: Optional filename for reference
            max_size: Optional maximum size in bytes

        Returns:
            BinaryContent instance

        Raises:
            ValidationError: If decoding fails or data exceeds max_size

        Example:
            >>> content = BinaryContent.from_base64("SGVsbG8=", "text/plain")
            >>> print(content.data)
            b'Hello'
        """
        try:
            data = base64.b64decode(encoded)
        except Exception as e:
            raise ValidationError(
                f"Failed to decode base64 data: {e}",
                code="INVALID_BASE64",
            ) from e

        return cls(data=data, mime_type=mime_type, filename=filename, max_size=max_size)

    @classmethod
    def from_file(
        cls,
        path: str | Path,
        mime_type: str | None = None,
        max_size: int | None = None,
    ) -> "BinaryContent":
        """Create BinaryContent by reading from a file.

        Args:
            path: Path to the file
            mime_type: Optional MIME type override. If not provided, will be detected
            max_size: Optional maximum size in bytes

        Returns:
            BinaryContent instance

        Raises:
            FileNotFoundError: If file doesn't exist
            ValidationError: If file exceeds max_size

        Example:
            >>> content = BinaryContent.from_file("image.png")
            >>> print(content.mime_type)
            image/png
        """
        path_obj = Path(path)

        if not path_obj.exists():
            raise FileNotFoundError(f"File not found: {path}")

        # Check size before reading if max_size provided
        if max_size is not None:
            file_size = path_obj.stat().st_size
            if file_size > max_size:
                raise ValidationError(
                    f"File size ({file_size} bytes) exceeds maximum ({max_size} bytes)",
                    code="FILE_TOO_LARGE",
                )

        # Read file
        with open(path_obj, "rb") as f:
            data = f.read()

        return cls(
            data=data,
            mime_type=mime_type,
            filename=path_obj.name,
            max_size=max_size,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation suitable for MCP protocol.

        Returns:
            Dictionary with base64-encoded data and metadata

        Example:
            >>> content = BinaryContent(b"Hello", mime_type="text/plain")
            >>> result = content.to_dict()
            >>> print(result.keys())
            dict_keys(['data', 'mime_type', 'encoding', 'size'])
        """
        return {
            "data": self.to_base64(),
            "mime_type": self.mime_type,
            "encoding": "base64",
            "size": self.size,
            "filename": self.filename,
        }

    def is_image(self) -> bool:
        """Check if content is an image.

        Returns:
            True if MIME type indicates image content
        """
        return self.mime_type.startswith("image/")

    def is_pdf(self) -> bool:
        """Check if content is a PDF.

        Returns:
            True if MIME type indicates PDF content
        """
        return self.mime_type == "application/pdf"

    def is_archive(self) -> bool:
        """Check if content is an archive.

        Returns:
            True if MIME type indicates archive content
        """
        archive_types = {
            "application/zip",
            "application/x-zip-compressed",
            "application/gzip",
            "application/x-gzip",
            "application/x-tar",
            "application/x-bzip2",
        }
        return self.mime_type in archive_types

    def __repr__(self) -> str:
        """String representation of BinaryContent."""
        filename_part = f", filename='{self.filename}'" if self.filename else ""
        return f"BinaryContent(size={self.size}, mime_type='{self.mime_type}'{filename_part})"


# Helper functions for common binary types


def read_image(
    path: str | Path,
    max_size: int | None = None,
) -> BinaryContent:
    """Read an image file as BinaryContent.

    This is a convenience function for reading image files with automatic
    MIME type detection.

    Args:
        path: Path to the image file
        max_size: Optional maximum size in bytes

    Returns:
        BinaryContent instance

    Raises:
        FileNotFoundError: If file doesn't exist
        ValidationError: If file exceeds max_size or is not an image

    Example:
        >>> image = read_image("photo.jpg")
        >>> print(image.mime_type)
        image/jpeg
    """
    content = BinaryContent.from_file(path, max_size=max_size)

    if not content.is_image():
        raise ValidationError(
            f"File is not an image: {content.mime_type}",
            code="NOT_AN_IMAGE",
        )

    return content


def read_pdf(
    path: str | Path,
    max_size: int | None = None,
) -> BinaryContent:
    """Read a PDF file as BinaryContent.

    This is a convenience function for reading PDF files.

    Args:
        path: Path to the PDF file
        max_size: Optional maximum size in bytes

    Returns:
        BinaryContent instance

    Raises:
        FileNotFoundError: If file doesn't exist
        ValidationError: If file exceeds max_size or is not a PDF

    Example:
        >>> pdf = read_pdf("document.pdf")
        >>> print(pdf.mime_type)
        application/pdf
    """
    content = BinaryContent.from_file(path, max_size=max_size)

    if not content.is_pdf():
        raise ValidationError(
            f"File is not a PDF: {content.mime_type}",
            code="NOT_A_PDF",
        )

    return content


def read_binary_file(
    path: str | Path,
    mime_type: str | None = None,
    max_size: int | None = None,
) -> BinaryContent:
    """Read any binary file as BinaryContent.

    This is a general-purpose function for reading any binary file.

    Args:
        path: Path to the file
        mime_type: Optional MIME type override
        max_size: Optional maximum size in bytes

    Returns:
        BinaryContent instance

    Raises:
        FileNotFoundError: If file doesn't exist
        ValidationError: If file exceeds max_size

    Example:
        >>> content = read_binary_file("data.bin", mime_type="application/octet-stream")
        >>> print(content.size)
        1024
    """
    return BinaryContent.from_file(path, mime_type=mime_type, max_size=max_size)


def create_binary_resource(
    data: bytes | BinaryContent,
    mime_type: str | None = None,
    filename: str | None = None,
) -> dict[str, Any]:
    """Create a binary resource dictionary suitable for MCP protocol.

    This helper function creates a properly formatted resource dictionary
    that can be returned from resource handlers.

    Args:
        data: Binary data or BinaryContent instance
        mime_type: MIME type (required if data is bytes)
        filename: Optional filename

    Returns:
        Dictionary formatted for MCP resource response

    Raises:
        ValueError: If mime_type not provided when data is bytes

    Example:
        >>> content = BinaryContent(b"Hello", mime_type="text/plain")
        >>> resource = create_binary_resource(content)
        >>> print(resource['mime_type'])
        text/plain
    """
    if isinstance(data, BinaryContent):
        content = data
    else:
        if mime_type is None:
            raise ValueError("mime_type must be provided when data is bytes")
        content = BinaryContent(data, mime_type=mime_type, filename=filename)

    return {
        "content": content.to_base64(),
        "mimeType": content.mime_type,
        "encoding": "base64",
        "size": content.size,
    }


def is_binary_mime_type(mime_type: str) -> bool:
    """Check if a MIME type represents binary content.

    Args:
        mime_type: MIME type to check

    Returns:
        True if MIME type represents binary content

    Example:
        >>> is_binary_mime_type("image/png")
        True
        >>> is_binary_mime_type("text/plain")
        False
    """
    # Text types that should not be treated as binary
    text_types = {
        "text/",
        "application/json",
        "application/xml",
        "application/javascript",
        "application/x-javascript",
    }

    # Check if it's a text type
    for text_type in text_types:
        if mime_type.startswith(text_type):
            return False

    # Check if it's a known binary type
    binary_types = {
        "image/",
        "audio/",
        "video/",
        "application/pdf",
        "application/zip",
        "application/octet-stream",
        "application/x-",
        "font/",
    }

    for binary_type in binary_types:
        if mime_type.startswith(binary_type):
            return True

    # Default to False for unknown types
    return False


__all__ = [
    "BinaryContent",
    "read_image",
    "read_pdf",
    "read_binary_file",
    "create_binary_resource",
    "is_binary_mime_type",
]
