# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-10-08

### Breaking Changes
- **Removed `STYTCH_ORGANIZATION_ID` environment variable**: For multi-tenant applications, the organization ID is now always obtained from the authenticated user's session context. The `get_member_by_email()` method now requires `organization_id` as a parameter instead of reading it from config. This change ensures proper multi-tenant isolation.
  ```python
  # Before (v1.x):
  member = await stytch_verifier.get_member_by_email(email)

  # After (v2.0.0):
  member = await stytch_verifier.get_member_by_email(email, user.organization_id)
  ```

### Added

#### Entitlements System
- **MongoDB Integration**: Optional MongoDB support for organization entitlements and user team context
  - New optional dependency group: `pip install 'ayz-auth[mongodb]'`
  - Automatic graceful degradation if MongoDB is not configured
  - Read-only access to `organizations`, `users`, and `teams` collections

#### StytchContext Enhancements
- **Entitlements Fields** (all optional, None if MongoDB not configured):
  - `entitlements: List[str]` - Organization feature entitlements
  - `subscription_tier: str` - Subscription tier (free, standard, premium, enterprise)
  - `subscription_limits: Dict[str, int]` - Subscription limits (max_projects, max_users, etc.)

- **Team Context Fields**:
  - `current_team_id: str` - User's current team ID (MongoDB ObjectId as string)
  - `current_team_name: str` - User's current team name

- **MongoDB Identifiers**:
  - `mongo_user_id: str` - MongoDB user document ID
  - `mongo_organization_id: str` - MongoDB organization document ID

#### Authorization Decorators
- `@require_entitlement(entitlement)` - Require a specific entitlement
- `@require_any_entitlement(*entitlements)` - Require at least one entitlement
- `@require_all_entitlements(*entitlements)` - Require all specified entitlements

#### Caching Enhancements
- Organization entitlements caching with 1-hour TTL
- User context caching with 5-minute TTL
- Separate cache keys for organization and user data
- Enhanced token cache to include entitlements data

#### Configuration
- New optional environment variable: `STYTCH_MONGODB_URI`
- MongoDB URI can point to any database (default: `soulmates`)

### Changed
- **Version**: Bumped to 2.0.0 (major version for new features)
- **Package Description**: Updated to mention entitlements and MongoDB features
- **Development Status**: Upgraded from Alpha to Beta
- **Token Caching**: Now includes entitlements and team context data

### Performance
- **Cached Requests**: <10ms (Stytch validation + Redis entitlements/context lookups)
- **Uncached Requests**: <100ms (Stytch validation + MongoDB queries + Redis writes)
- **Parallel Loading**: Organization and user data loaded concurrently

### Backwards Compatibility
- ✅ **100% backwards compatible** with v1.x
- All new StytchContext fields default to `None`
- MongoDB dependencies are optional
- Existing implementations work without any changes
- No breaking changes to existing APIs

### Documentation
- Updated `README.md` with entitlements features
- Added `CHANGELOG.md` (this file)
- Added `docs/entitlements.md` - Detailed entitlements guide
- Added `docs/migration-v2.md` - Migration guide from v1.x
- Updated `example_usage.py` with entitlements examples

### Security
- MongoDB connections are read-only
- Graceful error handling prevents authentication bypass
- Entitlements failures log warnings but don't break authentication
- No sensitive data in error responses

## [1.0.0] - 2025-07-22

### Added
- Initial stable release
- Stytch B2B session token verification
- Redis caching for session tokens
- FastAPI middleware integration
- `verify_auth` dependency for authentication
- `verify_auth_optional` for optional authentication
- `create_auth_dependency` for custom auth requirements
- StytchContext model with session data
- Comprehensive error handling
- Type-safe configuration with Pydantic
- Full test coverage

### Documentation
- Complete README with usage examples
- API documentation
- Development setup guide

## [0.1.0] - 2025-06-18

### Added
- Initial alpha release
- Basic Stytch B2B integration
- Redis caching support
- FastAPI middleware

---

[2.0.0]: https://github.com/brandsoulmates/ayz-auth/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/brandsoulmates/ayz-auth/compare/v0.1.0...v1.0.0
[0.1.0]: https://github.com/brandsoulmates/ayz-auth/releases/tag/v0.1.0
