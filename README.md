# 💰 Budget MCP Server

A Model Context Protocol (MCP) server enabling AI agents to manage budgets using the cash envelope system. Supports both HTTP and stdio transports with optional MotherDuck cloud integration.

## ✨ Features

- **💸 Cash Envelope Budgeting**: Create envelopes, track transactions, monitor balances
- **🔄 Dual Transport**: HTTP (with bearer token auth) + stdio for Claude Desktop
- **☁️ MotherDuck Integration**: Local/cloud/hybrid database modes with sync
- **🐳 Docker Support**: Containerized deployment options
- **🔒 HTTPS Support**: Optional SSL/TLS encryption

**Tech Stack**: Python 3.12+, FastMCP, DuckDB, MotherDuck, uv, pytest

## 📦 Installation

### ⚡ Quick Start (uvx - Recommended)

```bash
# Install and run directly
uvx --from git+https://github.com/<OWNER>/budget-mcp-server budget-mcp-server
```

### 🛠️ Development Setup

1. **Clone and install:**
```bash
git clone <repository-url>
cd budget-mcp-server
uv sync
```

2. **Configure environment:**
```bash
# Interactive setup (recommended)
./setup-env.sh

# Or manual setup
BEARER_TOKEN=$(openssl rand -hex 32)
echo "BEARER_TOKEN=$BEARER_TOKEN" > .env
echo "APP_ENV=development" >> .env
```

3. **Run server:**
```bash
uv run python run.py  # HTTP transport at http://127.0.0.1:8000/mcp
```

### 🐳 Docker

```bash
docker compose up budget-mcp-server-dev  # Development
docker compose --profile prod up budget-mcp-server  # Production
```

### ☁️ MotherDuck Cloud (Optional)

For cloud database integration:
```bash
export MOTHERDUCK_TOKEN="your-token"  # Get from motherduck.com
export DATABASE_MODE="cloud"  # Options: local, cloud, hybrid
uv run python run.py
```

## 🤖 AI Assistant Integration

### 🖥️ Claude Desktop (stdio)

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "budget-envelope": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/<OWNER>/budget-mcp-server", "budget-mcp-server"],
      "env": {
        "APP_ENV": "production",
        "MOTHERDUCK_TOKEN": "your-token-here"
      }
    }
  }
}
```

### 🌐 HTTP Clients

Connect to `http://127.0.0.1:8000/mcp` with bearer token authentication:

```bash
curl -H "Authorization: Bearer $BEARER_TOKEN" \
     -H "Content-Type: application/json" \
     -X POST http://127.0.0.1:8000/mcp/ \
     -d '{"jsonrpc": "2.0", "method": "get_budget_summary", "id": 1}'
```

## 🔧 MCP Tools

### 🎯 Core Tools
- **📋 Envelopes**: `create_envelope`, `list_envelopes`, `get_envelope`, `update_envelope`, `delete_envelope`
- **💳 Transactions**: `create_transaction`, `list_transactions`, `get_transaction`, `update_transaction`, `delete_transaction`
- **📊 Utilities**: `get_envelope_balance`, `get_budget_summary`
- **☁️ Cloud Sync**: `get_cloud_status`, `sync_to_cloud`, `sync_from_cloud`

## 💬 Usage Examples

Interact with your budget using natural language:

- *"Create a grocery budget envelope with $500 allocated"*
- *"I spent $75.50 at the grocery store today"*
- *"How much money do I have left in my grocery budget?"*
- *"Show me a summary of all my budget categories"*
- *"Sync my budget data to the cloud"*

## 🔨 Development

### 🧪 Testing
```bash
uv run pytest                     # All tests
uv run pytest tests/test_*.py     # Specific test files
```

### ⚙️ Environment Variables
- `BEARER_TOKEN`: Required for HTTP transport (generate with `openssl rand -hex 32`)
- `APP_ENV`: development/production/testing (default: development)
- `DATABASE_FILE`: DuckDB file path (default: ~/.local/share/budget-mcp-server/budget_app.duckdb)
- `HOST`/`PORT`: Server binding (default: 127.0.0.1:8000)
- `MOTHERDUCK_TOKEN`: Optional cloud database token
- `DATABASE_MODE`: local/cloud/hybrid (default: hybrid, auto-switches to local if no token)

## 🤝 Contributing

1. Fork and create feature branch
2. Follow SOLID principles and TDD
3. Ensure tests pass (`uv run pytest`)
4. Submit pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) file.
