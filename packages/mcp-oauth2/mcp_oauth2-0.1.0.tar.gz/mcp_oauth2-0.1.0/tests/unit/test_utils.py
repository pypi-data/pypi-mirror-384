"""Tests for utility functions."""

import pytest

from mcp_oauth2.exceptions import ConfigurationError, TokenValidationError
from mcp_oauth2.utils import (
    extract_bearer_token,
    extract_user_claims,
    format_error_response,
    is_exempt_route,
    is_https_url,
    is_route_exempt,
    normalize_path,
    sanitize_for_logging,
    validate_issuer_audience,
    validate_jwt_format,
    validate_required_claims,
    validate_url,
)


class TestValidateURL:
    """Test URL validation."""

    def test_validate_url_valid_https(self):
        """Test validating a valid HTTPS URL."""
        url = "https://example.com/api/"
        result = validate_url(url)
        assert result == "https://example.com/api/"

    def test_validate_url_valid_http(self):
        """Test validating a valid HTTP URL."""
        url = "http://example.com/api/"
        result = validate_url(url, require_https=False)
        assert result == "http://example.com/api/"

    def test_validate_url_http_requires_https(self):
        """Test HTTP URL when HTTPS is required."""
        url = "http://example.com/api/"
        with pytest.raises(ConfigurationError) as exc_info:
            validate_url(url, require_https=True)
        assert "URL must use HTTPS" in str(exc_info.value)

    def test_validate_url_empty_string(self):
        """Test empty string URL."""
        with pytest.raises(ConfigurationError) as exc_info:
            validate_url("")
        assert "URL cannot be empty" in str(exc_info.value)

    def test_validate_url_none(self):
        """Test None URL."""
        with pytest.raises(ConfigurationError) as exc_info:
            validate_url(None)
        assert "URL cannot be empty" in str(exc_info.value)

    def test_validate_url_whitespace_only(self):
        """Test whitespace-only URL."""
        with pytest.raises(ConfigurationError) as exc_info:
            validate_url("   ")
        assert "URL cannot be empty" in str(exc_info.value)

    def test_validate_url_no_scheme(self):
        """Test URL without scheme."""
        with pytest.raises(ConfigurationError) as exc_info:
            validate_url("example.com/api")
        assert "URL must include scheme" in str(exc_info.value)

    def test_validate_url_no_hostname(self):
        """Test URL without hostname."""
        with pytest.raises(ConfigurationError) as exc_info:
            validate_url("https:///api")
        assert "URL must include hostname" in str(exc_info.value)

    def test_validate_url_invalid_format(self):
        """Test URL with invalid format."""
        with pytest.raises(ConfigurationError) as exc_info:
            validate_url("not-a-url")
        assert "URL must include scheme" in str(exc_info.value)


class TestValidateJWTFormat:
    """Test JWT format validation."""

    def test_validate_jwt_format_valid(self):
        """Test valid JWT format."""
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        # Should not raise an exception
        validate_jwt_format(token)

    def test_validate_jwt_format_invalid_empty(self):
        """Test empty JWT token."""
        with pytest.raises(TokenValidationError) as exc_info:
            validate_jwt_format("")
        assert "Token cannot be empty" in str(exc_info.value)

    def test_validate_jwt_format_invalid_none(self):
        """Test None JWT token."""
        with pytest.raises(TokenValidationError) as exc_info:
            validate_jwt_format(None)
        assert "Token cannot be empty" in str(exc_info.value)

    def test_validate_jwt_format_invalid_one_part(self):
        """Test JWT with only one part."""
        with pytest.raises(TokenValidationError) as exc_info:
            validate_jwt_format("invalid")
        assert "Invalid JWT format" in str(exc_info.value)

    def test_validate_jwt_format_invalid_two_parts(self):
        """Test JWT with only two parts."""
        with pytest.raises(TokenValidationError) as exc_info:
            validate_jwt_format("header.payload")
        assert "Invalid JWT format" in str(exc_info.value)

    def test_validate_jwt_format_invalid_four_parts(self):
        """Test JWT with four parts."""
        with pytest.raises(TokenValidationError) as exc_info:
            validate_jwt_format("header.payload.signature.extra")
        assert "Invalid JWT format" in str(exc_info.value)


class TestExtractBearerToken:
    """Test token extraction from Authorization header."""

    def test_extract_bearer_token_valid(self):
        """Test extracting token from Bearer authorization header."""
        header = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        result = extract_bearer_token(header)
        assert (
            result
            == "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        )

    def test_extract_bearer_token_case_insensitive(self):
        """Test extracting token with case-insensitive Bearer."""
        header = "bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        result = extract_bearer_token(header)
        assert (
            result
            == "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        )

    def test_extract_bearer_token_empty_header(self):
        """Test extracting token from empty header."""
        with pytest.raises(TokenValidationError) as exc_info:
            extract_bearer_token("")
        assert "Authorization header is missing" in str(exc_info.value)

    def test_extract_bearer_token_none_header(self):
        """Test extracting token from None header."""
        with pytest.raises(TokenValidationError) as exc_info:
            extract_bearer_token(None)
        assert "Authorization header is missing" in str(exc_info.value)

    def test_extract_bearer_token_invalid_format(self):
        """Test extracting token from invalid header format."""
        with pytest.raises(TokenValidationError) as exc_info:
            extract_bearer_token("Basic dXNlcjpwYXNz")
        assert "Authorization header must use Bearer scheme" in str(exc_info.value)

    def test_extract_bearer_token_missing_token(self):
        """Test extracting token when token is missing."""
        with pytest.raises(TokenValidationError) as exc_info:
            extract_bearer_token("Bearer")
        assert "Authorization header must use Bearer scheme" in str(exc_info.value)

    def test_extract_bearer_token_whitespace_only(self):
        """Test extracting token from whitespace-only header."""
        with pytest.raises(TokenValidationError) as exc_info:
            extract_bearer_token("   ")
        assert "Authorization header is missing" in str(exc_info.value)


class TestExtractUserClaims:
    """Test user claims parsing from JWT payload."""

    def test_extract_user_claims_complete(self):
        """Test parsing complete user claims."""
        payload = {
            "sub": "user123",
            "email": "user@example.com",
            "name": "John Doe",
            "preferred_username": "johndoe",
            "given_name": "John",
            "family_name": "Doe",
            "aud": "https://test-server.com",
            "iss": "https://test-provider.com",
            "exp": 1640995200,
            "iat": 1640908800,
        }

        result = extract_user_claims(payload)

        assert result["sub"] == "user123"
        assert result["email"] == "user@example.com"
        assert result["name"] == "John Doe"
        assert result["preferred_username"] == "johndoe"
        assert result["given_name"] == "John"
        assert result["family_name"] == "Doe"
        assert result["aud"] == "https://test-server.com"
        assert result["iss"] == "https://test-provider.com"
        assert result["exp"] == 1640995200
        assert result["iat"] == 1640908800

    def test_extract_user_claims_minimal(self):
        """Test parsing minimal user claims."""
        payload = {"sub": "user123"}

        result = extract_user_claims(payload)

        assert result["sub"] == "user123"
        assert result["email"] is None
        assert result["name"] is None
        assert result["preferred_username"] is None
        assert result["given_name"] is None
        assert result["family_name"] is None
        assert result["aud"] is None
        assert result["iss"] is None
        assert result["exp"] is None
        assert result["iat"] is None

    def test_extract_user_claims_empty_payload(self):
        """Test parsing empty payload."""
        payload = {}

        result = extract_user_claims(payload)

        assert result["sub"] is None
        assert result["email"] is None
        assert result["name"] is None
        assert result["preferred_username"] is None
        assert result["given_name"] is None
        assert result["family_name"] is None
        assert result["aud"] is None
        assert result["iss"] is None
        assert result["exp"] is None
        assert result["iat"] is None


class TestValidateIssuerAudience:
    """Test issuer and audience validation."""

    def test_validate_issuer_audience_valid(self):
        """Test valid issuer and audience."""
        claims = {
            "iss": "https://test-provider.com",
            "aud": "https://test-server.com",
        }

        # Should not raise an exception
        validate_issuer_audience(
            claims["iss"],
            claims["aud"],
            "https://test-provider.com",
            "https://test-server.com",
        )

    def test_validate_issuer_audience_wrong_issuer(self):
        """Test wrong issuer."""
        claims = {
            "iss": "https://wrong-provider.com",
            "aud": "https://test-server.com",
        }

        with pytest.raises(TokenValidationError) as exc_info:
            validate_issuer_audience(
                claims["iss"],
                claims["aud"],
                "https://test-provider.com",
                "https://test-server.com",
            )

        assert (
            "Token issuer 'https://wrong-provider.com' does not match configured issuer 'https://test-provider.com'"
            in str(exc_info.value)
        )

    def test_validate_issuer_audience_wrong_audience(self):
        """Test wrong audience."""
        claims = {
            "iss": "https://test-provider.com",
            "aud": "https://wrong-server.com",
        }

        with pytest.raises(TokenValidationError) as exc_info:
            validate_issuer_audience(
                claims["iss"],
                claims["aud"],
                "https://test-provider.com",
                "https://test-server.com",
            )

        assert (
            "Token audience 'https://wrong-server.com' does not match configured audience 'https://test-server.com'"
            in str(exc_info.value)
        )


class TestValidateRequiredClaims:
    """Test required claims validation."""

    def test_validate_required_claims_valid(self):
        """Test valid required claims."""
        claims = {"sub": "user123"}

        # Should not raise an exception
        validate_required_claims(claims)

    def test_validate_required_claims_missing_sub(self):
        """Test missing sub claim."""
        claims = {}

        with pytest.raises(TokenValidationError) as exc_info:
            validate_required_claims(claims)

        assert "Token is missing required claims: sub" in str(exc_info.value)

    def test_validate_required_claims_empty_sub(self):
        """Test empty sub claim."""
        claims = {"sub": ""}

        with pytest.raises(TokenValidationError) as exc_info:
            validate_required_claims(claims)

        assert "Token is missing required claims: sub" in str(exc_info.value)

    def test_validate_required_claims_none_sub(self):
        """Test None sub claim."""
        claims = {"sub": None}

        with pytest.raises(TokenValidationError) as exc_info:
            validate_required_claims(claims)

        assert "Token is missing required claims: sub" in str(exc_info.value)


class TestIsExemptRoute:
    """Test exempt route checking."""

    def test_is_exempt_route_exact_match(self):
        """Test exact route match."""
        exempt_routes = ["/health", "/status"]
        assert is_exempt_route("/health", exempt_routes) is True
        assert is_exempt_route("/status", exempt_routes) is True
        assert is_exempt_route("/api", exempt_routes) is False

    def test_is_exempt_route_wildcard_match(self):
        """Test wildcard route match."""
        exempt_routes = ["/health/*", "/api/public/*"]
        assert is_exempt_route("/health/check", exempt_routes) is True
        assert is_exempt_route("/api/public/data", exempt_routes) is True
        assert is_exempt_route("/api/private/data", exempt_routes) is False

    def test_is_exempt_route_empty_list(self):
        """Test with empty exempt routes list."""
        exempt_routes = []
        assert is_exempt_route("/any/path", exempt_routes) is False

    def test_is_route_exempt_function(self):
        """Test the is_route_exempt function."""
        exempt_routes = ["/health", "/status"]
        assert is_route_exempt("/health", exempt_routes) is True
        assert is_route_exempt("/status", exempt_routes) is True
        assert is_route_exempt("/api", exempt_routes) is False


class TestIsHTTPSURL:
    """Test HTTPS URL checking."""

    def test_is_https_url_valid_https(self):
        """Test valid HTTPS URL."""
        assert is_https_url("https://example.com") is True

    def test_is_https_url_valid_http(self):
        """Test HTTP URL."""
        assert is_https_url("http://example.com") is False

    def test_is_https_url_invalid_url(self):
        """Test invalid URL."""
        assert is_https_url("not-a-url") is False

    def test_is_https_url_empty_string(self):
        """Test empty string."""
        assert is_https_url("") is False


class TestNormalizePath:
    """Test path normalization."""

    def test_normalize_path_with_trailing_slash(self):
        """Test path with trailing slash."""
        assert normalize_path("/api/test/") == "/api/test"

    def test_normalize_path_without_trailing_slash(self):
        """Test path without trailing slash."""
        assert normalize_path("/api/test") == "/api/test"

    def test_normalize_path_root(self):
        """Test root path."""
        assert normalize_path("/") == "/"

    def test_normalize_path_empty(self):
        """Test empty path."""
        assert normalize_path("") == ""


class TestSanitizeForLogging:
    """Test data sanitization for logging."""

    def test_sanitize_string_short(self):
        """Test sanitizing short string."""
        data = "short string"
        result = sanitize_for_logging(data)
        assert result == "short string"

    def test_sanitize_string_long(self):
        """Test sanitizing long string."""
        data = "a" * 150
        result = sanitize_for_logging(data)
        assert len(result) == 100
        assert result.endswith("...")

    def test_sanitize_dict(self):
        """Test sanitizing dictionary."""
        data = {"key": "value", "password": "secret"}
        result = sanitize_for_logging(data)
        assert "password" not in result or "secret" not in result

    def test_sanitize_none(self):
        """Test sanitizing None."""
        result = sanitize_for_logging(None)
        assert result == "None"


class TestFormatErrorResponse:
    """Test error response formatting."""

    def test_format_error_response_basic(self):
        """Test basic error response formatting."""
        response = format_error_response("TEST_ERROR", "Test error message")

        assert response.status_code == 401
        assert response.headers["Content-Type"] == "application/json"

        import json

        data = json.loads(response.body.decode())
        assert data["error"] == "TEST_ERROR"
        assert data["message"] == "Test error message"
        assert "timestamp" in data

    def test_format_error_response_with_details(self):
        """Test error response with details."""
        details = {"field": "issuer", "code": "INVALID_URL"}
        response = format_error_response("TEST_ERROR", "Test error message", details)

        import json

        data = json.loads(response.body.decode())
        assert data["error"] == "TEST_ERROR"
        assert data["message"] == "Test error message"
        # Details are sanitized but preserved as dict for API responses
        assert data["details"] == {"field": "issuer", "code": "INVALID_URL"}

    def test_format_error_response_custom_status(self):
        """Test error response with custom status code."""
        response = format_error_response(
            "TEST_ERROR", "Test error message", status_code=400
        )

        assert response.status_code == 400
