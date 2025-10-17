# ayz-auth Package Enhancement: Add Entitlements and Team Context Support

## Overview
Enhance the `ayz-auth` FastAPI Python authentication package to support organization entitlements and user team context. This package is published to PyPI and used by multiple FastAPI microservices. The enhancement must maintain **100% backwards compatibility** with existing implementations.

## Current State
- Package validates Stytch B2B session tokens
- Returns session data with user/org identifiers from Stytch
- No MongoDB or Redis integration
- No entitlements enforcement

## Required Changes

### 1. Add New Dependencies
Add optional dependencies to `pyproject.toml`:
- `pymongo` (for MongoDB connection)
- `redis` (for caching layer)
- `motor` (async MongoDB driver, if using async patterns)

Make these **optional dependencies** so existing users without MongoDB/Redis can continue using the package.

### 2. Configuration
Add new optional environment variables:
- `MONGODB_URI` - MongoDB connection string (read-only access required)
- `REDIS_URL` - Redis connection string (optional but recommended)

If these are not provided, package should work exactly as before (backwards compatible).

### 3. MongoDB Collections Access
Package needs **read-only** access to three collections:

#### `organizations` collection:
```python
{
    "_id": ObjectId,
    "stytch_org_id": str,  # Use this to query by Stytch org ID
    "subscription_tier": str,  # "free" | "standard" | "premium" | "enterprise"
    "entitlements": [str],  # e.g., ["foresight", "byod", "resonance_reports"]
    "subscription_limits": {
        "max_projects": int,  # -1 = unlimited
        "max_users": int,
        "max_queries_per_month": int
    }
}
```

#### `users` collection:
```python
{
    "_id": ObjectId,
    "stytch_member_id": str,  # Use this to query by Stytch member ID
    "current_team_id": ObjectId | None  # Reference to teams collection
}
```

#### `teams` collection:
```python
{
    "_id": ObjectId,
    "name": str,
    "organization_id": ObjectId
}
```

### 4. Enhanced SessionData Object
Extend the existing `SessionData` class/object with these new fields:

```python
class SessionData:
    # Existing fields (keep all current fields)
    # ... (stytch_member_id, stytch_org_id, etc.)

    # New fields (all optional for backwards compatibility):
    entitlements: List[str] | None = None
    subscription_tier: str | None = None  # "free" | "standard" | "premium" | "enterprise"
    subscription_limits: dict | None = None  # {max_projects, max_users, max_queries_per_month}
    current_team_id: str | None = None  # MongoDB ObjectId as string
    current_team_name: str | None = None
    mongo_user_id: str | None = None  # MongoDB ObjectId as string
    mongo_organization_id: str | None = None  # MongoDB ObjectId as string
```

### 5. Data Loading Flow
After Stytch session validation succeeds:

1. **Load organization entitlements** (if MongoDB configured):
   - Query `organizations` collection by `stytch_org_id` (from Stytch session)
   - Extract: `subscription_tier`, `entitlements`, `subscription_limits`, `_id` (as mongo_organization_id)
   - Cache in Redis with key: `entitlements:org:{stytch_org_id}` (1-hour TTL)

2. **Load user context** (if MongoDB configured):
   - Query `users` collection by `stytch_member_id` (from Stytch session)
   - Extract: `current_team_id`, `_id` (as mongo_user_id)
   - Cache in Redis with key: `user_context:{stytch_member_id}` (5-minute TTL)

3. **Load team details** (if `current_team_id` is not null):
   - Query `teams` collection by `_id` = `current_team_id`
   - Extract: `name` (as current_team_name)
   - Include in user_context cache

### 6. Caching Strategy
Use **two separate cache keys** with different TTLs:

```python
# Organization entitlements cache (1-hour TTL)
cache_key = f"entitlements:org:{stytch_org_id}"
# Stores: {subscription_tier, entitlements, subscription_limits, mongo_organization_id}

# User context cache (5-minute TTL)
cache_key = f"user_context:{stytch_member_id}"
# Stores: {current_team_id, current_team_name, mongo_user_id}
```

**Important**: Check Redis cache first before querying MongoDB. This is critical for performance (<10ms cached requests vs ~50-100ms uncached).

### 7. New Decorator: `@require_entitlement()`
Create a FastAPI route decorator for entitlement enforcement:

```python
from ayz_auth import require_entitlement

@app.get("/api/foresight/analyze")
@require_entitlement("foresight")
async def analyze_endpoint(request: Request):
    # Access session data
    session = request.state.session
    # session.entitlements contains ["foresight", ...]
    # session.current_team_id can be used for filtering
    return {"status": "ok"}
```

**Decorator behavior**:
- Check if entitlement exists in `session.entitlements`
- If missing, raise `HTTPException(status_code=403, detail={...})`
- 403 response should include structured error:
  ```python
  {
      "error": "forbidden",
      "message": "This feature requires the 'foresight' entitlement",
      "required_entitlement": "foresight",
      "current_tier": session.subscription_tier,
      "upgrade_required": True
  }
  ```

### 8. Error Handling & Graceful Degradation
- If MongoDB connection fails: log warning, set all new fields to `None`, continue (backwards compatible)
- If Redis unavailable: skip cache, query MongoDB directly (acceptable performance degradation)
- If organizations/users collections missing: log warning, set fields to `None`
- Never break authentication if entitlements loading fails

### 9. Performance Requirements
- **Cached request** (warm): <10ms total (Stytch + Redis reads)
- **Uncached request** (cold): <100ms total (Stytch + MongoDB queries + Redis writes)
- **Cache hit rate target**: >95% in production

### 10. Testing Requirements
Include tests for:
- Backwards compatibility (package works without MongoDB/Redis env vars)
- MongoDB connection and queries (organizations, users, teams)
- Redis caching with correct TTLs (1hr and 5min)
- Cache invalidation and refresh
- `@require_entitlement()` decorator blocks unauthorized requests
- `@require_entitlement()` decorator allows authorized requests
- SessionData includes all new fields when MongoDB configured
- SessionData new fields are `None` when MongoDB not configured
- Graceful error handling (MongoDB/Redis failures)
- Performance benchmarks (cold vs warm requests)

### 11. Version and Publishing
- Bump version to **2.0.0** (major version due to new features, but backwards compatible)
- Update README.md with:
  - New environment variables
  - SessionData field documentation
  - `@require_entitlement()` decorator usage examples
  - Migration guide from 1.x to 2.x
- Publish to PyPI

### 12. Documentation Needed
Update or create:
- `README.md` - Feature overview and quick start
- `CHANGELOG.md` - Version 2.0.0 changes
- `docs/entitlements.md` - Detailed entitlements guide
- `docs/migration-v2.md` - Upgrade guide from v1.x
- Type hints and docstrings for all new functions

## Example Usage (After Package Upgrade)

```python
# In any FastAPI microservice
from fastapi import FastAPI, Request
from ayz_auth import require_authentication, require_entitlement

app = FastAPI()

# Existing route (no changes needed - backwards compatible)
@app.get("/api/public")
@require_authentication
async def public_endpoint(request: Request):
    session = request.state.session
    return {"user": session.stytch_member_id}

# New route with entitlement enforcement
@app.get("/api/foresight/analyze")
@require_authentication
@require_entitlement("foresight")
async def foresight_endpoint(request: Request):
    session = request.state.session

    # Access entitlements
    if "advanced_analytics" in session.entitlements:
        # Enable advanced features
        pass

    # Use current team for RAG filtering
    team_id = session.current_team_id
    if team_id:
        # Filter results by team
        results = db.query({"team_id": team_id})

    return {"status": "ok"}
```

## Critical Requirements
- ✅ **100% backwards compatible** - existing code must work without changes
- ✅ **Optional dependencies** - MongoDB/Redis not required for basic auth
- ✅ **Performance** - Cached requests <10ms, uncached <100ms
- ✅ **Security** - Never bypass Stytch validation, entitlements loaded after auth succeeds
- ✅ **Error handling** - Graceful degradation if MongoDB/Redis unavailable
- ✅ **Type safety** - Full type hints with mypy compliance
- ✅ **Testing** - Comprehensive unit and integration tests
- ✅ **Documentation** - Clear upgrade path and usage examples

## Success Criteria
- [ ] Package published to PyPI as version 2.0.0
- [ ] Existing Python services can upgrade with zero code changes
- [ ] `@require_entitlement()` decorator works correctly
- [ ] SessionData includes all new fields when MongoDB configured
- [ ] Redis caching reduces latency to <10ms
- [ ] All tests passing (unit, integration, performance)
- [ ] Documentation complete and clear

---

**Note**: This is a critical infrastructure package. Prioritize stability, backwards compatibility, and performance over feature richness.
