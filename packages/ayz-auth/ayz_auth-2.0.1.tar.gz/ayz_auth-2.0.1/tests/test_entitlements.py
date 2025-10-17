"""
Tests for entitlement-based authorization decorators.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from ayz_auth.decorators import (
    require_all_entitlements,
    require_any_entitlement,
    require_entitlement,
)
from ayz_auth.models.context import StytchContext

# Test FastAPI app
app = FastAPI()

# Create test endpoints with entitlement decorators
foresight_required = require_entitlement("foresight")
byod_required = require_entitlement("byod")
analytics_any = require_any_entitlement("foresight", "analytics_basic")
premium_all = require_all_entitlements("foresight", "advanced_analytics")


@app.get("/foresight")
async def foresight_endpoint(user: StytchContext = Depends(foresight_required)):
    return {"message": "foresight access granted", "member_id": user.member_id}


@app.get("/byod")
async def byod_endpoint(user: StytchContext = Depends(byod_required)):
    return {"message": "byod access granted"}


@app.get("/analytics")
async def analytics_endpoint(user: StytchContext = Depends(analytics_any)):
    return {"message": "analytics access granted"}


@app.get("/premium")
async def premium_endpoint(user: StytchContext = Depends(premium_all)):
    return {"message": "premium access granted"}


client = TestClient(app)


class TestEntitlementDecorators:
    """Test cases for entitlement decorators."""

    def create_mock_stytch_context(self, **kwargs):
        """Create a mock StytchContext for testing."""
        defaults = {
            "member_id": "member_123",
            "session_id": "session_456",
            "organization_id": "org_789",
            "session_started_at": datetime.now(timezone.utc) - timedelta(hours=1),
            "session_expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
            "session_last_accessed_at": datetime.now(timezone.utc),
            "member_email": "test@example.com",
            "member_name": "Test User",
            "session_custom_claims": {},
            "authentication_factors": ["password"],
            "raw_session_data": {},
            "entitlements": ["foresight", "byod"],  # Default entitlements
            "subscription_tier": "premium",
            "subscription_limits": {"max_projects": 50},
            "current_team_id": "team_123",
            "current_team_name": "Test Team",
            "mongo_user_id": "user_mongo_123",
            "mongo_organization_id": "org_mongo_789",
        }
        defaults.update(kwargs)
        return StytchContext(**defaults)

    # =====================================================================
    # require_entitlement() Tests
    # =====================================================================

    @patch("ayz_auth.middleware.stytch_verifier.verify_session_token")
    @patch("ayz_auth.middleware.extract_token_from_request")
    def test_require_entitlement_with_valid_entitlement(
        self, mock_extract, mock_verify
    ):
        """Test that user with required entitlement can access endpoint."""
        mock_context = self.create_mock_stytch_context(
            entitlements=["foresight", "byod"]
        )
        mock_extract.return_value = "valid_token_12345678901234567890"
        mock_verify.return_value = mock_context

        response = client.get(
            "/foresight",
            headers={"Authorization": "Bearer valid_token_12345678901234567890"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "foresight access granted"
        assert data["member_id"] == "member_123"

    @patch("ayz_auth.middleware.stytch_verifier.verify_session_token")
    @patch("ayz_auth.middleware.extract_token_from_request")
    def test_require_entitlement_missing_entitlement(self, mock_extract, mock_verify):
        """Test that user without required entitlement gets 403."""
        mock_context = self.create_mock_stytch_context(
            entitlements=["byod"]  # Has byod but not foresight
        )
        mock_extract.return_value = "valid_token_12345678901234567890"
        mock_verify.return_value = mock_context

        response = client.get(
            "/foresight",
            headers={"Authorization": "Bearer valid_token_12345678901234567890"},
        )

        assert response.status_code == 403
        data = response.json()
        assert data["detail"]["error"] == "forbidden"
        assert "foresight" in data["detail"]["message"]
        assert data["detail"]["required_entitlement"] == "foresight"
        assert data["detail"]["current_tier"] == "premium"
        assert data["detail"]["upgrade_required"] is True

    @patch("ayz_auth.middleware.stytch_verifier.verify_session_token")
    @patch("ayz_auth.middleware.extract_token_from_request")
    def test_require_entitlement_entitlements_none(self, mock_extract, mock_verify):
        """Test that MongoDB not configured (entitlements=None) returns 403."""
        mock_context = self.create_mock_stytch_context(
            entitlements=None,  # MongoDB not configured
            subscription_tier=None,
        )
        mock_extract.return_value = "valid_token_12345678901234567890"
        mock_verify.return_value = mock_context

        response = client.get(
            "/foresight",
            headers={"Authorization": "Bearer valid_token_12345678901234567890"},
        )

        assert response.status_code == 403
        data = response.json()
        assert data["detail"]["error"] == "forbidden"
        assert "not configured" in data["detail"]["message"]
        assert data["detail"]["required_entitlement"] == "foresight"
        assert data["detail"]["current_tier"] is None

    @patch("ayz_auth.middleware.stytch_verifier.verify_session_token")
    @patch("ayz_auth.middleware.extract_token_from_request")
    def test_require_entitlement_empty_entitlements_list(
        self, mock_extract, mock_verify
    ):
        """Test that empty entitlements list returns 403."""
        mock_context = self.create_mock_stytch_context(
            entitlements=[],  # No entitlements
            subscription_tier="free",
        )
        mock_extract.return_value = "valid_token_12345678901234567890"
        mock_verify.return_value = mock_context

        response = client.get(
            "/foresight",
            headers={"Authorization": "Bearer valid_token_12345678901234567890"},
        )

        assert response.status_code == 403
        data = response.json()
        assert data["detail"]["error"] == "forbidden"
        assert data["detail"]["current_tier"] == "free"

    # =====================================================================
    # require_any_entitlement() Tests
    # =====================================================================

    @patch("ayz_auth.middleware.stytch_verifier.verify_session_token")
    @patch("ayz_auth.middleware.extract_token_from_request")
    def test_require_any_entitlement_with_first_entitlement(
        self, mock_extract, mock_verify
    ):
        """Test that user with first of multiple entitlements can access."""
        mock_context = self.create_mock_stytch_context(
            entitlements=["foresight"]  # Has foresight, not analytics_basic
        )
        mock_extract.return_value = "valid_token_12345678901234567890"
        mock_verify.return_value = mock_context

        response = client.get(
            "/analytics",
            headers={"Authorization": "Bearer valid_token_12345678901234567890"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "analytics access granted"

    @patch("ayz_auth.middleware.stytch_verifier.verify_session_token")
    @patch("ayz_auth.middleware.extract_token_from_request")
    def test_require_any_entitlement_with_second_entitlement(
        self, mock_extract, mock_verify
    ):
        """Test that user with second of multiple entitlements can access."""
        mock_context = self.create_mock_stytch_context(
            entitlements=["analytics_basic"]  # Has analytics_basic, not foresight
        )
        mock_extract.return_value = "valid_token_12345678901234567890"
        mock_verify.return_value = mock_context

        response = client.get(
            "/analytics",
            headers={"Authorization": "Bearer valid_token_12345678901234567890"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "analytics access granted"

    @patch("ayz_auth.middleware.stytch_verifier.verify_session_token")
    @patch("ayz_auth.middleware.extract_token_from_request")
    def test_require_any_entitlement_with_both(self, mock_extract, mock_verify):
        """Test that user with both entitlements can access."""
        mock_context = self.create_mock_stytch_context(
            entitlements=["foresight", "analytics_basic"]
        )
        mock_extract.return_value = "valid_token_12345678901234567890"
        mock_verify.return_value = mock_context

        response = client.get(
            "/analytics",
            headers={"Authorization": "Bearer valid_token_12345678901234567890"},
        )

        assert response.status_code == 200

    @patch("ayz_auth.middleware.stytch_verifier.verify_session_token")
    @patch("ayz_auth.middleware.extract_token_from_request")
    def test_require_any_entitlement_with_neither(self, mock_extract, mock_verify):
        """Test that user without any required entitlements gets 403."""
        mock_context = self.create_mock_stytch_context(
            entitlements=["byod"]  # Has byod but neither foresight nor analytics_basic
        )
        mock_extract.return_value = "valid_token_12345678901234567890"
        mock_verify.return_value = mock_context

        response = client.get(
            "/analytics",
            headers={"Authorization": "Bearer valid_token_12345678901234567890"},
        )

        assert response.status_code == 403
        data = response.json()
        assert data["detail"]["error"] == "forbidden"
        assert "foresight" in data["detail"]["message"]
        assert "analytics_basic" in data["detail"]["message"]
        assert data["detail"]["required_entitlements"] == [
            "foresight",
            "analytics_basic",
        ]

    @patch("ayz_auth.middleware.stytch_verifier.verify_session_token")
    @patch("ayz_auth.middleware.extract_token_from_request")
    def test_require_any_entitlement_entitlements_none(self, mock_extract, mock_verify):
        """Test require_any with entitlements=None returns 403."""
        mock_context = self.create_mock_stytch_context(
            entitlements=None, subscription_tier=None
        )
        mock_extract.return_value = "valid_token_12345678901234567890"
        mock_verify.return_value = mock_context

        response = client.get(
            "/analytics",
            headers={"Authorization": "Bearer valid_token_12345678901234567890"},
        )

        assert response.status_code == 403
        data = response.json()
        assert data["detail"]["error"] == "forbidden"
        assert "not configured" in data["detail"]["message"]

    # =====================================================================
    # require_all_entitlements() Tests
    # =====================================================================

    @patch("ayz_auth.middleware.stytch_verifier.verify_session_token")
    @patch("ayz_auth.middleware.extract_token_from_request")
    def test_require_all_entitlements_with_both(self, mock_extract, mock_verify):
        """Test that user with all required entitlements can access."""
        mock_context = self.create_mock_stytch_context(
            entitlements=["foresight", "advanced_analytics", "byod"]
        )
        mock_extract.return_value = "valid_token_12345678901234567890"
        mock_verify.return_value = mock_context

        response = client.get(
            "/premium",
            headers={"Authorization": "Bearer valid_token_12345678901234567890"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "premium access granted"

    @patch("ayz_auth.middleware.stytch_verifier.verify_session_token")
    @patch("ayz_auth.middleware.extract_token_from_request")
    def test_require_all_entitlements_missing_one(self, mock_extract, mock_verify):
        """Test that user missing one required entitlement gets 403."""
        mock_context = self.create_mock_stytch_context(
            entitlements=["foresight"]  # Has foresight but not advanced_analytics
        )
        mock_extract.return_value = "valid_token_12345678901234567890"
        mock_verify.return_value = mock_context

        response = client.get(
            "/premium",
            headers={"Authorization": "Bearer valid_token_12345678901234567890"},
        )

        assert response.status_code == 403
        data = response.json()
        assert data["detail"]["error"] == "forbidden"
        assert "foresight" in data["detail"]["message"]
        assert "advanced_analytics" in data["detail"]["message"]
        assert data["detail"]["required_entitlements"] == [
            "foresight",
            "advanced_analytics",
        ]
        assert data["detail"]["missing_entitlements"] == ["advanced_analytics"]

    @patch("ayz_auth.middleware.stytch_verifier.verify_session_token")
    @patch("ayz_auth.middleware.extract_token_from_request")
    def test_require_all_entitlements_missing_both(self, mock_extract, mock_verify):
        """Test that user missing all required entitlements gets 403."""
        mock_context = self.create_mock_stytch_context(
            entitlements=["byod"]  # Has byod but neither required entitlement
        )
        mock_extract.return_value = "valid_token_12345678901234567890"
        mock_verify.return_value = mock_context

        response = client.get(
            "/premium",
            headers={"Authorization": "Bearer valid_token_12345678901234567890"},
        )

        assert response.status_code == 403
        data = response.json()
        assert data["detail"]["error"] == "forbidden"
        assert data["detail"]["missing_entitlements"] == [
            "foresight",
            "advanced_analytics",
        ]

    @patch("ayz_auth.middleware.stytch_verifier.verify_session_token")
    @patch("ayz_auth.middleware.extract_token_from_request")
    def test_require_all_entitlements_entitlements_none(
        self, mock_extract, mock_verify
    ):
        """Test require_all with entitlements=None returns 403."""
        mock_context = self.create_mock_stytch_context(
            entitlements=None, subscription_tier=None
        )
        mock_extract.return_value = "valid_token_12345678901234567890"
        mock_verify.return_value = mock_context

        response = client.get(
            "/premium",
            headers={"Authorization": "Bearer valid_token_12345678901234567890"},
        )

        assert response.status_code == 403
        data = response.json()
        assert data["detail"]["error"] == "forbidden"
        assert "not configured" in data["detail"]["message"]

    # =====================================================================
    # Integration Tests
    # =====================================================================

    @patch("ayz_auth.middleware.stytch_verifier.verify_session_token")
    @patch("ayz_auth.middleware.extract_token_from_request")
    def test_multiple_endpoints_different_entitlements(self, mock_extract, mock_verify):
        """Test that same user can access different endpoints based on entitlements."""
        mock_context = self.create_mock_stytch_context(
            entitlements=["foresight", "byod"]
        )
        mock_extract.return_value = "valid_token_12345678901234567890"
        mock_verify.return_value = mock_context

        # Should succeed - has foresight
        response = client.get(
            "/foresight",
            headers={"Authorization": "Bearer valid_token_12345678901234567890"},
        )
        assert response.status_code == 200

        # Should succeed - has byod
        response = client.get(
            "/byod",
            headers={"Authorization": "Bearer valid_token_12345678901234567890"},
        )
        assert response.status_code == 200

        # Should succeed - has foresight (one of the required)
        response = client.get(
            "/analytics",
            headers={"Authorization": "Bearer valid_token_12345678901234567890"},
        )
        assert response.status_code == 200

        # Should fail - missing advanced_analytics
        response = client.get(
            "/premium",
            headers={"Authorization": "Bearer valid_token_12345678901234567890"},
        )
        assert response.status_code == 403

    @patch("ayz_auth.middleware.stytch_verifier.verify_session_token")
    @patch("ayz_auth.middleware.extract_token_from_request")
    def test_subscription_tier_in_error_response(self, mock_extract, mock_verify):
        """Test that subscription tier is included in 403 error responses."""
        mock_context = self.create_mock_stytch_context(
            entitlements=[], subscription_tier="standard"
        )
        mock_extract.return_value = "valid_token_12345678901234567890"
        mock_verify.return_value = mock_context

        response = client.get(
            "/foresight",
            headers={"Authorization": "Bearer valid_token_12345678901234567890"},
        )

        assert response.status_code == 403
        data = response.json()
        assert data["detail"]["current_tier"] == "standard"
        assert data["detail"]["upgrade_required"] is True

    @patch("ayz_auth.middleware.stytch_verifier.verify_session_token")
    @patch("ayz_auth.middleware.extract_token_from_request")
    def test_case_sensitive_entitlement_names(self, mock_extract, mock_verify):
        """Test that entitlement names are case-sensitive."""
        mock_context = self.create_mock_stytch_context(
            entitlements=["Foresight", "BYOD"]  # Wrong case
        )
        mock_extract.return_value = "valid_token_12345678901234567890"
        mock_verify.return_value = mock_context

        # Should fail - case mismatch
        response = client.get(
            "/foresight",
            headers={"Authorization": "Bearer valid_token_12345678901234567890"},
        )
        assert response.status_code == 403

        response = client.get(
            "/byod",
            headers={"Authorization": "Bearer valid_token_12345678901234567890"},
        )
        assert response.status_code == 403
