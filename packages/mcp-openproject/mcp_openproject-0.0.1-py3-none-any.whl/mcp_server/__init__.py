"""
MCP OpenProject Server

Provides MCP server integration with OpenProject API.
"""

from .main import main_sync, get_server

__version__ = "0.1.0"
__all__ = ["main_sync", "get_server"]