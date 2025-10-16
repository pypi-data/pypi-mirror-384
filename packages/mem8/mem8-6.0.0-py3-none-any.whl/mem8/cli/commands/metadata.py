#!/usr/bin/env python3
"""
Repository metadata management commands.
"""

import typer
from typing import Annotated, Optional
from pathlib import Path

from ..state import set_app_state
from ..utils import get_console

# Get console instance
console = get_console()

# Create metadata subcommand app
metadata_app = typer.Typer(name="metadata", help="Repository metadata management and research tools")


@metadata_app.command("git")
def metadata_git(
    format: Annotated[str, typer.Option(
        "--format", help="Output format"
    )] = "yaml",
    verbose: Annotated[bool, typer.Option(
        "--verbose", "-v", help="Enable verbose output"
    )] = False
):
    """Get git repository metadata."""
    from ...core.metadata import get_git_metadata

    set_app_state(verbose=verbose)

    try:
        metadata = get_git_metadata()

        if format == "yaml":
            import yaml
            console.print(yaml.dump(metadata, default_flow_style=False))
        elif format == "json":
            import json
            console.print(json.dumps(metadata, indent=2))
        else:
            for key, value in metadata.items():
                console.print(f"{key}: {value}")

    except Exception as e:
        console.print(f"❌ [bold red]Error getting metadata: {e}[/bold red]")
        if verbose:
            console.print_exception()


@metadata_app.command("research")
def metadata_research(
    topic: Annotated[Optional[str], typer.Argument(help="Research topic/question")] = None,
    output_file: Annotated[Optional[Path], typer.Option(
        "--output", "-o", help="Output to file"
    )] = None,
    format: Annotated[str, typer.Option(
        "--format", help="Output format: yaml, json, or frontmatter"
    )] = "frontmatter",
    verbose: Annotated[bool, typer.Option(
        "--verbose", "-v", help="Enable verbose output"
    )] = False
):
    """Generate complete metadata for research documents (replaces hack/spec_metadata.sh)."""
    # Use default topic if none provided
    if not topic:
        topic = "research"
    from ...core.metadata import generate_research_metadata, format_frontmatter

    set_app_state(verbose=verbose)

    try:
        metadata = generate_research_metadata(topic)

        if format == "frontmatter":
            output = format_frontmatter(metadata)
        elif format == "yaml":
            import yaml
            output = yaml.dump(metadata, default_flow_style=False)
        elif format == "json":
            import json
            output = json.dumps(metadata, indent=2)
        else:
            output = "\n".join(f"{key}: {value}" for key, value in metadata.items())

        if output_file:
            output_file.write_text(output, encoding='utf-8')
            console.print(f"✅ [green]Metadata written to: {output_file}[/green]")
        else:
            console.print(output)

    except Exception as e:
        console.print(f"❌ [bold red]Error generating metadata: {e}[/bold red]")
        if verbose:
            console.print_exception()


@metadata_app.command("project")
def metadata_project(
    format: Annotated[str, typer.Option(
        "--format", help="Output format"
    )] = "yaml",
    verbose: Annotated[bool, typer.Option(
        "--verbose", "-v", help="Enable verbose output"
    )] = False
):
    """Get project metadata and statistics."""
    from ...core.metadata import generate_project_metadata

    set_app_state(verbose=verbose)

    try:
        metadata = generate_project_metadata()

        if format == "yaml":
            import yaml
            console.print(yaml.dump(metadata, default_flow_style=False))
        elif format == "json":
            import json
            console.print(json.dumps(metadata, indent=2))
        else:
            console.print(f"Project Type: {metadata.get('project_type', 'Unknown')}")
            console.print(f"Repository: {metadata['git_metadata']['repository']}")
            console.print(f"Branch: {metadata['git_metadata']['branch']}")
            console.print(f"Commits: {metadata['repository_stats']['total_commits']}")
            console.print(f"Contributors: {metadata['repository_stats']['contributors']}")

    except Exception as e:
        console.print(f"❌ [bold red]Error getting project metadata: {e}[/bold red]")
        if verbose:
            console.print_exception()
