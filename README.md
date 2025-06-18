# Budget MCP Server

A Model Context Protocol (MCP) Server that enables AI agents to manage household or business budgets using the cash envelope system. This server provides tools for AI agents to create budget envelopes, track transactions, and monitor financial allocations through the MCP protocol.

## What is MCP?

The [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) is an open standard that enables AI assistants to securely connect to external data sources and tools. This budget server implements MCP to allow AI agents like Claude to directly interact with your budget data.

## Features

- **AI Agent Integration**: Designed for seamless integration with AI assistants via MCP
- **Cash Envelope Budgeting**: Create and manage budget categories with allocated amounts
- **Transaction Management**: Track income and expense transactions against budget envelopes
- **Real-time Balance Tracking**: Monitor current balances and budget summaries
- **Lightweight Database**: Uses DuckDB for fast, embedded database operations
- **Modern Python Tooling**: Built with uv for fast, reliable dependency management
- **Docker Support**: Containerized deployment for development and production

## Tech Stack

- **Runtime**: Python 3.12+
- **Protocol**: Model Context Protocol (MCP)
- **Database**: DuckDB
- **Package Management**: uv
- **Testing**: pytest
- **Containerization**: Docker, Docker Compose
- **Architecture**: SOLID principles, Test-Driven Development (TDD)

## Installation

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

3. Run the MCP server:
```bash
uv run python run.py
```

### Using pip (Alternative)

1. Clone the repository:
```bash
git clone <repository-url>
cd budget-mcp-server
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the MCP server:
```bash
python run.py
```

### Docker Setup

#### Development Mode
```bash
docker-compose --profile dev up
```

#### Production Mode
```bash
docker-compose up -d
```

## Integration with AI Assistants

This MCP server is designed to be integrated with AI assistants. Here's how to configure it:

### Claude Desktop Integration

Add the following to your Claude Desktop configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "budget-envelope": {
      "command": "uv",
      "args": ["run", "python", "/path/to/budget-mcp-server/run.py"],
      "cwd": "/path/to/budget-mcp-server"
    }
  }
}
```

### Other MCP Clients

The server communicates via stdio and can be integrated with any MCP-compatible client. Run the server and connect to its stdin/stdout streams.

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
│   ├── __init__.py          # MCP server factory
│   ├── config.py            # Configuration management
│   ├── mcp/                 # MCP tool implementations
│   │   ├── envelope_tools.py     # Envelope management tools
│   │   ├── transaction_tools.py  # Transaction management tools
│   │   └── utility_tools.py      # Utility and summary tools
│   ├── models/              # Data models
│   │   └── database.py      # Database operations
│   ├── services/            # Business logic
│   │   ├── envelope_service.py
│   │   └── transaction_service.py
│   └── utils/               # Utilities
├── tests/                   # Test suite
├── run.py                   # MCP server entry point
├── pyproject.toml          # Project configuration (uv)
├── requirements.txt        # Dependencies (pip fallback)
├── uv.lock                 # Dependency lockfile (uv)
├── Dockerfile              # Container definition
└── docker-compose.yml     # Container orchestration
```

### Running Tests

With uv:
```bash
uv run pytest
```

With pip:
```bash
pytest
```

### Environment Variables

- `APP_ENV`: Set to 'production', 'development', or 'testing' (default: development)
- `DATABASE_FILE`: Database file path (default: `./data/budget_app.duckdb`)

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