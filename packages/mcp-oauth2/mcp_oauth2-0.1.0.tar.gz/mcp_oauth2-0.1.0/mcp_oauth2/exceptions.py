"""Exception classes for OAuth2 MCP authorization library."""

from typing import Any


class MCPOAuth2Error(Exception):
    """Base exception for OAuth2 MCP errors."""

    def __init__(
        self,
        message: str,
        error_code: str | None = None,
        details: dict[str, Any] | None = None,
        field: str | None = None,
    ):
        """Initialize the exception.

        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            details: Additional error details for debugging
            field: Field that caused the error
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "MCP_OAUTH2_ERROR"
        self.details = details or {}
        self.field = field
        if field:
            self.details["field"] = field

    def __repr__(self) -> str:
        """Return string representation of the exception."""
        parts = [f"{self.__class__.__name__}('{self.message}'"]

        if self.field:
            parts.append(f"field='{self.field}'")

        if self.details:
            parts.append(f"details={self.details}")

        return ", ".join(parts) + ")"

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for API responses.

        Returns:
            Dictionary representation of the error
        """
        result: dict[str, Any] = {
            "error": self.message,
            "code": self.error_code,
        }
        if self.details:
            result["details"] = self.details
        return result


class TokenValidationError(MCPOAuth2Error):
    """Error during JWT token validation."""

    def __init__(
        self,
        message: str,
        token_issue: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        """Initialize token validation error.

        Args:
            message: Human-readable error message
            token_issue: Specific issue with the token (expired, invalid signature, etc.)
            details: Additional error details
        """
        super().__init__(message, "TOKEN_VALIDATION_ERROR", details)
        self.token_issue = token_issue
        if token_issue:
            self.details["token_issue"] = token_issue


class ConfigurationError(MCPOAuth2Error):
    """Error in configuration validation."""

    def __init__(
        self,
        message: str,
        field: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        """Initialize configuration error.

        Args:
            message: Human-readable error message
            field: Configuration field that caused the error
            details: Additional error details
        """
        super().__init__(message, "CONFIGURATION_ERROR", details)
        self.field = field
        if field:
            self.details["field"] = field


class JWKSError(MCPOAuth2Error):
    """Error during JWKS operations."""

    def __init__(
        self,
        message: str,
        jwks_uri: str | None = None,
        http_status: int | None = None,
        details: dict[str, Any] | None = None,
    ):
        """Initialize JWKS error.

        Args:
            message: Human-readable error message
            jwks_uri: JWKS URI that caused the error
            http_status: HTTP status code from JWKS fetch
            details: Additional error details
        """
        super().__init__(message, "JWKS_ERROR", details)
        self.jwks_uri = jwks_uri
        self.http_status = http_status

        if jwks_uri:
            self.details["jwks_uri"] = jwks_uri
        if http_status:
            self.details["http_status"] = http_status


class MiddlewareError(MCPOAuth2Error):
    """Error during middleware operations."""

    def __init__(
        self,
        message: str,
        route: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        """Initialize middleware error.

        Args:
            message: Human-readable error message
            route: Route that caused the error
            details: Additional error details
        """
        super().__init__(message, "MIDDLEWARE_ERROR", details)
        self.route = route
        if route:
            self.details["route"] = route


class AuthenticationError(MCPOAuth2Error):
    """Error during authentication process."""

    def __init__(
        self,
        message: str,
        auth_header: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        """Initialize authentication error.

        Args:
            message: Human-readable error message
            auth_header: Authorization header that caused the error (sanitized)
            details: Additional error details
        """
        super().__init__(message, "AUTHENTICATION_ERROR", details)
        self.auth_header = auth_header
        if auth_header:
            # Sanitize auth header for security
            sanitized = self._sanitize_auth_header(auth_header)
            self.details["auth_header"] = sanitized

    @staticmethod
    def _sanitize_auth_header(auth_header: str) -> str:
        """Sanitize authorization header for logging.

        Args:
            auth_header: Original authorization header

        Returns:
            Sanitized header with token redacted
        """
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]  # Remove "Bearer " prefix
            if len(token) > 10:
                # Show first 6 and last 4 characters
                return f"Bearer {token[:6]}...{token[-4:]}"
            else:
                return "Bearer [REDACTED]"
        return "[REDACTED]"


class AuthorizationError(MCPOAuth2Error):
    """Error during authorization process."""

    def __init__(
        self,
        message: str,
        required_scopes: list[str] | None = None,
        user_scopes: list[str] | None = None,
        details: dict[str, Any] | None = None,
    ):
        """Initialize authorization error.

        Args:
            message: Human-readable error message
            required_scopes: Scopes required for the operation
            user_scopes: Scopes available to the user
            details: Additional error details
        """
        super().__init__(message, "AUTHORIZATION_ERROR", details)
        self.required_scopes = required_scopes
        self.user_scopes = user_scopes

        if required_scopes:
            self.details["required_scopes"] = required_scopes
        if user_scopes:
            self.details["user_scopes"] = user_scopes


class CacheError(MCPOAuth2Error):
    """Error during cache operations."""

    def __init__(
        self,
        message: str,
        cache_key: str | None = None,
        operation: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        """Initialize cache error.

        Args:
            message: Human-readable error message
            cache_key: Cache key that caused the error
            operation: Cache operation that failed
            details: Additional error details
        """
        super().__init__(message, "CACHE_ERROR", details)
        self.cache_key = cache_key
        self.operation = operation

        if cache_key:
            self.details["cache_key"] = cache_key
        if operation:
            self.details["operation"] = operation


class NetworkError(MCPOAuth2Error):
    """Error during network operations."""

    def __init__(
        self,
        message: str,
        url: str | None = None,
        status_code: int | None = None,
        details: dict[str, Any] | None = None,
    ):
        """Initialize network error.

        Args:
            message: Human-readable error message
            url: URL that caused the error
            status_code: HTTP status code
            details: Additional error details
        """
        super().__init__(message, "NETWORK_ERROR", details)
        self.url = url
        self.status_code = status_code

        if url:
            self.details["url"] = url
        if status_code:
            self.details["status_code"] = status_code


# Error code constants for consistent error handling
class ErrorCodes:
    """Constants for error codes used throughout the library."""

    # Token validation errors
    TOKEN_MISSING = "TOKEN_MISSING"
    TOKEN_INVALID_FORMAT = "TOKEN_INVALID_FORMAT"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    TOKEN_INVALID_SIGNATURE = "TOKEN_INVALID_SIGNATURE"
    TOKEN_INVALID_ISSUER = "TOKEN_INVALID_ISSUER"
    TOKEN_INVALID_AUDIENCE = "TOKEN_INVALID_AUDIENCE"
    TOKEN_MISSING_CLAIMS = "TOKEN_MISSING_CLAIMS"

    # Configuration errors
    CONFIG_INVALID_ISSUER = "CONFIG_INVALID_ISSUER"
    CONFIG_INVALID_AUDIENCE = "CONFIG_INVALID_AUDIENCE"
    CONFIG_INVALID_JWKS_URI = "CONFIG_INVALID_JWKS_URI"
    CONFIG_INVALID_CACHE_TTL = "CONFIG_INVALID_CACHE_TTL"
    CONFIG_MISSING_REQUIRED_FIELD = "CONFIG_MISSING_REQUIRED_FIELD"

    # JWKS errors
    JWKS_FETCH_FAILED = "JWKS_FETCH_FAILED"
    JWKS_INVALID_RESPONSE = "JWKS_INVALID_RESPONSE"
    JWKS_NO_KEYS = "JWKS_NO_KEYS"
    JWKS_KEY_NOT_FOUND = "JWKS_KEY_NOT_FOUND"
    JWKS_INVALID_KEY = "JWKS_INVALID_KEY"

    # Middleware errors
    MIDDLEWARE_INIT_FAILED = "MIDDLEWARE_INIT_FAILED"
    MIDDLEWARE_PROCESS_FAILED = "MIDDLEWARE_PROCESS_FAILED"
    MIDDLEWARE_ROUTE_EXEMPTION_FAILED = "MIDDLEWARE_ROUTE_EXEMPTION_FAILED"

    # Authentication errors
    AUTH_HEADER_MISSING = "AUTH_HEADER_MISSING"
    AUTH_HEADER_INVALID = "AUTH_HEADER_INVALID"
    AUTH_BEARER_MISSING = "AUTH_BEARER_MISSING"
    AUTH_TOKEN_MISSING = "AUTH_TOKEN_MISSING"

    # Authorization errors
    AUTHZ_INSUFFICIENT_SCOPES = "AUTHZ_INSUFFICIENT_SCOPES"
    AUTHZ_INVALID_USER = "AUTHZ_INVALID_USER"
    AUTHZ_ACCESS_DENIED = "AUTHZ_ACCESS_DENIED"

    # Cache errors
    CACHE_KEY_GENERATION_FAILED = "CACHE_KEY_GENERATION_FAILED"
    CACHE_STORAGE_FAILED = "CACHE_STORAGE_FAILED"
    CACHE_RETRIEVAL_FAILED = "CACHE_RETRIEVAL_FAILED"
    CACHE_EXPIRATION_FAILED = "CACHE_EXPIRATION_FAILED"

    # Network errors
    NETWORK_TIMEOUT = "NETWORK_TIMEOUT"
    NETWORK_CONNECTION_FAILED = "NETWORK_CONNECTION_FAILED"
    NETWORK_HTTP_ERROR = "NETWORK_HTTP_ERROR"
    NETWORK_SSL_ERROR = "NETWORK_SSL_ERROR"
