"""
MCP OpenProject CLI - Command Line Interface

Provides command line interface for MCP OpenProject server operations.
Supports command format: mcp-openproject server --stdio
"""

import argparse
import asyncio
import sys
import os
import logging
from typing import Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import our modules
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Simple config class for CLI
class ServerConfig:
    def __init__(self, openproject_base_url: str, openproject_api_key: str, encryption_key: str):
        self.openproject_base_url = openproject_base_url
        self.openproject_api_key = openproject_api_key
        self.encryption_key = encryption_key

def load_config():
    """Load config from environment variables."""
    return ServerConfig(
        openproject_base_url=os.getenv("OPENPROJECT_BASE_URL", "http://localhost:8080"),
        openproject_api_key=os.getenv("OPENPROJECT_API_KEY", ""),
        encryption_key=os.getenv("ENCRYPTION_KEY", "default-encryption-key")
    )

# Import existing modules
from mcp_server.main import main_sync as stdio_main


def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        prog="mcp-openproject",
        description="MCP OpenProject Server - CLI Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  mcp-openproject server --stdio                    # Run in stdio mode (for MCP clients)
  mcp-openproject server --http --port 8000          # Run in HTTP mode
  mcp-openproject server --sse --port 8001          # Run in SSE mode
  mcp-openproject config                              # Show current configuration
  mcp-openproject status                             # Check server status
  mcp-openproject test                               # Run tests
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Server command
    server_parser = subparsers.add_parser("server", help="Run MCP server")
    server_parser.add_argument(
        "--stdio",
        action="store_true",
        help="Run in stdio mode (for MCP client integration)"
    )
    server_parser.add_argument(
        "--http",
        action="store_true",
        help="Run in HTTP mode"
    )
    server_parser.add_argument(
        "--sse",
        action="store_true",
        help="Run in SSE mode"
    )
    server_parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Server port (default: 8000)"
    )
    server_parser.add_argument(
        "--host",
        type=str,
        default="localhost",
        help="Server host (default: localhost)"
    )

    # Config command
    config_parser = subparsers.add_parser("config", help="Show configuration")

    # Status command
    status_parser = subparsers.add_parser("status", help="Check server status")

    # Test command
    test_parser = subparsers.add_parser("test", help="Run tests")

    # Global arguments
    parser.add_argument(
        "--endpoint",
        type=str,
        help="OpenProject base URL (default: OPENPROJECT_BASE_URL env var)"
    )

    parser.add_argument(
        "--api-key",
        type=str,
        help="OpenProject API key (default: OPENPROJECT_API_KEY env var)"
    )

    parser.add_argument(
        "--encryption-key",
        type=str,
        help="Encryption key (default: ENCRYPTION_KEY env var)"
    )

    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Log level (default: INFO)"
    )

    return parser


def load_config_from_args(args) -> ServerConfig:
    """Load configuration from arguments and environment."""
    # Priority: command line args > environment variables > defaults
    endpoint = args.endpoint or os.getenv("OPENPROJECT_BASE_URL", "http://localhost:8080")
    api_key = args.api_key or os.getenv("OPENPROJECT_API_KEY", "")
    encryption_key = args.encryption_key or os.getenv("ENCRYPTION_KEY", "default-encryption-key")

    return ServerConfig(
        openproject_base_url=endpoint,
        openproject_api_key=api_key,
        encryption_key=encryption_key
    )


def cmd_server(args) -> None:
    """Run MCP server."""
    config = load_config_from_args(args)

    # Set environment variables for compatibility
    if config.openproject_base_url:
        os.environ["OPENPROJECT_BASE_URL"] = config.openproject_base_url
    if config.openproject_api_key:
        os.environ["OPENPROJECT_API_KEY"] = config.openproject_api_key
    if config.encryption_key:
        os.environ["ENCRYPTION_KEY"] = config.encryption_key

    if args.stdio:
        # Use existing stdio server
        logger.info("Starting MCP OpenProject Server in stdio mode...")
        try:
            stdio_main()
        except KeyboardInterrupt:
            logger.info("Received interrupt signal, shutting down...")
        except Exception as e:
            logger.error(f"Server error: {e}")
            raise
    elif args.http:
        # Start HTTP server
        logger.info("Starting MCP OpenProject Server in HTTP mode...")
        try:
            import uvicorn
            from mcp_server.http.app import app

            # Note: MCP server is now automatically set up in app.py via fastapi_mcp
            # No manual setup needed - FastAPI endpoints are automatically converted to MCP tools

            logger.info(f"HTTP server starting on {args.host}:{args.port}")
            logger.info(f"MCP endpoint available at: http://{args.host}:{args.port}/mcp")
            logger.info(f"Health check available at: http://{args.host}:{args.port}/health")

            uvicorn.run(
                app,
                host=args.host,
                port=args.port,
                log_level=args.log_level.lower(),
                reload=False
            )
        except KeyboardInterrupt:
            logger.info("Received interrupt signal, shutting down...")
        except Exception as e:
            logger.error(f"HTTP server error: {e}")
            raise
    elif args.sse:
        print("❌ SSE mode is not yet implemented. Use --stdio or --http mode.")
        return
    else:
        print("❌ Please specify a transport mode: --stdio, --http, or --sse")
        return


def cmd_config(args) -> None:
    """Show current configuration."""
    config = load_config_from_args(args)

    print("MCP OpenProject Configuration:")
    print(f"  Endpoint: {config.openproject_base_url}")
    print(f"  API Key: {'***' + config.openproject_api_key[-4:] if config.openproject_api_key else 'Not set'}")
    print(f"  Encryption Key: {'***' + config.encryption_key[-4:] if config.encryption_key != 'default-encryption-key' else 'Default'}")

    # Check environment variables
    print("\nEnvironment Variables:")
    print(f"  OPENPROJECT_BASE_URL: {os.getenv('OPENPROJECT_BASE_URL', 'Not set')}")
    print(f"  OPENPROJECT_API_KEY: {'Set' if os.getenv('OPENPROJECT_API_KEY') else 'Not set'}")
    print(f"  ENCRYPTION_KEY: {'Set' if os.getenv('ENCRYPTION_KEY') else 'Not set'}")


def cmd_status(args) -> bool:
    """Check server status."""
    config = load_config_from_args(args)

    if not config.openproject_api_key:
        print("❌ Error: API key not configured")
        return False

    print("✅ MCP OpenProject Server Status:")
    print(f"  Endpoint: {config.openproject_base_url}")
    print(f"  API Key: {'Configured' if config.openproject_api_key else 'Not configured'}")
    print("  Note: Use 'mcp-openproject test' to test API connectivity")
    return True


def cmd_test(args) -> bool:
    """Run basic tests."""
    config = load_config_from_args(args)

    if not config.openproject_api_key:
        print("❌ Error: API key not configured")
        return False

    print("🧪 Running MCP OpenProject Tests...")

    # Test configuration
    print("  Testing configuration...")
    if config.openproject_base_url:
        print(f"  ✅ Endpoint configured: {config.openproject_base_url}")
    else:
        print("  ❌ Endpoint not configured")
        return False

    if config.openproject_api_key:
        print("  ✅ API key configured")
    else:
        print("  ❌ API key not configured")
        return False

    print("\n✅ Basic configuration tests passed!")
    print("  Note: Full API tests require OpenProject server connectivity")
    return True


def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    # Set log level
    logging.getLogger().setLevel(getattr(logging, args.log_level))

    # Route to appropriate command
    if args.command == "server":
        cmd_server(args)
    elif args.command == "config":
        cmd_config(args)
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "test":
        cmd_test(args)
    else:
        # Default behavior - show help
        parser.print_help()


# Entry points for pyproject.toml
def server():
    """Server command entry point (for pyproject.toml)."""
    parser = argparse.ArgumentParser(prog="mcp-openproject-server")
    parser.add_argument("--stdio", action="store_true", help="Run in stdio mode")
    parser.add_argument("--http", action="store_true", help="Run in HTTP mode")
    parser.add_argument("--sse", action="store_true", help="Run in SSE mode")
    parser.add_argument("--port", type=int, default=8000, help="Server port")
    parser.add_argument("--host", type=str, default="localhost", help="Server host")

    args = parser.parse_args()

    # Create minimal args object
    class SimpleArgs:
        def __init__(self):
            self.endpoint = None
            self.api_key = None
            self.encryption_key = None
            self.stdio = args.stdio
            self.http = args.http
            self.sse = args.sse
            self.port = args.port
            self.host = args.host
            self.log_level = "INFO"

    cmd_server(SimpleArgs())


def config():
    """Config command entry point."""
    class SimpleArgs:
        def __init__(self):
            self.endpoint = None
            self.api_key = None
            self.encryption_key = None

    cmd_config(SimpleArgs())


def status():
    """Status command entry point."""
    class SimpleArgs:
        def __init__(self):
            self.endpoint = None
            self.api_key = None
            self.encryption_key = None

    cmd_status(SimpleArgs())


def test():
    """Test command entry point."""
    class SimpleArgs:
        def __init__(self):
            self.endpoint = None
            self.api_key = None
            self.encryption_key = None

    cmd_test(SimpleArgs())


if __name__ == "__main__":
    main()