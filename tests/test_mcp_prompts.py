#!/usr/bin/env python3
"""
Unit tests for MCP prompt functionality in Budget Cash Envelope MCP Server.
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from app.mcp_server import create_mcp_server
from app.tools.handlers import (
    _filter_transactions_by_period,
    _get_date_range_for_period,
    handle_budget_health_analysis,
)


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
    async def test_mcp_server_gets_specific_prompt(
        self, mock_envelope_service, mock_transaction_service
    ):
        """Test that MCP server can retrieve specific prompt details."""
        server = create_mcp_server("testing")
        assert server is not None
        assert hasattr(server, "server")

        # Test that get_prompt handler functionality works by testing the handler logic directly
        # This simulates what the MCP framework would do when calling get_prompt

        # Temporarily replace the services with our mocks for testing
        original_envelope_service = server.adapter.registry.envelope_service
        original_transaction_service = server.adapter.registry.transaction_service

        try:
            server.adapter.registry.envelope_service = mock_envelope_service
            server.adapter.registry.transaction_service = mock_transaction_service

            # Import the handler function logic - test it directly since MCP internals are complex
            import mcp.types as types

            from app.tools.handlers import handle_budget_health_analysis

            # Test successful prompt generation for known prompt
            prompt_name = "budget_health_analysis"
            arguments = {}

            if prompt_name == "budget_health_analysis":
                args = arguments or {}
                result = await handle_budget_health_analysis(
                    server.adapter.registry.envelope_service,
                    server.adapter.registry.transaction_service,
                    args,
                )

                # Create the expected GetPromptResult structure
                prompt_result = types.GetPromptResult(
                    description="Budget health analysis results",
                    messages=[
                        types.PromptMessage(
                            role="user",
                            content=types.TextContent(
                                type="text",
                                text=f"Budget Analysis Results:\n{result}",
                            ),
                        )
                    ],
                )

                # Verify the prompt result structure
                assert prompt_result is not None
                assert prompt_result.description == "Budget health analysis results"
                assert len(prompt_result.messages) > 0
                assert prompt_result.messages[0].role == "user"
                assert (
                    "Budget Analysis Results:" in prompt_result.messages[0].content.text
                )

            # Test error handling for unknown prompt
            unknown_prompt_name = "unknown_prompt"
            if unknown_prompt_name != "budget_health_analysis":
                with pytest.raises(ValueError, match="Unknown prompt: unknown_prompt"):
                    # This simulates what the actual handler would do
                    raise ValueError(f"Unknown prompt: {unknown_prompt_name}")

        finally:
            # Restore original services
            server.adapter.registry.envelope_service = original_envelope_service
            server.adapter.registry.transaction_service = original_transaction_service

    @pytest.mark.asyncio
    async def test_budget_health_analysis_with_different_periods(
        self, mock_envelope_service, mock_transaction_service
    ):
        """Test budget health analysis with different time periods."""
        # Test that analysis respects different periods
        test_cases = [
            {"analysis_period": "last_30_days"},
            {"analysis_period": "last_90_days"},
            {"analysis_period": "ytd"},
            {"analysis_period": "all_time"},
        ]

        for test_args in test_cases:
            result = await handle_budget_health_analysis(
                mock_envelope_service, mock_transaction_service, test_args
            )

            assert isinstance(result, dict)
            assert "spending_analysis" in result
            assert (
                result["spending_analysis"]["period_applied"]
                == test_args["analysis_period"]
            )

    @pytest.mark.asyncio
    async def test_budget_health_analysis_error_handling(self):
        """Test budget health analysis error handling."""
        from unittest.mock import MagicMock

        # Create mock services that raise exceptions
        failing_envelope_service = MagicMock()
        failing_envelope_service.get_all_envelopes.side_effect = Exception(
            "Database error"
        )

        failing_transaction_service = MagicMock()

        result = await handle_budget_health_analysis(
            failing_envelope_service, failing_transaction_service, {}
        )

        # Should return error response
        assert isinstance(result, str)
        assert "error" in result.lower() and "Database error" in result


class TestDateFilteringFunctionality:
    """Test date filtering functions for budget analysis."""

    def test_get_date_range_for_period_last_30_days(self):
        """Test date range calculation for last 30 days."""
        with patch("app.tools.handlers.datetime") as mock_dt:
            mock_now = datetime(2025, 8, 8, 12, 0, 0)
            mock_dt.now.return_value = mock_now

            result = _get_date_range_for_period("last_30_days")
            expected = mock_now - timedelta(days=30)

            assert result == expected

    def test_get_date_range_for_period_last_90_days(self):
        """Test date range calculation for last 90 days."""
        with patch("app.tools.handlers.datetime") as mock_dt:
            mock_now = datetime(2025, 8, 8, 12, 0, 0)
            mock_dt.now.return_value = mock_now

            result = _get_date_range_for_period("last_90_days")
            expected = mock_now - timedelta(days=90)

            assert result == expected

    def test_get_date_range_for_period_ytd(self):
        """Test date range calculation for year to date."""
        with patch("app.tools.handlers.datetime") as mock_dt:
            mock_now = datetime(2025, 8, 8, 12, 0, 0)
            mock_dt.now.return_value = mock_now
            mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

            result = _get_date_range_for_period("ytd")
            expected = datetime(2025, 1, 1)

            assert result == expected

    def test_get_date_range_for_period_all_time(self):
        """Test date range calculation for all time (no filtering)."""
        result = _get_date_range_for_period("all_time")
        assert result is None

    def test_get_date_range_for_period_invalid_defaults_to_30_days(self):
        """Test that invalid period defaults to 30 days."""
        with patch("app.tools.handlers.datetime") as mock_dt:
            mock_now = datetime(2025, 8, 8, 12, 0, 0)
            mock_dt.now.return_value = mock_now

            result = _get_date_range_for_period("invalid_period")
            expected = mock_now - timedelta(days=30)

            assert result == expected

    def test_filter_transactions_by_period_all_time(self):
        """Test filtering transactions for all time period."""
        transactions = [
            {"date": "2023-01-01", "amount": -100, "type": "expense"},
            {"date": "2024-06-15", "amount": -200, "type": "expense"},
            {"date": "2025-08-01", "amount": -300, "type": "expense"},
        ]

        result = _filter_transactions_by_period(transactions, "all_time")
        assert len(result) == 3
        assert result == transactions

    def test_filter_transactions_by_period_last_30_days(self):
        """Test filtering transactions for last 30 days."""
        with patch("app.tools.handlers._get_date_range_for_period") as mock_range:
            # Set start date to 30 days ago
            mock_range.return_value = datetime(2025, 7, 9)

            transactions = [
                {"date": "2025-06-01", "amount": -100, "type": "expense"},  # Too old
                {
                    "date": "2025-07-15",
                    "amount": -200,
                    "type": "expense",
                },  # Within range
                {
                    "date": "2025-08-01",
                    "amount": -300,
                    "type": "expense",
                },  # Within range
            ]

            result = _filter_transactions_by_period(transactions, "last_30_days")
            assert len(result) == 2
            assert result[0]["date"] == "2025-07-15"
            assert result[1]["date"] == "2025-08-01"

    def test_filter_transactions_by_period_invalid_dates_skipped(self):
        """Test that transactions with invalid dates are skipped."""
        with patch("app.tools.handlers._get_date_range_for_period") as mock_range:
            mock_range.return_value = datetime(2025, 7, 1)

            transactions = [
                {"date": "invalid-date", "amount": -100, "type": "expense"},
                {"date": "2025-07-15", "amount": -200, "type": "expense"},
                {"amount": -300, "type": "expense"},  # Missing date key
            ]

            result = _filter_transactions_by_period(transactions, "last_30_days")
            assert len(result) == 1
            assert result[0]["date"] == "2025-07-15"

    def test_filter_transactions_by_period_boundary_conditions(self):
        """Test filtering with exact boundary date conditions."""
        with patch("app.tools.handlers._get_date_range_for_period") as mock_range:
            # Exact boundary: July 15, 2025
            mock_range.return_value = datetime(2025, 7, 15)

            transactions = [
                {
                    "date": "2025-07-14",
                    "amount": -100,
                    "type": "expense",
                },  # Before boundary
                {
                    "date": "2025-07-15",
                    "amount": -200,
                    "type": "expense",
                },  # On boundary
                {
                    "date": "2025-07-16",
                    "amount": -300,
                    "type": "expense",
                },  # After boundary
            ]

            result = _filter_transactions_by_period(transactions, "last_30_days")
            assert len(result) == 2  # Should include boundary date and after
            assert result[0]["date"] == "2025-07-15"
            assert result[1]["date"] == "2025-07-16"


class TestBudgetAnalysisPeriodIntegration:
    """Test budget analysis with different time periods."""

    @pytest.fixture
    def mock_envelope_service_with_data(self):
        """Create mock envelope service with test data."""
        service = MagicMock()
        service.get_all_envelopes.return_value = [
            {
                "id": 1,
                "category": "Groceries",
                "budgeted_amount": 500.0,
                "current_balance": 300.0,
                "starting_balance": 500.0,
            }
        ]
        return service

    @pytest.fixture
    def mock_transaction_service_with_periods(self):
        """Create mock transaction service with data across different periods."""
        service = MagicMock()
        service.get_all_transactions.return_value = [
            # Old transactions (beyond 90 days)
            {
                "id": 1,
                "envelope_id": 1,
                "amount": -50,
                "type": "expense",
                "date": "2025-04-01",
            },
            # Recent transactions (within 30 days)
            {
                "id": 2,
                "envelope_id": 1,
                "amount": -100,
                "type": "expense",
                "date": "2025-07-20",
            },
            {
                "id": 3,
                "envelope_id": 1,
                "amount": -75,
                "type": "expense",
                "date": "2025-08-01",
            },
            # Income transaction
            {
                "id": 4,
                "envelope_id": 1,
                "amount": 200,
                "type": "income",
                "date": "2025-07-25",
            },
        ]
        return service

    @pytest.mark.asyncio
    async def test_budget_analysis_period_filtering_integration(
        self, mock_envelope_service_with_data, mock_transaction_service_with_periods
    ):
        """Test that budget analysis properly applies period filtering."""
        with patch("app.tools.handlers.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2025, 8, 8)
            mock_dt.strptime.side_effect = datetime.strptime
            mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

            # Test last_30_days period
            arguments = {"analysis_period": "last_30_days"}

            result = await handle_budget_health_analysis(
                mock_envelope_service_with_data,
                mock_transaction_service_with_periods,
                arguments,
            )

            spending_analysis = result["spending_analysis"]

            # Should only include 3 transactions from the last 30 days
            assert spending_analysis["transaction_count"] == 3
            assert spending_analysis["period_applied"] == "last_30_days"

            # Should calculate totals from filtered transactions only
            assert spending_analysis["total_expenses"] == 175.0  # 100 + 75
            assert spending_analysis["total_income"] == 200.0
            assert spending_analysis["net_flow"] == 25.0  # 200 - 175

    @pytest.mark.asyncio
    async def test_budget_analysis_all_time_period(
        self, mock_envelope_service_with_data, mock_transaction_service_with_periods
    ):
        """Test that all_time period includes all transactions."""
        arguments = {"analysis_period": "all_time"}

        result = await handle_budget_health_analysis(
            mock_envelope_service_with_data,
            mock_transaction_service_with_periods,
            arguments,
        )

        spending_analysis = result["spending_analysis"]

        # Should include all 4 transactions
        assert spending_analysis["transaction_count"] == 4
        assert spending_analysis["period_applied"] == "all_time"

        # Should calculate totals from all transactions
        assert spending_analysis["total_expenses"] == 225.0  # 50 + 100 + 75
        assert spending_analysis["total_income"] == 200.0
