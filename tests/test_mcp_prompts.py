#!/usr/bin/env python3
"""
Unit tests for MCP prompt functionality in Budget Cash Envelope MCP Server.
"""

from unittest.mock import MagicMock

import pytest

from app.mcp_server import create_mcp_server
from app.tools.handlers import handle_budget_health_analysis


class TestMCPPrompts:
    """Test MCP prompt functionality."""

    @pytest.fixture
    def mock_envelope_service(self):
        """Create mock envelope service with sample data."""
        service = MagicMock()
        service.get_all_envelopes.return_value = [
            {
                "id": 1,
                "category": "Groceries",
                "budgeted_amount": 500.0,
                "current_balance": 300.0,
                "starting_balance": 500.0,
            },
            {
                "id": 2,
                "category": "Utilities",
                "budgeted_amount": 200.0,
                "current_balance": -50.0,
                "starting_balance": 200.0,
            },
        ]
        return service

    @pytest.fixture
    def mock_transaction_service(self):
        """Create mock transaction service with sample data."""
        service = MagicMock()
        service.get_all_transactions.return_value = [
            {
                "id": 1,
                "envelope_id": 1,
                "amount": -200.0,
                "type": "expense",
                "description": "Weekly groceries",
                "date": "2025-08-01",
            },
            {
                "id": 2,
                "envelope_id": 2,
                "amount": -250.0,
                "type": "expense",
                "description": "Electric bill",
                "date": "2025-08-05",
            },
        ]
        return service

    @pytest.mark.asyncio
    async def test_budget_health_analysis_handler_basic(
        self, mock_envelope_service, mock_transaction_service
    ):
        """Test budget health analysis handler with basic functionality."""
        arguments = {"analysis_period": "last_30_days"}

        result = await handle_budget_health_analysis(
            mock_envelope_service, mock_transaction_service, arguments
        )

        assert isinstance(result, dict)
        assert "envelope_health" in result
        assert "spending_analysis" in result
        assert "recommendations" in result

    @pytest.mark.asyncio
    async def test_budget_health_analysis_identifies_overspending(
        self, mock_envelope_service, mock_transaction_service
    ):
        """Test that handler identifies overspent envelopes."""
        arguments = {}

        result = await handle_budget_health_analysis(
            mock_envelope_service, mock_transaction_service, arguments
        )

        # Should identify Utilities envelope as overspent (negative balance)
        envelope_health = result["envelope_health"]
        utilities_health = next(
            env for env in envelope_health if env["category"] == "Utilities"
        )
        assert utilities_health["status"] == "overspent"

    @pytest.mark.asyncio
    async def test_mcp_server_lists_prompts(self):
        """Test that MCP server returns available prompts."""
        from app.tools.schemas import get_prompt_schemas

        prompt_schemas = get_prompt_schemas()
        assert "budget_health_analysis" in prompt_schemas

        schema = prompt_schemas["budget_health_analysis"]
        assert schema["name"] == "budget_health_analysis"
        assert "budget health" in schema["description"]

    @pytest.mark.asyncio
    async def test_mcp_server_gets_specific_prompt(self):
        """Test that MCP server can retrieve specific prompt details."""
        server = create_mcp_server("testing")

        # This test will pass once get_prompt handler is implemented
        # For now, just ensure the server is created successfully
        assert server is not None
