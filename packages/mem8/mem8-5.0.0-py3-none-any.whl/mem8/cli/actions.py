#!/usr/bin/env python3
"""
CLI action execution handlers.
"""

import typer
from pathlib import Path
from rich.table import Table

from .utils import get_console
from .state import get_state

# Create console instance
console = get_console()


def execute_action(action: str, results: list, force: bool, verbose: bool):
    """Execute action on found memory."""
    # Enhanced confirmation for destructive actions
    if action in ['delete', 'archive']:
        # Show what will be affected
        console.print(f"\n[yellow]⚠️  About to {action} {len(results)} file(s):[/yellow]")
        for idx, entity in enumerate(results[:5]):  # Show first 5
            console.print(f"  • {entity.path.name}")
        if len(results) > 5:
            console.print(f"  • ... and {len(results) - 5} more")

        if not force:
            # Require explicit typed confirmation for destructive actions
            confirmation_text = "DELETE" if action == "delete" else "ARCHIVE"
            console.print("\n[red]⚠️  This action cannot be easily undone![/red]")
            console.print(f"[dim]Backups will be created in: {get_state().action_engine.backup_dir}[/dim]\n")

            user_input = typer.prompt(
                f"Type '{confirmation_text}' to confirm (or press Ctrl+C to cancel)",
                default="",
                show_default=False
            )
            if user_input.strip() != confirmation_text:
                console.print("❌ [yellow]Action cancelled - confirmation text did not match[/yellow]")
                return

    # Get action engine for execution
    state = get_state()
    action_engine = state.action_engine

    try:
        if action == 'show':
            for entity in results:
                console.print(f"📄 [bold]{entity.path}[/bold]")
                content = entity.path.read_text(encoding='utf-8')
                console.print(content[:500] + "..." if len(content) > 500 else content)
                console.print()
        elif action == 'delete':
            # Use the bulk delete method
            result = action_engine.delete_memory(results, dry_run=False)
            console.print(f"\n✅ [green]Deleted {len(result['success'])} file(s)[/green]")
            for success_path in result['success']:
                console.print(f"  🗑️  [dim]{Path(success_path).name}[/dim]")
            if result['backups']:
                console.print(f"\n💾 [blue]Backups created in: {action_engine.backup_dir}[/blue]")
            for error in result['errors']:
                console.print(f"❌ [red]Error deleting: {error}[/red]")
        elif action == 'archive':
            # For now, just show that archive isn't fully implemented
            console.print("❌ [yellow]Archive action not yet fully implemented[/yellow]")
        elif action == 'promote':
            # For now, just show that promote isn't fully implemented
            console.print("❌ [yellow]Promote action not yet fully implemented[/yellow]")
    except Exception as e:
        console.print(f"❌ [red]Error executing {action}: {e}[/red]")
        if verbose:
            console.print_exception()


def preview_action(action: str, results: list):
    """Preview what action would do without executing."""
    table = Table(title=f"Would {action} {len(results)} memory (dry run)")
    table.add_column("Action", style="cyan", width=10)
    table.add_column("Type", style="blue", width=10)
    table.add_column("Path", style="dim")

    for entity in results:
        # Format relative path for display
        try:
            # If path is not relative to current directory, use absolute path or just filename
            rel_path = entity.path.relative_to(Path.cwd())
        except ValueError:
            # If path is not relative to current directory, use absolute path or just filename
            rel_path = entity.path.name
        table.add_row(action.title(), entity.type, str(rel_path))

    console.print(table)
    console.print("[dim]Run without --dry-run to execute[/dim]")
