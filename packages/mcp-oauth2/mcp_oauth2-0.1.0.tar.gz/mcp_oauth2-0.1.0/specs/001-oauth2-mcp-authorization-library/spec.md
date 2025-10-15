# OAuth2 MCP Authorization Library Specification

## Overview

This specification defines a minimal, secure OAuth2 authorization library written in Python for MCP (Model Context Protocol) servers. The library provides simple middleware integration for FastAPI applications to authenticate requests using standard OAuth2 JWT tokens.

## Clarifications

### Session 2025-01-27
- Q: What JWKS caching strategy should be implemented? → A: In-memory caching with TTL (time-to-live) expiration
- Q: How should error responses be handled for authentication failures? → A: Return detailed error messages to clients
- Q: What should be the TTL duration for JWKS caching? → A: 1 hour
- Q: How should middleware scope be configured for route protection? → A: Protect all routes by default, allow opt-out exceptions
- Q: How should JWKS fetch failures be handled? → A: Fail fast - return 503 error if JWKS cannot be fetched

## Out of Scope

This library focuses on minimal OAuth2 client functionality for MCP servers. The following are explicitly out of scope:

- **User Management**: User creation, modification, or deletion functionality
- **OAuth2 Server Implementation**: Authorization server or resource server functionality
- **Custom Grant Types**: Implementation of non-standard OAuth2 grant types
- **Identity Federation**: SAML, LDAP, or other federation protocols
- **Multi-Factor Authentication**: MFA enrollment or management
- **Administrative Interfaces**: Web dashboards or management consoles
- **Token Storage UI**: User interfaces for managing stored tokens
- **Enterprise Features**: Conditional access, device compliance, location policies
- **Complex Caching**: Advanced token caching strategies
- **Server Registration**: Dynamic client registration flows
- **Metadata Discovery**: OAuth2 server metadata discovery
- **Multiple Frameworks**: Support beyond FastAPI

## Edge Cases and Error Handling

### Authentication Edge Cases
- **Missing Authorization Header**: Return 401 with WWW-Authenticate header
- **Invalid Token Format**: Return 401 with detailed error message
- **Expired Tokens**: Return 401 with token expiration details
- **Malformed JWT**: Return 401 with JWT parsing error details
- **Invalid Signature**: Return 401 with signature verification failure
- **Wrong Audience**: Return 401 with audience mismatch details
- **Wrong Issuer**: Return 401 with issuer mismatch details
- **JWKS Fetch Failure**: Return 503 with service unavailable message
- **JWKS Parse Error**: Return 503 with JWKS parsing error
- **Network Timeout**: Return 503 with network timeout error

### Configuration Edge Cases
- **Invalid Issuer URL**: Configuration validation error on startup
- **Invalid Audience**: Configuration validation error on startup
- **Missing Client ID**: Configuration validation error on startup
- **Invalid JWKS URI**: Configuration validation error on startup
- **HTTPS Validation**: Reject non-HTTPS URLs with configuration error

### Runtime Edge Cases
- **Concurrent JWKS Fetch**: Handle multiple simultaneous JWKS requests
- **Cache Corruption**: Clear cache and refetch JWKS on corruption
- **Memory Pressure**: Clear JWKS cache if memory usage exceeds limits
- **Clock Skew**: Handle token expiration with reasonable clock skew tolerance
- **Large JWKS**: Handle JWKS with many keys efficiently

### Integration Edge Cases
- **FastAPI Middleware Order**: Ensure proper middleware execution order
- **Route Exemption**: Handle exempt routes without authentication
- **Custom Error Handlers**: Allow custom error response handling
- **Request Context**: Properly inject user context into FastAPI dependencies

## Core Principles

### 1. Minimal API Surface
- **Simple middleware**: `app.add_middleware(OAuth2Middleware, config=config)`
- **Transparent token validation**: Automatic JWT token verification
- **Minimal configuration**: Simple OAuth2 provider configuration
- **Secure by default**: All routes protected by default with opt-out exceptions
- **Essential security**: OAuth 2.1 security requirements (HTTPS, audience validation)

### 2. Core Security
- **OAuth 2.1 compliance**: Essential implementation with PKCE and audience binding
- **Generic OAuth2**: Support for any standard OAuth2 provider
- **Basic logging**: Error logs and authentication events
- **Token validation**: Secure JWT token validation with signature verification

### 3. Developer Experience
- **Type-safe**: Pydantic v2 type checking and validation
- **Well-tested**: High test coverage with focused tests
- **Clear documentation**: Simple examples and setup guides
- **FastAPI focused**: Optimized for FastAPI applications

## User Stories

Based on the core principles and requirements, the primary user stories are:

- **US1 (P1)**: As an MCP server developer, I want to integrate OAuth2 authentication with a single line of code so that I can secure my endpoints without complexity
- **US2 (P1)**: As an MCP server, I want to validate JWT tokens automatically so that I can authenticate users transparently
- **US3 (P2)**: As an MCP server developer, I want detailed error messages when authentication fails so that I can debug issues quickly
- **US4 (P2)**: As an MCP server, I want to cache JWKS for performance so that I don't fetch keys on every request
- **US5 (P3)**: As an MCP server developer, I want to exempt specific routes from authentication so that I can have public endpoints

## API Specification

### Primary API

```python
from mcp_oauth2 import OAuth2Middleware, OAuth2Config
from fastapi import FastAPI

# Simple middleware integration
app = FastAPI()

config = OAuth2Config(
    issuer="https://your-oauth-provider.com",
    audience="https://your-mcp-server.com",
    client_id="your-client-id"
)

app.add_middleware(OAuth2Middleware, config=config)

# MCP server endpoints automatically protected
@app.post("/mcp/tools/call")
async def call_tool(request: ToolCallRequest, user: AuthenticatedUser):
    # user is automatically injected after OAuth2 validation
    return await handle_tool_call(request, user)

@app.get("/mcp/resources")
async def list_resources(user: AuthenticatedUser):
    # All endpoints automatically require valid OAuth2 token
    return await get_user_resources(user)
```

### Configuration API

```python
from mcp_oauth2 import OAuth2Config

# Simple OAuth2 provider configuration
config = OAuth2Config(
    issuer="https://your-oauth-provider.com",
    audience="https://your-mcp-server.com",
    client_id="your-client-id",
    jwks_uri="https://your-oauth-provider.com/.well-known/jwks.json"
)
```

## Architecture Specification

### Core Components

#### 1. Middleware module (`middleware.py`)
**Purpose**: Handle OAuth2 middleware for FastAPI applications

**Responsibilities**:
- Intercept HTTP requests to all routes (protect by default)
- Extract and validate Authorization headers
- Validate JWT tokens
- Inject authenticated user context
- Handle 401 responses
- Allow opt-out exceptions for specific routes

**Key Methods**:
```python
async def process_request(request: Request, call_next) -> Response
async def extract_authorization_header(request: Request) -> Optional[str]
async def validate_token(token: str, config: OAuth2Config) -> AuthenticatedUser
async def handle_unauthorized(request: Request) -> Response
async def is_exempt_route(request: Request, exempt_routes: List[str]) -> bool
```

#### 2. Token validation module (`token_validation.py`)
**Purpose**: Handle JWT token validation

**Responsibilities**:
- Validate JWT access tokens
- Verify token signature using JWKS with in-memory caching and TTL
- Check token expiration and issuer
- Extract user information from tokens
- Validate audience binding

**Key Methods**:
```python
async def validate_access_token(token: str, config: OAuth2Config) -> AuthenticatedUser
async def fetch_jwks(jwks_uri: str) -> JWKS
async def get_cached_jwks(jwks_uri: str) -> Optional[JWKS]
async def verify_token_signature(token: str, jwks: JWKS) -> bool
async def extract_user_info(token: str) -> UserInfo
async def handle_jwks_fetch_failure(error: Exception) -> None  # Raises 503 error
```

#### 3. Configuration module (`config.py`)
**Purpose**: Handle OAuth2 configuration

**Responsibilities**:
- Define OAuth2 provider configuration
- Validate configuration parameters
- Provide default values

**Key Classes**:
```python
class OAuth2Config(BaseModel):
    issuer: str
    audience: str
    client_id: str
    jwks_uri: Optional[str] = None
```

#### 4. Models module (`models.py`)
**Purpose**: Define data models

**Responsibilities**:
- Define AuthenticatedUser model
- Define JWKS and token models
- Provide type safety with Pydantic

**Key Models**:
```python
class AuthenticatedUser(BaseModel):
    sub: str  # Subject identifier
    email: Optional[str] = None
    name: Optional[str] = None
    aud: Optional[str] = None  # Audience
    iss: Optional[str] = None  # Issuer
    exp: Optional[int] = None  # Expiration time
```

## Security Specification

### OAuth 2.1 Compliance

#### 1. Essential Security Features
- **Audience Binding**: Tokens validated against expected audience
- **Issuer Validation**: Tokens validated against expected issuer
- **HTTPS Only**: All communications over TLS
- **Token Expiration**: Automatic validation of token expiration

#### 2. JWT Token Security
- **Signature Validation**: JWT signatures verified using JWKS
- **Expiration Check**: Automatic validation of token expiration time
- **Issuer Verification**: Token issuer must match configured issuer
- **Audience Verification**: Token audience must match configured audience

#### 3. Communication Security
- **HTTPS Only**: All communications over TLS
- **Secure Headers**: Proper HTTP security headers
- **Error Handling**: Secure error responses without information leakage

## Data Models

### Core Models

All data models use Pydantic v2 BaseModel for validation, serialization, and type safety:

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class OAuth2Config(BaseModel):
    """OAuth2 provider configuration"""
    issuer: str
    audience: str
    client_id: str
    jwks_uri: Optional[str] = None
    jwks_cache_ttl: int = 3600  # 1 hour in seconds
    exempt_routes: List[str] = []  # Routes exempt from authentication

class AuthenticatedUser(BaseModel):
    """Authenticated user context from OAuth2 token"""
    sub: str  # Subject identifier
    email: Optional[str] = None
    name: Optional[str] = None
    aud: Optional[str] = None  # Audience
    iss: Optional[str] = None  # Issuer
    exp: Optional[int] = None  # Expiration time
    iat: Optional[int] = None  # Issued at

class UserInfo(BaseModel):
    """User information extracted from JWT token"""
    sub: str
    email: Optional[str] = None
    name: Optional[str] = None
    preferred_username: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None

class JWKS(BaseModel):
    """JSON Web Key Set for token validation"""
    keys: List[Dict[str, Any]]

class SigningKey(BaseModel):
    """Signing key for JWT validation"""
    kid: str  # Key ID
    kty: str  # Key type
    use: str  # Key use
    alg: str  # Algorithm
    n: Optional[str] = None  # RSA modulus
    e: Optional[str] = None  # RSA exponent
```

## Error Handling Specification

### Error Types

```python
class MCPOAuth2Error(Exception):
    """Base exception for OAuth2 MCP errors"""
    pass

class TokenValidationError(MCPOAuth2Error):
    """Error during token validation"""
    pass

class ConfigurationError(MCPOAuth2Error):
    """Error in configuration"""
    pass

class JWKSError(MCPOAuth2Error):
    """Error during JWKS operations"""
    pass
```

### HTTP Status Codes and Responses

#### Authentication Errors (HTTP 401)
- **Missing Authorization Header**: `WWW-Authenticate: Bearer`
- **Invalid Token Format**: Detailed error with token format requirements
- **Expired Tokens**: Error with token expiration timestamp
- **Malformed JWT**: Error with JWT parsing details
- **Invalid Signature**: Error with signature verification failure
- **Wrong Audience**: Error with expected vs actual audience
- **Wrong Issuer**: Error with expected vs actual issuer

#### Service Errors (HTTP 503)
- **JWKS Fetch Failure**: Service unavailable with retry guidance
- **JWKS Parse Error**: Service unavailable with JWKS format error
- **Network Timeout**: Service unavailable with timeout details

#### Configuration Errors (HTTP 500)
- **Invalid Configuration**: Internal server error during startup validation
- **Runtime Configuration Error**: Internal server error for runtime config issues

### Error Response Format

```json
{
  "error": "invalid_token",
  "error_description": "Token validation failed: signature verification error",
  "error_code": "TOKEN_SIGNATURE_INVALID",
  "timestamp": "2025-01-27T10:30:00Z"
}
```

### Error Logging
- **Authentication Failures**: Log with user context (without sensitive data)
- **JWKS Errors**: Log with provider details and retry attempts
- **Configuration Errors**: Log with configuration validation details
- **Performance Issues**: Log with timing and resource usage data

## Performance Specification

### Response Times
- **Token Validation**: < 100ms for JWT validation (measured from token receipt to user context injection)
- **JWKS Fetching**: < 500ms for initial fetch, cached thereafter with 1-hour TTL
- **Middleware Overhead**: < 50ms additional latency per request (measured end-to-end request time)

### Performance Benchmarks
- **Token Validation Benchmark**: Validate 1000 JWT tokens in <10 seconds
- **JWKS Cache Performance**: Cache hit ratio >95% after initial fetch
- **Concurrent Load Test**: Handle 100+ simultaneous requests with <200ms average response time
- **Memory Usage Test**: Middleware instance memory usage <10MB under normal load

### Resource Usage
- **Memory**: < 10MB for middleware instances (measured via memory profiling)
- **CPU**: <5% CPU usage during token validation under normal load
- **Network**: HTTP client with connection reuse for JWKS fetching (max 2 concurrent connections)
- **Storage**: In-memory JWKS caching only (no persistent storage)

### Scalability
- **Concurrent Requests**: Support 100+ simultaneous requests with linear performance scaling
- **JWKS Caching**: In-memory caching with 1-hour TTL expiration and automatic refresh
- **Connection Reuse**: HTTP connection pooling for JWKS requests with connection limits

## Compatibility Specification

### OAuth2 Providers
- **RFC 6749 Compliant**: OAuth2 providers implementing RFC 6749 authorization framework
- **JWT Access Tokens**: Providers issuing JWT-formatted access tokens (RFC 7519)
- **JWKS Endpoint**: Providers exposing JSON Web Key Set endpoints (RFC 7517)
- **OpenID Connect**: Basic OIDC provider support with standard claims
- **Supported Algorithms**: RS256, RS384, RS512 for JWT signature verification
- **HTTPS Required**: All provider endpoints must use HTTPS with valid certificates

### MCP Servers
- **FastAPI**: Native integration with FastAPI applications

### Platforms
- **Cross-platform**: Works on Windows, macOS, and Linux
- **Docker**: Container-friendly configuration

## Project Structure

### Python Library Structure

```
mcp_oauth2/
├── __init__.py                 # Main API exports
├── middleware.py               # OAuth2 middleware for FastAPI
├── token_validation.py         # JWT token validation
├── config.py                   # Configuration models
├── models.py                   # Data models
├── exceptions.py               # Custom exception classes
└── utils.py                    # Utility functions

tests/
├── unit/                       # Unit tests
├── integration/                # Integration tests
└── conftest.py                 # Test configuration

docs/
├── README.md                   # Main documentation
└── examples/                   # Usage examples

pyproject.toml                  # Python project configuration
Makefile                        # Development commands
```

### Development Toolchain
- **Package Manager**: `uv` for dependency management
- **Type Checking**: `mypy` for static type analysis
- **Linting**: `ruff` for fast Python linting and formatting
- **Testing**: `pytest` for comprehensive testing framework
- **Build System**: `pyproject.toml` with modern Python packaging standards

## Testing Specification

### MVP Requirements
- **Coverage**: >95% code coverage required
- **Mocking**: Mock OAuth2 provider responses
- **Edge Cases**: Test all error conditions

### Integration Testing
- **OAuth2 Providers**: Test with real OAuth2 providers
- **FastAPI Integration**: Test with FastAPI applications
- **Error Scenarios**: Test failure modes and recovery

### Security Testing
- **Token Security**: Test JWT token validation
- **Audience Validation**: Verify audience binding
- **Error Handling**: Test secure error responses
