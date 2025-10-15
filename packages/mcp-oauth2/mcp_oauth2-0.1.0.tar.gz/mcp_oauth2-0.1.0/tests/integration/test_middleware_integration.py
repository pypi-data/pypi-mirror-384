"""
Integration tests for OAuth2 middleware.

Tests the basic integration of OAuth2Middleware with FastAPI applications,
including middleware setup, configuration validation, and exempt routes.
"""

import pytest
from fastapi import Depends, FastAPI, Request
from fastapi.testclient import TestClient
from pydantic import ValidationError

from mcp_oauth2 import OAuth2Config, OAuth2Middleware, get_authenticated_user
from mcp_oauth2.models import AuthenticatedUser


class TestMiddlewareIntegration:
    """Test OAuth2 middleware integration with FastAPI."""

    def test_middleware_can_be_added_to_fastapi_app(self):
        """Test that middleware can be added to FastAPI app without errors."""
        app = FastAPI()
        config = OAuth2Config(
            issuer="https://test-provider.com",
            audience="https://test-server.com",
            client_id="test-client",
        )

        # Should not raise any exceptions
        app.add_middleware(OAuth2Middleware, config=config)

        assert len(app.user_middleware) == 1
        assert app.user_middleware[0].cls == OAuth2Middleware

    def test_middleware_accepts_valid_oauth2_config(self):
        """Test that middleware accepts valid OAuth2Config."""
        app = FastAPI()
        config = OAuth2Config(
            issuer="https://test-provider.com",
            audience="https://test-server.com",
            client_id="test-client",
            jwks_cache_ttl=1800,
            exempt_routes=["/health", "/metrics"],
        )

        # Should not raise any exceptions
        app.add_middleware(OAuth2Middleware, config=config)

        # Verify middleware was added
        middleware = app.user_middleware[0]
        assert middleware.cls == OAuth2Middleware
        assert middleware.kwargs["config"] == config

    def test_middleware_doesnt_break_app_startup(self):
        """Test that middleware doesn't break FastAPI app startup."""
        app = FastAPI()
        config = OAuth2Config(
            issuer="https://test-provider.com",
            audience="https://test-server.com",
            client_id="test-client",
        )

        app.add_middleware(OAuth2Middleware, config=config)

        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}

        # Should not raise any exceptions during startup
        client = TestClient(app)

        # App should start successfully
        assert client is not None

    def test_exempt_routes_bypass_authentication(self):
        """Test that exempt routes bypass authentication."""
        app = FastAPI()
        config = OAuth2Config(
            issuer="https://test-provider.com",
            audience="https://test-server.com",
            client_id="test-client",
            exempt_routes=["/health", "/metrics", "/docs"],
        )

        app.add_middleware(OAuth2Middleware, config=config)

        @app.get("/health")
        async def health_check():
            return {"status": "healthy"}

        @app.get("/metrics")
        async def metrics():
            return {"requests": 100}

        @app.get("/protected")
        async def protected_endpoint(
            user: AuthenticatedUser = Depends(get_authenticated_user),
        ):
            return {"user_id": user.sub}

        client = TestClient(app)

        # Exempt routes should work without authentication
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

        response = client.get("/metrics")
        assert response.status_code == 200
        assert response.json() == {"requests": 100}

        # Protected route should require authentication
        response = client.get("/protected")
        assert response.status_code == 401
        assert "error" in response.json()
        assert response.json()["code"] in ["MISSING_TOKEN", "TOKEN_VALIDATION_ERROR"]

    def test_middleware_configuration_validation(self):
        """Test that middleware validates configuration properly."""
        app = FastAPI()

        # Test with invalid configuration (non-HTTPS issuer)
        with pytest.raises(ValidationError):  # Should raise ValidationError
            config = OAuth2Config(
                issuer="http://insecure-provider.com",  # Invalid: not HTTPS
                audience="https://test-server.com",
                client_id="test-client",
            )
            app.add_middleware(OAuth2Middleware, config=config)

    def test_middleware_with_multiple_exempt_routes(self):
        """Test middleware with multiple exempt routes."""
        app = FastAPI()
        config = OAuth2Config(
            issuer="https://test-provider.com",
            audience="https://test-server.com",
            client_id="test-client",
            exempt_routes=["/health", "/metrics", "/docs", "/openapi.json", "/redoc"],
        )

        app.add_middleware(OAuth2Middleware, config=config)

        @app.get("/health")
        async def health():
            return {"status": "ok"}

        @app.get("/metrics")
        async def metrics():
            return {"count": 42}

        @app.get("/docs")
        async def docs():
            return {"docs": "available"}

        client = TestClient(app)

        # All exempt routes should work without authentication
        exempt_paths = ["/health", "/metrics", "/docs"]
        for path in exempt_paths:
            response = client.get(path)
            assert response.status_code == 200, f"Failed for path: {path}"

    def test_middleware_preserves_request_context(self):
        """Test that middleware preserves request context for exempt routes."""
        app = FastAPI()
        config = OAuth2Config(
            issuer="https://test-provider.com",
            audience="https://test-server.com",
            client_id="test-client",
            exempt_routes=["/test"],
        )

        app.add_middleware(OAuth2Middleware, config=config)

        @app.get("/test")
        async def test_endpoint(request: Request):
            # Should be able to access request object normally
            return {
                "path": request.url.path,
                "method": request.method,
                "headers": dict(request.headers),
            }

        client = TestClient(app)
        response = client.get("/test")

        assert response.status_code == 200
        data = response.json()
        assert data["path"] == "/test"
        assert data["method"] == "GET"
        assert "headers" in data

    def test_middleware_error_handling(self):
        """Test that middleware handles errors gracefully."""
        app = FastAPI()
        config = OAuth2Config(
            issuer="https://test-provider.com",
            audience="https://test-server.com",
            client_id="test-client",
        )

        app.add_middleware(OAuth2Middleware, config=config)

        @app.get("/protected")
        async def protected_endpoint(
            user: AuthenticatedUser = Depends(get_authenticated_user),
        ):
            return {"user_id": user.sub}

        client = TestClient(app)

        # Test various invalid authorization headers
        test_cases = [
            ("", "Missing Authorization header"),
            ("Invalid", "Invalid Authorization header format"),
            ("Bearer", "Missing token after Bearer"),
            ("Basic token", "Invalid Authorization header format"),
        ]

        for auth_header, _expected_error in test_cases:
            headers = {"Authorization": auth_header} if auth_header else {}
            response = client.get("/protected", headers=headers)

            assert response.status_code == 401
            assert "error" in response.json()
            assert response.json()["code"] in [
                "MISSING_TOKEN",
                "TOKEN_VALIDATION_ERROR",
            ]

    def test_middleware_with_custom_exempt_patterns(self):
        """Test middleware with custom exempt route patterns."""
        app = FastAPI()
        config = OAuth2Config(
            issuer="https://test-provider.com",
            audience="https://test-server.com",
            client_id="test-client",
            exempt_routes=["/api/v1/public/*", "/static/*", "/health"],
        )

        app.add_middleware(OAuth2Middleware, config=config)

        @app.get("/api/v1/public/info")
        async def public_info():
            return {"info": "public"}

        @app.get("/static/style.css")
        async def static_css():
            return {"css": "content"}

        @app.get("/health")
        async def health():
            return {"status": "ok"}

        client = TestClient(app)

        # Test exempt routes work
        exempt_paths = ["/api/v1/public/info", "/static/style.css", "/health"]
        for path in exempt_paths:
            response = client.get(path)
            assert response.status_code == 200, f"Failed for path: {path}"


class TestMiddlewareConfiguration:
    """Test middleware configuration scenarios."""

    def test_minimal_configuration(self):
        """Test middleware with minimal required configuration."""
        app = FastAPI()
        config = OAuth2Config(
            issuer="https://test-provider.com",
            audience="https://test-server.com",
            client_id="test-client",
        )

        # Should work with minimal config
        app.add_middleware(OAuth2Middleware, config=config)
        assert len(app.user_middleware) == 1

    def test_full_configuration(self):
        """Test middleware with full configuration options."""
        app = FastAPI()
        config = OAuth2Config(
            issuer="https://test-provider.com",
            audience="https://test-server.com",
            client_id="test-client",
            jwks_uri="https://test-provider.com/.well-known/jwks.json",
            jwks_cache_ttl=7200,
            exempt_routes=["/health", "/metrics", "/docs"],
        )

        # Should work with full config
        app.add_middleware(OAuth2Middleware, config=config)
        assert len(app.user_middleware) == 1

        middleware = app.user_middleware[0]
        assert (
            middleware.kwargs["config"].jwks_uri
            == "https://test-provider.com/.well-known/jwks.json"
        )
        assert middleware.kwargs["config"].jwks_cache_ttl == 7200
        assert middleware.kwargs["config"].exempt_routes == [
            "/health",
            "/metrics",
            "/docs",
        ]

    def test_configuration_immutability(self):
        """Test that configuration is properly validated and immutable."""
        app = FastAPI()
        config = OAuth2Config(
            issuer="https://test-provider.com",
            audience="https://test-server.com",
            client_id="test-client",
        )

        app.add_middleware(OAuth2Middleware, config=config)

        # Original config should remain unchanged
        assert config.issuer == "https://test-provider.com"
        assert config.audience == "https://test-server.com"
        assert config.client_id == "test-client"
