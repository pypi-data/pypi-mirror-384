#!/usr/bin/env python3
"""
Core CLI commands for mem8.
"""

import typer
from typing import Annotated, Optional
from pathlib import Path

from ..types import SearchMethod, ContentType, SyncDirection
from ..state import get_state, set_app_state, handle_command_error
from ..utils import get_console
from ...core.templates import TemplateManager

# Get console instance
console = get_console()


def register_core_commands(app: typer.Typer):
    """Register all core commands to the main app."""

    @app.command()
    def status(
        detailed: Annotated[bool, typer.Option("--detailed", help="Show detailed status information")] = False,
        verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Enable verbose output")] = False
    ):
        """Show mem8 workspace status."""
        set_app_state(verbose=verbose)
        state = get_state()
        memory_manager = state.memory_manager

        console.print("[bold blue]mem8 Workspace Status[/bold blue]")

        try:
            status_info = memory_manager.get_status(detailed=detailed)

            # Check Claude Code integration
            template_manager = TemplateManager()
            claude_analysis = template_manager.analyze_claude_template(Path.cwd())
            has_claude = Path('.claude').exists()

            # Basic status table
            from rich.table import Table
            table = Table()
            table.add_column("Component", style="cyan")
            table.add_column("Status", style="green")
            table.add_column("Details", style="dim")

            # Add Claude Code status first if it exists
            if has_claude:
                claude_status = f"✅ Active ({len(claude_analysis['existing_commands'])} cmds, {len(claude_analysis['existing_agents'])} agents)"
                table.add_row(
                    "🤖 Claude Code",
                    claude_status,
                    ".claude/"
                )

            for component, info in status_info['components'].items():
                status_icon = "✅" if info['exists'] else "❌"
                table.add_row(
                    component.title().replace('_', ' '),
                    f"{status_icon} {'Ready' if info['exists'] else 'Missing'}",
                    str(info['path'])
                )

            console.print(table)

            # Show thought counts if detailed
            if detailed:
                if 'thought_counts' in status_info:
                    counts = status_info['thought_counts']
                    console.print("\n[bold blue]Thought Statistics:[/bold blue]")

                    count_table = Table()
                    count_table.add_column("Type", style="cyan")
                    count_table.add_column("Count", style="yellow")

                    for thought_type, count in counts.items():
                        count_table.add_row(thought_type.title(), str(count))

                    console.print(count_table)

                # Show Claude Code details if present
                if has_claude and (claude_analysis['existing_commands'] or claude_analysis['existing_agents']):
                    console.print("\n[bold blue]Claude Code Components:[/bold blue]")
                    if claude_analysis['existing_commands']:
                        cmd_preview = ', '.join(claude_analysis['existing_commands'][:6])
                        if len(claude_analysis['existing_commands']) > 6:
                            cmd_preview += f" (+{len(claude_analysis['existing_commands']) - 6} more)"
                        console.print(f"  📝 Commands: {cmd_preview}")
                    if claude_analysis['existing_agents']:
                        agent_preview = ', '.join(claude_analysis['existing_agents'][:4])
                        if len(claude_analysis['existing_agents']) > 4:
                            agent_preview += f" (+{len(claude_analysis['existing_agents']) - 4} more)"
                        console.print(f"  🤖 Agents: {agent_preview}")

            # Show any issues
            if 'issues' in status_info and status_info['issues']:
                console.print("\n⚠️  [bold yellow]Issues:[/bold yellow]")
                for issue in status_info['issues']:
                    console.print(f"  • {issue}")

        except Exception as e:
            handle_command_error(e, verbose, "status check")

    @app.command()
    def doctor(
        fix: Annotated[bool, typer.Option("--fix", help="Attempt to automatically fix issues")] = False,
        json_output: Annotated[bool, typer.Option("--json", help="Output results as JSON for agent consumption")] = False,
        template_source: Annotated[Optional[str], typer.Option(
            "--template-source", help="Template source for toolbelt definition: local path, git URL, or GitHub shorthand (org/repo)"
        )] = None,
        verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Enable verbose output")] = False
    ):
        """Diagnose and fix mem8 workspace issues."""
        import json
        import sys

        set_app_state(verbose=verbose)
        state = get_state()
        memory_manager = state.memory_manager

        # Resolve template source from: CLI flag > project config > user config > builtin
        if template_source is None:
            from ...core.config import Config

            # Check project-level config first
            project_config_file = Path.cwd() / ".mem8" / "config.yaml"
            if project_config_file.exists():
                import yaml
                try:
                    with open(project_config_file, 'r') as f:
                        project_config = yaml.safe_load(f) or {}
                        template_source = project_config.get('templates', {}).get('default_source')
                except Exception:
                    pass

            # Fall back to user-level config
            if template_source is None:
                config = Config()
                template_source = config.get('templates.default_source')

        if not json_output:
            console.print("[bold blue]Running mem8 diagnostics...[/bold blue]")
            if template_source:
                console.print(f"[dim]Using template source: {template_source}[/dim]")

        try:
            diagnosis = memory_manager.diagnose_workspace(auto_fix=fix, template_source=template_source)

            # JSON output mode
            if json_output:
                json_output_data = {
                    "status": "healthy" if not diagnosis['issues'] else "unhealthy",
                    "health_score": diagnosis['health_score'],
                    "issues": diagnosis['issues'],
                    "fixes_applied": diagnosis['fixes_applied'],
                    "recommendations": diagnosis.get('recommendations', [])
                }
                print(json.dumps(json_output_data, indent=2))
                # Exit with non-zero if there are issues
                if diagnosis['issues']:
                    sys.exit(1)
                return

            # Human-readable output mode
            # Show issues
            if diagnosis['issues']:
                console.print("\n⚠️  [bold yellow]Issues found:[/bold yellow]")
                for issue in diagnosis['issues']:
                    severity_icon = {
                        'error': '❌',
                        'warning': '⚠️',
                        'info': 'ℹ️'
                    }.get(issue['severity'], '•')
                    console.print(f"  {severity_icon} {issue['description']}")
                    if fix and issue.get('fixed'):
                        console.print("    ✅ [green]Fixed automatically[/green]")

                    # Show missing tools with install commands
                    if 'missing_tools' in issue:
                        for tool in issue['missing_tools']:
                            version_info = f" (requires {tool['version']})" if tool.get('version') else ""
                            console.print(f"    • [cyan]{tool['name']}[/cyan] ({tool['command']}){version_info} - {tool['description']}")
                            console.print(f"      Install: [yellow]{tool['install']}[/yellow]")

                            # Show current version if available
                            if tool.get('current_version'):
                                console.print(f"      Current: [yellow]{tool['current_version']}[/yellow]")

            # Show fixes applied
            if fix and diagnosis['fixes_applied']:
                console.print("\n✅ [bold green]Fixes applied:[/bold green]")
                for fix_msg in diagnosis['fixes_applied']:
                    console.print(f"  • {fix_msg}")

            # Show recommendations
            if diagnosis.get('recommendations'):
                console.print("\n💡 [bold blue]Recommendations:[/bold blue]")
                for rec in diagnosis['recommendations']:
                    console.print(f"  • {rec}")

            # Overall health
            if not diagnosis['issues']:
                console.print("\n✅ [bold green]All checks passed! Your mem8 workspace is healthy.[/bold green]")

                # Save toolbelt when healthy
                try:
                    from ...core.toolbelt import save_toolbelt
                    output_file = save_toolbelt()
                    if verbose:
                        console.print(f"[dim]Saved toolbelt to {output_file}[/dim]")
                except Exception:
                    pass  # Non-critical, don't fail on this

            elif fix:
                console.print(f"\n🔧 [blue]Fixed {len(diagnosis['fixes_applied'])} of {len(diagnosis['issues'])} issues.[/blue]")
            else:
                console.print(f"\n⚠️  [yellow]Found {len(diagnosis['issues'])} issues. Run with --fix to attempt repairs.[/yellow]")

            # Exit with non-zero code if issues remain (CI-friendly)
            if diagnosis['issues']:
                sys.exit(1)

        except Exception as e:
            handle_command_error(e, verbose, "diagnostics")

    @app.command()
    def serve(
        host: Annotated[str, typer.Option("--host", help="Host to bind to")] = "0.0.0.0",
        port: Annotated[int, typer.Option("--port", help="Port to bind to")] = 8000,
        reload: Annotated[bool, typer.Option("--reload", help="Enable auto-reload for development")] = False,
        workers: Annotated[int, typer.Option("--workers", help="Number of worker processes")] = 1,
        verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Enable verbose output")] = False
    ):
        """Start the mem8 API server (FastAPI backend)."""
        console.print(f"🚀 [bold blue]Starting mem8 API server on {host}:{port}[/bold blue]")

        # Check for backend in multiple locations
        import os
        backend_locations = [
            Path(__file__).parent.parent.parent / "backend",  # Development: repo root
            Path("/app/backend"),  # Docker container
            Path.cwd() / "backend"  # Current directory
        ]

        backend_path = None
        for loc in backend_locations:
            if loc.exists():
                backend_path = loc
                break

        if not backend_path:
            console.print("❌ [red]Backend not found. Please ensure backend directory exists.[/red]")
            console.print("💡 [dim]Run from mem8 repository root or install with backend support.[/dim]")
            return

        try:
            import subprocess
            import sys

            # Build uvicorn command
            cmd = [
                sys.executable, "-m", "uvicorn",
                "mem8_api.main:app",
                "--host", host,
                "--port", str(port)
            ]

            if reload:
                cmd.append("--reload")

            if workers > 1 and not reload:
                cmd.extend(["--workers", str(workers)])

            if verbose:
                cmd.append("--log-level=debug")
            else:
                cmd.append("--log-level=info")

            # Change to backend/src directory for proper module resolution
            backend_src = backend_path / "src"

            # Set PYTHONPATH to include src directory
            env = os.environ.copy()
            if "PYTHONPATH" in env:
                # Use os.pathsep for cross-platform compatibility (: on Unix, ; on Windows)
                env["PYTHONPATH"] = f"{backend_src}{os.pathsep}{env['PYTHONPATH']}"
            else:
                env["PYTHONPATH"] = str(backend_src)

            console.print(f"📁 [dim]Working directory: {backend_src}[/dim]")
            if verbose:
                console.print(f"⚙️  [dim]Command: {' '.join(cmd)}[/dim]")
                console.print(f"📚 [dim]PYTHONPATH: {env.get('PYTHONPATH')}[/dim]")

            # Run the server
            result = subprocess.run(cmd, cwd=str(backend_src), env=env)

            if result.returncode != 0:
                console.print("❌ [red]Server exited with error[/red]")
                sys.exit(result.returncode)

        except ImportError:
            console.print("❌ [red]FastAPI dependencies not installed.[/red]")
            console.print("💡 Install with: [cyan]pip install 'mem8[api]'[/cyan]")
        except KeyboardInterrupt:
            console.print("\n👋 [yellow]Server shutdown requested[/yellow]")
        except Exception as e:
            console.print(f"❌ [bold red]Error starting server: {e}[/bold red]")
            if verbose:
                console.print_exception()

    @app.command()
    def search(
        query: Annotated[str, typer.Argument(help="Search query")],
        limit: Annotated[int, typer.Option("--limit", help="Maximum number of results")] = 10,
        category: Annotated[Optional[str], typer.Option("--category", "-c", help="Category: plans, research, decisions, shared")] = None,
        method: Annotated[SearchMethod, typer.Option("--method", help="Search method")] = SearchMethod.FULLTEXT,
        path: Annotated[Optional[str], typer.Option("--path", help="Path filter")] = None,
        web: Annotated[bool, typer.Option("--web", help="Open in web UI")] = False,
        verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False
    ):
        """
        Full-text content search with context snippets.

        Use 'search' to find specific text/keywords within file contents.
        Use 'find' to browse/filter memory by type, status, or metadata.

        Examples:
          mem8 search "docker"                    # Search everywhere
          mem8 search "auth" --category plans     # Search only plans
          mem8 search "API" -c research           # Search only research
        """
        import urllib.parse
        import webbrowser

        # Handle web UI search early - no need to initialize app state
        if web and query:
            console.print(f"🌐 [bold blue]Opening search for '{query}' in web UI...[/bold blue]")
            search_url = f'http://localhost:20040?search={urllib.parse.quote(query)}'

            from ...core.smart_setup import launch_web_ui, show_setup_instructions
            if launch_web_ui():
                webbrowser.open(search_url)
                console.print("✅ [green]Search opened in web browser![/green]")
            else:
                console.print("ℹ️  [yellow]Backend not running. Here's how to start it:[/yellow]")
                instructions = show_setup_instructions()
                console.print(instructions)
            return

        # Traditional CLI search - initialize state now
        set_app_state(verbose=verbose)
        state = get_state()
        memory_manager = state.memory_manager

        # Determine content type and path based on category
        content_type = ContentType.ALL
        path_filter = path

        if category:
            content_type = ContentType.MEMORY
            if not path:
                # Map category to path
                category_paths = {
                    'plans': 'memory/shared/plans',
                    'research': 'memory/shared/research',
                    'decisions': 'memory/shared/decisions',
                    'tickets': 'memory/shared/tickets',
                    'prs': 'memory/shared/prs',
                    'shared': 'memory/shared',
                }
                path_filter = category_paths.get(category)

        search_method = f"[cyan]{method.value}[/cyan]"
        category_display = f" in [cyan]{category}[/cyan]" if category else ""
        console.print(f"[bold blue]Searching{category_display} for: '{query}' ({search_method})[/bold blue]")

        if method == SearchMethod.SEMANTIC:
            try:
                import importlib.util
                if importlib.util.find_spec("sentence_transformers") is None:
                    raise ImportError("sentence_transformers not found")
            except ImportError:
                console.print("[yellow]⚠️  Semantic search requires sentence-transformers library[/yellow]")
                console.print("Install with: [dim]pip install 'mem8[semantic]'[/dim]")

        try:
            results = memory_manager.search_content(
                query=query,
                limit=limit,
                content_type=content_type.value,
                search_method=method.value,
                path_filter=path_filter
            )

            if results['matches']:
                # Display results with snippets
                console.print(f"\n[bold cyan]Search Results[/bold cyan] [dim]({len(results['matches'])} found)[/dim]\n")

                for idx, match in enumerate(results['matches'], 1):
                    # Header with match number and title
                    title = match.get('title', match.get('name', 'Untitled'))
                    match_count = match.get('match_count', 0)
                    score = match.get('score', 0)

                    console.print(f"[bold]{idx}. {title}[/bold]")

                    # Path and metadata
                    path_display = str(match.get('path', ''))
                    if len(path_display) > 80:
                        path_display = "..." + path_display[-77:]

                    console.print(f"   [dim]Path:[/dim] {path_display}")
                    console.print(f"   [dim]Type:[/dim] {match.get('type', 'unknown')}  [dim]Matches:[/dim] {match_count}  [dim]Score:[/dim] {score:.1f}")

                    # Snippet if available
                    if 'snippet' in match and match['snippet']:
                        console.print("   [dim]Context:[/dim]")
                        # Indent snippet lines
                        snippet_lines = match['snippet'].split('\n')
                        for line in snippet_lines:
                            if line.startswith('→'):
                                # Highlight the match line
                                console.print(f"   [yellow]{line}[/yellow]")
                            else:
                                console.print(f"   [dim]{line}[/dim]")

                    # Separator between results
                    if idx < len(results['matches']):
                        console.print()

                # Show summary
                console.print(f"\n💡 [dim]Found {len(results['matches'])} of {results['total_found']} total matches. Use --limit to adjust results shown.[/dim]")
                if not web:
                    console.print("💡 [dim]Add --web to open results in web UI for better browsing.[/dim]")

            else:
                console.print(f"🔍 [yellow]No results found for '{query}' in {content_type.value}[/yellow]")
                console.print("💡 [dim]Try:")
                console.print("   • Different search terms")
                console.print("   • --method semantic for meaning-based search")
                console.print("   • --type all to search all content types")

        except Exception as e:
            handle_command_error(e, verbose, "search")

    @app.command()
    def sync(
        direction: Annotated[SyncDirection, typer.Option(
            "--direction", help="Sync direction"
        )] = SyncDirection.BOTH,
        dry_run: Annotated[bool, typer.Option(
            "--dry-run", help="Show what would be synced without making changes"
        )] = False,
        verbose: Annotated[bool, typer.Option(
            "--verbose", "-v", help="Enable verbose output"
        )] = False
    ):
        """Synchronize local and shared memory."""
        set_app_state(verbose=verbose)
        state = get_state()
        sync_manager = state.sync_manager

        action = "Dry run:" if dry_run else "Syncing"
        console.print(f"[bold blue]{action} memory ({direction.value})...[/bold blue]")

        try:
            result = sync_manager.sync_memory(direction=direction.value, dry_run=dry_run)

            if result['success']:
                console.print("✅ [green]Sync completed successfully[/green]")
                if 'stats' in result:
                    stats = result['stats']
                    console.print(f"📊 [dim]Files synced: {stats.get('files_synced', 0)}, "
                                f"Conflicts: {stats.get('conflicts', 0)}[/dim]")
            else:
                console.print("❌ [red]Sync failed[/red]")
                if 'error' in result:
                    console.print(f"Error: {result['error']}")

        except Exception as e:
            handle_command_error(e, verbose, "sync")
