# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a Budget Cash Envelope REST API built with Python Flask and DuckDB. It implements a cash envelope budgeting system where users can create budget envelopes (categories) and track income/expense transactions against them.

## Development Commands

### Running the Application

#### Local Development
```bash
python3 run.py
```
The application runs on port 5000 in debug mode. The database file `budget_app.duckdb` is automatically created and reset on each run during development.

#### Docker Development
```bash
# Production mode
docker-compose up -d

# Development mode with code mounting
docker-compose --profile dev up

# Manual Docker build and run
docker build -t budget-rest-api .
docker run -p 5000:5000 -v budget_data:/app/data budget-rest-api
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
- Flask (>=2.3.0)
- DuckDB (>=0.8.0)
- pytest (>=7.0.0) - for testing
- pytest-flask (>=1.2.0) - for testing

## Architecture

### Modular Flask Architecture
The application follows Flask best practices with clear separation of concerns:

- **app/models/database.py**: `Database` class handles all DuckDB interactions, table creation, and CRUD operations
- **app/services/**: Business logic classes (`EnvelopeService`, `TransactionService`) with validation
- **app/api/**: Flask Blueprint definitions for envelope and transaction endpoints
- **app/utils/**: Authentication decorators and error handlers
- **app/config.py**: Configuration management for different environments
- **app/__init__.py**: Application factory pattern
- **run.py**: Application entry point
- **tests/**: Test directories organized by component

### Database Schema
- **envelopes**: id, category (unique), budgeted_amount, starting_balance, description
- **transactions**: id, envelope_id (FK), amount, description, date, type ('income'/'expense')

**DuckDB Compatibility Notes**:
- Uses `INTEGER PRIMARY KEY` instead of `AUTOINCREMENT` (DuckDB auto-increments primary keys by default)
- Foreign key constraints cannot use CASCADE options in DuckDB
- Tables are recreated on each application restart during development

### API Authentication
All endpoints except `/health` require an `X-API-Key` header with the value defined in `API_KEY` constant (line 9).

### Key Design Patterns
- Dependency Injection: Services receive Database instance in constructor
- Single Responsibility: Each class has one clear purpose
- Blueprint organization: Separate blueprints for envelopes and transactions
- Global error handling: Custom error handlers for common HTTP errors

## API Endpoints

### Envelopes
- `POST /envelopes/` - Create envelope
- `GET /envelopes/` - List all envelopes (with current balance)
- `GET /envelopes/<id>` - Get envelope by ID
- `PUT /envelopes/<id>` - Update envelope
- `DELETE /envelopes/<id>` - Delete envelope

### Transactions  
- `POST /transactions/` - Create transaction
- `GET /transactions/` - List all transactions (or filter by `?envelope_id=<id>`)
- `GET /transactions/<id>` - Get transaction by ID
- `PUT /transactions/<id>` - Update transaction
- `DELETE /transactions/<id>` - Delete transaction

### Health Check
- `GET /health` - Health check (no authentication required)

## Key Configuration
- `API_KEY`: Authentication key (line 9) - change for production
- `DATABASE_FILE`: DuckDB database file path (line 10)
- Database is reset on each application start during development (lines 697-699)

## Docker Configuration

### Container Files
- **Dockerfile**: Multi-stage Python 3.11-slim build with health checks
- **.dockerignore**: Excludes development files, cache, and virtual environments
- **docker-compose.yml**: Production and development service configurations

### Environment Variables
- `FLASK_ENV`: Set to 'production' or 'development' (default: development)
- `HOST`: Container host binding (default: 0.0.0.0 for containers)
- `PORT`: Application port (default: 5000)
- `API_KEY`: Authentication key for API access
- `DATABASE_FILE`: Database file path (default: /app/data/budget_app.duckdb in containers)

### Data Persistence
- Database files are stored in Docker volume `budget_data` mounted at `/app/data`
- Volume ensures data persistence between container restarts
- Production mode (`FLASK_ENV=production`) disables database reset on startup