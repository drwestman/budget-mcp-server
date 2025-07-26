from fastapi.testclient import TestClient

# No longer need to import create_mcp_server directly in tests
# The client fixture from conftest will provide the test client


class TestMCPTools:
    """Test suite for MCP tools functionality using TestClient."""

    def test_create_envelope_tool(self, client: TestClient) -> None:
        """Test the create_envelope MCP tool via HTTP."""
        response = client.post(
            "/tools/create_envelope",
            json={
                "category": "Groceries",
                "budgeted_amount": 500.0,
                "starting_balance": 100.0,
                "description": "Monthly grocery budget",
            },
        )
        assert response.status_code == 200
        envelope_data = response.json()
        assert envelope_data["category"] == "Groceries"
        assert envelope_data["budgeted_amount"] == 500.0
        assert envelope_data["starting_balance"] == 100.0
        assert "id" in envelope_data

    def test_list_envelopes_tool(self, client: TestClient) -> None:
        """Test the list_envelopes MCP tool via HTTP."""
        # Create a test envelope first
        client.post(
            "/tools/create_envelope",
            json={
                "category": "Test Category",
                "budgeted_amount": 200.0,
                "starting_balance": 50.0,
                "description": "Test envelope",
            },
        )

        response = client.post("/tools/list_envelopes")
        assert response.status_code == 200
        envelopes_data = response.json()
        assert isinstance(envelopes_data, list)
        assert len(envelopes_data) >= 1

        test_envelope = next(
            (env for env in envelopes_data if env["category"] == "Test Category"), None
        )
        assert test_envelope is not None
        assert test_envelope["budgeted_amount"] == 200.0
        assert test_envelope["starting_balance"] == 50.0

    def test_create_transaction_tool(self, client: TestClient) -> None:
        """Test the create_transaction MCP tool via HTTP."""
        # Create an envelope first
        envelope_response = client.post(
            "/tools/create_envelope",
            json={
                "category": "Test Budget",
                "budgeted_amount": 300.0,
                "starting_balance": 200.0,
                "description": "Test budget for transactions",
            },
        )
        envelope_data = envelope_response.json()
        envelope_id = envelope_data["id"]

        response = client.post(
            "/tools/create_transaction",
            json={
                "envelope_id": envelope_id,
                "amount": 50.0,
                "description": "Test grocery purchase",
                "date": "2024-01-15",
                "type": "expense",
            },
        )
        assert response.status_code == 200
        transaction_data = response.json()
        assert transaction_data["envelope_id"] == envelope_id
        assert transaction_data["amount"] == 50.0
        assert transaction_data["description"] == "Test grocery purchase"
        assert transaction_data["date"] == "2024-01-15"
        assert transaction_data["type"] == "expense"
        assert "id" in transaction_data

    def test_get_budget_summary_tool(self, client: TestClient) -> None:
        """Test the get_budget_summary MCP tool via HTTP."""
        # Create test data
        envelope_response = client.post(
            "/tools/create_envelope",
            json={
                "category": "Summary Test",
                "budgeted_amount": 1000.0,
                "starting_balance": 800.0,
                "description": "Test envelope for summary",
            },
        )
        envelope_data = envelope_response.json()
        envelope_id = envelope_data["id"]

        client.post(
            "/tools/create_transaction",
            json={
                "envelope_id": envelope_id,
                "amount": 150.0,
                "description": "Test expense",
                "date": "2024-01-20",
                "type": "expense",
            },
        )

        response = client.post("/tools/get_budget_summary")
        assert response.status_code == 200
        summary_data = response.json()
        assert "total_envelopes" in summary_data
        assert "total_budgeted" in summary_data
        assert "total_current_balance" in summary_data
        assert "total_spent" in summary_data
        assert "envelopes" in summary_data

    def test_error_handling(self, client: TestClient) -> None:
        """Test error handling in MCP tools via HTTP."""
        response = client.post(
            "/tools/create_envelope",
            json={
                "category": "",  # Empty category should cause error
                "budgeted_amount": 100.0,
                "starting_balance": 50.0,
                "description": "Test",
            },
        )
        assert response.status_code == 200  # The tool itself returns a 200
        assert "Error:" in response.text

    def test_tool_schema_generation(self, client: TestClient) -> None:
        """Test the input schema generation for MCP tools via HTTP."""
        response = client.get("/tools")
        assert response.status_code == 200
        tools_data = response.json()
        tools = {tool["name"]: tool for tool in tools_data}

        # Test schema for create_envelope
        create_envelope_tool = tools.get("create_envelope")
        assert create_envelope_tool is not None
        schema = create_envelope_tool["input_schema"]
        assert schema["type"] == "object"
        assert "category" in schema["properties"]
        assert schema["properties"]["category"]["type"] == "string"
        assert "budgeted_amount" in schema["properties"]
        assert schema["properties"]["budgeted_amount"]["type"] == "number"
        assert "starting_balance" in schema["properties"]
        assert schema["properties"]["starting_balance"]["type"] == "number"
        assert "description" in schema["properties"]
        assert schema["properties"]["description"]["type"] == "string"
        assert "category" in schema["required"]
        assert "budgeted_amount" in schema["required"]
        assert "starting_balance" not in schema.get("required", [])
        assert "description" not in schema.get("required", [])

        # Test schema for list_transactions
        list_transactions_tool = tools.get("list_transactions")
        assert list_transactions_tool is not None
        schema = list_transactions_tool["input_schema"]
        assert schema["type"] == "object"
        assert "envelope_id" in schema["properties"]
        assert schema["properties"]["envelope_id"]["type"] == "integer"
        assert "envelope_id" not in schema.get("required", [])

        # Test schema for get_envelope
        get_envelope_tool = tools.get("get_envelope")
        assert get_envelope_tool is not None
        schema = get_envelope_tool["input_schema"]
        assert "envelope_id" in schema["properties"]
        assert schema["properties"]["envelope_id"]["type"] == "integer"
        assert "envelope_id" in schema["required"]
