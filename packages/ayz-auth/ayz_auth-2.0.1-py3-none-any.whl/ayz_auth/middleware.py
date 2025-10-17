"""
FastAPI middleware for Stytch B2B authentication.

Provides the main verify_auth dependency that can be used in FastAPI routes
to authenticate requests and provide Stytch session context.
"""

from typing import Callable, List, Optional

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer

from .auth.stytch_verifier import stytch_verifier
from .auth.token_extractor import extract_token_from_request
from .models.context import StytchContext
from .utils.exceptions import (
    ConfigurationError,
    StytchAPIError,
    TokenExtractionError,
    TokenVerificationError,
)
from .utils.logger import logger

# FastAPI security scheme for OpenAPI documentation
security = HTTPBearer(
    scheme_name="Bearer Token",
    description="Stytch B2B session token",
    auto_error=False,  # We handle errors manually for better control
)


async def verify_auth(
    request: Request, token: Optional[str] = Depends(security)
) -> StytchContext:
    """
    FastAPI dependency for Stytch B2B authentication.

    This function serves as the main entry point for authentication in FastAPI
    applications. It extracts the session token from the request, verifies it
    with Stytch (using Redis caching), and returns the authenticated user context.

    Usage:
        @app.get("/protected")
        async def protected_route(user: StytchContext = Depends(verify_auth)):
            return {"message": f"Hello {user.member_email}"}

    Args:
        request: FastAPI Request object
        token: Optional token from HTTPBearer (for OpenAPI docs)

    Returns:
        StytchContext with authenticated session data

    Raises:
        HTTPException: 401 for authentication failures, 503 for service errors
    """
    try:
        logger.debug("Starting authentication verification")

        # Extract token from request
        session_token = extract_token_from_request(request)

        # Verify token with Stytch (with caching)
        stytch_context = await stytch_verifier.verify_session_token(session_token)

        logger.info(
            f"Authentication successful for member: {stytch_context.member_id}",
            extra={
                "member_id": stytch_context.member_id,
                "organization_id": stytch_context.organization_id,
                "session_id": stytch_context.session_id,
            },
        )

        return stytch_context

    except TokenExtractionError as e:
        logger.warning(f"Token extraction failed: {e.message}")
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "error": "authentication_failed",
                "message": e.message,
                "type": "token_extraction",
            },
        )

    except TokenVerificationError as e:
        logger.warning(f"Token verification failed: {e.message}")
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "error": "authentication_failed",
                "message": e.message,
                "type": "token_verification",
            },
        )

    except StytchAPIError as e:
        logger.error(f"Stytch API error: {e.message}", extra=e.details)
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "error": "service_unavailable",
                "message": "Authentication service temporarily unavailable",
                "type": "stytch_api",
            },
        )

    except ConfigurationError as e:
        logger.critical(f"Configuration error: {e.message}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_server_error",
                "message": "Authentication service misconfigured",
                "type": "configuration",
            },
        )

    except Exception as e:
        logger.error(f"Unexpected authentication error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_server_error",
                "message": "An unexpected error occurred during authentication",
                "type": "unknown",
            },
        )


async def verify_auth_optional(
    request: Request, token: Optional[str] = Depends(security)
) -> Optional[StytchContext]:
    """
    Optional authentication dependency for FastAPI.

    Similar to verify_auth but returns None instead of raising an exception
    when authentication fails. Useful for endpoints that work with or without
    authentication.

    Usage:
        @app.get("/optional-auth")
        async def optional_route(user: Optional[StytchContext] = Depends(verify_auth_optional)):
            if user:
                return {"message": f"Hello {user.member_email}"}
            else:
                return {"message": "Hello anonymous user"}

    Args:
        request: FastAPI Request object
        token: Optional token from HTTPBearer

    Returns:
        StytchContext if authentication succeeds, None otherwise
    """
    try:
        return await verify_auth(request, token)
    except HTTPException:
        # Log the failure but don't raise
        logger.debug("Optional authentication failed, continuing without auth")
        return None


def create_auth_dependency(
    required_claims: Optional[List[str]] = None,
    required_factors: Optional[List[str]] = None,
) -> Callable:
    """
    Create a custom authentication dependency with additional requirements.

    This factory function allows you to create authentication dependencies
    with specific requirements beyond basic token verification.

    Args:
        required_claims: List of custom claims that must be present
        required_factors: List of authentication factors that must be present

    Returns:
        FastAPI dependency function

    Usage:
        admin_auth = create_auth_dependency(required_claims=["admin"])

        @app.get("/admin")
        async def admin_route(user: StytchContext = Depends(admin_auth)):
            return {"message": "Admin access granted"}
    """

    async def custom_verify_auth(
        request: Request, token: Optional[str] = Depends(security)
    ) -> StytchContext:
        # First, perform standard authentication
        stytch_context = await verify_auth(request, token)

        # Check custom claims if required
        if required_claims:
            user_claims = stytch_context.session_custom_claims
            missing_claims = [
                claim for claim in required_claims if claim not in user_claims
            ]
            if missing_claims:
                logger.warning(
                    f"User missing required claims: {missing_claims}",
                    extra={"member_id": stytch_context.member_id},
                )
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "insufficient_permissions",
                        "message": f"Missing required claims: {missing_claims}",
                        "type": "authorization",
                    },
                )

        # Check authentication factors if required
        if required_factors:
            user_factors = stytch_context.authentication_factors
            missing_factors = [
                factor for factor in required_factors if factor not in user_factors
            ]
            if missing_factors:
                logger.warning(
                    f"User missing required auth factors: {missing_factors}",
                    extra={"member_id": stytch_context.member_id},
                )
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "insufficient_authentication",
                        "message": f"Missing required authentication factors: {missing_factors}",
                        "type": "authorization",
                    },
                )

        return stytch_context

    return custom_verify_auth
