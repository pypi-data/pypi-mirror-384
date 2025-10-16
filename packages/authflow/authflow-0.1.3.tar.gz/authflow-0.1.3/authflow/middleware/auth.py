"""Authentication and CORS middleware."""

import logging
from typing import Callable, Optional, List

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware as StarlettesCORSMiddleware

from authflow.core.jwt_handler import JWTHandler
from authflow.core.exceptions import InvalidTokenError

logger = logging.getLogger(__name__)


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware for JWT authentication.

    This middleware:
    - Extracts JWT tokens from Authorization header
    - Validates tokens and adds user info to request state
    - Allows public routes to bypass authentication
    - Handles token errors gracefully
    """

    def __init__(
        self,
        app,
        jwt_handler: JWTHandler,
        public_routes: Optional[List[str]] = None,
        exclude_prefixes: Optional[List[str]] = None,
    ):
        """Initialize authentication middleware.

        Args:
            app: FastAPI application
            jwt_handler: JWT handler for token validation
            public_routes: List of routes that don't require authentication
            exclude_prefixes: List of path prefixes to exclude from authentication
        """
        super().__init__(app)
        self.jwt_handler = jwt_handler
        self.public_routes = public_routes or [
            "/auth/login",
            "/auth/register",
            "/auth/forgot-password",
            "/auth/reset-password",
            "/docs",
            "/openapi.json",
            "/redoc",
            "/health",
        ]
        self.exclude_prefixes = exclude_prefixes or ["/static", "/public"]

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """Process request and validate authentication.

        Args:
            request: Incoming request
            call_next: Next middleware/handler

        Returns:
            Response from next handler
        """
        # Check if route is public or excluded
        if self._is_public_route(request.url.path):
            return await call_next(request)

        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            # No token provided - continue but don't set user
            # Some endpoints may allow optional authentication
            return await call_next(request)

        try:
            # Parse Bearer token
            if not auth_header.startswith("Bearer "):
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Invalid authentication scheme"},
                )

            token = auth_header[7:]  # Remove "Bearer " prefix

            # Validate and decode token
            token_data = self.jwt_handler.decode_token(token)

            # Add user info to request state
            request.state.user_id = token_data.get("sub")
            request.state.username = token_data.get("preferred_username")
            request.state.email = token_data.get("email")
            request.state.roles = self.jwt_handler.get_roles(token)
            request.state.permissions = self.jwt_handler.get_permissions(token)
            request.state.token_data = token_data
            request.state.authenticated = True

            logger.debug(
                f"Authenticated user: {request.state.username} "
                f"with roles: {request.state.roles}"
            )

        except InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or expired token"},
            )
        except Exception as e:
            logger.error(f"Error processing authentication: {e}")
            return JSONResponse(
                status_code=500,
                content={"detail": "Authentication processing error"},
            )

        return await call_next(request)

    def _is_public_route(self, path: str) -> bool:
        """Check if route is public or excluded.

        Args:
            path: Request path

        Returns:
            True if route is public
        """
        # Check exact match
        if path in self.public_routes:
            return True

        # Check prefix match
        for prefix in self.exclude_prefixes:
            if path.startswith(prefix):
                return True

        return False


class CORSMiddleware:
    """CORS middleware wrapper for easy configuration."""

    @staticmethod
    def create(
        allow_origins: Optional[List[str]] = None,
        allow_credentials: bool = True,
        allow_methods: Optional[List[str]] = None,
        allow_headers: Optional[List[str]] = None,
        expose_headers: Optional[List[str]] = None,
        max_age: int = 600,
    ) -> dict:
        """Create CORS middleware configuration with sensible defaults.

        Args:
            allow_origins: List of allowed origins (default: localhost)
            allow_credentials: Allow credentials
            allow_methods: Allowed HTTP methods (default: all)
            allow_headers: Allowed headers (default: common headers)
            expose_headers: Headers to expose
            max_age: Preflight cache max age

        Returns:
            Dictionary of CORS middleware parameters
        """
        # Default allowed origins for development
        if allow_origins is None:
            allow_origins = [
                "http://localhost:3000",
                "http://localhost:3001",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:3001",
            ]

        # Default allowed methods
        if allow_methods is None:
            allow_methods = ["*"]  # Allow all methods

        # Default allowed headers
        if allow_headers is None:
            allow_headers = [
                "Accept",
                "Accept-Language",
                "Content-Type",
                "Authorization",
                "X-Requested-With",
                "X-Request-ID",
            ]

        # Default exposed headers
        if expose_headers is None:
            expose_headers = ["X-Total-Count", "X-Page", "X-Page-Size"]

        return {
            "allow_origins": allow_origins,
            "allow_credentials": allow_credentials,
            "allow_methods": allow_methods,
            "allow_headers": allow_headers,
            "expose_headers": expose_headers,
            "max_age": max_age,
        }


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware (placeholder for future implementation).

    This can be implemented with Redis-based rate limiting using:
    - Token bucket algorithm
    - Sliding window algorithm
    - Fixed window algorithm
    """

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """Process request with rate limiting.

        Args:
            request: Incoming request
            call_next: Next middleware/handler

        Returns:
            Response from next handler
        """
        # TODO: Implement rate limiting
        # For now, just pass through
        return await call_next(request)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging requests and responses."""

    def __init__(
        self,
        app,
        log_request_body: bool = False,
        log_response_body: bool = False,
    ):
        """Initialize request logging middleware.

        Args:
            app: FastAPI application
            log_request_body: Whether to log request bodies
            log_response_body: Whether to log response bodies
        """
        super().__init__(app)
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """Process and log request/response.

        Args:
            request: Incoming request
            call_next: Next middleware/handler

        Returns:
            Response from next handler
        """
        import time

        # Log request
        start_time = time.time()
        user_id = getattr(request.state, "user_id", "anonymous")

        logger.info(
            f"Request: {request.method} {request.url.path} "
            f"by user: {user_id}"
        )

        # Process request
        response = await call_next(request)

        # Log response
        process_time = time.time() - start_time
        logger.info(
            f"Response: {request.method} {request.url.path} "
            f"status: {response.status_code} "
            f"time: {process_time:.3f}s"
        )

        # Add custom header
        response.headers["X-Process-Time"] = str(process_time)

        return response
