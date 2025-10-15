# vMCP - Virtual Model Context Protocol

An open-source tool for aggregating and managing multiple MCP servers with a unified interface.

## 🚀 Quickstart

### Prerequisites

vMCP requires [Python 3.10 to 3.13](https://www.python.org/downloads/) and [uv](https://docs.astral.sh/uv/).

### Installation

To install vMCP, run:

```bash
uv pip install vmcp
```

Or use uvx to run directly:

```bash
uvx vmcp run
```

### Running vMCP

To run vMCP locally:

```bash
vmcp run
```

This will start the vMCP server on `http://localhost:7860`.

## 📖 What is vMCP?

vMCP (Virtual Model Context Protocol) is an open-source platform that allows you to:

- **Aggregate Multiple MCP Servers**: Connect to multiple MCP servers (stdio, HTTP, SSE) and manage them from a single interface
- **Create Virtual MCPs**: Combine tools, resources, and prompts from multiple servers into unified virtual endpoints
- **Manage Connections**: Handle MCP server authentication (OAuth, Bearer tokens, Basic auth)
- **Track Usage**: Monitor tool calls, resource reads, and prompt usage with built-in analytics
- **Deploy Anywhere**: Run locally, in Docker, or deploy to cloud platforms

### Key Features

- ✅ **No Authentication Required**: Single local user mode for simplicity
- 🔌 **MCP Protocol Support**: Full support for stdio, HTTP, and SSE transports
- 🔐 **MCP Server Authentication**: OAuth 2.0 support for MCP servers that require it
- 📊 **Usage Statistics**: Track and analyze vMCP usage patterns
- 🐳 **Docker Ready**: Official Docker images for easy deployment
- 🔍 **OpenTelemetry Tracing**: Built-in distributed tracing support
- 📝 **Standard Logging**: Clean logging with DEBUG, INFO, WARNING, ERROR levels

## 🏗️ Architecture

### Components

1. **MCP Servers**: Individual MCP servers you connect to (e.g., filesystem, GitHub, Slack)
2. **VMCPs**: Virtual MCPs that aggregate multiple MCP servers
3. **Storage**: PostgreSQL database for configuration and stats
4. **Web UI**: React-based interface for managing VMCPs and connections

### How it Works

```
┌─────────────┐
│  AI Client  │ (Claude, OpenAI, etc.)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│    vMCP     │ (Virtual MCP Endpoint)
└──────┬──────┘
       │
       ├─────► MCP Server 1 (Filesystem)
       ├─────► MCP Server 2 (GitHub)
       └─────► MCP Server 3 (Slack)
```

## 🛠️ Development

### Project Structure

```
vmcp/
├── src/vmcp/              # Main package
│   ├── backend/           # FastAPI backend
│   │   ├── mcps/          # MCP server management
│   │   ├── vmcps/         # Virtual MCP management
│   │   ├── storage/       # Database models
│   │   ├── proxy_server/  # Main app
│   │   └── utilities/     # Logging & tracing
│   └── cli/               # CLI commands
├── frontend/              # React frontend (Vite)
├── docs/                  # Documentation (Docusaurus)
└── tests/                 # Test suite
```

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/vmcp/vmcp.git
cd vmcp

# Install dependencies
uv sync

# Setup PostgreSQL database
docker run -d \
  --name vmcp-postgres \
  -e POSTGRES_USER=vmcp \
  -e POSTGRES_PASSWORD=vmcp \
  -e POSTGRES_DB=vmcp \
  -p 5432:5432 \
  postgres:15

# Run database migrations
vmcp db init

# Start development server
vmcp run --reload --debug
```

### Environment Variables

Create a `.env` file in the project root:

```env
# Database
DATABASE_URL=postgresql://vmcp:vmcp@localhost:5432/vmcp

# Server
HOST=0.0.0.0
PORT=7860
BASE_URL=http://localhost:7860

# Logging
LOG_LEVEL=INFO

# Tracing (optional)
ENABLE_TRACING=false
OTLP_ENDPOINT=http://localhost:4317
```

## 📊 Usage Examples

### Creating a vMCP

```python
import httpx

# Create a new vMCP
response = httpx.post("http://localhost:7860/vmcps/create", json={
    "name": "my-vmcp",
    "description": "My virtual MCP",
    "mcp_server_ids": [
        "filesystem-server",
        "github-server"
    ]
})

vmcp_id = response.json()["vmcp_id"]
print(f"Created vMCP: {vmcp_id}")
```

### Calling Tools via vMCP

```python
# Call a tool through the vMCP
response = httpx.post(
    f"http://localhost:7860/vmcp/{vmcp_id}/tools/call",
    json={
        "tool_name": "read_file",
        "arguments": {"path": "/tmp/test.txt"}
    }
)

result = response.json()
print(result)
```

## 🐳 Docker Deployment

```bash
# Using Docker Compose
docker-compose up -d

# Or build manually
docker build -t vmcp:latest .
docker run -p 7860:7860 -e DATABASE_URL=postgresql://... vmcp:latest
```

## 📚 Documentation

Full documentation is available at [docs.vmcp.dev](https://docs.vmcp.dev) (coming soon).

### Key Concepts

- **MCP Servers**: Individual servers implementing the Model Context Protocol
- **vMCPs**: Virtual endpoints that aggregate multiple MCP servers
- **Tools**: Functions exposed by MCP servers
- **Resources**: Data sources accessible through MCP servers
- **Prompts**: Templated prompts provided by MCP servers

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=vmcp --cov-report=html

# Run specific test file
pytest tests/test_mcps/test_client.py
```

## 📄 License

vMCP is open-source software licensed under the [MIT License](LICENSE).

## 🙏 Acknowledgments

vMCP is inspired by:
- [Langflow](https://github.com/langflow-ai/langflow) - For the OSS distribution model
- [Model Context Protocol](https://modelcontextprotocol.io/) - The protocol specification
- The MCP community and ecosystem

## 📞 Support

- 🐛 [Report Issues](https://github.com/vmcp/vmcp/issues)
- 💬 [Discussions](https://github.com/vmcp/vmcp/discussions)
- 📧 Email: support@vmcp.dev

---

Made with ❤️ by the vMCP Team
