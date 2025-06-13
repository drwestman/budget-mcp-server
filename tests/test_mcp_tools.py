import pytest
import asyncio
import json
from app import create_mcp_server
from app.config import Config


class TestMCPTools:
    """Test suite for MCP tools functionality."""
    
    @pytest.fixture
    def server(self):
        """Create a test MCP server instance."""
        return create_mcp_server('testing')
    
    @pytest.fixture
    def event_loop(self):
        """Create an event loop for async tests."""
        loop = asyncio.new_event_loop()
        yield loop
        loop.close()
    
    @pytest.mark.asyncio
    async def test_create_envelope_tool(self, server):
        """Test the create_envelope MCP tool."""
        # Get the tool function from server
        tools = {tool.name: tool for tool in server._tools}
        create_envelope_tool = tools['create_envelope']
        
        # Test creating an envelope
        result = await create_envelope_tool.handler(
            category="Groceries",
            budgeted_amount=500.0,
            starting_balance=100.0,
            description="Monthly grocery budget"
        )
        
        assert len(result) == 1
        assert result[0].type == "text"
        
        # Parse the JSON response
        envelope_data = json.loads(result[0].text)
        assert envelope_data['category'] == "Groceries"
        assert envelope_data['budgeted_amount'] == 500.0
        assert envelope_data['starting_balance'] == 100.0
        assert envelope_data['current_balance'] == 100.0
        assert 'id' in envelope_data
    
    @pytest.mark.asyncio
    async def test_list_envelopes_tool(self, server):
        """Test the list_envelopes MCP tool."""
        # Get the tool function from server
        tools = {tool.name: tool for tool in server._tools}
        create_envelope_tool = tools['create_envelope']
        list_envelopes_tool = tools['list_envelopes']
        
        # Create a test envelope first
        await create_envelope_tool.handler(
            category="Test Category",
            budgeted_amount=200.0,
            starting_balance=50.0,
            description="Test envelope"
        )
        
        # Test listing envelopes
        result = await list_envelopes_tool.handler()
        
        assert len(result) == 1
        assert result[0].type == "text"
        
        # Parse the JSON response
        envelopes_data = json.loads(result[0].text)
        assert isinstance(envelopes_data, list)
        assert len(envelopes_data) >= 1
        
        # Check the created envelope is in the list
        test_envelope = next((env for env in envelopes_data if env['category'] == "Test Category"), None)
        assert test_envelope is not None
        assert test_envelope['budgeted_amount'] == 200.0
        assert test_envelope['starting_balance'] == 50.0
    
    @pytest.mark.asyncio
    async def test_create_transaction_tool(self, server):
        """Test the create_transaction MCP tool."""
        # Get the tool functions from server
        tools = {tool.name: tool for tool in server._tools}
        create_envelope_tool = tools['create_envelope']
        create_transaction_tool = tools['create_transaction']
        
        # Create an envelope first
        envelope_result = await create_envelope_tool.handler(
            category="Test Budget",
            budgeted_amount=300.0,
            starting_balance=200.0,
            description="Test budget for transactions"
        )
        envelope_data = json.loads(envelope_result[0].text)
        envelope_id = envelope_data['id']
        
        # Test creating a transaction
        result = await create_transaction_tool.handler(
            envelope_id=envelope_id,
            amount=50.0,
            description="Test grocery purchase",
            date="2024-01-15",
            type="expense"
        )
        
        assert len(result) == 1
        assert result[0].type == "text"
        
        # Parse the JSON response
        transaction_data = json.loads(result[0].text)
        assert transaction_data['envelope_id'] == envelope_id
        assert transaction_data['amount'] == 50.0
        assert transaction_data['description'] == "Test grocery purchase"
        assert transaction_data['date'] == "2024-01-15"
        assert transaction_data['type'] == "expense"
        assert 'id' in transaction_data
    
    @pytest.mark.asyncio
    async def test_get_budget_summary_tool(self, server):
        """Test the get_budget_summary MCP tool."""
        # Get the tool functions from server
        tools = {tool.name: tool for tool in server._tools}
        create_envelope_tool = tools['create_envelope']
        create_transaction_tool = tools['create_transaction']
        get_budget_summary_tool = tools['get_budget_summary']
        
        # Create test data
        envelope_result = await create_envelope_tool.handler(
            category="Summary Test",
            budgeted_amount=1000.0,
            starting_balance=800.0,
            description="Test envelope for summary"
        )
        envelope_data = json.loads(envelope_result[0].text)
        envelope_id = envelope_data['id']
        
        # Add a transaction
        await create_transaction_tool.handler(
            envelope_id=envelope_id,
            amount=150.0,
            description="Test expense",
            date="2024-01-20",
            type="expense"
        )
        
        # Test getting budget summary
        result = await get_budget_summary_tool.handler()
        
        assert len(result) == 1
        assert result[0].type == "text"
        
        # Parse the JSON response
        summary_data = json.loads(result[0].text)
        assert 'budget_summary' in summary_data
        assert 'envelope_count' in summary_data
        assert 'envelopes' in summary_data
        
        budget_summary = summary_data['budget_summary']
        assert budget_summary['total_budgeted_amount'] >= 1000.0
        assert budget_summary['total_starting_balance'] >= 800.0
        assert 'total_current_balance' in budget_summary
        assert 'total_spent' in budget_summary
    
    @pytest.mark.asyncio
    async def test_error_handling(self, server):
        """Test error handling in MCP tools."""
        # Get the tool function from server
        tools = {tool.name: tool for tool in server._tools}
        create_envelope_tool = tools['create_envelope']
        
        # Test creating envelope with invalid data
        result = await create_envelope_tool.handler(
            category="",  # Empty category should cause error
            budgeted_amount=100.0,
            starting_balance=50.0,
            description="Test"
        )
        
        assert len(result) == 1
        assert result[0].type == "text"
        assert "Error:" in result[0].text