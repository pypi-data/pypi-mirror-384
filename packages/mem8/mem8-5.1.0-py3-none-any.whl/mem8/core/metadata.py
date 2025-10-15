"""Metadata generation for memory and research documents."""

import datetime
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

def get_git_metadata() -> Dict[str, Any]:
    """Get current git repository metadata."""
    from .utils import get_git_info
    
    git_info = get_git_info()
    
    if not git_info['is_git_repo']:
        raise ValueError("Not in a git repository")
    
    # Get current commit hash
    commit_result = subprocess.run(
        ["git", "rev-parse", "HEAD"], 
        capture_output=True, text=True
    )
    
    # Get commit timestamp
    timestamp_result = subprocess.run(
        ["git", "log", "-1", "--format=%ci"],
        capture_output=True, text=True
    )
    
    return {
        "git_commit": commit_result.stdout.strip() if commit_result.returncode == 0 else "unknown",
        "branch": git_info['current_branch'],
        "repository": git_info['repo_root'].name,
        "repo_path": str(git_info['repo_root']),
        "is_clean": _check_git_status(),
        "last_commit_date": timestamp_result.stdout.strip() if timestamp_result.returncode == 0 else None
    }


def generate_research_metadata(topic: str, researcher: Optional[str] = None) -> Dict[str, Any]:
    """Generate complete metadata for research documents."""
    git_metadata = get_git_metadata()
    current_time = datetime.datetime.now().astimezone()
    
    # Get researcher name from git config or use provided name
    if not researcher:
        name_result = subprocess.run(
            ["git", "config", "user.name"], 
            capture_output=True, text=True
        )
        researcher = name_result.stdout.strip() if name_result.returncode == 0 else "unknown"
    
    return {
        "date": current_time.isoformat(),
        "researcher": researcher,
        "git_commit": git_metadata["git_commit"],
        "branch": git_metadata["branch"],
        "repository": git_metadata["repository"],
        "topic": topic,
        "tags": ["research", "codebase"],
        "status": "draft",
        "last_updated": current_time.strftime("%Y-%m-%d"),
        "last_updated_by": researcher
    }


def generate_project_metadata() -> Dict[str, Any]:
    """Generate metadata about the current project context."""
    git_metadata = get_git_metadata()
    current_time = datetime.datetime.now().astimezone()
    
    # Detect project type based on files
    project_type = _detect_project_type()
    
    # Get repository statistics
    stats = _get_repository_stats()
    
    return {
        "timestamp": current_time.isoformat(),
        "project_type": project_type,
        "git_metadata": git_metadata,
        "repository_stats": stats,
        "generated_by": "mem8 metadata"
    }


def format_frontmatter(metadata: Dict[str, Any]) -> str:
    """Format metadata as YAML frontmatter for markdown documents."""
    import yaml
    
    # Create a clean copy with string values for YAML
    clean_metadata = {}
    for key, value in metadata.items():
        if isinstance(value, (str, int, float, bool, list)):
            clean_metadata[key] = value
        elif value is None:
            clean_metadata[key] = "unknown"
        else:
            clean_metadata[key] = str(value)
    
    yaml_content = yaml.dump(clean_metadata, default_flow_style=False, sort_keys=False)
    return f"---\n{yaml_content}---\n"


def _check_git_status() -> bool:
    """Check if git working directory is clean."""
    status_result = subprocess.run(
        ["git", "status", "--porcelain"], 
        capture_output=True, text=True
    )
    
    return len(status_result.stdout.strip()) == 0


def _detect_project_type() -> str:
    """Detect the type of project based on files present."""
    current_dir = Path.cwd()
    
    if (current_dir / "package.json").exists():
        return "javascript"
    elif (current_dir / "pyproject.toml").exists() or (current_dir / "setup.py").exists():
        return "python"
    elif (current_dir / "Cargo.toml").exists():
        return "rust"
    elif (current_dir / "go.mod").exists():
        return "go"
    elif (current_dir / "pom.xml").exists():
        return "java"
    elif (current_dir / ".claude").exists():
        return "claude-code"
    elif (current_dir / "memory").exists():
        return "memory-repo"
    else:
        return "unknown"


def _get_repository_stats() -> Dict[str, Any]:
    """Get basic repository statistics."""
    try:
        # Count commits
        commit_count_result = subprocess.run(
            ["git", "rev-list", "--count", "HEAD"],
            capture_output=True, text=True
        )
        commit_count = int(commit_count_result.stdout.strip()) if commit_count_result.returncode == 0 else 0
        
        # Count contributors
        contributors_result = subprocess.run(
            ["git", "shortlog", "-sn", "--all"],
            capture_output=True, text=True
        )
        contributor_count = len(contributors_result.stdout.strip().split('\n')) if contributors_result.returncode == 0 and contributors_result.stdout.strip() else 0
        
        # Get repository age (first commit date)
        first_commit_result = subprocess.run(
            ["git", "log", "--reverse", "--format=%ci", "-1"],
            capture_output=True, text=True
        )
        first_commit_date = first_commit_result.stdout.strip() if first_commit_result.returncode == 0 else None
        
        return {
            "total_commits": commit_count,
            "contributors": contributor_count,
            "first_commit": first_commit_date
        }
    except Exception:
        return {
            "total_commits": 0,
            "contributors": 0,
            "first_commit": None
        }


def generate_filename_timestamp() -> str:
    """Generate a timestamp suitable for filenames."""
    return datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")