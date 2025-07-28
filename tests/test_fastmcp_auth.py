"""
Unit tests for FastMCP server with bearer token authentication.
"""

import asyncio
import json
import os
from collections.abc import Generator
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.fastmcp_server import create_fastmcp_server


class TestFastMCPServerAuth:
    """Test suite for FastMCP server authentication functionality."""

    @pytest.fixture
    def event_loop(self) -> Generator[asyncio.AbstractEventLoop, None, None]:
        """Create an event loop for async tests."""
        loop = asyncio.new_event_loop()
        yield loop
        loop.close()

    def test_create_server_without_auth(self) -> None:
        """Test creating FastMCP server with authentication disabled."""
        server = create_fastmcp_server(
            "testing", enable_auth=False, enable_init_check=False
        )

        assert server is not None
        assert hasattr(server, "envelope_service")
        assert hasattr(server, "transaction_service")
        assert hasattr(server, "db")

    @patch.dict(os.environ, {"BEARER_TOKEN": "test-token-123"})
    def test_create_server_with_auth_enabled(self) -> None:
        """Test creating FastMCP server with authentication enabled."""
        server = create_fastmcp_server(
            "testing", enable_auth=True, enable_init_check=False
        )

        assert server is not None
        assert hasattr(server, "envelope_service")
        assert hasattr(server, "transaction_service")
        assert hasattr(server, "db")

        # Verify that HTTP app has middleware applied
        http_app = server.http_app()
        assert http_app is not None

        # Check that middleware is applied (we can't directly inspect middleware stack,
        # but we can test behavior)
        client = TestClient(http_app)

        # Test that requests without auth are rejected
        response = client.get("/")
        assert response.status_code == 401
        assert "Missing Authorization header" in response.json()["error"]

    @patch.dict(os.environ, {"BEARER_TOKEN": "test-token-123"})
    def test_server_http_app_with_auth_middleware(self) -> None:
        """Test that HTTP app properly applies authentication middleware."""
        server = create_fastmcp_server(
            "testing", enable_auth=True, enable_init_check=False
        )
        http_app = server.http_app()
        client = TestClient(http_app)

        # Test unauthorized request
        response = client.get("/")
        assert response.status_code == 401
        assert "Missing Authorization header" in response.json()["error"]

        # Test invalid token
        response = client.get("/", headers={"Authorization": "Bearer wrong-token"})
        assert response.status_code == 401
        assert "Invalid bearer token" in response.json()["error"]

        # Test valid token (should pass auth, may fail at FastMCP level)
        response = client.get("/", headers={"Authorization": "Bearer test-token-123"})
        # Should not be 401 (authentication passed), but may be other HTTP status
        assert response.status_code != 401

    @patch.dict(os.environ, {"BEARER_TOKEN": "test-token-123"})
    def test_server_http_app_instance_consistency(self) -> None:
        """Test that HTTP app instance is consistent across calls."""
        server = create_fastmcp_server(
            "testing", enable_auth=True, enable_init_check=False
        )

        # Get HTTP app multiple times
        http_app1 = server.http_app()
        http_app2 = server.http_app()

        # Should be the same instance (our wrapper ensures this)
        assert http_app1 is http_app2

    def test_create_server_without_bearer_token_no_auth(self) -> None:
        """Test creating server without bearer token when auth is disabled."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove BEARER_TOKEN from environment
            if "BEARER_TOKEN" in os.environ:
                del os.environ["BEARER_TOKEN"]

            server = create_fastmcp_server(
                "testing", enable_auth=False, enable_init_check=False
            )
            assert server is not None

            # HTTP app should work without authentication
            http_app = server.http_app()
            client = TestClient(http_app)

            # Should not require authentication
            response = client.get("/")
            # May fail at FastMCP level but should not be 401 (auth not required)
            assert response.status_code != 401

    def test_create_server_without_bearer_token_with_auth_enabled(self) -> None:
        """Test creating server without bearer token when auth is enabled."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove BEARER_TOKEN from environment
            if "BEARER_TOKEN" in os.environ:
                del os.environ["BEARER_TOKEN"]

            # Should work but auth won't be applied
            server = create_fastmcp_server(
                "testing", enable_auth=True, enable_init_check=False
            )
            assert server is not None

            # HTTP app should work without authentication middleware
            http_app = server.http_app()
            client = TestClient(http_app)

            # Should not require authentication since no token was configured
            response = client.get("/")
            assert response.status_code != 401


class TestFastMCPServerAuthIntegration:
    """Integration tests for FastMCP server tools with authentication."""

    @pytest.fixture
    def event_loop(self) -> Generator[asyncio.AbstractEventLoop, None, None]:
        """Create an event loop for async tests."""
        loop = asyncio.new_event_loop()
        yield loop
        loop.close()

    @patch.dict(os.environ, {"BEARER_TOKEN": "integration-test-token"})
    def test_mcp_tools_with_auth(self) -> None:
        """Test that MCP tools work correctly when authentication is enabled."""
        server = create_fastmcp_server(
            "testing", enable_auth=True, enable_init_check=False
        )
        http_app = server.http_app()
        with TestClient(http_app) as client:
            # Test MCP endpoint with authentication
            mcp_request = {"jsonrpc": "2.0", "method": "list_envelopes", "id": 1}

            # Test without authentication - should fail
            response = client.post("/mcp/", json=mcp_request)
            assert response.status_code == 401

            # Test with valid authentication
            headers = {
                "Authorization": "Bearer integration-test-token",
                "Accept": "application/json, text/event-stream",
            }
            response = client.post("/mcp/", json=mcp_request, headers=headers)

            # Should pass authentication (may fail at MCP protocol level, but not auth)
            assert response.status_code != 401

    @patch.dict(os.environ, {"BEARER_TOKEN": "test-token"})
    @pytest.mark.asyncio
    async def test_tools_execution_with_auth(self) -> None:
        """Test that individual tools execute correctly with authentication enabled."""
        server = create_fastmcp_server(
            "testing", enable_auth=True, enable_init_check=False
        )

        # Get tools from server
        tools = await server.get_tools()
        assert "list_envelopes" in tools
        assert "create_envelope" in tools

        # Test tool execution (should work regardless of HTTP auth since this is direct tool access)
        list_tool = tools["list_envelopes"]
        result = await list_tool.fn()

        # Should return valid JSON
        envelopes = json.loads(result)
        assert isinstance(envelopes, list)


class TestAuthConfigurationValidation:
    """Test configuration validation for authentication."""

    def test_config_bearer_token_present(self) -> None:
        """Test configuration when bearer token is present."""
        with patch.dict(os.environ, {"BEARER_TOKEN": "test-token-value"}):
            from app.config import Config

            config = Config()
            assert config.BEARER_TOKEN == "test-token-value"

    def test_config_bearer_token_absent(self) -> None:
        """Test configuration when bearer token is absent."""
        with patch.dict(os.environ, {}, clear=True):
            if "BEARER_TOKEN" in os.environ:
                del os.environ["BEARER_TOKEN"]

            from app.config import Config

            config = Config()
            assert config.BEARER_TOKEN is None

    def test_config_bearer_token_empty_string(self) -> None:
        """Test configuration when bearer token is empty string."""
        with patch.dict(os.environ, {"BEARER_TOKEN": ""}):
            from app.config import Config

            config = Config()
            assert config.BEARER_TOKEN == ""
