import asyncio
import json
from collections.abc import Generator

import pytest
from fastmcp import FastMCP

from app.fastmcp_server import create_fastmcp_server


class TestMCPTools:
    """Test suite for MCP tools functionality using FastMCP API."""

    @pytest.fixture
    def server(self) -> FastMCP:
        """Create a test FastMCP server instance."""
        return create_fastmcp_server(
            "testing", enable_auth=False, enable_init_check=False
        )

    @pytest.fixture
    def event_loop(self) -> Generator[asyncio.AbstractEventLoop, None, None]:
        """Create an event loop for async tests."""
        loop = asyncio.new_event_loop()
        yield loop
        loop.close()

    @pytest.mark.asyncio
    async def test_create_envelope_tool(self, server: FastMCP) -> None:
        """Test the create_envelope MCP tool via FastMCP API."""
        # Get the tool function from server
        tools = await server.get_tools()
        create_envelope_tool = tools["create_envelope"]

        # Test creating an envelope
        result = await create_envelope_tool.fn(
            category="Groceries",
            budgeted_amount=500.0,
            starting_balance=100.0,
            description="Monthly grocery budget",
        )

        # Parse the JSON response
        envelope_data = json.loads(result)
        assert envelope_data["category"] == "Groceries"
        assert envelope_data["budgeted_amount"] == 500.0
        assert envelope_data["starting_balance"] == 100.0
        assert "id" in envelope_data

    @pytest.mark.asyncio
    async def test_list_envelopes_tool(self, server: FastMCP) -> None:
        """Test the list_envelopes MCP tool via FastMCP API."""
        tools = await server.get_tools()

        # Create a test envelope first
        create_envelope_tool = tools["create_envelope"]
        await create_envelope_tool.fn(
            category="Test Category",
            budgeted_amount=200.0,
            starting_balance=50.0,
            description="Test envelope",
        )

        # Test listing envelopes
        list_envelopes_tool = tools["list_envelopes"]
        result = await list_envelopes_tool.fn()

        # Parse the JSON response
        envelopes_data = json.loads(result)
        assert isinstance(envelopes_data, list)
        assert len(envelopes_data) >= 1

        test_envelope = next(
            (env for env in envelopes_data if env["category"] == "Test Category"), None
        )
        assert test_envelope is not None
        assert test_envelope["budgeted_amount"] == 200.0
        assert test_envelope["starting_balance"] == 50.0

    @pytest.mark.asyncio
    async def test_create_transaction_tool(self, server: FastMCP) -> None:
        """Test the create_transaction MCP tool via FastMCP API."""
        tools = await server.get_tools()

        # Create an envelope first
        create_envelope_tool = tools["create_envelope"]
        envelope_result = await create_envelope_tool.fn(
            category="Test Budget",
            budgeted_amount=300.0,
            starting_balance=200.0,
            description="Test budget for transactions",
        )
        envelope_data = json.loads(envelope_result)
        envelope_id = envelope_data["id"]

        # Test creating a transaction
        create_transaction_tool = tools["create_transaction"]
        result = await create_transaction_tool.fn(
            envelope_id=envelope_id,
            amount=50.0,
            description="Test grocery purchase",
            date="2024-01-15",
            type="expense",
        )

        # Parse the JSON response
        transaction_data = json.loads(result)
        assert transaction_data["envelope_id"] == envelope_id
        assert transaction_data["amount"] == 50.0
        assert transaction_data["description"] == "Test grocery purchase"
        assert transaction_data["date"] == "2024-01-15"
        assert transaction_data["type"] == "expense"
        assert "id" in transaction_data

    @pytest.mark.asyncio
    async def test_get_budget_summary_tool(self, server: FastMCP) -> None:
        """Test the get_budget_summary MCP tool via FastMCP API."""
        tools = await server.get_tools()

        # Create test data
        create_envelope_tool = tools["create_envelope"]
        envelope_result = await create_envelope_tool.fn(
            category="Summary Test",
            budgeted_amount=1000.0,
            starting_balance=800.0,
            description="Test envelope for summary",
        )
        envelope_data = json.loads(envelope_result)
        envelope_id = envelope_data["id"]

        # Create a transaction
        create_transaction_tool = tools["create_transaction"]
        await create_transaction_tool.fn(
            envelope_id=envelope_id,
            amount=150.0,
            description="Test expense",
            date="2024-01-20",
            type="expense",
        )

        # Test getting budget summary
        get_budget_summary_tool = tools["get_budget_summary"]
        result = await get_budget_summary_tool.fn()

        # Parse the JSON response
        summary_data = json.loads(result)
        assert "total_envelopes" in summary_data
        assert "total_budgeted" in summary_data
        assert "total_current_balance" in summary_data
        assert "total_spent" in summary_data
        assert "envelopes" in summary_data

    @pytest.mark.asyncio
    async def test_error_handling(self, server: FastMCP) -> None:
        """Test error handling in MCP tools via FastMCP API."""
        tools = await server.get_tools()
        create_envelope_tool = tools["create_envelope"]

        # Test with empty category (should cause error)
        result = await create_envelope_tool.fn(
            category="",  # Empty category should cause error
            budgeted_amount=100.0,
            starting_balance=50.0,
            description="Test",
        )

        # Should return an error message
        assert "Error:" in result

    @pytest.mark.asyncio
    async def test_tool_schema_generation(self, server: FastMCP) -> None:
        """Test the input schema generation for MCP tools via FastMCP API."""
        tools = await server.get_tools()

        # Test schema for create_envelope
        create_envelope_tool = tools.get("create_envelope")
        assert create_envelope_tool is not None
        schema = create_envelope_tool.parameters
        assert schema["type"] == "object"
        assert "category" in schema["properties"]
        assert schema["properties"]["category"]["type"] == "string"
        assert "budgeted_amount" in schema["properties"]
        assert schema["properties"]["budgeted_amount"]["type"] == "number"
        assert "starting_balance" in schema["properties"]
        assert "description" in schema["properties"]
        assert "category" in schema["required"]
        assert "budgeted_amount" in schema["required"]
        assert "starting_balance" not in schema.get("required", [])
        assert "description" not in schema.get("required", [])

        # Test schema for list_transactions
        list_transactions_tool = tools.get("list_transactions")
        assert list_transactions_tool is not None
        schema = list_transactions_tool.parameters
        assert schema["type"] == "object"
        assert "envelope_id" in schema["properties"]
        # FastMCP generates nullable integers with anyOf pattern for Optional types
        envelope_id_schema = schema["properties"]["envelope_id"]
        # FastMCP may use anyOf for Optional types instead of direct type field
        if "anyOf" in envelope_id_schema:
            assert any(t.get("type") == "integer" for t in envelope_id_schema["anyOf"])
        else:
            assert envelope_id_schema["type"] == "integer"
        assert "envelope_id" not in schema.get("required", [])

        # Test schema for get_envelope
        get_envelope_tool = tools.get("get_envelope")
        assert get_envelope_tool is not None
        schema = get_envelope_tool.parameters
        assert "envelope_id" in schema["properties"]
        assert schema["properties"]["envelope_id"]["type"] == "integer"
        assert "envelope_id" in schema["required"]
