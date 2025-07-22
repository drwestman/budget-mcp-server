# Budget MCP Server

A Model Context Protocol (MCP) Server that enables AI agents to manage household or business budgets using the cash envelope system. This server provides tools for AI agents to create budget envelopes, track transactions, and monitor financial allocations through the MCP protocol.

## What is MCP?

The [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) is an open standard that enables AI assistants to securely connect to external data sources and tools. This budget server implements MCP to allow AI agents like Claude to directly interact with your budget data.

## Features

- **AI Agent Integration**: Designed for seamless integration with AI assistants via MCP
- **Dual Transport Support**: FastMCP with Streamable HTTP transport + stdio transport
- **Web-Accessible**: HTTP endpoint for modern MCP clients and web integrations
- **Bearer Token Authentication**: Secure HTTP transport with configurable token-based authentication
- **MotherDuck Cloud Integration**: Seamless cloud database connectivity with local/cloud/hybrid modes
- **Cloud Data Synchronization**: Bidirectional sync between local DuckDB and MotherDuck cloud
- **Multi-Environment Support**: Local-first, cloud-first, or hybrid database workflows
- **Cash Envelope Budgeting**: Create and manage budget categories with allocated amounts
- **Transaction Management**: Track income and expense transactions against budget envelopes
- **Real-time Balance Tracking**: Monitor current balances and budget summaries
- **Lightweight Database**: Uses DuckDB for fast, embedded database operations with optional cloud storage
- **Modern Python Tooling**: Built with FastMCP (>=2.3.0) and uv for fast, reliable development
- **HTTPS Support**: Optional SSL/TLS encryption with self-signed certificates for development
- **Docker Support**: Containerized deployment for development and production

## Tech Stack

- **Runtime**: Python 3.12+
- **MCP Framework**: FastMCP with Streamable HTTP transport
- **Protocol**: Model Context Protocol (MCP)
- **Database**: DuckDB with MotherDuck cloud integration
- **Cloud Platform**: MotherDuck (cloud-native DuckDB service)
- **Package Management**: uv
- **Testing**: pytest
- **Containerization**: Docker, Docker Compose
- **Architecture**: SOLID principles, Test-Driven Development (TDD)

## Installation

### uvx Installation (Recommended for Users)

The easiest way to install and run the MCP server is using uvx:

```bash
# Install and run directly from GitHub
uvx --from git+https://github.com/<OWNER>/budget-mcp-server budget-mcp-server

# Or install from a local directory
uvx --from . budget-mcp-server
```

**Benefits of uvx installation:**
- Automatic dependency management
- Isolated environment execution
- Direct stdio transport for MCP clients
- No manual Python environment setup required

**Environment Configuration:**
- `APP_ENV`: Set to 'production', 'development', or 'testing' (default: development)
- Database file location: `budget_app.duckdb` in current directory
- In development mode, database persists between runs

### Development Installation

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

### Using uv (Recommended)

1. Clone the repository:
```bash
git clone <repository-url>
cd budget-mcp-server
```

2. Install dependencies with uv:
```bash
uv sync
```

3. Set up environment configuration:

#### Option A: Interactive Setup Script (Recommended)
```bash
# Run the interactive setup script
./setup-env.sh
```

The script will guide you through:
- **Environment Selection**: Choose development, production, or testing
- **Database Configuration**: Set database file path with environment-specific defaults
- **Authentication Setup**: Auto-generate secure bearer token or provide custom token
- **MotherDuck Integration**: Configure cloud database connectivity and sync options
- **Server Configuration**: Configure host, port, and MCP endpoint path
- **HTTPS Configuration**: Optionally enable HTTPS with SSL certificate setup
- **Certificate Generation**: Generate self-signed certificates if needed

**Key Features:**
- Press Enter to accept sensible defaults for all prompts
- Automatic backup of existing `.env` files
- Auto-generated secure bearer tokens using OpenSSL
- Environment-specific configuration defaults
- Optional SSL certificate generation integration

#### Option B: Manual Setup
```bash
# Set bearer token for authentication (required)
BEARER_TOKEN=$(openssl rand -hex 32)
echo "BEARER_TOKEN=$BEARER_TOKEN" > .env

# Add other environment variables as needed
echo "APP_ENV=development" >> .env
echo "DATABASE_FILE=budget_app.duckdb" >> .env
echo "HOST=127.0.0.1" >> .env
echo "PORT=8000" >> .env
echo "MCP_PATH=/mcp" >> .env
echo "HTTPS_ENABLED=false" >> .env

# Optional: Configure MotherDuck cloud integration
echo "MOTHERDUCK_TOKEN=your-motherduck-token" >> .env
echo "MOTHERDUCK_DATABASE=budget_app" >> .env
echo "DATABASE_MODE=local" >> .env  # Options: local, cloud, hybrid
echo "MOTHERDUCK_SYNC_ON_START=false" >> .env
```

4. Run the server:
```bash
uv run python run.py
```

The server will start with Streamable HTTP transport on `http://127.0.0.1:8000/mcp`

**⚠️ Security Note**: The `BEARER_TOKEN` environment variable is **required** for HTTP transport. The server will not start without it.

### HTTPS Setup (Optional)

For secure connections, you can enable HTTPS with self-signed certificates:

#### Option A: Using Setup Script (Recommended)
```bash
# Run the interactive setup script and enable HTTPS when prompted
./setup-env.sh
```

The script will:
- Prompt you to enable HTTPS
- Configure SSL certificate file paths
- Offer to generate self-signed certificates automatically
- Set up the complete HTTPS configuration

#### Option B: Manual HTTPS Setup
1. **Generate certificates:**
```bash
uv run python scripts/generate_cert.py
```

2. **Configure environment:**
```bash
# Set bearer token and enable HTTPS (reads BEARER_TOKEN from .env if available)
HTTPS_ENABLED=true uv run python run.py

# Or set bearer token manually if needed
BEARER_TOKEN=$(openssl rand -hex 32) HTTPS_ENABLED=true uv run python run.py
```

The server will be available at `https://127.0.0.1:8000/mcp`

See [HTTPS_SETUP.md](HTTPS_SETUP.md) for detailed HTTPS configuration instructions.

### MotherDuck Cloud Integration Setup

MotherDuck extends DuckDB with cloud storage, sharing, and analytics capabilities. The server supports three database modes:

#### Database Modes

1. **Local Mode** (Default): Standard DuckDB file storage
2. **Cloud Mode**: Pure MotherDuck cloud database  
3. **Hybrid Mode**: Local DuckDB with MotherDuck attachment for cross-database operations

#### Quick Setup

**Option A: Interactive Setup (Recommended)**
```bash
# Run setup script and configure MotherDuck when prompted
./setup-env.sh
```

**Option B: Manual Configuration**
```bash
# Get your MotherDuck token from: https://motherduck.com/
export MOTHERDUCK_TOKEN="your-motherduck-token"
export MOTHERDUCK_DATABASE="budget_app"
export DATABASE_MODE="cloud"  # or "hybrid" for local+cloud
export MOTHERDUCK_SYNC_ON_START="true"  # Auto-sync on startup

# Run with cloud database
uv run python run.py
```

#### Configuration Options

- **`MOTHERDUCK_TOKEN`**: Your MotherDuck access token (required for cloud/hybrid modes)
- **`MOTHERDUCK_DATABASE`**: Cloud database name (default: "budget_app")
- **`DATABASE_MODE`**: Connection mode - "local", "cloud", or "hybrid" (default: "local")
- **`MOTHERDUCK_SYNC_ON_START`**: Auto-sync local data to cloud on startup (default: false)

#### Getting Started with MotherDuck

1. **Sign up**: Create account at [motherduck.com](https://motherduck.com/)
2. **Get token**: Generate access token in MotherDuck console
3. **Configure**: Run `./setup-env.sh` and select MotherDuck integration
4. **Choose mode**: Select local/cloud/hybrid based on your needs
5. **Sync data**: Use cloud-specific tools to sync existing data

### Docker Setup

#### Development Mode (Default)
```bash
# Docker automatically reads BEARER_TOKEN from .env file
docker compose up budget-mcp-server-dev

# Or set bearer token manually if needed
BEARER_TOKEN=$(openssl rand -hex 32) docker compose up budget-mcp-server-dev
```

#### Production Mode
```bash
# Docker automatically reads BEARER_TOKEN from .env file
docker compose --profile prod up budget-mcp-server

# Or set bearer token manually if needed
BEARER_TOKEN=$(openssl rand -hex 32) docker compose --profile prod up budget-mcp-server
```

## Integration with AI Assistants

This MCP server supports both modern HTTP transport and stdio transport for maximum compatibility.

### FastMCP HTTP Integration (Recommended)

The server runs with Streamable HTTP transport by default, making it accessible via HTTP:

```bash
# Run server (reads BEARER_TOKEN from .env file automatically)
python run.py
# Server available at: http://127.0.0.1:8000/mcp

# Or set bearer token manually if needed
BEARER_TOKEN=$(openssl rand -hex 32) python run.py
```

**Client Authentication:**
```bash
# Example HTTP request with bearer token
curl -H "Authorization: Bearer your-token-here" \
     -H "Content-Type: application/json" \
     -H "Accept: application/json, text/event-stream" \
     -X POST http://127.0.0.1:8000/mcp/ \
     -d '{"jsonrpc": "2.0", "method": "list_envelopes", "id": 1}'
```

**Environment Variables:**
- `BEARER_TOKEN`: **REQUIRED** - Bearer token for HTTP authentication (generate with `openssl rand -hex 32`)
  - Can be set in `.env` file or as environment variable
  - Docker Compose automatically reads from `.env` file
- `HOST`: Server host (default: 127.0.0.1) - the address the server will bind to.
- `PORT`: Server port (default: 8000) - the TCP port for HTTP transport.
- `MCP_PATH`: MCP endpoint path (default: /mcp) - the HTTP path where the MCP endpoint is exposed.
- `APP_ENV`: Environment mode (development/production/testing) - the application environment (development, production, or testing), affecting logging and database persistence.
- `HTTPS_ENABLED`: Enable HTTPS mode (default: false) - set to 'true' to enable SSL/TLS encryption.
- `SSL_CERT_FILE`: Path to SSL certificate file (default: certs/server.crt) - PEM format certificate file.
- `SSL_KEY_FILE`: Path to SSL private key file (default: certs/server.key) - PEM format private key file.
- `MOTHERDUCK_TOKEN`: MotherDuck access token (optional) - for cloud database integration.
- `DATABASE_MODE`: Database mode (default: local) - options: "local", "cloud", "hybrid".

### Claude Desktop Integration (stdio)

For Claude Desktop, use the stdio transport mode:

Add the following to your Claude Desktop configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "budget-envelope": {
      "command": "uv",
      "args": ["run", "python", "${PWD}/run_stdio.py"],
      "cwd": "/path/to/budget-mcp-server"
    }
  }
}
```

**🔓 Note**: stdio transport does not require bearer token authentication as it operates over standard input/output streams, not HTTP.

### Other MCP Clients

**HTTP Transport (Modern):**
Connect to `http://127.0.0.1:8000/mcp` using any HTTP MCP client with bearer token authentication

**HTTPS Transport (Secure):**
Connect to `https://127.0.0.1:8000/mcp` when HTTPS is enabled (requires certificate configuration and bearer token)

**stdio Transport:**
Run `run_stdio.py` and connect to its stdin/stdout streams (no authentication required)

## Security & Authentication

### Bearer Token Authentication

The FastMCP server with HTTP transport requires bearer token authentication for security:

#### Setup
```bash
# Generate a secure 256-bit token
BEARER_TOKEN=$(openssl rand -hex 32)
echo "BEARER_TOKEN=$BEARER_TOKEN" > .env

# Start server
python run.py
```

#### Client Usage
```bash
# All HTTP requests must include Authorization header
curl -H "Authorization: Bearer $BEARER_TOKEN" \
     -H "Content-Type: application/json" \
     -H "Accept: application/json, text/event-stream" \
     -X POST http://127.0.0.1:8000/mcp/ \
     -d '{"jsonrpc": "2.0", "method": "get_budget_summary", "id": 1}'
```

#### Security Features
- **Required for HTTP Transport**: All HTTP requests must include valid bearer token
- **Configurable Token**: Set via `BEARER_TOKEN` environment variable  
- **Secure Validation**: Middleware validates token format and content
- **HTTP-Only**: stdio transport bypasses authentication (direct process communication)
- **Error Handling**: Returns 401 Unauthorized for missing/invalid tokens

#### Token Management
- **Generation**: Use `openssl rand -hex 32` for cryptographically secure tokens
- **Storage**: Store in environment variables or `.env` file (never in code)
- **Rotation**: Generate new tokens periodically for enhanced security
- **Environment Isolation**: Use different tokens for development, testing, and production

## Available MCP Tools

The server provides the following tools for AI agents:

### Envelope Management
- **`create_envelope`** - Create a new budget envelope
  - Parameters: `category` (string), `budgeted_amount` (number), `starting_balance` (number, optional), `description` (string, optional)
- **`list_envelopes`** - List all budget envelopes with current balances
- **`get_envelope`** - Get details of a specific envelope by ID
  - Parameters: `envelope_id` (number)
- **`update_envelope`** - Update envelope details
  - Parameters: `envelope_id` (number), `category` (string, optional), `budgeted_amount` (number, optional), `description` (string, optional)
- **`delete_envelope`** - Delete an envelope
  - Parameters: `envelope_id` (number)

### Transaction Management
- **`create_transaction`** - Create a new income or expense transaction
  - Parameters: `envelope_id` (number), `amount` (number), `description` (string), `type` (string: "income" or "expense")
- **`list_transactions`** - List all transactions, optionally filtered by envelope
  - Parameters: `envelope_id` (number, optional)
- **`get_transaction`** - Get details of a specific transaction by ID
  - Parameters: `transaction_id` (number)
- **`update_transaction`** - Update transaction details
  - Parameters: `transaction_id` (number), `amount` (number, optional), `description` (string, optional), `type` (string, optional)
- **`delete_transaction`** - Delete a transaction
  - Parameters: `transaction_id` (number)

### Utility Tools
- **`get_envelope_balance`** - Get current balance for a specific envelope
  - Parameters: `envelope_id` (number)
- **`get_budget_summary`** - Get comprehensive budget overview with all envelopes and balances

### Cloud Integration Tools
- **`get_cloud_status`** - Get MotherDuck connection and synchronization status
  - Returns: Database mode, connection status, sync information
- **`sync_to_cloud`** - Synchronize local data to MotherDuck cloud database
  - Uploads all envelopes and transactions to cloud
- **`sync_from_cloud`** - Synchronize cloud data to local database
  - Downloads all envelopes and transactions from cloud
  - Handles conflicts using INSERT OR REPLACE strategy

## Usage Examples

Once integrated with an AI assistant, you can interact with your budget using natural language:

### Creating Envelopes
> "Create a grocery budget envelope with $500 allocated for this month"

The AI will use the `create_envelope` tool to create the envelope.

### Adding Transactions  
> "I spent $75.50 at the grocery store today"

The AI will use the `create_transaction` tool to record the expense against the appropriate envelope.

### Checking Balances
> "How much money do I have left in my grocery budget?"

The AI will use the `get_envelope_balance` tool to check your current balance.

### Budget Overview
> "Show me a summary of all my budget categories and balances"

The AI will use the `get_budget_summary` tool to provide a comprehensive overview.

### Cloud Integration Examples

> "Sync my budget data to the cloud"

The AI will use the `sync_to_cloud` tool to upload all local envelopes and transactions to MotherDuck.

> "Download my budget from the cloud to this device"

The AI will use the `sync_from_cloud` tool to download cloud data to the local database.

> "What's my cloud connection status?"

The AI will use the `get_cloud_status` tool to show MotherDuck connectivity, database mode, and sync information.

## Database Schema

### Envelopes Table
- `id` (INTEGER PRIMARY KEY)
- `category` (TEXT UNIQUE) - Envelope name/category
- `budgeted_amount` (REAL) - Allocated budget amount
- `starting_balance` (REAL) - Initial balance
- `description` (TEXT) - Optional description

### Transactions Table
- `id` (INTEGER PRIMARY KEY)
- `envelope_id` (INTEGER) - Foreign key to envelopes table
- `amount` (REAL) - Transaction amount (positive for income, negative for expenses)
- `description` (TEXT) - Transaction description
- `date` (TEXT) - Transaction date (ISO format)
- `type` (TEXT) - Transaction type ('income' or 'expense')

## Development

### Project Structure

```
budget-mcp-server/
├── app/
│   ├── __init__.py              # Legacy MCP server factory
│   ├── fastmcp_server.py        # FastMCP server with HTTP transport
│   ├── config.py                # Configuration management (includes HTTPS & auth settings)
│   ├── auth.py                  # Bearer token authentication middleware ✅ NEW
│   ├── cli.py                   # CLI entry point for uvx installation
│   ├── mcp/                     # Legacy MCP tool implementations
│   │   ├── __init__.py          # MCP module initialization
│   │   ├── registry.py          # Centralized tool registration system
│   │   ├── envelope_tools.py    # Envelope management tools (legacy)
│   │   ├── transaction_tools.py # Transaction management tools (legacy)
│   │   └── utility_tools.py     # Utility and summary tools (legacy)
│   ├── models/                  # Data models
│   │   ├── __init__.py          # Models module initialization
│   │   └── database.py          # Database operations
│   ├── services/                # Business logic (shared)
│   │   ├── __init__.py          # Services module initialization
│   │   ├── envelope_service.py  # Envelope business logic
│   │   └── transaction_service.py # Transaction business logic
│   └── utils/                   # Utilities
│       └── __init__.py          # Utilities module initialization
├── scripts/                     # Utility scripts
│   └── generate_cert.py         # SSL certificate generation for HTTPS
├── tests/                       # Test suite
│   ├── __init__.py              # Test module initialization
│   ├── conftest.py              # Pytest configuration and fixtures
│   ├── test_fastmcp_tools.py    # FastMCP transport tests
│   ├── test_mcp_tools.py        # stdio transport tests
│   ├── test_auth.py             # Bearer token middleware tests ✅ NEW
│   ├── test_fastmcp_auth.py     # FastMCP server authentication tests ✅ NEW
│   ├── test_config_auth.py      # Configuration & startup validation tests ✅ NEW
│   ├── test_models/             # Model tests
│   │   ├── __init__.py          # Test models module initialization
│   │   └── test_database.py     # Database model tests
│   └── test_services/           # Service tests
│       ├── __init__.py          # Test services module initialization
│       ├── test_envelope_service.py  # Envelope service tests
│       └── test_transaction_service.py # Transaction service tests
├── certs/                       # SSL certificates directory
├── data/                        # Database files directory
├── setup-env.sh                 # Interactive environment setup script ✅ NEW
├── run.py                       # FastMCP server entry point (HTTP/HTTPS with auth)
├── run_stdio.py                 # MCP server entry point (stdio, no auth)
├── ApplicationStructure.md      # Detailed application architecture documentation
├── CLAUDE.md                    # Claude Code instructions and project guidance
├── HTTPS_SETUP.md              # Detailed HTTPS configuration guide
├── pyproject.toml              # Project configuration (uv)
├── uv.lock                     # Dependency lockfile (uv)
├── Dockerfile                  # Container definition (includes OpenSSL)
└── docker-compose.yml         # Container orchestration (includes HTTPS volumes)
```

### Running Tests

**All tests:**
```bash
uv run pytest
```

**FastMCP tests (HTTP transport):**
```bash
uv run pytest tests/test_fastmcp_tools.py
```

**stdio transport tests:**
```bash
uv run pytest tests/test_mcp_tools.py
```

**Authentication tests:**
```bash
# Bearer token middleware tests
uv run pytest tests/test_auth.py

# FastMCP server authentication integration tests  
uv run pytest tests/test_fastmcp_auth.py

# Configuration and startup validation tests
uv run pytest tests/test_config_auth.py
```


### Environment Variables

**Server Configuration:**
- `HOST`: Server host for HTTP transport (default: 127.0.0.1) - the address the server will bind to.
- `PORT`: Server port for HTTP transport (default: 8000) - the TCP port for HTTP transport.
- `MCP_PATH`: MCP endpoint path (default: /mcp) - the HTTP path where the MCP endpoint is exposed.

**Authentication Configuration:**
- `BEARER_TOKEN`: **REQUIRED** for HTTP transport - Bearer token for API authentication security (generate with `openssl rand -hex 32`)

**Application Configuration:**
- `APP_ENV`: Set to 'production', 'development', or 'testing' (default: development) - the application environment, affecting logging and database persistence.
- `DATABASE_FILE`: Database file path (default: `./data/budget_app.duckdb`) - the location of the DuckDB file used for persistent storage.

**HTTPS Configuration:**
- `HTTPS_ENABLED`: Enable HTTPS mode (default: false) - set to 'true' to enable SSL/TLS encryption.
- `SSL_CERT_FILE`: Path to SSL certificate file (default: certs/server.crt) - PEM format certificate file.
- `SSL_KEY_FILE`: Path to SSL private key file (default: certs/server.key) - PEM format private key file.

**MotherDuck Cloud Configuration:**
- `MOTHERDUCK_TOKEN`: MotherDuck access token (required for cloud/hybrid modes) - generate from MotherDuck console.
- `MOTHERDUCK_DATABASE`: Cloud database name (default: budget_app) - the name of your MotherDuck database.
- `DATABASE_MODE`: Database connection mode (default: local) - options: "local", "cloud", "hybrid".
- `MOTHERDUCK_SYNC_ON_START`: Auto-sync on startup (default: false) - set to 'true' to sync local data to cloud on server start.

### Configuration

The application uses different configurations for different environments:

- **Development**: Database resets on each restart, debug mode enabled
- **Production**: Database persistence, optimized for deployment
- **Testing**: In-memory database, isolated test environment

## Cash Envelope Budgeting System

This server implements the traditional cash envelope budgeting method digitally:

### How It Works
1. **Create Envelopes**: Set up budget categories (e.g., "Groceries", "Gas", "Entertainment")
2. **Allocate Money**: Assign a budgeted amount to each envelope
3. **Track Spending**: Record transactions against the appropriate envelope
4. **Monitor Balances**: Keep track of remaining funds in each envelope

### Benefits
- **Intentional Spending**: Every dollar has a purpose
- **Overspending Prevention**: Can't spend more than what's in the envelope
- **Clear Visibility**: See exactly where your money is going
- **Flexible Categories**: Create envelopes that match your lifestyle

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes following SOLID principles and TDD practices
4. Ensure all tests pass (`uv run pytest`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Development Guidelines

- Follow SOLID principles
- Use Test-Driven Development (TDD)
- Keep functions/methods focused and under 50 lines
- Write comprehensive tests for new features
- Update documentation as needed
- Use uv for dependency management

## License

[Add your license here]

## Support

For questions about MCP integration or budget management features, please open an issue on GitHub.
