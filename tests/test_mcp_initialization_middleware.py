"""
Tests for MCP initialization check middleware.
"""

import json
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.auth import MCPInitializationMiddleware


class TestMCPInitializationMiddleware:
    """Test suite for MCP initialization check middleware."""

    @pytest.fixture
    def middleware(self) -> MCPInitializationMiddleware:
        """Create a test middleware instance."""
        mock_app = Mock()
        return MCPInitializationMiddleware(mock_app)

    @pytest.fixture
    def mock_request(self) -> Mock:
        """Create a mock request object."""
        request = Mock(spec=Request)
        request.method = "POST"
        request.headers = {"content-type": "application/json"}
        request.client = Mock()
        request.client.host = "127.0.0.1"
        return request

    def test_get_session_id(self, middleware: MCPInitializationMiddleware) -> None:
        """Test session ID generation."""
        request = Mock()
        request.client = Mock()
        request.client.host = "192.168.1.1"
        request.headers = {"user-agent": "test-client/1.0"}

        session_id = middleware._get_session_id(request)
        assert session_id == "192.168.1.1:test-client/1.0"

    def test_get_session_id_no_client(
        self, middleware: MCPInitializationMiddleware
    ) -> None:
        """Test session ID generation when client is None."""
        request = Mock()
        request.client = None
        request.headers = {"user-agent": "test-client/1.0"}

        session_id = middleware._get_session_id(request)
        assert session_id == "unknown:test-client/1.0"

    def test_get_session_id_no_user_agent(
        self, middleware: MCPInitializationMiddleware
    ) -> None:
        """Test session ID generation when user agent is missing."""
        request = Mock()
        request.client = Mock()
        request.client.host = "192.168.1.1"
        request.headers = {}

        session_id = middleware._get_session_id(request)
        assert session_id == "192.168.1.1:unknown"

    def test_is_mcp_protocol_request_valid(
        self, middleware: MCPInitializationMiddleware
    ) -> None:
        """Test MCP protocol request detection for valid requests."""
        request = Mock()
        request.method = "POST"
        request.headers = {"content-type": "application/json"}

        assert middleware._is_mcp_protocol_request(request) is True

    def test_is_mcp_protocol_request_wrong_method(
        self, middleware: MCPInitializationMiddleware
    ) -> None:
        """Test MCP protocol request detection for wrong HTTP method."""
        request = Mock()
        request.method = "GET"
        request.headers = {"content-type": "application/json"}

        assert middleware._is_mcp_protocol_request(request) is False

    def test_is_mcp_protocol_request_wrong_content_type(
        self, middleware: MCPInitializationMiddleware
    ) -> None:
        """Test MCP protocol request detection for wrong content type."""
        request = Mock()
        request.method = "POST"
        request.headers = {"content-type": "text/plain"}

        assert middleware._is_mcp_protocol_request(request) is False

    @pytest.mark.asyncio
    async def test_check_request_body_for_protocol_initialize(
        self, middleware: MCPInitializationMiddleware
    ) -> None:
        """Test protocol request detection for initialize method."""
        request = Mock()
        body_data = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"protocolVersion": "2024-11-05"},
        }
        request.body = AsyncMock(return_value=json.dumps(body_data).encode())

        is_protocol, data = await middleware._check_request_body_for_protocol(request)
        assert is_protocol is True
        assert data == body_data

    @pytest.mark.asyncio
    async def test_check_request_body_for_protocol_initialized(
        self, middleware: MCPInitializationMiddleware
    ) -> None:
        """Test protocol request detection for initialized notification."""
        request = Mock()
        body_data = {"jsonrpc": "2.0", "method": "notifications/initialized"}
        request.body = AsyncMock(return_value=json.dumps(body_data).encode())

        is_protocol, data = await middleware._check_request_body_for_protocol(request)
        assert is_protocol is True
        assert data == body_data

    @pytest.mark.asyncio
    async def test_check_request_body_for_protocol_ping(
        self, middleware: MCPInitializationMiddleware
    ) -> None:
        """Test protocol request detection for ping method."""
        request = Mock()
        body_data = {"jsonrpc": "2.0", "id": 2, "method": "ping"}
        request.body = AsyncMock(return_value=json.dumps(body_data).encode())

        is_protocol, data = await middleware._check_request_body_for_protocol(request)
        assert is_protocol is True
        assert data == body_data

    @pytest.mark.asyncio
    async def test_check_request_body_for_protocol_tools_list(
        self, middleware: MCPInitializationMiddleware
    ) -> None:
        """Test protocol request detection for tools/list method."""
        request = Mock()
        body_data = {"jsonrpc": "2.0", "id": 3, "method": "tools/list"}
        request.body = AsyncMock(return_value=json.dumps(body_data).encode())

        is_protocol, data = await middleware._check_request_body_for_protocol(request)
        assert is_protocol is False
        assert data == body_data

    @pytest.mark.asyncio
    async def test_check_request_body_for_protocol_invalid_json(
        self, middleware: MCPInitializationMiddleware
    ) -> None:
        """Test protocol request detection for invalid JSON."""
        request = Mock()
        request.body = AsyncMock(return_value=b"invalid json")

        is_protocol, data = await middleware._check_request_body_for_protocol(request)
        assert is_protocol is False
        assert data is None

    @pytest.mark.asyncio
    async def test_check_request_body_for_protocol_empty_body(
        self, middleware: MCPInitializationMiddleware
    ) -> None:
        """Test protocol request detection for empty body."""
        request = Mock()
        request.body = AsyncMock(return_value=b"")

        is_protocol, data = await middleware._check_request_body_for_protocol(request)
        assert is_protocol is False
        assert data is None

    def test_handle_initialized_notification(
        self, middleware: MCPInitializationMiddleware
    ) -> None:
        """Test handling of initialized notification."""
        session_id = "test-session"
        data = {"method": "notifications/initialized"}

        # Initially session should not be initialized
        assert not middleware._is_session_initialized(session_id)

        # Handle the notification
        middleware._handle_initialized_notification(session_id, data)

        # Now session should be initialized
        assert middleware._is_session_initialized(session_id)

    def test_handle_initialized_notification_wrong_method(
        self, middleware: MCPInitializationMiddleware
    ) -> None:
        """Test handling of notification with wrong method."""
        session_id = "test-session"
        data = {"method": "initialize"}

        # Handle the notification (should not mark as initialized)
        middleware._handle_initialized_notification(session_id, data)

        # Session should not be initialized
        assert not middleware._is_session_initialized(session_id)

    def test_create_initialization_error(
        self, middleware: MCPInitializationMiddleware
    ) -> None:
        """Test creation of initialization error response."""
        response = middleware._create_initialization_error()

        assert isinstance(response, JSONResponse)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        # Check response content
        content = response.body.decode()
        data = json.loads(content)
        assert data["error"] == "MCP session not initialized"
        assert "initialization handshake" in data["message"]
        assert data["code"] == "mcp_not_initialized"

    @pytest.mark.asyncio
    async def test_dispatch_protocol_request_initialize(
        self, middleware: MCPInitializationMiddleware, mock_request: Mock
    ) -> None:
        """Test dispatch for initialize protocol request."""
        body_data = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"protocolVersion": "2024-11-05"},
        }
        mock_request.body = AsyncMock(return_value=json.dumps(body_data).encode())

        # Mock call_next to return a response
        mock_response = Mock()
        call_next = AsyncMock(return_value=mock_response)

        # Mock request._receive attribute for body reconstruction
        mock_request._receive = None

        response = await middleware.dispatch(mock_request, call_next)

        # Should call next middleware and return its response
        call_next.assert_called_once_with(mock_request)
        assert response == mock_response

        # Check that request body was reconstructed
        assert hasattr(mock_request, "_receive")

    @pytest.mark.asyncio
    async def test_dispatch_protocol_request_initialized(
        self, middleware: MCPInitializationMiddleware, mock_request: Mock
    ) -> None:
        """Test dispatch for initialized notification."""
        body_data = {"jsonrpc": "2.0", "method": "notifications/initialized"}
        mock_request.body = AsyncMock(return_value=json.dumps(body_data).encode())

        # Mock session ID
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {
            "user-agent": "test-client",
            "content-type": "application/json",
        }

        # Mock call_next to return a response
        mock_response = Mock()
        call_next = AsyncMock(return_value=mock_response)

        # Mock request._receive attribute for body reconstruction
        mock_request._receive = None

        response = await middleware.dispatch(mock_request, call_next)

        # Should call next middleware and return its response
        call_next.assert_called_once_with(mock_request)
        assert response == mock_response

        # Session should now be marked as initialized
        session_id = middleware._get_session_id(mock_request)
        assert middleware._is_session_initialized(session_id)

    @pytest.mark.asyncio
    async def test_dispatch_non_protocol_request_uninitialized(
        self, middleware: MCPInitializationMiddleware, mock_request: Mock
    ) -> None:
        """Test dispatch for non-protocol request from uninitialized session."""
        # Make it not look like a protocol request
        mock_request.method = "GET"

        # Mock session ID
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"user-agent": "test-client"}

        call_next = AsyncMock()

        response = await middleware.dispatch(mock_request, call_next)

        # Should return error response without calling next middleware
        call_next.assert_not_called()
        assert isinstance(response, JSONResponse)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.asyncio
    async def test_dispatch_non_protocol_request_initialized(
        self, middleware: MCPInitializationMiddleware, mock_request: Mock
    ) -> None:
        """Test dispatch for non-protocol request from initialized session."""
        # Make it not look like a protocol request
        mock_request.method = "GET"

        # Mock session ID and mark as initialized
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"user-agent": "test-client"}
        session_id = middleware._get_session_id(mock_request)
        middleware._initialized_sessions.add(session_id)

        # Mock call_next to return a response
        mock_response = Mock()
        call_next = AsyncMock(return_value=mock_response)

        response = await middleware.dispatch(mock_request, call_next)

        # Should call next middleware and return its response
        call_next.assert_called_once_with(mock_request)
        assert response == mock_response

    @pytest.mark.asyncio
    async def test_dispatch_tools_call_uninitialized(
        self, middleware: MCPInitializationMiddleware, mock_request: Mock
    ) -> None:
        """Test dispatch for tools/call from uninitialized session."""
        body_data = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": "create_envelope", "arguments": {}},
        }
        mock_request.body = AsyncMock(return_value=json.dumps(body_data).encode())

        # Mock session ID
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {
            "user-agent": "test-client",
            "content-type": "application/json",
        }

        call_next = AsyncMock()

        response = await middleware.dispatch(mock_request, call_next)

        # Should return error response without calling next middleware
        call_next.assert_not_called()
        assert isinstance(response, JSONResponse)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.asyncio
    async def test_full_initialization_flow(
        self, middleware: MCPInitializationMiddleware
    ) -> None:
        """Test a complete initialization flow."""

        # Create mock requests for the flow
        def create_mock_request(method: str, body_data: dict) -> Mock:
            request = Mock(spec=Request)
            request.method = "POST"
            request.headers = {
                "content-type": "application/json",
                "user-agent": "test-client",
            }
            request.client = Mock()
            request.client.host = "127.0.0.1"
            request.body = AsyncMock(return_value=json.dumps(body_data).encode())
            request._receive = None
            return request

        call_next = AsyncMock(return_value=Mock())

        # 1. Initialize request
        init_request = create_mock_request(
            "initialize",
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {"protocolVersion": "2024-11-05"},
            },
        )

        response = await middleware.dispatch(init_request, call_next)
        assert call_next.called
        call_next.reset_mock()

        # 2. Initialized notification
        initialized_request = create_mock_request(
            "notifications/initialized",
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
        )

        response = await middleware.dispatch(initialized_request, call_next)
        assert call_next.called
        call_next.reset_mock()

        # 3. Tool call (should now work)
        tool_request = create_mock_request(
            "tools/call",
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {"name": "create_envelope", "arguments": {}},
            },
        )

        response = await middleware.dispatch(tool_request, call_next)
        assert call_next.called
