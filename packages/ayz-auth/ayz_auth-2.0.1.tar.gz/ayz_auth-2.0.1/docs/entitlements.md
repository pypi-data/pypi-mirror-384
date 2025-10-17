# Entitlements and Team Context Guide

This guide covers the entitlements and team context features introduced in ayz-auth v2.0.0.

## Overview

Version 2.0.0 adds support for:
- **Organization Entitlements**: Feature-based authorization using subscription tiers and entitlements
- **Team Context**: User team membership and filtering capabilities
- **MongoDB Integration**: Optional read-only access to organization, user, and team data
- **Intelligent Caching**: Two-tier caching strategy for optimal performance

## Table of Contents

1. [Setup](#setup)
2. [MongoDB Collections](#mongodb-collections)
3. [Enhanced StytchContext](#enhanced-stytchcontext)
4. [Authorization Decorators](#authorization-decorators)
5. [Caching Strategy](#caching-strategy)
6. [Usage Examples](#usage-examples)
7. [Error Handling](#error-handling)
8. [Performance](#performance)

## Setup

### 1. Install with MongoDB Support

```bash
pip install 'ayz-auth[mongodb]'
```

This installs the optional MongoDB dependencies (`motor` and `pymongo`).

### 2. Configure MongoDB Connection

Add the MongoDB connection string to your environment:

```bash
# Required for entitlements features
STYTCH_MONGODB_URI=mongodb://localhost:27017/soulmates

# Existing required variables
STYTCH_PROJECT_ID=your_project_id
STYTCH_SECRET=your_secret_key
STYTCH_ENV=test
REDIS_URL=redis://localhost:6379
```

**Note**: If `STYTCH_MONGODB_URI` is not set, the package will work in backwards-compatible mode (v1.x behavior) with all entitlements fields set to `None`.

### 3. Backwards Compatibility

The entitlements features are **100% backwards compatible**:
- MongoDB dependencies are optional
- Package works without `STYTCH_MONGODB_URI` configured
- Existing v1.x code requires no changes
- New StytchContext fields default to `None`

## MongoDB Collections

The package requires **read-only** access to three MongoDB collections:

### `organizations` Collection

Stores organization subscription and entitlements data:

```javascript
{
    "_id": ObjectId("..."),
    "stytch_org_id": "organization-live-...",  // Used for queries
    "subscription_tier": "premium",  // "free" | "standard" | "premium" | "enterprise"
    "entitlements": ["foresight", "byod", "resonance_reports"],
    "subscription_limits": {
        "max_projects": 50,
        "max_users": 100,
        "max_queries_per_month": 10000
    }
}
```

### `users` Collection

Stores user context and team membership:

```javascript
{
    "_id": ObjectId("..."),
    "stytch_member_id": "member-live-...",  // Used for queries
    "current_team_id": ObjectId("...")  // Reference to teams collection
}
```

### `teams` Collection

Stores team information:

```javascript
{
    "_id": ObjectId("..."),
    "name": "Engineering Team",
    "organization_id": ObjectId("...")
}
```

## Enhanced StytchContext

The `StytchContext` model now includes entitlements and team data:

```python
class StytchContext(BaseModel):
    # Existing v1.x fields (unchanged)
    member_id: str
    session_id: str
    organization_id: str
    member_email: Optional[str]
    member_name: Optional[str]
    session_expires_at: datetime
    # ... other existing fields

    # New v2.0.0 fields (all optional, None if MongoDB not configured)

    # Organization entitlements
    entitlements: Optional[List[str]] = None  # e.g., ["foresight", "byod"]
    subscription_tier: Optional[str] = None  # "free" | "standard" | "premium" | "enterprise"
    subscription_limits: Optional[Dict[str, int]] = None  # {"max_projects": 50, ...}

    # Team context
    current_team_id: Optional[str] = None  # MongoDB ObjectId as string
    current_team_name: Optional[str] = None

    # MongoDB identifiers
    mongo_user_id: Optional[str] = None  # MongoDB user document ID
    mongo_organization_id: Optional[str] = None  # MongoDB org document ID
```

## Authorization Decorators

Three new decorators for entitlement-based authorization:

### `require_entitlement(entitlement)`

Requires a single specific entitlement:

```python
from fastapi import Depends, FastAPI
from ayz_auth import require_entitlement, StytchContext

app = FastAPI()

@app.get("/foresight/analyze")
async def analyze_endpoint(user: StytchContext = Depends(require_entitlement("foresight"))):
    return {
        "status": "ok",
        "team": user.current_team_name,
        "tier": user.subscription_tier
    }
```

### `require_any_entitlement(*entitlements)`

Requires at least ONE of the specified entitlements:

```python
from ayz_auth import require_any_entitlement

@app.get("/analytics")
async def analytics(user: StytchContext = Depends(require_any_entitlement("foresight", "analytics_basic"))):
    # User has "foresight" OR "analytics_basic"
    return {"message": "Analytics dashboard"}
```

### `require_all_entitlements(*entitlements)`

Requires ALL of the specified entitlements:

```python
from ayz_auth import require_all_entitlements

@app.get("/premium-features")
async def premium(user: StytchContext = Depends(require_all_entitlements("foresight", "advanced_analytics"))):
    # User has both "foresight" AND "advanced_analytics"
    return {"message": "Premium features"}
```

## Caching Strategy

The package uses a two-tier caching strategy with different TTLs:

### Organization Entitlements Cache

- **Cache Key**: `ayz_auth:entitlements:org:{stytch_org_id}`
- **TTL**: 1 hour (3600 seconds)
- **Data**: subscription_tier, entitlements, subscription_limits, mongo_organization_id
- **Rationale**: Organization entitlements change infrequently

### User Context Cache

- **Cache Key**: `ayz_auth:user_context:{stytch_member_id}`
- **TTL**: 5 minutes (300 seconds)
- **Data**: current_team_id, current_team_name, mongo_user_id
- **Rationale**: Users may switch teams more frequently

### Token Verification Cache

- **Cache Key**: `ayz_auth:token:{token_hash}`
- **TTL**: 5 minutes (300 seconds)
- **Data**: Complete StytchContext with all entitlements and team data
- **Rationale**: Token validation is expensive, but tokens may be revoked

## Usage Examples

### Basic Entitlement Check

```python
from fastapi import Depends
from ayz_auth import verify_auth, StytchContext

@app.get("/api/feature")
async def feature_endpoint(user: StytchContext = Depends(verify_auth)):
    # Manual entitlement check
    if user.entitlements and "premium_feature" in user.entitlements:
        # Enable premium features
        return {"status": "premium"}
    else:
        return {"status": "basic"}
```

### Team-Based Data Filtering

```python
@app.get("/api/projects")
async def list_projects(user: StytchContext = Depends(verify_auth)):
    # Filter projects by current team
    if user.current_team_id:
        projects = await db.projects.find({"team_id": user.current_team_id}).to_list()
    else:
        # Fall back to user's own projects
        projects = await db.projects.find({"user_id": user.mongo_user_id}).to_list()

    return {"projects": projects}
```

### Subscription Limits Check

```python
@app.post("/api/projects")
async def create_project(user: StytchContext = Depends(verify_auth)):
    # Check subscription limits
    if user.subscription_limits:
        max_projects = user.subscription_limits.get("max_projects", 0)
        current_count = await db.projects.count_documents(
            {"organization_id": user.mongo_organization_id}
        )

        if max_projects != -1 and current_count >= max_projects:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "limit_exceeded",
                    "message": f"Project limit reached ({max_projects})",
                    "current_tier": user.subscription_tier,
                    "upgrade_required": True
                }
            )

    # Create project...
    return {"status": "created"}
```

### Frontend Feature Toggles

```python
@app.get("/api/user/features")
async def get_user_features(user: StytchContext = Depends(verify_auth)):
    """
    Return feature flags for frontend to show/hide features.
    """
    return {
        "entitlements": user.entitlements or [],
        "subscription_tier": user.subscription_tier,
        "features": {
            "foresight": "foresight" in (user.entitlements or []),
            "byod": "byod" in (user.entitlements or []),
            "advanced_analytics": "advanced_analytics" in (user.entitlements or []),
            "team_features": user.current_team_id is not None
        },
        "limits": user.subscription_limits or {}
    }
```

### Combined Authentication and Entitlement

```python
from ayz_auth import require_entitlement

# Create reusable dependency
foresight_required = require_entitlement("foresight")

@app.get("/foresight/dashboard")
async def foresight_dashboard(user: StytchContext = Depends(foresight_required)):
    # Authentication + entitlement check done by decorator
    return {"dashboard_data": "..."}
```

## Error Handling

### Entitlement Missing (403 Response)

When a user lacks the required entitlement:

```json
{
    "error": "forbidden",
    "message": "This feature requires the 'foresight' entitlement",
    "required_entitlement": "foresight",
    "current_tier": "standard",
    "upgrade_required": true
}
```

### Multiple Entitlements Missing

For `require_all_entitlements`:

```json
{
    "error": "forbidden",
    "message": "This feature requires all of: foresight, advanced_analytics",
    "required_entitlements": ["foresight", "advanced_analytics"],
    "missing_entitlements": ["advanced_analytics"],
    "current_tier": "premium",
    "upgrade_required": true
}
```

### MongoDB Not Configured

If entitlement decorators are used but MongoDB is not configured:

```json
{
    "error": "forbidden",
    "message": "Entitlements feature is not configured",
    "required_entitlement": "foresight",
    "current_tier": null,
    "upgrade_required": true
}
```

### Graceful Degradation

The package handles MongoDB failures gracefully:
- MongoDB connection errors: Log warning, continue with `None` values
- Redis unavailable: Skip cache, query MongoDB directly
- Collections missing: Log warning, set fields to `None`
- **Authentication never fails due to entitlements issues**

## Performance

### Performance Targets

- **Cached request** (warm): <10ms total
  - Stytch token verification: cached
  - Entitlements data: cached in Redis
  - User context: cached in Redis

- **Uncached request** (cold): <100ms total
  - Stytch API call: ~30-50ms
  - MongoDB queries (parallel): ~20-40ms
  - Redis writes: ~5-10ms

### Cache Hit Rate

Target cache hit rate: >95% in production

### Parallel Loading

Organization and user data are loaded in parallel using `asyncio.gather()` to minimize latency.

### Monitoring

Monitor these metrics:
- Cache hit rate for each cache type (token, org, user)
- MongoDB query latency
- Redis operation latency
- Overall authentication latency (p50, p95, p99)

## Best Practices

### 1. Use Entitlement Decorators

Prefer decorators over manual checks:

```python
# ✅ Good - Declarative and consistent
@app.get("/premium")
async def premium_route(user: StytchContext = Depends(require_entitlement("premium_feature"))):
    return {"status": "ok"}

# ❌ Avoid - Manual checks are error-prone
@app.get("/premium")
async def premium_route(user: StytchContext = Depends(verify_auth)):
    if not user.entitlements or "premium_feature" not in user.entitlements:
        raise HTTPException(status_code=403)
    return {"status": "ok"}
```

### 2. Handle None Values

Always check for `None` when using entitlements fields:

```python
# ✅ Safe
if user.entitlements and "feature" in user.entitlements:
    # Use feature

# ❌ Unsafe - may raise TypeError if entitlements is None
if "feature" in user.entitlements:
    # Use feature
```

### 3. Cache Invalidation

To invalidate caches after subscription changes:

```python
# Invalidate organization entitlements cache
await redis_client.delete(f"ayz_auth:entitlements:org:{stytch_org_id}")

# Invalidate user context cache
await redis_client.delete(f"ayz_auth:user_context:{stytch_member_id}")
```

### 4. Team Context for Multi-Tenancy

Use team context for data isolation:

```python
# Filter all queries by team
query = {"team_id": user.current_team_id} if user.current_team_id else {"user_id": user.mongo_user_id}
results = await db.collection.find(query).to_list()
```

### 5. Subscription Limits

Check limits before expensive operations:

```python
# Check limit before starting expensive task
if user.subscription_limits:
    max_queries = user.subscription_limits.get("max_queries_per_month", 0)
    # Check current usage against limit
```

## Troubleshooting

### Entitlements Always None

**Cause**: MongoDB not configured or connection failed

**Solution**:
1. Verify `STYTCH_MONGODB_URI` is set correctly
2. Check MongoDB connection: `mongosh <uri>`
3. Install MongoDB dependencies: `pip install 'ayz-auth[mongodb]'`
4. Check logs for MongoDB connection errors

### Stale Entitlements Data

**Cause**: Caches not invalidated after subscription changes

**Solution**:
1. Manually invalidate Redis caches (see cache invalidation above)
2. Wait for TTL expiration (1 hour for org, 5 minutes for user)
3. Implement cache invalidation in subscription update workflows

### Performance Issues

**Cause**: Low cache hit rate or MongoDB latency

**Solution**:
1. Monitor cache hit rates in Redis
2. Ensure Redis is healthy and responsive
3. Add MongoDB indexes: `stytch_org_id`, `stytch_member_id`
4. Check MongoDB query performance with `.explain()`

### 403 Errors Despite Valid Entitlements

**Cause**: Case sensitivity or typos in entitlement names

**Solution**:
1. Verify exact entitlement strings match MongoDB data
2. Entitlement checks are case-sensitive
3. Check decorator spelling: `require_entitlement("foresight")`

## Migration from v1.x

See [docs/migration-v2.md](./migration-v2.md) for detailed upgrade instructions.

## Support

For issues or questions:
- GitHub Issues: https://github.com/ayzenberg/ayz-auth/issues
- Check logs for warning messages about entitlements loading
- Ensure backwards compatibility by testing without MongoDB configured
