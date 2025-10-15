# Research: OAuth2 MCP Authorization Library

**Date**: 2025-01-27  
**Feature**: OAuth2 MCP Authorization Library  
**Phase**: 0 - Research and Technology Decisions

## Technology Stack Decisions

### Python 3.13.5+ with Modern Tooling

**Decision**: Use Python 3.13.5+ with uv package manager, Pydantic v2, and modern development tools

**Rationale**: 
- Python provides excellent OAuth2/JWT libraries (PyJWT, cryptography)
- uv package manager offers faster dependency resolution than pip
- Pydantic v2 provides superior type safety and validation
- Python 3.13.5+ includes performance improvements and modern async features

**Alternatives Considered**:
- Node.js/TypeScript: Rejected due to Python's superior JWT/OAuth2 ecosystem
- Rust: Rejected due to complexity vs. minimal scope requirements
- Go: Rejected due to FastAPI integration requirements

### FastAPI Middleware Architecture

**Decision**: Implement as FastAPI middleware with automatic route protection

**Rationale**:
- FastAPI is the most popular Python web framework for APIs
- Middleware pattern provides transparent integration
- Automatic dependency injection for authenticated users
- Built-in async support for performance

**Alternatives Considered**:
- Flask middleware: Rejected due to FastAPI's superior async performance
- Decorator-based approach: Rejected due to complexity and manual application
- Standalone validation service: Rejected due to scope constraints

### JWT Token Validation with JWKS

**Decision**: Use PyJWT with JWKS for token signature verification

**Rationale**:
- PyJWT is the standard library for JWT validation in Python
- JWKS provides secure key rotation support
- In-memory caching with TTL balances performance and security
- Fail-fast behavior ensures secure defaults

**Alternatives Considered**:
- Token introspection: Rejected due to additional network calls
- Custom signature validation: Rejected due to security risks
- Persistent key storage: Rejected due to complexity

### In-Memory JWKS Caching

**Decision**: Implement in-memory caching with 1-hour TTL for JWKS

**Rationale**:
- Eliminates repeated network calls for key fetching
- 1-hour TTL balances performance with security (key rotation)
- Simple implementation without external dependencies
- Fail-fast on fetch errors ensures security

**Alternatives Considered**:
- No caching: Rejected due to performance impact
- File-based caching: Rejected due to complexity
- Redis/external cache: Rejected due to scope constraints
- Longer TTL (24h): Rejected due to security concerns

### Secure-by-Default Route Protection

**Decision**: Protect all routes by default with opt-out exceptions

**Rationale**:
- Aligns with security best practices
- Prevents accidental exposure of unprotected endpoints
- Simple configuration via exempt_routes list
- Clear security model for developers

**Alternatives Considered**:
- Opt-in protection: Rejected due to security risks
- Per-route decorators: Rejected due to complexity
- Path-based configuration: Rejected due to maintenance overhead

### Detailed Error Responses

**Decision**: Return detailed error messages to clients for debugging

**Rationale**:
- Improves developer experience and debugging
- Helps MCP clients understand authentication failures
- Aligns with modern API design patterns
- Supports troubleshooting in development environments

**Alternatives Considered**:
- Generic error messages: Rejected due to poor developer experience
- Log-only detailed errors: Rejected due to debugging difficulties
- Conditional error detail: Rejected due to complexity

### HTTP Client for JWKS Fetching

**Decision**: Use httpx for asynchronous HTTP requests to JWKS endpoints

**Rationale**:
- httpx provides modern async HTTP client capabilities
- Built-in connection pooling and reuse
- Excellent error handling and timeout support
- Lightweight compared to requests library

**Alternatives Considered**:
- aiohttp: Rejected due to larger dependency footprint
- requests: Rejected due to synchronous nature
- urllib: Rejected due to complexity and lack of async support

### Testing Strategy

**Decision**: Use pytest with >95% coverage requirement and comprehensive mocking

**Rationale**:
- pytest is the standard testing framework for Python
- >95% coverage ensures comprehensive testing
- Mock OAuth2 providers for reliable unit tests
- Integration tests with real OAuth2 providers

**Alternatives Considered**:
- unittest: Rejected due to pytest's superior features
- Coverage threshold <95%: Rejected due to quality requirements
- No integration testing: Rejected due to reliability concerns

## Security Considerations

### OAuth 2.1 Compliance

**Decision**: Implement essential OAuth 2.1 security requirements

**Rationale**:
- Audience binding prevents token misuse
- Issuer validation ensures token authenticity
- HTTPS-only communications prevent interception
- Token expiration validation prevents replay attacks

### JWT Signature Verification

**Decision**: Verify JWT signatures using JWKS with proper key rotation

**Rationale**:
- Prevents token tampering
- Supports key rotation for enhanced security
- Uses industry-standard cryptographic practices
- Fail-fast on signature validation errors

### Error Handling Security

**Decision**: Provide detailed errors while maintaining security

**Rationale**:
- Detailed errors help with debugging without exposing sensitive data
- HTTP status codes provide clear failure reasons
- WWW-Authenticate headers guide client authentication
- No sensitive token or key information in error messages

## Performance Considerations

### Token Validation Performance

**Decision**: Target <100ms for JWT validation operations

**Rationale**:
- Fast validation improves user experience
- Supports high-throughput MCP server scenarios
- Achievable with PyJWT and proper caching
- Measurable performance target for testing

### JWKS Caching Strategy

**Decision**: 1-hour TTL with in-memory storage

**Rationale**:
- Reduces network calls by 99%+ in typical usage
- 1-hour TTL balances performance with security
- In-memory storage provides fastest access
- Simple implementation without external dependencies

### Memory Usage Constraints

**Decision**: Limit to <10MB memory usage for middleware instances

**Rationale**:
- Supports deployment in resource-constrained environments
- Achievable with efficient data structures
- Measurable constraint for testing
- Supports high-density deployments

## Integration Patterns

### FastAPI Middleware Integration

**Decision**: Use FastAPI's middleware system with dependency injection

**Rationale**:
- Automatic request interception and processing
- Dependency injection for authenticated user context
- Seamless integration with FastAPI's async model
- Standard pattern familiar to FastAPI developers

### MCP Server Integration

**Decision**: Automatic protection of MCP endpoints with user context injection

**Rationale**:
- Transparent integration with MCP server patterns
- Automatic user context for MCP tool/resource handlers
- Consistent authentication across all MCP endpoints
- Minimal code changes required for MCP server developers

### Configuration Management

**Decision**: Use Pydantic models for configuration validation

**Rationale**:
- Type-safe configuration with automatic validation
- Clear error messages for invalid configuration
- IDE support with autocompletion and type checking
- Standard pattern for Python applications

## Conclusion

The research phase has established a clear technology stack and architectural approach that balances security, performance, and developer experience. All major technical decisions have been made with clear rationale and alternatives considered. The approach focuses on minimal complexity while maintaining enterprise-grade security and performance characteristics.

The implementation can proceed to Phase 1 design with confidence in the technical foundation.