"""
Unit tests for bearer token authentication middleware.
"""
import pytest
from unittest.mock import Mock, AsyncMock
from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.auth import BearerTokenMiddleware, create_auth_middleware


class TestBearerTokenMiddleware:
    """Test cases for BearerTokenMiddleware class."""

    def test_init_with_valid_token(self):
        """Test middleware initialization with valid bearer token."""
        app = Mock()
        token = "test-token-123"
        middleware = BearerTokenMiddleware(app, bearer_token=token)

        assert middleware.bearer_token == token
        assert middleware.app == app

    def test_init_with_empty_token_raises_error(self):
        """Test middleware initialization with empty token raises ValueError."""
        app = Mock()

        with pytest.raises(ValueError, match="Bearer token cannot be empty"):
            BearerTokenMiddleware(app, bearer_token="")

        with pytest.raises(ValueError, match="Bearer token cannot be empty"):
            BearerTokenMiddleware(app, bearer_token=None)

    @pytest.mark.asyncio
    async def test_dispatch_missing_authorization_header(self):
        """Test request without Authorization header returns 401."""
        app = Mock()
        middleware = BearerTokenMiddleware(app, bearer_token="test-token")

        # Mock request without Authorization header
        request = Mock(spec=Request)
        request.headers = {}
        call_next = AsyncMock()

        response = await middleware.dispatch(request, call_next)

        assert isinstance(response, JSONResponse)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.body == b'{"error":"Missing Authorization header"}'
        call_next.assert_not_called()

    @pytest.mark.asyncio
    async def test_dispatch_invalid_authorization_header_format(self):
        """Test request with invalid Authorization header format returns 401."""
        app = Mock()
        middleware = BearerTokenMiddleware(app, bearer_token="test-token")

        # Mock request with invalid Authorization header
        request = Mock(spec=Request)
        request.headers = {"Authorization": "Basic dXNlcjpwYXNz"}  # Not Bearer
        call_next = AsyncMock()

        response = await middleware.dispatch(request, call_next)

        assert isinstance(response, JSONResponse)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert b"Invalid Authorization header format" in response.body
        call_next.assert_not_called()

    @pytest.mark.asyncio
    async def test_dispatch_missing_token_in_bearer_header(self):
        """Test request with Bearer header but no token returns 401."""
        app = Mock()
        middleware = BearerTokenMiddleware(app, bearer_token="test-token")

        # Mock request with Bearer header but missing token
        request = Mock(spec=Request)
        request.headers = {"Authorization": "Bearer"}  # No token after Bearer
        call_next = AsyncMock()

        response = await middleware.dispatch(request, call_next)

        assert isinstance(response, JSONResponse)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        # "Bearer" without space and token fails the startswith check
        assert b"Invalid Authorization header format" in response.body
        call_next.assert_not_called()

    @pytest.mark.asyncio
    async def test_dispatch_bearer_with_space_but_no_token(self):
        """Test request with 'Bearer ' but no actual token returns 401."""
        app = Mock()
        middleware = BearerTokenMiddleware(app, bearer_token="test-token")

        # Mock request with Bearer header with space but missing token
        request = Mock(spec=Request)
        request.headers = {"Authorization": "Bearer "}  # Space but no token
        call_next = AsyncMock()

        response = await middleware.dispatch(request, call_next)

        assert isinstance(response, JSONResponse)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        # "Bearer " results in empty token, which fails token validation
        assert b"Invalid bearer token" in response.body
        call_next.assert_not_called()

    @pytest.mark.asyncio
    async def test_dispatch_invalid_bearer_token(self):
        """Test request with invalid bearer token returns 401."""
        app = Mock()
        middleware = BearerTokenMiddleware(app, bearer_token="correct-token")

        # Mock request with wrong bearer token
        request = Mock(spec=Request)
        request.headers = {"Authorization": "Bearer wrong-token"}
        call_next = AsyncMock()

        response = await middleware.dispatch(request, call_next)

        assert isinstance(response, JSONResponse)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert b"Invalid bearer token" in response.body
        call_next.assert_not_called()

    @pytest.mark.asyncio
    async def test_dispatch_valid_bearer_token_allows_request(self):
        """Test request with valid bearer token proceeds to next handler."""
        app = Mock()
        middleware = BearerTokenMiddleware(app, bearer_token="correct-token")

        # Mock request with correct bearer token
        request = Mock(spec=Request)
        request.headers = {"Authorization": "Bearer correct-token"}

        # Mock successful response from next handler
        expected_response = Mock()
        call_next = AsyncMock(return_value=expected_response)

        response = await middleware.dispatch(request, call_next)

        assert response == expected_response
        call_next.assert_called_once_with(request)

    @pytest.mark.asyncio
    async def test_dispatch_case_insensitive_authorization_header(self):
        """Test that Authorization header is case-insensitive."""
        app = Mock()
        middleware = BearerTokenMiddleware(app, bearer_token="test-token")

        # Create a case-insensitive headers mock
        class CaseInsensitiveHeaders:
            def __init__(self, headers):
                self._headers = {k.lower(): v for k, v in headers.items()}

            def get(self, key, default=None):
                return self._headers.get(key.lower(), default)

        # Mock request with lowercase authorization header
        request = Mock(spec=Request)
        request.headers = CaseInsensitiveHeaders({"authorization": "Bearer test-token"})

        expected_response = Mock()
        call_next = AsyncMock(return_value=expected_response)

        response = await middleware.dispatch(request, call_next)

        assert response == expected_response
        call_next.assert_called_once_with(request)

    @pytest.mark.asyncio
    async def test_dispatch_bearer_token_with_spaces(self):
        """Test bearer token with spaces is handled correctly."""
        app = Mock()
        token_with_spaces = "token with spaces"
        middleware = BearerTokenMiddleware(app, bearer_token=token_with_spaces)

        # Mock request with bearer token containing spaces
        request = Mock(spec=Request)
        request.headers = {"Authorization": f"Bearer {token_with_spaces}"}

        expected_response = Mock()
        call_next = AsyncMock(return_value=expected_response)

        response = await middleware.dispatch(request, call_next)

        assert response == expected_response
        call_next.assert_called_once_with(request)


class TestCreateAuthMiddleware:
    """Test cases for create_auth_middleware factory function."""

    def test_create_auth_middleware_with_valid_token(self):
        """Test factory function creates middleware with valid token."""
        token = "test-token-123"
        middleware_factory = create_auth_middleware(token)

        # Factory should return a callable
        assert callable(middleware_factory)

        # Factory should create BearerTokenMiddleware when called with app
        app = Mock()
        middleware = middleware_factory(app)

        assert isinstance(middleware, BearerTokenMiddleware)
        assert middleware.bearer_token == token
        assert middleware.app == app

    def test_create_auth_middleware_with_empty_token_raises_error(self):
        """Test factory function with empty token raises ValueError."""
        with pytest.raises(ValueError, match="Bearer token cannot be empty"):
            create_auth_middleware("")

        with pytest.raises(ValueError, match="Bearer token cannot be empty"):
            create_auth_middleware(None)


class TestMiddlewareIntegration:
    """Integration tests for middleware with FastAPI app."""

    @pytest.mark.asyncio
    async def test_middleware_integration_with_fastapi_headers(self):
        """Test middleware works with actual FastAPI Request headers."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        app = FastAPI()
        app.add_middleware(BearerTokenMiddleware, bearer_token="test-token")

        @app.get("/test")
        async def test_endpoint():
            return {"message": "success"}

        client = TestClient(app)

        # Test without authorization header
        response = client.get("/test")
        assert response.status_code == 401
        assert "Missing Authorization header" in response.json()["error"]

        # Test with invalid token
        response = client.get("/test", headers={"Authorization": "Bearer wrong-token"})
        assert response.status_code == 401
        assert "Invalid bearer token" in response.json()["error"]

        # Test with valid token
        response = client.get("/test", headers={"Authorization": "Bearer test-token"})
        assert response.status_code == 200
        assert response.json() == {"message": "success"}
