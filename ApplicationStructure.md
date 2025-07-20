# Budget MCP Server Application Structure

## 1. About

Budget MCP Server is a Python-based application that allows an AI agent to manage financial transactions for a household or business budget. The system is designed around the cash envelope budgeting system, providing a clear and effective way to track spending and manage funds.

## 2. Architecture

The application is built with a focus on modern development practices, ensuring robustness, maintainability, and ease of use.

- **Package Management**: [uv](https://docs.astral.sh/uv/) is used for Python package management and virtual environments, providing a fast and reliable dependency management solution.
- **MCP Server**: The core of the application is the [python-sdk](https://github.com/modelcontextprotocol/python-sdk), which provides the foundation for the Model-Context-Protocol server.
- **Database**: [DuckDB](https://duckdb.org/) is used for data persistence, offering a high-performance, in-process analytical database that is easy to manage.
- **Testing**: [pytest](https://docs.pytest.org/) is used for unit testing, enabling a comprehensive and maintainable test suite.
- **Design Principles**: The application adheres to **SOLID** principles and **Test-Driven Development (TDD)** techniques to ensure a high-quality, scalable, and maintainable codebase.
- **Containerization**: **Docker** and **Docker Compose** are used to containerize the application, simplifying development, deployment, and scaling.
- **Code Quality**: A suite of tools ensures code quality and consistency:
  - **black**: for automated code formatting.
  - **ruff**: for linting and code analysis.
  - **mypy**: for static type checking.

## 3. Project Layout

The project is organized into the following directories and files:

- **`/.github`**: Contains GitHub-specific files, such as workflow definitions and issue templates.
- **`/app`**: The main application directory.
  - **`__init__.py`**: Initializes the `app` module.
  - **`auth.py`**: Handles authentication and authorization logic.
  - **`cli.py`**: Defines the command-line interface for the application.
  - **`config.py`**: Manages application configuration settings.
  - **`fastmcp_server.py`**: The main entry point for the MCP server.
  - **`/mcp`**: Contains the core MCP tools.
    - **`envelope_tools.py`**: Tools for managing budget envelopes.
    - **`registry.py`**: The MCP tool registry.
    - **`transaction_tools.py`**: Tools for managing financial transactions.
    - **`utility_tools.py`**: General utility functions.
  - **`/models`**: Contains the data models for the application.
    - **`database.py`**: Defines the database schema and provides an interface for interacting with the database.
  - **`/services`**: Contains the business logic for the application.
    - **`envelope_service.py`**: Business logic for managing envelopes.
    - **`transaction_service.py`**: Business logic for managing transactions.
- **`/certs`**: Contains SSL certificates for HTTPS.
- **`/data`**: Stores the application's data, including the DuckDB database file.
- **`/dist`**: Contains the distributable packages for the application.
- **`/scripts`**: Contains various scripts for managing the application.
  - **`generate_cert.py`**: A script for generating self-signed SSL certificates.
- **`/tests`**: Contains the test suite for the application.
  - **`conftest.py`**: Provides fixtures and configuration for the test suite.
  - **`test_*.py`**: Individual test files for different parts of the application.
- **`docker-compose.yml`**: Defines the services, networks, and volumes for the Docker application.
- **`Dockerfile`**: Defines the Docker image for the application.
- **`pyproject.toml`**: The main configuration file for the project, including dependencies and tool settings.
- **`run.py`**: A script for running the application.
- **`setup-env.sh`**: A script for setting up the development environment.
- **`uv.lock`**: The lock file for the project's dependencies.