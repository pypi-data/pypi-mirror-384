#!/usr/bin/env python3
"""
Git worktree management commands.
"""

import typer
from typing import Annotated
from pathlib import Path

from ..state import set_app_state
from ..utils import get_console

# Get console instance
console = get_console()

# Create worktree subcommand app
worktree_app = typer.Typer(name="worktree", help="Git worktree management for development workflows")


@worktree_app.command("create")
def worktree_create(
    ticket_id: Annotated[str, typer.Argument(help="Ticket ID (e.g., ENG-1234, GH-123)")],
    branch_name: Annotated[str, typer.Argument(help="Git branch name")],
    base_dir: Annotated[Path, typer.Option(
        "--base-dir", help="Base directory for worktrees"
    )] = Path.home() / "wt",
    auto_launch: Annotated[bool, typer.Option(
        "--launch", help="Auto-launch VS Code in worktree"
    )] = False,
    verbose: Annotated[bool, typer.Option(
        "--verbose", "-v", help="Enable verbose output"
    )] = False
):
    """Create a git worktree for ticket implementation (replaces hack/create_worktree.sh)."""
    from ...core.worktree import create_worktree

    set_app_state(verbose=verbose)

    try:
        worktree_path = create_worktree(ticket_id, branch_name, base_dir)
        console.print(f"✅ [green]Created worktree: {worktree_path}[/green]")

        if auto_launch:
            # Try to open in VS Code
            import subprocess
            import shutil

            if shutil.which("code"):
                console.print("🚀 [cyan]Opening worktree in VS Code[/cyan]")
                subprocess.run(["code", str(worktree_path)], shell=False)
            else:
                console.print("💡 [dim]Install VS Code to auto-open worktrees[/dim]")

    except Exception as e:
        console.print(f"❌ [bold red]Error creating worktree: {e}[/bold red]")
        if verbose:
            console.print_exception()


@worktree_app.command("list")
def worktree_list(
    verbose: Annotated[bool, typer.Option(
        "--verbose", "-v", help="Enable verbose output"
    )] = False
):
    """List existing worktrees."""
    from ...core.worktree import list_worktrees
    from rich.table import Table

    set_app_state(verbose=verbose)

    try:
        worktrees = list_worktrees()

        if not worktrees:
            console.print("[yellow]No worktrees found[/yellow]")
            return

        table = Table(title=f"Git Worktrees ({len(worktrees)} found)")
        table.add_column("Path", style="cyan")
        table.add_column("Branch", style="green")
        table.add_column("Commit", style="dim", width=12)
        table.add_column("Status", style="yellow")

        for wt in worktrees:
            path = wt.get('path', 'Unknown')
            branch = wt.get('branch', wt.get('commit', 'Detached'))[:20] if wt.get('branch') else 'detached'
            commit = wt.get('commit', 'Unknown')[:12]

            if wt.get('bare'):
                status = "bare"
            elif wt.get('detached'):
                status = "detached"
            else:
                status = "active"

            table.add_row(path, branch, commit, status)

        console.print(table)

    except Exception as e:
        console.print(f"❌ [bold red]Error listing worktrees: {e}[/bold red]")
        if verbose:
            console.print_exception()


@worktree_app.command("remove")
def worktree_remove(
    worktree_path: Annotated[Path, typer.Argument(help="Path to worktree to remove")],
    force: Annotated[bool, typer.Option(
        "--force", help="⚠️  Force removal even with uncommitted changes (use with caution)"
    )] = False,
    verbose: Annotated[bool, typer.Option(
        "--verbose", "-v", help="Enable verbose output"
    )] = False
):
    """Remove a worktree."""
    from ...core.worktree import remove_worktree

    set_app_state(verbose=verbose)

    if not force:
        import typer
        confirm = typer.confirm(f"Remove worktree at {worktree_path}?")
        if not confirm:
            console.print("❌ [yellow]Removal cancelled[/yellow]")
            return

    try:
        remove_worktree(worktree_path, force)
        console.print(f"✅ [green]Removed worktree: {worktree_path}[/green]")

    except Exception as e:
        console.print(f"❌ [bold red]Error removing worktree: {e}[/bold red]")
        if verbose:
            console.print_exception()
