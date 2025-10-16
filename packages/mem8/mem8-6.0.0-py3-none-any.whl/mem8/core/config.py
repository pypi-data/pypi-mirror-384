"""Configuration management for mem8."""

import os
from pathlib import Path
from typing import Optional, Dict, Any
import yaml
from platformdirs import user_config_dir, user_data_dir


class Config:
    """mem8 configuration manager."""
    
    def __init__(self, config_dir: Optional[str] = None):
        """Initialize configuration manager.

        Honors environment overrides for testability and isolation:
        - MEM8_CONFIG_DIR: overrides platformdirs' config directory
        - MEM8_DATA_DIR: overrides platformdirs' data directory
        """
        env_config_dir = os.environ.get("MEM8_CONFIG_DIR")
        env_data_dir = os.environ.get("MEM8_DATA_DIR")

        self.config_dir = Path(config_dir or env_config_dir or user_config_dir("mem8"))
        self.data_dir = Path(env_data_dir or user_data_dir("mem8"))
        self.config_file = self.config_dir / "config.yaml"
        
        # Ensure directories exist
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Load configuration
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
            except (yaml.YAMLError, IOError):
                pass
        
        # Return default configuration
        return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            'workspace': {
                'default_template': 'full',
                'auto_sync': True,
                'sync_interval': 300,  # 5 minutes
            },
            'templates': {
                'default_source': 'killerapp/mem8-plugin',  # External template repo
            },
            'discovery': {
                'cross_repo': False,  # default to single-repo discovery
            },
            'workflow': {
                'provider': 'github',
                'automation_level': 'standard',
                'github_org': None,
                'github_repo': None,
                'auto_detect_repo': True,
            },
            'shared': {
                'default_location': str(self._get_default_shared_location()),
                'symlink_support': True,
                'network_drive_support': True,
            },
            'claude_code': {
                'integration_enabled': True,
                'auto_detect_workspace': True,
                'memory_hierarchy': ['enterprise', 'project', 'user', 'local'],
            },
            'sync': {
                'conflict_resolution': 'prompt',  # prompt, local, shared, newest
                'backup_before_sync': True,
                'exclude_patterns': ['.git', '__pycache__', '*.pyc', '.DS_Store'],
            },
            'search': {
                'index_enabled': True,
                'index_content': True,
                'index_metadata': True,
            },
        }
    
    def _get_default_shared_location(self) -> Path:
        """Get platform-appropriate default shared location."""
        if os.name == 'nt':  # Windows
            # Try common Windows shared locations
            possible_paths = [
                Path.home() / "Documents" / "mem8-Shared",
                Path("C:/mem8-Shared"),
                Path.home() / "mem8-Shared",
            ]
        else:  # Unix-like systems
            possible_paths = [
                Path.home() / "mem8-Shared",
                Path("/shared/mem8"),
                Path("/mnt/shared/mem8"),
            ]
        
        # Return the first writable location
        for path in possible_paths:
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                if path.parent.is_dir() and os.access(path.parent, os.W_OK):
                    return path
            except (OSError, PermissionError):
                continue
        
        # Fallback to user documents
        return Path.home() / "Documents" / "mem8-Shared"
    
    def get(self, key: str, default=None) -> Any:
        """Get configuration value using dot notation."""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value using dot notation."""
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        self._save_config()
    
    def _save_config(self) -> None:
        """Save configuration to file."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(self._config, f, default_flow_style=False, indent=2)
        except (yaml.YAMLError, IOError) as e:
            print(f"Warning: Could not save configuration: {e}")
    
    @property
    def workspace_dir(self) -> Path:
        """Get current workspace directory."""
        return Path.cwd()
    
    @property
    def claude_dir(self) -> Path:
        """Get .claude directory path."""
        return self.workspace_dir / ".claude"
    
    @property
    def memory_dir(self) -> Path:
        """Get memory directory path."""
        return self.workspace_dir / "memory"
    
    @property
    def shared_dir(self) -> Optional[Path]:
        """Get configured shared directory path."""
        shared_path = self.get('shared.default_location')
        if shared_path:
            path = Path(shared_path)
            # Resolve symlinks if needed
            if path.is_symlink() and self.get('shared.symlink_support', True):
                return path.resolve()
            return path
        return None
    
    def save_workflow_preferences(self, template: str, workflow_provider: str,
                                automation_level: str, github_org: str = None) -> None:
        """Save workflow preferences for future init commands.

        Note: github_repo is intentionally NOT saved as it's project-specific.
        Each project should determine its repo name from context (directory name, git remote, etc).
        """
        self.set('workspace.default_template', template)
        self.set('workflow.provider', workflow_provider)
        self.set('workflow.automation_level', automation_level)

        if github_org:
            self.set('workflow.github_org', github_org)
    
    def get_workflow_defaults(self) -> Dict[str, Any]:
        """Get saved workflow preferences for use as defaults.

        Note: github_repo is intentionally excluded as it's project-specific.
        """
        return {
            'template': self.get('workspace.default_template', 'full'),
            'workflow_provider': self.get('workflow.provider', 'github'),
            'automation_level': self.get('workflow.automation_level', 'standard'),
            'github_org': self.get('workflow.github_org'),
        }
    
    def create_home_shortcut(self) -> bool:
        """Create a ~/.mem8 shortcut to the config directory (like kubectl)."""
        # Allow disabling from environment to avoid side-effects during tests
        if os.environ.get("MEM8_DISABLE_HOME_SHORTCUT") == "1":
            return False

        home_shortcut = Path.home() / ".mem8"

        try:
            # Check existing shortcut
            if home_shortcut.exists() or home_shortcut.is_symlink():
                if home_shortcut.is_dir() and not home_shortcut.is_symlink():
                    # It's a real directory, don't overwrite
                    return False

                if home_shortcut.is_symlink():
                    # Check if symlink points to our config directory
                    existing_target = home_shortcut.resolve()
                    if existing_target == self.config_dir.resolve():
                        # Already points to correct location
                        return True
                    else:
                        # Points to different location - warn and skip
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.warning(
                            f"~/.mem8 symlink exists but points to {existing_target} "
                            f"(expected {self.config_dir}). Skipping replacement."
                        )
                        return False

                # Remove existing shortcut (non-directory file)
                home_shortcut.unlink()

            # Create symlink/junction to config directory
            if os.name == 'nt':  # Windows - use junction
                import subprocess
                result = subprocess.run([
                    "mklink", "/J", str(home_shortcut), str(self.config_dir)
                ], shell=True, capture_output=True)
                return result.returncode == 0
            else:  # Unix-like - use symlink
                home_shortcut.symlink_to(self.config_dir)
                return True

        except (OSError, PermissionError):
            return False
