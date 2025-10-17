"""
MCP OpenProject Server - Main stdio transport implementation

Provides stdio transport for MCP OpenProject server integration.
"""

import asyncio
import sys
import os
import logging
import datetime
import re
from typing import Optional

from mcp import ClientSession, StdioServerParameters
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

# Import OpenProject client
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'openproject_client'))

from openproject_api_client import Configuration, ApiClient
from openproject_api_client.api.projects_api import ProjectsApi
from openproject_api_client.api.work_packages_api import WorkPackagesApi

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create server instance
server = Server("mcp-openproject")


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools."""
    return [
        types.Tool(
            name="list-projects",
            description="List OpenProject projects",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of projects to return"
                    }
                }
            }
        ),
        types.Tool(
            name="get-project",
            description="Get project details by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "integer",
                        "description": "Project ID"
                    }
                },
                "required": ["project_id"]
            }
        ),
        types.Tool(
            name="list-work-packages",
            description="List work packages in a project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "integer",
                        "description": "Project ID"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of work packages to return"
                    }
                },
                "required": ["project_id"]
            }
        ),
        types.Tool(
            name="get-work-package",
            description="Get work package details by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "work_package_id": {
                        "type": "integer",
                        "description": "Work package ID"
                    }
                },
                "required": ["work_package_id"]
            }
        ),
        types.Tool(
            name="generate-weekly-report",
            description="Generate weekly report for a project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "integer",
                        "description": "Project ID"
                    },
                    "week_start": {
                        "type": "string",
                        "description": "Week start date (YYYY-MM-DD format)"
                    },
                    "week_end": {
                        "type": "string",
                        "description": "Week end date (YYYY-MM-DD format)"
                    }
                },
                "required": ["project_id"]
            }
        )
    ]


class OpenProjectClient:
    """OpenProject API client wrapper."""

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.config = Configuration(
            host=self.base_url,
            username="apikey",
            password=api_key
        )

    async def __aenter__(self):
        self.client = ApiClient(self.config)
        self.projects_api = ProjectsApi(self.client)
        self.work_packages_api = WorkPackagesApi(self.client)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if hasattr(self, 'client'):
            # ApiClient 使用 urllib3，是同步客户端，没有 close_async 方法
            # 连接会在垃圾回收时自动关闭，无需手动关闭
            pass


async def get_openproject_client() -> OpenProjectClient:
    """Get OpenProject client from environment variables."""
    base_url = os.getenv("OPENPROJECT_BASE_URL")
    api_key = os.getenv("OPENPROJECT_API_KEY")

    if not base_url or not api_key:
        raise ValueError("OPENPROJECT_BASE_URL and OPENPROJECT_API_KEY environment variables are required")

    return OpenProjectClient(base_url, api_key)


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> list[types.TextContent]:
    """Handle tool calls."""
    try:
        async with await get_openproject_client() as client:
            if name == "list-projects":
                limit = arguments.get("limit", 10) if arguments else 10
                projects = client.projects_api.list_projects()

                project_list = []
                for project in projects.embedded.elements if hasattr(projects.embedded, 'elements') else []:
                    project_list.append({
                        "id": project.id,
                        "name": project.name,
                        "identifier": project.identifier,
                        "description": project.description if hasattr(project, 'description') else None
                    })

                return [types.TextContent(
                    type="text",
                    text=f"Found {len(project_list)} projects:\n" + "\n".join(
                        f"  - {p['name']} (ID: {p['id']}, Identifier: {p['identifier']})"
                        for p in project_list
                    )
                )]

            elif name == "get-project":
                project_id = arguments["project_id"]
                project = client.projects_api.view_project(id=project_id)

                return [types.TextContent(
                    type="text",
                    text=f"Project: {project.name}\n"
                         f"ID: {project.id}\n"
                         f"Identifier: {project.identifier}\n"
                         f"Description: {project.description if hasattr(project, 'description') else 'N/A'}\n"
                         f"Created at: {project.created_at if hasattr(project, 'created_at') else 'N/A'}"
                )]

            elif name == "list-work-packages":
                project_id = arguments["project_id"]
                limit = arguments.get("limit", 10) if arguments else 10
                import json
                # Filter by project only - simple working filter
                work_packages = client.work_packages_api.list_work_packages(
                    filters=json.dumps([
                        {"project": {"operator": "=", "values": [str(project_id)]}}
                    ]),
                    page_size=limit
                )

                wp_list = []
                if hasattr(work_packages, 'embedded') and hasattr(work_packages.embedded, 'elements'):
                    for wp in work_packages.embedded.elements:
                        wp_list.append({
                            "id": wp.id,
                            "subject": wp.subject,
                            "type": getattr(wp, 'type', 'N/A'),
                            "status": getattr(wp, 'status', 'N/A')
                        })

                return [types.TextContent(
                    type="text",
                    text=f"Found {len(wp_list)} work packages:\n" + "\n".join(
                        f"  - {wp['subject']} (ID: {wp['id']}, Type: {wp['type']}, Status: {wp['status']})"
                        for wp in wp_list
                    )
                )]

            elif name == "get-work-package":
                work_package_id = arguments["work_package_id"]
                wp = client.work_packages_api.view_work_package(id=work_package_id)

                return [types.TextContent(
                    type="text",
                    text=f"Work Package: {wp.subject}\n"
                         f"ID: {wp.id}\n"
                         f"Type: {getattr(wp, 'type', 'N/A')}\n"
                         f"Status: {getattr(wp, 'status', 'N/A')}\n"
                         f"Description: {getattr(wp, 'description', 'N/A')}\n"
                         f"Created at: {getattr(wp, 'created_at', 'N/A')}"
                )]

            elif name == "generate-weekly-report":
                project_id = arguments["project_id"]
                week_start = arguments.get("week_start")
                week_end = arguments.get("week_end")

                # Get project details
                project = client.projects_api.view_project(id=project_id)

                # Get work packages for the project
                work_packages = client.work_packages_api.list_work_packages(
                    filters=[{"status_id": {"operator": "!", "values": ["3", "5", "7"]}}],  # Exclude closed, rejected, cancelled
                    sort_by=[["created_at", "desc"]]
                )

                # Generate weekly report
                report_lines = [
                    f"# OpenProject 週報 - {project.name}",
                    f"プロジェクトID: {project_id}",
                    f"週報期間: {week_start or '先週'} ~ {week_end or '本週'}",
                    ""
                ]

                if hasattr(work_packages, 'embedded') and hasattr(work_packages.embedded, 'elements'):
                    wp_list = work_packages.embedded.elements
                    if wp_list:
                        report_lines.append("## 更新された作業パッケージ")
                        report_lines.append("")

                        for wp in wp_list[:10]:  # 最初の10件のみ表示
                            status = getattr(wp, 'status', '不明')
                            assigned_to = getattr(wp, '_links', {}).get('assignee', {}).get('title', '未割り当て')

                            report_lines.append(f"### {wp.subject}")
                            report_lines.append(f"- **ステータス**: {status}")
                            report_lines.append(f"- **担当者**: {assigned_to}")
                            report_lines.append(f"- **タイプ**: {getattr(wp, 'type', 'N/A')}")
                            report_lines.append(f"- **優先度**: {getattr(wp, 'priority', 'N/A')}")

                            if hasattr(wp, 'description') and wp.description:
                                # HTMLタグを除去して簡単な説明文に変換
                                clean_desc = re.sub('<[^<]+?>', '', wp.description)
                                clean_desc = re.sub(r'\s+', ' ', clean_desc).strip()
                                if len(clean_desc) > 100:
                                    clean_desc = clean_desc[:100] + "..."
                                report_lines.append(f"- **説明**: {clean_desc}")

                            report_lines.append("")

                        if len(wp_list) > 10:
                            report_lines.append(f"... 他 {len(wp_list) - 10} 件の作業パッケージ")
                    else:
                        report_lines.append("今週の更新はありません。")
                else:
                    report_lines.append("作業パッケージが見つかりませんでした。")

                report_lines.append("")
                report_lines.append("---")
                report_lines.append(f"レポート生成時刻: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

                return [types.TextContent(
                    type="text",
                    text="\n".join(report_lines)
                )]

            else:
                raise ValueError(f"Unknown tool: {name}")

    except Exception as e:
        logger.error(f"Tool call failed: {e}")
        return [types.TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]


async def main():
    """Main entry point for MCP server."""

    # Check required environment variables
    if not os.getenv("OPENPROJECT_BASE_URL"):
        logger.error("OPENPROJECT_BASE_URL environment variable is required")
        sys.exit(1)

    if not os.getenv("OPENPROJECT_API_KEY"):
        logger.error("OPENPROJECT_API_KEY environment variable is required")
        sys.exit(1)

    # Run the server
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="mcp-openproject",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


def main_sync():
    """Synchronous wrapper for main."""
    asyncio.run(main())


def get_server():
    """Get server instance for MCP entry point."""
    return server


if __name__ == "__main__":
    main_sync()