"""
Custom exceptions for ayz-auth package.

Provides specific exception types for different authentication failure scenarios.
"""

from typing import Any, Dict, Optional


class AuthenticationError(Exception):
    """
    Base exception for all authentication-related errors.

    This is the parent class for all authentication failures in the middleware.
    """

    def __init__(
        self,
        message: str,
        status_code: int = 401,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class TokenExtractionError(AuthenticationError):
    """
    Raised when a token cannot be extracted from the request headers.

    This includes scenarios where:
    - Authorization header is missing
    - Authorization header is malformed
    - Token format is invalid
    """

    def __init__(self, message: str = "Failed to extract authentication token"):
        super().__init__(
            message=message, status_code=401, details={"error_type": "token_extraction"}
        )


class TokenVerificationError(AuthenticationError):
    """
    Raised when token verification fails.

    This includes scenarios where:
    - Token is invalid or expired
    - Stytch API rejects the token
    - Token format is correct but verification fails
    """

    def __init__(
        self,
        message: str = "Token verification failed",
        token_hint: Optional[str] = None,
    ):
        details = {"error_type": "token_verification"}
        if token_hint:
            details["token_hint"] = token_hint

        super().__init__(message=message, status_code=401, details=details)


class StytchAPIError(AuthenticationError):
    """
    Raised when Stytch API returns an error or is unreachable.

    This includes scenarios where:
    - Stytch API is down or unreachable
    - API returns unexpected error responses
    - Network timeouts or connection issues
    """

    def __init__(
        self,
        message: str = "Stytch API error",
        api_status_code: Optional[int] = None,
        api_response: Optional[Dict[str, Any]] = None,
    ):
        details = {
            "error_type": "stytch_api",
            "api_status_code": api_status_code,
            "api_response": api_response,
        }

        super().__init__(
            message=message,
            status_code=503,  # Service Unavailable for API errors
            details=details,
        )


class CacheError(AuthenticationError):
    """
    Raised when Redis cache operations fail.

    This is typically a non-fatal error - the middleware should fall back
    to direct Stytch API verification when cache is unavailable.
    """

    def __init__(
        self, message: str = "Cache operation failed", operation: Optional[str] = None
    ):
        details = {"error_type": "cache", "operation": operation}

        super().__init__(
            message=message,
            status_code=500,  # Internal Server Error for cache issues
            details=details,
        )


class ConfigurationError(Exception):
    """
    Raised when the middleware is misconfigured.

    This includes scenarios where:
    - Required environment variables are missing
    - Configuration values are invalid
    - Dependencies are not properly configured
    """

    def __init__(self, message: str = "Authentication middleware misconfigured"):
        self.message = message
        super().__init__(self.message)
