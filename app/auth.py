"""
Authentication middleware for FastMCP server with bearer token validation.
"""

import secrets
from collections.abc import Awaitable, Callable

from fastapi import Request, status
from fastapi.responses import JSONResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


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
