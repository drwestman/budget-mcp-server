"""
Authentication middleware for FastMCP server with bearer token validation.
"""
from typing import Callable
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware



class BearerTokenMiddleware(BaseHTTPMiddleware):
    """Bearer token authentication middleware for FastMCP server."""
    
    def __init__(self, app, bearer_token: str):
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
    
    async def dispatch(self, request: Request, call_next):
        """
        Middleware function to validate bearer token from Authorization header.
        
        Args:
            request: FastAPI request object
            call_next: Next middleware/handler in the chain
            
        Returns:
            Response from next handler if authenticated, 401 error if not
        """
        # Get Authorization header
        auth_header = request.headers.get("Authorization")
        
        if not auth_header:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"error": "Missing Authorization header"}
            )
        
        # Check if it's a Bearer token
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"error": "Invalid Authorization header format. Expected: Bearer <token>"}
            )
        
        # Extract token
        try:
            token = auth_header.split(" ", 1)[1]
        except IndexError:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"error": "Missing bearer token"}
            )
        
        # Validate token
        if token != self.bearer_token:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,  
                content={"error": "Invalid bearer token"}
            )
        
        # Token is valid, proceed to next handler
        response = await call_next(request)
        return response


def create_auth_middleware(bearer_token: str):
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
    def middleware_factory(app):
        return BearerTokenMiddleware(app, bearer_token)
    
    return middleware_factory