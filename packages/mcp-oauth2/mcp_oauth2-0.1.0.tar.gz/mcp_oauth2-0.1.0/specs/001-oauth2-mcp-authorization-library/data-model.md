# Data Model: OAuth2 MCP Authorization Library

**Date**: 2025-01-27  
**Feature**: OAuth2 MCP Authorization Library  
**Phase**: 1 - Design & Contracts

## Overview

This document defines the data models for the OAuth2 MCP authorization library, including configuration models, user context models, and JWT-related models. All models use Pydantic v2 for type safety, validation, and serialization.

## Core Configuration Models

### OAuth2Config

Primary configuration model for OAuth2 provider settings.

```python
class OAuth2Config(BaseModel):
    """OAuth2 provider configuration"""
    issuer: str = Field(..., description="OAuth2 provider issuer URL")
    audience: str = Field(..., description="Expected token audience (MCP server URI)")
    client_id: str = Field(..., description="OAuth2 client ID")
    jwks_uri: Optional[str] = Field(None, description="JWKS endpoint URL (auto-discovered if not provided)")
    jwks_cache_ttl: int = Field(3600, description="JWKS cache TTL in seconds (default: 1 hour)")
    exempt_routes: List[str] = Field(default_factory=list, description="Routes exempt from authentication")
    
    @validator('issuer')
    def validate_issuer(cls, v):
        if not v.startswith('https://'):
            raise ValueError('Issuer must use HTTPS')
        return v.rstrip('/')
    
    @validator('audience')
    def validate_audience(cls, v):
        if not v.startswith('https://'):
            raise ValueError('Audience must use HTTPS')
        return v.rstrip('/')
    
    @validator('jwks_cache_ttl')
    def validate_cache_ttl(cls, v):
        if v <= 0:
            raise ValueError('Cache TTL must be positive')
        return v
```

**Fields**:
- `issuer`: OAuth2 provider's issuer identifier (e.g., "https://auth.example.com")
- `audience`: Expected audience in JWT tokens (e.g., "https://mcp-server.example.com")
- `client_id`: OAuth2 client identifier for the MCP server
- `jwks_uri`: Optional JWKS endpoint URL (auto-discovered from issuer/.well-known/jwks.json)
- `jwks_cache_ttl`: Cache duration for JWKS in seconds (default: 3600)
- `exempt_routes`: List of route patterns exempt from authentication

**Validation Rules**:
- All URLs must use HTTPS
- Cache TTL must be positive
- URLs are normalized (trailing slashes removed)

## User Context Models

### AuthenticatedUser

Represents an authenticated user extracted from JWT token.

```python
class AuthenticatedUser(BaseModel):
    """Authenticated user context from OAuth2 token"""
    sub: str = Field(..., description="Subject identifier (user ID)")
    email: Optional[str] = Field(None, description="User email address")
    name: Optional[str] = Field(None, description="User display name")
    aud: Optional[str] = Field(None, description="Token audience")
    iss: Optional[str] = Field(None, description="Token issuer")
    exp: Optional[int] = Field(None, description="Token expiration time (Unix timestamp)")
    iat: Optional[int] = Field(None, description="Token issued at time (Unix timestamp)")
    
    @validator('email')
    def validate_email(cls, v):
        if v is not None and '@' not in v:
            raise ValueError('Invalid email format')
        return v
    
    @validator('exp', 'iat')
    def validate_timestamps(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Timestamp must be positive')
        return v
```

**Fields**:
- `sub`: Subject identifier (unique user ID from OAuth2 provider)
- `email`: User's email address (if available in token)
- `name`: User's display name (if available in token)
- `aud`: Token audience (should match configured audience)
- `iss`: Token issuer (should match configured issuer)
- `exp`: Token expiration timestamp
- `iat`: Token issued-at timestamp

**Validation Rules**:
- Email format validation if provided
- Timestamps must be positive if provided

### UserInfo

Extended user information extracted from JWT token claims.

```python
class UserInfo(BaseModel):
    """Extended user information from JWT token"""
    sub: str = Field(..., description="Subject identifier")
    email: Optional[str] = Field(None, description="User email address")
    name: Optional[str] = Field(None, description="User display name")
    preferred_username: Optional[str] = Field(None, description="Preferred username")
    given_name: Optional[str] = Field(None, description="Given name")
    family_name: Optional[str] = Field(None, description="Family name")
```

**Fields**:
- Standard OIDC claims for user information
- All fields optional except `sub`
- Used for extracting additional user details from tokens

## JWT and Security Models

### JWKS

JSON Web Key Set for token signature verification.

```python
class JWKS(BaseModel):
    """JSON Web Key Set for token validation"""
    keys: List[Dict[str, Any]] = Field(..., description="List of JSON Web Keys")
    
    @validator('keys')
    def validate_keys(cls, v):
        if not v:
            raise ValueError('JWKS must contain at least one key')
        return v
    
    def get_key_by_kid(self, kid: str) -> Optional[Dict[str, Any]]:
        """Get key by key ID"""
        for key in self.keys:
            if key.get('kid') == kid:
                return key
        return None
```

**Fields**:
- `keys`: List of JSON Web Keys for signature verification

**Methods**:
- `get_key_by_kid()`: Retrieve specific key by key ID

### SigningKey

Individual signing key from JWKS.

```python
class SigningKey(BaseModel):
    """Signing key for JWT validation"""
    kid: str = Field(..., description="Key ID")
    kty: str = Field(..., description="Key type (RSA, EC, etc.)")
    use: str = Field(..., description="Key use (sig, enc)")
    alg: str = Field(..., description="Algorithm (RS256, ES256, etc.)")
    n: Optional[str] = Field(None, description="RSA modulus (base64url)")
    e: Optional[str] = Field(None, description="RSA exponent (base64url)")
    x: Optional[str] = Field(None, description="EC x coordinate (base64url)")
    y: Optional[str] = Field(None, description="EC y coordinate (base64url)")
    
    @validator('kty')
    def validate_key_type(cls, v):
        if v not in ['RSA', 'EC', 'oct']:
            raise ValueError('Unsupported key type')
        return v
    
    @validator('use')
    def validate_key_use(cls, v):
        if v not in ['sig', 'enc']:
            raise ValueError('Invalid key use')
        return v
```

**Fields**:
- `kid`: Key identifier for JWT header matching
- `kty`: Key type (RSA, EC, octet string)
- `use`: Key use (signature, encryption)
- `alg`: Algorithm identifier
- `n`, `e`: RSA key components (modulus, exponent)
- `x`, `y`: Elliptic curve key components

**Validation Rules**:
- Key type must be supported (RSA, EC, oct)
- Key use must be valid (sig, enc)

## Exception Models

### MCPOAuth2Error

Base exception class for all OAuth2 MCP errors.

```python
class MCPOAuth2Error(Exception):
    """Base exception for OAuth2 MCP errors"""
    
    def __init__(self, message: str, error_code: Optional[str] = None):
        super().__init__(message)
        self.error_code = error_code
        self.message = message
```

### TokenValidationError

Exception for JWT token validation failures.

```python
class TokenValidationError(MCPOAuth2Error):
    """Error during token validation"""
    
    def __init__(self, message: str, token_issue: Optional[str] = None):
        super().__init__(message, "TOKEN_VALIDATION_ERROR")
        self.token_issue = token_issue
```

### ConfigurationError

Exception for configuration validation failures.

```python
class ConfigurationError(MCPOAuth2Error):
    """Error in configuration"""
    
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(message, "CONFIGURATION_ERROR")
        self.field = field
```

### JWKSError

Exception for JWKS operations failures.

```python
class JWKSError(MCPOAuth2Error):
    """Error during JWKS operations"""
    
    def __init__(self, message: str, jwks_uri: Optional[str] = None):
        super().__init__(message, "JWKS_ERROR")
        self.jwks_uri = jwks_uri
```

## Cache Models

### JWKSCacheEntry

In-memory cache entry for JWKS.

```python
class JWKSCacheEntry(BaseModel):
    """JWKS cache entry"""
    jwks: JWKS = Field(..., description="Cached JWKS")
    cached_at: datetime = Field(default_factory=datetime.utcnow, description="Cache timestamp")
    ttl_seconds: int = Field(..., description="Cache TTL in seconds")
    
    def is_expired(self) -> bool:
        """Check if cache entry is expired"""
        age = (datetime.utcnow() - self.cached_at).total_seconds()
        return age >= self.ttl_seconds
```

**Fields**:
- `jwks`: Cached JWKS data
- `cached_at`: Timestamp when cached
- `ttl_seconds`: Cache TTL duration

**Methods**:
- `is_expired()`: Check if cache entry has expired

## Model Relationships

```
OAuth2Config
├── Contains configuration for JWKS caching
├── Defines exempt routes
└── References issuer and audience

AuthenticatedUser
├── Extracted from JWT token
├── Validated against OAuth2Config
└── Injected into FastAPI endpoints

JWKS
├── Fetched from jwks_uri in OAuth2Config
├── Cached using JWKSCacheEntry
└── Used to validate JWT signatures

SigningKey
├── Individual keys from JWKS
├── Matched by 'kid' from JWT header
└── Used for signature verification
```

## Validation and Serialization

All models support:
- **Pydantic v2 validation**: Automatic type checking and validation
- **JSON serialization**: Built-in serialization to/from JSON
- **Field validation**: Custom validators for business rules
- **Type hints**: Full type safety with IDE support
- **Documentation**: Built-in field documentation and descriptions

## Usage Patterns

### Configuration
```python
config = OAuth2Config(
    issuer="https://auth.example.com",
    audience="https://mcp-server.example.com",
    client_id="mcp-server-client"
)
```

### User Context Injection
```python
@app.post("/mcp/tools/call")
async def call_tool(request: ToolCallRequest, user: AuthenticatedUser):
    # user is automatically validated and injected
    return await handle_tool_call(request, user.sub)
```

### Error Handling
```python
try:
    user = await validate_token(token, config)
except TokenValidationError as e:
    return JSONResponse(
        status_code=401,
        content={"error": e.message, "code": e.error_code}
    )
```

This data model provides a solid foundation for the OAuth2 MCP authorization library with comprehensive type safety, validation, and clear relationships between entities.