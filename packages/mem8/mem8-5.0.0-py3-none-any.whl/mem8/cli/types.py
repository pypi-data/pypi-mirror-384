#!/usr/bin/env python3
"""
Type definitions for mem8 CLI.
"""

from enum import Enum


class SearchMethod(str, Enum):
    """Search method types for content search."""
    FULLTEXT = "fulltext"
    SEMANTIC = "semantic"  # Experimental


class ContentType(str, Enum):
    """Content type filters for search."""
    MEMORY = "memory"
    MEMORIES = "memories"
    ALL = "all"


class ActionType(str, Enum):
    """Action types for memory operations."""
    SHOW = "show"
    DELETE = "delete"
    ARCHIVE = "archive"
    PROMOTE = "promote"


class SyncDirection(str, Enum):
    """Synchronization direction."""
    PULL = "pull"
    PUSH = "push"
    BOTH = "both"


class DeployEnvironment(str, Enum):
    """Deployment environment types."""
    LOCAL = "local"
    STAGING = "staging"
    PRODUCTION = "production"
