"""Tests for middleware functionality."""

from unittest.mock import AsyncMock, Mock, patch

from fastapi import FastAPI, Request

from mcp_oauth2.exceptions import AuthenticationError, TokenValidationError
from mcp_oauth2.middleware import OAuth2Middleware
from mcp_oauth2.models import OAuth2Config


class TestOAuth2Middleware:
    """Test OAuth2 middleware functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = OAuth2Config(
            issuer="https://test-provider.com",
            audience="https://test-server.com",
            client_id="test-client-id",
            exempt_routes=["/health"],
        )

        self.app = FastAPI()
        self.middleware = OAuth2Middleware(self.app, self.config)

        @self.app.get("/protected")
        async def protected_route(request: Request):
            return {"message": "protected"}

        @self.app.get("/health")
        async def health_route():
            return {"status": "ok"}

        self.app.add_middleware(OAuth2Middleware, config=self.config)

    def test_middleware_initialization(self):
        """Test middleware initialization."""
        middleware = OAuth2Middleware(self.app, self.config)
        assert middleware.config == self.config
        assert middleware.jwks_cache == {}
        assert middleware.cache_stats == {"hits": 0, "misses": 0, "errors": 0}

    def test_middleware_with_valid_config(self):
        """Test middleware with valid configuration."""
        middleware = OAuth2Middleware(self.app, self.config)
        assert middleware.config.issuer == "https://test-provider.com"
        assert middleware.config.audience == "https://test-server.com"
        assert middleware.config.client_id == "test-client-id"

    @patch("mcp_oauth2.token_validation.validate_access_token")
    async def test_middleware_call_with_valid_token(self, mock_validate):
        """Test middleware call with valid token."""
        # Mock successful token validation
        mock_user = Mock()
        mock_user.sub = "user123"
        mock_validate.return_value = mock_user

        request = Mock()
        request.url.path = "/protected"
        request.headers = {"Authorization": "Bearer valid-token"}
        request.scope = {"type": "http"}

        response = Mock()
        response.status_code = 200

        # Mock the next callable
        next_callable = AsyncMock(return_value=response)

        middleware = OAuth2Middleware(self.app, self.config)
        result = await middleware.dispatch(request, next_callable)

        assert result == response
        mock_validate.assert_called_once()

    @patch("mcp_oauth2.token_validation.validate_access_token")
    async def test_middleware_call_with_invalid_token(self, mock_validate):
        """Test middleware call with invalid token."""
        # Mock token validation failure
        mock_validate.side_effect = TokenValidationError("Invalid token")

        request = Mock()
        request.url.path = "/protected"
        request.headers = {"authorization": "Bearer invalid-token"}
        request.scope = {"type": "http"}

        next_callable = AsyncMock()

        middleware = OAuth2Middleware(self.app, self.config)
        result = await middleware.dispatch(request, next_callable)

        assert result.status_code == 401
        next_callable.assert_not_called()

    @patch("mcp_oauth2.token_validation.validate_access_token")
    async def test_middleware_call_with_missing_token(self, mock_validate):
        """Test middleware call with missing token."""
        request = Mock()
        request.url.path = "/protected"
        request.headers = {}
        request.scope = {"type": "http"}

        next_callable = AsyncMock()

        middleware = OAuth2Middleware(self.app, self.config)
        result = await middleware.dispatch(request, next_callable)

        assert result.status_code == 401
        mock_validate.assert_not_called()
        next_callable.assert_not_called()

    async def test_middleware_call_exempt_route(self):
        """Test middleware call with exempt route."""
        request = Mock()
        request.url.path = "/health"
        request.headers = {}
        request.scope = {"type": "http"}

        response = Mock()
        response.status_code = 200
        next_callable = AsyncMock(return_value=response)

        middleware = OAuth2Middleware(self.app, self.config)
        result = await middleware.dispatch(request, next_callable)

        assert result == response
        next_callable.assert_called_once()

    @patch("mcp_oauth2.token_validation.validate_access_token")
    async def test_middleware_call_with_jwks_error(self, mock_validate):
        """Test middleware call with JWKS error."""
        from mcp_oauth2.exceptions import JWKSError

        mock_validate.side_effect = JWKSError("JWKS fetch failed")

        request = Mock()
        request.url.path = "/protected"
        request.headers = {"authorization": "Bearer token"}
        request.scope = {"type": "http"}

        next_callable = AsyncMock()

        middleware = OAuth2Middleware(self.app, self.config)
        result = await middleware.dispatch(request, next_callable)

        assert result.status_code == 401

    @patch("mcp_oauth2.token_validation.validate_access_token")
    async def test_middleware_call_with_authentication_error(self, mock_validate):
        """Test middleware call with authentication error."""
        mock_validate.side_effect = AuthenticationError("Authentication failed")

        request = Mock()
        request.url.path = "/protected"
        request.headers = {"authorization": "Bearer token"}
        request.scope = {"type": "http"}

        next_callable = AsyncMock()

        middleware = OAuth2Middleware(self.app, self.config)
        result = await middleware.dispatch(request, next_callable)

        assert result.status_code == 401

    @patch("mcp_oauth2.token_validation.validate_access_token")
    async def test_middleware_call_with_unexpected_error(self, mock_validate):
        """Test middleware call with unexpected error."""
        mock_validate.side_effect = Exception("Unexpected error")

        request = Mock()
        request.url.path = "/protected"
        request.headers = {"authorization": "Bearer token"}
        request.scope = {"type": "http"}

        next_callable = AsyncMock()

        middleware = OAuth2Middleware(self.app, self.config)
        result = await middleware.dispatch(request, next_callable)

        assert result.status_code == 401

    def test_middleware_cache_initialization(self):
        """Test middleware cache initialization."""
        middleware = OAuth2Middleware(self.app, self.config)
        assert middleware.jwks_cache == {}
        assert middleware.cache_stats == {"hits": 0, "misses": 0, "errors": 0}

    def test_middleware_cache_stats_tracking(self):
        """Test middleware cache stats tracking."""
        middleware = OAuth2Middleware(self.app, self.config)

        # Initial stats
        assert middleware.cache_stats["hits"] == 0
        assert middleware.cache_stats["misses"] == 0
        assert middleware.cache_stats["errors"] == 0

        # Simulate cache operations
        middleware.cache_stats["hits"] += 1
        middleware.cache_stats["misses"] += 1
        middleware.cache_stats["errors"] += 1

        assert middleware.cache_stats["hits"] == 1
        assert middleware.cache_stats["misses"] == 1
        assert middleware.cache_stats["errors"] == 1

    async def test_middleware_non_http_request(self):
        """Test middleware with non-HTTP request."""
        request = Mock()
        request.scope = {"type": "websocket"}  # Non-HTTP request

        response = Mock()
        next_callable = AsyncMock(return_value=response)

        middleware = OAuth2Middleware(self.app, self.config)
        result = await middleware.dispatch(request, next_callable)

        # Should pass through without authentication
        assert result == response
        next_callable.assert_called_once()

    def test_middleware_exempt_routes_configuration(self):
        """Test middleware with configured exempt routes."""
        config_with_exempt = OAuth2Config(
            issuer="https://test-provider.com",
            audience="https://test-server.com",
            client_id="test-client-id",
            exempt_routes=["/health", "/status", "/metrics"],
        )

        middleware = OAuth2Middleware(self.app, config_with_exempt)
        assert middleware.config.exempt_routes == ["/health", "/status", "/metrics"]

    @patch("mcp_oauth2.token_validation.validate_access_token")
    async def test_middleware_user_context_injection(self, mock_validate):
        """Test middleware user context injection."""
        mock_user = Mock()
        mock_user.sub = "user123"
        mock_user.email = "user@example.com"
        mock_validate.return_value = mock_user

        request = Mock()
        request.url.path = "/protected"
        request.headers = {"Authorization": "Bearer valid-token"}
        request.scope = {"type": "http"}

        response = Mock()
        response.status_code = 200
        next_callable = AsyncMock(return_value=response)

        middleware = OAuth2Middleware(self.app, self.config)
        result = await middleware.dispatch(request, next_callable)

        # Verify user context was injected
        assert hasattr(request.state, "authenticated_user")
        assert request.state.authenticated_user == mock_user
        assert result == response

    async def test_middleware_error_response_format(self):
        """Test middleware error response format."""
        request = Mock()
        request.url.path = "/protected"
        request.headers = {}
        request.scope = {"type": "http"}

        next_callable = AsyncMock()

        middleware = OAuth2Middleware(self.app, self.config)
        result = await middleware.dispatch(request, next_callable)

        assert result.status_code == 401
        # Verify response is JSON
        import json

        response_data = json.loads(result.body.decode())
        assert "error" in response_data
        assert "message" in response_data
        assert "timestamp" in response_data

    @patch("mcp_oauth2.token_validation.validate_access_token")
    async def test_middleware_token_validation_called_once(self, mock_validate):
        """Test that token validation is called exactly once per request."""
        mock_user = Mock()
        mock_user.sub = "user123"
        mock_validate.return_value = mock_user

        request = Mock()
        request.url.path = "/protected"
        request.headers = {"Authorization": "Bearer valid-token"}
        request.scope = {"type": "http"}

        response = Mock()
        response.status_code = 200
        next_callable = AsyncMock(return_value=response)

        middleware = OAuth2Middleware(self.app, self.config)
        await middleware.dispatch(request, next_callable)

        # Verify validate_access_token was called exactly once
        assert mock_validate.call_count == 1
        call_args = mock_validate.call_args
        assert call_args[0][0] == "valid-token"  # First positional argument
        assert call_args[0][1] == self.config  # Second positional argument
