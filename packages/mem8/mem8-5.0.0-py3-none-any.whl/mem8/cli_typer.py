#!/usr/bin/env python3
"""
Typer-based CLI implementation for mem8.
Modern CLI framework with enhanced type safety and developer experience.
"""

import typer
from typing import Annotated, Optional, Dict, Any
from pathlib import Path

from rich.console import Console

from . import __version__
from .core.config import Config
from .core.memory import MemoryManager
from .core.sync import SyncManager
from .core.utils import setup_logging
from .core.intelligent_query import IntelligentQueryEngine
from .core.thought_actions import ThoughtActionEngine
from .core.templates import TemplateManager
from .cli.types import SearchMethod, ContentType, ActionType, SyncDirection, DeployEnvironment

# Create console instance
console = Console(force_terminal=True, legacy_windows=None)

# Create Typer app
typer_app = typer.Typer(
    name="mem8",
    help="Memory management CLI for team collaboration",
    add_completion=False,  # We'll manage this ourselves
    rich_markup_mode="rich"
)





# Enhanced state management with lazy initialization (Phase 2)
class AppState:
    def __init__(self):
        self._config = None
        self._memory_manager = None
        self._sync_manager = None
        self._query_engine = None
        self._action_engine = None
        self._initialized = False

    def initialize(self, verbose: bool = False, config_dir: Optional[Path] = None):
        """Initialize state with parameters. Only initializes once."""
        if self._initialized:
            return  # Already initialized, skip re-initialization

        if verbose:
            setup_logging(True)

        # Initialize components
        self._config = Config(config_dir)
        self._memory_manager = MemoryManager(self._config)
        self._sync_manager = SyncManager(self._config)
        self._query_engine = IntelligentQueryEngine(self._memory_manager.thought_discovery)
        self._action_engine = ThoughtActionEngine(self._config)
        self._initialized = True
    
    @property
    def config(self) -> Config:
        if not self._config:
            self.initialize()
        return self._config
        
    @property
    def memory_manager(self) -> MemoryManager:
        if not self._memory_manager:
            self.initialize()
        return self._memory_manager
        
    @property
    def sync_manager(self) -> SyncManager:
        if not self._sync_manager:
            self.initialize()
        return self._sync_manager
        
    @property
    def query_engine(self) -> IntelligentQueryEngine:
        if not self._query_engine:
            self.initialize()
        return self._query_engine
        
    @property
    def action_engine(self) -> ThoughtActionEngine:
        if not self._action_engine:
            self.initialize()
        return self._action_engine


# Global app state instance
app_state = AppState()


def get_state() -> AppState:
    """Dependency injection helper for accessing app state."""
    return app_state


# Dependency injection helpers
def get_memory_manager() -> MemoryManager:
    """Get memory manager instance."""
    return app_state.memory_manager


def get_query_engine() -> IntelligentQueryEngine:
    """Get query engine instance."""
    return app_state.query_engine


def get_action_engine() -> ThoughtActionEngine:
    """Get action engine instance."""
    return app_state.action_engine


def get_sync_manager() -> SyncManager:
    """Get sync manager instance."""
    return app_state.sync_manager


def get_config() -> Config:
    """Get configuration instance."""
    return app_state.config


def set_app_state(verbose: bool = False, config_dir: Optional[Path] = None):
    """Initialize app state with parameters."""
    app_state.initialize(verbose=verbose, config_dir=config_dir)


def handle_command_error(e: Exception, verbose: bool, context: str = "command") -> None:
    """Standardized error handling for all commands."""
    console.print(f"❌ [bold red]Error during {context}: {e}[/bold red]")
    if verbose:
        console.print_exception()


# ============================================================================
# Simple Commands (Phase 1)
# ============================================================================

def version_callback(value: bool):
    if value:
        console.print(f"mem8 version {__version__}")
        raise typer.Exit()


@typer_app.callback()
def main(
    version: bool = typer.Option(
        None, "--version", "-V", 
        callback=version_callback,
        is_eager=True,
        help="Show version and exit"
    )
):
    """Memory management CLI for team collaboration."""
    pass


@typer_app.command()
def status(
    detailed: Annotated[bool, typer.Option("--detailed", help="Show detailed status information")] = False,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Enable verbose output")] = False
):
    """Show mem8 workspace status."""
    set_app_state(verbose=verbose)

    from rich.table import Table

    console.print("[bold blue]mem8 Workspace Status[/bold blue]\n")

    try:
        # Check installation method
        claude_dir = Path.cwd() / '.claude'
        plugin_marker = claude_dir / '.mem8-plugin'

        has_claude = claude_dir.exists()
        is_plugin = plugin_marker.exists()

        if not is_plugin and has_claude:
            # Check for m8 commands as fallback
            commands_dir = claude_dir / 'commands'
            if commands_dir.exists():
                m8_commands = list(commands_dir.glob('m8-*.md'))
                is_plugin = len(m8_commands) >= 6

        # Create status table
        table = Table()
        table.add_column("Component", style="cyan")
        table.add_column("Status")
        table.add_column("Details", style="dim")

        # Installation method
        if is_plugin:
            table.add_row(
                "Installation",
                "[green]✓ Plugin[/green]",
                "Installed via Claude Code plugins"
            )
        elif has_claude:
            table.add_row(
                "Installation",
                "[yellow]⚠ Unknown[/yellow]",
                "Claude Code detected but not via plugin"
            )
        else:
            table.add_row(
                "Installation",
                "[red]✗ Not installed[/red]",
                "Install mem8 plugin in Claude Code"
            )

        # Memory directory
        memory_dir = Path.cwd() / 'memory'
        if memory_dir.exists():
            subdirs = [d.name for d in memory_dir.iterdir() if d.is_dir()]
            table.add_row(
                "Memory",
                "[green]✓ Configured[/green]",
                f"{len(subdirs)} directories"
            )
        else:
            table.add_row(
                "Memory",
                "[yellow]⚠ Missing[/yellow]",
                "Memory directory not found"
            )

        # Get m8 commands and agents
        m8_commands = []
        m8_agents = []

        if has_claude:
            commands_dir = claude_dir / 'commands'
            if commands_dir.exists():
                m8_commands = sorted([f.stem for f in commands_dir.glob('m8-*.md')])

            agents_dir = claude_dir / 'agents'
            if agents_dir.exists():
                patterns = ['memory-*.md', 'codebase-*.md', 'web-search-*.md']
                agent_files = []
                for pattern in patterns:
                    agent_files.extend(agents_dir.glob(pattern))
                m8_agents = sorted(set([f.stem for f in agent_files]))

        # Commands
        if m8_commands:
            commands_preview = ", ".join(m8_commands[:3])
            if len(m8_commands) > 3:
                commands_preview += f" (+{len(m8_commands) - 3} more)"
            table.add_row(
                "Commands",
                f"[green]{len(m8_commands)} installed[/green]",
                commands_preview
            )
        else:
            table.add_row(
                "Commands",
                "[red]0 installed[/red]",
                "No m8-* commands found"
            )

        # Agents
        if m8_agents:
            agents_preview = ", ".join(m8_agents[:3])
            if len(m8_agents) > 3:
                agents_preview += f" (+{len(m8_agents) - 3} more)"
            table.add_row(
                "Agents",
                f"[green]{len(m8_agents)} installed[/green]",
                agents_preview
            )
        else:
            table.add_row(
                "Agents",
                "[red]0 installed[/red]",
                "No m8 agents found"
            )

        console.print(table)

        # Show detailed command/agent lists if requested
        if detailed and (m8_commands or m8_agents):
            console.print("\n[bold blue]m8 Components:[/bold blue]\n")

            if m8_commands:
                console.print("[cyan]Commands:[/cyan]")
                for cmd in m8_commands:
                    console.print(f"  • /{cmd}")

            if m8_agents:
                console.print("\n[cyan]Agents:[/cyan]")
                for agent in m8_agents:
                    console.print(f"  • {agent}")

        # Show next steps if not installed
        if not is_plugin:
            console.print("\n[yellow]💡 To install mem8:[/yellow]")
            console.print("   1. [bold]/plugin marketplace add killerapp/mem8-plugin[/bold]")
            console.print("   2. [bold]/plugin install mem8@mem8-official[/bold]")
            console.print("   See: https://github.com/killerapp/mem8-plugin\n")

    except Exception as e:
        handle_command_error(e, verbose, "status check")


@typer_app.command()
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
        from .core.config import Config

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
                from .core.toolbelt import save_toolbelt
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




@typer_app.command()
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
        Path(__file__).parent.parent / "backend",  # Development: repo root
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


@typer_app.command()
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

        from .core.smart_setup import launch_web_ui, show_setup_instructions
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


# ============================================================================
# Complex Commands (Phase 2)
# ============================================================================


def _interactive_prompt_for_init(context: Dict[str, Any]) -> Dict[str, Any]:
    """Interactive prompts for init command configuration."""
    import typer
    from .core.config import Config
    from .core.smart_setup import get_git_username
    from .integrations.github import get_consistent_github_context
    
    # Load saved preferences
    config = Config()
    defaults = config.get_workflow_defaults()
    
    # Show project type
    if context['is_claude_code_project']:
        console.print("\nClaude Code project")
    else:
        console.print(f"\n{context['project_type'].title()} project")
    
    # Get consistent GitHub context early
    gh_context = get_consistent_github_context(prefer_authenticated_user=True)

    # Always use GitHub as workflow provider (simplified - no choice)
    interactive_config = {"workflow_provider": "github"}

    # GitHub configuration
    console.print("\n[cyan]GitHub Configuration[/cyan]")

    # Use consistent GitHub context for defaults (prefer active account over saved preferences)
    # Use current directory name as default for repo name instead of saved preference
    # This ensures each project gets a sensible default based on its directory name
    current_dir_name = Path.cwd().name
    github_org = gh_context.get("org") or gh_context.get("username") or defaults.get('github_org') or "your-org"
    # Prioritize: detected repo > current directory name > saved preference
    github_repo = gh_context.get("repo") or current_dir_name

    if gh_context.get("org") and gh_context.get("repo"):
        console.print(f"  Detected: {github_org}/{github_repo}")
    console.print("")

    github_org = typer.prompt("GitHub org/username", default=github_org)
    github_repo = typer.prompt("Repository name", default=github_repo)
    interactive_config.update({
        "github_org": github_org,
        "github_repo": github_repo
    })

    # Template selection
    existing_memory = Path('memory').exists()
    default_template = 'claude-config' if existing_memory else defaults.get('template', 'full')
    template_choices = ["full", "claude-config", "memory-repo", "none"]

    console.print("\n[cyan]Template[/cyan]")
    console.print("  full           - Commands + memory structure")
    console.print("  claude-config  - Commands only")
    console.print("  memory-repo  - Memory structure only")
    console.print("  none           - Skip templates")
    console.print("")
    
    template = typer.prompt("Template", default=default_template)
    while template not in template_choices:
        console.print("[red]Choose: full, claude-config, memory-repo, or none[/red]")
        template = typer.prompt("Template", default=default_template)

    interactive_config["template"] = template if template != "none" else None

    # Username
    default_username = gh_context["username"] or get_git_username() or "user"
    interactive_username = typer.prompt("\nUsername for memory", default=default_username)
    interactive_config["username"] = interactive_username

    # Workflow automation (always GitHub, simplified)
    if template and template != "none":
        automation_choices = ["standard", "none"]
        default_automation = defaults.get('automation_level', 'standard')
        workflow_automation = typer.prompt(
            "Workflow automation (standard/none)",
            default=default_automation
        )
        while workflow_automation not in automation_choices:
            console.print("[red]Choose: standard or none[/red]")
            workflow_automation = typer.prompt("Workflow automation", default="standard")
        interactive_config["workflow_automation"] = workflow_automation
    
    # Skip repo discovery and shared memory - keep it simple
    interactive_config["include_repos"] = False
    interactive_config["shared_enabled"] = False
    
    # Remove web UI launch question - per feedback
    interactive_config["web"] = False
    
    # Save workflow preferences for future use
    # Note: github_repo is intentionally NOT saved as it's project-specific
    if template and template != "none":
        config.save_workflow_preferences(
            template=template,
            workflow_provider=interactive_config.get('workflow_provider', 'github'),
            automation_level=interactive_config.get('workflow_automation', 'standard'),
            github_org=interactive_config.get('github_org')
        )
        console.print("\n[dim]💾 Saved preferences for future init commands[/dim]")
    
    return interactive_config


def _execute_action(action: str, results: list, force: bool, verbose: bool):
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
            import typer
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


def _preview_action(action: str, results: list):
    """Preview what action would do without executing."""
    from rich.table import Table
    
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


# ============================================================================
# Find Subcommands - New Structure
# ============================================================================

# Create find subcommand app
find_app = typer.Typer(
    name="find",
    help="Browse/filter memory by type, status, or metadata. For content search, use 'mem8 search <query>' instead."
)
typer_app.add_typer(find_app, name="find")

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
    from rich.table import Table
    from pathlib import Path
    import re
    
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


# ============================================================================
# Remaining Commands (Phase 3)
# ============================================================================

def _should_skip_confirmation(force: bool, non_interactive: bool, existing_memory: bool, existing_claude: bool, should_install_templates: bool, template_type: str) -> tuple[bool, list[str]]:
    """Determine if we should skip confirmation and what issues exist."""
    needs_confirmation = False
    issues = []

    if existing_memory and not force:
        issues.append("memory/ directory already exists")
        needs_confirmation = True

    if existing_claude and should_install_templates and "claude" in (template_type or "") and not force:
        issues.append(".claude/ directory already exists")
        needs_confirmation = True

    return needs_confirmation, issues


def _handle_init_confirmation(needs_confirmation: bool, issues: list[str], force: bool, non_interactive: bool) -> bool:
    """Handle confirmation logic for init command. Returns True if should proceed."""
    if not needs_confirmation:
        return True

    if force:
        return True

    console.print("\n⚠️  [yellow]Existing directories detected:[/yellow]")
    for issue in issues:
        console.print(f"  • {issue}")

    console.print("\n💡 [cyan]What will happen:[/cyan]")
    console.print("  • Existing directories will be [bold]preserved (not overwritten)[/bold]")
    console.print("  • Only missing components will be created")
    console.print("  • Use [dim]--force[/dim] to overwrite existing directories")

    if non_interactive:
        console.print("\n❌ [red]Cannot proceed in non-interactive mode with existing data[/red]")
        console.print("💡 [dim]Use --force to proceed anyway, or run from a clean directory[/dim]")
        return False

    import typer
    proceed = typer.confirm("\nContinue with setup (will skip existing directories)?")
    if not proceed:
        console.print("❌ [yellow]Setup cancelled[/yellow]")
        return False

    return True


def _validate_init_workspace_location(force: bool, non_interactive: bool = False) -> Path:
    """Validate workspace location for init command only."""
    from .core.utils import get_git_info
    import typer
    
    current_dir = Path.cwd()
    git_info = get_git_info()
    
    # Prefer git repository root when available
    if git_info['is_git_repo']:
        repo_root = git_info['repo_root']
        if repo_root != current_dir:
            # Notify user we're using git root instead of cwd
            typer.secho(
                f"📁 Using git repository root: {repo_root}",
                fg=typer.colors.BLUE
            )
        return repo_root
    
    # If not in a git repository, warn user about non-standard location
    if force:
        typer.secho(f"🔧 Force mode: Using current directory {current_dir}", fg=typer.colors.CYAN)
        return current_dir

    if non_interactive:
        typer.secho(f"⚠️  Non-interactive mode: Using current directory {current_dir} (not a git repository)", fg=typer.colors.YELLOW)
        return current_dir

    typer.secho("⚠️  Warning: Creating .claude directory outside git repository", fg=typer.colors.YELLOW)
    typer.secho(f"Current directory: {current_dir}", fg=typer.colors.WHITE)
    typer.secho("This directory is not part of a git repository.", fg=typer.colors.YELLOW)
    typer.echo()
    typer.secho("Consider running this command from a git repository root.", fg=typer.colors.BLUE)
    typer.echo()

    if not typer.confirm("Continue with current directory anyway?", default=False):
        typer.secho("Cancelled. Please run from an appropriate project root.", fg=typer.colors.RED)
        raise typer.Exit(1)

    return current_dir

@typer_app.command()
def init(
    template: Optional[str] = typer.Option(
        None,
        "--template", "-t",
        help="Force specific template: claude-config, memory-repo, or full (default: auto-detect)",
    ),
    template_source: Annotated[Optional[str], typer.Option(
        "--template-source", help="External template source: local path, git URL, or GitHub shorthand (org/repo)"
    )] = None,
    repos: Annotated[Optional[str], typer.Option(
        "--repos", help="Comma-separated list of repository paths to discover"
    )] = None,
    shared_dir: Annotated[Optional[Path], typer.Option(
        "--shared-dir", help="Path to shared directory for memory"
    )] = None,
    web: Annotated[bool, typer.Option(
        "--web", help="Launch web UI after setup"
    )] = False,
    force: Annotated[bool, typer.Option(
        "--force", help="⚠️  DANGEROUS: Skip all confirmations and overwrite existing directories without backup"
    )] = False,
    non_interactive: Annotated[bool, typer.Option(
        "--non-interactive", help="Non-interactive mode, use auto-detected defaults without prompts"
    )] = False,
    verbose: Annotated[bool, typer.Option(
        "--verbose", "-v", help="Enable verbose output"
    )] = False
):
    """Initialize mem8 workspace with interactive guided setup (default) or auto-detected defaults."""
    from .core.smart_setup import (
        detect_project_context, generate_smart_config, setup_minimal_structure
    )
    
    set_app_state(verbose=verbose)

    console.print("[bold]mem8 init[/bold]")
    
    # INIT-SPECIFIC workspace validation - check git repository before setup
    validated_workspace_dir = _validate_init_workspace_location(force, non_interactive)
    
    try:
        # 1. Auto-detect project context
        if verbose:
            console.print("🔍 [dim]Detecting project configuration...[/dim]")
        context = detect_project_context()
        
        if verbose:
            console.print(f"[dim]Detected: {context['project_type']} project, "
                        f"{len(context['git_repos'])} repositories found[/dim]")
        
        # 2. Interactive mode: gather user preferences (default behavior)
        interactive_config = {}
        if not non_interactive and not force:  # Interactive is now the default
            interactive_config = _interactive_prompt_for_init(context)

            # Override parameters with interactive values where not explicitly set
            template = template or interactive_config.get('template')
            shared_dir = shared_dir or interactive_config.get('shared_dir')
            web = web or interactive_config.get('web', False)
            repos = repos or interactive_config.get('repos')
        elif force:
            template = template or "full"
        elif non_interactive:
            template = template or "full"
        
        # 3. Generate smart configuration with interactive overrides
        context['interactive_config'] = interactive_config
        config = generate_smart_config(context, repos)
        if interactive_config:
            config.update(interactive_config)
        
        # 3. Auto-detect if templates should be installed
        should_install_templates = False
        template_type = template  # Use explicit template if provided
        
        if template and template != "none":
            # User explicitly requested templates
            should_install_templates = True
        elif template == "none":
            # User explicitly doesn't want templates
            should_install_templates = False
        elif context['is_claude_code_project'] and not template:
            # Auto-detect Claude Code projects need templates
            should_install_templates = True
            template_type = "claude-config"  # Default for Claude projects
        
        # 3. Check for existing setup and conflicts
        existing_memory = Path('memory').exists()
        existing_claude = Path('.claude').exists()

        needs_confirmation, issues = _should_skip_confirmation(
            force, non_interactive, existing_memory, existing_claude,
            should_install_templates, template_type
        )

        # Only show repository info in verbose mode or if explicitly requested
        if verbose and config.get('repositories'):
            console.print(f"📁 [dim]Including {len(config['repositories'])} repositories[/dim]")

        if shared_dir:
            config['shared_location'] = shared_dir
            config['shared_enabled'] = True  # Enable shared when --shared-dir is provided

        # 4. Handle confirmations if needed
        if not _handle_init_confirmation(needs_confirmation, issues, force, non_interactive):
            return
        
        # 5. Create directory structure
        setup_result = setup_minimal_structure(config)

        # 6. Install templates if needed
        if should_install_templates and template_type != "none":
            template_name = template_type or "full"
            console.print(f"\nInstalling {template_name} template...")
            template_manager = TemplateManager()
            template_manager.install_templates(
                template_name,
                validated_workspace_dir,
                force,
                verbose,
                interactive_config,
                template_source,
                console
            )
        
        if setup_result['errors']:
            console.print("[red]Errors:[/red]")
            for error in setup_result['errors']:
                console.print(f"  {error}")
            return

        # Show what was created (only if verbose or something actually created)
        if verbose and setup_result['created']:
            console.print("\nCreated:")
            for created in setup_result['created']:
                console.print(f"  {created}")

        # Create ~/.mem8 shortcut
        from .core.config import Config
        config_manager = Config()
        config_manager.create_home_shortcut()

        # Save toolbelt
        try:
            from .core.toolbelt import save_toolbelt
            output_file = save_toolbelt()
            if verbose:
                console.print(f"[dim]Saved toolbelt to {output_file}[/dim]")
        except Exception:
            pass  # Non-critical, don't fail on this

        # Done
        console.print("\n[green]✓[/green] Setup complete")
        console.print("  mem8 status  - verify setup")
        console.print("  mem8 search  - find memory")
        
    except Exception as e:
        handle_command_error(e, verbose, "setup")


@typer_app.command()
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


# ============================================================================
# Command Groups (Team and Deploy)
# ============================================================================

# Create team subapp
team_app = typer.Typer(name="team", help="Experimental team collaboration commands")
typer_app.add_typer(team_app, name="team")

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


# Create deploy subapp
deploy_app = typer.Typer(name="deploy", help="Experimental deployment commands")
typer_app.add_typer(deploy_app, name="deploy")

@deploy_app.command()
def kubernetes(
    env: Annotated[DeployEnvironment, typer.Option(
        "--env", help="Deployment environment"
    )] = DeployEnvironment.LOCAL,
    domain: Annotated[Optional[str], typer.Option("--domain", help="Custom domain for deployment")] = None,
    replicas: Annotated[int, typer.Option("--replicas", help="Number of replicas")] = 2,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Enable verbose output")] = False
):
    """Deploy to Kubernetes cluster (experimental)."""
    set_app_state(verbose=verbose)
    
    console.print(f"[bold blue]Deploying to Kubernetes ({env.value})...[/bold blue]")
    if domain:
        console.print(f"Domain: {domain}")
    console.print(f"Replicas: {replicas}")
    
    console.print("[yellow]⚠️  Kubernetes deployment requires backend API (Phase 2)[/yellow]")
    console.print("Available after backend API and frontend are implemented.")


@deploy_app.command()
def local(
    port: Annotated[int, typer.Option("--port", help="Port to run on")] = 8000,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Enable verbose output")] = False
):
    """Start local development server (experimental)."""
    set_app_state(verbose=verbose)
    
    console.print(f"[bold blue]Starting local server on port {port}...[/bold blue]")
    console.print("[yellow]⚠️  Local server requires backend API (Phase 2)[/yellow]")


# ============================================================================
# Worktree Management Commands
# ============================================================================

# Create worktree subcommand app
worktree_app = typer.Typer(name="worktree", help="Git worktree management for development workflows")
typer_app.add_typer(worktree_app, name="worktree")

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
    from .core.worktree import create_worktree
    
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
    from .core.worktree import list_worktrees
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
    from .core.worktree import remove_worktree
    
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


# ============================================================================
# Metadata Management Commands  
# ============================================================================

# Create metadata subcommand app
metadata_app = typer.Typer(name="metadata", help="Repository metadata management and research tools")
typer_app.add_typer(metadata_app, name="metadata")

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
    from .core.metadata import get_git_metadata
    
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
    from .core.metadata import generate_research_metadata, format_frontmatter
    
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
    from .core.metadata import generate_project_metadata
    
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


# ============================================================================
# Shell Completion (Using Typer's built-in system)
# ============================================================================

# Enable Typer's built-in completion
typer_app.add_completion = True
# ============================================================================
# Template Management Commands
# ============================================================================

# Create templates subcommand app
templates_app = typer.Typer(name="templates", help="Template source management and inspection")
typer_app.add_typer(templates_app, name="templates")

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
    from .core.template_source import create_template_source
    from .core.config import Config
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
    from .core.template_source import create_template_source
    from .core.config import Config

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
    from .core.config import Config

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


# Lightweight GitHub CLI helpers
gh_app = typer.Typer(name="gh", help="GitHub CLI integration helpers")
typer_app.add_typer(gh_app, name="gh")


@gh_app.command("whoami")
def gh_whoami(
    host: Annotated[str, typer.Option("--host", help="GitHub host",)] = "github.com",
):
    """Show active GitHub CLI login and current repository context."""
    set_app_state()
    from .integrations.github import get_consistent_github_context

    gh_context = get_consistent_github_context()

    if gh_context["username"]:
        console.print(f"Logged in to {host} as [bold]{gh_context['username']}[/bold]")

        if gh_context["org"] and gh_context["repo"]:
            console.print(f"Current repository: [bold]{gh_context['org']}/{gh_context['repo']}[/bold]")

            if gh_context["auth_user"] != gh_context["repo_owner"]:
                console.print(f"[dim]Note: You're authenticated as {gh_context['auth_user']} but this repo is owned by {gh_context['repo_owner']}[/dim]")
        else:
            console.print("[dim]No repository detected in current directory[/dim]")
    else:
        console.print("[yellow]gh not detected or no active login for this host[/yellow]")


@typer_app.command()
def tools(
    save: Annotated[bool, typer.Option("--save", help="Save toolbelt to .mem8/tools.md")] = False,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Enable verbose output")] = False
):
    """List toolbelt CLI tools and OS details for AI system prompts."""
    from .core.toolbelt import check_toolbelt, save_toolbelt as save_tools_to_file
    from rich.table import Table

    set_app_state(verbose=verbose)

    # Check tools
    output_data = check_toolbelt()
    os_info = output_data['os']
    verified = output_data['tools']

    # Display to user
    console.print("[bold blue]System Environment[/bold blue]")
    console.print(f"OS: {os_info['system']} {os_info['release']} ({os_info['machine']})")
    console.print(f"Python: {os_info['python_version']}")

    console.print("\n[bold blue]Verified Tools[/bold blue]")
    if verified:
        table = Table()
        table.add_column("Tool", style="cyan")
        table.add_column("Version", style="green")

        for tool, version in sorted(verified.items()):
            table.add_row(tool, version)
        console.print(table)
    else:
        console.print("[yellow]No tools verified[/yellow]")

    # Save if requested
    if save:
        output_file = save_tools_to_file()
        console.print(f"\n✅ [green]Saved to {output_file}[/green]")
    else:
        console.print("\n💡 [dim]Use --save to write to .mem8/tools.md[/dim]")


@typer_app.command()
def ports(
    lease: Annotated[bool, typer.Option("--lease", help="Lease new ports for this project")] = False,
    start: Annotated[Optional[int], typer.Option("--start", help="Starting port number (auto-assign if not specified)")] = None,
    count: Annotated[int, typer.Option("--count", help="Number of ports to lease")] = 5,
    release: Annotated[bool, typer.Option("--release", help="Release this project's port lease")] = False,
    list_all: Annotated[bool, typer.Option("--list-all", help="List all port leases across all projects")] = False,
    check_conflicts: Annotated[bool, typer.Option("--check-conflicts", help="Check for port conflicts")] = False,
    kill: Annotated[Optional[int], typer.Option("--kill", help="Kill process using specified port")] = None,
    force: Annotated[bool, typer.Option("--force", help="Force kill port outside project range")] = False,
    show: Annotated[bool, typer.Option("--show", help="Show current project's port assignments")] = True,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Enable verbose output")] = False
):
    """Manage project port assignments to prevent conflicts across projects."""
    from .core.ports import PortManager, save_ports_file

    set_app_state(verbose=verbose)

    manager = PortManager()

    # Kill port process
    if kill:
        console.print(f"[yellow]Attempting to kill process on port {kill}...[/yellow]")
        success, message = manager.kill_port(kill, force=force)
        if success:
            console.print(f"[green]✓ {message}[/green]")
        else:
            console.print(f"[red]✗ {message}[/red]")
            if not force and "outside project's range" in message:
                console.print("[dim]Use --force to kill ports outside your range[/dim]")
        return

    # Release lease
    if release:
        if manager.release_lease():
            console.print("[green]✓ Port lease released[/green]")
            # Remove ports.md
            ports_file = Path.cwd() / ".mem8" / "ports.md"
            if ports_file.exists():
                ports_file.unlink()
                console.print(f"[dim]Removed {ports_file}[/dim]")
        else:
            console.print("[yellow]No active lease for this project[/yellow]")
        return

    # Check conflicts
    if check_conflicts:
        conflicts = manager.check_conflicts()
        if conflicts:
            console.print(f"[red]Found {len(conflicts)} port conflicts:[/red]")
            for conflict in conflicts:
                console.print(f"  Port {conflict['port']}: {conflict['project1']} ⚠️  {conflict['project2']}")
        else:
            console.print("[green]✓ No port conflicts detected[/green]")
        return

    # List all leases
    if list_all:
        leases = manager.list_all_leases()
        if not leases:
            console.print("[yellow]No port leases found[/yellow]")
            return

        console.print(f"\n[bold]Global Port Leases[/bold] ({len(leases)} projects)\n")

        for project_path, lease in leases.items():
            console.print(f"[cyan]{lease['project_name']}[/cyan]")
            console.print(f"  Path: {project_path}")
            console.print(f"  Ports: {lease['port_range']}")
            console.print(f"  Leased: {lease['leased_at']}\n")

        console.print(f"[dim]Registry: {manager.registry_file}[/dim]")
        return

    # Lease new ports
    if lease:
        try:
            lease_info = manager.lease_ports(start=start, count=count)
            console.print(f"[green]✓ Leased ports {lease_info['port_range']}[/green]")
            console.print(f"[dim]{lease_info['port_count']} ports available for your services[/dim]")

            # Save ports.md
            output_file = save_ports_file(lease_info)
            console.print(f"[dim]Created {output_file}[/dim]")

        except ValueError as e:
            console.print(f"[red]Error: {e}[/red]")
            return

    # Show current lease (default)
    elif show:
        lease_info = manager.get_lease()
        if not lease_info:
            console.print("[yellow]No port lease for this project[/yellow]")
            console.print("\n[dim]Lease ports with:[/dim] mem8 ports --lease")
            console.print("[dim]Or specify a range:[/dim] mem8 ports --lease --start 20000 --count 5")
            return

        console.print(f"\n[bold]{lease_info['project_name']}[/bold]")
        console.print(f"Port Range: [cyan]{lease_info['port_range']}[/cyan]")
        console.print(f"Port Count: {lease_info['port_count']}")
        console.print(f"Leased: {lease_info['leased_at']}\n")

        console.print("[dim]Config file:[/dim] .mem8/ports.md")
        console.print("[dim]Global registry:[/dim] ~/.mem8/port_leases.yaml")
        console.print(f"\n[dim]Use any port in range {lease_info['port_range']} for your services[/dim]")
