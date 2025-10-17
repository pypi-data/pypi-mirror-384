"""
Stytch B2B session token verification.

Handles verification of session tokens with the Stytch B2B API, including
caching, error handling, and session data extraction.
"""

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import stytch

from ..cache.redis_client import redis_client
from ..db.entitlements_loader import entitlements_loader
from ..models.context import StytchContext
from ..utils.config import settings
from ..utils.exceptions import StytchAPIError, TokenVerificationError
from ..utils.logger import logger


class StytchVerifier:
    """
    Handles Stytch B2B session token verification with Redis caching.

    Provides a two-tier verification system:
    1. Check Redis cache for previously verified tokens
    2. Fall back to Stytch API for fresh verification
    """

    def __init__(self) -> None:
        self._client: Optional[stytch.B2BClient] = None

    def _get_client(self) -> stytch.B2BClient:
        """
        Get or create Stytch B2B client.

        Returns:
            Configured Stytch B2B client

        Raises:
            StytchAPIError: If client cannot be configured
        """
        if self._client is None:
            try:
                # These should be validated as non-None by the model_validator
                assert settings.project_id is not None, "project_id must be set"
                assert settings.secret is not None, "secret must be set"

                self._client = stytch.B2BClient(
                    project_id=settings.project_id,
                    secret=settings.secret,
                    environment=settings.environment,
                )
            except Exception as e:
                logger.error(f"Failed to initialize Stytch client: {str(e)}")
                raise StytchAPIError(f"Stytch client initialization failed: {str(e)}")

        return self._client

    def _hash_token(self, token: str) -> str:
        """
        Create a hash of the token for cache key generation.

        Args:
            token: Session token to hash

        Returns:
            SHA256 hash of the token
        """
        return hashlib.sha256(token.encode()).hexdigest()

    async def verify_session_token(self, token: str) -> StytchContext:
        """
        Verify session token with caching support.

        Args:
            token: Stytch session token to verify

        Returns:
            StytchContext with session data

        Raises:
            TokenVerificationError: If token verification fails
            StytchAPIError: If Stytch API is unreachable
        """
        token_hash = self._hash_token(token)

        # Try cache first
        cached_result = await self._get_cached_verification(token_hash)
        if cached_result:
            return await self._build_context_from_cache(cached_result)

        # Fall back to Stytch API
        session_data = await self._verify_with_stytch_api(token)

        # Build context with entitlements (v2.0.0+)
        stytch_context = await self._build_context_from_stytch_data(session_data)

        # Cache the complete result (including entitlements)
        await self._cache_verification_result(token_hash, stytch_context)

        return stytch_context

    async def _get_cached_verification(
        self, token_hash: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached verification result.

        Args:
            token_hash: Hash of the token to look up

        Returns:
            Cached verification data if found and valid
        """
        try:
            cached_data = await redis_client.get_cached_verification(token_hash)
            if cached_data:
                # Check if cached session is still valid
                expires_at_str = cached_data.get("session_expires_at")
                if not expires_at_str or not isinstance(expires_at_str, str):
                    return None
                expires_at = datetime.fromisoformat(expires_at_str)
                if datetime.now(timezone.utc) < expires_at:
                    logger.debug("Using cached verification result")
                    return cached_data
                else:
                    logger.debug("Cached session expired, removing from cache")
                    await redis_client.delete_cached_verification(token_hash)

            return None

        except Exception as e:
            logger.warning(f"Cache lookup failed: {str(e)}")
            return None

    async def _verify_with_stytch_api(self, token: str) -> Dict[str, Any]:
        """
        Verify token directly with Stytch B2B API.

        Args:
            token: Session token to verify

        Returns:
            Raw session data from Stytch API

        Raises:
            TokenVerificationError: If token is invalid
            StytchAPIError: If API call fails
        """
        try:
            client = self._get_client()

            logger.debug("Verifying token with Stytch API")
            response = client.sessions.authenticate(session_token=token)

            if hasattr(response, "status_code") and response.status_code != 200:
                logger.warning(
                    f"Stytch API returned error: {response.status_code}",
                    extra={
                        "response": (
                            response.json()
                            if hasattr(response, "json")
                            else str(response)
                        )
                    },
                )
                raise TokenVerificationError(
                    "Invalid or expired session token", token_hint=token[:8] + "..."
                )

            # Handle different response formats from Stytch SDK
            session_data = None

            # First, try to convert response to string to check if it's JSON
            response_str = str(response)

            if hasattr(response, "json") and callable(response.json):
                # Response is an HTTP response object
                try:
                    session_data = response.json()

                    # Check if .json() returned a string instead of parsed data
                    if isinstance(session_data, str):
                        session_data = json.loads(session_data)

                except Exception:
                    session_data = None
            elif isinstance(response, dict):
                # Response is already a dictionary
                session_data = response
            elif hasattr(response, "member_session") and hasattr(response, "member"):
                # Modern Stytch response object with direct attributes
                member_session = getattr(response, "member_session", {})
                member = getattr(response, "member", {})
                organization = getattr(response, "organization", {})

                # Convert objects to dicts if they're not already
                if hasattr(member_session, "__dict__"):
                    member_session = member_session.__dict__
                if hasattr(member, "__dict__"):
                    member = member.__dict__
                if hasattr(organization, "__dict__"):
                    organization = organization.__dict__

                session_data = {
                    "status_code": getattr(response, "status_code", 200),
                    "request_id": getattr(response, "request_id", ""),
                    "member_session": member_session,
                    "member": member,
                    "organization": organization,
                    "session_token": getattr(response, "session_token", ""),
                    "session_jwt": getattr(response, "session_jwt", ""),
                }
            elif response_str.startswith("{") and response_str.endswith("}"):
                # Response looks like JSON - try to parse it
                try:
                    session_data = json.loads(response_str)
                except json.JSONDecodeError as e:
                    raise StytchAPIError(
                        "Invalid JSON response from Stytch API",
                        api_response={"error": f"JSON parse error: {str(e)}"},
                    )
            elif isinstance(response, str):
                # Response is a JSON string - parse it
                try:
                    session_data = json.loads(response)
                except json.JSONDecodeError as e:
                    raise StytchAPIError(
                        "Invalid JSON response from Stytch API",
                        api_response={"error": f"JSON parse error: {str(e)}"},
                    )
            elif hasattr(response, "__dict__"):
                # Response is a Stytch response object - convert to dict
                session_data = response.__dict__
            else:
                # Response is some other format - try to get its attributes
                session_data = vars(response) if hasattr(response, "__dict__") else {}

            # Final validation and logging

            # Validate we have the expected data structure
            if not isinstance(session_data, dict):
                raise StytchAPIError(
                    "Invalid response format from Stytch API",
                    api_response={"error": f"Expected dict, got {type(session_data)}"},
                )

            # Check for required fields in the response
            # Stytch B2B API returns member_session instead of separate member/session
            if "member_session" not in session_data or "member" not in session_data:
                raise StytchAPIError(
                    "Invalid session data format from Stytch API",
                    api_response={"error": "Missing member_session or member data"},
                )

            logger.info("Token verified successfully with Stytch API")
            return session_data

        except TokenVerificationError:
            # Re-raise token verification errors as-is
            raise

        except Exception as e:
            # Log configuration details when API calls fail to help diagnose environment issues
            logger.error(f"Stytch API verification failed: {str(e)}", exc_info=True)
            raise StytchAPIError(
                f"Failed to verify token with Stytch: {str(e)}",
                api_response={"error": str(e)},
            )

    async def _cache_verification_result(
        self, token_hash: str, context: StytchContext
    ) -> None:
        """
        Cache verification result with entitlements for future use.

        Args:
            token_hash: Hash of the verified token
            context: Complete StytchContext with all session and entitlements data
        """
        try:
            # Convert StytchContext to cacheable dict
            # Note: Team context (current_team_id, current_team_name) is NOT cached
            # to ensure it's always fresh from MongoDB
            cache_data = {
                # Core Stytch identifiers
                "member_id": context.member_id,
                "session_id": context.session_id,
                "organization_id": context.organization_id,
                # Session timing
                "session_started_at": (
                    context.session_started_at.isoformat()
                    if context.session_started_at
                    else None
                ),
                "session_expires_at": (
                    context.session_expires_at.isoformat()
                    if context.session_expires_at
                    else None
                ),
                "session_last_accessed_at": (
                    context.session_last_accessed_at.isoformat()
                    if context.session_last_accessed_at
                    else None
                ),
                # Member information
                "member_email": context.member_email,
                "member_name": context.member_name,
                # Session metadata
                "session_custom_claims": context.session_custom_claims,
                "authentication_factors": context.authentication_factors,
                "raw_session_data": context.raw_session_data,
                # Entitlements and subscription (v2.0.0+)
                "entitlements": context.entitlements,
                "subscription_tier": context.subscription_tier,
                "subscription_limits": context.subscription_limits,
                # MongoDB identifiers (v2.0.0+)
                "mongo_user_id": context.mongo_user_id,
                "mongo_organization_id": context.mongo_organization_id,
                # Cache metadata
                "cached_at": datetime.now(timezone.utc).isoformat(),
            }

            await redis_client.cache_verification_result(token_hash, cache_data)

        except Exception as e:
            logger.warning(f"Failed to cache verification result: {str(e)}")
            # Don't raise - caching failures should be non-fatal

    async def _build_context_from_cache(
        self, cached_data: Dict[str, Any]
    ) -> StytchContext:
        """
        Build StytchContext from cached verification data.

        Team context is loaded fresh from MongoDB on every request to ensure
        current_team_id and current_team_name are always up-to-date.

        Args:
            cached_data: Cached session data (includes entitlements if available)

        Returns:
            StytchContext instance with fresh team context
        """
        # Handle datetime fields safely
        started_at = cached_data.get("session_started_at")
        expires_at = cached_data.get("session_expires_at")
        last_accessed_at = cached_data.get("session_last_accessed_at")

        # Load fresh team context from MongoDB (not cached)
        member_id = cached_data["member_id"]
        team_context = {}
        if settings.mongodb_uri and member_id:
            try:
                team_context = (
                    await entitlements_loader.load_user_context(member_id) or {}
                )
            except Exception as e:
                logger.warning(
                    f"Failed to load fresh team context from cache: {str(e)}"
                )

        return StytchContext(
            # Core Stytch identifiers
            member_id=member_id,
            session_id=cached_data["session_id"],
            organization_id=cached_data["organization_id"],
            # Session timing
            session_started_at=(
                datetime.fromisoformat(started_at)
                if started_at
                else datetime.now(timezone.utc)
            ),
            session_expires_at=(
                datetime.fromisoformat(expires_at)
                if expires_at
                else datetime.now(timezone.utc)
            ),
            session_last_accessed_at=(
                datetime.fromisoformat(last_accessed_at)
                if last_accessed_at
                else datetime.now(timezone.utc)
            ),
            # Member information
            member_email=cached_data.get("member_email"),
            member_name=cached_data.get("member_name"),
            # Session metadata
            session_custom_claims=cached_data.get("session_custom_claims", {}),
            authentication_factors=cached_data.get("authentication_factors", []),
            raw_session_data=cached_data.get("raw_session_data", {}),
            # Entitlements and subscription (v2.0.0+ - may be None for old cache entries)
            entitlements=cached_data.get("entitlements"),
            subscription_tier=cached_data.get("subscription_tier"),
            subscription_limits=cached_data.get("subscription_limits"),
            # Team context (v2.0.1+ - always loaded fresh from MongoDB)
            current_team_id=team_context.get("current_team_id"),
            current_team_name=team_context.get("current_team_name"),
            # MongoDB identifiers (v2.0.0+ - may be None for old cache entries)
            mongo_user_id=team_context.get("mongo_user_id")
            or cached_data.get("mongo_user_id"),
            mongo_organization_id=cached_data.get("mongo_organization_id"),
        )

    async def _build_context_from_stytch_data(
        self, session_data: Dict[str, Any]
    ) -> StytchContext:
        """
        Build StytchContext from fresh Stytch API response.

        Loads entitlements and team context from MongoDB if configured.

        Args:
            session_data: Raw session data from Stytch API

        Returns:
            StytchContext instance with entitlements and team data
        """
        # Handle both dict and object formats from Stytch SDK
        member = session_data.get("member", {})
        session = session_data.get("member_session", {})
        organization = session_data.get("organization", {})

        # Helper function to safely get attribute from object or dict
        def safe_get(obj: Any, attr: str, default: Any = None) -> Any:
            if hasattr(obj, attr):
                return getattr(obj, attr)
            elif isinstance(obj, dict):
                return obj.get(attr, default)
            return default

        # Helper function to normalize authentication factors
        def normalize_auth_factors(factors: Any) -> List[str]:
            """Convert authentication factors to list of strings."""
            if not factors:
                return []

            normalized = []
            for factor in factors:
                if isinstance(factor, dict):
                    # Extract the type from the dict or use a fallback
                    factor_type = factor.get("type", "unknown")
                    normalized.append(factor_type)
                elif isinstance(factor, str):
                    # Already a string, keep as-is
                    normalized.append(factor)
                else:
                    # Fallback for unexpected types
                    normalized.append(str(factor))

            return normalized

        # Handle datetime fields safely
        started_at = safe_get(session, "started_at")
        expires_at = safe_get(session, "expires_at")
        last_accessed_at = safe_get(session, "last_accessed_at")

        # Get and normalize authentication factors
        raw_auth_factors = safe_get(session, "authentication_factors", [])
        normalized_auth_factors = normalize_auth_factors(raw_auth_factors)

        # Extract core identifiers
        member_id = safe_get(member, "member_id") or safe_get(session, "member_id")
        organization_id = safe_get(organization, "organization_id") or safe_get(
            session, "organization_id"
        )

        # Load entitlements and team context (v2.0.0+)
        # This is optional - if MongoDB is not configured, all fields will be None
        entitlements_data = {}
        if settings.mongodb_uri and member_id and organization_id:
            try:
                logger.debug(
                    f"Loading entitlements for org: {organization_id}, member: {member_id}"
                )
                entitlements_data = (
                    await entitlements_loader.load_complete_session_data(
                        stytch_org_id=organization_id,
                        stytch_member_id=member_id,
                    )
                )
                logger.debug(f"Entitlements data loaded: {bool(entitlements_data)}")
            except Exception as e:
                logger.warning(
                    f"Failed to load entitlements data: {str(e)}. "
                    f"Continuing without entitlements."
                )
                entitlements_data = {}

        return StytchContext(
            # Core Stytch identifiers
            member_id=member_id,
            session_id=safe_get(session, "member_session_id"),
            organization_id=organization_id,
            # Session timing
            session_started_at=(
                datetime.fromisoformat(started_at)
                if started_at
                else datetime.now(timezone.utc)
            ),
            session_expires_at=(
                datetime.fromisoformat(expires_at)
                if expires_at
                else datetime.now(timezone.utc)
            ),
            session_last_accessed_at=(
                datetime.fromisoformat(last_accessed_at)
                if last_accessed_at
                else datetime.now(timezone.utc)
            ),
            # Member information
            member_email=safe_get(member, "email_address"),
            member_name=safe_get(member, "name"),
            # Session metadata
            session_custom_claims=safe_get(session, "custom_claims", {}),
            authentication_factors=normalized_auth_factors,
            raw_session_data=session_data,
            # Entitlements and subscription (v2.0.0+)
            entitlements=entitlements_data.get("entitlements"),
            subscription_tier=entitlements_data.get("subscription_tier"),
            subscription_limits=entitlements_data.get("subscription_limits"),
            # Team context (v2.0.0+)
            current_team_id=entitlements_data.get("current_team_id"),
            current_team_name=entitlements_data.get("current_team_name"),
            # MongoDB identifiers (v2.0.0+)
            mongo_user_id=entitlements_data.get("mongo_user_id"),
            mongo_organization_id=entitlements_data.get("mongo_organization_id"),
        )

    async def get_member_by_email(
        self, email: str, organization_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a member's details by their email address within a specific organization.

        This is needed to resolve an email to a Stytch member ID, which can be used
        to add a user to a project or perform other user management operations.

        Args:
            email: Email address to search for
            organization_id: Stytch organization ID (from authenticated user's context)

        Returns:
            Member data dict if found, None otherwise

        Raises:
            StytchAPIError: If the Stytch API call fails

        Example:
            # Get organization_id from authenticated user's session
            @app.post("/invite-member")
            async def invite_member(
                email: str,
                user: StytchContext = Depends(verify_auth)
            ):
                # Use the authenticated user's organization
                member = await stytch_verifier.get_member_by_email(
                    email, user.organization_id
                )
        """
        logger.info(
            f"Attempting to get member by email: {email} in org: {organization_id}"
        )

        try:
            client = self._get_client()
            response = client.organizations.members.search(
                organization_ids=[organization_id],
                query={
                    "operator": "AND",
                    "operands": [
                        {"filter_name": "member_emails", "filter_value": [email]}
                    ],
                },
            )

            response_json: Dict[str, Any] = {}
            try:
                if hasattr(response, "json"):
                    json_data = response.json()
                    if isinstance(json_data, dict):
                        response_json = json_data
            except Exception:
                pass  # Keep response_json as empty dict

            if response.status_code != 200:
                logger.warning(
                    f"Stytch API returned error when searching for member: {response.status_code}",
                    extra={"response": response_json},
                )
                raise StytchAPIError(
                    f"Stytch API error ({response.status_code})",
                    api_response=response_json,
                )

            # Ensure response_json is a dictionary (should already be guaranteed by above logic)

            members = response_json.get("members", [])
            if members:
                logger.info(f"Found member for email: {email}")
                return members[0]

            logger.info(f"Member not found for email: {email}")
            return None

        except StytchAPIError as e:
            extra = {}
            if hasattr(e, "details") and e.details is not None:
                extra = {"api_response": e.details.get("api_response")}
            logger.error(
                f"Stytch API search for member failed: {e.message}",
                extra=extra,
            )
            raise  # Re-raise the exception to be handled by the endpoint
        except Exception as e:
            logger.error(
                f"An unexpected error occurred during Stytch member search: {str(e)}",
                exc_info=True,
            )
            raise StytchAPIError(f"An unexpected error occurred: {str(e)}")


# Global verifier instance
stytch_verifier = StytchVerifier()
