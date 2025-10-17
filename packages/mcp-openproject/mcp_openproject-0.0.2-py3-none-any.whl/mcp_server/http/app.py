"""
Minimal FastAPI-MCP Server - Clean version with only essential fixes
"""

import structlog
import asyncio
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi_mcp import FastApiMCP, AuthConfig
from .auth import verify_mcp_client, get_client_auth_info
import os
import sys
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up structured logging
logger = structlog.get_logger()

# Add parent directory to path for importing existing modules
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import OpenProject client from existing stdio server
from mcp_server.main import OpenProjectClient, get_openproject_client

# Create FastAPI application
app = FastAPI(
    title="MCP OpenProject HTTP Server",
    description="HTTP transport for MCP OpenProject integration using fastapi_mcp",
    version="0.1.0"
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

# Global client management for OpenProject
_global_client: Optional[OpenProjectClient] = None
_client_lock = None

async def get_openproject_client_singleton():
    """Get global OpenProject client, initialize only once."""
    global _global_client, _client_lock

    async with _client_lock:
        if _global_client is None:
            logger.info("Initializing global OpenProject client")
            base_url = os.getenv("OPENPROJECT_BASE_URL")
            api_key = os.getenv("OPENPROJECT_API_KEY")

            if not base_url or not api_key:
                raise HTTPException(
                    status_code=500,
                    detail="OPENPROJECT_BASE_URL and OPENPROJECT_API_KEY environment variables are required"
                )

            _global_client = OpenProjectClient(base_url, api_key)
            await _global_client.__aenter__()

            logger.info("Global OpenProject client initialized successfully",
                       base_url=base_url[:50] + "...")

        return _global_client

# Dependency to get OpenProject client
async def get_client() -> OpenProjectClient:
    """FastAPI dependency: return initialized OpenProject client."""
    try:
        return await get_openproject_client_singleton()
    except Exception as e:
        logger.error("Failed to get OpenProject client", error=str(e))
        raise HTTPException(status_code=500, detail="OpenProject client initialization failed")

# Simple test endpoint
@app.get("/test", operation_id="simple_test")
async def simple_test():
    """Simple test endpoint for MCP debugging."""
    return {"message": "Hello from MCP!", "status": "working"}

# Weekly report endpoint with minimal fixes
@app.get("/projects/{project_id}/weekly-report", operation_id="generate_weekly_report")
async def generate_weekly_report(
    project_id: int,
    client: OpenProjectClient = Depends(get_client),
    week_start: Optional[str] = None,
    week_end: Optional[str] = None
):
    """Generate weekly report for a project."""
    import datetime
    import json

    # Validate parameters
    if week_start == "null":
        week_start = None
    if week_end == "null":
        week_end = None

    try:
        # Get project details
        project = client.projects_api.view_project(id=project_id)

        # Get work packages for project
        work_packages = client.work_packages_api.list_work_packages(
            filters=json.dumps([
                {"project": {"operator": "=", "values": [str(project_id)]}},
                {"status_id": {"operator": "!", "values": ["3", "5", "7"]}}
            ])
        )

        # Generate simple report
        report_lines = [
            f"# OpenProject 週報 - {getattr(project, 'name', f'Project {project_id}')}",
            f"プロジェクトID: {project_id}",
            f"週報期間: {week_start or '先週'} ~ {week_end or '本週'}",
            ""
        ]

        if hasattr(work_packages, 'embedded') and hasattr(work_packages.embedded, 'elements'):
            wp_list = work_packages.embedded.elements
            if wp_list:
                report_lines.append("## 更新された作業パッケージ")
                report_lines.append("")

                for wp in wp_list[:5]:
                    report_lines.append(f"### {getattr(wp, 'subject', 'No subject')}")
                    report_lines.append(f"- **ステータス**: {getattr(wp, 'status', '不明')}")
                    report_lines.append("")
            else:
                report_lines.append("今週の更新はありません。")
        else:
            report_lines.append("作業パッケージが見つかりませんでした。")

        report_lines.append("")
        report_lines.append("---")
        report_lines.append(f"レポート生成時刻: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        return {"report": "\n".join(report_lines)}

    except Exception as e:
        logger.error("Error generating weekly report", error=str(e), project_id=project_id)
        return {"report": f"エラー: 週報の生成に失敗しました ({str(e)})"}

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "service": "mcp-openproject-http",
        "version": "0.1.0"
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "MCP OpenProject HTTP Server",
        "version": "0.1.0",
        "transport": "Streamable HTTP",
        "mcp_endpoint": "/mcp"
    }

# Initialize fastapi_mcp (simplified version for now)
mcp = FastApiMCP(
    app,
    name="OpenProject MCP Server",
    description="MCP server for OpenProject integration with HTTP transport"
)
# Mount MCP server using streamable HTTP transport
mcp.mount_http()

@app.on_event("startup")
async def startup_event():
    """Log application startup and initialize global resources."""
    global _client_lock

    # Initialize client lock
    _client_lock = asyncio.Lock()

    logger.info(
        "MCP OpenProject HTTP Server starting up",
        version="0.1.0",
        transport="Streamable HTTP",
        mcp_endpoint="/mcp"
    )

@app.on_event("shutdown")
async def shutdown_event():
    """Log application shutdown and cleanup global resources."""
    global _global_client

    if _global_client:
        try:
            await _global_client.__aexit__(None, None, None)
            logger.info("Global OpenProject client cleaned up successfully")
        except Exception as e:
            logger.error("Failed to cleanup global OpenProject client", error=str(e))

    logger.info("MCP OpenProject HTTP Server shutting down")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
# Configuration check endpoint for Smithery deployment validation
@app.get("/config", operation_id="check_configuration")
async def check_configuration():
    """Check current configuration status for deployment validation."""
    import os
    
    base_url = os.getenv("OPENPROJECT_BASE_URL")
    api_key = os.getenv("OPENPROJECT_API_KEY") 
    encryption_key = os.getenv("ENCRYPTION_KEY")
    
    # Mask sensitive values in response
    masked_api_key = "***" + (api_key[-4:] if api_key and len(api_key) > 4 else "***")
    masked_encryption_key = "***" + (encryption_key[-4:] if encryption_key and len(encryption_key) > 4 else "***")
    
    return {
        "status": "configured",
        "openproject_configured": bool(base_url and api_key),
        "encryption_configured": bool(encryption_key),
        "openproject_base_url": base_url,
        "openproject_api_key": masked_api_key,
        "encryption_key": masked_encryption_key,
        "mcp_endpoint": "/mcp",
        "health_endpoint": "/health"
    }

# Client configuration endpoint for MCP client setup
@app.get("/client-config", operation_id="get_client_config")
async def get_client_config():
    """Get client configuration for MCP client setup."""
    try:
        auth_info = get_client_auth_info()
        return {
            "status": "ready",
            "mcp_endpoint": "/mcp",
            "auth_required": True,
            "auth_config": auth_info,
            "windsurf_config": {
                "url": "http://localhost:8000/mcp",
                "auth": {
                    "type": "bearer",
                    "token": auth_info["auth_token"]
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Configuration error: {str(e)}")
