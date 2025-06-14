# Budget REST API

A Flask-based REST API for managing household or business budgets using the cash envelope system. This API allows you to create budget envelopes (categories), track income and expense transactions, and monitor your financial allocations.

## Features

- **Cash Envelope Budgeting**: Create and manage budget categories with allocated amounts
- **Transaction Management**: Track income and expense transactions against budget envelopes
- **Real-time Balance Tracking**: Monitor current balances for each envelope
- **RESTful API**: Clean, consistent API endpoints following REST principles
- **Lightweight Database**: Uses DuckDB for fast, embedded database operations
- **Docker Support**: Containerized deployment with development and production configurations

## Tech Stack

- **Backend**: Python 3.11, Flask
- **Database**: DuckDB
- **Testing**: pytest, pytest-flask
- **Containerization**: Docker, Docker Compose
- **Architecture**: SOLID principles, Test-Driven Development (TDD)

## Installation

### Prerequisites

- Python 3.11+
- pip

### Local Development Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd budget-rest-api
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

**Note**: On systems with externally-managed Python environments (like Ubuntu/Debian), you may need to use:
```bash
pip install --break-system-packages -r requirements.txt
```

3. Run the application:
```bash
python3 run.py
```

The API will be available at `http://localhost:5000`

### Docker Setup

#### Production Mode
```bash
docker-compose up -d
```

#### Development Mode (with code mounting)
```bash
docker-compose --profile dev up
```

#### Manual Docker Build
```bash
docker build -t budget-rest-api .
docker run -p 5000:5000 -v budget_data:/app/data budget-rest-api
```

## API Documentation

### Authentication

All endpoints except `/health` require an `X-API-Key` header with a valid API key.

```bash
curl -H "X-API-Key: your-api-key-here" http://localhost:5000/envelopes
```

### Endpoints

#### Health Check
- `GET /health` - Health check (no authentication required)

#### Envelopes
- `POST /envelopes/` - Create a new envelope
- `GET /envelopes/` - List all envelopes with current balances
- `GET /envelopes/<id>` - Get specific envelope by ID
- `PUT /envelopes/<id>` - Update envelope details
- `DELETE /envelopes/<id>` - Delete envelope

#### Transactions
- `POST /transactions/` - Create a new transaction
- `GET /transactions/` - List all transactions (optional: `?envelope_id=<id>` to filter)
- `GET /transactions/<id>` - Get specific transaction by ID
- `PUT /transactions/<id>` - Update transaction details
- `DELETE /transactions/<id>` - Delete transaction

### Example Usage

#### Create an Envelope
```bash
curl -X POST http://localhost:5000/envelopes/ \
  -H "X-API-Key: your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "category": "Groceries",
    "budgeted_amount": 500.00,
    "starting_balance": 500.00,
    "description": "Monthly grocery budget"
  }'
```

#### Create a Transaction
```bash
curl -X POST http://localhost:5000/transactions/ \
  -H "X-API-Key: your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "envelope_id": 1,
    "amount": -75.50,
    "description": "Weekly grocery shopping",
    "type": "expense"
  }'
```

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
budget-rest-api/
├── app/
│   ├── __init__.py          # Application factory
│   ├── config.py            # Configuration management
│   ├── api/                 # API endpoints
│   │   ├── envelopes.py     # Envelope routes
│   │   └── transactions.py  # Transaction routes
│   ├── models/              # Data models
│   │   └── database.py      # Database operations
│   ├── services/            # Business logic
│   │   ├── envelope_service.py
│   │   └── transaction_service.py
│   └── utils/               # Utilities
│       ├── auth.py          # Authentication
│       └── error_handlers.py
├── tests/                   # Test suite
├── run.py                   # Application entry point
├── requirements.txt         # Python dependencies
├── Dockerfile              # Container definition
└── docker-compose.yml     # Container orchestration
```

### Running Tests

```bash
pytest
```

### Environment Variables

- `APP_ENV`: Set to 'production' or 'development' (default: development)
- `HOST`: Host binding (default: 127.0.0.1 for local, 0.0.0.0 for containers)
- `PORT`: Application port (default: 5000)
- `API_KEY`: Authentication key for API access
- `DATABASE_FILE`: Database file path

### Configuration

The application uses different configurations for development and production:

- **Development**: Database resets on each restart, debug mode enabled
- **Production**: Database persistence, optimized for deployment

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes following SOLID principles and TDD practices
4. Ensure all tests pass (`pytest`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Development Guidelines

- Follow SOLID principles
- Use Test-Driven Development (TDD)
- Keep functions/methods under 50 lines
- Write comprehensive tests for new features
- Update documentation as needed

## License

[Add your license here]

## Support

[Add contact information or support channels here]