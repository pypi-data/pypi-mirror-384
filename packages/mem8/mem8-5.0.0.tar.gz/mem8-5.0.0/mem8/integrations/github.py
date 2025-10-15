"""GitHub integration helpers for mem8.

Provides a robust wrapper around the GitHub CLI (gh) with structured data,
version detection, and graceful fallbacks for environments without gh.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Union
import logging

logger = logging.getLogger(__name__)


def gh_available() -> bool:
    return shutil.which("gh") is not None


def version_compare(version1: str, version2: str) -> int:
    """Compare two version strings. Returns -1, 0, or 1."""
    def version_tuple(v):
        return tuple(map(int, v.split('.')))

    v1, v2 = version_tuple(version1), version_tuple(version2)
    return (v1 > v2) - (v1 < v2)


def get_gh_version() -> Optional[str]:
    """Get GitHub CLI version."""
    if not gh_available():
        return None

    try:
        result = subprocess.run(
            ["gh", "--version"],
            capture_output=True, text=True, timeout=2, check=False
        )
        if result.returncode == 0:
            # Parse version from output like "gh version 2.40.1 (2023-12-13)"
            match = re.search(r"gh version (\d+\.\d+\.\d+)", result.stdout)
            return match.group(1) if match else None
    except Exception:
        pass
    return None


class GitHubCommand:
    """Builder for GitHub CLI commands with validation and structured output."""

    def __init__(self):
        self.cmd = ["gh"]
        self.timeout = 5
        self.json_output = False
        self.hostname = None

    def auth_status(self) -> 'GitHubCommand':
        """Add auth status subcommand."""
        self.cmd.extend(["auth", "status"])
        return self

    def api_user(self) -> 'GitHubCommand':
        """Add API user endpoint."""
        self.cmd.extend(["api", "user"])
        return self

    def repo_view(self) -> 'GitHubCommand':
        """Add repo view subcommand."""
        self.cmd.extend(["repo", "view"])
        return self

    def auth_token(self) -> 'GitHubCommand':
        """Add auth token subcommand."""
        self.cmd.extend(["auth", "token"])
        return self

    def with_json(self, fields: Optional[str] = None) -> 'GitHubCommand':
        """Add JSON output flag with optional field specification."""
        self.cmd.append("--json")
        if fields:
            self.cmd.append(fields)
        self.json_output = True
        return self

    def with_hostname(self, hostname: str) -> 'GitHubCommand':
        """Add hostname flag."""
        self.cmd.extend(["--hostname", hostname])
        self.hostname = hostname
        return self

    def with_timeout(self, timeout: int) -> 'GitHubCommand':
        """Set command timeout."""
        self.timeout = timeout
        return self

    def execute(self) -> Union[Dict[str, Any], str, None]:
        """Execute command and return parsed result."""
        if not gh_available():
            return None

        try:
            result = subprocess.run(
                self.cmd, capture_output=True, text=True,
                timeout=self.timeout, check=False
            )

            if result.returncode != 0:
                logger.debug(f"gh command failed: {' '.join(self.cmd)}, stderr: {result.stderr}")
                return None

            if self.json_output:
                try:
                    return json.loads(result.stdout)
                except json.JSONDecodeError as e:
                    logger.debug(f"Failed to parse JSON from gh command: {e}")
                    return None

            return result.stdout.strip()

        except subprocess.TimeoutExpired:
            logger.debug(f"gh command timed out: {' '.join(self.cmd)}")
            return None
        except Exception as e:
            logger.debug(f"gh command failed with exception: {e}")
            return None


@dataclass
class GitHubContext:
    """Structured GitHub context with validation and robust detection."""
    username: Optional[str] = None
    active_account: Optional[str] = None
    all_accounts: List[str] = field(default_factory=list)
    repo_owner: Optional[str] = None
    repo_name: Optional[str] = None
    has_token: bool = False
    gh_version: Optional[str] = None
    hostname: str = "github.com"

    @classmethod
    def detect(cls, hostname: str = "github.com") -> 'GitHubContext':
        """Auto-detect GitHub context using best available methods."""
        context = cls(hostname=hostname)
        context.gh_version = get_gh_version()

        # Strategy 1: Try API-based user detection (most reliable)
        context._detect_user_via_api()

        # Strategy 2: Detect repository info using JSON
        context._detect_repo_info()

        # Strategy 3: Check for token availability
        context._detect_token()

        # Strategy 4: Fallback to auth status parsing if needed
        if not context.username:
            context._detect_user_via_auth_status()

        context._validate()
        return context

    def _detect_user_via_api(self) -> None:
        """Detect active user using gh api user command."""
        try:
            user_data = GitHubCommand().api_user().with_hostname(self.hostname).execute()
            if isinstance(user_data, dict) and "login" in user_data:
                self.username = user_data["login"]
                self.active_account = user_data["login"]
                logger.debug(f"Detected GitHub user via API: {self.username}")
                return
        except Exception as e:
            logger.debug(f"Failed to detect user via API: {e}")

    def _detect_repo_info(self) -> None:
        """Detect current repository information using structured data."""
        try:
            repo_data = GitHubCommand().repo_view().with_json("owner,name").execute()
            if isinstance(repo_data, dict):
                if "owner" in repo_data and "name" in repo_data:
                    self.repo_owner = repo_data["owner"]["login"]
                    self.repo_name = repo_data["name"]
                    logger.debug(f"Detected repo: {self.repo_owner}/{self.repo_name}")
        except Exception as e:
            logger.debug(f"Failed to detect repo info: {e}")

    def _detect_token(self) -> None:
        """Check if we have a valid token."""
        try:
            token = GitHubCommand().auth_token().with_hostname(self.hostname).execute()
            self.has_token = bool(token and isinstance(token, str) and token.strip())
        except Exception:
            # Try environment variables as fallback
            env_token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
            self.has_token = bool(env_token)

    def _detect_user_via_auth_status(self) -> None:
        """Fallback: detect user via auth status parsing."""
        try:
            from ..core.utils import detect_gh_active_login
            self.username = detect_gh_active_login(self.hostname)
            if self.username:
                self.active_account = self.username
                logger.debug(f"Detected GitHub user via auth status: {self.username}")
        except Exception as e:
            logger.debug(f"Failed to detect user via auth status: {e}")

    def _validate(self) -> None:
        """Validate context consistency and log warnings."""
        if self.username and self.repo_owner and self.username != self.repo_owner:
            logger.info(f"Note: Authenticated as {self.username} but repo owned by {self.repo_owner}")

        if not self.username and not self.has_token:
            logger.debug("No GitHub authentication detected")

    def is_authenticated(self) -> bool:
        """Check if user is authenticated."""
        return bool(self.username or self.has_token)

    def get_effective_username(self, prefer_authenticated: bool = True) -> Optional[str]:
        """Get the most appropriate username based on context."""
        if prefer_authenticated:
            return self.username or self.repo_owner
        else:
            return self.repo_owner or self.username

    def get_repo_context(self) -> Optional[Dict[str, str]]:
        """Get repository context if available."""
        if self.repo_owner and self.repo_name:
            return {"owner": self.repo_owner, "name": self.repo_name}
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for backward compatibility."""
        return {
            "username": self.username,
            "org": self.get_effective_username(),
            "repo": self.repo_name,
            "auth_user": self.username,
            "repo_owner": self.repo_owner,
            "has_token": self.has_token,
            "gh_version": self.gh_version
        }


def whoami(host: str = "github.com") -> Optional[str]:
    """Return the active login according to robust detection."""
    context = GitHubContext.detect(host)
    return context.username


def get_token(host: str = "github.com") -> Optional[str]:
    """Get a token via gh auth token or environment with robust error handling."""
    try:
        token = GitHubCommand().auth_token().with_hostname(host).with_timeout(3).execute()
        if isinstance(token, str) and token.strip():
            return token.strip()
    except Exception:
        pass

    # Fallback to environment variables
    return os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")


def ensure_login(host: str = "github.com") -> bool:
    """Best-effort check that gh has an active login for host."""
    context = GitHubContext.detect(host)
    return context.is_authenticated()


def get_current_repo_info() -> Optional[Dict[str, str]]:
    """Get current repository info using robust detection.

    Returns dict with 'owner' and 'name' keys, or None if not available.
    """
    context = GitHubContext.detect()
    return context.get_repo_context()


def get_consistent_github_context(prefer_authenticated_user: bool = True) -> Dict[str, Optional[str]]:
    """Get consistent GitHub context for mem8 operations using robust detection.

    Args:
        prefer_authenticated_user: If True, prefer authenticated user over repo owner

    Returns:
        Dict with 'username', 'org', 'repo' keys for backward compatibility.
    """
    context = GitHubContext.detect()
    result = context.to_dict()

    # Apply preference logic
    if prefer_authenticated_user:
        result["org"] = context.get_effective_username(prefer_authenticated=True)
    else:
        result["org"] = context.get_effective_username(prefer_authenticated=False)

    return result

