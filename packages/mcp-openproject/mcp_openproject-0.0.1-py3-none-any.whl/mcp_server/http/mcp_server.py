"""
MCP Server Integration for HTTP Transport

Integrates fastapi_mcp with existing stdio server logic.
Provides MCP HTTP transport by reusing existing tool definitions.
"""

import sys
import os
import structlog
from fastapi import APIRouter
from fastapi_mcp import FastApiMCP

# Set up logging
logger = structlog.get_logger()

# Add parent directory to path for importing existing modules
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import the existing stdio server instance and tools
# This is the key - we reuse existing logic instead of rewriting it
try:
    from mcp_server.main import server as stdio_server
    logger.info("Successfully imported existing stdio server")
except ImportError as e:
    logger.error("Failed to import existing stdio server", error=str(e))
    raise


def setup_mcp_server(fastapi_app):
    """
    Set up MCP server using fastapi_mcp.

    This is the critical integration point where fastapi_mcp automatically
    discovers the tool decorators (@server.list_tools, @server.call_tool)
    from our existing stdio server and exposes them via HTTP transport.

    Args:
        fastapi_app: The FastAPI application instance

    Returns:
        The configured MCP server instance
    """
    logger.info("Setting up MCP HTTP server")

    try:
        # Create MCP server instance
        mcp = FastApiMCP(fastapi_app)

        # Mount Streamable HTTP transport - this automatically discovers and exposes
        # the tools decorated with @server.list_tools and @server.call_tool
        # from our existing stdio server
        mcp.mount_http()

        # Also mount SSE transport for future expansion (commented for now)
        # mcp.mount_sse()

        logger.info(
            "MCP HTTP server mounted successfully",
            endpoint="/mcp",
            transport="Streamable HTTP"
        )

        return mcp

    except Exception as e:
        logger.error("Failed to set up MCP HTTP server", error=str(e))
        raise


def get_mcp_client_config():
    """
    Get MCP client configuration for HTTP mode.

    Returns:
        dict: Configuration for MCP clients to connect via HTTP
    """
    return {
        "mcpServers": {
            "openproject-http": {
                "url": "http://localhost:8000/mcp",
                "description": "OpenProject MCP HTTP Server",
                "transport": "HTTP"
            }
        }
    }


# For direct import and testing
mcp_client_config = get_mcp_client_config()