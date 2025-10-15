"""Toolbelt verification and tracking for CLI tools."""

import subprocess
import platform
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Tuple, Optional
import yaml


def parse_toolbelt_file(file_path: Path) -> Tuple[Dict[str, Any], str]:
    """Parse toolbelt file, separating frontmatter from user content.

    Args:
        file_path: Path to tools.md file

    Returns:
        Tuple of (metadata_dict, markdown_content)
    """
    if not file_path.exists():
        return {}, ""

    content = file_path.read_text(encoding='utf-8')

    # Parse YAML frontmatter (same pattern as ThoughtEntity)
    if content.startswith('---'):
        yaml_end = content.find('---', 3)
        if yaml_end != -1:
            yaml_content = content[4:yaml_end]
            try:
                metadata = yaml.safe_load(yaml_content) or {}
            except yaml.YAMLError:
                metadata = {}
            markdown_body = content[yaml_end + 3:].strip()
        else:
            metadata = {}
            markdown_body = content
    else:
        metadata = {}
        markdown_body = content

    return metadata, markdown_body


def check_toolbelt() -> Dict[str, Any]:
    """Check and return toolbelt CLI tools and OS info.

    Returns:
        Dictionary with 'os' and 'tools' keys containing system and tool information.
    """
    # Define toolbelt to check
    toolbelt = {
        'git': {'command': 'git --version', 'parse': lambda x: x.split()[-1] if x else None},
        'gh': {'command': 'gh --version', 'parse': lambda x: x.split('\n')[0].split()[-1] if x else None},
        'docker': {'command': 'docker --version', 'parse': lambda x: x.split()[2].rstrip(',') if x else None},
        'uv': {'command': 'uv --version', 'parse': lambda x: x.split()[-1] if x else None},
        'npm': {'command': 'npm --version', 'parse': lambda x: x.strip() if x else None},
        'python': {'command': 'python --version', 'parse': lambda x: x.split()[-1] if x else None},
        'node': {'command': 'node --version', 'parse': lambda x: x.strip().lstrip('v') if x else None},
        'curl': {'command': 'curl --version', 'parse': lambda x: x.split('\n')[0].split()[1] if x else None},
        'ast-grep': {'command': 'ast-grep --version', 'parse': lambda x: x.strip() if x else None},
    }

    # Collect OS details
    os_info = {
        'system': platform.system(),
        'release': platform.release(),
        'version': platform.version(),
        'machine': platform.machine(),
        'processor': platform.processor() or 'Unknown',
        'python_version': platform.python_version()
    }

    # Check each tool
    verified = {}
    for tool, config in toolbelt.items():
        try:
            result = subprocess.run(
                config['command'].split(),
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                output = result.stdout or result.stderr
                version = config['parse'](output) if output else 'available'
                verified[tool] = version
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            # Tool not available
            pass

    return {
        'generated_at': datetime.now().isoformat(),
        'os': os_info,
        'tools': verified
    }


def save_toolbelt(workspace_dir: Optional[Path] = None) -> Path:
    """Check tools and save to .mem8/tools.md.

    Preserves user-editable markdown content while updating frontmatter.

    Args:
        workspace_dir: Directory to save in (defaults to current directory)

    Returns:
        Path to saved file
    """
    if workspace_dir is None:
        workspace_dir = Path.cwd()

    mem8_dir = workspace_dir / '.mem8'
    mem8_dir.mkdir(exist_ok=True)
    output_file = mem8_dir / 'tools.md'

    # Generate new metadata
    new_metadata = check_toolbelt()

    # Parse existing file to preserve user content
    existing_metadata, user_content = parse_toolbelt_file(output_file)

    # If no user content exists, create default template
    if not user_content:
        user_content = """# Toolbelt

This file contains auto-generated toolbelt verification data (in YAML frontmatter above) and project-specific usage notes below.

## Regeneration

Run `mem8 tools --save` to update the frontmatter with current tool versions. Your notes below will be preserved.

## Project-Specific Tool Usage

### Git Workflow
Add your team's git conventions, branch naming, commit message format, etc.

### GitHub CLI (gh)
Document common gh commands used in your project workflow.

### Docker
Project-specific docker commands, environment setup, common issues.

### UV / Python Package Manager
Package management commands, dependency updates, virtual environment setup.

### Other Tools
Add documentation for any other tools your team uses regularly.

## Team Notes

Add any additional project-specific CLI tips, common commands, and workflows here.
This section is preserved when you run `mem8 tools --save`.
"""

    # Format frontmatter with regeneration instructions
    frontmatter_comments = f"""# Auto-generated by mem8 tools --save
# Last updated: {new_metadata['generated_at']}
# Regenerate with: mem8 tools --save

"""

    # Combine frontmatter + user content
    yaml_content = yaml.dump(new_metadata, default_flow_style=False, sort_keys=False)
    full_content = f"---\n{frontmatter_comments}{yaml_content}---\n\n{user_content}"

    # Write atomically
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(full_content)

    return output_file
