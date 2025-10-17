"""
Tests for token extraction functionality.
"""

from unittest.mock import Mock

import pytest
from fastapi import Request

from ayz_auth.auth.token_extractor import TokenExtractor, extract_token_from_request
from ayz_auth.utils.exceptions import TokenExtractionError


class TestTokenExtractor:
    """Test cases for TokenExtractor class."""

    def test_extract_valid_bearer_token(self):
        """Test extracting a valid Bearer token."""
        header_value = "Bearer valid_token_12345678901234567890"
        token = TokenExtractor.extract_from_header_value(header_value)
        assert token == "valid_token_12345678901234567890"

    def test_extract_bearer_token_case_insensitive(self):
        """Test that Bearer token extraction is case insensitive."""
        header_value = "bearer valid_token_12345678901234567890"
        token = TokenExtractor.extract_from_header_value(header_value)
        assert token == "valid_token_12345678901234567890"

        header_value = "BEARER valid_token_12345678901234567890"
        token = TokenExtractor.extract_from_header_value(header_value)
        assert token == "valid_token_12345678901234567890"

    def test_extract_bearer_token_with_extra_spaces(self):
        """Test extracting Bearer token with extra whitespace."""
        header_value = "  Bearer   valid_token_12345678901234567890  "
        token = TokenExtractor.extract_from_header_value(header_value)
        assert token == "valid_token_12345678901234567890"

    def test_invalid_header_format(self):
        """Test extraction fails with invalid header format."""
        with pytest.raises(TokenExtractionError) as exc_info:
            TokenExtractor.extract_from_header_value("Invalid header format")

        assert "Bearer" in str(exc_info.value)

    def test_missing_token_in_bearer_header(self):
        """Test extraction fails when token is missing."""
        with pytest.raises(TokenExtractionError) as exc_info:
            TokenExtractor.extract_from_header_value("Bearer ")

        assert "bearer" in str(exc_info.value).lower()

    def test_token_too_short(self):
        """Test extraction fails when token is too short."""
        with pytest.raises(TokenExtractionError) as exc_info:
            TokenExtractor.extract_from_header_value("Bearer short")

        assert "20 characters" in str(exc_info.value)

    def test_token_with_invalid_characters(self):
        """Test extraction fails with invalid characters."""
        # Token with spaces
        with pytest.raises(TokenExtractionError):
            TokenExtractor.extract_from_header_value("Bearer token with spaces here")

        # Token with newlines
        with pytest.raises(TokenExtractionError):
            TokenExtractor.extract_from_header_value("Bearer token\nwith\nnewlines")

        # Token with special characters
        with pytest.raises(TokenExtractionError):
            TokenExtractor.extract_from_header_value("Bearer token@with#special$chars")

    def test_valid_token_characters(self):
        """Test that valid token characters are accepted."""
        # Alphanumeric with underscores, hyphens, and dots
        valid_token = "Bearer valid_token-123.456_789012345"
        token = TokenExtractor.extract_from_header_value(valid_token)
        assert token == "valid_token-123.456_789012345"

    def test_extract_from_request_success(self):
        """Test successful token extraction from FastAPI request."""
        # Mock request with valid Authorization header
        mock_request = Mock(spec=Request)
        mock_request.headers = {
            "Authorization": "Bearer valid_token_12345678901234567890"
        }

        token = extract_token_from_request(mock_request)
        assert token == "valid_token_12345678901234567890"

    def test_extract_from_request_missing_header(self):
        """Test extraction fails when Authorization header is missing."""
        mock_request = Mock(spec=Request)
        mock_request.headers = {}

        with pytest.raises(TokenExtractionError) as exc_info:
            extract_token_from_request(mock_request)

        assert "required" in str(exc_info.value).lower()

    def test_extract_from_request_invalid_header(self):
        """Test extraction fails with invalid Authorization header."""
        mock_request = Mock(spec=Request)
        mock_request.headers = {"Authorization": "Invalid format"}

        with pytest.raises(TokenExtractionError):
            extract_token_from_request(mock_request)


if __name__ == "__main__":
    pytest.main([__file__])
