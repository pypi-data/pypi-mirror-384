"""Builder API - Re-export of BuildMCPServer.

This module re-exports BuildMCPServer from the programmatic API for convenience.
The builder.py name is kept for file organization but the class is BuildMCPServer.
"""

from simply_mcp.api.programmatic import BuildMCPServer

__all__ = ["BuildMCPServer"]
