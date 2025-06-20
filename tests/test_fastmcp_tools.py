import pytest
import asyncio
import json
from app.fastmcp_server import create_fastmcp_server
from app.config import Config


class TestFastMCPTools:
    """Test suite for FastMCP tools functionality."""
    
    @pytest.fixture
    def server(self):
        """Create a test FastMCP server instance."""
        return create_fastmcp_server('testing')
    
    @pytest.fixture
    def event_loop(self):
        """Create an event loop for async tests."""
        loop = asyncio.new_event_loop()
        yield loop
        loop.close()
    
    @pytest.mark.asyncio
    async def test_create_envelope_tool(self, server):
        """Test the create_envelope FastMCP tool."""
        # Get the tool function from server
        tools = await server.get_tools()
        create_envelope_tool = tools['create_envelope']
        
        # Test creating an envelope
        result = await create_envelope_tool.fn(
            category="Groceries",
            budgeted_amount=500.0,
            starting_balance=100.0,
            description="Monthly grocery budget"
        )
        
        # Parse the JSON response
        envelope_data = json.loads(result)
        assert envelope_data['category'] == "Groceries"
        assert envelope_data['budgeted_amount'] == 500.0
        assert envelope_data['starting_balance'] == 100.0
        assert envelope_data['current_balance'] == 100.0
        assert 'id' in envelope_data
    
    @pytest.mark.asyncio
    async def test_list_envelopes_tool(self, server):
        """Test the list_envelopes FastMCP tool."""
        # Get the tool functions from server
        tools = await server.get_tools()
        create_envelope_tool = tools['create_envelope']
        list_envelopes_tool = tools['list_envelopes']
        
        # Create a test envelope first
        await create_envelope_tool.fn(
            category="Test Category",
            budgeted_amount=200.0,
            starting_balance=50.0,
            description="Test envelope"
        )
        
        # Test listing envelopes
        result = await list_envelopes_tool.fn()
        
        # Parse the JSON response
        envelopes_data = json.loads(result)
        assert isinstance(envelopes_data, list)
        assert len(envelopes_data) >= 1
        
        # Check the created envelope is in the list
        test_envelope = next((env for env in envelopes_data if env['category'] == "Test Category"), None)
        assert test_envelope is not None
        assert test_envelope['budgeted_amount'] == 200.0
        assert test_envelope['starting_balance'] == 50.0
    
    @pytest.mark.asyncio
    async def test_create_transaction_tool(self, server):
        """Test the create_transaction FastMCP tool."""
        # Get the tool functions from server
        tools = await server.get_tools()
        create_envelope_tool = tools['create_envelope']
        create_transaction_tool = tools['create_transaction']
        
        # Create an envelope first
        envelope_result = await create_envelope_tool.fn(
            category="Test Budget",
            budgeted_amount=300.0,
            starting_balance=200.0,
            description="Test budget for transactions"
        )
        envelope_data = json.loads(envelope_result)
        envelope_id = envelope_data['id']
        
        # Test creating a transaction
        result = await create_transaction_tool.fn(
            envelope_id=envelope_id,
            amount=50.0,
            description="Test grocery purchase",
            type="expense",
            date="2024-01-15"
        )
        
        # Parse the JSON response
        transaction_data = json.loads(result)
        assert transaction_data['envelope_id'] == envelope_id
        assert transaction_data['amount'] == 50.0
        assert transaction_data['description'] == "Test grocery purchase"
        assert transaction_data['date'] == "2024-01-15"
        assert transaction_data['type'] == "expense"
        assert 'id' in transaction_data
    
    @pytest.mark.asyncio
    async def test_get_budget_summary_tool(self, server):
        """Test the get_budget_summary FastMCP tool."""
        # Get the tool functions from server
        tools = await server.get_tools()
        create_envelope_tool = tools['create_envelope']
        create_transaction_tool = tools['create_transaction']
        get_budget_summary_tool = tools['get_budget_summary']
        
        # Create test data
        envelope_result = await create_envelope_tool.fn(
            category="Summary Test",
            budgeted_amount=1000.0,
            starting_balance=800.0,
            description="Test envelope for summary"
        )
        envelope_data = json.loads(envelope_result)
        envelope_id = envelope_data['id']
        
        # Add a transaction
        await create_transaction_tool.fn(
            envelope_id=envelope_id,
            amount=150.0,
            description="Test expense",
            type="expense",
            date="2024-01-20"
        )
        
        # Test getting budget summary
        result = await get_budget_summary_tool.fn()
        
        # Parse the JSON response
        summary_data = json.loads(result)
        assert 'total_envelopes' in summary_data
        assert 'total_budgeted' in summary_data
        assert 'total_current_balance' in summary_data
        assert 'envelopes' in summary_data
        
        assert summary_data['total_budgeted'] >= 1000.0
        assert summary_data['total_envelopes'] >= 1
    
    @pytest.mark.asyncio
    async def test_error_handling(self, server):
        """Test error handling in FastMCP tools."""
        # Get the tool function from server
        tools = await server.get_tools()
        create_envelope_tool = tools['create_envelope']
        
        # Test creating envelope with invalid data
        result = await create_envelope_tool.fn(
            category="",  # Empty category should cause error
            budgeted_amount=100.0,
            starting_balance=50.0,
            description="Test"
        )
        
        assert "Error:" in result
    
    @pytest.mark.asyncio
    async def test_tool_availability(self, server):
        """Test that all expected tools are available."""
        tools = await server.get_tools()
        
        expected_tools = [
            'create_envelope',
            'list_envelopes', 
            'get_envelope',
            'update_envelope',
            'delete_envelope',
            'create_transaction',
            'list_transactions',
            'get_transaction',
            'update_transaction',
            'delete_transaction',
            'get_envelope_balance',
            'get_budget_summary'
        ]
        
        for tool_name in expected_tools:
            assert tool_name in tools, f"Tool '{tool_name}' not found in server tools"
    
    @pytest.mark.asyncio
    async def test_envelope_balance_tool(self, server):
        """Test the get_envelope_balance FastMCP tool."""
        # Get the tool functions from server
        tools = await server.get_tools()
        create_envelope_tool = tools['create_envelope']
        get_envelope_balance_tool = tools['get_envelope_balance']
        
        # Create an envelope
        envelope_result = await create_envelope_tool.fn(
            category="Balance Test",
            budgeted_amount=500.0,
            starting_balance=300.0,
            description="Test envelope for balance"
        )
        envelope_data = json.loads(envelope_result)
        envelope_id = envelope_data['id']
        
        # Test getting envelope balance
        result = await get_envelope_balance_tool.fn(envelope_id=envelope_id)
        
        # Parse the JSON response
        balance_data = json.loads(result)
        assert 'current_balance' in balance_data
        assert balance_data['current_balance'] == 300.0
    
    @pytest.mark.asyncio
    async def test_update_and_delete_envelope(self, server):
        """Test updating and deleting envelopes."""
        # Get the tool functions from server
        tools = await server.get_tools()
        create_envelope_tool = tools['create_envelope']
        update_envelope_tool = tools['update_envelope']
        delete_envelope_tool = tools['delete_envelope']
        
        # Create an envelope
        envelope_result = await create_envelope_tool.fn(
            category="Update Test",
            budgeted_amount=400.0,
            starting_balance=200.0,
            description="Test envelope for updates"
        )
        envelope_data = json.loads(envelope_result)
        envelope_id = envelope_data['id']
        
        # Test updating envelope
        update_result = await update_envelope_tool.fn(
            envelope_id=envelope_id,
            category="Updated Category",
            budgeted_amount=600.0
        )
        updated_data = json.loads(update_result)
        assert updated_data['category'] == "Updated Category"
        assert updated_data['budgeted_amount'] == 600.0
        
        # Test deleting envelope
        delete_result = await delete_envelope_tool.fn(envelope_id=envelope_id)
        delete_data = json.loads(delete_result)
        assert 'message' in delete_data
        assert 'deleted' in delete_data['message'].lower()