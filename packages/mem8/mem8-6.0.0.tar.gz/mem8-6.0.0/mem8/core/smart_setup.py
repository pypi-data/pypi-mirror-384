"""Smart setup functionality for mem8 quick-start workflow."""

import os
import subprocess
import webbrowser
from pathlib import Path
from typing import Dict, Any, List, Optional
import requests

from .utils import (
    get_git_info,
    get_shared_directory,
    create_symlink_with_info,
    ensure_directory_exists,
    detect_gh_active_login,
)


def detect_project_context() -> Dict[str, Any]:
    """Detect project type, git repos, and optimal configuration."""
    git_info = get_git_info()
    
    # Simplify repository discovery - only count them, don't enumerate all
    repos = discover_local_repositories()
    
    context = {
        'is_claude_code_project': Path('.claude').exists(),
        'git_repos': repos[:5] if repos else [],  # Limit to first 5 for performance
        'repos_from_parent': len(repos) if repos else 0,  # Just count for display
        'project_type': infer_project_type(),
        'username': get_git_username(),
        'shared_location': find_optimal_shared_location(),
        'git_info': git_info,
        'current_dir': Path.cwd(),
        'parent_dir': Path.cwd().parent,
    }
    return context


def discover_local_repositories() -> List[Dict[str, Any]]:
    """Find git repositories - optionally in parent directories.
    
    Only searches if explicitly requested or if in a standard layout.
    """
    current_dir = Path.cwd()
    parent_dir = current_dir.parent
    
    repos = []
    
    # Only search parent if we're likely in a projects-style layout
    # Check if parent has multiple directories that look like projects
    try:
        sibling_dirs = [d for d in parent_dir.iterdir() if d.is_dir() and not d.name.startswith('.')]
        # Only search if there are multiple sibling directories (suggesting a projects folder)
        if len(sibling_dirs) > 3:
            # Search current directory first
            repos.extend(find_git_repos(current_dir, max_depth=0))
            # Then search siblings, but only 1 level deep
            repos.extend(find_git_repos(parent_dir, max_depth=1))
    except (PermissionError, OSError):
        # If we can't read parent, just check current
        repos.extend(find_git_repos(current_dir, max_depth=0))
    
    return repos


def find_git_repos(base_path: Path, max_depth: int = 1) -> List[Dict[str, Any]]:
    """Find git repositories in a directory tree."""
    repos = []
    
    def _scan_directory(path: Path, current_depth: int = 0):
        if current_depth > max_depth:
            return
            
        try:
            # Check if this directory is a git repository
            if (path / '.git').exists():
                repo_info = analyze_git_repository(path)
                if repo_info:
                    repos.append(repo_info)
                return  # Don't scan inside git repos
            
            # Scan subdirectories if we haven't reached max depth
            if current_depth < max_depth:
                for subdir in path.iterdir():
                    if subdir.is_dir() and not subdir.name.startswith('.'):
                        _scan_directory(subdir, current_depth + 1)
                        
        except (PermissionError, OSError):
            # Skip directories we can't read
            pass
    
    _scan_directory(base_path)
    return repos


def analyze_git_repository(repo_path: Path) -> Optional[Dict[str, Any]]:
    """Analyze a git repository for mem8 relevant information."""
    try:
        # Get basic git info
        result = subprocess.run(
            ['git', 'rev-parse', '--show-toplevel'],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        
        repo_root = Path(result.stdout.strip())
        repo_name = repo_root.name
        
        # Get remote URL if available
        try:
            remote_result = subprocess.run(
                ['git', 'config', '--get', 'remote.origin.url'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            remote_url = remote_result.stdout.strip()
        except subprocess.CalledProcessError:
            remote_url = None
        
        # Check for memory directories
        memory_paths = []
        candidate_paths = [
            repo_root / 'memory',
            repo_root / 'docs' / 'memory'
        ]

        for candidate in candidate_paths:
            if candidate.exists() and candidate.is_dir():
                memory_paths.append(str(candidate))
        
        # Check if it's an mem8 project
        is_ai_mem_project = (repo_root / 'ai_mem').exists() or repo_name == 'mem8'
        
        # Check if it's a Claude Code project
        is_claude_project = (repo_root / '.claude').exists()
        
        return {
            'name': repo_name,
            'path': str(repo_root),
            'remote_url': remote_url,
            'memory_paths': memory_paths,
            'is_ai_mem_project': is_ai_mem_project,
            'is_claude_project': is_claude_project,
            'has_memory': len(memory_paths) > 0,
        }
        
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def infer_project_type() -> str:
    """Infer the type of project based on files present."""
    cwd = Path.cwd()
    
    # Check for common project indicators
    if (cwd / 'package.json').exists():
        return 'nodejs'
    elif (cwd / 'pyproject.toml').exists() or (cwd / 'setup.py').exists():
        return 'python'
    elif (cwd / 'Cargo.toml').exists():
        return 'rust'
    elif (cwd / 'go.mod').exists():
        return 'go'
    elif (cwd / '.claude').exists():
        return 'claude-code'
    elif (cwd / 'memory').exists():
        return 'mem8'
    else:
        return 'general'


def get_git_username() -> str:
    """Determine a sensible username for mem8.

    Preference order:
    1) MEM8_USERNAME env
    2) gh CLI active login (github.com)
    3) git config user.name
    4) OS user (USER/USERNAME)
    """
    # 1) explicit env override
    env_name = os.environ.get('MEM8_USERNAME')
    if env_name:
        return env_name

    # 2) gh CLI active login
    gh_login = detect_gh_active_login('github.com')
    if gh_login:
        return gh_login

    # 3) git config user.name
    try:
        result = subprocess.run(
            ['git', 'config', 'user.name'],
            capture_output=True,
            text=True,
            check=True
        )
        name = result.stdout.strip()
        if name:
            return name
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    # 4) OS user
    return os.environ.get('USER', os.environ.get('USERNAME', 'user'))


def find_optimal_shared_location() -> Path:
    """Find the optimal shared directory location."""
    # Start with the default from utilities
    shared_dir = get_shared_directory()
    
    # Check if user has a preferred location in environment
    if os.environ.get('MEM8_SHARED_DIR'):
        env_shared = Path(os.environ['MEM8_SHARED_DIR'])
        if env_shared.exists() or can_create_directory(env_shared):
            return env_shared
    
    # Otherwise use the default home-based location
    return shared_dir


def can_create_directory(path: Path) -> bool:
    """Check if we can create a directory at the given path."""
    try:
        parent = path.parent
        if not parent.exists():
            return False
        return os.access(parent, os.W_OK)
    except (OSError, PermissionError):
        return False


def generate_smart_config(context: Dict[str, Any], repos_arg: Optional[str] = None) -> Dict[str, Any]:
    """Generate configuration based on detected context."""
    repos = context.get('git_repos', [])
    
    # If repos were specified via command line, filter to those
    if repos_arg:
        repo_names = [name.strip() for name in repos_arg.split(',')]
        repos = [repo for repo in repos if repo['name'] in repo_names or repo['path'] in repo_names]
    # Only include repos if explicitly requested in interactive mode
    elif not context.get('interactive_config', {}).get('include_repos'):
        repos = []
    
    config = {
        'username': context['username'],
        # Do not enable shared by default; path is available but unused unless enabled
        'shared_location': context['shared_location'],
        'shared_enabled': False,
        'project_type': context['project_type'],
        'is_claude_project': context['is_claude_code_project'],
        'repositories': repos,
        'current_repo': context.get('git_info', {}).get('repo_root'),
    }
    
    return config


def setup_minimal_structure(config: Dict[str, Any]) -> Dict[str, Any]:
    """Create minimal mem8 structure with flat memory directory."""
    results = {'created': [], 'linked': [], 'errors': []}

    # Check if memory directory exists as git submodule
    memory_dir = Path('memory')
    gitmodules_file = Path('.gitmodules')

    # If memory is already a submodule, don't create structure
    if gitmodules_file.exists():
        gitmodules_content = gitmodules_file.read_text()
        if 'path = memory' in gitmodules_content:
            results['linked'].append('memory/ (git submodule already configured)')
            return results

    # Create memory directory if it doesn't exist
    if not memory_dir.exists():
        if ensure_directory_exists(memory_dir):
            results['created'].append(str(memory_dir))
        else:
            results['errors'].append(f"Failed to create {memory_dir}")
            return results

    # Create flat structure - no shared/ or username subdirectories
    # Memory is now all at root level: plans/, research/, prs/
    subdirs = ['plans', 'research', 'prs']
    for subdir_name in subdirs:
        subdir = memory_dir / subdir_name
        if not subdir.exists():
            if ensure_directory_exists(subdir):
                results['created'].append(str(subdir))
            else:
                results['errors'].append(f"Failed to create {subdir}")

    # Create README if missing
    readme = memory_dir / 'README.md'
    if not readme.exists():
        readme.write_text(
            "# Memory\n\nOrganizational memory for development context and knowledge.\n\n"
            "- `plans/` - Implementation plans and architecture\n"
            "- `research/` - Research notes and analysis\n"
            "- `prs/` - Pull request descriptions\n",
            encoding='utf-8'
        )
        results['created'].append(str(readme))

    return results


def create_shared_link(link_path: Path, target_path: Path) -> tuple[bool, str]:
    """Create shared directory link with fallback options.

    Returns:
        (success, link_type) where link_type describes what was created
    """
    # Try symlink/junction first
    success, link_type = create_symlink_with_info(target_path, link_path)
    if success:
        return True, link_type

    # If symlink fails, create the directory locally as fallback
    if ensure_directory_exists(link_path):
        return True, "directory"

    return False, "failed"


def launch_web_ui() -> bool:
    """Launch web UI if backend is running, otherwise provide instructions."""
    try:
        # Check if backend is running
        response = requests.get('http://localhost:8000/api/v1/health', timeout=2)
        if response.status_code == 200:
            webbrowser.open('http://localhost:20040')
            return True
        else:
            return False
    except requests.RequestException:
        return False


def show_setup_instructions():
    """Show instructions for setting up backend."""
    instructions = """
🚀 To launch the mem8 web interface:

1. Start the backend:
   cd backend && uv run uvicorn mem8_api.main:app --reload --host 127.0.0.1 --port 8000

2. Start the frontend:
   cd frontend && npm run dev -- --port 20040

3. Open your browser to: http://localhost:20040

Or use Docker:
   docker-compose up -d
"""
    return instructions
