#!/usr/bin/env python3
"""
Find commands for thought discovery and management.
"""

import typer
from typing import Annotated, Optional
from pathlib import Path
import re
from rich.table import Table

from ..types import ActionType
from ..state import get_state, set_app_state
from ..actions import execute_action as _execute_action, preview_action as _preview_action
from ..utils import get_console

# Get console instance
console = get_console()

# Create find subcommand app
find_app = typer.Typer(
    name="find",
    help="Browse/filter memory by type, status, or metadata. For content search, use 'mem8 search <query>' instead."
)


def _find_memory_new(
    filter_type: str = "all",
    filter_value: str = None,
    keywords: Optional[str] = None,
    limit: int = 20,
    action: Optional[ActionType] = None,
    dry_run: bool = False,
    force: bool = False,
    verbose: bool = False
):
    """Core find logic used by all subcommands."""
    set_app_state(verbose=verbose)
    state = get_state()
    discovery = state.memory_manager.thought_discovery

    # Get filtered memory using existing methods
    if filter_type == "type":
        results = discovery.find_by_type(filter_value)
    elif filter_type == "scope":
        results = discovery.find_by_scope(filter_value)
    elif filter_type == "status":
        results = discovery.find_by_status(filter_value)
    else:
        results = discovery.discover_all_memory()

    # Apply keyword filter if provided
    if keywords and keywords.strip():
        keyword_results = []
        # Split keywords by spaces, treat each as regex pattern
        patterns = [re.compile(k.strip(), re.IGNORECASE) for k in keywords.split() if k.strip()]

        for entity in results:
            # Search in content, title, tags
            searchable_text = (
                entity.content + ' ' +
                str(entity.metadata.get('topic', '')) + ' ' +
                ' '.join(entity.metadata.get('tags', []))
            )

            # Match if ANY pattern matches (OR logic)
            if any(pattern.search(searchable_text) for pattern in patterns):
                keyword_results.append(entity)

        results = keyword_results

    # Limit results
    results = results[:limit]

    if not results:
        console.print("[yellow]❌ No memory found[/yellow]")
        return

    # Show what we're finding
    search_desc = filter_value or filter_type
    if keywords:
        search_desc += f" matching '{keywords}'"
    console.print(f"[bold blue]🔍 Finding: {search_desc}[/bold blue]")

    if action:
        action_color = "yellow" if dry_run else "red" if action == ActionType.DELETE else "cyan"
        dry_run_text = " (dry run)" if dry_run else ""
        console.print(f"[bold {action_color}]Action: {action.value}{dry_run_text}[/bold {action_color}]")

    # Display results table
    table = Table(title=f"Found {len(results)} memory")
    table.add_column("Type", style="cyan", width=10)
    table.add_column("Title", style="green")
    table.add_column("Status", style="yellow", width=12)
    table.add_column("Scope", style="blue", width=10)
    table.add_column("Path", style="dim")

    for entity in results:
        # Extract title from metadata or content
        title = entity.metadata.get('topic', entity.path.stem)
        if len(title) > 40:
            title = title[:37] + "..."

        # Format path relative to workspace
        try:
            rel_path = entity.path.relative_to(Path.cwd())
        except ValueError:
            rel_path = entity.path

        table.add_row(
            entity.type.title(),
            title,
            entity.lifecycle_state or "Unknown",
            entity.scope or "Unknown",
            str(rel_path)
        )

    console.print(table)

    # Execute action if specified
    if action and not dry_run:
        _execute_action(action.value, results, force, verbose)
    elif action and dry_run:
        _preview_action(action.value, results)


@find_app.command("all")
def find_all_new(
    keywords: Annotated[Optional[str], typer.Argument(
        help="Keywords to search for (space-separated, supports regex)"
    )] = None,
    limit: Annotated[int, typer.Option(
        "--limit", help="Maximum results to return"
    )] = 20,
    action: Annotated[Optional[ActionType], typer.Option(
        "--action", help="Action to perform on found memory"
    )] = None,
    dry_run: Annotated[bool, typer.Option(
        "--dry-run", help="Show what would be done without executing"
    )] = False,
    force: Annotated[bool, typer.Option(
        "--force", help="⚠️  Skip confirmation prompts for destructive actions (use with caution)"
    )] = False,
    verbose: Annotated[bool, typer.Option(
        "--verbose", "-v", help="Enable verbose output"
    )] = False
):
    """Find all memory, optionally filtered by keywords."""
    _find_memory_new("all", None, keywords, limit, action, dry_run, force, verbose)


@find_app.command("plans")
def find_plans_new(
    keywords: Annotated[Optional[str], typer.Argument(
        help="Keywords to search for (space-separated, supports regex)"
    )] = None,
    limit: Annotated[int, typer.Option(
        "--limit", help="Maximum results to return"
    )] = 20,
    action: Annotated[Optional[ActionType], typer.Option(
        "--action", help="Action to perform on found memory"
    )] = None,
    dry_run: Annotated[bool, typer.Option(
        "--dry-run", help="Show what would be done without executing"
    )] = False,
    force: Annotated[bool, typer.Option(
        "--force", help="⚠️  Skip confirmation prompts for destructive actions (use with caution)"
    )] = False,
    verbose: Annotated[bool, typer.Option(
        "--verbose", "-v", help="Enable verbose output"
    )] = False
):
    """Find plan documents, optionally filtered by keywords."""
    _find_memory_new("type", "plan", keywords, limit, action, dry_run, force, verbose)


@find_app.command("research")
def find_research_new(
    keywords: Annotated[Optional[str], typer.Argument(
        help="Keywords to search for (space-separated, supports regex)"
    )] = None,
    limit: Annotated[int, typer.Option(
        "--limit", help="Maximum results to return"
    )] = 20,
    action: Annotated[Optional[ActionType], typer.Option(
        "--action", help="Action to perform on found memory"
    )] = None,
    dry_run: Annotated[bool, typer.Option(
        "--dry-run", help="Show what would be done without executing"
    )] = False,
    force: Annotated[bool, typer.Option(
        "--force", help="⚠️  Skip confirmation prompts for destructive actions (use with caution)"
    )] = False,
    verbose: Annotated[bool, typer.Option(
        "--verbose", "-v", help="Enable verbose output"
    )] = False
):
    """Find research documents, optionally filtered by keywords."""
    _find_memory_new("type", "research", keywords, limit, action, dry_run, force, verbose)


@find_app.command("shared")
def find_shared_new(
    keywords: Annotated[Optional[str], typer.Argument(
        help="Keywords to search for (space-separated, supports regex)"
    )] = None,
    limit: Annotated[int, typer.Option(
        "--limit", help="Maximum results to return"
    )] = 20,
    action: Annotated[Optional[ActionType], typer.Option(
        "--action", help="Action to perform on found memory"
    )] = None,
    dry_run: Annotated[bool, typer.Option(
        "--dry-run", help="Show what would be done without executing"
    )] = False,
    verbose: Annotated[bool, typer.Option(
        "--verbose", "-v", help="Enable verbose output"
    )] = False
):
    """Find shared memory, optionally filtered by keywords."""
    _find_memory_new("scope", "shared", keywords, limit, action, dry_run, verbose)


@find_app.command("completed")
def find_completed_new(
    keywords: Annotated[Optional[str], typer.Argument(
        help="Keywords to search for (space-separated, supports regex)"
    )] = None,
    limit: Annotated[int, typer.Option(
        "--limit", help="Maximum results to return"
    )] = 20,
    action: Annotated[Optional[ActionType], typer.Option(
        "--action", help="Action to perform on found memory"
    )] = None,
    dry_run: Annotated[bool, typer.Option(
        "--dry-run", help="Show what would be done without executing"
    )] = False,
    verbose: Annotated[bool, typer.Option(
        "--verbose", "-v", help="Enable verbose output"
    )] = False
):
    """Find completed memory, optionally filtered by keywords."""
    _find_memory_new("status", "completed", keywords, limit, action, dry_run, verbose)
