import pytest
from app import create_app

@pytest.fixture(scope='session')
def app():
    """Session-wide test `Flask` application."""
    # Create a new app instance for testing using the 'testing' configuration
    app = create_app('testing')

    # The create_app factory already initializes services.
    # If mocking is needed for specific tests, it should be done
    # by patching the service instances within the test functions
    # or fixtures that use the app context.

    yield app

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()
