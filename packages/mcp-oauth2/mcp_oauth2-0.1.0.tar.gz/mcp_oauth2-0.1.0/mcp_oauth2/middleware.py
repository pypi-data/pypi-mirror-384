"""
OAuth2 middleware for FastAPI applications.

This module provides the OAuth2Middleware class for integrating OAuth2 authentication
into FastAPI applications with minimal configuration.
"""

import logging
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from .exceptions import ConfigurationError, MCPOAuth2Error, TokenValidationError
from .models import AuthenticatedUser, OAuth2Config
from .utils import extract_bearer_token, is_exempt_route

logger = logging.getLogger(__name__)


class OAuth2Middleware(BaseHTTPMiddleware):
    """
    OAuth2 middleware for FastAPI applications.

    This middleware automatically validates JWT tokens from the Authorization header
    and injects authenticated user context into protected endpoints.

    Example:
        ```python
        from fastapi import FastAPI
        from mcp_oauth2 import OAuth2Middleware, OAuth2Config

        app = FastAPI()
        config = OAuth2Config(
            issuer="https://auth.example.com",
            audience="https://mcp-server.example.com",
            client_id="mcp-server-client"
        )
        app.add_middleware(OAuth2Middleware, config=config)
        ```
    """

    def __init__(
        self,
        app: ASGIApp,
        config: OAuth2Config,
    ):
        """
        Initialize OAuth2 middleware.

        Args:
            app: FastAPI application instance
            config: OAuth2 configuration
        """
        super().__init__(app)
        self.config = config
        self.jwks_cache: dict[str, Any] = {}
        self.cache_stats = {"hits": 0, "misses": 0, "errors": 0}
        self._validate_config()

    def _validate_config(self) -> None:
        """Validate OAuth2 configuration."""
        try:
            # Validate configuration using Pydantic
            self.config = OAuth2Config.model_validate(self.config.model_dump())
            logger.info("OAuth2 configuration validated successfully")
        except Exception as e:
            logger.error(f"Invalid OAuth2 configuration: {e}")
            raise ConfigurationError(
                f"Invalid OAuth2 configuration: {e}", field="config"
            ) from e

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Any]]
    ) -> Any:
        """
        Process incoming requests with OAuth2 authentication.

        Args:
            request: FastAPI request object
            call_next: Next middleware/handler in chain

        Returns:
            Response with authentication applied
        """
        try:
            # Check if request is HTTP (skip authentication for non-HTTP requests)
            if request.scope.get("type") != "http":
                logger.debug(
                    f"Non-HTTP request type {request.scope.get('type')}, bypassing authentication"
                )
                return await call_next(request)

            # Check if route is exempt from authentication
            if self.is_exempt_route(request.url.path):
                logger.debug(f"Route {request.url.path} is exempt from authentication")
                return await call_next(request)

            # Extract and validate Bearer token
            token = self._extract_token(request)
            if not token:
                return self._create_unauthorized_response(
                    "Missing or invalid Authorization header", "MISSING_TOKEN"
                )

            # Validate token and get user context
            user = await self._validate_token(token)

            # Inject user context into request state
            request.state.authenticated_user = user

            logger.debug(f"Authenticated user {user.sub} for route {request.url.path}")

            # Continue to next middleware/handler
            return await call_next(request)

        except TokenValidationError as e:
            logger.warning(f"Token validation failed: {e}")
            return self._create_unauthorized_response(
                f"Token validation failed: {e.message}",
                e.error_code or "TOKEN_VALIDATION_ERROR",
            )
        except MCPOAuth2Error as e:
            logger.error(f"OAuth2 error: {e}")
            return self._create_unauthorized_response(
                f"Authentication failed: {e.message}",
                e.error_code or "AUTHENTICATION_ERROR",
            )
        except Exception as e:
            logger.error(f"Unexpected error in OAuth2 middleware: {e}")
            return self._create_internal_error_response(
                "Internal authentication error", "INTERNAL_ERROR"
            )

    def _extract_token(self, request: Request) -> str | None:
        """
        Extract Bearer token from Authorization header.

        Args:
            request: FastAPI request object

        Returns:
            JWT token string or None if not found/invalid
        """
        authorization = request.headers.get("Authorization")
        if not authorization:
            return None

        try:
            return extract_bearer_token(authorization)
        except TokenValidationError:
            return None

    async def _validate_token(self, token: str) -> AuthenticatedUser:
        """
        Validate JWT token and return authenticated user.

        Args:
            token: JWT token string

        Returns:
            AuthenticatedUser object

        Raises:
            TokenValidationError: If token validation fails
        """
        from .token_validation import validate_access_token

        return await validate_access_token(token, self.config)

    def is_exempt_route(self, path: str) -> bool:
        """
        Check if a route is exempt from authentication.

        Args:
            path: Request path

        Returns:
            True if route is exempt, False otherwise
        """
        return is_exempt_route(path, self.config.exempt_routes)

    def _create_unauthorized_response(
        self, message: str, error_code: str, details: str | None = None
    ) -> JSONResponse:
        """
        Create standardized unauthorized response.

        Args:
            message: Error message
            error_code: Error code
            details: Additional error details

        Returns:
            JSONResponse with 401 status
        """
        content = {
            "error": message,
            "message": message,  # Add message field for test compatibility
            "code": error_code,
            "timestamp": datetime.now(UTC).isoformat(),
        }

        if details:
            content["details"] = details

        return JSONResponse(
            status_code=401,
            content=content,
            headers={
                "WWW-Authenticate": 'Bearer realm="mcp-server", error="invalid_token"'
            },
        )

    def _create_internal_error_response(
        self, message: str, error_code: str, details: str | None = None
    ) -> JSONResponse:
        """
        Create standardized internal error response.

        Args:
            message: Error message
            error_code: Error code
            details: Additional error details

        Returns:
            JSONResponse with 500 status
        """
        content = {
            "error": message,
            "message": message,
            "code": error_code,
            "timestamp": datetime.now(UTC).isoformat(),
        }

        if details:
            content["details"] = details

        return JSONResponse(
            status_code=500,
            content=content,
        )


def get_authenticated_user(request: Request) -> AuthenticatedUser:
    """
    FastAPI dependency to get authenticated user from request state.

    This dependency can be used in FastAPI endpoints to automatically
    inject the authenticated user context.

    Example:
        ```python
        @app.post("/mcp/tools/call")
        async def call_tool(
            request: ToolCallRequest,
            user: AuthenticatedUser = Depends(get_authenticated_user)
        ):
            # user is automatically injected after token validation
            return await handle_tool_call(request, user.sub)
        ```

    Args:
        request: FastAPI request object

    Returns:
        AuthenticatedUser object

    Raises:
        HTTPException: If user is not authenticated
    """
    user = getattr(request.state, "authenticated_user", None)
    if not user:
        raise HTTPException(status_code=401, detail="User not authenticated")
    assert isinstance(user, AuthenticatedUser)
    return user
