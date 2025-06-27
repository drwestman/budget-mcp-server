# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a Budget Cash Envelope MCP Server built with Python and DuckDB. It implements a cash envelope budgeting system where AI assistants can create budget envelopes (categories) and track income/expense transactions against them through MCP (Model Context Protocol) tools.

## MCP Server Implementation

### Conversion Status
✅ **COMPLETED**: This project has been successfully converted from a Flask REST API to an MCP server while preserving:
- Existing business logic in services layer
- Database architecture and models
- SOLID principles and TDD approach
- Validation and error handling

### Implemented MCP Tools
**Envelope Management:** ✅ All Complete
- `create_envelope` - Create a new budget envelope
- `list_envelopes` - Get all envelopes with current balances
- `get_envelope` - Get specific envelope details by ID
- `update_envelope` - Modify envelope properties
- `delete_envelope` - Remove an envelope

**Transaction Management:** ✅ All Complete
- `create_transaction` - Add income/expense transaction
- `list_transactions` - Get transactions (optionally filtered by envelope)
- `get_transaction` - Get specific transaction by ID
- `update_transaction` - Modify transaction details
- `delete_transaction` - Remove a transaction

**Utility Tools:** ✅ All Complete
- `get_envelope_balance` - Get current balance for specific envelope
- `get_budget_summary` - Get overall budget status

## Development Commands

### Running the MCP Server

#### FastMCP with Streamable HTTP Transport (Default)
```bash
python3 run.py
```
The FastMCP server starts with Streamable HTTP transport on `http://127.0.0.1:8000/mcp` by default. The database file `budget_app.duckdb` is automatically created and reset on each run during development.

#### FastMCP with HTTPS Support ✅ **NEW**
```bash
# Generate self-signed certificates for development
python3 scripts/generate_cert.py

# Run with HTTPS enabled
HTTPS_ENABLED=true python3 run.py
```
The server will be accessible at `https://127.0.0.1:8000/mcp` with SSL/TLS encryption. Self-signed certificates will show browser security warnings in development.

**Environment Variables:**
- `HOST`: Server host (default: 127.0.0.1) - the address the server will bind to.
- `PORT`: Server port (default: 8000) - the TCP port for HTTP transport.
- `MCP_PATH`: MCP endpoint path (default: /mcp) - the HTTP path where the MCP endpoint is exposed.
- `APP_ENV`: Environment mode (development/production/testing) - the application environment (development, production, or testing), affecting logging and database persistence.
- `HTTPS_ENABLED`: Enable HTTPS mode (default: false) - set to 'true' to enable SSL/TLS encryption.
- `SSL_CERT_FILE`: Path to SSL certificate file (default: certs/server.crt) - PEM format certificate file.
- `SSL_KEY_FILE`: Path to SSL private key file (default: certs/server.key) - PEM format private key file.

#### Legacy stdio Transport
```bash
python3 run_stdio.py
```
Runs the server with traditional stdio transport for backward compatibility with older MCP clients.

#### Docker Development
```bash
# Development mode (default)
docker compose up -d --build

# Production mode
docker compose --profile prod up -d

# Manual Docker build and run
docker build -t budget-mcp-server .
docker run -v budget_data:/app/data budget-mcp-server
```

#### Docker with HTTPS ✅ **NEW**
```bash
# Generate certificates for Docker
python3 scripts/generate_cert.py

# Run development with HTTPS
HTTPS_ENABLED=true PORT=8443 docker compose up -d --build

# Access at: https://localhost:8443/mcp
```

### Dependencies
Install dependencies with uv (recommended):
```bash
uv sync
```

**Alternative with pip:**
```bash
pip install -r requirements.txt
```

**Note**: On systems with externally-managed Python environments (like Ubuntu/Debian), you may need to use:
```bash
pip install --break-system-packages -r requirements.txt
```

Required packages:
- mcp (=>1.0.0) - MCP Server for STDIO transport
- fastmcp (>=2.9.0) - FastMCP framework with Streamable HTTP transport
- uvicorn - ASGI server with SSL support for HTTPS functionality
- DuckDB (>=0.8.0) - Database
- pytest (>=7.0.0) - for testing
- pytest-asyncio (>=0.18.0) - for async testing

**Additional system dependencies for HTTPS:**
- OpenSSL - Required for SSL certificate generation and validation

### Testing
Run tests with:
```bash
pytest
```

**With uv:**
```bash
uv run pytest
```

**Run specific test categories:**
```bash
# Test database models
pytest tests/test_models/

# Test services
pytest tests/test_services/

# Test FastMCP tools
pytest tests/test_fastmcp_tools.py

# Test legacy MCP tools (stdio transport)
pytest tests/test_mcp_tools.py
```

## Architecture

### Modular MCP Server Architecture
The application supports both modern FastMCP with Streamable HTTP transport and legacy stdio transport:

**FastMCP Architecture (Primary):**
- **app/fastmcp_server.py**: FastMCP server factory with @tool decorators and Streamable HTTP transport
- **run.py**: FastMCP entry point with HTTP/HTTPS server (includes custom HTTPS implementation)
- **scripts/generate_cert.py**: SSL certificate generation utility for HTTPS support
- **tests/test_fastmcp_tools.py**: FastMCP-specific test suite

**Core Business Logic (Shared):**
- **app/models/database.py**: `Database` class handles all DuckDB interactions, table creation, and CRUD operations
- **app/services/**: Business logic classes (`EnvelopeService`, `TransactionService`) with validation
- **app/config.py**: Configuration management for different environments (includes HTTPS settings)

**Legacy MCP Support (Backward Compatibility):**
- **app/mcp/**: Legacy MCP tool definitions and centralized registration system
  - **registry.py**: Centralized decorator-based tool registration system
  - **envelope_tools.py**: Envelope management MCP tools
  - **transaction_tools.py**: Transaction management MCP tools  
  - **utility_tools.py**: Balance and summary MCP tools
- **app/__init__.py**: Legacy MCP server factory pattern
- **run_stdio.py**: Legacy stdio transport entry point
- **tests/test_mcp_tools.py**: Legacy MCP test suite

**Supporting Components:**
- **app/utils/**: Error handlers and utility functions
- **tests/**: Test directories organized by component with async test support

### Database Schema
- **envelopes**: id, category (unique), budgeted_amount, starting_balance, description
- **transactions**: id, envelope_id (FK), amount, description, date, type ('income'/'expense')

**DuckDB Compatibility Notes**:
- Uses `INTEGER PRIMARY KEY` instead of `AUTOINCREMENT` (DuckDB auto-increments primary keys by default)
- Foreign key constraints cannot use CASCADE options in DuckDB
- Tables are recreated on each application restart during development

### MCP Tool Security
MCP server runs in a controlled environment with tool-level access control through the MCP protocol.

### Key Design Patterns
- **Dependency Injection**: Services receive Database instance in constructor
- **Single Responsibility**: Each class has one clear purpose
- **Centralized Tool Registration**: Decorator-based `@register` pattern for automatic tool discovery
- **Tool Organization**: Separate tool classes for envelopes, transactions, and utilities
- **Structured Error Handling**: Consistent error responses across all tools with proper exception handling
- **Type Safety**: Full type hints with `Annotated` types for MCP tool parameter documentation

## MCP Tools

### Envelope Tools
- `create_envelope` - Create new budget envelope
- `list_envelopes` - List all envelopes with current balances
- `get_envelope` - Get envelope details by ID
- `update_envelope` - Update envelope properties
- `delete_envelope` - Delete envelope by ID

### Transaction Tools  
- `create_transaction` - Create new transaction
- `list_transactions` - List transactions (optionally filtered by envelope_id)
- `get_transaction` - Get transaction details by ID
- `update_transaction` - Update transaction properties
- `delete_transaction` - Delete transaction by ID

### Utility Tools
- `get_envelope_balance` - Get current balance for specific envelope
- `get_budget_summary` - Get overall budget status and summary

## Key Configuration

### Core Configuration
- `DATABASE_FILE`: Database file path (default: ./data/budget_app.duckdb) - the location of the DuckDB file used for persistent storage.
- `APP_ENV`: Set to 'production', 'development', or 'testing' (default: development) - the application environment, affecting logging and database persistence.
- Database is reset on each application start during development mode

### HTTPS Configuration ✅ **NEW**
- `HTTPS_ENABLED`: Enable HTTPS mode (default: false) - set to 'true' to enable SSL/TLS encryption.
- `SSL_CERT_FILE`: Path to SSL certificate file (default: certs/server.crt) - PEM format certificate file.
- `SSL_KEY_FILE`: Path to SSL private key file (default: certs/server.key) - PEM format private key file.

**HTTPS Implementation Details:**
- Uses custom Uvicorn server with SSL context for HTTPS mode
- Automatic fallback to standard FastMCP HTTP server when HTTPS is disabled
- Certificate validation with helpful error messages
- Self-signed certificate generation script included

## Docker Configuration

### Container Files
- **Dockerfile**: Multi-stage Python 3.12-slim build optimized for MCP server (includes OpenSSL for HTTPS)
- **.dockerignore**: Excludes development files, cache, and virtual environments
- **docker-compose.yml**: Production and development service configurations (includes HTTPS support)

### Environment Variables
- `APP_ENV`: Set to 'production' or 'development' (default: development)
- `DATABASE_FILE`: Database file path (default: /app/data/budget_app.duckdb in containers)
- `HTTPS_ENABLED`: Enable HTTPS mode (default: false) 
- `SSL_CERT_FILE`: SSL certificate path (default: /app/certs/server.crt in containers)
- `SSL_KEY_FILE`: SSL key path (default: /app/certs/server.key in containers)

### Data Persistence
- Database files are stored in Docker volume `budget_data` mounted at `/app/data`
- SSL certificates are stored in Docker volume `budget_certs` mounted at `/app/certs`
- Volumes ensure data and certificate persistence between container restarts
- Production mode (`APP_ENV=production`) disables database reset on startup

### HTTPS Docker Setup ✅ **NEW**
```bash
# Generate certificates on host
python3 scripts/generate_cert.py

# Copy certificates to Docker volume
docker run --rm -v budget_certs:/certs -v $(pwd)/certs:/host-certs alpine cp -r /host-certs/. /certs/

# Run with HTTPS enabled
HTTPS_ENABLED=true PORT=8443 docker compose up -d
```
