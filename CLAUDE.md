# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a Budget Cash Envelope MCP Server built with Python and DuckDB. It implements a cash envelope budgeting system where AI assistants can create budget envelopes (categories) and track income/expense transactions against them through MCP (Model Context Protocol) tools.

## MCP Server Conversion Plan

### Conversion Strategy
This project is being converted from a Flask REST API to an MCP server while preserving:
- Existing business logic in services layer
- Database architecture and models
- SOLID principles and TDD approach
- Validation and error handling

### MCP Tools to Implement
**Envelope Management:**
- `create_envelope` - Create a new budget envelope
- `list_envelopes` - Get all envelopes with current balances
- `get_envelope` - Get specific envelope details by ID
- `update_envelope` - Modify envelope properties
- `delete_envelope` - Remove an envelope

**Transaction Management:**
- `create_transaction` - Add income/expense transaction
- `list_transactions` - Get transactions (optionally filtered by envelope)
- `get_transaction` - Get specific transaction by ID
- `update_transaction` - Modify transaction details
- `delete_transaction` - Remove a transaction

**Utility Tools:**
- `get_envelope_balance` - Get current balance for specific envelope
- `get_budget_summary` - Get overall budget status

## Development Commands

### Running the MCP Server

#### Local Development
```bash
python3 run.py
```
The MCP server starts and listens for MCP protocol connections. The database file `budget_app.duckdb` is automatically created and reset on each run during development.

#### Docker Development
```bash
# Production mode
docker-compose up -d

# Development mode with code mounting
docker-compose --profile dev up

# Manual Docker build and run
docker build -t budget-mcp-server .
docker run -v budget_data:/app/data budget-mcp-server
```

### Dependencies
Install dependencies with:
```bash
pip install -r requirements.txt
```

**Note**: On systems with externally-managed Python environments (like Ubuntu/Debian), you may need to use:
```bash
pip install --break-system-packages -r requirements.txt
```

Required packages:
- mcp (>=1.0.0) - MCP server framework
- DuckDB (>=0.8.0) - Database
- pytest (>=7.0.0) - for testing

## Architecture

### Modular MCP Server Architecture
The application follows MCP best practices with clear separation of concerns:

- **app/models/database.py**: `Database` class handles all DuckDB interactions, table creation, and CRUD operations
- **app/services/**: Business logic classes (`EnvelopeService`, `TransactionService`) with validation
- **app/mcp/**: MCP tool definitions for envelope and transaction operations
- **app/utils/**: Error handlers and utility functions
- **app/config.py**: Configuration management for different environments
- **app/__init__.py**: MCP server factory pattern
- **run.py**: MCP server entry point
- **tests/**: Test directories organized by component

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
- Dependency Injection: Services receive Database instance in constructor
- Single Responsibility: Each class has one clear purpose
- Tool organization: Separate tool groups for envelopes and transactions
- Structured error handling: Consistent error responses across all tools

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
- `DATABASE_FILE`: DuckDB database file path - stores all budget data
- `APP_ENV`: Set to 'production' or 'development' (controls database reset behavior)
- Database is reset on each application start during development mode

## Docker Configuration

### Container Files
- **Dockerfile**: Multi-stage Python 3.11-slim build optimized for MCP server
- **.dockerignore**: Excludes development files, cache, and virtual environments
- **docker-compose.yml**: Production and development service configurations

### Environment Variables
- `APP_ENV`: Set to 'production' or 'development' (default: development)
- `DATABASE_FILE`: Database file path (default: /app/data/budget_app.duckdb in containers)

### Data Persistence
- Database files are stored in Docker volume `budget_data` mounted at `/app/data`
- Volume ensures data persistence between container restarts
- Production mode (`APP_ENV=production`) disables database reset on startup