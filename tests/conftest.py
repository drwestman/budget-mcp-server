import pytest
from fastapi.testclient import TestClient
from app.fastmcp_server import create_fastmcp_server

@pytest.fixture(scope='session')
def app():
    """Session-wide test `FastAPI` application."""
    # Create a new app instance for testing using the 'testing' configuration
    # Disable authentication for testing purposes
    mcp = create_fastmcp_server(config_name='testing', enable_auth=False)
    return mcp.http_app()

@pytest.fixture
def client(app):
    """A test client for the app."""
    return TestClient(app)
