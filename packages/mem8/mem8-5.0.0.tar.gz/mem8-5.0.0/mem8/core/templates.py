#!/usr/bin/env python3
"""
Template management for mem8 workspaces.
"""

from pathlib import Path
from typing import Dict, Optional, Any


class TemplateManager:
    """Centralized template installation and management."""

    def __init__(self):
        self._template_base = None

    def install_templates(
        self,
        template_type: str,
        workspace_dir: Path,
        force: bool,
        verbose: bool,
        interactive_config: Dict[str, Any] = None,
        template_source: Optional[str] = None,
        console = None
    ) -> None:
        """Install cookiecutter templates to the workspace."""
        from cookiecutter.main import cookiecutter
        from .config import Config
        from .template_source import create_template_source

        # Get template source (external or builtin)
        if template_source is None:
            # Check for configured default source
            config = Config()
            template_source = config.get('templates.default_source')

        # Create and resolve template source
        source = create_template_source(template_source)

        try:
            template_base = source.resolve()

            # Map template types to directories
            template_map = {
                "full": ["claude-dot-md-template", "shared-memory-template"],
                "claude-config": ["claude-dot-md-template"],
                "memory-repo": ["shared-memory-template"],
            }

            if template_type not in template_map:
                if console:
                    console.print(f"[red]Invalid template: {template_type}[/red]")
                return

            # Run cookiecutter for each template
            for template_name in template_map[template_type]:
                # Use template source to resolve path
                try:
                    template_path = source.get_template_path(template_name)
                except ValueError as e:
                    if verbose and console:
                        console.print(f"[yellow]Template not found in source: {template_name}[/yellow]")
                        console.print(f"[dim]Error: {e}[/dim]")
                    # Try fallback for builtin templates
                    template_path = template_base / template_name
                    if not template_path.exists():
                        if console:
                            console.print(f"[red]Template not available: {template_name}[/red]")
                        continue

                # Check if target already exists
                target_dir = ".claude" if "claude" in template_name else "memory"

                # Check if target exists and handle overwrite confirmation
                should_overwrite = force
                if (workspace_dir / target_dir).exists() and not force:
                    if "claude" in template_name and console:
                        analysis = self.analyze_claude_template(workspace_dir)
                        console.print(f"\n.claude/ exists ({len(analysis['existing_commands'])} commands, {len(analysis['existing_agents'])} agents)")

                        import typer
                        if typer.confirm("Overwrite with mem8 templates?", default=False):
                            should_overwrite = True

                            # Log what will be overwritten
                            existing_items = analysis['existing_commands'] + analysis['existing_agents']
                            if existing_items:
                                console.print(f"  [dim]Will overwrite: {', '.join(existing_items[:5])}")
                                if len(existing_items) > 5:
                                    console.print(f"  [dim]... and {len(existing_items) - 5} more[/dim]")
                        else:
                            console.print("Skipped")
                            continue
                    else:
                        if console:
                            console.print(f"Skipping {target_dir}/ (already exists)")
                        continue

                try:
                    # Build extra_context from interactive configuration
                    extra_context = {}
                    if "claude" in template_name:
                        extra_context = {"project_slug": ".claude"}

                        # Apply interactive configuration to claude templates
                        if interactive_config:
                            if "workflow_provider" in interactive_config:
                                extra_context["workflow_provider"] = interactive_config["workflow_provider"]
                            if "github_org" in interactive_config:
                                extra_context["github_org"] = interactive_config["github_org"]
                            if "github_repo" in interactive_config:
                                extra_context["github_repo"] = interactive_config["github_repo"]
                            if "workflow_automation" in interactive_config:
                                extra_context["include_workflow_automation"] = interactive_config["workflow_automation"]
                            if "username" in interactive_config:
                                extra_context["username"] = interactive_config["username"]
                            if "shared_enabled" in interactive_config:
                                extra_context["shared_enabled"] = interactive_config["shared_enabled"]

                    # Use no_input mode when NOT in interactive mode
                    # When interactive_config is None, we're in regular mode, so no_input=True
                    # When interactive_config is provided, we already have all values, so no_input=True
                    no_input = True

                    cookiecutter(
                        str(template_path),
                        no_input=no_input,
                        output_dir=str(workspace_dir),
                        overwrite_if_exists=should_overwrite,
                        extra_context=extra_context
                    )

                    # Show installation result
                    if console:
                        if "claude" in template_name:
                            analysis = self.analyze_claude_template(workspace_dir)
                            console.print(f"  {len(analysis['template_commands'])} commands, {len(analysis['template_agents'])} agents installed")
                        elif "memory" in template_name:
                            console.print("  memory/ structure created")
                except Exception as e:
                    # Always show installation errors, not just in verbose mode
                    if console:
                        console.print(f"[red]❌ Failed to install {template_name}:[/red] {e}")
                    if verbose and console:
                        import traceback
                        console.print(f"[dim]{traceback.format_exc()}[/dim]")

        # Cleanup source if it was a temp directory
        finally:
            source.cleanup()

    def analyze_claude_template(self, workspace_dir: Path) -> Dict[str, Any]:
        """Analyze existing Claude integration and what will be installed."""
        analysis = {
            'existing_commands': [],
            'existing_agents': [],
            'new_commands': [],
            'new_agents': [],
            'conflicts': [],
            'total_existing': 0,
            'total_new': 0
        }

        # Check existing Claude setup
        claude_dir = workspace_dir / '.claude'
        if claude_dir.exists():
            # Count existing commands
            commands_dir = claude_dir / 'commands'
            if commands_dir.exists():
                analysis['existing_commands'] = [f.stem for f in commands_dir.glob('*.md')]

            # Count existing agents
            agents_dir = claude_dir / 'agents'
            if agents_dir.exists():
                analysis['existing_agents'] = [f.stem for f in agents_dir.glob('*.md')]

            analysis['total_existing'] = len(analysis['existing_commands']) + len(analysis['existing_agents'])

        # List of commands/agents that mem8 templates will install
        # These are based on the claude-dot-md-template
        analysis['template_commands'] = [
            'browse-memories', 'commit', 'create_plan', 'create_worktree',
            'debug', 'describe_pr', 'founder_mode', 'github_issues',
            'implement_plan', 'local_review', 'repo_setup', 'research_codebase',
            'setup-memory', 'validate_plan', 'workflow_automation'
        ]

        analysis['template_agents'] = [
            'codebase-analyzer', 'codebase-locator', 'codebase-pattern-finder',
            'github-workflow-agent', 'memory-analyzer', 'memory-locator',
            'web-search-researcher'
        ]

        # Determine what's new vs conflicts
        for cmd in analysis['template_commands']:
            if cmd in analysis['existing_commands']:
                analysis['conflicts'].append(f"command: {cmd}")
            else:
                analysis['new_commands'].append(cmd)

        for agent in analysis['template_agents']:
            if agent in analysis['existing_agents']:
                analysis['conflicts'].append(f"agent: {agent}")
            else:
                analysis['new_agents'].append(agent)

        analysis['total_new'] = len(analysis['new_commands']) + len(analysis['new_agents'])

        return analysis
