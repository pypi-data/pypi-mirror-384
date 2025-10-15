#!/usr/bin/env python3
"""
Template management commands.
"""

import typer
from typing import Annotated, Optional

from ..state import set_app_state, handle_command_error
from ..utils import get_console

# Get console instance
console = get_console()

# Create templates subcommand app
templates_app = typer.Typer(name="templates", help="Template source management and inspection")


@templates_app.command("list")
def templates_list(
    source: Annotated[Optional[str], typer.Option(
        "--source", help="Template source (local path, git URL, or GitHub shorthand). Uses default/builtin if not specified."
    )] = None,
    verbose: Annotated[bool, typer.Option(
        "--verbose", "-v", help="Enable verbose output"
    )] = False
):
    """List available templates from a source."""
    from ...core.template_source import create_template_source
    from ...core.config import Config
    from rich.table import Table

    set_app_state(verbose=verbose)

    # Use provided source, configured default, or builtin
    if source is None:
        config = Config()
        source = config.get('templates.default_source')

    source_display = source or "builtin"
    console.print(f"[bold blue]Templates from: {source_display}[/bold blue]\n")

    try:
        with create_template_source(source) as template_source:
            # Load manifest if available
            manifest = template_source.load_manifest()

            if manifest:
                # Display from manifest
                table = Table(title=f"Templates (manifest v{manifest.version})")
                table.add_column("Name", style="cyan")
                table.add_column("Type", style="green")
                table.add_column("Description", style="dim")

                for name, template_def in manifest.templates.items():
                    desc = template_def.description or "(no description)"
                    table.add_row(name, template_def.type, desc)

                console.print(table)

                if manifest.metadata:
                    console.print("\n[dim]Source metadata:[/dim]")
                    for key, value in manifest.metadata.items():
                        console.print(f"  {key}: {value}")
            else:
                # Fallback: list discovered templates
                templates = template_source.list_templates()

                if templates:
                    console.print("[yellow]No manifest found, listing discovered templates:[/yellow]\n")
                    for template in templates:
                        console.print(f"  • {template}")
                else:
                    console.print("[yellow]No templates found in source[/yellow]")

            if verbose:
                console.print(f"\n[dim]Source type: {template_source.source_type.value}[/dim]")
                console.print(f"[dim]Resolved path: {template_source.resolve()}[/dim]")

    except Exception as e:
        handle_command_error(e, verbose, "template listing")


@templates_app.command("validate")
def templates_validate(
    source: Annotated[Optional[str], typer.Option(
        "--source", help="Template source to validate (local path, git URL, or GitHub shorthand)"
    )] = None,
    verbose: Annotated[bool, typer.Option(
        "--verbose", "-v", help="Enable verbose output"
    )] = False
):
    """Validate a template source and its manifest."""
    from ...core.template_source import create_template_source
    from ...core.config import Config

    set_app_state(verbose=verbose)

    # Use provided source or configured default
    if source is None:
        config = Config()
        source = config.get('templates.default_source')
        if source is None:
            console.print("[red]No source specified and no default configured[/red]")
            console.print("💡 [dim]Use --source to specify a template source[/dim]")
            return

    console.print(f"[bold blue]Validating template source: {source}[/bold blue]\n")

    issues = []
    warnings = []

    try:
        with create_template_source(source) as template_source:
            # Check if source resolves
            try:
                resolved_path = template_source.resolve()
                console.print(f"✅ [green]Source resolves to: {resolved_path}[/green]")
            except Exception as e:
                issues.append(f"Failed to resolve source: {e}")
                console.print(f"❌ [red]Failed to resolve source: {e}[/red]")
                return

            # Check for manifest
            manifest_path = resolved_path / "manifest.yaml"
            if manifest_path.exists():
                console.print("✅ [green]Manifest file found[/green]")

                # Load and validate manifest
                try:
                    manifest = template_source.load_manifest()
                    console.print(f"✅ [green]Manifest parsed successfully (version {manifest.version})[/green]")

                    # Validate templates
                    console.print(f"\n[bold]Validating {len(manifest.templates)} template(s):[/bold]\n")
                    for name, template_def in manifest.templates.items():
                        console.print(f"  📦 [cyan]{name}[/cyan]")

                        # Check if template path exists
                        source_dir = resolved_path / manifest.source
                        template_path = source_dir / template_def.path

                        if template_path.exists():
                            console.print(f"    ✅ Path exists: {template_def.path}")
                        else:
                            issue = f"Template path not found: {name} -> {template_def.path}"
                            issues.append(issue)
                            console.print(f"    ❌ [red]Path not found: {template_def.path}[/red]")

                        # Check for cookiecutter.json
                        cookiecutter_json = template_path / "cookiecutter.json"
                        if cookiecutter_json.exists():
                            console.print("    ✅ cookiecutter.json found")
                        else:
                            warning = f"No cookiecutter.json in template: {name}"
                            warnings.append(warning)
                            console.print("    ⚠️  [yellow]No cookiecutter.json found[/yellow]")

                        if template_def.description:
                            console.print(f"    [dim]{template_def.description}[/dim]")

                except Exception as e:
                    issue = f"Failed to parse manifest: {e}"
                    issues.append(issue)
                    console.print(f"❌ [red]Failed to parse manifest: {e}[/red]")
            else:
                warnings.append("No manifest file (will fallback to directory discovery)")
                console.print("⚠️  [yellow]No manifest file found[/yellow]")
                console.print("    [dim]Templates will be discovered from directory structure[/dim]")

                # Try to list templates anyway
                templates = template_source.list_templates()
                if templates:
                    console.print(f"\n[bold]Discovered {len(templates)} template(s) by fallback:[/bold]")
                    for template in templates:
                        console.print(f"  • {template}")

            # Summary
            console.print("\n" + "="*50)
            if not issues and not warnings:
                console.print("✅ [bold green]Validation passed! Template source is ready to use.[/bold green]")
            elif not issues:
                console.print(f"✅ [green]Validation passed with {len(warnings)} warning(s)[/green]")
                for warning in warnings:
                    console.print(f"  ⚠️  {warning}")
            else:
                console.print(f"❌ [red]Validation failed with {len(issues)} error(s)[/red]")
                for issue in issues:
                    console.print(f"  • {issue}")
                if warnings:
                    console.print(f"\n⚠️  [yellow]And {len(warnings)} warning(s):[/yellow]")
                    for warning in warnings:
                        console.print(f"  • {warning}")

    except Exception as e:
        handle_command_error(e, verbose, "template validation")


@templates_app.command("set-default")
def templates_set_default(
    source: Annotated[str, typer.Argument(
        help="Template source to set as default (local path, git URL, or GitHub shorthand). Use 'builtin' to reset."
    )],
    verbose: Annotated[bool, typer.Option(
        "--verbose", "-v", help="Enable verbose output"
    )] = False
):
    """Set the default template source for init commands."""
    from ...core.config import Config

    set_app_state(verbose=verbose)
    config = Config()

    # Handle builtin keyword
    if source.lower() == "builtin":
        config.set('templates.default_source', None)
        console.print("✅ [green]Reset to builtin templates[/green]")
    else:
        config.set('templates.default_source', source)
        console.print(f"✅ [green]Default template source set to: {source}[/green]")
        console.print("💡 [dim]Run 'mem8 templates validate' to test the source[/dim]")
