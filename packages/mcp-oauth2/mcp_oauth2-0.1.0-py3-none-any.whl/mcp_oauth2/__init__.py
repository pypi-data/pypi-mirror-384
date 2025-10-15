"""OAuth2 MCP Authorization Library.

A minimal, secure OAuth2 authorization library for MCP (Model Context Protocol) servers.
Provides simple middleware integration for FastAPI applications to authenticate requests
using standard OAuth2 JWT tokens.
"""

__version__ = "0.1.0"
__author__ = "MCP OAuth2 Team"
__email__ = "team@mcp-oauth2.dev"

# Core models
# Configuration utilities
from .config import (
    auto_discover_jwks_uri,
    create_config,
    get_default_config,
    load_config_from_dict,
    load_config_from_env,
    validate_config,
)

# Exception classes
from .exceptions import (
    AuthenticationError,
    AuthorizationError,
    CacheError,
    ConfigurationError,
    ErrorCodes,
    JWKSError,
    MCPOAuth2Error,
    MiddlewareError,
    NetworkError,
    TokenValidationError,
)

# Middleware
from .middleware import OAuth2Middleware, get_authenticated_user
from .models import (
    JWKS,
    AuthenticatedUser,
    JWKSCacheEntry,
    OAuth2Config,
    SigningKey,
    TokenValidationResult,
    UserInfo,
)

# Token validation
from .token_validation import (
    clear_jwks_cache,
    fetch_jwks,
    get_cached_jwks,
    get_jwks_cache_stats,
    validate_access_token,
)

# Utility functions
from .utils import (
    extract_bearer_token,
    extract_user_claims,
    generate_cache_key,
    is_exempt_route,
    sanitize_for_logging,
    validate_issuer_audience,
    validate_jwt_format,
    validate_required_claims,
    validate_token_expiration,
    validate_token_issued_at,
    validate_url,
)

# Main API exports
__all__ = [
    # Version info
    "__version__",
    "__author__",
    "__email__",
    # Core models
    "AuthenticatedUser",
    "JWKS",
    "JWKSCacheEntry",
    "OAuth2Config",
    "SigningKey",
    "TokenValidationResult",
    "UserInfo",
    # Exception classes
    "AuthenticationError",
    "AuthorizationError",
    "CacheError",
    "ConfigurationError",
    "ErrorCodes",
    "JWKSError",
    "MCPOAuth2Error",
    "MiddlewareError",
    "NetworkError",
    "TokenValidationError",
    # Configuration utilities
    "auto_discover_jwks_uri",
    "create_config",
    "get_default_config",
    "load_config_from_dict",
    "load_config_from_env",
    "validate_config",
    # Utility functions
    "extract_bearer_token",
    "is_exempt_route",
    "validate_url",
    "validate_jwt_format",
    "validate_required_claims",
    "validate_token_expiration",
    "validate_token_issued_at",
    "validate_issuer_audience",
    "extract_user_claims",
    "generate_cache_key",
    "sanitize_for_logging",
    # Middleware
    "OAuth2Middleware",
    "get_authenticated_user",
    # Token validation
    "validate_access_token",
    "fetch_jwks",
    "get_cached_jwks",
    "clear_jwks_cache",
    "get_jwks_cache_stats",
]
