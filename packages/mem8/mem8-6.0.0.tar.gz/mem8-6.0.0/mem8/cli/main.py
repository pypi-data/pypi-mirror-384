#!/usr/bin/env python3
"""
Typer-based CLI implementation for mem8.
Modern CLI framework with enhanced type safety and developer experience.
"""

import typer

from .. import __version__

# Import types and utils from CLI package
from .utils import get_console

# Import state management and actions

# Import template management

# Import command modules
from .commands import (
    find_app, team_app, deploy_app,
    register_core_commands,
    worktree_app, metadata_app, templates_app,
    gh_app, register_tools_command, register_ports_command
)

# Create console instance
console = get_console()

# Create Typer app
typer_app = typer.Typer(
    name="mem8",
    help="Memory management CLI for team collaboration",
    add_completion=False,  # We'll manage this ourselves
    rich_markup_mode="rich"
)

# ============================================================================
# App Setup and Callbacks
# ============================================================================

def version_callback(value: bool):
    if value:
        console.print(f"mem8 version {__version__}")
        raise typer.Exit()


@typer_app.callback()
def main_callback(
    version: bool = typer.Option(
        None, "--version", "-V",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit"
    )
):
    """Memory management CLI for team collaboration."""
    pass


# ============================================================================
# Register Core Commands
# ============================================================================

# Register core commands: status, doctor, serve, search, sync
register_core_commands(typer_app)


# ============================================================================
# Register Command Groups and Commands
# ============================================================================

# Register subcommand groups
typer_app.add_typer(find_app, name="find")
typer_app.add_typer(team_app, name="team")
typer_app.add_typer(deploy_app, name="deploy")
typer_app.add_typer(worktree_app, name="worktree")
typer_app.add_typer(metadata_app, name="metadata")
typer_app.add_typer(templates_app, name="templates")
typer_app.add_typer(gh_app, name="gh")

# Register utility commands
register_tools_command(typer_app)
register_ports_command(typer_app)


# ============================================================================
# Shell Completion (Using Typer's built-in system)
# ============================================================================

# Enable Typer's built-in completion
typer_app.add_completion = True
