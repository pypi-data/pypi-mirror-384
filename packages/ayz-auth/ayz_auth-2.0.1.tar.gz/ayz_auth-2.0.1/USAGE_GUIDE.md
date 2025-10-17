# ayz-auth Usage Guide

This guide shows exactly how end users will install and import the ayz-auth package in their FastAPI applications.

## 📦 Installation

### For End Users
```bash
# Install from PyPI
pip install ayz-auth

# Or with UV
uv add ayz-auth

# Or with Poetry
poetry add ayz-auth
```

### Dependencies
The package automatically installs these dependencies:
- `fastapi>=0.100.0`
- `pydantic>=2.0.0`
- `pydantic-settings>=2.0.0`
- `stytch>=5.0.0`
- `redis>=4.5.0`
- `httpx>=0.24.0`
- `python-multipart>=0.0.6`

## 🔧 Environment Setup

Create a `.env` file or set environment variables:
```bash
STYTCH_PROJECT_ID=your_stytch_project_id
STYTCH_SECRET=your_stytch_secret_key
STYTCH_ENV=test  # or "live" for production
STYTCH_REDIS_URL=redis://localhost:6379  # optional
```

## 📋 Import Patterns

### Basic Imports
```python
# Main authentication dependency
from ayz_auth import verify_auth

# Stytch context model
from ayz_auth import StytchContext

# Optional authentication
from ayz_auth import verify_auth_optional

# Custom authentication factory
from ayz_auth import create_auth_dependency

# All in one import
from ayz_auth import (
    verify_auth,
    verify_auth_optional, 
    create_auth_dependency,
    StytchContext
)
```

### Exception Imports (Optional)
```python
# For custom error handling
from ayz_auth import (
    AuthenticationError,
    TokenExtractionError,
    TokenVerificationError,
    StytchAPIError
)
```

## 🚀 Usage Examples

### 1. Basic Protected Route
```python
from fastapi import FastAPI, Depends
from ayz_auth import verify_auth, StytchContext

app = FastAPI()

@app.get("/protected")
async def protected_route(user: StytchContext = Depends(verify_auth)):
    return {
        "message": f"Hello {user.member_email}!",
        "member_id": user.member_id,
        "organization_id": user.organization_id
    }
```

### 2. Optional Authentication
```python
from typing import Optional
from ayz_auth import verify_auth_optional

@app.get("/optional")
async def optional_route(user: Optional[StytchContext] = Depends(verify_auth_optional)):
    if user:
        return {"authenticated": True, "user": user.member_id}
    else:
        return {"authenticated": False, "message": "Public access"}
```

### 3. Custom Authentication Requirements
```python
from ayz_auth import create_auth_dependency

# Require admin claims
admin_auth = create_auth_dependency(required_claims=["admin"])

@app.get("/admin")
async def admin_route(user: StytchContext = Depends(admin_auth)):
    return {"message": "Admin access granted"}

# Require MFA
mfa_auth = create_auth_dependency(required_factors=["mfa"])

@app.get("/secure")
async def secure_route(user: StytchContext = Depends(mfa_auth)):
    return {"message": "MFA verified"}
```

### 4. Integration with Your User System
```python
from your_app.database import get_user_by_stytch_member_id

@app.get("/profile")
async def get_profile(stytch_user: StytchContext = Depends(verify_auth)):
    # Use Stytch member_id to fetch your user data
    app_user = await get_user_by_stytch_member_id(stytch_user.member_id)
    
    if not app_user:
        raise HTTPException(404, "User not found in our system")
    
    return {
        "stytch_session": {
            "member_id": stytch_user.member_id,
            "expires_at": stytch_user.session_expires_at
        },
        "user_profile": app_user.to_dict()
    }
```

### 5. Error Handling
```python
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from ayz_auth import AuthenticationError

@app.exception_handler(AuthenticationError)
async def auth_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "details": exc.details
        }
    )
```

## 🔍 Available Data in StytchContext

When you use `verify_auth`, you get a `StytchContext` object with:

```python
class StytchContext:
    # Core identifiers
    member_id: str                    # Use this to fetch your user data
    session_id: str
    organization_id: str
    
    # Session timing
    session_started_at: datetime
    session_expires_at: datetime
    session_last_accessed_at: datetime
    authenticated_at: datetime        # When this context was created
    
    # Member info from Stytch
    member_email: Optional[str]
    member_name: Optional[str]
    
    # Session metadata
    session_custom_claims: Dict[str, Any]
    authentication_factors: List[str]
    raw_session_data: Dict[str, Any]  # Complete raw session response from Stytch
    
    # Utility properties
    @property
    def is_expired(self) -> bool: ...
    
    @property 
    def time_until_expiry(self) -> Optional[float]: ...
```

## ⚙️ Configuration Options

All configuration is via environment variables with `STYTCH_` prefix:

```python
# These are automatically loaded by the package
STYTCH_PROJECT_ID=required
STYTCH_SECRET=required
STYTCH_ENV=test  # or "live"
STYTCH_REDIS_URL=redis://localhost:6379
STYTCH_CACHE_TTL=300  # seconds
STYTCH_LOG_LEVEL=INFO
```

## 🔄 Complete FastAPI App Example

```python
from fastapi import FastAPI, Depends, HTTPException
from typing import Optional
from ayz_auth import (
    verify_auth, 
    verify_auth_optional, 
    create_auth_dependency,
    StytchContext
)

app = FastAPI(title="My App with Stytch Auth")

# Custom auth dependencies
admin_auth = create_auth_dependency(required_claims=["admin"])
mfa_auth = create_auth_dependency(required_factors=["mfa"])

@app.get("/")
async def public_endpoint():
    return {"message": "Public access"}

@app.get("/protected")
async def protected_endpoint(user: StytchContext = Depends(verify_auth)):
    return {
        "message": f"Hello {user.member_email}",
        "member_id": user.member_id,
        "session_expires": user.session_expires_at.isoformat()
    }

@app.get("/optional")
async def optional_endpoint(user: Optional[StytchContext] = Depends(verify_auth_optional)):
    if user:
        return {"authenticated": True, "user": user.member_id}
    return {"authenticated": False}

@app.get("/admin")
async def admin_endpoint(user: StytchContext = Depends(admin_auth)):
    return {"message": "Admin access", "claims": user.session_custom_claims}

@app.get("/secure")
async def secure_endpoint(user: StytchContext = Depends(mfa_auth)):
    return {"message": "MFA verified", "factors": user.authentication_factors}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## 🧪 Testing Your Integration

```python
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

def test_protected_endpoint():
    with patch('ayz_auth.verify_auth') as mock_auth:
        # Mock the authentication
        mock_auth.return_value = StytchContext(
            member_id="test_member",
            session_id="test_session",
            organization_id="test_org",
            # ... other required fields
        )
        
        client = TestClient(app)
        response = client.get(
            "/protected",
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 200
        assert response.json()["member_id"] == "test_member"
```

## 📚 Additional Resources

- **Package Documentation**: Available on PyPI
- **Stytch B2B Docs**: [https://stytch.com/docs/b2b](https://stytch.com/docs/b2b)
- **FastAPI Docs**: [https://fastapi.tiangolo.com](https://fastapi.tiangolo.com)
- **Example Repository**: See `example_usage.py` in the package
