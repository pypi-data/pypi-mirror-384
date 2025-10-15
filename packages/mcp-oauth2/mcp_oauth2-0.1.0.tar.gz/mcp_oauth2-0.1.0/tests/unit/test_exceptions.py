"""Tests for custom exceptions."""

from mcp_oauth2.exceptions import (
    AuthenticationError,
    AuthorizationError,
    CacheError,
    ConfigurationError,
    JWKSError,
    MCPOAuth2Error,
    MiddlewareError,
    NetworkError,
    TokenValidationError,
)


class TestMCPOAuth2Error:
    """Test base MCPOAuth2Error class."""

    def test_mcp_oauth2_error_basic(self):
        """Test basic MCPOAuth2Error creation."""
        error = MCPOAuth2Error("Test error message")
        assert str(error) == "Test error message"
        assert error.message == "Test error message"
        assert error.details == {}
        assert error.field is None

    def test_mcp_oauth2_error_with_details(self):
        """Test MCPOAuth2Error with details."""
        details = {"field": "issuer", "code": "INVALID_URL"}
        error = MCPOAuth2Error("Test error message", details=details)
        assert str(error) == "Test error message"
        assert error.message == "Test error message"
        assert error.details == details
        assert error.field is None

    def test_mcp_oauth2_error_with_field(self):
        """Test MCPOAuth2Error with field."""
        error = MCPOAuth2Error("Test error message", field="issuer")
        assert str(error) == "Test error message"
        assert error.message == "Test error message"
        assert error.details == {"field": "issuer"}
        assert error.field == "issuer"

    def test_mcp_oauth2_error_with_all_params(self):
        """Test MCPOAuth2Error with all parameters."""
        details = {"code": "INVALID_URL"}
        error = MCPOAuth2Error("Test error message", details=details, field="issuer")
        assert str(error) == "Test error message"
        assert error.message == "Test error message"
        assert error.details == {"code": "INVALID_URL", "field": "issuer"}
        assert error.field == "issuer"

    def test_mcp_oauth2_error_repr(self):
        """Test MCPOAuth2Error representation."""
        error = MCPOAuth2Error("Test error message", field="issuer")
        repr_str = repr(error)
        assert "MCPOAuth2Error" in repr_str
        assert "Test error message" in repr_str
        assert "issuer" in repr_str


class TestConfigurationError:
    """Test ConfigurationError class."""

    def test_configuration_error_basic(self):
        """Test basic ConfigurationError creation."""
        error = ConfigurationError("Configuration error")
        assert str(error) == "Configuration error"
        assert isinstance(error, MCPOAuth2Error)

    def test_configuration_error_with_field(self):
        """Test ConfigurationError with field."""
        error = ConfigurationError("Invalid issuer URL", field="issuer")
        assert str(error) == "Invalid issuer URL"
        assert error.field == "issuer"

    def test_configuration_error_with_details(self):
        """Test ConfigurationError with details."""
        details = {"original_error": "Invalid URL format"}
        error = ConfigurationError("Configuration failed", details=details)
        assert str(error) == "Configuration failed"
        assert error.details == details


class TestTokenValidationError:
    """Test TokenValidationError class."""

    def test_token_validation_error_basic(self):
        """Test basic TokenValidationError creation."""
        error = TokenValidationError("Token validation failed")
        assert str(error) == "Token validation failed"
        assert isinstance(error, MCPOAuth2Error)

    def test_token_validation_error_with_details(self):
        """Test TokenValidationError with details."""
        details = {"token_type": "access_token", "claim": "sub"}
        error = TokenValidationError("Missing required claim", details=details)
        assert str(error) == "Missing required claim"
        assert error.details == details


class TestJWKSError:
    """Test JWKSError class."""

    def test_jwks_error_basic(self):
        """Test basic JWKSError creation."""
        error = JWKSError("JWKS fetch failed")
        assert str(error) == "JWKS fetch failed"
        assert isinstance(error, MCPOAuth2Error)

    def test_jwks_error_with_details(self):
        """Test JWKSError with details."""
        details = {
            "jwks_uri": "https://example.com/.well-known/jwks.json",
            "status_code": 404,
        }
        error = JWKSError("JWKS not found", details=details)
        assert str(error) == "JWKS not found"
        assert error.details == details


class TestAuthenticationError:
    """Test AuthenticationError class."""

    def test_authentication_error_basic(self):
        """Test basic AuthenticationError creation."""
        error = AuthenticationError("Authentication failed")
        assert str(error) == "Authentication failed"
        assert isinstance(error, MCPOAuth2Error)

    def test_authentication_error_with_details(self):
        """Test AuthenticationError with details."""
        details = {"reason": "invalid_token", "status_code": 401}
        error = AuthenticationError("Invalid token", details=details)
        assert str(error) == "Invalid token"
        assert error.details == details


class TestAuthorizationError:
    """Test AuthorizationError class."""

    def test_authorization_error_basic(self):
        """Test basic AuthorizationError creation."""
        error = AuthorizationError("Access denied")
        assert str(error) == "Access denied"
        assert isinstance(error, MCPOAuth2Error)

    def test_authorization_error_with_details(self):
        """Test AuthorizationError with details."""
        details = {"required_role": "admin", "user_role": "user"}
        error = AuthorizationError("Insufficient permissions", details=details)
        assert str(error) == "Insufficient permissions"
        assert error.details == details


class TestMiddlewareError:
    """Test MiddlewareError class."""

    def test_middleware_error_basic(self):
        """Test basic MiddlewareError creation."""
        error = MiddlewareError("Middleware error")
        assert str(error) == "Middleware error"
        assert isinstance(error, MCPOAuth2Error)

    def test_middleware_error_with_details(self):
        """Test MiddlewareError with details."""
        details = {"route": "/api/protected", "method": "POST"}
        error = MiddlewareError("Route protection failed", details=details)
        assert str(error) == "Route protection failed"
        assert error.details == details


class TestCacheError:
    """Test CacheError class."""

    def test_cache_error_basic(self):
        """Test basic CacheError creation."""
        error = CacheError("Cache error")
        assert str(error) == "Cache error"
        assert isinstance(error, MCPOAuth2Error)

    def test_cache_error_with_details(self):
        """Test CacheError with details."""
        details = {"cache_key": "jwks:https://example.com", "operation": "store"}
        error = CacheError("Cache store failed", details=details)
        assert str(error) == "Cache store failed"
        assert error.details == details


class TestNetworkError:
    """Test NetworkError class."""

    def test_network_error_basic(self):
        """Test basic NetworkError creation."""
        error = NetworkError("Network error")
        assert str(error) == "Network error"
        assert isinstance(error, MCPOAuth2Error)

    def test_network_error_with_details(self):
        """Test NetworkError with details."""
        details = {"url": "https://example.com/api", "status_code": 500, "timeout": 30}
        error = NetworkError("Request timeout", details=details)
        assert str(error) == "Request timeout"
        assert error.details == details


class TestErrorInheritance:
    """Test error class inheritance."""

    def test_all_errors_inherit_from_mcp_oauth2_error(self):
        """Test that all custom errors inherit from MCPOAuth2Error."""
        errors = [
            ConfigurationError("test"),
            TokenValidationError("test"),
            JWKSError("test"),
            AuthenticationError("test"),
            AuthorizationError("test"),
            MiddlewareError("test"),
            CacheError("test"),
            NetworkError("test"),
        ]

        for error in errors:
            assert isinstance(error, MCPOAuth2Error)

    def test_error_message_consistency(self):
        """Test that error messages are consistent."""
        message = "Test error message"
        errors = [
            ConfigurationError(message),
            TokenValidationError(message),
            JWKSError(message),
            AuthenticationError(message),
            AuthorizationError(message),
            MiddlewareError(message),
            CacheError(message),
            NetworkError(message),
        ]

        for error in errors:
            assert str(error) == message
            assert error.message == message


class TestErrorDetails:
    """Test error details handling."""

    def test_error_details_preservation(self):
        """Test that error details are preserved correctly."""
        details = {
            "field": "issuer",
            "code": "INVALID_URL",
            "original_error": "Invalid URL format",
        }

        error = ConfigurationError("Configuration failed", details=details)
        assert error.details == details
        assert error.details["field"] == "issuer"
        assert error.details["code"] == "INVALID_URL"
        assert error.details["original_error"] == "Invalid URL format"

    def test_error_field_preservation(self):
        """Test that error field is preserved correctly."""
        error = ConfigurationError("Invalid value", field="issuer")
        assert error.field == "issuer"

    def test_error_combined_params(self):
        """Test error with both field and details."""
        details = {"code": "INVALID_URL"}
        error = ConfigurationError(
            "Invalid issuer URL", field="issuer", details=details
        )
        assert error.field == "issuer"
        assert error.details == details
        assert error.details["code"] == "INVALID_URL"


class TestErrorRepr:
    """Test error representation."""

    def test_error_repr_includes_class_name(self):
        """Test that error repr includes class name."""
        error = ConfigurationError("Test message")
        repr_str = repr(error)
        assert "ConfigurationError" in repr_str

    def test_error_repr_includes_message(self):
        """Test that error repr includes message."""
        message = "Test error message"
        error = TokenValidationError(message)
        repr_str = repr(error)
        assert message in repr_str

    def test_error_repr_includes_field(self):
        """Test that error repr includes field when present."""
        error = ConfigurationError("Test message", field="issuer")
        repr_str = repr(error)
        assert "issuer" in repr_str

    def test_error_repr_includes_details(self):
        """Test that error repr includes details when present."""
        details = {"code": "INVALID_URL"}
        error = ConfigurationError("Test message", details=details)
        repr_str = repr(error)
        assert "INVALID_URL" in repr_str
