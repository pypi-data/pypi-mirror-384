"""
Token extraction utilities for FastAPI requests.

Handles extracting authentication tokens from various request header formats
and validates token structure before verification.
"""

import re

from fastapi import Request

from ..utils.exceptions import TokenExtractionError
from ..utils.logger import logger


class TokenExtractor:
    """
    Extracts and validates authentication tokens from FastAPI requests.

    Supports multiple token formats and provides detailed error messages
    for debugging authentication issues.
    """

    # Regex pattern for Bearer token format
    BEARER_PATTERN = re.compile(r"^Bearer\s+(.+)$", re.IGNORECASE)

    # Minimum token length (Stytch session tokens are typically longer)
    MIN_TOKEN_LENGTH = 20

    @classmethod
    def extract_from_request(cls, request: Request) -> str:
        """
        Extract authentication token from FastAPI request.

        Args:
            request: FastAPI Request object

        Returns:
            Extracted session token

        Raises:
            TokenExtractionError: If token cannot be extracted or is invalid
        """
        # Check for Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            logger.warning("Missing Authorization header in request")
            raise TokenExtractionError("Authorization header is required")

        # Extract token from Bearer format
        token = cls._extract_bearer_token(auth_header)

        # Validate token format
        cls._validate_token_format(token)

        logger.debug(f"Successfully extracted token from request: {token[:8]}...")
        return token

    @classmethod
    def _extract_bearer_token(cls, auth_header: str) -> str:
        """
        Extract token from Bearer authorization header.

        Args:
            auth_header: Authorization header value

        Returns:
            Extracted token

        Raises:
            TokenExtractionError: If header format is invalid
        """
        # Match Bearer token pattern
        match = cls.BEARER_PATTERN.match(auth_header.strip())
        if not match:
            logger.warning(
                f"Invalid Authorization header format: {auth_header[:20]}..."
            )
            raise TokenExtractionError(
                "Authorization header must be in format: 'Bearer <token>'"
            )

        token = match.group(1).strip()
        if not token:
            logger.warning("Empty token in Authorization header")
            raise TokenExtractionError("Token cannot be empty")

        return token

    @classmethod
    def _validate_token_format(cls, token: str) -> None:
        """
        Validate basic token format requirements.

        Args:
            token: Token to validate

        Raises:
            TokenExtractionError: If token format is invalid
        """
        # Check minimum length
        if len(token) < cls.MIN_TOKEN_LENGTH:
            logger.warning(f"Token too short: {len(token)} characters")
            raise TokenExtractionError(
                f"Token must be at least {cls.MIN_TOKEN_LENGTH} characters long"
            )

        # Check for obvious invalid characters (basic validation)
        if any(char in token for char in [" ", "\n", "\r", "\t"]):
            logger.warning("Token contains invalid whitespace characters")
            raise TokenExtractionError("Token contains invalid characters")

        # Check if token looks like a valid format (basic heuristic)
        if not re.match(r"^[A-Za-z0-9_\-\.]+$", token):
            logger.warning("Token contains unexpected characters")
            raise TokenExtractionError("Token format appears invalid")

    @classmethod
    def extract_from_header_value(cls, header_value: str) -> str:
        """
        Extract token directly from header value (for testing/manual use).

        Args:
            header_value: Raw Authorization header value

        Returns:
            Extracted token

        Raises:
            TokenExtractionError: If extraction fails
        """
        token = cls._extract_bearer_token(header_value)
        cls._validate_token_format(token)
        return token


# Convenience function for direct use
def extract_token_from_request(request: Request) -> str:
    """
    Convenience function to extract token from FastAPI request.

    Args:
        request: FastAPI Request object

    Returns:
        Extracted session token

    Raises:
        TokenExtractionError: If token extraction fails
    """
    return TokenExtractor.extract_from_request(request)
