"""
MongoDB client for entitlements and team context.

Provides async MongoDB operations for read-only access to organizations,
users, and teams collections.
"""

from typing import Any, Dict, Optional

from ..utils.config import settings
from ..utils.exceptions import ConfigurationError
from ..utils.logger import logger

# Import motor conditionally to make it optional
try:
    from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

    MOTOR_AVAILABLE = True
except ImportError:
    MOTOR_AVAILABLE = False
    AsyncIOMotorClient = Any  # type: ignore
    AsyncIOMotorDatabase = Any  # type: ignore


class MongoClient:
    """
    Async MongoDB client for entitlements and team context.

    Provides read-only access to organizations, users, and teams collections.
    Handles connection management and graceful error handling.
    """

    def __init__(self) -> None:
        self._client: Optional[AsyncIOMotorClient] = None  # type: ignore
        self._db: Optional[AsyncIOMotorDatabase] = None  # type: ignore
        self._is_available = False

    async def _get_client(self) -> Optional[AsyncIOMotorDatabase]:  # type: ignore
        """
        Get or create MongoDB client with database connection.

        Returns:
            MongoDB database instance, or None if MongoDB is not configured

        Raises:
            ConfigurationError: If motor is not installed but MongoDB URI is provided
        """
        # If MongoDB is not configured, return None (backwards compatible)
        if not settings.mongodb_uri:
            return None

        # Check if motor is available
        if not MOTOR_AVAILABLE:
            logger.warning(
                "MongoDB URI provided but 'motor' package is not installed. "
                "Install with: pip install 'ayz-auth[mongodb]'"
            )
            raise ConfigurationError(
                "MongoDB integration requires 'motor' package. "
                "Install with: pip install 'ayz-auth[mongodb]'"
            )

        # Create client if not already created
        if self._client is None:
            try:
                self._client = AsyncIOMotorClient(
                    settings.mongodb_uri,
                    serverSelectionTimeoutMS=5000,  # 5 second timeout
                    connectTimeoutMS=5000,
                    socketTimeoutMS=10000,
                )

                # Use explicit mongodb_db if provided, otherwise extract from URI or use default
                db_name = None
                if settings.mongodb_db:
                    # Explicit database name takes priority
                    db_name = settings.mongodb_db
                elif "/" in settings.mongodb_uri:
                    # Extract database name from URI
                    # MongoDB URIs are like: mongodb://host:port/database
                    parts = settings.mongodb_uri.split("/")
                    if len(parts) > 3 and parts[-1]:
                        # Remove query params if present
                        db_name = parts[-1].split("?")[0]

                # Fallback to default if no database name found
                if not db_name:
                    db_name = "soulmates"

                self._db = self._client[db_name]

                # Test connection with a simple command
                await self._client.admin.command("ping")
                self._is_available = True
                logger.info(
                    f"MongoDB connection established successfully to database: {db_name}"
                )

            except Exception as e:
                logger.warning(
                    f"Failed to connect to MongoDB: {str(e)}. "
                    f"Entitlements features will be disabled. "
                    f"Session authentication will continue to work."
                )
                self._is_available = False
                self._client = None
                self._db = None
                # Don't raise - graceful degradation
                return None

        return self._db

    async def get_organization(self, stytch_org_id: str) -> Optional[Dict[str, Any]]:
        """
        Get organization data by Stytch organization ID.

        Args:
            stytch_org_id: Stytch organization identifier

        Returns:
            Organization document if found, None otherwise
        """
        try:
            db = await self._get_client()
            if db is None:
                return None

            org = await db.organizations.find_one({"stytch_org_id": stytch_org_id})

            if org:
                logger.debug(f"Found organization for stytch_org_id: {stytch_org_id}")
            else:
                logger.debug(
                    f"Organization not found for stytch_org_id: {stytch_org_id}"
                )

            return org

        except Exception as e:
            logger.warning(f"Failed to fetch organization from MongoDB: {str(e)}")
            return None

    async def get_user(self, stytch_member_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user data by Stytch member ID.

        Args:
            stytch_member_id: Stytch member identifier

        Returns:
            User document if found, None otherwise
        """
        try:
            db = await self._get_client()
            if db is None:
                return None

            user = await db.users.find_one({"stytch_member_id": stytch_member_id})

            if user:
                logger.debug(f"Found user for stytch_member_id: {stytch_member_id}")
            else:
                logger.debug(f"User not found for stytch_member_id: {stytch_member_id}")

            return user

        except Exception as e:
            logger.warning(f"Failed to fetch user from MongoDB: {str(e)}")
            return None

    async def get_team(self, team_id: Any) -> Optional[Dict[str, Any]]:
        """
        Get team data by team ID.

        Args:
            team_id: MongoDB ObjectId of the team (can be ObjectId or string)

        Returns:
            Team document if found, None otherwise
        """
        try:
            db = await self._get_client()
            if db is None:
                return None

            # Handle both ObjectId and string formats
            from bson import ObjectId

            if isinstance(team_id, str):
                try:
                    team_id = ObjectId(team_id)
                except Exception:
                    logger.warning(f"Invalid ObjectId format: {team_id}")
                    return None

            team = await db.teams.find_one({"_id": team_id})

            if team:
                logger.debug(f"Found team for team_id: {team_id}")
            else:
                logger.debug(f"Team not found for team_id: {team_id}")

            return team

        except Exception as e:
            logger.warning(f"Failed to fetch team from MongoDB: {str(e)}")
            return None

    async def health_check(self) -> bool:
        """
        Check if MongoDB is healthy and responsive.

        Returns:
            True if MongoDB is healthy, False otherwise
        """
        try:
            if not settings.mongodb_uri:
                return False

            db = await self._get_client()
            if db is None:
                return False

            if self._client:
                await self._client.admin.command("ping")
                return True

            return False

        except Exception:
            return False

    async def close(self) -> None:
        """Close MongoDB connection and cleanup resources."""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None
            self._is_available = False
            logger.info("MongoDB connection closed")

    @property
    def is_available(self) -> bool:
        """Check if MongoDB connection is available."""
        return self._is_available and self._client is not None


# Global MongoDB client instance
mongo_client = MongoClient()
