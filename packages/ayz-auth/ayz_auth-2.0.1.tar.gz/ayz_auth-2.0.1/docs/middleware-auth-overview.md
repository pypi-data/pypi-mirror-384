# Middleware Authentication Overview

This document provides a high-level overview of the middleware authentication package, outlining its responsibilities, technologies, testing strategies, and deployment procedures.

## Purpose

The middleware serves as a central authentication and authorization point for APIs, ensuring all incoming requests are securely verified, user context is attached, and unauthorized requests are gracefully rejected.

## Technologies and Tools

- **Python**: Core programming language.
- **Stytch**: B2B Authentication service for verifying session tokens.
- **MongoDB**: Storage solution for user objects and relevant user data.
- **Redis**: Session token caching mechanism for efficient verification.
- **Pytest**: Testing framework for robust unit and integration tests.
- **UV**: Build tooling for Python package management and dependencies.
- **Twine**: Deployment tool for publishing packages to PyPI.

## Functional Requirements

### 1. Token Extraction
- Extract the session token from the incoming request headers.
- Clearly handle scenarios where the session token is missing or malformed.

### 2. Token Verification
- Verify the token using the following workflow:
  1. Check Redis for token validity (cached verification).
  2. If not present in Redis, authenticate via the Stytch B2B Auth API.
  3. Cache the validated token status in Redis for performance optimization.

### 3. User Context Attachment
- Upon successful verification, attach relevant user context to the request object.
- The user context should minimally include:
  - Stytch Member ID
  - User Roles
  - Organizational affiliation
  - Project identifiers (if applicable)

### 4. Error Handling
- Clearly defined response structure for authentication errors:
  - Return an HTTP `401 Unauthorized` status for invalid or expired tokens.
  - Include informative messages to assist client-side debugging.

## Testing Strategy

Tests will be developed using Pytest to cover:

- Token extraction logic (valid, missing, malformed).
- Redis cache interaction (hits and misses).
- Stytch API integration (successful and unsuccessful authentication).
- Context attachment verification.
- Authentication error handling and response structures.

## Implementation Considerations

- Ensure sensitive data, such as session tokens, are securely handled and logged responsibly.
- Implement robust logging and error tracing to ease debugging and incident response.
- Design middleware to be lightweight, performant, and easily maintainable.

## Deployment to PyPI

Deployment involves packaging the middleware using UV and uploading to PyPI:

### 1. Build your package with UV

```bash
uv build
```

## Implementation Log

### 2025-06-02: Initial Package Implementation

**What was done:**
- Created complete ayz-auth Python package from scratch
- Implemented FastAPI middleware for Stytch B2B authentication with Redis caching
- Built modular architecture with separate concerns for token extraction, verification, caching, and context building
- Added comprehensive error handling and logging with sensitive data protection
- Created full Pydantic models for type safety and validation
- Implemented comprehensive test suite with 21 passing tests
- Added proper Python packaging with UV support

**Key Features Implemented:**
- Token extraction from Authorization headers with validation
- Two-tier verification system (Redis cache + Stytch API fallback)
- StytchContext model containing only essential session data from Stytch
- Environment-based configuration with sensible defaults
- Custom authentication dependencies for advanced authorization
- Optional authentication support
- Comprehensive error handling with structured responses

**Architecture:**
- Clean separation between authentication middleware and business logic
- Middleware only returns Stytch session data - applications use member_id to fetch their own user data
- Modular design following Single Responsibility Principle
- Full type safety with Pydantic models
- Environment-scoped logging that protects sensitive data

**Rationale:**
This approach provides a clean, reusable authentication layer that can be easily integrated into any FastAPI application using Stytch B2B. By keeping the middleware focused solely on authentication and returning only Stytch data, we maintain loose coupling and allow applications to manage their own user data schemas independently.

### 2025-06-02: Warning Resolution & Future-Proofing

**What was done:**
- Fixed Pydantic deprecation warnings by replacing `json_encoders` with modern `@field_serializer` decorators
- Updated all datetime usage from deprecated `datetime.utcnow()` to `datetime.now(timezone.utc)`
- Ensured all tests run cleanly without warnings
- Added comprehensive .gitignore for Python projects
- Created example usage script demonstrating all features

**Rationale:**
Addressed deprecation warnings to ensure the package remains compatible with future versions of Pydantic and Python. This proactive approach prevents breaking changes and maintains code quality standards.
