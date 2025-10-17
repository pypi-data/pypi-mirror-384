"""
Environment-scoped logging utility for ayz-auth package.

Provides structured logging with environment-aware log levels and sensitive data protection.
"""

import logging
import sys
from typing import Any, Dict, Optional

from .config import settings


class AuthLogger:
    """
    Custom logger for authentication middleware with environment-scoped logging.

    Automatically filters sensitive data and adjusts log levels based on environment.
    """

    def __init__(self, name: str = "ayz_auth"):
        self.logger = logging.getLogger(name)
        self._setup_logger()

    def _setup_logger(self) -> None:
        """Configure logger with appropriate handlers and formatters."""
        if self.logger.handlers:
            return  # Already configured

        # Set log level from configuration
        log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
        self.logger.setLevel(log_level)

        # Create console handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(log_level)

        # Create formatter
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)

        self.logger.addHandler(handler)
        self.logger.propagate = False

    def _sanitize_data(self, data: Any) -> Any:
        """
        Remove or mask sensitive data from log messages.

        Args:
            data: Data to sanitize

        Returns:
            Sanitized data safe for logging
        """
        if not settings.log_sensitive_data:
            if isinstance(data, dict):
                sanitized = {}
                for key, value in data.items():
                    if any(
                        sensitive in key.lower()
                        for sensitive in ["token", "secret", "password", "key", "auth"]
                    ):
                        sanitized[key] = "***REDACTED***"
                    else:
                        sanitized[key] = self._sanitize_data(value)
                return sanitized
            elif isinstance(data, str) and len(data) > 20:
                # Potentially a token - mask it
                return f"{data[:4]}...{data[-4:]}"

        return data

    def debug(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log debug message with optional extra data."""
        if extra:
            extra = self._sanitize_data(extra)
            message = f"{message} | Extra: {extra}"
        self.logger.debug(message)

    def info(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log info message with optional extra data."""
        if extra:
            extra = self._sanitize_data(extra)
            message = f"{message} | Extra: {extra}"
        self.logger.info(message)

    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log warning message with optional extra data."""
        if extra:
            extra = self._sanitize_data(extra)
            message = f"{message} | Extra: {extra}"
        self.logger.warning(message)

    def error(
        self,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
        exc_info: bool = False,
    ) -> None:
        """Log error message with optional extra data and exception info."""
        if extra:
            extra = self._sanitize_data(extra)
            message = f"{message} | Extra: {extra}"
        self.logger.error(message, exc_info=exc_info)

    def critical(
        self,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
        exc_info: bool = False,
    ) -> None:
        """Log critical message with optional extra data and exception info."""
        if extra:
            extra = self._sanitize_data(extra)
            message = f"{message} | Extra: {extra}"
        self.logger.critical(message, exc_info=exc_info)


# Global logger instance
logger = AuthLogger()
