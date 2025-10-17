"""
Entitlements and team context data loader.

Orchestrates loading of organization entitlements, user context, and team data
from MongoDB with Redis caching.
"""

from typing import Any, Dict, Optional

from ..cache.redis_client import redis_client
from ..utils.logger import logger
from .mongo_client import mongo_client


class EntitlementsLoader:
    """
    Loads entitlements and team context data with caching.

    Provides a high-level interface for loading organization entitlements,
    user context, and team details with intelligent caching strategies.
    """

    async def load_organization_entitlements(
        self, stytch_org_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Load organization entitlements with 1-hour caching.

        Args:
            stytch_org_id: Stytch organization identifier

        Returns:
            Dict containing:
                - entitlements: List[str]
                - subscription_tier: str
                - subscription_limits: Dict[str, int]
                - mongo_organization_id: str (MongoDB ObjectId as string)
            Returns None if MongoDB is not configured or organization not found
        """
        try:
            # Try cache first
            cached_data = await redis_client.get_cached_organization_entitlements(
                stytch_org_id
            )
            if cached_data:
                logger.debug(
                    f"Using cached organization entitlements for org: {stytch_org_id}"
                )
                return cached_data

            # Fallback to MongoDB
            org_doc = await mongo_client.get_organization(stytch_org_id)
            if not org_doc:
                logger.debug(
                    f"Organization not found in MongoDB for org: {stytch_org_id}"
                )
                return None

            # Extract entitlements data
            raw_id = org_doc.get("_id")
            entitlements_data = {
                "entitlements": org_doc.get("entitlements", []),
                "subscription_tier": org_doc.get("subscription_tier"),
                "subscription_limits": org_doc.get("subscription_limits", {}),
                "mongo_organization_id": str(raw_id) if raw_id is not None else None,
            }

            # Cache for 1 hour
            await redis_client.cache_organization_entitlements(
                stytch_org_id, entitlements_data
            )

            logger.debug(
                f"Loaded organization entitlements from MongoDB for org: {stytch_org_id}"
            )
            return entitlements_data

        except Exception as e:
            logger.warning(
                f"Failed to load organization entitlements: {str(e)}. "
                f"Continuing without entitlements data."
            )
            return None

    async def load_user_context(
        self, stytch_member_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Load user context with team information.

        Caches mongo_user_id for 1 hour, but team context (current_team_id,
        current_team_name) is always loaded fresh from MongoDB.

        Args:
            stytch_member_id: Stytch member identifier

        Returns:
            Dict containing:
                - current_team_id: str (MongoDB ObjectId as string) or None
                - current_team_name: str or None
                - mongo_user_id: str (MongoDB ObjectId as string)
            Returns None if MongoDB is not configured or user not found
        """
        try:
            # Try to get cached mongo_user_id
            cached_user_id = await redis_client.get_cached_user_id(stytch_member_id)

            # Always load fresh user doc for team context
            user_doc = await mongo_client.get_user(stytch_member_id)
            if not user_doc:
                logger.debug(
                    f"User not found in MongoDB for member: {stytch_member_id}"
                )
                return None

            # Extract user context
            current_team_id = user_doc.get("current_team_id")
            user_id = user_doc.get("_id")
            mongo_user_id_str = str(user_id) if user_id is not None else None

            user_context = {
                "current_team_id": str(current_team_id) if current_team_id else None,
                "current_team_name": None,
                "mongo_user_id": mongo_user_id_str,
            }

            # Cache mongo_user_id if not already cached
            if mongo_user_id_str and not cached_user_id:
                await redis_client.cache_user_id(stytch_member_id, mongo_user_id_str)

            # Load team details if team ID is present (always fresh)
            if current_team_id:
                team_name = await self._load_team_name(current_team_id)
                user_context["current_team_name"] = team_name

            logger.debug(
                f"Loaded user context from MongoDB for member: {stytch_member_id}"
            )
            return user_context

        except Exception as e:
            logger.warning(
                f"Failed to load user context: {str(e)}. "
                f"Continuing without user context data."
            )
            return None

    async def _load_team_name(self, team_id: Any) -> Optional[str]:
        """
        Load team name by team ID.

        Args:
            team_id: MongoDB ObjectId of the team

        Returns:
            Team name if found, None otherwise
        """
        try:
            team_doc = await mongo_client.get_team(team_id)
            if team_doc:
                return team_doc.get("name")
            return None

        except Exception as e:
            logger.warning(f"Failed to load team name: {str(e)}")
            return None

    async def load_complete_session_data(
        self, stytch_org_id: str, stytch_member_id: str
    ) -> Dict[str, Any]:
        """
        Load both organization entitlements and user context in one call.

        Args:
            stytch_org_id: Stytch organization identifier
            stytch_member_id: Stytch member identifier

        Returns:
            Dict containing all entitlements and user context data.
            Returns empty dict values if MongoDB is not configured.
        """
        # Load organization entitlements and user context in parallel
        import asyncio

        org_data_task = self.load_organization_entitlements(stytch_org_id)
        user_data_task = self.load_user_context(stytch_member_id)

        org_data, user_data = await asyncio.gather(
            org_data_task, user_data_task, return_exceptions=True
        )

        # Handle exceptions from parallel loading
        if isinstance(org_data, Exception):
            logger.warning(f"Exception loading organization data: {org_data}")
            org_data = None

        if isinstance(user_data, Exception):
            logger.warning(f"Exception loading user data: {user_data}")
            user_data = None

        # Combine results with safe defaults
        return {
            # Organization entitlements (default to None if not available)
            "entitlements": org_data.get("entitlements") if org_data else None,
            "subscription_tier": (
                org_data.get("subscription_tier") if org_data else None
            ),
            "subscription_limits": (
                org_data.get("subscription_limits") if org_data else None
            ),
            "mongo_organization_id": (
                org_data.get("mongo_organization_id") if org_data else None
            ),
            # User context (default to None if not available)
            "current_team_id": user_data.get("current_team_id") if user_data else None,
            "current_team_name": (
                user_data.get("current_team_name") if user_data else None
            ),
            "mongo_user_id": user_data.get("mongo_user_id") if user_data else None,
        }


# Global entitlements loader instance
entitlements_loader = EntitlementsLoader()
