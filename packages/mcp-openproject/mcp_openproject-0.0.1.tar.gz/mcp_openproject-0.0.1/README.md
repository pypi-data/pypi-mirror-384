# MCP OpenProject Server

A Model Context Protocol (MCP) server for integrating OpenProject with AI assistants like Claude, Windsurf, and other MCP-compatible clients.

## 🚀 Quick Start - 5 Minutes to Running

### Option 1: Install from GitHub (Recommended for Users)

```bash
# Install globally from GitHub
pipx install git+https://github.com/boma086/mcp-openproject.git

# Set environment variables
export OPENPROJECT_BASE_URL="http://localhost:8090/"
export OPENPROJECT_API_KEY="your-api-key-here"
export ENCRYPTION_KEY="your-encryption-key-here"

# Test installation
mcp-openproject --help
```

### Option 2: Development Installation

```bash
# Clone repository
git clone https://github.com/boma086/mcp-openproject.git
cd mcp-openproject

# Install in development mode
pip install -e .

# Set environment variables
export OPENPROJECT_BASE_URL="http://localhost:8090/"
export OPENPROJECT_API_KEY="your-api-key-here"
export ENCRYPTION_KEY="your-encryption-key-here"
```

### Option 3: Smithery Platform (Cloud Deployment)

For cloud deployment without local installation, use the [Smithery Platform](https://smithery.ai):

1. Visit the MCP OpenProject server on Smithery
2. Configure your OpenProject instance URL and API key
3. Start using immediately - no installation required

## ⚙️ MCP Client Configuration

### Claude Code / Windsurf Configuration

Add this to your MCP client configuration:

```json
{
  "mcpServers": {
    "openproject": {
      "command": "mcp-openproject",
      "args": ["server", "--stdio"],
      "env": {
        "OPENPROJECT_BASE_URL": "http://localhost:8090/",
        "OPENPROJECT_API_KEY": "your-api-key-here",
        "ENCRYPTION_KEY": "your-encryption-key-here"
      }
    }
  }
}
```

**Two-step process for MCP clients:**
1. **Install**: `pipx install git+https://github.com/boma086/mcp-openproject.git`
2. **Configure**: Add the JSON configuration above to your MCP client

## Features

- **🚀 GitHub Installation**: Install directly from GitHub with pipx
- **📡 Multiple Transport Modes**: Stdio and HTTP support (SSE planned)
- **🔗 OpenProject API Integration**: Complete access to projects, work packages, and tasks
- **🛡️ Security**: Encrypted configuration and API key management
- **🖥️ CLI Interface**: Comprehensive command-line tools
- **🎯 MCP Compatible**: Works with Claude Code, Windsurf, and other MCP clients
- **☁️ Cloud Ready**: Smithery platform support for zero-install deployment

## Configuration

### Required Environment Variables

- `OPENPROJECT_BASE_URL`: Your OpenProject instance URL (e.g., `http://localhost:8090/`)
- `OPENPROJECT_API_KEY`: Your OpenProject API key
- `ENCRYPTION_KEY`: Encryption key for sensitive data (generate one: `openssl rand -hex 32`)

### Example Configuration

```bash
# Add to your ~/.bashrc or ~/.zshrc
export OPENPROJECT_BASE_URL="http://localhost:8090/"
export OPENPROJECT_API_KEY="your-api-key-here"
export ENCRYPTION_KEY="your-32-byte-encryption-key-here"
```

## CLI Commands

```bash
# Show help
mcp-openproject --help

# Test connection to OpenProject
mcp-openproject test

# Show current configuration
mcp-openproject config

# Start MCP server in different modes
mcp-openproject server --stdio          # Stdio mode (for MCP clients)
mcp-openproject server --http --port 8000  # HTTP mode

# Check server status
mcp-openproject status
```

## Available MCP Tools

- **Project Management**: List projects, get project details, project statistics
- **Work Packages**: Create, read, update work packages and tasks
- **Weekly Reports**: Generate weekly reports for projects
- **Time Tracking**: Log time entries, track project hours
- **Team Management**: Access user information and team assignments

## MCP Client Integration

### Claude Code Configuration

Add to your Claude Code configuration:

```json
{
  "mcpServers": {
    "openproject": {
      "command": "mcp-openproject",
      "args": ["server", "--stdio"],
      "env": {
        "OPENPROJECT_BASE_URL": "http://localhost:8090/",
        "OPENPROJECT_API_KEY": "your-api-key-here",
        "ENCRYPTION_KEY": "your-encryption-key-here"
      }
    }
  }
}
```

### Windsurf Configuration

**Step 1: Install MCP Server**
```bash
pipx install git+https://github.com/boma086/mcp-openproject.git
```

**Step 2: Add to Windsurf MCP Configuration**
```json
{
  "mcpServers": {
    "openproject": {
      "command": "mcp-openproject",
      "args": ["server", "--stdio"],
      "env": {
        "OPENPROJECT_BASE_URL": "http://localhost:8090/",
        "OPENPROJECT_API_KEY": "your-api-key-here",
        "ENCRYPTION_KEY": "your-encryption-key-here"
      }
    }
  }
}
```

### General MCP Client Configuration

For any MCP-compatible client:

1. **Install the server**: `pipx install git+https://github.com/boma086/mcp-openproject.git`
2. **Configure environment variables** (as shown above)
3. **Add MCP server configuration**:
   ```json
   {
     "mcpServers": {
       "openproject": {
         "command": "mcp-openproject",
         "args": ["server", "--stdio"]
       }
     }
   }
   ```

## Deployment Options

### Local Development

```bash
# Clone and install
git clone https://github.com/boma086/mcp-openproject.git
cd mcp-openproject
pip install -e .

# Run in development mode
uv run mcp-openproject server --stdio
uv run mcp-openproject server --http --port 8000
```

### Production Installation

```bash
# Install from GitHub
pipx install git+https://github.com/boma086/mcp-openproject.git

# Run as system service
sudo systemctl enable mcp-openproject
sudo systemctl start mcp-openproject
```

### Cloud Deployment (Smithery)

No installation required - configure and run directly on Smithery platform:
1. Visit [Smithery MCP OpenProject](https://smithery.ai)
2. Configure OpenProject connection
3. Start using immediately

## Architecture

This project uses a comprehensive architecture with:

- **MCP Server**: FastMCP-based implementation with multiple transport modes
- **OpenProject Integration**: Generated API client with full OpenProject support
- **Security Framework**: Encrypted configuration and API key management
- **CLI Interface**: Comprehensive command-line tools for all operations
- **Documentation**: Complete project documentation and guides

### Key Components

- `mcp_server/`: Core MCP server implementation
- `docs/`: Comprehensive documentation and guides
- `pyproject.toml`: Project configuration with comprehensive dependency management
- `smithery.yaml`: Smithery platform deployment configuration

## Transport Modes

### ✅ Stdio Mode (Recommended for MCP Clients)
- **Use Case**: Direct integration with Claude Code, Windsurf, and other MCP clients
- **Command**: `mcp-openproject server --stdio`
- **Benefits**: Standard MCP protocol, low latency, secure

### ✅ HTTP Mode (For Web Integration)
- **Use Case**: Web applications, HTTP API integration
- **Command**: `mcp-openproject server --http --port 8000`
- **Benefits**: RESTful API, web-friendly, CORS support

### 🚧 SSE Mode (Planned)
- **Status**: Planned for future release
- **Use Case**: Real-time updates, streaming responses
- **Command**: `mcp-openproject server --sse --port 8001` (future)

## Support

### Documentation
- **Installation Guide**: [docs/installation.md](docs/installation.md)
- **Configuration Guide**: [docs/guides/configuration-guide.md](docs/guides/configuration-guide.md)
- **Troubleshooting**: [docs/troubleshooting.md](docs/troubleshooting.md)
- **Architecture**: [docs/architecture/](docs/architecture/)

### Getting Help
- **GitHub Issues**: [Report bugs](https://github.com/boma086/mcp-openproject/issues)
- **GitHub Discussions**: [Community discussions](https://github.com/boma086/mcp-openproject/discussions)
- **Documentation**: [Full documentation](https://github.com/boma086/mcp-openproject/tree/main/docs)

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/boma086/mcp-openproject.git
cd mcp-openproject

# Install development dependencies
pip install -e ".[dev]"

# Run tests
uv run pytest

# Run linting
uv run ruff check
uv run black .
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and updates.