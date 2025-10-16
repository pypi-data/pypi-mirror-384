"""Claude Code integration functionality for mem8."""

from pathlib import Path
from typing import Dict, Any


def generate_claude_memory_integration(config: Dict[str, Any]) -> str:
    """Generate CLAUDE.md content for mem8 integration."""
    repos_config = ""
    if config.get('repositories'):
        repos_config = "\n".join([
            f"- {repo['name']}: {repo.get('memory_paths', ['No memory found'])[0] if repo.get('memory_paths') else 'No memory found'}" 
            for repo in config.get('repositories', [])
        ])
    else:
        repos_config = "- No repositories discovered (run mem8 quick-start to discover)"
    
    claude_md_content = f"""
# AI Memory Integration

This project uses mem8 for memory management across repositories.

## Available Repositories
{repos_config}

## Memory Commands
- `/setup-memory` - Configure AI memory for this project
- `/browse-memories` - Search and explore memory across repositories
- `mem8 search "query"` - Full-text search across all memories
- `mem8 init` - Initialize mem8 workspace with templates

## Shared Memory Location
Shared memory: `{config.get('shared_location', 'memory/shared/')}`

## Workflow Integration  
- Research documents: `memory/shared/research/`
- Implementation plans: `memory/shared/plans/` 
- PR discussions: `memory/shared/prs/`
- User notes: `memory/{config.get('username', 'user')}/`

## Quick Start
Run `mem8 init` to set up your mem8 workspace with Claude Code templates.
"""
    return claude_md_content


def update_claude_md_integration(config: Dict[str, Any]) -> bool:
    """Add mem8 integration section to existing CLAUDE.md."""
    claude_md_path = Path('.claude/CLAUDE.md')
    project_claude_md = Path('CLAUDE.md')
    
    # Try both locations
    target_file = None
    if claude_md_path.exists():
        target_file = claude_md_path
    elif project_claude_md.exists():
        target_file = project_claude_md
    
    if target_file:
        try:
            content = target_file.read_text(encoding='utf-8')
            if 'AI Memory Integration' not in content:
                integration = generate_claude_memory_integration(config)
                content += f"\n{integration}"
                target_file.write_text(content, encoding='utf-8')
                return True
        except (OSError, UnicodeDecodeError):
            return False
    
    return False


def create_minimal_claude_md(config: Dict[str, Any]) -> bool:
    """Create a minimal CLAUDE.md file with mem8 integration."""
    claude_md = Path('CLAUDE.md')
    
    if not claude_md.exists():
        integration = generate_claude_memory_integration(config)
        minimal_content = f"""# Project Memory

This project uses mem8 for intelligent memory management and team collaboration.
{integration}
"""
        try:
            claude_md.write_text(minimal_content, encoding='utf-8')
            return True
        except OSError:
            return False
    
    return False


def setup_claude_code_integration(config: Dict[str, Any]) -> Dict[str, Any]:
    """Set up Claude Code integration for mem8."""
    results = {'updated': [], 'created': [], 'errors': []}
    
    # Try to update existing CLAUDE.md
    if update_claude_md_integration(config):
        if Path('.claude/CLAUDE.md').exists():
            results['updated'].append('.claude/CLAUDE.md')
        elif Path('CLAUDE.md').exists():
            results['updated'].append('CLAUDE.md')
    
    # If no CLAUDE.md exists and this isn't a Claude Code project, create one
    elif not Path('.claude').exists() and create_minimal_claude_md(config):
        results['created'].append('CLAUDE.md')
    
    return results