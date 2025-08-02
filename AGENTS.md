# AGENTS.md - Development Guidelines

## Commands
- **Run**: `uv run python -m app.cli`
- **Test All**: `uv run pytest`
- **Test Single**: `uv run pytest tests/test_specific_file.py::test_function_name`
- **Lint**: `uv run ruff check .`
- **Format**: `uv run black .`
- **Type Check**: `uv run mypy .`

## Code Style
- **Line Length**: 88 characters (Black/Ruff)
- **Python Version**: 3.12+
- **Type Hints**: Required for all functions (`disallow_untyped_defs = true`)
- **Imports**: Standard library, third-party, local (separated by blank lines)
- **Naming**: snake_case for functions/variables, PascalCase for classes
- **Docstrings**: Required for all public methods and classes

## Architecture
- **SOLID Principles**: Mandatory - Single Responsibility, Open-Closed, Liskov Substitution, Interface Segregation, Dependency Inversion
- **TDD**: Write tests before implementation (red-green-refactor cycle)
- **Function Size**: Maximum 50 lines per function
- **Error Handling**: Use specific ValueError with descriptive messages
- **Logging**: Set up per-module loggers (`logger = logging.getLogger(__name__)`)
- **Dependencies**: Inject via constructor (Database -> Service pattern)
