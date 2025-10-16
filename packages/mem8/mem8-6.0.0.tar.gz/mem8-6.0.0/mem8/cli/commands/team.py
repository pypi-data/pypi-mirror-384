#!/usr/bin/env python3
"""
Team collaboration commands (experimental).
"""

import typer
from typing import Annotated, Optional

from ..state import set_app_state
from ..utils import get_console

# Get console instance
console = get_console()

# Create team subapp
team_app = typer.Typer(name="team", help="Experimental team collaboration commands")


@team_app.command()
def create(
    name: Annotated[str, typer.Option("--name", help="Team name")],
    description: Annotated[Optional[str], typer.Option("--description", help="Team description")] = None,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Enable verbose output")] = False
):
    """Create a new team (experimental)."""
    set_app_state(verbose=verbose)

    console.print(f"[bold blue]Creating team: {name}[/bold blue]")
    if description:
        console.print(f"Description: {description}")

    console.print("[yellow]⚠️  Team features require backend API (Phase 2)[/yellow]")
    console.print("For now, teams are managed locally through shared directories.")


@team_app.command()
def list(
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Enable verbose output")] = False
):
    """List available teams (experimental)."""
    set_app_state(verbose=verbose)

    console.print("[bold blue]Available teams:[/bold blue]")
    console.print("[yellow]⚠️  Team features require backend API (Phase 2)[/yellow]")


@team_app.command()
def join(
    team_name: Annotated[str, typer.Argument(help="Team name to join")],
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Enable verbose output")] = False
):
    """Join an existing team (experimental)."""
    set_app_state(verbose=verbose)

    console.print(f"[bold blue]Joining team: {team_name}[/bold blue]")
    console.print("[yellow]⚠️  Team features require backend API (Phase 2)[/yellow]")
