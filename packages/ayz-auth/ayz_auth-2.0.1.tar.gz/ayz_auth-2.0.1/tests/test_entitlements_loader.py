"""
Tests for entitlements and user context data loading.
"""

import sys
from unittest.mock import AsyncMock, patch

import pytest

# Import these first to ensure they're in sys.modules
import ayz_auth.cache.redis_client  # noqa: F401
import ayz_auth.db.mongo_client  # noqa: F401
from ayz_auth.db.entitlements_loader import EntitlementsLoader

# Get the actual modules, not the instances that are re-exported in __init__.py
redis_client_module = sys.modules["ayz_auth.cache.redis_client"]
mongo_client_module = sys.modules["ayz_auth.db.mongo_client"]


class TestEntitlementsLoader:
    """Test cases for EntitlementsLoader."""

    @pytest.fixture
    def loader(self):
        """Create a fresh EntitlementsLoader instance for testing."""
        return EntitlementsLoader()

    # =====================================================================
    # load_organization_entitlements() Tests
    # =====================================================================

    @pytest.mark.asyncio
    async def test_load_organization_entitlements_from_cache(self, loader):
        """Test loading organization entitlements from Redis cache."""
        cached_data = {
            "entitlements": ["foresight", "byod"],
            "subscription_tier": "premium",
            "subscription_limits": {"max_projects": 50},
            "mongo_organization_id": "org_mongo_123",
        }

        with patch.object(
            redis_client_module.redis_client,
            "get_cached_organization_entitlements",
            new_callable=AsyncMock,
            return_value=cached_data,
        ):
            result = await loader.load_organization_entitlements(
                "organization-live-abc123"
            )

            assert result == cached_data

    @pytest.mark.asyncio
    async def test_load_organization_entitlements_from_mongodb(self, loader):
        """Test loading organization entitlements from MongoDB when cache misses."""
        org_doc = {
            "_id": "org_mongo_123",
            "stytch_org_id": "organization-live-abc123",
            "entitlements": ["foresight", "byod"],
            "subscription_tier": "premium",
            "subscription_limits": {"max_projects": 50},
        }

        expected_result = {
            "entitlements": ["foresight", "byod"],
            "subscription_tier": "premium",
            "subscription_limits": {"max_projects": 50},
            "mongo_organization_id": "org_mongo_123",
        }

        with patch.object(
            redis_client_module.redis_client,
            "get_cached_organization_entitlements",
            new_callable=AsyncMock,
            return_value=None,  # Cache miss
        ):
            with patch.object(
                mongo_client_module.mongo_client,
                "get_organization",
                new_callable=AsyncMock,
                return_value=org_doc,
            ):
                with patch.object(
                    redis_client_module.redis_client,
                    "cache_organization_entitlements",
                    new_callable=AsyncMock,
                ) as mock_cache:
                    result = await loader.load_organization_entitlements(
                        "organization-live-abc123"
                    )

                    assert result == expected_result
                    # Verify data was cached
                    mock_cache.assert_called_once_with(
                        "organization-live-abc123", expected_result
                    )

    @pytest.mark.asyncio
    async def test_load_organization_entitlements_org_not_found(self, loader):
        """Test loading organization entitlements when org not found in MongoDB."""
        with patch.object(
            redis_client_module.redis_client,
            "get_cached_organization_entitlements",
            new_callable=AsyncMock,
            return_value=None,
        ):
            with patch.object(
                mongo_client_module.mongo_client,
                "get_organization",
                new_callable=AsyncMock,
                return_value=None,  # Org not found
            ):
                result = await loader.load_organization_entitlements(
                    "organization-live-nonexistent"
                )

                assert result is None

    @pytest.mark.asyncio
    async def test_load_organization_entitlements_with_missing_fields(self, loader):
        """Test loading org entitlements when some fields are missing from MongoDB."""
        org_doc = {
            "_id": "org_mongo_123",
            "stytch_org_id": "organization-live-abc123",
            # Missing: entitlements, subscription_tier, subscription_limits
        }

        expected_result = {
            "entitlements": [],  # Default empty list
            "subscription_tier": None,
            "subscription_limits": {},  # Default empty dict
            "mongo_organization_id": "org_mongo_123",
        }

        with patch.object(
            redis_client_module.redis_client,
            "get_cached_organization_entitlements",
            new_callable=AsyncMock,
            return_value=None,
        ):
            with patch.object(
                mongo_client_module.mongo_client,
                "get_organization",
                new_callable=AsyncMock,
                return_value=org_doc,
            ):
                with patch.object(
                    redis_client_module.redis_client,
                    "cache_organization_entitlements",
                    new_callable=AsyncMock,
                ):
                    result = await loader.load_organization_entitlements(
                        "organization-live-abc123"
                    )

                    assert result == expected_result

    @pytest.mark.asyncio
    async def test_load_organization_entitlements_handles_exception(self, loader):
        """Test graceful handling of exceptions during org entitlements loading."""
        with patch.object(
            redis_client_module.redis_client,
            "get_cached_organization_entitlements",
            new_callable=AsyncMock,
            side_effect=Exception("Redis error"),
        ):
            result = await loader.load_organization_entitlements(
                "organization-live-abc123"
            )

            assert result is None

    # =====================================================================
    # load_user_context() Tests
    # =====================================================================

    @pytest.mark.asyncio
    async def test_load_user_context_from_mongodb_with_team(self, loader):
        """Test loading user context from MongoDB when user has a team."""
        user_doc = {
            "_id": "user_mongo_456",
            "stytch_member_id": "member-live-xyz789",
            "current_team_id": "team_mongo_123",
        }

        team_doc = {"_id": "team_mongo_123", "name": "Engineering Team"}

        expected_result = {
            "current_team_id": "team_mongo_123",
            "current_team_name": "Engineering Team",
            "mongo_user_id": "user_mongo_456",
        }

        with patch.object(
            mongo_client_module.mongo_client,
            "get_user",
            new_callable=AsyncMock,
            return_value=user_doc,
        ):
            with patch.object(
                mongo_client_module.mongo_client,
                "get_team",
                new_callable=AsyncMock,
                return_value=team_doc,
            ):
                result = await loader.load_user_context("member-live-xyz789")

                assert result == expected_result

    @pytest.mark.asyncio
    async def test_load_user_context_from_mongodb_without_team(self, loader):
        """Test loading user context when user has no team."""
        user_doc = {
            "_id": "user_mongo_456",
            "stytch_member_id": "member-live-xyz789",
            "current_team_id": None,  # No team
        }

        expected_result = {
            "current_team_id": None,
            "current_team_name": None,
            "mongo_user_id": "user_mongo_456",
        }

        with patch.object(
            mongo_client_module.mongo_client,
            "get_user",
            new_callable=AsyncMock,
            return_value=user_doc,
        ):
            result = await loader.load_user_context("member-live-xyz789")

            assert result == expected_result

    @pytest.mark.asyncio
    async def test_load_user_context_user_not_found(self, loader):
        """Test loading user context when user not found in MongoDB."""
        with patch.object(
            mongo_client_module.mongo_client,
            "get_user",
            new_callable=AsyncMock,
            return_value=None,  # User not found
        ):
            result = await loader.load_user_context("member-live-nonexistent")

            assert result is None

    @pytest.mark.asyncio
    async def test_load_user_context_team_not_found(self, loader):
        """Test loading user context when team doesn't exist."""
        user_doc = {
            "_id": "user_mongo_456",
            "stytch_member_id": "member-live-xyz789",
            "current_team_id": "team_nonexistent",
        }

        expected_result = {
            "current_team_id": "team_nonexistent",
            "current_team_name": None,  # Team not found
            "mongo_user_id": "user_mongo_456",
        }

        with patch.object(
            mongo_client_module.mongo_client,
            "get_user",
            new_callable=AsyncMock,
            return_value=user_doc,
        ):
            with patch.object(
                mongo_client_module.mongo_client,
                "get_team",
                new_callable=AsyncMock,
                return_value=None,  # Team not found
            ):
                result = await loader.load_user_context("member-live-xyz789")

                assert result == expected_result

    @pytest.mark.asyncio
    async def test_load_user_context_handles_exception(self, loader):
        """Test graceful handling of exceptions during user context loading."""
        with patch.object(
            mongo_client_module.mongo_client,
            "get_user",
            new_callable=AsyncMock,
            side_effect=Exception("MongoDB error"),
        ):
            result = await loader.load_user_context("member-live-xyz789")

            assert result is None

    # =====================================================================
    # load_complete_session_data() Tests
    # =====================================================================

    @pytest.mark.asyncio
    async def test_load_complete_session_data_success(self, loader):
        """Test loading complete session data with both org and user data."""
        org_data = {
            "entitlements": ["foresight", "byod"],
            "subscription_tier": "premium",
            "subscription_limits": {"max_projects": 50},
            "mongo_organization_id": "org_mongo_123",
        }

        user_data = {
            "current_team_id": "team_mongo_123",
            "current_team_name": "Engineering Team",
            "mongo_user_id": "user_mongo_456",
        }

        with patch.object(
            loader,
            "load_organization_entitlements",
            new_callable=AsyncMock,
            return_value=org_data,
        ):
            with patch.object(
                loader,
                "load_user_context",
                new_callable=AsyncMock,
                return_value=user_data,
            ):
                result = await loader.load_complete_session_data(
                    "organization-live-abc123", "member-live-xyz789"
                )

                expected = {
                    **org_data,
                    **user_data,
                }
                assert result == expected

    @pytest.mark.asyncio
    async def test_load_complete_session_data_parallel_loading(self, loader):
        """Test that org and user data are loaded in parallel."""
        org_data = {
            "entitlements": ["foresight"],
            "subscription_tier": "premium",
            "subscription_limits": {"max_projects": 50},
            "mongo_organization_id": "org_mongo_123",
        }

        user_data = {
            "current_team_id": "team_mongo_123",
            "current_team_name": "Engineering Team",
            "mongo_user_id": "user_mongo_456",
        }

        with patch.object(
            loader,
            "load_organization_entitlements",
            new_callable=AsyncMock,
            return_value=org_data,
        ) as mock_load_org:
            with patch.object(
                loader,
                "load_user_context",
                new_callable=AsyncMock,
                return_value=user_data,
            ) as mock_load_user:
                await loader.load_complete_session_data(
                    "organization-live-abc123", "member-live-xyz789"
                )

                # Both methods should be called
                mock_load_org.assert_called_once_with("organization-live-abc123")
                mock_load_user.assert_called_once_with("member-live-xyz789")

    @pytest.mark.asyncio
    async def test_load_complete_session_data_org_fails(self, loader):
        """Test complete session data loading when org loading fails."""
        user_data = {
            "current_team_id": "team_mongo_123",
            "current_team_name": "Engineering Team",
            "mongo_user_id": "user_mongo_456",
        }

        with patch.object(
            loader,
            "load_organization_entitlements",
            new_callable=AsyncMock,
            return_value=None,  # Org loading failed
        ):
            with patch.object(
                loader,
                "load_user_context",
                new_callable=AsyncMock,
                return_value=user_data,
            ):
                result = await loader.load_complete_session_data(
                    "organization-live-abc123", "member-live-xyz789"
                )

                # Should have user data but None for org fields
                assert result["entitlements"] is None
                assert result["subscription_tier"] is None
                assert result["subscription_limits"] is None
                assert result["mongo_organization_id"] is None
                assert result["current_team_id"] == "team_mongo_123"
                assert result["current_team_name"] == "Engineering Team"
                assert result["mongo_user_id"] == "user_mongo_456"

    @pytest.mark.asyncio
    async def test_load_complete_session_data_user_fails(self, loader):
        """Test complete session data loading when user loading fails."""
        org_data = {
            "entitlements": ["foresight"],
            "subscription_tier": "premium",
            "subscription_limits": {"max_projects": 50},
            "mongo_organization_id": "org_mongo_123",
        }

        with patch.object(
            loader,
            "load_organization_entitlements",
            new_callable=AsyncMock,
            return_value=org_data,
        ):
            with patch.object(
                loader,
                "load_user_context",
                new_callable=AsyncMock,
                return_value=None,  # User loading failed
            ):
                result = await loader.load_complete_session_data(
                    "organization-live-abc123", "member-live-xyz789"
                )

                # Should have org data but None for user fields
                assert result["entitlements"] == ["foresight"]
                assert result["subscription_tier"] == "premium"
                assert result["subscription_limits"] == {"max_projects": 50}
                assert result["mongo_organization_id"] == "org_mongo_123"
                assert result["current_team_id"] is None
                assert result["current_team_name"] is None
                assert result["mongo_user_id"] is None

    @pytest.mark.asyncio
    async def test_load_complete_session_data_both_fail(self, loader):
        """Test complete session data loading when both org and user loading fail."""
        with patch.object(
            loader,
            "load_organization_entitlements",
            new_callable=AsyncMock,
            return_value=None,
        ):
            with patch.object(
                loader, "load_user_context", new_callable=AsyncMock, return_value=None
            ):
                result = await loader.load_complete_session_data(
                    "organization-live-abc123", "member-live-xyz789"
                )

                # All fields should be None
                assert result["entitlements"] is None
                assert result["subscription_tier"] is None
                assert result["subscription_limits"] is None
                assert result["mongo_organization_id"] is None
                assert result["current_team_id"] is None
                assert result["current_team_name"] is None
                assert result["mongo_user_id"] is None

    @pytest.mark.asyncio
    async def test_load_complete_session_data_handles_exceptions(self, loader):
        """Test that exceptions in parallel loading are handled gracefully."""
        with patch.object(
            loader,
            "load_organization_entitlements",
            new_callable=AsyncMock,
            side_effect=Exception("Org loading error"),
        ):
            with patch.object(
                loader,
                "load_user_context",
                new_callable=AsyncMock,
                side_effect=Exception("User loading error"),
            ):
                result = await loader.load_complete_session_data(
                    "organization-live-abc123", "member-live-xyz789"
                )

                # Should return None for all fields without raising
                assert result["entitlements"] is None
                assert result["subscription_tier"] is None
                assert result["current_team_id"] is None
                assert result["mongo_user_id"] is None
