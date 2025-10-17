"""
Database integration module for ayz-auth.

Provides MongoDB integration for entitlements and team context features.
"""

from .entitlements_loader import entitlements_loader
from .mongo_client import mongo_client

__all__ = ["mongo_client", "entitlements_loader"]
