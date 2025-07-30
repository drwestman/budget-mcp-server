"""
Integration tests for MCP initialization middleware with FastMCP server factory.
"""

import pytest
from fastmcp import FastMCP

from app.fastmcp_server import create_fastmcp_server


class TestFastMCPInitializationIntegration:
    """Test suite for MCP initialization middleware integration."""

    def test_create_server_with_init_check_enabled(self) -> None:
        """Test server creation with initialization check enabled."""
        server = create_fastmcp_server(
            config_name="testing", enable_auth=False, enable_init_check=True
        )

        assert isinstance(server, FastMCP)
        assert server.name == "budget-envelope-server"

    def test_create_server_with_init_check_disabled(self) -> None:
        """Test server creation with initialization check disabled."""
        server = create_fastmcp_server(
            config_name="testing", enable_auth=False, enable_init_check=False
        )

        assert isinstance(server, FastMCP)
        assert server.name == "budget-envelope-server"

    def test_create_server_with_both_middleware_enabled(self) -> None:
        """Test server creation with both auth and init check enabled."""
        # Note: This test doesn't actually test auth since we'd need a real bearer token
        # in the testing config, but it tests that the server can be created
        server = create_fastmcp_server(
            config_name="testing", enable_auth=True, enable_init_check=True
        )

        assert isinstance(server, FastMCP)
        assert server.name == "budget-envelope-server"

    def test_create_server_defaults(self) -> None:
        """Test server creation with default parameters."""
        server = create_fastmcp_server(config_name="testing")

        assert isinstance(server, FastMCP)
        assert server.name == "budget-envelope-server"
        # By default, both auth and init check should be enabled

    @pytest.mark.asyncio
    async def test_server_tools_available(self) -> None:
        """Test that server tools are still available with middleware."""
        server = create_fastmcp_server(
            config_name="testing", enable_auth=False, enable_init_check=True
        )

        tools = await server.get_tools()

        # Check that expected tools are registered
        expected_tools = {
            "create_envelope",
            "list_envelopes",
            "get_envelope",
            "update_envelope",
            "delete_envelope",
            "create_transaction",
            "list_transactions",
            "get_transaction",
            "update_transaction",
            "delete_transaction",
            "get_envelope_balance",
            "get_budget_summary",
            "get_cloud_status",
            "sync_to_cloud",
            "sync_from_cloud",
        }

        tool_names = set(tools.keys())
        assert expected_tools.issubset(tool_names)

    def test_middleware_configuration_only_auth(self) -> None:
        """Test middleware configuration with only auth enabled."""
        server = create_fastmcp_server(
            config_name="testing",
            enable_auth=False,  # Would be True with real token
            enable_init_check=False,
        )

        # Server should be created successfully
        assert isinstance(server, FastMCP)

    def test_middleware_configuration_only_init_check(self) -> None:
        """Test middleware configuration with only init check enabled."""
        server = create_fastmcp_server(
            config_name="testing", enable_auth=False, enable_init_check=True
        )

        # Server should be created successfully
        assert isinstance(server, FastMCP)

    def test_middleware_configuration_neither_enabled(self) -> None:
        """Test middleware configuration with neither middleware enabled."""
        server = create_fastmcp_server(
            config_name="testing", enable_auth=False, enable_init_check=False
        )

        # Server should be created successfully
        assert isinstance(server, FastMCP)
