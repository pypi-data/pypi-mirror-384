"""Utility functions for mem8."""

import os
import logging
import platform
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any
import shutil
import re


def setup_logging(verbose: bool = False) -> None:
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def get_shared_directory() -> Path:
    """Get the shared directory path with cross-platform support."""
    system = platform.system().lower()
    
    if system == 'windows':
        return _get_windows_shared_directory()
    elif system in ['linux', 'darwin']:
        return _get_unix_shared_directory()
    else:
        # Fallback to user directory
        return Path.home() / "mem8-Shared"


def _get_windows_shared_directory() -> Path:
    """Get Windows-specific shared directory."""
    # Check for common Windows shared locations
    candidates = [
        # Network drives
        Path("//shared/mem8"),
        Path("Z:/mem8"),
        Path("Y:/mem8"),
        # Local shared folders
        Path("C:/Shared/mem8"),
        Path(os.environ.get('USERPROFILE', '')) / "Documents" / "mem8-Shared",
        Path.home() / "mem8-Shared",
    ]
    
    # Check for existing OneDrive or other cloud sync folders
    onedrive_path = os.environ.get('OneDrive')
    if onedrive_path:
        candidates.insert(0, Path(onedrive_path) / "mem8-Shared")
    
    # Return first accessible location
    for path in candidates:
        if path.exists() or _can_create_directory(path):
            return path
    
    # Fallback
    return Path.home() / "mem8-Shared"


def _get_unix_shared_directory() -> Path:
    """Get Unix-like system shared directory."""
    candidates = [
        # Common Unix shared locations
        Path("/shared/mem8"),
        Path("/mnt/shared/mem8"),
        Path("/opt/mem8"),
        Path.home() / "mem8-Shared",
        # Check for mounted network drives
        Path("/media") / os.environ.get('USER', 'shared') / "mem8",
    ]
    
    # Return first accessible location
    for path in candidates:
        if path.exists() or _can_create_directory(path):
            return path
    
    # Fallback
    return Path.home() / "mem8-Shared"


def _can_create_directory(path: Path) -> bool:
    """Check if we can create a directory at the given path."""
    try:
        parent = path.parent
        if not parent.exists():
            return False
        return os.access(parent, os.W_OK)
    except (OSError, PermissionError):
        return False


def is_symlink_supported() -> bool:
    """Check if the current platform supports symlinks."""
    if platform.system().lower() == 'windows':
        # Windows requires special privileges for symlinks in older versions
        try:
            # Try creating a test symlink
            test_dir = Path.home() / ".mem8-test"
            test_link = Path.home() / ".mem8-test-link"
            
            test_dir.mkdir(exist_ok=True)
            if test_link.exists():
                test_link.unlink()
            
            os.symlink(test_dir, test_link)
            test_link.unlink()
            test_dir.rmdir()
            return True
        except (OSError, NotImplementedError):
            return False
    
    return True


def find_claude_code_workspace() -> Optional[Path]:
    """Find the nearest Claude Code workspace (.claude directory)."""
    current = Path.cwd()
    
    while current != current.parent:
        claude_dir = current / ".claude"
        if claude_dir.is_dir():
            return current
        current = current.parent
    
    return None


def get_claude_memory_files() -> List[Path]:
    """Get all Claude Code memory files in hierarchy."""
    memory_files = []
    workspace = find_claude_code_workspace()
    
    if not workspace:
        return memory_files
    
    # Look for CLAUDE.md files from workspace up to root
    current = workspace
    while current != current.parent:
        claude_md = current / "CLAUDE.md"
        if claude_md.exists():
            memory_files.append(claude_md)
        current = current.parent
    
    # Also check user-level memory
    user_claude = Path.home() / ".claude" / "CLAUDE.md"
    if user_claude.exists():
        memory_files.append(user_claude)
    
    return memory_files


def parse_claude_imports(content: str) -> List[str]:
    """Parse @import directives from Claude memory content."""
    imports = []
    lines = content.split('\\n')
    
    for line in lines:
        line = line.strip()
        # Look for @path imports outside code blocks
        if '@' in line and not line.startswith('```') and '`@' not in line:
            # Extract paths starting with @
            import_start = line.find('@')
            if import_start != -1:
                # Find the end of the path (space, newline, or end of line)
                import_path = ""
                for char in line[import_start + 1:]:
                    if char.isspace():
                        break
                    import_path += char
                
                if import_path:
                    imports.append(import_path)
    
    return imports


def resolve_import_path(import_path: str, base_path: Path) -> Optional[Path]:
    """Resolve an import path relative to base path."""
    if import_path.startswith('~/'):
        # User home directory
        return Path.home() / import_path[2:]
    elif import_path.startswith('/'):
        # Absolute path
        return Path(import_path)
    else:
        # Relative to base path
        return base_path.parent / import_path


def get_git_info() -> Dict[str, Any]:
    """Get git repository information if available."""
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--show-toplevel'],
            capture_output=True,
            text=True,
            check=True
        )
        repo_root = Path(result.stdout.strip())
        
        # Get current branch
        branch_result = subprocess.run(
            ['git', 'branch', '--show-current'],
            capture_output=True,
            text=True,
            check=True
        )
        current_branch = branch_result.stdout.strip()
        
        return {
            'is_git_repo': True,
            'repo_root': repo_root,
            'current_branch': current_branch,
        }
    except (subprocess.CalledProcessError, FileNotFoundError):
        return {
            'is_git_repo': False,
            'repo_root': None,
            'current_branch': None,
        }


def create_symlink(target: Path, link_path: Path, force: bool = False) -> bool:
    """Create a symlink with cross-platform support.

    Args:
        target: The target path the symlink should point to
        link_path: The location where the symlink should be created
        force: If True, replace existing symlinks. If False, fail if symlink exists.

    Returns:
        True if symlink was created successfully, False otherwise
    """
    try:
        if link_path.exists() or link_path.is_symlink():
            if link_path.is_symlink():
                if not force:
                    # Don't replace existing symlinks without explicit permission
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Symlink already exists at {link_path}, skipping (use force=True to replace)")
                    return False
                # Remove existing symlink
                link_path.unlink()
            else:
                # Never overwrite real files/directories
                return False

        # On Windows, try junction for directories
        if platform.system().lower() == 'windows' and target.is_dir():
            try:
                subprocess.run(['mklink', '/J', str(link_path), str(target)],
                              shell=True, check=True)
                return True
            except subprocess.CalledProcessError:
                pass

        # Standard symlink
        os.symlink(target, link_path)
        return True
    except (OSError, NotImplementedError):
        return False


def create_symlink_with_info(target: Path, link_path: Path, force: bool = False) -> tuple[bool, str]:
    """Create a symlink with cross-platform support and return info about what was created.

    Args:
        target: The target path the symlink should point to
        link_path: The location where the symlink should be created
        force: If True, replace existing symlinks. If False, fail if symlink exists.

    Returns:
        (success, link_type) where link_type is one of:
        - "junction" (Windows directory junction)
        - "symlink" (Unix symlink or Windows symlink)
        - "directory" (fallback regular directory)
        - "failed" (could not create any type)
    """
    try:
        if link_path.exists() or link_path.is_symlink():
            if link_path.is_symlink():
                if not force:
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Symlink already exists at {link_path}, skipping (use force=True to replace)")
                    return False, "exists"
                link_path.unlink()
            else:
                return False, "failed"

        # On Windows, try junction for directories
        if platform.system().lower() == 'windows' and target.is_dir():
            try:
                subprocess.run(['mklink', '/J', str(link_path), str(target)],
                              shell=True, check=True, capture_output=True)
                return True, "junction"
            except subprocess.CalledProcessError:
                pass

        # Standard symlink
        os.symlink(target, link_path)
        return True, "symlink"
    except (OSError, NotImplementedError):
        return False, "failed"


def ensure_directory_exists(path: Path) -> bool:
    """Ensure directory exists, creating if necessary."""
    try:
        path.mkdir(parents=True, exist_ok=True)
        return True
    except (OSError, PermissionError):
        return False


def verify_templates() -> bool:
    """Verify that template resources are accessible."""
    try:
        from importlib import resources
        import mem8.templates
        
        template_base = resources.files(mem8.templates)
        
        # Check for both templates
        claude_template = template_base / "claude-dot-md-template"
        memory_template = template_base / "shared-memory-template"
        
        # Try to list files in templates
        claude_exists = (claude_template / "cookiecutter.json").exists()
        memory_exists = (memory_template / "cookiecutter.json").exists()
        
        return claude_exists and memory_exists
        
    except Exception:
        return False


def get_template_path(template_name: str) -> Path:
    """Get the path to a template, with fallback to development."""
    try:
        from importlib import resources
        import mem8.templates
        
        template_path = resources.files(mem8.templates) / template_name
        if template_path.exists():
            return template_path
    except Exception:
        pass
    
    # Development fallback
    dev_path = Path(__file__).parent.parent.parent / template_name
    if dev_path.exists():
        return dev_path
    
    raise FileNotFoundError(f"Template not found: {template_name}")


def detect_gh_active_login(hostname: str = "github.com") -> Optional[str]:
    """Detect active GitHub CLI login for a host using `gh auth status`.

    Returns the detected username or None if unavailable.
    Does not require network; relies on local gh auth configuration.
    """
    if not shutil.which("gh"):
        return None
    try:
        # Use gh auth status without hostname to get all accounts and find the active one
        result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )
        out = (result.stdout or "") + "\n" + (result.stderr or "")

        # Parse the new format that shows multiple accounts:
        # ✓ Logged in to github.com account killerapp (keyring)
        # - Active account: true
        # ✓ Logged in to github.com account vaskin-blip (keyring)
        # - Active account: false

        lines = out.split('\n')
        current_account = None

        for i, line in enumerate(lines):
            # Look for login line for the specified hostname
            login_match = re.search(r"Logged in to\s+" + re.escape(hostname) + r"\s+account\s+([A-Za-z0-9-_.]+)", line)
            if login_match:
                current_account = login_match.group(1)
                # Check the next few lines for "Active account: true"
                for j in range(i + 1, min(i + 5, len(lines))):
                    if "Active account: true" in lines[j]:
                        return current_account

            # Also try legacy formats as fallback
            legacy_match = re.search(r"Logged in to\s+" + re.escape(hostname) + r"\s+as\s+([A-Za-z0-9-_.]+)", line)
            if legacy_match:
                return legacy_match.group(1)

        return None
    except Exception:
        return None
