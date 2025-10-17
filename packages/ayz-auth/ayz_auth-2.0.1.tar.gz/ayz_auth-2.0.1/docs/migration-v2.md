# Migration Guide: v1.x to v2.0.0

This guide helps you upgrade from ayz-auth v1.x to v2.0.0.

## TL;DR - Minimal Breaking Changes

v2.0.0 is **99% backwards compatible** with v1.x. Most existing code will work without modifications.

**Breaking Change**: If you use `get_member_by_email()` for member search operations, you must now pass `organization_id` as a parameter.

To upgrade:
```bash
pip install --upgrade ayz-auth
# or
uv add ayz-auth@latest
```

**Action Required** (only if you use member search):
```python
# Before (v1.x):
member = await stytch_verifier.get_member_by_email(email)

# After (v2.0.0):
member = await stytch_verifier.get_member_by_email(email, user.organization_id)
```

## What's New in v2.0.0

### Core Features

1. **Organization Entitlements**: Feature-based authorization using subscription tiers
2. **Team Context**: User team membership for data filtering and multi-tenancy
3. **MongoDB Integration**: Optional read-only access to organization and user data
4. **Enhanced Caching**: Two-tier caching strategy (1hr for org, 5min for user context)
5. **New Decorators**: `require_entitlement`, `require_any_entitlement`, `require_all_entitlements`

### New StytchContext Fields

All new fields are optional and default to `None`:

```python
# Organization Entitlements (v2.0.0+)
entitlements: Optional[List[str]] = None
subscription_tier: Optional[str] = None
subscription_limits: Optional[Dict[str, int]] = None

# Team Context (v2.0.0+)
current_team_id: Optional[str] = None
current_team_name: Optional[str] = None

# MongoDB Identifiers (v2.0.0+)
mongo_user_id: Optional[str] = None
mongo_organization_id: Optional[str] = None
```

## Breaking Changes Detail

### Removed: `STYTCH_ORGANIZATION_ID` Environment Variable

**Why this change?**
- Multi-tenant applications should never hardcode a single organization ID in configuration
- Organization ID should always come from the authenticated user's session for proper tenant isolation
- This prevents potential security issues where operations could accidentally cross tenant boundaries

**Who is affected?**
- Only services using `get_member_by_email()` for member search operations
- Most services using only authentication/entitlements are **not affected**

**Migration steps**:

1. **Remove the environment variable** (if set):
   ```bash
   # Delete this line from your .env file:
   # STYTCH_ORGANIZATION_ID=organization-live-...
   ```

2. **Update `get_member_by_email()` calls**:
   ```python
   # ❌ Old way (v1.x):
   from ayz_auth.auth.stytch_verifier import stytch_verifier

   @app.post("/invite-member")
   async def invite_member(email: str):
       member = await stytch_verifier.get_member_by_email(email)
       # ...

   # ✅ New way (v2.0.0):
   from ayz_auth import verify_auth, StytchContext
   from ayz_auth.auth.stytch_verifier import stytch_verifier

   @app.post("/invite-member")
   async def invite_member(
       email: str,
       user: StytchContext = Depends(verify_auth)
   ):
       # Use authenticated user's organization
       member = await stytch_verifier.get_member_by_email(
           email, user.organization_id
       )
       # ...
   ```

3. **Benefits of the new approach**:
   - ✅ Proper multi-tenant isolation
   - ✅ No risk of cross-tenant data access
   - ✅ Explicit organization context in every operation
   - ✅ Works seamlessly with multiple organizations

## Migration Scenarios

### Scenario 1: Simple Upgrade (No Entitlements)

**Who**: Services that only need basic Stytch authentication (no MongoDB)

**Steps**:
1. Upgrade the package:
   ```bash
   pip install --upgrade ayz-auth
   ```
2. No code changes needed
3. New StytchContext fields will be `None`
4. Everything works exactly as before

**Testing**:
```python
@app.get("/protected")
async def protected_route(user: StytchContext = Depends(verify_auth)):
    # Works exactly as in v1.x
    return {
        "member_id": user.member_id,
        "email": user.member_email,
        # New fields are None
        "entitlements": user.entitlements,  # None
        "team": user.current_team_name,  # None
    }
```

### Scenario 2: Add Entitlements Support

**Who**: Services that want to use feature-based authorization

**Steps**:

1. Install with MongoDB support:
   ```bash
   pip install --upgrade 'ayz-auth[mongodb]'
   ```

2. Add MongoDB configuration:
   ```bash
   # .env
   STYTCH_MONGODB_URI=mongodb://localhost:27017/soulmates
   ```

3. Ensure MongoDB collections exist (see [MongoDB Setup](#mongodb-setup) below)

4. Start using entitlements decorators:
   ```python
   from ayz_auth import require_entitlement

   @app.get("/premium-feature")
   async def premium_route(user: StytchContext = Depends(require_entitlement("premium"))):
       return {"status": "ok"}
   ```

5. Access entitlements in existing endpoints:
   ```python
   @app.get("/dashboard")
   async def dashboard(user: StytchContext = Depends(verify_auth)):
       # Now populated if MongoDB is configured
       if user.entitlements and "advanced_analytics" in user.entitlements:
           return {"view": "advanced"}
       return {"view": "basic"}
   ```

### Scenario 3: Gradual Rollout

**Who**: Teams wanting to test entitlements in staging before production

**Steps**:

1. **Staging Environment**:
   ```bash
   # .env.staging
   STYTCH_MONGODB_URI=mongodb://staging-mongo:27017/soulmates
   ```

2. **Production Environment** (initially):
   ```bash
   # .env.production
   # STYTCH_MONGODB_URI not set - backwards compatible mode
   ```

3. Test in staging, then enable in production when ready:
   ```bash
   # .env.production (after testing)
   STYTCH_MONGODB_URI=mongodb://prod-mongo:27017/soulmates
   ```

4. Code works in both modes:
   ```python
   @app.get("/feature")
   async def feature_route(user: StytchContext = Depends(verify_auth)):
       # Safe check - works with or without MongoDB
       has_feature = user.entitlements and "feature" in user.entitlements

       if has_feature:
           return {"version": "premium"}
       return {"version": "basic"}
   ```

## MongoDB Setup

### 1. Collections Schema

Create or verify these collections exist in your MongoDB database:

#### `organizations` Collection

```javascript
db.organizations.createIndex({ "stytch_org_id": 1 }, { unique: true })

// Example document
db.organizations.insertOne({
    "stytch_org_id": "organization-live-...",
    "subscription_tier": "premium",
    "entitlements": ["foresight", "byod", "advanced_analytics"],
    "subscription_limits": {
        "max_projects": 50,
        "max_users": 100,
        "max_queries_per_month": 10000
    }
})
```

#### `users` Collection

```javascript
db.users.createIndex({ "stytch_member_id": 1 }, { unique: true })

// Example document
db.users.insertOne({
    "stytch_member_id": "member-live-...",
    "current_team_id": ObjectId("...")  // optional
})
```

#### `teams` Collection

```javascript
// Example document
db.teams.insertOne({
    "name": "Engineering Team",
    "organization_id": ObjectId("...")
})
```

### 2. Database User Permissions

The ayz-auth package only needs **read-only** access:

```javascript
// Create read-only user for ayz-auth
db.createUser({
    user: "ayz_auth_reader",
    pwd: "secure_password",
    roles: [
        { role: "read", db: "soulmates" }
    ]
})
```

Connection string:
```bash
STYTCH_MONGODB_URI=mongodb://ayz_auth_reader:secure_password@localhost:27017/soulmates
```

## Deployment Checklist

### Pre-Deployment

- [ ] Upgrade package in development: `pip install --upgrade 'ayz-auth[mongodb]'`
- [ ] Update `requirements.txt` or `pyproject.toml`
- [ ] Test without MongoDB configured (backwards compatibility)
- [ ] Set up MongoDB collections with proper indexes
- [ ] Create read-only MongoDB user for ayz-auth
- [ ] Test with MongoDB configured in staging
- [ ] Verify cache TTLs are appropriate (1hr org, 5min user)

### During Deployment

- [ ] Deploy code changes (no breaking changes)
- [ ] Set `STYTCH_MONGODB_URI` environment variable (if using entitlements)
- [ ] Verify MongoDB connectivity in logs
- [ ] Monitor Redis cache hit rates

### Post-Deployment Validation

- [ ] Test existing authenticated endpoints (should work unchanged)
- [ ] Test new entitlements decorators (if configured)
- [ ] Check logs for MongoDB connection status
- [ ] Verify performance metrics (cached <10ms, uncached <100ms)
- [ ] Test error handling (MongoDB unavailable scenario)

## Common Migration Patterns

### Pattern 1: Feature Flags

Replace manual feature flags with entitlements:

**Before (v1.x)**:
```python
@app.get("/premium-feature")
async def premium_feature(user: StytchContext = Depends(verify_auth)):
    # Manual database check
    org_settings = await db.organizations.find_one({"stytch_org_id": user.organization_id})
    if not org_settings or "premium" not in org_settings.get("features", []):
        raise HTTPException(status_code=403, detail="Premium subscription required")

    return {"data": "..."}
```

**After (v2.0.0)**:
```python
from ayz_auth import require_entitlement

@app.get("/premium-feature")
async def premium_feature(user: StytchContext = Depends(require_entitlement("premium"))):
    # Entitlement check handled by decorator
    return {"data": "..."}
```

### Pattern 2: Team-Based Filtering

Add team context to existing queries:

**Before (v1.x)**:
```python
@app.get("/projects")
async def list_projects(user: StytchContext = Depends(verify_auth)):
    # Organization-wide query
    projects = await db.projects.find({
        "organization_id": user.organization_id
    }).to_list()
    return {"projects": projects}
```

**After (v2.0.0)** with backwards compatibility:
```python
@app.get("/projects")
async def list_projects(user: StytchContext = Depends(verify_auth)):
    # Team-based filtering if available, otherwise organization-wide
    if user.current_team_id:
        query = {"team_id": user.current_team_id}
    else:
        query = {"organization_id": user.organization_id}

    projects = await db.projects.find(query).to_list()
    return {"projects": projects}
```

### Pattern 3: Subscription Limits

Replace manual limit checks:

**Before (v1.x)**:
```python
@app.post("/projects")
async def create_project(user: StytchContext = Depends(verify_auth)):
    org = await db.organizations.find_one({"stytch_org_id": user.organization_id})
    max_projects = org.get("max_projects", 5) if org else 5

    current_count = await db.projects.count_documents({
        "organization_id": user.organization_id
    })

    if current_count >= max_projects:
        raise HTTPException(status_code=403, detail="Project limit reached")

    # Create project...
```

**After (v2.0.0)**:
```python
@app.post("/projects")
async def create_project(user: StytchContext = Depends(verify_auth)):
    # Limits automatically loaded from MongoDB
    if user.subscription_limits:
        max_projects = user.subscription_limits.get("max_projects", 5)

        current_count = await db.projects.count_documents({
            "organization_id": user.mongo_organization_id
        })

        if max_projects != -1 and current_count >= max_projects:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "limit_exceeded",
                    "current_tier": user.subscription_tier
                }
            )

    # Create project...
```

## Testing Your Migration

### Unit Tests

Update test mocks to include new fields:

```python
# tests/test_my_endpoint.py
from ayz_auth.models.context import StytchContext

def create_test_user(**kwargs):
    defaults = {
        "member_id": "test_member",
        "organization_id": "test_org",
        # ... other required fields

        # v2.0.0 fields (optional)
        "entitlements": ["foresight", "byod"],
        "subscription_tier": "premium",
        "current_team_id": "team_123",
    }
    defaults.update(kwargs)
    return StytchContext(**defaults)

# Test with entitlements
user_with_entitlements = create_test_user(entitlements=["premium_feature"])

# Test without entitlements (backwards compatibility)
user_without_entitlements = create_test_user(entitlements=None)
```

### Integration Tests

Test both modes:

```python
import pytest

@pytest.mark.integration
def test_with_mongodb_configured():
    """Test with STYTCH_MONGODB_URI set"""
    # Assert entitlements are loaded
    assert user.entitlements is not None
    assert user.subscription_tier is not None

@pytest.mark.integration
def test_without_mongodb_configured():
    """Test without STYTCH_MONGODB_URI (backwards compatibility)"""
    # Assert entitlements are None but auth works
    assert user.entitlements is None
    assert user.subscription_tier is None
    assert user.member_id is not None  # Core auth still works
```

## Rollback Plan

If you need to rollback to v1.x:

1. **Code rollback** (not needed - v2.0.0 is backwards compatible):
   ```bash
   pip install ayz-auth==1.0.0
   ```

2. **Remove MongoDB configuration** (optional):
   ```bash
   # Comment out or remove
   # STYTCH_MONGODB_URI=...
   ```

3. **No data migration needed** - MongoDB collections can remain as-is

## Performance Considerations

### Cache Hit Rates

Monitor Redis cache performance:

```python
# Check cache keys
redis-cli KEYS "ayz_auth:entitlements:org:*"
redis-cli KEYS "ayz_auth:user_context:*"

# Check TTLs
redis-cli TTL "ayz_auth:entitlements:org:organization-live-abc123"
redis-cli TTL "ayz_auth:user_context:member-live-xyz789"
```

### MongoDB Indexes

Ensure indexes exist for performance:

```javascript
// Critical indexes
db.organizations.createIndex({ "stytch_org_id": 1 })
db.users.createIndex({ "stytch_member_id": 1 })
db.teams.createIndex({ "_id": 1 })  // default index
```

### Expected Latency

- **v1.x baseline**: 5-30ms (Stytch + Redis)
- **v2.0.0 cached**: 5-30ms (same as v1.x - no additional overhead)
- **v2.0.0 uncached**: 30-100ms (includes MongoDB queries)
- **Target cache hit rate**: >95%

## Troubleshooting

### Issue: Entitlements are always None

**Cause**: MongoDB not configured or connection failed

**Solution**:
- Verify `STYTCH_MONGODB_URI` is set
- Check MongoDB is accessible: `mongosh <uri>`
- Install MongoDB dependencies: `pip install 'ayz-auth[mongodb]'`
- Check application logs for MongoDB connection errors

### Issue: Performance degradation after upgrade

**Cause**: Low cache hit rate or MongoDB latency

**Solution**:
- Check Redis is healthy: `redis-cli PING`
- Monitor MongoDB query performance
- Verify indexes exist on MongoDB collections
- Review cache TTL settings

### Issue: Tests failing after upgrade

**Cause**: Test mocks missing new fields

**Solution**:
- Update test fixtures to include v2.0.0 fields (set to None for backwards compatibility)
- Use `create_mock_stytch_context()` helper pattern shown above

## Getting Help

- **Documentation**: [docs/entitlements.md](./entitlements.md)
- **GitHub Issues**: https://github.com/ayzenberg/ayz-auth/issues
- **Examples**: See `example_usage.py` in the repository

## Summary

**Key Takeaways**:
1. ✅ v2.0.0 is 100% backwards compatible with v1.x
2. ✅ No code changes required for upgrade
3. ✅ Entitlements are optional - enable when ready
4. ✅ MongoDB configuration is optional
5. ✅ Performance impact is minimal with proper caching
6. ✅ Rollback is safe and easy

**Recommended Migration Path**:
1. Upgrade package in development
2. Test without MongoDB (backwards compatibility)
3. Set up MongoDB in staging
4. Test with MongoDB configured
5. Deploy to production
6. Enable MongoDB when ready

**Questions?** Check the [entitlements guide](./entitlements.md) or open a GitHub issue.
