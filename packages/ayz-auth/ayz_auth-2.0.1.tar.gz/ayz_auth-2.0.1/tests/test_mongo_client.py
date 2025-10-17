"""
Tests for MongoDB client and operations.
"""

import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ayz_auth.db.mongo_client import MongoClient
from ayz_auth.utils.exceptions import ConfigurationError

# Get the actual module, not the instance that's re-exported in __init__.py
mongo_client_module = sys.modules["ayz_auth.db.mongo_client"]


class TestMongoClient:
    """Test cases for MongoClient."""

    @pytest.fixture
    def mock_mongo_client(self):
        """Create a fresh MongoClient instance for testing."""
        return MongoClient()

    @pytest.fixture
    def mock_settings_with_mongodb(self):
        """Mock settings with MongoDB URI configured."""
        with patch.object(
            mongo_client_module, "settings", create=False
        ) as mock_settings:
            mock_settings.mongodb_uri = "mongodb://localhost:27017/testdb"
            yield mock_settings

    @pytest.fixture
    def mock_settings_without_mongodb(self):
        """Mock settings without MongoDB URI."""
        with patch.object(
            mongo_client_module, "settings", create=False
        ) as mock_settings:
            mock_settings.mongodb_uri = None
            yield mock_settings

    # =====================================================================
    # Connection Tests
    # =====================================================================

    @pytest.mark.asyncio
    async def test_get_client_returns_none_when_not_configured(
        self, mock_mongo_client, mock_settings_without_mongodb
    ):
        """Test that _get_client returns None when MongoDB URI not configured."""
        result = await mock_mongo_client._get_client()
        assert result is None
        assert not mock_mongo_client.is_available

    @pytest.mark.asyncio
    async def test_get_client_raises_error_when_motor_not_installed(
        self, mock_mongo_client, mock_settings_with_mongodb
    ):
        """Test that _get_client raises ConfigurationError if motor not installed."""
        with patch.object(mongo_client_module, "MOTOR_AVAILABLE", False):
            with pytest.raises(ConfigurationError) as exc_info:
                await mock_mongo_client._get_client()

            assert "motor" in str(exc_info.value)
            assert "pip install 'ayz-auth[mongodb]'" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_client_creates_connection(
        self, mock_mongo_client, mock_settings_with_mongodb
    ):
        """Test successful MongoDB connection creation."""
        # Mock the AsyncIOMotorClient
        mock_motor_client = AsyncMock()
        mock_motor_client.admin.command = AsyncMock(return_value={"ok": 1})
        mock_db = MagicMock()
        mock_motor_client.__getitem__ = MagicMock(return_value=mock_db)

        with patch.object(mongo_client_module, "MOTOR_AVAILABLE", True):
            with patch.object(
                mongo_client_module,
                "AsyncIOMotorClient",
                return_value=mock_motor_client,
            ):
                result = await mock_mongo_client._get_client()

                assert result is not None
                assert result == mock_db
                assert mock_mongo_client.is_available
                # Verify ping was called to test connection
                mock_motor_client.admin.command.assert_called_once_with("ping")

    @pytest.mark.asyncio
    async def test_get_client_handles_connection_failure(
        self, mock_mongo_client, mock_settings_with_mongodb
    ):
        """Test graceful handling of MongoDB connection failures."""
        with patch.object(mongo_client_module, "MOTOR_AVAILABLE", True):
            with patch.object(
                mongo_client_module,
                "AsyncIOMotorClient",
                side_effect=Exception("Connection failed"),
            ):
                result = await mock_mongo_client._get_client()

                assert result is None
                assert not mock_mongo_client.is_available

    @pytest.mark.asyncio
    async def test_get_client_caches_connection(
        self, mock_mongo_client, mock_settings_with_mongodb
    ):
        """Test that MongoDB client is cached and reused."""
        mock_motor_client = AsyncMock()
        mock_motor_client.admin.command = AsyncMock(return_value={"ok": 1})
        mock_db = MagicMock()
        mock_motor_client.__getitem__ = MagicMock(return_value=mock_db)

        with patch.object(mongo_client_module, "MOTOR_AVAILABLE", True):
            with patch.object(
                mongo_client_module,
                "AsyncIOMotorClient",
                return_value=mock_motor_client,
            ) as mock_motor_class:
                # First call
                result1 = await mock_mongo_client._get_client()
                # Second call
                result2 = await mock_mongo_client._get_client()

                assert result1 == result2
                # AsyncIOMotorClient should only be called once
                assert mock_motor_class.call_count == 1

    # =====================================================================
    # get_organization() Tests
    # =====================================================================

    @pytest.mark.asyncio
    async def test_get_organization_success(
        self, mock_mongo_client, mock_settings_with_mongodb
    ):
        """Test successful organization retrieval."""
        org_data = {
            "_id": "org_mongo_id",
            "stytch_org_id": "organization-live-abc123",
            "subscription_tier": "premium",
            "entitlements": ["foresight", "byod"],
            "subscription_limits": {"max_projects": 50},
        }

        mock_db = MagicMock()
        mock_collection = AsyncMock()
        mock_collection.find_one = AsyncMock(return_value=org_data)
        mock_db.organizations = mock_collection

        with patch.object(mock_mongo_client, "_get_client", return_value=mock_db):
            result = await mock_mongo_client.get_organization(
                "organization-live-abc123"
            )

            assert result == org_data
            mock_collection.find_one.assert_called_once_with(
                {"stytch_org_id": "organization-live-abc123"}
            )

    @pytest.mark.asyncio
    async def test_get_organization_not_found(
        self, mock_mongo_client, mock_settings_with_mongodb
    ):
        """Test organization retrieval when org doesn't exist."""
        mock_db = MagicMock()
        mock_collection = AsyncMock()
        mock_collection.find_one = AsyncMock(return_value=None)
        mock_db.organizations = mock_collection

        with patch.object(mock_mongo_client, "_get_client", return_value=mock_db):
            result = await mock_mongo_client.get_organization(
                "organization-live-nonexistent"
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_get_organization_mongodb_not_configured(
        self, mock_mongo_client, mock_settings_without_mongodb
    ):
        """Test get_organization returns None when MongoDB not configured."""
        result = await mock_mongo_client.get_organization("organization-live-abc123")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_organization_handles_exception(
        self, mock_mongo_client, mock_settings_with_mongodb
    ):
        """Test graceful handling of exceptions during org retrieval."""
        mock_db = MagicMock()
        mock_collection = AsyncMock()
        mock_collection.find_one = AsyncMock(
            side_effect=Exception("Database query failed")
        )
        mock_db.organizations = mock_collection

        with patch.object(mock_mongo_client, "_get_client", return_value=mock_db):
            result = await mock_mongo_client.get_organization(
                "organization-live-abc123"
            )

            assert result is None

    # =====================================================================
    # get_user() Tests
    # =====================================================================

    @pytest.mark.asyncio
    async def test_get_user_success(
        self, mock_mongo_client, mock_settings_with_mongodb
    ):
        """Test successful user retrieval."""
        user_data = {
            "_id": "user_mongo_id",
            "stytch_member_id": "member-live-xyz789",
            "current_team_id": "team_mongo_id",
        }

        mock_db = MagicMock()
        mock_collection = AsyncMock()
        mock_collection.find_one = AsyncMock(return_value=user_data)
        mock_db.users = mock_collection

        with patch.object(mock_mongo_client, "_get_client", return_value=mock_db):
            result = await mock_mongo_client.get_user("member-live-xyz789")

            assert result == user_data
            mock_collection.find_one.assert_called_once_with(
                {"stytch_member_id": "member-live-xyz789"}
            )

    @pytest.mark.asyncio
    async def test_get_user_not_found(
        self, mock_mongo_client, mock_settings_with_mongodb
    ):
        """Test user retrieval when user doesn't exist."""
        mock_db = MagicMock()
        mock_collection = AsyncMock()
        mock_collection.find_one = AsyncMock(return_value=None)
        mock_db.users = mock_collection

        with patch.object(mock_mongo_client, "_get_client", return_value=mock_db):
            result = await mock_mongo_client.get_user("member-live-nonexistent")

            assert result is None

    @pytest.mark.asyncio
    async def test_get_user_mongodb_not_configured(
        self, mock_mongo_client, mock_settings_without_mongodb
    ):
        """Test get_user returns None when MongoDB not configured."""
        result = await mock_mongo_client.get_user("member-live-xyz789")
        assert result is None

    # =====================================================================
    # get_team() Tests
    # =====================================================================

    @pytest.mark.asyncio
    async def test_get_team_success(
        self, mock_mongo_client, mock_settings_with_mongodb
    ):
        """Test successful team retrieval."""
        # Use a valid ObjectId format (24 hex characters)
        valid_object_id = "507f1f77bcf86cd799439011"
        team_data = {
            "_id": valid_object_id,
            "name": "Engineering Team",
            "organization_id": "507f1f77bcf86cd799439012",
        }

        mock_db = MagicMock()
        mock_collection = AsyncMock()
        mock_collection.find_one = AsyncMock(return_value=team_data)
        mock_db.teams = mock_collection

        # Create a mock ObjectId class that returns the input when called
        mock_object_id_class = MagicMock()
        mock_object_id_class.return_value = valid_object_id

        with patch.object(mock_mongo_client, "_get_client", return_value=mock_db):
            # Mock the bson module so ObjectId import doesn't fail
            with patch.dict(
                "sys.modules", {"bson": MagicMock(ObjectId=mock_object_id_class)}
            ):
                # Test with valid ObjectId string
                result = await mock_mongo_client.get_team(valid_object_id)

                assert result == team_data
                # Verify find_one was called
                assert mock_collection.find_one.call_count == 1

    @pytest.mark.asyncio
    async def test_get_team_with_invalid_objectid(
        self, mock_mongo_client, mock_settings_with_mongodb
    ):
        """Test team retrieval with invalid ObjectId format."""
        mock_db = MagicMock()
        mock_collection = AsyncMock()
        mock_db.teams = mock_collection

        with patch.object(mock_mongo_client, "_get_client", return_value=mock_db):
            result = await mock_mongo_client.get_team("invalid_id_format!!!")

            assert result is None

    @pytest.mark.asyncio
    async def test_get_team_not_found(
        self, mock_mongo_client, mock_settings_with_mongodb
    ):
        """Test team retrieval when team doesn't exist."""
        mock_db = MagicMock()
        mock_collection = AsyncMock()
        mock_collection.find_one = AsyncMock(return_value=None)
        mock_db.teams = mock_collection

        with patch.object(mock_mongo_client, "_get_client", return_value=mock_db):
            result = await mock_mongo_client.get_team("507f1f77bcf86cd799439011")

            assert result is None

    # =====================================================================
    # health_check() Tests
    # =====================================================================

    @pytest.mark.asyncio
    async def test_health_check_success(
        self, mock_mongo_client, mock_settings_with_mongodb
    ):
        """Test successful health check."""
        mock_motor_client = AsyncMock()
        mock_motor_client.admin.command = AsyncMock(return_value={"ok": 1})
        mock_db = MagicMock()

        mock_mongo_client._client = mock_motor_client

        with patch.object(mock_mongo_client, "_get_client", return_value=mock_db):
            result = await mock_mongo_client.health_check()

            assert result is True
            mock_motor_client.admin.command.assert_called_once_with("ping")

    @pytest.mark.asyncio
    async def test_health_check_mongodb_not_configured(
        self, mock_mongo_client, mock_settings_without_mongodb
    ):
        """Test health check when MongoDB not configured."""
        result = await mock_mongo_client.health_check()
        assert result is False

    @pytest.mark.asyncio
    async def test_health_check_connection_failure(
        self, mock_mongo_client, mock_settings_with_mongodb
    ):
        """Test health check when connection fails."""
        mock_motor_client = AsyncMock()
        mock_motor_client.admin.command = AsyncMock(
            side_effect=Exception("Connection lost")
        )
        mock_db = MagicMock()

        mock_mongo_client._client = mock_motor_client

        with patch.object(mock_mongo_client, "_get_client", return_value=mock_db):
            result = await mock_mongo_client.health_check()

            assert result is False

    # =====================================================================
    # close() Tests
    # =====================================================================

    @pytest.mark.asyncio
    async def test_close_connection(self, mock_mongo_client):
        """Test closing MongoDB connection."""
        mock_motor_client = MagicMock()
        mock_db = MagicMock()

        mock_mongo_client._client = mock_motor_client
        mock_mongo_client._db = mock_db
        mock_mongo_client._is_available = True

        await mock_mongo_client.close()

        assert mock_mongo_client._client is None
        assert mock_mongo_client._db is None
        assert not mock_mongo_client.is_available
        mock_motor_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_when_no_connection(self, mock_mongo_client):
        """Test closing when no connection exists."""
        # Should not raise any errors
        await mock_mongo_client.close()
        assert mock_mongo_client._client is None

    # =====================================================================
    # Database Name Extraction Tests
    # =====================================================================

    @pytest.mark.asyncio
    async def test_database_name_extraction_from_uri(self, mock_mongo_client):
        """Test that database name is correctly extracted from URI."""
        with patch.object(
            mongo_client_module, "settings", create=False
        ) as mock_settings:
            mock_settings.mongodb_uri = "mongodb://localhost:27017/custom_db"
            mock_settings.mongodb_db = None  # No explicit db set

            mock_motor_client = AsyncMock()
            mock_motor_client.admin.command = AsyncMock(return_value={"ok": 1})
            mock_db = MagicMock()
            mock_motor_client.__getitem__ = MagicMock(return_value=mock_db)

            with patch.object(mongo_client_module, "MOTOR_AVAILABLE", True):
                with patch.object(
                    mongo_client_module,
                    "AsyncIOMotorClient",
                    return_value=mock_motor_client,
                ):
                    await mock_mongo_client._get_client()

                    # Verify correct database name was used (extracted from URI)
                    mock_motor_client.__getitem__.assert_called_once_with("custom_db")

    @pytest.mark.asyncio
    async def test_default_database_name(self, mock_mongo_client):
        """Test that default database name is used when not in URI."""
        with patch.object(
            mongo_client_module, "settings", create=False
        ) as mock_settings:
            mock_settings.mongodb_uri = "mongodb://localhost:27017"
            mock_settings.mongodb_db = None  # No explicit db set

            mock_motor_client = AsyncMock()
            mock_motor_client.admin.command = AsyncMock(return_value={"ok": 1})
            mock_db = MagicMock()
            mock_motor_client.__getitem__ = MagicMock(return_value=mock_db)

            with patch.object(mongo_client_module, "MOTOR_AVAILABLE", True):
                with patch.object(
                    mongo_client_module,
                    "AsyncIOMotorClient",
                    return_value=mock_motor_client,
                ):
                    await mock_mongo_client._get_client()

                    # Verify default "soulmates" database name was used
                    mock_motor_client.__getitem__.assert_called_once_with("soulmates")

    @pytest.mark.asyncio
    async def test_explicit_mongodb_db_overrides_uri(self, mock_mongo_client):
        """Test that mongodb_db setting overrides database name from URI."""
        with patch.object(
            mongo_client_module, "settings", create=False
        ) as mock_settings:
            mock_settings.mongodb_uri = "mongodb://localhost:27017/ignored_db"
            mock_settings.mongodb_db = "explicit_db"  # Explicit db takes priority

            mock_motor_client = AsyncMock()
            mock_motor_client.admin.command = AsyncMock(return_value={"ok": 1})
            mock_db = MagicMock()
            mock_motor_client.__getitem__ = MagicMock(return_value=mock_db)

            with patch.object(mongo_client_module, "MOTOR_AVAILABLE", True):
                with patch.object(
                    mongo_client_module,
                    "AsyncIOMotorClient",
                    return_value=mock_motor_client,
                ):
                    await mock_mongo_client._get_client()

                    # Verify explicit mongodb_db was used, not URI database
                    mock_motor_client.__getitem__.assert_called_once_with("explicit_db")
