"""
Decorators for entitlement-based authorization.

Provides FastAPI dependencies for enforcing feature entitlements on routes.
"""

from typing import Callable

from fastapi import Depends, HTTPException

from .middleware import verify_auth
from .models.context import StytchContext
from .utils.logger import logger


def require_entitlement(entitlement: str) -> Callable:
    """
    Create a FastAPI dependency that requires a specific entitlement.

    This decorator checks if the authenticated user's organization has the
    required entitlement. If not, it returns a 403 Forbidden response with
    details about the missing entitlement.

    Args:
        entitlement: The entitlement name required (e.g., "foresight", "byod")

    Returns:
        FastAPI dependency function that verifies entitlement

    Usage:
        Option A - Route-level dependency (no context needed in endpoint):
        ```python
        from fastapi import Depends
        from ayz_auth import require_entitlement

        @app.get("/api/foresight/analyze", dependencies=[Depends(require_entitlement("foresight"))])
        async def analyze_endpoint():
            return {"status": "ok"}
        ```

        Option B - Inject user context in endpoint:
        ```python
        from fastapi import Depends
        from ayz_auth import require_entitlement, StytchContext

        foresight_auth = require_entitlement("foresight")

        @app.get("/api/foresight/analyze")
        async def analyze_endpoint(user: StytchContext = Depends(foresight_auth)):
            return {"status": "ok", "team": user.current_team_name}
        ```
    """

    async def entitlement_dependency(
        user: StytchContext = Depends(verify_auth),
    ) -> StytchContext:
        """
        Verify that the user has the required entitlement.

        Args:
            user: Authenticated user context from verify_auth

        Returns:
            StytchContext if entitlement check passes

        Raises:
            HTTPException: 403 if entitlement is missing
        """
        # Check if entitlements are available (MongoDB must be configured)
        if user.entitlements is None:
            logger.warning(
                f"Entitlements check attempted but entitlements not loaded. "
                f"Ensure the configured MongoDB URI (settings.mongodb_uri) is set. "
                f"Member: {user.member_id}, Required entitlement: {entitlement}"
            )
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "forbidden",
                    "message": "Entitlements feature is not configured",
                    "required_entitlement": entitlement,
                    "current_tier": None,
                    "upgrade_required": True,
                },
            )

        # Check if user has the required entitlement
        if entitlement not in user.entitlements:
            logger.warning(
                f"Entitlement check failed for member: {user.member_id}. "
                f"Required: '{entitlement}', Available: {user.entitlements}"
            )
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "forbidden",
                    "message": f"This feature requires the '{entitlement}' entitlement",
                    "required_entitlement": entitlement,
                    "current_tier": user.subscription_tier,
                    "upgrade_required": True,
                },
            )

        # Entitlement check passed
        logger.debug(
            f"Entitlement check passed for member: {user.member_id}. "
            f"Required: '{entitlement}'"
        )
        return user

    return entitlement_dependency


def require_any_entitlement(*entitlements: str) -> Callable:
    """
    Create a FastAPI dependency that requires ANY of the specified entitlements.

    The user must have at least one of the specified entitlements to access the route.

    Args:
        *entitlements: Variable number of entitlement names (e.g., "foresight", "byod")

    Returns:
        FastAPI dependency function that verifies entitlements

    Usage:
        ```python
        from fastapi import Depends
        from ayz_auth import require_any_entitlement

        @app.get("/api/analytics", dependencies=[Depends(require_any_entitlement("foresight", "analytics_basic"))])
        async def analytics_endpoint():
            return {"status": "ok"}
        ```
    """

    async def any_entitlement_dependency(
        user: StytchContext = Depends(verify_auth),
    ) -> StytchContext:
        """Verify that the user has at least one of the required entitlements."""
        # Check if entitlements are available
        if user.entitlements is None:
            logger.warning(
                f"Entitlements check attempted but entitlements not loaded. "
                f"Ensure the configured MongoDB URI (settings.mongodb_uri) is set. "
                f"Member: {user.member_id}, Required entitlements: {entitlements}"
            )
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "forbidden",
                    "message": "Entitlements feature is not configured",
                    "required_entitlements": list(entitlements),
                    "current_tier": None,
                    "upgrade_required": True,
                },
            )

        # Check if user has at least one of the required entitlements
        user_has_entitlement = any(ent in user.entitlements for ent in entitlements)

        if not user_has_entitlement:
            logger.warning(
                f"Entitlement check failed for member: {user.member_id}. "
                f"Required (any of): {entitlements}, Available: {user.entitlements}"
            )
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "forbidden",
                    "message": f"This feature requires one of: {', '.join(entitlements)}",
                    "required_entitlements": list(entitlements),
                    "current_tier": user.subscription_tier,
                    "upgrade_required": True,
                },
            )

        # Entitlement check passed
        logger.debug(
            f"Entitlement check passed for member: {user.member_id}. "
            f"Required (any of): {entitlements}"
        )
        return user

    return any_entitlement_dependency


def require_all_entitlements(*entitlements: str) -> Callable:
    """
    Create a FastAPI dependency that requires ALL of the specified entitlements.

    The user must have all specified entitlements to access the route.

    Args:
        *entitlements: Variable number of entitlement names (e.g., "foresight", "byod")

    Returns:
        FastAPI dependency function that verifies entitlements

    Usage:
        ```python
        from fastapi import Depends
        from ayz_auth import require_all_entitlements

        @app.get("/api/premium-analytics", dependencies=[Depends(require_all_entitlements("foresight", "advanced_analytics"))])
        async def premium_analytics_endpoint():
            return {"status": "ok"}
        ```
    """

    async def all_entitlements_dependency(
        user: StytchContext = Depends(verify_auth),
    ) -> StytchContext:
        """Verify that the user has all of the required entitlements."""
        # Check if entitlements are available
        if user.entitlements is None:
            logger.warning(
                f"Entitlements check attempted but entitlements not loaded. "
                f"Ensure the configured MongoDB URI (settings.mongodb_uri) is set. "
                f"Member: {user.member_id}, Required entitlements: {entitlements}"
            )
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "forbidden",
                    "message": "Entitlements feature is not configured",
                    "required_entitlements": list(entitlements),
                    "current_tier": None,
                    "upgrade_required": True,
                },
            )

        # Check if user has all of the required entitlements
        missing_entitlements = [
            ent for ent in entitlements if ent not in user.entitlements
        ]

        if missing_entitlements:
            logger.warning(
                f"Entitlement check failed for member: {user.member_id}. "
                f"Missing: {missing_entitlements}, Available: {user.entitlements}"
            )
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "forbidden",
                    "message": f"This feature requires all of: {', '.join(entitlements)}",
                    "required_entitlements": list(entitlements),
                    "missing_entitlements": missing_entitlements,
                    "current_tier": user.subscription_tier,
                    "upgrade_required": True,
                },
            )

        # Entitlement check passed
        logger.debug(
            f"Entitlement check passed for member: {user.member_id}. "
            f"Required (all of): {entitlements}"
        )
        return user

    return all_entitlements_dependency
