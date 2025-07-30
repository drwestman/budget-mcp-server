"""
Authentication and initialization middleware for FastMCP server.
"""

import asyncio
import json
import logging
import os
import secrets
import time
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import Request, status
from fastapi.responses import JSONResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class BearerTokenMiddleware(BaseHTTPMiddleware):
    """Bearer token authentication middleware for FastMCP server."""

    def __init__(self, app: ASGIApp, bearer_token: str) -> None:
        """
        Initialize bearer token authentication middleware.

        Args:
            app: ASGI application
            bearer_token: The bearer token that must be provided for authentication
        """
        if not bearer_token:
            raise ValueError("Bearer token cannot be empty")
        super().__init__(app)
        self.bearer_token = bearer_token

    def _validate_auth_header(self, auth_header: str | None) -> JSONResponse | None:
        """Validate the Authorization header format. Returns error response or None."""
        if not auth_header:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"error": "Missing Authorization header"},
            )

        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": (
                        "Invalid Authorization header format. Expected: Bearer <token>"
                    )
                },
            )
        return None

    def _extract_token(self, auth_header: str) -> str | JSONResponse:
        """Extract token from Authorization header. Returns token or error response."""
        try:
            return auth_header.split(" ", 1)[1]
        except IndexError:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"error": "Missing bearer token"},
            )

    def _validate_token(self, token: str) -> JSONResponse | None:
        """
        Validate token using constant-time comparison.
        Returns error response or None.
        """
        if not secrets.compare_digest(token, self.bearer_token):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"error": "Invalid bearer token"},
            )
        return None

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> JSONResponse | Response:
        """
        Middleware function to validate bearer token from Authorization header.

        Args:
            request: FastAPI request object
            call_next: Next middleware/handler in the chain

        Returns:
            Response from next handler if authenticated, 401 error if not
        """
        auth_header = request.headers.get("Authorization")

        # Validate Authorization header format
        error_response = self._validate_auth_header(auth_header)
        if error_response:
            return error_response

        # Extract token from header
        assert auth_header is not None
        token_or_error = self._extract_token(auth_header)
        if isinstance(token_or_error, JSONResponse):
            return token_or_error

        # Validate token using constant-time comparison to prevent timing attacks
        error_response = self._validate_token(token_or_error)
        if error_response:
            return error_response

        # Token is valid, proceed to next handler
        response = await call_next(request)
        return response


def create_auth_middleware(
    bearer_token: str,
) -> Callable[[ASGIApp], BearerTokenMiddleware]:
    """
    Factory function to create bearer token authentication middleware class.

    Args:
        bearer_token: Required bearer token for authentication

    Returns:
        BearerTokenMiddleware class configured with the token

    Raises:
        ValueError: If bearer_token is empty or None
    """
    if not bearer_token:
        raise ValueError("Bearer token cannot be empty")

    # Return a middleware class factory
    def middleware_factory(app: ASGIApp) -> BearerTokenMiddleware:
        return BearerTokenMiddleware(app, bearer_token)

    return middleware_factory


class MCPInitializationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce MCP protocol initialization requirements.

    This middleware ensures that clients have properly completed the MCP
    initialization handshake before allowing access to tools and other
    MCP resources. It tracks session state and blocks tool requests
    from uninitialized sessions.
    """

    def __init__(self, app: ASGIApp) -> None:
        """
        Initialize MCP initialization middleware.

        Args:
            app: ASGI application
        """
        super().__init__(app)
        # Store initialized session state with TTL (session_id -> timestamp)
        self._initialized_sessions: dict[str, float] = {}

        # Configuration from environment variables with safe defaults
        self._session_ttl = self._get_env_int("MCP_SESSION_TTL", 3600)  # 1 hour
        self._cleanup_interval = self._get_env_int(
            "MCP_CLEANUP_INTERVAL", 300
        )  # 5 minutes

        # Background cleanup task
        self._cleanup_task: asyncio.Task[None] | None = None
        self._cleanup_started = False

    def __del__(self) -> None:
        """Ensure cleanup task is stopped when middleware is destroyed."""
        self._stop_cleanup_task()

    def _get_env_int(self, env_var: str, default: int) -> int:
        """
        Get integer value from environment variable with validation.

        Args:
            env_var: Environment variable name
            default: Default value if not set or invalid

        Returns:
            Integer value from environment or default
        """
        try:
            value = os.getenv(env_var)
            if value is None:
                return default
            parsed = int(value)
            return parsed if parsed > 0 else default
        except (ValueError, TypeError):
            logger.warning(f"Invalid value for {env_var}, using default {default}")
            return default

    def _get_session_id(self, request: Request) -> str:
        """
        Extract a session identifier from the request.

        For HTTP requests, we use the client IP and User-Agent as a simple
        session identifier. In production, this could be enhanced with
        proper session management.

        Args:
            request: The incoming request

        Returns:
            Session identifier string
        """
        client_ip = (
            getattr(request.client, "host", "unknown") if request.client else "unknown"
        )
        user_agent = request.headers.get("user-agent", "unknown")
        return f"{client_ip}:{user_agent}"

    def _add_initialized_session(self, session_id: str) -> None:
        """
        Add session with current timestamp for TTL tracking.

        Args:
            session_id: The session identifier to add
        """
        self._initialized_sessions[session_id] = time.time()

    def _cleanup_expired_sessions(self) -> int:
        """
        Remove expired sessions based on TTL.

        Returns:
            Number of sessions removed
        """
        current_time = time.time()
        expired_sessions = [
            session_id
            for session_id, timestamp in self._initialized_sessions.items()
            if current_time - timestamp > self._session_ttl
        ]

        for session_id in expired_sessions:
            del self._initialized_sessions[session_id]

        if expired_sessions:
            logger.debug(f"Cleaned up {len(expired_sessions)} expired sessions")

        return len(expired_sessions)

    def _start_cleanup_task(self) -> None:
        """Start the background cleanup task if in async context."""
        try:
            if not self._cleanup_started and (
                self._cleanup_task is None or self._cleanup_task.done()
            ):
                self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
                self._cleanup_started = True
        except RuntimeError:
            # No event loop running - will start later when needed
            pass

    def _stop_cleanup_task(self) -> None:
        """Stop the background cleanup task."""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()

    async def _periodic_cleanup(self) -> None:
        """Background task to periodically clean up expired sessions."""
        while True:
            try:
                await asyncio.sleep(self._cleanup_interval)
                self._cleanup_expired_sessions()
            except asyncio.CancelledError:
                logger.debug("Cleanup task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {e}")
                # Continue running despite errors

    def _is_mcp_protocol_request(self, request: Request) -> bool:
        """
        Check if this is an MCP protocol-level request that should be allowed
        before initialization is complete.

        Args:
            request: The incoming request

        Returns:
            True if this is a protocol request, False otherwise
        """
        # Allow MCP protocol requests (initialize, ping, etc.)
        # These typically come as JSON-RPC over HTTP POST
        if request.method != "POST":
            return False

        content_type = request.headers.get("content-type", "")
        if "application/json" not in content_type:
            return False

        # We can't easily inspect the body here without consuming it,
        # so we'll allow all JSON POST requests and check the body
        # in the request processing
        return True

    async def _check_request_body_for_protocol(
        self, request: Request
    ) -> tuple[bool, dict[str, Any] | None]:
        """
        Check if the request body contains MCP protocol messages.

        Args:
            request: The incoming request

        Returns:
            Tuple of (is_protocol_request, parsed_body)
        """
        try:
            # Read the body
            body = await request.body()
            if not body:
                return False, None

            # Parse JSON
            data = json.loads(body.decode())

            # Check for MCP protocol methods
            method = data.get("method", "")

            # Allow these MCP protocol methods before initialization
            allowed_methods = {
                "initialize",
                "notifications/initialized",
                "ping",
                "logs/setLevel",
            }

            return method in allowed_methods, data

        except (json.JSONDecodeError, UnicodeDecodeError, KeyError):
            return False, None

    def _handle_initialized_notification(
        self, session_id: str, data: dict[str, Any]
    ) -> None:
        """
        Handle the MCP initialized notification to mark session as ready.

        Args:
            session_id: The session identifier
            data: The parsed request data
        """
        if data.get("method") == "notifications/initialized":
            self._add_initialized_session(session_id)

    def _is_session_initialized(self, session_id: str) -> bool:
        """
        Check if a session has completed MCP initialization and is not expired.

        Args:
            session_id: The session identifier

        Returns:
            True if session is initialized and not expired, False otherwise
        """
        if session_id not in self._initialized_sessions:
            return False

        # Check if session has expired (lazy cleanup)
        current_time = time.time()
        session_time = self._initialized_sessions[session_id]

        if current_time - session_time > self._session_ttl:
            # Session expired, remove it
            del self._initialized_sessions[session_id]
            logger.debug(f"Session {session_id} expired and removed")
            return False

        return True

    def _create_initialization_error(self) -> JSONResponse:
        """
        Create an error response for uninitialized sessions.

        Returns:
            JSON error response
        """
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "MCP session not initialized",
                "message": (
                    "Client must complete MCP initialization handshake before "
                    "accessing tools. Send 'initialize' request followed by "
                    "'notifications/initialized' notification."
                ),
                "code": "mcp_not_initialized",
            },
        )

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Middleware function to check MCP initialization state.

        Args:
            request: FastAPI request object
            call_next: Next middleware/handler in the chain

        Returns:
            Response from next handler if initialized, error if not
        """
        # Start cleanup task if not already started
        self._start_cleanup_task()

        session_id = self._get_session_id(request)

        # Check if this might be an MCP protocol request
        if self._is_mcp_protocol_request(request):
            # Check the actual request body
            is_protocol, data = await self._check_request_body_for_protocol(request)

            if is_protocol and data:
                # Handle initialized notification
                self._handle_initialized_notification(session_id, data)

                # Allow protocol requests to proceed
                # Reconstruct request with proper body for downstream processing
                return await self._create_request_with_body(request, data, call_next)

        # For non-protocol requests, check if session is initialized
        if not self._is_session_initialized(session_id):
            return self._create_initialization_error()

        # Session is initialized, proceed normally
        response = await call_next(request)
        return response

    async def _create_request_with_body(
        self,
        request: Request,
        data: dict[str, Any],
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """
        Create a new request with reconstructed body for downstream processing.

        This method properly handles request body reconstruction without
        relying on internal Starlette APIs.

        Args:
            request: Original request object
            data: Parsed request body data
            call_next: Next middleware/handler in the chain

        Returns:
            Response from downstream handlers
        """
        # Check if we have a proper Starlette Request with scope
        if hasattr(request, "scope") and request.scope:
            # Serialize the data back to JSON bytes
            body_bytes = json.dumps(data).encode()

            # Create new ASGI receive callable that provides the reconstructed body
            async def receive() -> dict[str, Any]:
                return {
                    "type": "http.request",
                    "body": body_bytes,
                    "more_body": False,
                }

            # Create a new Request object with the reconstructed body
            # This uses the documented Starlette API
            new_request = Request(request.scope, receive)
            return await call_next(new_request)
        else:
            # For testing or other cases where scope is not available,
            # create a mock body method that returns the reconstructed data
            body_bytes = json.dumps(data).encode()

            async def mock_body() -> bytes:
                return body_bytes

            # Replace the body method with our reconstructed data
            setattr(request, "body", mock_body)
            return await call_next(request)


def create_mcp_initialization_middleware() -> (
    Callable[[ASGIApp], MCPInitializationMiddleware]
):
    """
    Factory function to create MCP initialization middleware.

    Returns:
        MCPInitializationMiddleware class factory

    Example:
        app.add_middleware(create_mcp_initialization_middleware())
    """

    def middleware_factory(app: ASGIApp) -> MCPInitializationMiddleware:
        return MCPInitializationMiddleware(app)

    return middleware_factory
