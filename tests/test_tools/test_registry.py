#!/usr/bin/env python3
"""
Tests for the ToolRegistry class and related adapters.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import mcp.types as types
import pytest

from app.services.envelope_service import EnvelopeService
from app.services.transaction_service import TransactionService
from app.tools.registry import (
    MCPToolAdapter,
    ToolRegistry,
    create_mcp_adapter,
    create_tool_registry,
)


@pytest.fixture
def mock_envelope_service():
    """Mock envelope service."""
    return MagicMock(spec=EnvelopeService)


@pytest.fixture
def mock_transaction_service():
    """Mock transaction service."""
    return MagicMock(spec=TransactionService)


@pytest.fixture
def registry(mock_envelope_service, mock_transaction_service):
    """Create a ToolRegistry instance for testing."""
    return ToolRegistry(mock_envelope_service, mock_transaction_service)


class TestToolRegistry:
    """Test the ToolRegistry class."""

    def test_initialization(self, mock_envelope_service, mock_transaction_service):
        """Test ToolRegistry initialization."""
        registry = ToolRegistry(mock_envelope_service, mock_transaction_service)

        assert registry.envelope_service == mock_envelope_service
        assert registry.transaction_service == mock_transaction_service
        assert isinstance(registry._tools, dict)
        assert isinstance(registry._handlers, dict)

        # Check that tools are registered
        assert len(registry._tools) > 0
        assert len(registry._handlers) > 0

    def test_get_tool_list(self, registry):
        """Test getting list of tool names."""
        tool_list = registry.get_tool_list()

        assert isinstance(tool_list, list)
        assert len(tool_list) > 0

        # Check for expected tool categories
        envelope_tools = [
            "create_envelope",
            "list_envelopes",
            "get_envelope",
            "update_envelope",
            "delete_envelope",
        ]
        transaction_tools = [
            "create_transaction",
            "list_transactions",
            "get_transaction",
            "update_transaction",
            "delete_transaction",
        ]
        utility_tools = [
            "get_envelope_balance",
            "get_budget_summary",
            "get_cloud_status",
            "sync_to_cloud",
            "sync_from_cloud",
        ]

        for tool in envelope_tools + transaction_tools + utility_tools:
            assert tool in tool_list

    def test_get_tool_schema_valid(self, registry):
        """Test getting schema for a valid tool."""
        schema = registry.get_tool_schema("create_envelope")

        assert isinstance(schema, dict)
        assert "name" in schema
        assert "description" in schema
        assert "inputSchema" in schema

    def test_get_tool_schema_invalid(self, registry):
        """Test getting schema for an invalid tool."""
        with pytest.raises(ValueError, match="Unknown tool: invalid_tool"):
            registry.get_tool_schema("invalid_tool")

    def test_get_all_tool_schemas(self, registry):
        """Test getting all tool schemas."""
        all_schemas = registry.get_all_tool_schemas()

        assert isinstance(all_schemas, dict)
        assert len(all_schemas) > 0

        # Verify each schema has required fields
        for tool_name, schema in all_schemas.items():
            assert isinstance(tool_name, str)
            assert isinstance(schema, dict)
            assert "name" in schema
            assert "description" in schema
            assert "inputSchema" in schema

    @pytest.mark.asyncio
    async def test_call_tool_envelope_tool(self, registry):
        """Test calling an envelope tool."""
        # Mock the handler
        mock_handler = AsyncMock(return_value={"success": True})
        registry._handlers["create_envelope"] = (
            mock_handler,
            registry.envelope_service,
        )

        arguments = {"category": "Test Envelope", "budgeted_amount": 100.0}
        result = await registry.call_tool("create_envelope", arguments)

        mock_handler.assert_called_once_with(registry.envelope_service, arguments)
        assert result == {"success": True}

    @pytest.mark.asyncio
    async def test_call_tool_transaction_tool(self, registry):
        """Test calling a transaction tool."""
        # Mock the handler
        mock_handler = AsyncMock(return_value={"transaction_id": "123"})
        registry._handlers["create_transaction"] = (
            mock_handler,
            registry.transaction_service,
        )

        arguments = {"amount": 50.0, "description": "Test transaction"}
        result = await registry.call_tool("create_transaction", arguments)

        mock_handler.assert_called_once_with(registry.transaction_service, arguments)
        assert result == {"transaction_id": "123"}

    @pytest.mark.asyncio
    async def test_call_tool_utility_tool(self, registry):
        """Test calling a utility tool."""
        # Define expected result to avoid duplication
        expected_result = {
            "envelope_id": 123,
            "category": "Test Category",
            "current_balance": 75.0,
            "starting_balance": 100.0,
            "budgeted_amount": 200.0,
        }

        # Mock the handler
        mock_handler = AsyncMock(return_value=expected_result)
        registry._handlers["get_envelope_balance"] = (
            mock_handler,
            registry.envelope_service,
        )

        arguments = {"envelope_id": "env123"}
        result = await registry.call_tool("get_envelope_balance", arguments)

        mock_handler.assert_called_once_with(registry.envelope_service, arguments)
        assert result == expected_result

    @pytest.mark.asyncio
    async def test_call_tool_unknown_tool(self, registry):
        """Test calling an unknown tool."""
        with pytest.raises(ValueError, match="Unknown tool: nonexistent_tool"):
            await registry.call_tool("nonexistent_tool", {})

    @patch("app.tools.registry.get_all_tool_schemas")
    def test_register_all_tools_called(
        self, mock_get_schemas, mock_envelope_service, mock_transaction_service
    ):
        """Test that tool registration calls get_all_tool_schemas."""
        # Create a comprehensive mock schema with all expected tools
        expected_tools = [
            # Envelope tools
            "create_envelope",
            "list_envelopes",
            "get_envelope",
            "update_envelope",
            "delete_envelope",
            # Transaction tools
            "create_transaction",
            "list_transactions",
            "get_transaction",
            "update_transaction",
            "delete_transaction",
            # Utility tools
            "get_envelope_balance",
            "get_budget_summary",
            "get_cloud_status",
            "sync_to_cloud",
            "sync_from_cloud",
        ]

        mock_schemas = {}
        for tool_name in expected_tools:
            mock_schemas[tool_name] = {
                "name": tool_name,
                "description": f"Test description for {tool_name}",
                "inputSchema": {"type": "object"},
            }

        mock_get_schemas.return_value = mock_schemas

        registry = ToolRegistry(mock_envelope_service, mock_transaction_service)

        mock_get_schemas.assert_called_once()
        assert len(registry._tools) == len(mock_schemas)
        assert len(registry._handlers) == len(mock_schemas)


class TestMCPToolAdapter:
    """Test the MCPToolAdapter class."""

    def test_initialization(self, registry):
        """Test MCPToolAdapter initialization."""
        adapter = MCPToolAdapter(registry)
        assert adapter.registry == registry

    def test_get_mcp_tools(self, registry):
        """Test getting tools in MCP SDK format."""
        adapter = MCPToolAdapter(registry)
        mcp_tools = adapter.get_mcp_tools()

        assert isinstance(mcp_tools, list)
        assert len(mcp_tools) > 0

        # Check that all returned items are MCP Tool objects
        for tool in mcp_tools:
            assert isinstance(tool, types.Tool)
            assert hasattr(tool, "name")
            assert hasattr(tool, "description")
            assert hasattr(tool, "inputSchema")

    @pytest.mark.asyncio
    async def test_handle_tool_call_dict_result(self, registry):
        """Test handling tool call with dict result."""
        adapter = MCPToolAdapter(registry)

        # Mock the registry call_tool method
        mock_result = {"success": True, "id": "123"}
        registry.call_tool = AsyncMock(return_value=mock_result)

        result = await adapter.handle_tool_call("create_envelope", {"name": "Test"})

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], types.TextContent)
        assert result[0].type == "text"
        assert json.loads(result[0].text) == mock_result

    @pytest.mark.asyncio
    async def test_handle_tool_call_string_result(self, registry):
        """Test handling tool call with string result."""
        adapter = MCPToolAdapter(registry)

        # Mock the registry call_tool method
        mock_result = "Operation completed successfully"
        registry.call_tool = AsyncMock(return_value=mock_result)

        result = await adapter.handle_tool_call("create_envelope", {"name": "Test"})

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], types.TextContent)
        assert result[0].type == "text"
        assert result[0].text == mock_result


class TestFactoryFunctions:
    """Test the factory functions."""

    def test_create_tool_registry(
        self, mock_envelope_service, mock_transaction_service
    ):
        """Test create_tool_registry factory function."""
        registry = create_tool_registry(mock_envelope_service, mock_transaction_service)

        assert isinstance(registry, ToolRegistry)
        assert registry.envelope_service == mock_envelope_service
        assert registry.transaction_service == mock_transaction_service

    def test_create_mcp_adapter(self, registry):
        """Test create_mcp_adapter factory function."""
        adapter = create_mcp_adapter(registry)

        assert isinstance(adapter, MCPToolAdapter)
        assert adapter.registry == registry
