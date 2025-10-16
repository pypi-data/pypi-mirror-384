#!/usr/bin/env python3
"""
Init command for workspace initialization via Claude Code plugin.
"""

import typer
import os
import shutil
from typing import Annotated, Optional
from pathlib import Path

from ..state import set_app_state, handle_command_error
from ..utils import get_console

# Get console instance
console = get_console()


def _is_claude_code_available() -> bool:
    """Check if running in Claude Code environment."""
    return (
        (Path.cwd() / '.claude').exists() or
        'CLAUDE_CODE' in os.environ or
        shutil.which('claude') is not None
    )


def _is_plugin_installed() -> bool:
    """Check if mem8 plugin is already installed."""
    claude_dir = Path.cwd() / '.claude'
    if not claude_dir.exists():
        return False

    # Check for plugin marker
    plugin_marker = claude_dir / '.mem8-plugin'
    if plugin_marker.exists():
        return True

    # Check for m8 commands as fallback
    commands_dir = claude_dir / 'commands'
    if commands_dir.exists():
        m8_commands = list(commands_dir.glob('m8-*.md'))
        return len(m8_commands) >= 6  # Should have at least 6 m8 commands

    return False


def register_init_command(app: typer.Typer):
    """Register the init command."""

    @app.command()
    def init(
        force: Annotated[bool, typer.Option(
            "--force", help="Check installation status even if already installed"
        )] = False,
        verbose: Annotated[bool, typer.Option(
            "--verbose", "-v", help="Enable verbose output"
        )] = False
    ):
        """Initialize mem8 workspace using Claude Code plugin.

        This command provides instructions for installing mem8 as a Claude Code plugin.
        For the best experience, use the plugin installation method.
        """
        set_app_state(verbose=verbose)

        try:
            console.print("[bold cyan]mem8 Plugin Installation[/bold cyan]\n")

            # Check if already installed
            if _is_plugin_installed() and not force:
                console.print("[green]✓[/green] mem8 plugin is already installed!\n")
                console.print("Use [bold]mem8 status[/bold] to verify your configuration.")
                console.print("Use [bold]/m8-research[/bold] to start exploring your codebase.\n")
                return

            # Check if Claude Code is available
            if not _is_claude_code_available():
                console.print("[yellow]⚠[/yellow]  Claude Code not detected in this environment.\n")
                console.print("mem8 works best with Claude Code. To install Claude Code:")
                console.print("  Visit: https://claude.ai/code\n")
                return

            # Show installation instructions
            console.print("Installing mem8 as a Claude Code plugin provides:")
            console.print("  [green]✓[/green] 8 workflow commands (/m8-plan, /m8-research, etc.)")
            console.print("  [green]✓[/green] 6 specialized agents for code analysis")
            console.print("  [green]✓[/green] Automatic memory/ directory setup")
            console.print("  [green]✓[/green] Team distribution via .claude/settings.json")
            console.print("  [green]✓[/green] Automatic updates\n")

            console.print("[bold]Installation Steps:[/bold]\n")

            console.print("[cyan]1.[/cyan] Add the mem8 marketplace in Claude Code:")
            console.print("   [bold]/plugin marketplace add killerapp/mem8-plugin[/bold]\n")

            console.print("[cyan]2.[/cyan] Install the mem8 plugin:")
            console.print("   [bold]/plugin install mem8@mem8-official[/bold]\n")

            console.print("[cyan]3.[/cyan] Verify installation:")
            console.print("   [bold]mem8 status[/bold]\n")

            console.print("The memory/ directory will be created automatically when you install the plugin.\n")

            console.print("[dim]─────────────────────────────────────────────────────────[/dim]\n")

            console.print("[bold]Team Installation:[/bold]\n")
            console.print("For automatic installation across your team, add to [bold].claude/settings.json[/bold]:\n")

            json_config = '''[dim]{
  "extraKnownMarketplaces": {
    "mem8": {
      "source": {
        "source": "github",
        "repo": "killerapp/mem8-plugin"
      }
    }
  },
  "enabledPlugins": ["mem8@mem8-official"]
}[/dim]'''
            console.print(json_config + "\n")

            console.print("When team members trust the repository, mem8 installs automatically.\n")

            console.print("[dim]─────────────────────────────────────────────────────────[/dim]\n")

            console.print("[bold]After Installation:[/bold]\n")
            console.print("Try these commands to get started:")
            console.print("  [bold]/m8-research[/bold]    - Research and document your codebase")
            console.print("  [bold]/m8-plan[/bold]        - Create implementation plans")
            console.print("  [bold]/m8-implement[/bold]   - Implement from plans")
            console.print("  [bold]/m8-validate[/bold]    - Validate implementations\n")

            console.print("For more information:")
            console.print("  Docs: https://github.com/killerapp/mem8")
            console.print("  Issues: https://github.com/killerapp/mem8/issues\n")

        except Exception as e:
            handle_command_error(e, verbose, "init")
