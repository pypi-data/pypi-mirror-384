"""
ayz-auth: FastAPI middleware for Stytch B2B authentication with Redis caching.

This package provides a clean, reusable authentication middleware for FastAPI
applications using Stytch B2B authentication services with Redis caching for
optimal performance.

Version 2.0.0 adds support for:
- Organization entitlements and subscription tiers
- User team context
- MongoDB integration for entitlements data
- Entitlement-based authorization decorators
"""

from .decorators import (
    require_all_entitlements,
    require_any_entitlement,
    require_entitlement,
)
from .middleware import create_auth_dependency, verify_auth, verify_auth_optional
from .models.context import StytchContext
from .utils.exceptions import (
    AuthenticationError,
    StytchAPIError,
    TokenExtractionError,
    TokenVerificationError,
)

__version__ = "2.0.1"
__all__ = [
    # Core authentication
    "verify_auth",
    "verify_auth_optional",
    "create_auth_dependency",
    # Entitlement decorators (v2.0.0+)
    "require_entitlement",
    "require_any_entitlement",
    "require_all_entitlements",
    # Models
    "StytchContext",
    # Exceptions
    "AuthenticationError",
    "TokenExtractionError",
    "TokenVerificationError",
    "StytchAPIError",
]
