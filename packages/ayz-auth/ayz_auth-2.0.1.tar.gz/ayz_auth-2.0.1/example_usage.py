"""
Example usage of the ayz-auth package.

This demonstrates how to integrate the authentication middleware into a FastAPI application.
"""

from typing import Optional

from fastapi import Depends, FastAPI

from ayz_auth import (
    StytchContext,
    create_auth_dependency,
    require_all_entitlements,
    require_any_entitlement,
    require_entitlement,
    verify_auth,
    verify_auth_optional,
)

# Create FastAPI app
app = FastAPI(title="Example API with Stytch Authentication")

# Create custom auth dependencies
admin_auth = create_auth_dependency(required_claims=["admin"])
mfa_auth = create_auth_dependency(required_factors=["mfa"])

# Create entitlement-based dependencies (v2.0.0+)
foresight_auth = require_entitlement("foresight")
byod_auth = require_entitlement("byod")
analytics_auth = require_any_entitlement("foresight", "analytics_basic")
premium_auth = require_all_entitlements("foresight", "advanced_analytics")


@app.get("/")
async def root():
    """Public endpoint - no authentication required."""
    return {
        "message": "Welcome to the API! Use /protected for authenticated endpoints."
    }


@app.get("/protected")
async def protected_route(user: StytchContext = Depends(verify_auth)):
    """Protected endpoint requiring authentication."""
    return {
        "message": f"Hello {user.member_email}!",
        "member_id": user.member_id,
        "organization_id": user.organization_id,
        "session_expires_at": user.session_expires_at.isoformat(),
    }


@app.get("/optional-auth")
async def optional_auth_route(
    user: Optional[StytchContext] = Depends(verify_auth_optional),
):
    """Endpoint that works with or without authentication."""
    if user:
        return {
            "authenticated": True,
            "message": f"Hello {user.member_email}!",
            "member_id": user.member_id,
        }
    else:
        return {
            "authenticated": False,
            "message": "Hello anonymous user!",
        }


@app.get("/admin")
async def admin_route(user: StytchContext = Depends(admin_auth)):
    """Admin-only endpoint requiring 'admin' claim."""
    return {
        "message": "Admin access granted!",
        "member_id": user.member_id,
        "admin_claims": user.session_custom_claims,
    }


@app.get("/secure")
async def secure_route(user: StytchContext = Depends(mfa_auth)):
    """Secure endpoint requiring MFA authentication."""
    return {
        "message": "MFA verified access granted!",
        "member_id": user.member_id,
        "auth_factors": user.authentication_factors,
    }


@app.get("/user-profile")
async def get_user_profile(user: StytchContext = Depends(verify_auth)):
    """
    Example of how to integrate with your own user system.

    The middleware provides Stytch session data, and you use the member_id
    to fetch your own user data from your database.
    """
    # In a real application, you would:
    # user_data = await get_user_by_stytch_member_id(user.member_id)
    #
    # For this example, we'll simulate it:
    simulated_user_data = {
        "user_id": "user_123",
        "name": "John Doe",
        "email": user.member_email,
        "roles": ["user", "editor"],
        "permissions": ["read", "write"],
        "preferences": {
            "theme": "dark",
            "notifications": True,
        },
    }

    return {
        "stytch_session": {
            "member_id": user.member_id,
            "organization_id": user.organization_id,
            "session_expires_at": user.session_expires_at.isoformat(),
        },
        "user_profile": simulated_user_data,
    }


# ============================================================================
# Entitlement-based Authorization Examples (v2.0.0+)
# ============================================================================


@app.get("/foresight/analyze")
async def foresight_analyze(user: StytchContext = Depends(foresight_auth)):
    """
    Example of entitlement-based authorization.

    Requires the 'foresight' entitlement to access.
    """
    return {
        "message": "Foresight analysis endpoint",
        "member_id": user.member_id,
        "entitlements": user.entitlements,
        "subscription_tier": user.subscription_tier,
        "current_team": user.current_team_name,
    }


@app.get("/byod/upload")
async def byod_upload(user: StytchContext = Depends(byod_auth)):
    """
    BYOD (Bring Your Own Data) endpoint.

    Requires the 'byod' entitlement to access.
    """
    return {
        "message": "BYOD upload endpoint",
        "member_id": user.member_id,
        "current_team_id": user.current_team_id,
        "subscription_limits": user.subscription_limits,
    }


@app.get("/analytics/dashboard")
async def analytics_dashboard(user: StytchContext = Depends(analytics_auth)):
    """
    Analytics dashboard - requires ANY of the analytics entitlements.

    Users with 'foresight' OR 'analytics_basic' can access.
    """
    return {
        "message": "Analytics dashboard",
        "member_id": user.member_id,
        "entitlements": user.entitlements,
        "tier": user.subscription_tier,
    }


@app.get("/premium/advanced-analytics")
async def premium_analytics(user: StytchContext = Depends(premium_auth)):
    """
    Premium analytics - requires ALL specified entitlements.

    Users must have both 'foresight' AND 'advanced_analytics'.
    """
    return {
        "message": "Premium advanced analytics",
        "member_id": user.member_id,
        "entitlements": user.entitlements,
        "mongo_org_id": user.mongo_organization_id,
    }


@app.get("/team/projects")
async def team_projects(user: StytchContext = Depends(verify_auth)):
    """
    Example of using team context for data filtering.

    In a real application, you would filter results by team_id.
    """
    # In a real application:
    # if user.current_team_id:
    #     projects = await db.projects.find({"team_id": user.current_team_id})
    # else:
    #     projects = await db.projects.find({"user_id": user.mongo_user_id})

    return {
        "message": "Team projects endpoint",
        "current_team": {
            "id": user.current_team_id,
            "name": user.current_team_name,
        },
        "subscription": {
            "tier": user.subscription_tier,
            "limits": user.subscription_limits,
        },
    }


@app.get("/entitlements/check")
async def check_entitlements(user: StytchContext = Depends(verify_auth)):
    """
    Check what entitlements the current user has.

    Useful for frontend feature toggles and UI customization.
    """
    return {
        "member_id": user.member_id,
        "organization_id": user.organization_id,
        "entitlements": user.entitlements or [],
        "subscription_tier": user.subscription_tier,
        "subscription_limits": user.subscription_limits,
        "current_team": {
            "id": user.current_team_id,
            "name": user.current_team_name,
        },
        "mongo_ids": {
            "user_id": user.mongo_user_id,
            "organization_id": user.mongo_organization_id,
        },
    }


if __name__ == "__main__":
    import uvicorn

    print("Starting example API server...")
    print("Make sure to set these environment variables:")
    print("  STYTCH_PROJECT_ID=your_project_id")
    print("  STYTCH_SECRET=your_secret_key")
    print("  STYTCH_REDIS_URL=redis://localhost:6379  # optional")
    print(
        "  STYTCH_MONGODB_URI=mongodb://localhost:27017/soulmates  # optional (v2.0.0+)"
    )
    print()
    print("Example requests:")
    print("  GET /                    # Public endpoint")
    print("  GET /protected           # Requires: Authorization: Bearer <token>")
    print("  GET /optional-auth       # Works with or without auth")
    print("  GET /admin               # Requires 'admin' claim")
    print("  GET /secure              # Requires MFA")
    print("  GET /user-profile        # Shows integration pattern")
    print()
    print("Entitlement examples (v2.0.0+ - requires MongoDB):")
    print("  GET /foresight/analyze   # Requires 'foresight' entitlement")
    print("  GET /byod/upload         # Requires 'byod' entitlement")
    print("  GET /analytics/dashboard # Requires ANY of: foresight, analytics_basic")
    print(
        "  GET /premium/advanced-analytics  # Requires ALL of: foresight, advanced_analytics"
    )
    print("  GET /team/projects       # Shows team context usage")
    print("  GET /entitlements/check  # Check current user's entitlements")
    print()

    uvicorn.run(app, host="0.0.0.0", port=8000)
