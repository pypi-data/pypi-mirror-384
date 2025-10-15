#!/usr/bin/env python3
"""
CLI command modules for mem8.
"""

from .find import find_app
from .team import team_app
from .deploy import deploy_app
from .core import register_core_commands
# Init command removed - use plugin installation instead
# from .init import register_init_command
from .worktree import worktree_app
from .metadata import metadata_app
from .templates import templates_app
from .utilities import gh_app, register_tools_command, register_ports_command

__all__ = [
    "find_app",
    "team_app",
    "deploy_app",
    "register_core_commands",
    # "register_init_command",  # Removed - use plugin installation
    "worktree_app",
    "metadata_app",
    "templates_app",
    "gh_app",
    "register_tools_command",
    "register_ports_command"
]
