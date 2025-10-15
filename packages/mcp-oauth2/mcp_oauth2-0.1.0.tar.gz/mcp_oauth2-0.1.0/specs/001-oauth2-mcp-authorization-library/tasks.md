# Tasks: OAuth2 MCP Authorization Library

**Feature**: OAuth2 MCP Authorization Library  
**Branch**: `001-oauth2-mcp-authorization-library`  
**Date**: 2025-01-27

## Overview

This document defines the implementation tasks for building a minimal, secure OAuth2 authorization library for MCP servers. The library provides simple middleware integration for FastAPI applications with automatic JWT token validation and user context injection.

**Tech Stack**: Python 3.13.5+, FastAPI, Pydantic v2, PyJWT, httpx, uv package manager  
**Testing**: pytest with >95% coverage requirement  
**Target**: Cross-platform Python library package

## User Stories

User stories are defined in spec.md (see User Stories section). The implementation tasks are organized around these user stories:

- **US1 (P1)**: Single-line middleware integration (T008-T010)
- **US2 (P1)**: Automatic JWT token validation (T011-T015)
- **US3 (P2)**: Detailed error messages (T016-T018)
- **US4 (P2)**: JWKS caching for performance (T019-T021)
- **US5 (P3)**: Route exemption configuration (T022-T024)

## Task Organization

Tasks are organized by user story to enable independent implementation and testing. Each user story phase can be completed independently and provides immediate value.

## Phase 1: Setup Tasks (Project Initialization)

### T001: Initialize Python Package Structure ✅
**File**: `pyproject.toml`
- ✅ Create Python package configuration with uv package manager
- ✅ Define project metadata, dependencies (FastAPI, Pydantic v2, PyJWT, httpx)
- ✅ Configure build system and entry points
- ✅ Set up development dependencies (pytest, mypy, ruff)

### T002: Create Package Directory Structure ✅
**Files**: `mcp_oauth2/__init__.py`, `tests/`, `docs/`
- ✅ Create `mcp_oauth2/` package directory
- ✅ Create `tests/unit/` and `tests/integration/` directories
- ✅ Create `docs/` directory with README.md and examples/
- ✅ Set up basic package structure

### T003: Configure Development Tools ✅
**Files**: `Makefile`, `.gitignore`, `conftest.py`
- ✅ Create Makefile with development commands (dev, test, lint, format, type-check)
- ✅ Set up .gitignore for Python projects
- ✅ Configure pytest conftest.py with common fixtures
- ✅ Set up mypy and ruff configuration

## Phase 2: Foundational Tasks (Blocking Prerequisites)

### T004: Implement Core Exception Classes ✅
**File**: `mcp_oauth2/exceptions.py`
- ✅ Implement `MCPOAuth2Error` base exception
- ✅ Implement `TokenValidationError` for JWT validation failures
- ✅ Implement `ConfigurationError` for config validation failures
- ✅ Implement `JWKSError` for JWKS operation failures
- ✅ Add error codes and structured error information

### T005: Implement Data Models ✅
**File**: `mcp_oauth2/models.py`
- ✅ Implement `OAuth2Config` with validation (HTTPS enforcement, TTL validation)
- ✅ Implement `AuthenticatedUser` with JWT token fields
- ✅ Implement `UserInfo` for extended user information
- ✅ Implement `JWKS` and `SigningKey` models
- ✅ Implement `JWKSCacheEntry` for caching
- ✅ Add Pydantic v2 validators and field documentation

### T006: Implement Configuration Module ✅
**File**: `mcp_oauth2/config.py`
- ✅ Implement configuration loading and validation
- ✅ Add environment variable support
- ✅ Implement configuration defaults and validation
- ✅ Add configuration error handling

### T007: Implement Utility Functions ✅
**File**: `mcp_oauth2/utils.py`
- ✅ Implement URL validation utilities
- ✅ Implement JWT token parsing utilities
- ✅ Implement cache key generation utilities
- ✅ Add common validation functions

## Phase 3: User Story 1 - Single-Line Middleware Integration (P1)

**Goal**: Enable MCP server developers to add OAuth2 authentication with minimal code

**Independent Test Criteria**: 
- Developer can add middleware with single line: `app.add_middleware(OAuth2Middleware, config=config)`
- Middleware accepts OAuth2Config without errors
- Middleware integrates with FastAPI application without breaking existing functionality

### T008: Implement OAuth2 Middleware Class ✅
**File**: `mcp_oauth2/middleware.py`
- ✅ Implement `OAuth2Middleware` class extending FastAPI middleware
- ✅ Add middleware initialization with OAuth2Config
- ✅ Implement `process_request` method for request interception
- ✅ Add route exemption checking (`is_exempt_route` method)
- ✅ Implement middleware integration with FastAPI dependency injection

### T009: Implement Main Package API ✅
**File**: `mcp_oauth2/__init__.py`
- ✅ Export `OAuth2Middleware` and `OAuth2Config` classes
- ✅ Export `AuthenticatedUser` model for type hints
- ✅ Export exception classes
- ✅ Add package version and metadata

### T010: Create Basic Integration Test ✅ [P]
**File**: `tests/integration/test_middleware_integration.py`
- ✅ Test middleware can be added to FastAPI app
- ✅ Test middleware accepts valid OAuth2Config
- ✅ Test middleware doesn't break app startup
- ✅ Test exempt routes bypass authentication

## Phase 4: User Story 2 - Automatic JWT Token Validation (P1)

**Goal**: Automatically validate JWT tokens and inject authenticated user context

**Independent Test Criteria**:
- Middleware extracts Bearer tokens from Authorization header
- Middleware validates JWT tokens against configured issuer and audience
- Middleware injects AuthenticatedUser into protected endpoints
- Middleware returns 401 for invalid/missing tokens

### T011: Implement Token Validation Module ✅ [P]
**File**: `mcp_oauth2/token_validation.py`
- ✅ Implement `validate_access_token` function
- ✅ Implement JWT signature verification with JWKS
- ✅ Implement issuer and audience validation
- ✅ Implement token expiration checking
- ✅ Implement user information extraction from JWT claims

### T012: Implement JWKS Handling ✅ [P]
**File**: `mcp_oauth2/token_validation.py` (continued)
- ✅ Implement `fetch_jwks` function for HTTP requests
- ✅ Implement `get_cached_jwks` function with TTL checking
- ✅ Implement `verify_token_signature` with key matching
- ✅ Implement JWKS cache management with in-memory storage
- ✅ Add error handling for JWKS fetch failures (503 errors)

### T013: Integrate Token Validation with Middleware ✅ [P]
**File**: `mcp_oauth2/middleware.py` (continued)
- ✅ Integrate token validation in middleware request processing
- ✅ Implement Authorization header extraction
- ✅ Implement user context injection into FastAPI endpoints
- ✅ Implement 401 error responses with WWW-Authenticate headers
- ✅ Add proper error handling and logging

### T014: Create Token Validation Tests ✅ [P]
**File**: `tests/unit/test_token_validation.py`
- ✅ Test JWT token validation with valid tokens
- ✅ Test signature verification with mock JWKS
- ✅ Test issuer and audience validation
- ✅ Test token expiration handling
- ✅ Test JWKS caching and TTL expiration
- ✅ Test error handling for invalid tokens

### T015: Create Middleware Integration Tests ✅ [P]
**File**: `tests/integration/test_middleware_auth.py`
- ✅ Test middleware with valid JWT tokens
- ✅ Test middleware with invalid JWT tokens
- ✅ Test middleware with missing Authorization header
- ✅ Test user context injection in endpoints
- ✅ Test 401 responses with proper headers

## Phase 5: User Story 3 - Detailed Error Messages (P2)

**Goal**: Provide clear, actionable error messages for authentication failures

**Independent Test Criteria**:
- Authentication errors return detailed error messages
- Error responses include specific error codes
- Error messages help developers understand what went wrong
- Error responses maintain security (no sensitive information leakage)

### T016: Implement Detailed Error Responses [P]
**File**: `mcp_oauth2/middleware.py` (continued)
- Implement detailed error message formatting
- Add error codes for different failure types
- Implement secure error response generation
- Add error logging for debugging
- Ensure no sensitive information in error messages

### T017: Enhance Exception Classes with Details [P]
**File**: `mcp_oauth2/exceptions.py` (continued)
- Add detailed error message generation
- Add error context information
- Implement error code mapping
- Add error severity levels
- Implement error serialization for API responses

### T018: Create Error Handling Tests [P]
**File**: `tests/unit/test_error_handling.py`
- Test error message generation for different failure types
- Test error code assignment
- Test error response formatting
- Test security of error messages (no sensitive data)
- Test error logging functionality

## Phase 6: User Story 4 - JWKS Caching for Performance (P2)

**Goal**: Cache JWKS with TTL to improve performance and reduce network calls

**Independent Test Criteria**:
- JWKS is cached after first fetch
- Cache respects TTL configuration
- Cache expires and refetches when needed
- Cache handles concurrent requests properly
- Cache provides significant performance improvement

### T019: Implement JWKS Caching System [P]
**File**: `mcp_oauth2/token_validation.py` (continued)
- Implement thread-safe in-memory cache
- Implement TTL-based cache expiration
- Implement cache key generation
- Implement cache hit/miss tracking
- Add cache statistics and monitoring

### T020: Optimize JWKS Fetch Performance [P]
**File**: `mcp_oauth2/token_validation.py` (continued)
- Implement HTTP connection reuse with httpx
- Implement request timeout configuration
- Implement retry logic for failed requests
- Add performance monitoring for JWKS operations
- Optimize cache lookup performance

### T021: Create Performance Tests [P]
**File**: `tests/unit/test_performance.py`
- Test JWKS caching performance (<500ms initial, <50ms cached)
- Test cache TTL expiration behavior
- Test concurrent cache access
- Test memory usage constraints (<10MB)
- Test token validation performance (<100ms)
- Test token validation benchmark (1000 tokens in <10 seconds)
- Test JWKS cache hit ratio (>95% after initial fetch)
- Test concurrent load (100+ requests with <200ms average)
- Test CPU usage (<5% during token validation)
- Test connection limits (max 2 concurrent JWKS connections)

## Phase 7: User Story 5 - Route Exemption Configuration (P3)

**Goal**: Allow developers to exempt specific routes from authentication

**Independent Test Criteria**:
- Routes in exempt_routes list bypass authentication
- Exempt routes work with pattern matching
- Exempt routes don't receive user context
- Configuration validation for exempt routes
- Exempt routes maintain security for public endpoints

### T022: Implement Route Exemption Logic [P]
**File**: `mcp_oauth2/middleware.py` (continued)
- Implement route pattern matching for exemptions
- Implement exempt route checking in middleware
- Add support for wildcard patterns
- Implement exempt route validation
- Add exempt route logging for security auditing

### T023: Enhance Configuration for Route Exemptions [P]
**File**: `mcp_oauth2/config.py` (continued)
- Add exempt_routes validation
- Implement route pattern validation
- Add exempt route documentation
- Implement exempt route examples
- Add security warnings for exempt routes

### T024: Create Route Exemption Tests [P]
**File**: `tests/unit/test_route_exemption.py`
- Test exempt route pattern matching
- Test exempt routes bypass authentication
- Test exempt route configuration validation
- Test exempt route security considerations
- Test exempt route logging

## Phase 8: Polish & Cross-Cutting Concerns

### T025: Implement Comprehensive Test Suite [P]
**File**: `tests/conftest.py`, `tests/fixtures/`
- Create comprehensive test fixtures
- Implement mock OAuth2 provider responses
- Add test data generators
- Implement test utilities and helpers
- Ensure >95% test coverage

### T026: Create Documentation and Examples [P]
**Files**: `docs/README.md`, `docs/examples/`
- Create comprehensive README with installation instructions
- Add usage examples for common scenarios
- Create troubleshooting guide
- Add API documentation
- Create integration examples

### T027: Implement Security Hardening [P]
**Files**: Various
- Add input validation and sanitization
- Implement rate limiting considerations
- Add security headers
- Implement secure logging practices
- Add security audit checklist

### T028: Performance Optimization [P]
**Files**: Various
- Optimize token validation algorithms
- Implement connection pooling
- Add performance monitoring
- Optimize memory usage
- Add performance benchmarks

### T029: Final Integration Testing [P]
**File**: `tests/integration/test_full_integration.py`
- Test complete OAuth2 flow with real providers
- Test FastAPI integration scenarios
- Test error handling end-to-end
- Test performance under load
- Test security scenarios

### T030: Package Distribution Setup [P]
**Files**: `pyproject.toml`, `Makefile`
- Configure package distribution
- Add version management
- Implement automated testing
- Add CI/CD configuration
- Create release process

## Dependencies

### User Story Completion Order
1. **US1 (P1)**: Single-line middleware integration - Can start after Phase 2
2. **US2 (P1)**: Automatic JWT validation - Depends on US1 completion
3. **US3 (P2)**: Detailed error messages - Can be implemented in parallel with US2
4. **US4 (P2)**: JWKS caching - Can be implemented in parallel with US2/US3
5. **US5 (P3)**: Route exemptions - Can be implemented after US1-US4

### Parallel Execution Opportunities

**Phase 3 (US1)**:
- T008, T009, T010 can be implemented in parallel

**Phase 4 (US2)**:
- T011, T012, T013 can be implemented in parallel
- T014, T015 can be implemented in parallel after core implementation

**Phase 5-6 (US3-US4)**:
- All tasks in Phase 5 and Phase 6 can be implemented in parallel
- T016-T021 can be worked on simultaneously

**Phase 7 (US5)**:
- T022, T023, T024 can be implemented in parallel

**Phase 8 (Polish)**:
- All tasks can be implemented in parallel

## Implementation Strategy

### MVP Scope (Recommended)
**MVP includes**: US1 + US2 (Single-line integration + Automatic JWT validation)
- Provides core functionality for OAuth2 authentication
- Enables immediate value for MCP server developers
- Establishes foundation for additional features

### Incremental Delivery
1. **Sprint 1**: Phase 1-2 (Setup + Foundational) - 1-2 days
2. **Sprint 2**: Phase 3-4 (US1 + US2) - 3-4 days  
3. **Sprint 3**: Phase 5-6 (US3 + US4) - 2-3 days
4. **Sprint 4**: Phase 7 (US5) - 1-2 days
5. **Sprint 5**: Phase 8 (Polish) - 2-3 days

### Quality Gates
- Each phase must achieve >95% test coverage
- Performance targets must be met (<100ms token validation)
- Security requirements must be validated
- Documentation must be complete for each delivered feature

## Task Summary

- **Total Tasks**: 30
- **Setup Tasks**: 3 (T001-T003)
- **Foundational Tasks**: 4 (T004-T007) 
- **US1 Tasks**: 3 (T008-T010)
- **US2 Tasks**: 5 (T011-T015)
- **US3 Tasks**: 3 (T016-T018)
- **US4 Tasks**: 3 (T019-T021)
- **US5 Tasks**: 3 (T022-T024)
- **Polish Tasks**: 6 (T025-T030)

**Parallel Opportunities**: 15+ tasks can be implemented in parallel across different phases
**Independent Test Criteria**: Each user story has clear, measurable completion criteria
**Suggested MVP Scope**: US1 + US2 (Single-line integration + Automatic JWT validation)