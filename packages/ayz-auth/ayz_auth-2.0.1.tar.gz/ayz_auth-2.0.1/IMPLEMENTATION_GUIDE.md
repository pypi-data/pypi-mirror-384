# ayz-auth Complete Implementation Guide

**A comprehensive guide for junior developers to implement Stytch B2B authentication in Python FastAPI projects**

---

## Table of Contents

1. [Overview](#overview)
2. [What This Package Does](#what-this-package-does)
3. [Prerequisites](#prerequisites)
4. [Installation](#installation)
5. [Environment Setup](#environment-setup)
6. [Basic Implementation](#basic-implementation)
7. [Understanding StytchContext](#understanding-stytchcontext)
8. [Authentication Patterns](#authentication-patterns)
9. [Advanced Features (v2.0.0+)](#advanced-features-v200)
10. [Error Handling](#error-handling)
11. [Integration with Your Database](#integration-with-your-database)
12. [Testing Your Implementation](#testing-your-implementation)
13. [Security Best Practices](#security-best-practices)
14. [Troubleshooting](#troubleshooting)
15. [Complete Working Examples](#complete-working-examples)

---

## Overview

`ayz-auth` is a FastAPI middleware package that handles authentication and authorization for your web application using Stytch B2B (Business-to-Business) authentication service. It sits between your API endpoints and the outside world, verifying that users are who they say they are, loading their entitlements and team context, and providing you with a rich context object containing all user, organization, and team information.

### Key Concepts

- **Authentication**: Verifying a user's identity (who are you?)
- **Authorization**: Verifying a user's permissions (what can you do?)
- **Session Token**: A secret string that proves a user is authenticated
- **Middleware**: Code that runs before your endpoint handlers to check authentication
- **Caching**: Storing authentication results temporarily to improve performance

---

## What This Package Does

### Core Functionality

1. **Token Extraction**: Automatically reads authentication tokens from HTTP requests
2. **Token Verification**: Validates tokens with Stytch's API to ensure they're genuine
3. **Redis Caching**: Stores verified tokens in Redis to avoid repeated API calls (faster!)
4. **Comprehensive User Context**: Provides complete user session information including:
   - Identity: member ID, email, name, organization ID, session ID
   - Session timing: started at, expires at, last accessed at
   - Authentication metadata: factors used, custom claims
   - Full raw session data for extended access
5. **Error Handling**: Returns proper HTTP error codes when authentication fails

### v2.0.0 Additional Features

6. **Organization Entitlements**: Automatic loading of subscription data including:
   - Entitlements list (which features are enabled)
   - Subscription tier (free, standard, premium, enterprise)
   - Usage limits (max projects, max users, API quotas, etc.)
7. **Team Context**: Complete team information for multi-tenancy:
   - Current team ID (for database queries and filtering)
   - Current team name (for UI display)
8. **MongoDB Integration**: Seamlessly loads organization and user data:
   - MongoDB user document ID for your database queries
   - MongoDB organization document ID for filtering
   - Automatic parallel loading with caching
9. **Authorization Decorators**: Easy-to-use dependencies for feature gating:
   - `require_entitlement()` - single feature check
   - `require_any_entitlement()` - user needs at least one
   - `require_all_entitlements()` - user needs all specified

### Caching Strategy

The package uses a sophisticated three-tier caching system for optimal performance:

```mermaid
graph LR
    subgraph "Cache Tiers"
        Token[Token Cache<br/>TTL: 5 min<br/>Key: token hash]
        Org[Organization Cache<br/>TTL: 1 hour<br/>Key: stytch_org_id]
        User[User Context Cache<br/>TTL: 5 min<br/>Key: stytch_member_id]
    end

    subgraph "Data Sources"
        Stytch[Stytch API]
        MongoDB[(MongoDB)]
    end

    Request[Request] --> Token
    Token -->|Hit| FastResponse[<10ms Response]
    Token -->|Miss| Stytch
    Stytch --> Org
    Org -->|Hit| OrgCached[Cached Org Data]
    Org -->|Miss| MongoDB
    MongoDB --> User
    User -->|Hit| UserCached[Cached User Data]
    User -->|Miss| MongoDB

    style Token fill:#f9f
    style Org fill:#bbf
    style User fill:#bfb
    style FastResponse fill:#afa
```

### Architecture Overview

```mermaid
graph TB
    Client[Client Application]
    FastAPI[FastAPI Endpoint]
    Middleware[ayz-auth Middleware]
    Redis[(Redis Cache)]
    Stytch[Stytch API]
    MongoDB[(MongoDB)]

    Client -->|1. Request + Token| FastAPI
    FastAPI -->|2. Depends verify_auth| Middleware
    Middleware -->|3. Check Cache| Redis
    Redis -->|Cache Hit| Middleware
    Redis -->|Cache Miss| Stytch
    Stytch -->|5. Verify Token| Middleware
    Middleware -->|6. Load Entitlements| MongoDB
    MongoDB -->|Organization Data| Middleware
    Middleware -->|7. StytchContext| FastAPI
    FastAPI -->|8. Response| Client

    style Redis fill:#f9f,stroke:#333
    style Stytch fill:#bbf,stroke:#333
    style MongoDB fill:#bfb,stroke:#333
```

### Complete Request Lifecycle

```mermaid
sequenceDiagram
    autonumber
    participant Client
    participant FastAPI
    participant Middleware as ayz-auth
    participant Redis
    participant Stytch
    participant MongoDB

    Client->>FastAPI: POST /api/projects<br/>Authorization: Bearer TOKEN

    Note over FastAPI,Middleware: Authentication Phase

    FastAPI->>Middleware: Depends(require_entitlement("premium"))
    Middleware->>Middleware: Extract token from header
    Middleware->>Redis: GET cache:token:{hash}

    alt Token in Cache
        Redis-->>Middleware: Cached StytchContext
        Note over Middleware: ✓ Skip Stytch API call
    else Token not in Cache
        Middleware->>Stytch: Authenticate token
        Stytch-->>Middleware: Session data
        Middleware->>Redis: GET cache:org:{stytch_org_id}

        alt Org Data in Cache
            Redis-->>Middleware: Cached entitlements
        else Org Data not in Cache
            Middleware->>MongoDB: Query organizations collection
            MongoDB-->>Middleware: Subscription & entitlements
            Middleware->>Redis: SET cache:org:{id} (TTL: 1 hour)
        end

        Middleware->>Redis: GET cache:user:{stytch_member_id}

        alt User Data in Cache
            Redis-->>Middleware: Cached team context
        else User Data not in Cache
            Middleware->>MongoDB: Query users & teams collections
            MongoDB-->>Middleware: Team membership
            Middleware->>Redis: SET cache:user:{id} (TTL: 5 min)
        end

        Middleware->>Redis: SET cache:token:{hash} (TTL: 5 min)
    end

    Note over Middleware: Authorization Phase

    Middleware->>Middleware: Check if "premium" in entitlements

    alt Has Required Entitlement
        Middleware-->>FastAPI: ✓ StytchContext
        Note over FastAPI: Business Logic Phase
        FastAPI->>FastAPI: Execute endpoint logic
        FastAPI->>MongoDB: Create project
        MongoDB-->>FastAPI: Project created
        FastAPI-->>Client: 200 OK + Project data
    else Missing Entitlement
        Middleware-->>FastAPI: ✗ Raise HTTPException(403)
        FastAPI-->>Client: 403 Forbidden<br/>upgrade_required: true
    end
```

---

## Prerequisites

### Required Knowledge

- Basic Python programming (functions, classes, async/await)
- Understanding of REST APIs and HTTP requests
- Familiarity with FastAPI framework basics
- Basic understanding of environment variables

### Required Services

Before using this package, you need:

1. **Stytch Account**: Sign up at [https://stytch.com](https://stytch.com)
   - Create a B2B project
   - Get your Project ID and Secret Key
   - Choose environment: `test` (development) or `live` (production)

2. **Redis Server**: For caching authentication results
   - Local: Install Redis (`brew install redis` on Mac)
   - Cloud: Use Redis Cloud, AWS ElastiCache, etc.
   - Default URL: `redis://localhost:6379`

3. **MongoDB (Optional)**: For entitlements and team features (v2.0.0+)
   - Only needed if you want subscription-based features
   - Works fine without MongoDB for basic authentication

### System Requirements

- Python 3.8 or higher
- pip or uv package manager

---

## Installation

### Basic Installation (Authentication Only)

If you only need authentication (no entitlements/teams):

```bash
# Using pip
pip install ayz-auth

# Using uv (faster)
uv add ayz-auth

# Using poetry
poetry add ayz-auth
```

### Installation with MongoDB Support (v2.0.0+)

If you need entitlements and team context features:

```bash
# Using pip
pip install 'ayz-auth[mongodb]'

# Using uv
uv add 'ayz-auth[mongodb]'

# Using poetry
poetry add 'ayz-auth[mongodb]'
```

**Note**: The `[mongodb]` extra installs additional dependencies: `motor` and `pymongo`.

### Verify Installation

```python
# Test that the package is installed
import ayz_auth
print(ayz_auth.__version__)  # Should print: 2.0.0 or higher
```

---

## Environment Setup

### Step 1: Get Your Stytch Credentials

1. Log in to [Stytch Dashboard](https://stytch.com/dashboard)
2. Select your B2B project
3. Navigate to **API Keys** section
4. Copy your **Project ID** and **Secret Key**
5. Note your environment: `test` or `live`

### Step 2: Create .env File

In your project's root directory, create a file named `.env`:

```bash
# Required - Get these from Stytch Dashboard
STYTCH_PROJECT_ID=project-test-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
STYTCH_SECRET=secret-test-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
STYTCH_ENV=test

# Required - Redis connection
STYTCH_REDIS_URL=redis://localhost:6379

# Optional - Only if using Redis authentication
STYTCH_REDIS_PASSWORD=your_redis_password

# Optional - MongoDB for entitlements (v2.0.0+)
STYTCH_MONGODB_URI=mongodb://localhost:27017/your_database_name

# Optional - Cache settings (defaults shown)
STYTCH_CACHE_TTL=300
STYTCH_CACHE_PREFIX=ayz_auth

# Optional - Logging (defaults shown)
STYTCH_LOG_LEVEL=INFO
STYTCH_LOG_SENSITIVE_DATA=false
```

### Step 3: Load Environment Variables

Install python-dotenv to automatically load .env files:

```bash
pip install python-dotenv
```

In your main application file (e.g., `main.py`):

```python
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Verify they're loaded
print(f"Project ID: {os.getenv('STYTCH_PROJECT_ID')}")
```

### Configuration Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `STYTCH_PROJECT_ID` | ✅ Yes | None | Your Stytch project identifier |
| `STYTCH_SECRET` | ✅ Yes | None | Your Stytch secret key (keep secure!) |
| `STYTCH_ENV` | ✅ Yes | `test` | Stytch environment: `test` or `live` |
| `STYTCH_REDIS_URL` | ✅ Yes | `redis://localhost:6379` | Redis connection string |
| `STYTCH_REDIS_PASSWORD` | No | None | Redis password if required |
| `STYTCH_REDIS_DB` | No | `0` | Redis database number (0-15) |
| `STYTCH_MONGODB_URI` | No | None | MongoDB connection for entitlements |
| `STYTCH_CACHE_TTL` | No | `300` | Cache lifetime in seconds (5 min) |
| `STYTCH_CACHE_PREFIX` | No | `ayz_auth` | Prefix for Redis keys |
| `STYTCH_LOG_LEVEL` | No | `INFO` | Logging level: DEBUG, INFO, WARNING, ERROR |
| `STYTCH_LOG_SENSITIVE_DATA` | No | `false` | Log tokens? (NEVER in production!) |
| `STYTCH_REQUEST_TIMEOUT` | No | `10` | Stytch API timeout in seconds |
| `STYTCH_MAX_RETRIES` | No | `3` | Max retry attempts for failed requests |

---

## Basic Implementation

### Step 1: Create Your FastAPI Application

Create a file called `main.py`:

```python
from fastapi import FastAPI, Depends
from dotenv import load_dotenv

# Import authentication components
from ayz_auth import verify_auth, StytchContext

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(title="My Protected API")

# Public endpoint - no authentication needed
@app.get("/")
async def public_endpoint():
    return {"message": "This endpoint is public"}

# Protected endpoint - authentication required
@app.get("/protected")
async def protected_endpoint(user: StytchContext = Depends(verify_auth)):
    """
    This endpoint requires authentication.
    The user parameter will contain the authenticated user's information.
    """
    return {
        "message": f"Hello {user.member_email}!",
        "user_id": user.member_id,
        "organization_id": user.organization_id,
        "session_expires_at": user.session_expires_at,
        # v2.0.0+ fields are also available (None if MongoDB not configured)
        "subscription_tier": user.subscription_tier,
        "current_team": user.current_team_name,
        "entitlements": user.entitlements
    }

# Run the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Step 2: Understanding the Code

```mermaid
sequenceDiagram
    participant Client
    participant FastAPI
    participant Middleware
    participant Redis
    participant Stytch

    Client->>FastAPI: GET /protected + Bearer Token
    FastAPI->>Middleware: Depends(verify_auth)
    Middleware->>Middleware: Extract token from header
    Middleware->>Redis: Check cache for token
    alt Token in cache
        Redis-->>Middleware: Return cached StytchContext
    else Token not in cache
        Middleware->>Stytch: Verify token with API
        Stytch-->>Middleware: Valid session data
        Middleware->>Redis: Cache result
    end
    Middleware-->>FastAPI: StytchContext object
    FastAPI->>FastAPI: Execute endpoint logic
    FastAPI-->>Client: JSON response
```

Let's break down what's happening:

1. **Import Authentication Components**:
   ```python
   from ayz_auth import verify_auth, StytchContext
   ```
   - `verify_auth`: The function that checks if a request is authenticated
   - `StytchContext`: The data model containing user information

2. **Public Endpoint**:
   ```python
   @app.get("/")
   async def public_endpoint():
       return {"message": "This endpoint is public"}
   ```
   - No authentication required
   - Anyone can access this

3. **Protected Endpoint**:
   ```python
   @app.get("/protected")
   async def protected_endpoint(user: StytchContext = Depends(verify_auth)):
   ```
   - `Depends(verify_auth)`: FastAPI will call `verify_auth` before running your function
   - If authentication fails, FastAPI returns 401 error automatically
   - If authentication succeeds, `user` contains the authenticated user's data

### Step 3: Run Your Application

```bash
# Start Redis (if running locally)
redis-server

# In another terminal, start your FastAPI app
python main.py

# Or use uvicorn directly
uvicorn main:app --reload
```

Your API is now running at `http://localhost:8000`

### Step 4: Test Your Endpoints

**Test the public endpoint**:
```bash
curl http://localhost:8000/
# Returns: {"message": "This endpoint is public"}
```

**Test the protected endpoint without authentication**:
```bash
curl http://localhost:8000/protected
# Returns: 401 error
```

**Test the protected endpoint with authentication**:
```bash
curl http://localhost:8000/protected \
  -H "Authorization: Bearer YOUR_STYTCH_SESSION_TOKEN"
# Returns: {"message": "Hello user@example.com!", ...}
```

**Where to get a session token for testing**:
1. In Stytch Dashboard, go to **API Keys**
2. Use Stytch's test mode to create a test session
3. Use your frontend login flow (if you have one set up)

---

## Understanding StytchContext

When authentication succeeds, you receive a `StytchContext` object containing **ALL** of the following:
- ✅ Complete Stytch session data (member ID, email, name, organization ID, session timing)
- ✅ Authentication metadata (factors used, custom claims, raw session data)
- ✅ **v2.0.0+**: Organization entitlements (features list, subscription tier, usage limits)
- ✅ **v2.0.0+**: User team context (current team ID and name for data filtering)
- ✅ **v2.0.0+**: MongoDB references (user and organization document IDs)

**Every field listed below is always available on the `StytchContext` object**. Fields marked as v2.0.0+ will be `None` if MongoDB is not configured, but all base fields are always populated after successful authentication.

### Complete StytchContext Structure

```python
class StytchContext:
    """
    Complete user context returned after successful authentication.
    ALL fields below are accessible on every authenticated request.
    """
    # ===== Core Identifiers =====
    member_id: str
    # - Unique identifier for the user in Stytch
    # - Use this to link to your database's user records
    # - Example: "member-live-abc123..."

    session_id: str
    # - Unique identifier for this login session
    # - Changes each time the user logs in
    # - Example: "session-live-xyz789..."

    organization_id: str
    # - The company/organization the user belongs to
    # - All users in same company share this ID
    # - Example: "organization-live-company123..."

    # ===== Session Timing =====
    session_started_at: datetime
    # - When the user logged in
    # - Python datetime object (timezone-aware)

    session_expires_at: datetime
    # - When this session will expire
    # - User must log in again after this time

    session_last_accessed_at: datetime
    # - Last time this session was used
    # - Updates on each authenticated request

    authenticated_at: datetime
    # - When this StytchContext object was created
    # - Set by the middleware (current time)

    # ===== Member Information =====
    member_email: Optional[str]
    # - User's email address
    # - May be None if not provided

    member_name: Optional[str]
    # - User's display name
    # - May be None if not set

    # ===== Session Metadata =====
    session_custom_claims: Dict[str, Any]
    # - Custom data attached to the session
    # - Example: {"role": "admin", "department": "engineering"}
    # - Empty dict {} if no custom claims

    authentication_factors: List[str]
    # - How the user authenticated
    # - Examples: ["password"], ["sso"], ["mfa", "password"]
    # - Empty list [] if not provided

    raw_session_data: Dict[str, Any]
    # - Complete raw response from Stytch API
    # - Contains all fields above plus Stytch-specific data
    # - Use for debugging or accessing undocumented fields

    # ===== v2.0.0+ Entitlements (Optional) =====
    entitlements: Optional[List[str]]
    # - Features the organization's subscription includes
    # - Example: ["foresight", "byod", "analytics"]
    # - None if MongoDB not configured

    subscription_tier: Optional[str]
    # - Organization's subscription level
    # - Example: "free", "standard", "premium", "enterprise"
    # - None if MongoDB not configured

    subscription_limits: Optional[Dict[str, int]]
    # - Usage limits for the subscription
    # - Example: {"max_projects": 50, "max_users": 100}
    # - None if MongoDB not configured

    # ===== v2.0.0+ Team Context (Optional) =====
    current_team_id: Optional[str]
    # - MongoDB ObjectId of user's current team
    # - Example: "507f1f77bcf86cd799439011"
    # - None if MongoDB not configured or user has no team

    current_team_name: Optional[str]
    # - Name of user's current team
    # - Example: "Engineering Team"
    # - None if MongoDB not configured or user has no team

    # ===== v2.0.0+ MongoDB IDs (Optional) =====
    mongo_user_id: Optional[str]
    # - MongoDB ObjectId of user document
    # - Links to your users collection
    # - None if MongoDB not configured

    mongo_organization_id: Optional[str]
    # - MongoDB ObjectId of organization document
    # - Links to your organizations collection
    # - None if MongoDB not configured
```

### What Data is ALWAYS Returned?

**Base Fields (always populated after successful authentication):**
- `member_id`, `session_id`, `organization_id` - Core identifiers
- `member_email`, `member_name` - User information (may be `None`)
- `session_started_at`, `session_expires_at`, `session_last_accessed_at` - Session timing
- `authenticated_at` - When middleware created this context
- `session_custom_claims` - Custom data (empty `{}` if none)
- `authentication_factors` - How user authenticated (empty `[]` if none)
- `raw_session_data` - Complete Stytch API response

**v2.0.0+ Fields (requires MongoDB configuration, otherwise `None`):**
- `entitlements` - List of enabled features
- `subscription_tier` - Subscription level (free, standard, premium, enterprise)
- `subscription_limits` - Usage limits (max_projects, max_users, etc.)
- `current_team_id` - **MongoDB ObjectId of user's current team** ⭐
- `current_team_name` - **Team name for display** ⭐
- `mongo_user_id` - MongoDB user document ID
- `mongo_organization_id` - MongoDB organization document ID

**Key Point**: The package returns much more than just "email, ID, organization" - it returns a complete context with session data, timing, authentication factors, entitlements, team context, and MongoDB references!

### Using StytchContext Properties

```python
@app.get("/user-info")
async def get_user_info(user: StytchContext = Depends(verify_auth)):
    # Access basic information
    email = user.member_email
    name = user.member_name or "Unknown"

    # Check session expiry
    if user.is_expired:
        return {"error": "Session has expired"}

    # Get time until expiry
    seconds_left = user.time_until_expiry

    # Access custom claims
    is_admin = user.session_custom_claims.get("admin", False)

    # Check authentication factors
    has_mfa = "mfa" in user.authentication_factors

    # Convert to dictionary for JSON response
    user_dict = user.to_dict()

    return {
        "email": email,
        "name": name,
        "seconds_until_expiry": seconds_left,
        "is_admin": is_admin,
        "has_mfa": has_mfa,
        "full_context": user_dict
    }
```

### Utility Methods and Properties

```python
# Check if session is expired
if user.is_expired:
    # Session has expired
    pass

# Get seconds until expiry (None if expired)
time_left = user.time_until_expiry

# Convert to dictionary
user_data = user.to_dict()

# String representation (safe for logging)
print(user)  # "StytchContext(member_id=..., organization_id=..., expires_at=...)"
```

---

## Authentication Patterns

### Authentication Flow Diagram

```mermaid
flowchart TD
    Start[Request Received] --> HasToken{Has Auth Token?}
    HasToken -->|No| Return401[Return 401 Unauthorized]
    HasToken -->|Yes| CheckCache{Token in Cache?}

    CheckCache -->|Yes| ValidCache{Cache Valid?}
    CheckCache -->|No| CallStytch[Call Stytch API]

    ValidCache -->|Yes| LoadEntitlements[Load Entitlements]
    ValidCache -->|No| CallStytch

    CallStytch --> StytchValid{Token Valid?}
    StytchValid -->|No| Return401
    StytchValid -->|Yes| CacheResult[Cache Result]
    CacheResult --> LoadEntitlements

    LoadEntitlements --> MongoConfigured{MongoDB Configured?}
    MongoConfigured -->|Yes| QueryMongo[Query Organization & User Data]
    MongoConfigured -->|No| SkipEntitlements[Entitlements = None]

    QueryMongo --> BuildContext[Build StytchContext]
    SkipEntitlements --> BuildContext

    BuildContext --> CheckPermissions{Has Required Permissions?}
    CheckPermissions -->|No| Return403[Return 403 Forbidden]
    CheckPermissions -->|Yes| ExecuteEndpoint[Execute Endpoint]

    ExecuteEndpoint --> ReturnResponse[Return Response]

    style Return401 fill:#faa
    style Return403 fill:#faa
    style ReturnResponse fill:#afa
```

### Pattern 1: Required Authentication

**Use Case**: Endpoint requires user to be logged in

```python
from fastapi import Depends
from ayz_auth import verify_auth, StytchContext

@app.get("/dashboard")
async def dashboard(user: StytchContext = Depends(verify_auth)):
    """User MUST be authenticated to access"""
    return {
        "dashboard_data": "...",
        "user_email": user.member_email,
        "user_id": user.member_id,
        "org_id": user.organization_id,
        # All StytchContext fields are available here:
        "session_expires": user.session_expires_at,
        "team_id": user.current_team_id,  # v2.0.0+ (None if MongoDB not configured)
        "team_name": user.current_team_name,  # v2.0.0+
        "subscription": user.subscription_tier  # v2.0.0+
    }
```

**What happens**:
- ✅ With valid token → Endpoint runs normally
- ❌ Without token → Returns 401 error
- ❌ With invalid token → Returns 401 error

---

### Pattern 2: Optional Authentication

**Use Case**: Endpoint works differently for authenticated vs. anonymous users

```python
from typing import Optional
from fastapi import Depends
from ayz_auth import verify_auth_optional, StytchContext

@app.get("/products")
async def list_products(user: Optional[StytchContext] = Depends(verify_auth_optional)):
    """Works with or without authentication"""
    if user:
        # Authenticated user - show personalized content
        return {
            "products": get_recommended_products(user.member_id),
            "user_email": user.member_email
        }
    else:
        # Anonymous user - show generic content
        return {
            "products": get_generic_products()
        }
```

**What happens**:
- ✅ With valid token → `user` is StytchContext object
- ✅ Without token → `user` is None
- ✅ With invalid token → `user` is None (no error!)

---

### Pattern 3: Custom Claims Required

**Use Case**: Endpoint requires specific permissions (e.g., admin only)

```python
from ayz_auth import create_auth_dependency, StytchContext

# Create custom authentication dependency
admin_auth = create_auth_dependency(required_claims=["admin"])

@app.get("/admin/users")
async def list_all_users(user: StytchContext = Depends(admin_auth)):
    """Only users with 'admin' claim can access"""
    return {"users": get_all_users()}
```

**Setting Custom Claims in Stytch**:
Custom claims are set in your Stytch session when a user logs in:

```python
# In your login endpoint (example)
stytch_client.sessions.authenticate(
    session_token=token,
    session_custom_claims={
        "admin": True,
        "department": "engineering"
    }
)
```

**What happens**:
- ✅ Authenticated + has "admin" claim → Endpoint runs
- ❌ Authenticated but missing "admin" claim → Returns 403 error
- ❌ Not authenticated → Returns 401 error

---

### Pattern 4: MFA Required

**Use Case**: Sensitive endpoints requiring multi-factor authentication

```python
from ayz_auth import create_auth_dependency, StytchContext

# Require MFA
mfa_auth = create_auth_dependency(required_factors=["mfa"])

@app.post("/transfer-money")
async def transfer_money(
    amount: float,
    user: StytchContext = Depends(mfa_auth)
):
    """Requires multi-factor authentication"""
    return {
        "status": "success",
        "amount": amount,
        "user": user.member_email
    }
```

**What happens**:
- ✅ Authenticated with MFA → Endpoint runs
- ❌ Authenticated without MFA → Returns 403 error
- ❌ Not authenticated → Returns 401 error

---

### Pattern 5: Multiple Requirements

**Use Case**: Endpoint requires both custom claims AND authentication factors

```python
# Require admin claim AND MFA
secure_admin_auth = create_auth_dependency(
    required_claims=["admin"],
    required_factors=["mfa"]
)

@app.delete("/admin/delete-organization")
async def delete_organization(
    org_id: str,
    user: StytchContext = Depends(secure_admin_auth)
):
    """Requires admin privileges AND multi-factor authentication"""
    return {"status": "deleted", "org_id": org_id}
```

---

## Advanced Features (v2.0.0+)

### Prerequisites for Advanced Features

These features require:
1. MongoDB installed and running
2. `ayz-auth[mongodb]` package installed
3. `STYTCH_MONGODB_URI` environment variable set
4. Specific MongoDB collections configured (see below)

### MongoDB Setup

#### Required Collections

Your MongoDB database needs these three collections:

**1. organizations collection**:
```javascript
{
    "_id": ObjectId("..."),
    "stytch_org_id": "organization-live-abc123...",  // Links to Stytch
    "subscription_tier": "premium",  // "free" | "standard" | "premium" | "enterprise"
    "entitlements": ["foresight", "byod", "analytics"],  // Features enabled
    "subscription_limits": {
        "max_projects": 50,
        "max_users": 100,
        "max_queries_per_month": 10000
    }
}
```

**2. users collection**:
```javascript
{
    "_id": ObjectId("..."),
    "stytch_member_id": "member-live-xyz789...",  // Links to Stytch
    "current_team_id": ObjectId("..."),  // Reference to teams collection
    "email": "user@example.com",
    "name": "John Doe"
}
```

**3. teams collection**:
```javascript
{
    "_id": ObjectId("..."),
    "name": "Engineering Team",
    "organization_id": ObjectId("...")  // Reference to organizations collection
}
```

#### MongoDB Indexes (Recommended)

Create indexes for better performance:

```javascript
// In MongoDB shell or Compass
db.organizations.createIndex({ "stytch_org_id": 1 })
db.users.createIndex({ "stytch_member_id": 1 })
db.teams.createIndex({ "organization_id": 1 })
```

#### MongoDB Collection Relationships

```mermaid
erDiagram
    ORGANIZATIONS ||--o{ USERS : "has many"
    ORGANIZATIONS ||--o{ TEAMS : "has many"
    USERS }o--|| TEAMS : "belongs to"

    ORGANIZATIONS {
        ObjectId _id
        string stytch_org_id
        string subscription_tier
        array entitlements
        object subscription_limits
    }

    USERS {
        ObjectId _id
        string stytch_member_id
        ObjectId current_team_id
        string email
        string name
    }

    TEAMS {
        ObjectId _id
        string name
        ObjectId organization_id
    }
```

---

### Feature 1: Entitlement-Based Authorization

**Use Case**: Restrict features based on subscription tier

#### Entitlement Check Flow

```mermaid
flowchart LR
    Request[API Request] --> Auth[verify_auth]
    Auth --> Authenticated{Authenticated?}
    Authenticated -->|No| Reject401[401 Unauthorized]
    Authenticated -->|Yes| CheckEntitlement{Check Entitlement}

    CheckEntitlement --> MongoConfigured{MongoDB Configured?}
    MongoConfigured -->|No| Reject403A[403 - Entitlements Not Configured]
    MongoConfigured -->|Yes| HasEntitlement{Has Required Entitlement?}

    HasEntitlement -->|No| Reject403B[403 - Missing Entitlement]
    HasEntitlement -->|Yes| Allow[Allow Access]

    style Reject401 fill:#faa
    style Reject403A fill:#faa
    style Reject403B fill:#faa
    style Allow fill:#afa
```

#### Single Entitlement Required

```python
from fastapi import Depends
from ayz_auth import require_entitlement, StytchContext

@app.get("/foresight/analyze")
async def foresight_analysis(
    user: StytchContext = Depends(require_entitlement("foresight"))
):
    """Only users with 'foresight' entitlement can access"""
    return {
        "analysis": "...",
        "subscription_tier": user.subscription_tier,
        "current_team": user.current_team_name
    }
```

#### Multiple Entitlements - ANY

**Use Case**: User needs at least ONE of several entitlements

```python
from ayz_auth import require_any_entitlement

@app.get("/analytics")
async def analytics_dashboard(
    user: StytchContext = Depends(
        require_any_entitlement("foresight", "analytics_basic")
    )
):
    """User needs 'foresight' OR 'analytics_basic'"""
    available_features = user.entitlements or []
    return {
        "dashboard": "...",
        "features": available_features
    }
```

#### Multiple Entitlements - ALL

**Use Case**: User needs ALL specified entitlements

```python
from ayz_auth import require_all_entitlements

@app.get("/premium/advanced-analytics")
async def premium_analytics(
    user: StytchContext = Depends(
        require_all_entitlements("foresight", "advanced_analytics")
    )
):
    """User needs BOTH 'foresight' AND 'advanced_analytics'"""
    return {"premium_data": "..."}
```

#### Manual Entitlement Checks

**Use Case**: Custom logic based on entitlements

```python
@app.get("/features")
async def get_features(user: StytchContext = Depends(verify_auth)):
    """Manual entitlement checking with custom logic"""

    # Always check if entitlements are loaded (MongoDB configured)
    if user.entitlements is None:
        return {
            "error": "Entitlements not available",
            "upgrade_to_enable": True
        }

    # Check specific entitlements
    has_foresight = "foresight" in user.entitlements
    has_byod = "byod" in user.entitlements

    # Build response based on entitlements
    features = {
        "basic_analytics": True,  # Always available
        "foresight": has_foresight,
        "bring_your_own_data": has_byod,
        "export_data": has_foresight or has_byod,  # Either one
        "premium_support": len(user.entitlements) > 5  # More than 5 entitlements
    }

    return {
        "features": features,
        "tier": user.subscription_tier,
        "all_entitlements": user.entitlements
    }
```

---

### Feature 2: Subscription Limits

**Use Case**: Enforce usage limits based on subscription

```python
@app.post("/projects")
async def create_project(
    project_name: str,
    user: StytchContext = Depends(verify_auth),
    db=Depends(get_database)  # Your database dependency
):
    """Create project with subscription limit checking"""

    # Check if subscription limits are available
    if not user.subscription_limits:
        return {"error": "Subscription limits not configured"}

    # Get the limit from subscription
    max_projects = user.subscription_limits.get("max_projects", 0)

    # Count current projects
    current_count = await db.projects.count_documents({
        "organization_id": user.mongo_organization_id
    })

    # Check if limit would be exceeded
    # (max_projects == -1 means unlimited)
    if max_projects != -1 and current_count >= max_projects:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "limit_exceeded",
                "message": f"Your {user.subscription_tier} plan allows {max_projects} projects",
                "current_count": current_count,
                "limit": max_projects,
                "upgrade_required": True
            }
        )

    # Create the project
    project = await db.projects.insert_one({
        "name": project_name,
        "organization_id": user.mongo_organization_id,
        "created_by": user.mongo_user_id
    })

    return {
        "status": "created",
        "project_id": str(project.inserted_id),
        "usage": f"{current_count + 1}/{max_projects}"
    }
```

---

### Feature 3: Team Context and Data Filtering

**Use Case**: Multi-tenant application where users work in teams

```python
@app.get("/projects")
async def list_projects(
    user: StytchContext = Depends(verify_auth),
    db=Depends(get_database)
):
    """List projects filtered by user's current team"""

    # Build query based on team context
    if user.current_team_id:
        # User has a team - show team's projects
        query = {"team_id": user.current_team_id}
        scope = f"team '{user.current_team_name}'"
    else:
        # User has no team - show only their own projects
        query = {"user_id": user.mongo_user_id}
        scope = "personal"

    # Fetch projects
    projects = await db.projects.find(query).to_list(length=100)

    return {
        "projects": projects,
        "scope": scope,
        "team": {
            "id": user.current_team_id,
            "name": user.current_team_name
        }
    }
```

**Data Isolation Pattern**:
```python
async def ensure_team_access(project_id: str, user: StytchContext, db):
    """Helper function to verify user can access a project"""
    project = await db.projects.find_one({"_id": ObjectId(project_id)})

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check if user has access via team
    if user.current_team_id:
        if project["team_id"] != user.current_team_id:
            raise HTTPException(status_code=403, detail="Access denied")
    else:
        # Check if user owns the project
        if project["user_id"] != user.mongo_user_id:
            raise HTTPException(status_code=403, detail="Access denied")

    return project
```

---

### Feature 4: Frontend Feature Toggles

**Use Case**: Tell your frontend which features to show/hide

```python
@app.get("/user/features")
async def get_user_features(user: StytchContext = Depends(verify_auth)):
    """
    Return feature flags for frontend to customize UI.
    Frontend can show/hide buttons, menus, etc. based on this.
    """

    # Build feature flags
    features = {
        "enabled_features": user.entitlements or [],
        "subscription_tier": user.subscription_tier,
        "has_team": user.current_team_id is not None,

        # Specific feature checks
        "can_use_foresight": user.entitlements and "foresight" in user.entitlements,
        "can_upload_data": user.entitlements and "byod" in user.entitlements,
        "can_export": user.entitlements and "export" in user.entitlements,

        # Limits
        "limits": user.subscription_limits or {},

        # Team info
        "team": {
            "id": user.current_team_id,
            "name": user.current_team_name
        } if user.current_team_id else None
    }

    return features
```

**Frontend Usage** (React example):
```javascript
// In your React app
const { data: features } = await fetch('/user/features')

// Show/hide UI elements
{features.can_use_foresight && (
    <Button onClick={openForesightAnalysis}>
        Foresight Analysis
    </Button>
)}

// Show upgrade prompt
{!features.can_export && (
    <UpgradePrompt feature="data export" />
)}
```

---

## Error Handling

Understanding and handling authentication errors properly.

### Error Flow Diagram

```mermaid
flowchart TD
    Request[Incoming Request] --> ExtractToken[Extract Token]
    ExtractToken --> TokenPresent{Token Present?}

    TokenPresent -->|No| Error401A[401: Token Missing]
    TokenPresent -->|Yes| VerifyToken[Verify with Stytch]

    VerifyToken --> StytchAvailable{Stytch API Available?}
    StytchAvailable -->|No| Error503[503: Service Unavailable]
    StytchAvailable -->|Yes| TokenValid{Token Valid?}

    TokenValid -->|No| Error401B[401: Invalid/Expired Token]
    TokenValid -->|Yes| CheckPermissions[Check Permissions]

    CheckPermissions --> HasClaims{Has Required Claims?}
    HasClaims -->|No| Error403A[403: Missing Claims]
    HasClaims -->|Yes| HasFactors{Has Required Factors?}

    HasFactors -->|No| Error403B[403: Missing Auth Factors]
    HasFactors -->|Yes| HasEntitlement{Has Required Entitlement?}

    HasEntitlement -->|No| Error403C[403: Missing Entitlement]
    HasEntitlement -->|Yes| Success[200: Success]

    style Error401A fill:#faa
    style Error401B fill:#faa
    style Error403A fill:#f96
    style Error403B fill:#f96
    style Error403C fill:#f96
    style Error503 fill:#fa6
    style Success fill:#afa
```

### Error Types

#### 1. Token Extraction Error (401)

**Cause**: Token missing or malformed

```json
{
    "error": "authentication_failed",
    "message": "Authorization header is required",
    "type": "token_extraction"
}
```

**Common reasons**:
- No `Authorization` header in request
- Header format wrong (should be: `Authorization: Bearer TOKEN`)
- Token is empty string

**How to fix**:
```python
# Client-side (requests)
headers = {
    "Authorization": f"Bearer {session_token}"
}
response = requests.get(url, headers=headers)

# Frontend (JavaScript)
fetch(url, {
    headers: {
        'Authorization': `Bearer ${sessionToken}`
    }
})
```

---

#### 2. Token Verification Error (401)

**Cause**: Token is invalid or expired

```json
{
    "error": "authentication_failed",
    "message": "Invalid or expired session token",
    "type": "token_verification"
}
```

**Common reasons**:
- Token has expired (session timeout)
- Token was revoked
- Token is from wrong Stytch project
- Token is fake/tampered

**How to fix**:
- User needs to log in again
- Get a fresh token from Stytch
- Check token expiration before using

---

#### 3. Service Unavailable (503)

**Cause**: Stytch API or Redis is down

```json
{
    "error": "service_unavailable",
    "message": "Authentication service temporarily unavailable",
    "type": "stytch_api"
}
```

**Common reasons**:
- Stytch API outage
- Redis server is down
- Network connectivity issues
- Stytch API rate limit exceeded

**How to fix**:
- Check Stytch status page
- Verify Redis is running: `redis-cli ping`
- Check network connectivity
- Implement retry logic in your client

---

#### 4. Insufficient Permissions (403)

**Cause**: Missing required claims or authentication factors

```json
{
    "error": "insufficient_permissions",
    "message": "Missing required claims: ['admin']",
    "type": "authorization"
}
```

**How to fix**:
- User needs proper role/permissions
- Update user's session custom claims in Stytch
- Use different authentication dependency

---

#### 5. Missing Entitlement (403)

**Cause**: Subscription doesn't include required feature

```json
{
    "error": "forbidden",
    "message": "This feature requires the 'foresight' entitlement",
    "required_entitlement": "foresight",
    "current_tier": "standard",
    "upgrade_required": true
}
```

**How to fix**:
- Organization needs to upgrade subscription
- Update organization's entitlements in MongoDB
- Contact billing/support

---

### Custom Error Handling

**Global Error Handler**:
```python
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from ayz_auth import AuthenticationError

app = FastAPI()

@app.exception_handler(AuthenticationError)
async def auth_error_handler(request: Request, exc: AuthenticationError):
    """Custom handler for authentication errors"""

    # Log the error
    print(f"Auth error on {request.url.path}: {exc.message}")

    # Return custom response
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "authentication_failed",
            "message": exc.message,
            "details": exc.details,
            "path": str(request.url.path),
            "hint": "Please log in again or contact support"
        }
    )
```

**Endpoint-Level Error Handling**:
```python
from fastapi import HTTPException

@app.get("/protected")
async def protected_endpoint(user: StytchContext = Depends(verify_auth)):
    try:
        # Your logic here
        data = get_sensitive_data(user.member_id)
        return {"data": data}

    except HTTPException:
        # Re-raise FastAPI exceptions (auth errors)
        raise

    except Exception as e:
        # Catch and log other errors
        print(f"Error for user {user.member_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred processing your request"
        )
```

---

## Integration with Your Database

### Pattern: Link Stytch Users to Your Database

Most applications need to store additional user data beyond what Stytch provides.

### Data Flow: Authentication + Database Integration

```mermaid
sequenceDiagram
    participant Client
    participant FastAPI
    participant ayz_auth
    participant Stytch
    participant AppDB as Your Database

    Client->>FastAPI: GET /profile + Token
    FastAPI->>ayz_auth: verify_auth()
    ayz_auth->>Stytch: Verify token
    Stytch-->>ayz_auth: Session data
    ayz_auth-->>FastAPI: StytchContext (member_id, email, etc.)

    Note over FastAPI,AppDB: Now use member_id to fetch your data

    FastAPI->>AppDB: SELECT * WHERE stytch_member_id = ?
    AppDB-->>FastAPI: User profile data
    FastAPI->>FastAPI: Combine Stytch + App data
    FastAPI-->>Client: Complete user profile
```

#### Database Schema Example

```python
# Your users table/collection
{
    "_id": ObjectId("..."),
    "stytch_member_id": "member-live-abc123...",  # Link to Stytch
    "email": "user@example.com",
    "full_name": "John Doe",
    "avatar_url": "https://...",
    "preferences": {
        "theme": "dark",
        "notifications": true
    },
    "created_at": "2024-01-15T10:30:00Z",
    "last_login": "2024-01-20T15:45:00Z"
}
```

#### Implementation

```python
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import Depends

# Database connection
def get_database():
    client = AsyncIOMotorClient(os.getenv("MONGODB_URI"))
    return client.your_database_name

# Helper function to get your user record
async def get_app_user(stytch_context: StytchContext, db):
    """Fetch your application's user record"""
    user = await db.users.find_one({
        "stytch_member_id": stytch_context.member_id
    })

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found in application database"
        )

    return user

# Use in endpoints
@app.get("/profile")
async def get_profile(
    stytch_user: StytchContext = Depends(verify_auth),
    db=Depends(get_database)
):
    """Get user profile with both Stytch and app data"""

    # Get your application's user data
    app_user = await get_app_user(stytch_user, db)

    return {
        "stytch": {
            "member_id": stytch_user.member_id,
            "email": stytch_user.member_email,
            "organization_id": stytch_user.organization_id,
            "session_expires": stytch_user.session_expires_at
        },
        "profile": {
            "full_name": app_user["full_name"],
            "avatar": app_user["avatar_url"],
            "preferences": app_user["preferences"]
        }
    }
```

#### Create User on First Login

```python
@app.post("/auth/complete")
async def complete_authentication(
    stytch_user: StytchContext = Depends(verify_auth),
    db=Depends(get_database)
):
    """Called after Stytch login - create user if doesn't exist"""

    # Check if user exists in your database
    existing_user = await db.users.find_one({
        "stytch_member_id": stytch_user.member_id
    })

    if not existing_user:
        # First time login - create user record
        new_user = {
            "stytch_member_id": stytch_user.member_id,
            "email": stytch_user.member_email,
            "full_name": stytch_user.member_name or stytch_user.member_email,
            "preferences": {
                "theme": "light",
                "notifications": True
            },
            "created_at": datetime.now(timezone.utc),
            "last_login": datetime.now(timezone.utc)
        }

        result = await db.users.insert_one(new_user)
        user_id = str(result.inserted_id)
    else:
        # Update last login
        await db.users.update_one(
            {"_id": existing_user["_id"]},
            {"$set": {"last_login": datetime.now(timezone.utc)}}
        )
        user_id = str(existing_user["_id"])

    return {
        "status": "success",
        "user_id": user_id,
        "is_new_user": existing_user is None
    }
```

---

## Testing Your Implementation

### Unit Testing with Mocks

```python
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from datetime import datetime, timezone, timedelta

from main import app
from ayz_auth import StytchContext

client = TestClient(app)

@pytest.fixture
def mock_user():
    """Create a mock authenticated user"""
    return StytchContext(
        member_id="member-test-123",
        session_id="session-test-456",
        organization_id="org-test-789",
        member_email="test@example.com",
        member_name="Test User",
        session_started_at=datetime.now(timezone.utc),
        session_expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        session_last_accessed_at=datetime.now(timezone.utc),
        session_custom_claims={"admin": True},
        authentication_factors=["password"],
        raw_session_data={},
        # v2.0.0+ fields
        entitlements=["foresight", "byod"],
        subscription_tier="premium",
        subscription_limits={"max_projects": 50},
        current_team_id="team-123",
        current_team_name="Test Team",
        mongo_user_id="user-mongo-123",
        mongo_organization_id="org-mongo-456"
    )

def test_public_endpoint():
    """Test that public endpoint works without auth"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "This endpoint is public"}

def test_protected_endpoint_without_auth():
    """Test that protected endpoint rejects requests without auth"""
    response = client.get("/protected")
    assert response.status_code == 401

@patch('ayz_auth.middleware.verify_auth')
def test_protected_endpoint_with_auth(mock_verify_auth, mock_user):
    """Test that protected endpoint works with valid auth"""
    # Mock the verify_auth dependency
    mock_verify_auth.return_value = mock_user

    response = client.get(
        "/protected",
        headers={"Authorization": "Bearer fake_token"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "member-test-123"
    assert "test@example.com" in data["message"]

@patch('ayz_auth.middleware.verify_auth')
def test_entitlement_check(mock_verify_auth, mock_user):
    """Test entitlement-based authorization"""
    mock_verify_auth.return_value = mock_user

    # Should succeed - user has 'foresight' entitlement
    response = client.get(
        "/foresight/analyze",
        headers={"Authorization": "Bearer fake_token"}
    )
    assert response.status_code == 200

@patch('ayz_auth.middleware.verify_auth')
def test_missing_entitlement(mock_verify_auth, mock_user):
    """Test that missing entitlement returns 403"""
    # Remove foresight from user's entitlements
    mock_user.entitlements = ["byod"]
    mock_verify_auth.return_value = mock_user

    response = client.get(
        "/foresight/analyze",
        headers={"Authorization": "Bearer fake_token"}
    )
    assert response.status_code == 403
    assert "foresight" in response.json()["message"]
```

### Integration Testing

```python
import pytest
import os
from stytch import Client

# Only run if we have real credentials
pytestmark = pytest.mark.skipif(
    not os.getenv("STYTCH_PROJECT_ID"),
    reason="Requires real Stytch credentials"
)

@pytest.fixture
def stytch_client():
    """Create real Stytch client for integration tests"""
    return Client(
        project_id=os.getenv("STYTCH_PROJECT_ID"),
        secret=os.getenv("STYTCH_SECRET"),
        environment=os.getenv("STYTCH_ENV", "test")
    )

def test_real_authentication(stytch_client):
    """Test with real Stytch session (requires valid token)"""
    # Create a test session using Stytch SDK
    # This is simplified - actual implementation depends on your auth flow

    token = "real_session_token_from_stytch"

    response = client.get(
        "/protected",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
```

---

## Security Best Practices

### Security Architecture

```mermaid
graph TB
    subgraph "Client Side"
        Browser[Browser/App]
        LocalStorage[DO NOT Use localStorage]
        Cookie[✓ Use httpOnly Cookies]
    end

    subgraph "Network Layer"
        HTTPS[✓ Always Use HTTPS]
        HTTP[✗ Never Use HTTP]
    end

    subgraph "Server Side"
        FastAPI[FastAPI Server]
        EnvVars[✓ Environment Variables]
        HardCoded[✗ Hardcoded Secrets]
        Logs[✓ Safe Logging]
    end

    subgraph "External Services"
        Stytch[Stytch API]
        Redis[(Redis)]
        MongoDB[(MongoDB)]
    end

    Browser -->|Send Token| HTTPS
    HTTPS --> FastAPI
    FastAPI --> EnvVars
    FastAPI --> Stytch
    FastAPI --> Redis
    FastAPI --> MongoDB
    FastAPI --> Logs

    style LocalStorage fill:#faa
    style HTTP fill:#faa
    style HardCoded fill:#faa
    style Cookie fill:#afa
    style HTTPS fill:#afa
    style EnvVars fill:#afa
    style Logs fill:#afa
```

### 1. Environment Variables

**❌ Never commit secrets to git**:
```python
# DON'T DO THIS
STYTCH_SECRET = "secret-live-abc123..."  # Hardcoded secret!
```

**✅ Always use environment variables**:
```python
# .env file (add to .gitignore!)
STYTCH_SECRET=secret-live-abc123...

# .gitignore
.env
.env.local
.env.production
```

---

### 2. Logging

**❌ Never log sensitive data in production**:
```python
# DON'T DO THIS
STYTCH_LOG_SENSITIVE_DATA=true  # Will log tokens!
```

**✅ Only enable sensitive logging in development**:
```bash
# Production .env
STYTCH_LOG_LEVEL=INFO
STYTCH_LOG_SENSITIVE_DATA=false

# Development .env
STYTCH_LOG_LEVEL=DEBUG
STYTCH_LOG_SENSITIVE_DATA=true
```

---

### 3. HTTPS

**❌ Never send tokens over HTTP**:
```bash
# DON'T DO THIS
curl http://example.com/protected \
  -H "Authorization: Bearer token"
```

**✅ Always use HTTPS in production**:
```bash
curl https://example.com/protected \
  -H "Authorization: Bearer token"
```

---

### 4. CORS Configuration

**❌ Don't allow all origins in production**:
```python
# DON'T DO THIS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows any website!
    allow_credentials=True
)
```

**✅ Specify allowed origins**:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://yourdomain.com",
        "https://app.yourdomain.com"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"]
)
```

---

### 5. Token Storage (Frontend)

**❌ Don't store tokens in localStorage** (vulnerable to XSS):
```javascript
// DON'T DO THIS
localStorage.setItem('token', sessionToken)
```

**✅ Use httpOnly cookies or secure session storage**:
```javascript
// Backend sets httpOnly cookie
response.set_cookie(
    key="session",
    value=session_token,
    httponly=True,  # Not accessible via JavaScript
    secure=True,    # Only sent over HTTPS
    samesite="lax"
)
```

---

### 6. Error Messages

**❌ Don't leak sensitive info in errors**:
```python
# DON'T DO THIS
raise HTTPException(
    status_code=401,
    detail=f"Token {token} is invalid"  # Exposes token!
)
```

**✅ Use generic error messages**:
```python
# DO THIS
raise HTTPException(
    status_code=401,
    detail="Invalid or expired session token"
)
```

---

### 7. Rate Limiting

Add rate limiting to prevent brute force attacks:

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/protected")
@limiter.limit("100/minute")  # Max 100 requests per minute
async def protected_endpoint(
    request: Request,
    user: StytchContext = Depends(verify_auth)
):
    return {"message": "Success"}
```

---

## Troubleshooting

### Troubleshooting Decision Tree

```mermaid
flowchart TD
    Start[Having Issues?] --> Type{What's the problem?}

    Type -->|Can't start app| ConfigIssue[Configuration Issue]
    Type -->|401 errors| AuthIssue[Authentication Issue]
    Type -->|403 errors| PermissionIssue[Permission Issue]
    Type -->|Slow performance| PerformanceIssue[Performance Issue]
    Type -->|Entitlements not working| EntitlementIssue[Entitlement Issue]

    ConfigIssue --> CheckEnv{Env vars set?}
    CheckEnv -->|No| SetEnvVars[Set STYTCH_PROJECT_ID, STYTCH_SECRET, etc.]
    CheckEnv -->|Yes| CheckRedis{Redis running?}
    CheckRedis -->|No| StartRedis[Start Redis: redis-server]
    CheckRedis -->|Yes| CheckDotenv[Load .env with load_dotenv]

    AuthIssue --> CheckHeader{Auth header present?}
    CheckHeader -->|No| AddHeader[Add: Authorization: Bearer TOKEN]
    CheckHeader -->|Yes| CheckToken{Token valid?}
    CheckToken -->|No| GetNewToken[Get fresh token from Stytch]
    CheckToken -->|Yes| CheckStytch[Verify in Stytch Dashboard]

    PermissionIssue --> CheckClaims{Required claims?}
    CheckClaims -->|Yes| AddClaims[Add claims to session]
    CheckClaims -->|No| CheckEntitlements{Required entitlement?}
    CheckEntitlements -->|Yes| UpdateMongo[Update MongoDB entitlements]

    PerformanceIssue --> CheckCache{Redis working?}
    CheckCache -->|No| FixRedis[Fix Redis connection]
    CheckCache -->|Yes| CheckIndexes[Add MongoDB indexes]

    EntitlementIssue --> MongoSet{STYTCH_MONGODB_URI set?}
    MongoSet -->|No| SetMongo[Set MongoDB URI]
    MongoSet -->|Yes| CheckCollections{Collections exist?}
    CheckCollections -->|No| CreateCollections[Create organizations, users, teams]
    CheckCollections -->|Yes| CheckData[Verify stytch_org_id field]

    style SetEnvVars fill:#afa
    style StartRedis fill:#afa
    style AddHeader fill:#afa
    style GetNewToken fill:#afa
    style UpdateMongo fill:#afa
    style SetMongo fill:#afa
```

### Problem: "project_id is required" Error

**Symptoms**:
```
ValueError: project_id is required. Set STYTCH_PROJECT_ID environment variable.
```

**Solutions**:
1. Check `.env` file exists and has `STYTCH_PROJECT_ID`
2. Make sure you're calling `load_dotenv()` before importing `ayz_auth`
3. Verify environment variable is actually loaded: `print(os.getenv('STYTCH_PROJECT_ID'))`
4. Try setting variable directly: `export STYTCH_PROJECT_ID=your_id`

---

### Problem: Redis Connection Failed

**Symptoms**:
```
redis.exceptions.ConnectionError: Error connecting to Redis
```

**Solutions**:
1. Check if Redis is running: `redis-cli ping` (should return "PONG")
2. Start Redis: `redis-server` or `brew services start redis`
3. Check Redis URL in `.env`: `STYTCH_REDIS_URL=redis://localhost:6379`
4. If using Redis password: Set `STYTCH_REDIS_PASSWORD` in `.env`

---

### Problem: 401 Unauthorized on Protected Endpoints

**Symptoms**:
```json
{"error": "authentication_failed", "type": "token_extraction"}
```

**Solutions**:
1. **Check Authorization header format**:
   ```bash
   # Correct format
   curl -H "Authorization: Bearer YOUR_TOKEN_HERE" http://localhost:8000/protected
   ```

2. **Verify token is valid**:
   - Token might be expired
   - Token might be from wrong Stytch project
   - Get a fresh token from Stytch

3. **Test with curl**:
   ```bash
   # This should fail (no token)
   curl http://localhost:8000/protected

   # This should work (with token)
   curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/protected
   ```

---

### Problem: Entitlements Always None

**Symptoms**:
- `user.entitlements` is always `None`
- `user.subscription_tier` is always `None`

**Solutions**:
1. **Check MongoDB is configured**:
   ```bash
   # Must be set in .env
   STYTCH_MONGODB_URI=mongodb://localhost:27017/your_database
   ```

2. **Install MongoDB dependencies**:
   ```bash
   pip install 'ayz-auth[mongodb]'
   ```

3. **Verify MongoDB collections exist**:
   ```javascript
   // In MongoDB shell
   db.organizations.findOne()
   db.users.findOne()
   db.teams.findOne()
   ```

4. **Check MongoDB connection**:
   ```bash
   mongosh "mongodb://localhost:27017/your_database"
   ```

5. **Verify data has correct field names**:
   ```javascript
   // Must have these exact field names
   db.organizations.findOne({}, {
       stytch_org_id: 1,
       subscription_tier: 1,
       entitlements: 1
   })
   ```

---

### Problem: 403 Forbidden Despite Having Entitlement

**Symptoms**:
```json
{"error": "forbidden", "required_entitlement": "foresight"}
```

**Solutions**:
1. **Check exact spelling** (case-sensitive):
   ```python
   # These are different!
   "foresight" != "Foresight" != "FORESIGHT"
   ```

2. **Verify in MongoDB**:
   ```javascript
   db.organizations.findOne(
       { stytch_org_id: "organization-live-..." },
       { entitlements: 1 }
   )
   ```

3. **Check cache** (might be stale):
   ```bash
   # Clear Redis cache
   redis-cli FLUSHDB

   # Or wait for TTL (1 hour for org entitlements)
   ```

4. **Enable debug logging**:
   ```bash
   # In .env
   STYTCH_LOG_LEVEL=DEBUG

   # Check logs for entitlements loading
   ```

---

### Problem: Slow Authentication

**Symptoms**:
- First request takes >1 second
- Subsequent requests are fast

**This is normal behavior**:
- First request: Calls Stytch API + MongoDB (~50-100ms)
- Cached requests: Redis only (<10ms)

**To investigate further**:
1. **Check Redis performance**:
   ```bash
   redis-cli --latency
   ```

2. **Check MongoDB indexes**:
   ```javascript
   db.organizations.getIndexes()
   db.users.getIndexes()
   ```

3. **Monitor Stytch API latency** in Stytch Dashboard

---

## Complete Working Examples

### Example 1: Simple Blog API

```python
# blog_api.py
from fastapi import FastAPI, Depends, HTTPException
from typing import Optional, List
from dotenv import load_dotenv
from pydantic import BaseModel
from ayz_auth import verify_auth, verify_auth_optional, StytchContext

load_dotenv()
app = FastAPI(title="Blog API")

# Mock database
posts_db = []

class Post(BaseModel):
    title: str
    content: str
    author_id: Optional[str] = None

# Public - List all posts
@app.get("/posts")
async def list_posts():
    """Anyone can read posts"""
    return {"posts": posts_db}

# Public - Get single post
@app.get("/posts/{post_id}")
async def get_post(post_id: int):
    """Anyone can read a post"""
    if post_id >= len(posts_db):
        raise HTTPException(status_code=404, detail="Post not found")
    return posts_db[post_id]

# Protected - Create post (must be logged in)
@app.post("/posts")
async def create_post(
    post: Post,
    user: StytchContext = Depends(verify_auth)
):
    """Must be authenticated to create posts"""
    post.author_id = user.member_id
    posts_db.append(post.dict())
    return {
        "status": "created",
        "post_id": len(posts_db) - 1,
        "author": user.member_email
    }

# Protected - Update own post
@app.put("/posts/{post_id}")
async def update_post(
    post_id: int,
    post: Post,
    user: StytchContext = Depends(verify_auth)
):
    """Can only update your own posts"""
    if post_id >= len(posts_db):
        raise HTTPException(status_code=404, detail="Post not found")

    existing_post = posts_db[post_id]
    if existing_post["author_id"] != user.member_id:
        raise HTTPException(status_code=403, detail="Not your post")

    post.author_id = user.member_id
    posts_db[post_id] = post.dict()
    return {"status": "updated"}

# Optional auth - Different response based on auth
@app.get("/posts/{post_id}/view")
async def view_post(
    post_id: int,
    user: Optional[StytchContext] = Depends(verify_auth_optional)
):
    """Show extra info to authenticated users"""
    if post_id >= len(posts_db):
        raise HTTPException(status_code=404, detail="Post not found")

    post = posts_db[post_id]

    if user:
        # Authenticated - show full post + analytics
        return {
            "post": post,
            "can_edit": post["author_id"] == user.member_id,
            "viewer": user.member_email
        }
    else:
        # Anonymous - show post only
        return {"post": post}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

### Example 2: SaaS Application with Entitlements

```python
# saas_app.py
from fastapi import FastAPI, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

from ayz_auth import (
    verify_auth,
    require_entitlement,
    require_any_entitlement,
    StytchContext
)

load_dotenv()
app = FastAPI(title="SaaS Application")

# Database setup
@app.on_event("startup")
async def startup():
    app.mongodb_client = AsyncIOMotorClient(os.getenv("MONGODB_URI"))
    app.mongodb = app.mongodb_client.get_database()

@app.on_event("shutdown")
async def shutdown():
    app.mongodb_client.close()

def get_db():
    return app.mongodb

# Public endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to our SaaS platform"}

# Basic authenticated endpoint
@app.get("/dashboard")
async def dashboard(user: StytchContext = Depends(verify_auth)):
    """Basic dashboard - all authenticated users"""
    return {
        "user": user.member_email,
        "organization": user.organization_id,
        "subscription": user.subscription_tier,
        "features": user.entitlements or []
    }

# Feature requiring specific entitlement
@app.get("/analytics/basic")
async def basic_analytics(
    user: StytchContext = Depends(require_entitlement("analytics")),
    db=Depends(get_db)
):
    """Requires 'analytics' entitlement"""

    # Get user's data
    data = await db.analytics.find({
        "organization_id": user.mongo_organization_id
    }).limit(100).to_list()

    return {
        "analytics": data,
        "tier": user.subscription_tier
    }

# Feature requiring ANY of multiple entitlements
@app.get("/reports")
async def view_reports(
    user: StytchContext = Depends(
        require_any_entitlement("analytics", "reporting")
    ),
    db=Depends(get_db)
):
    """Requires 'analytics' OR 'reporting' entitlement"""

    reports = await db.reports.find({
        "organization_id": user.mongo_organization_id
    }).to_list()

    return {"reports": reports}

# Team-based data filtering
@app.get("/projects")
async def list_projects(
    user: StytchContext = Depends(verify_auth),
    db=Depends(get_db)
):
    """List projects filtered by team"""

    # Build query based on team
    if user.current_team_id:
        query = {"team_id": user.current_team_id}
        scope = f"Team: {user.current_team_name}"
    else:
        query = {"user_id": user.mongo_user_id}
        scope = "Personal"

    projects = await db.projects.find(query).to_list()

    return {
        "projects": projects,
        "scope": scope,
        "count": len(projects)
    }

# Subscription limit enforcement
@app.post("/projects")
async def create_project(
    name: str,
    user: StytchContext = Depends(verify_auth),
    db=Depends(get_db)
):
    """Create project with subscription limit check"""

    # Check subscription limits
    if user.subscription_limits:
        max_projects = user.subscription_limits.get("max_projects", 10)

        # Count existing projects
        count = await db.projects.count_documents({
            "organization_id": user.mongo_organization_id
        })

        # Check limit (unless unlimited)
        if max_projects != -1 and count >= max_projects:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "limit_exceeded",
                    "message": f"Your {user.subscription_tier} plan allows {max_projects} projects",
                    "current": count,
                    "limit": max_projects,
                    "upgrade_url": "/billing/upgrade"
                }
            )

    # Create project
    project = {
        "name": name,
        "organization_id": user.mongo_organization_id,
        "team_id": user.current_team_id,
        "created_by": user.mongo_user_id
    }

    result = await db.projects.insert_one(project)

    return {
        "status": "created",
        "project_id": str(result.inserted_id)
    }

# Frontend feature flags
@app.get("/features")
async def get_features(user: StytchContext = Depends(verify_auth)):
    """Feature flags for frontend"""

    entitlements = user.entitlements or []

    return {
        "user": {
            "id": user.member_id,
            "email": user.member_email,
            "tier": user.subscription_tier
        },
        "features": {
            "basic_analytics": True,
            "advanced_analytics": "analytics_pro" in entitlements,
            "data_export": "export" in entitlements,
            "api_access": "api" in entitlements,
            "custom_branding": user.subscription_tier in ["premium", "enterprise"],
            "team_features": user.current_team_id is not None
        },
        "limits": user.subscription_limits or {},
        "team": {
            "id": user.current_team_id,
            "name": user.current_team_name
        } if user.current_team_id else None
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

## Next Steps

1. **Read the Examples**: Study the [example_usage.py](example_usage.py) file in this repository
2. **Check Documentation**:
   - [Entitlements Guide](docs/entitlements.md) for advanced features
   - [Migration Guide](docs/migration-v2.md) if upgrading from v1.x
3. **Test Your Implementation**: Write tests using the patterns shown above
4. **Monitor Performance**: Set up logging and monitoring for authentication
5. **Read Stytch Docs**: [https://stytch.com/docs/b2b](https://stytch.com/docs/b2b)

## Getting Help

- **Package Issues**: [GitHub Issues](https://github.com/ayzenberg/ayz-auth/issues)
- **Stytch Issues**: [Stytch Support](https://stytch.com/support)
- **FastAPI Issues**: [FastAPI Documentation](https://fastapi.tiangolo.com)

---

**Last Updated**: January 2025
**Package Version**: 2.0.0
**Maintained by**: Ayzenberg
