"""
External template source management for mem8.

Supports loading templates from:
- Local directories
- Git repositories (local or remote)
- GitHub URLs (with optional refs and subdirectories)
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
import tempfile
import shutil
import yaml
import subprocess


class TemplateSourceType(Enum):
    """Type of template source."""
    LOCAL = "local"
    GIT = "git"
    GITHUB = "github"
    BUILTIN = "builtin"


@dataclass
class ToolbeltTool:
    """Definition of a CLI tool in the toolbelt."""
    name: str
    command: str
    description: str
    install: Dict[str, str]  # platform -> install command
    version: Optional[str] = None  # minimum version requirement (e.g., ">=2.60")


@dataclass
class ToolbeltDefinition:
    """CLI toolbelt recommendations."""
    required: List[ToolbeltTool]
    optional: List[ToolbeltTool]


@dataclass
class TemplateDefinition:
    """Definition of a single template from the manifest."""
    name: str
    path: str
    type: str  # "cookiecutter"
    variables: Dict[str, Any]
    description: Optional[str] = None


@dataclass
class TemplateManifest:
    """Parsed template manifest."""
    version: int
    source: str  # Relative path to templates directory
    templates: Dict[str, TemplateDefinition]
    metadata: Optional[Dict[str, Any]] = None
    toolbelt: Optional[ToolbeltDefinition] = None


class TemplateSource:
    """
    Represents a source of templates (local, git, GitHub, or builtin).

    Supports various URL formats:
    - Local path: /path/to/templates or ./relative/path
    - Git URL: https://github.com/org/repo.git
    - Git URL with ref: https://github.com/org/repo.git@v1.0.0
    - Git URL with subdir: https://github.com/org/repo.git#subdir=templates
    - Git URL with both: https://github.com/org/repo.git@v1.0.0#subdir=templates
    - GitHub shorthand: org/repo (resolves to https://github.com/org/repo)
    """

    def __init__(self, source_url: Optional[str] = None):
        """
        Initialize template source.

        Args:
            source_url: Path, URL, or GitHub shorthand. None for builtin templates.
        """
        self.source_url = source_url
        self.source_type = self._detect_source_type(source_url)
        self.git_ref: Optional[str] = None
        self.subdir: Optional[str] = None
        self._temp_dir: Optional[Path] = None
        self._resolved_path: Optional[Path] = None

        # Parse git ref and subdir from URL
        if self.source_type in [TemplateSourceType.GIT, TemplateSourceType.GITHUB]:
            self._parse_git_url(source_url)

    def _detect_source_type(self, source_url: Optional[str]) -> TemplateSourceType:
        """Detect the type of template source."""
        if source_url is None:
            return TemplateSourceType.BUILTIN

        # Check for Git URL first (most specific)
        if any(source_url.startswith(prefix) for prefix in ['http://', 'https://', 'git@', 'git://']):
            return TemplateSourceType.GIT

        # Check for GitHub shorthand (org/repo with optional @ref or #subdir)
        # Pattern: org/repo[@ref][#subdir=path]
        if '/' in source_url and not source_url.startswith('.'):
            # Extract base part before @ or #
            base_part = source_url.split('@')[0].split('#')[0]
            parts = base_part.split('/')
            if len(parts) == 2 and not any(c in base_part for c in [':', '..']):
                return TemplateSourceType.GITHUB

        # Check for local path (must exist to be considered local)
        path = Path(source_url)
        if path.exists() and path.is_dir():
            return TemplateSourceType.LOCAL

        # Default to local path (may not exist yet)
        return TemplateSourceType.LOCAL

    def _parse_git_url(self, url: str) -> None:
        """Parse git URL to extract ref and subdir."""
        # Handle GitHub shorthand first
        if self.source_type == TemplateSourceType.GITHUB and '/' in url and not url.startswith('http'):
            # Handle #subdir first (can appear with or without @ref)
            url_without_subdir = url
            if '#subdir=' in url:
                url_without_subdir, subdir_part = url.split('#subdir=', 1)
                self.subdir = subdir_part

            # Then handle @ref
            parts = url_without_subdir.split('@', 1)
            base_url = parts[0]
            if len(parts) > 1:
                self.git_ref = parts[1]

            # Store the base URL for later use
            self._base_url = base_url
            return

        # Parse regular Git URLs
        # Format: url[@ref][#subdir=path]
        url_without_fragment = url
        if '#subdir=' in url:
            url_without_fragment, subdir_part = url.split('#subdir=', 1)
            self.subdir = subdir_part

        if '@' in url_without_fragment:
            # Split on last @ to handle git@github.com:org/repo.git@ref
            parts = url_without_fragment.rsplit('@', 1)
            if not parts[0].endswith('git'):  # Not git@github.com
                self.git_ref = parts[1]

    def resolve(self) -> Path:
        """
        Resolve the template source to a local path.

        For local sources, returns the path directly.
        For git/GitHub sources, clones to a temp directory and returns that path.
        For builtin, returns the packaged templates directory.

        Returns:
            Path to the templates directory
        """
        if self._resolved_path:
            return self._resolved_path

        if self.source_type == TemplateSourceType.LOCAL:
            path = Path(self.source_url)
            if not path.exists():
                raise ValueError(f"Local template path does not exist: {path}")
            self._resolved_path = path
            return path

        if self.source_type == TemplateSourceType.BUILTIN:
            # Builtin templates now live in external repo (killerapp/mem8-plugin)
            # Use the default external source instead
            from .config import Config
            config = Config()
            default_source = config.get('templates.default_source', 'killerapp/mem8-plugin')

            # Create a new TemplateSource for the external repo
            external_source = TemplateSource(default_source)
            self._resolved_path = external_source.resolve()
            # Copy over the temp_dir for cleanup
            self._temp_dir = external_source._temp_dir
            return self._resolved_path

        if self.source_type in [TemplateSourceType.GIT, TemplateSourceType.GITHUB]:
            # Clone to ephemeral temp directory
            self._temp_dir = Path(tempfile.mkdtemp(prefix="mem8-templates-"))

            # Build git URL
            git_url = self.source_url
            if self.source_type == TemplateSourceType.GITHUB and hasattr(self, '_base_url'):
                git_url = f"https://github.com/{self._base_url}.git"
            else:
                # Remove ref and subdir annotations for cloning
                git_url = git_url.split('@')[0].split('#')[0]

            # Clone repository
            clone_cmd = ["git", "clone"]
            if self.git_ref:
                clone_cmd.extend(["--branch", self.git_ref, "--single-branch"])
            clone_cmd.extend([git_url, str(self._temp_dir)])

            try:
                subprocess.run(clone_cmd, check=True, capture_output=True)
            except subprocess.CalledProcessError as e:
                raise ValueError(f"Failed to clone repository: {e.stderr.decode()}")

            # Navigate to subdir if specified
            if self.subdir:
                self._resolved_path = self._temp_dir / self.subdir
                if not self._resolved_path.exists():
                    raise ValueError(f"Subdirectory does not exist in repository: {self.subdir}")
            else:
                self._resolved_path = self._temp_dir

            return self._resolved_path

        raise ValueError(f"Unsupported source type: {self.source_type}")

    def load_manifest(self) -> Optional[TemplateManifest]:
        """
        Load the template manifest from the resolved source.

        Returns:
            TemplateManifest if manifest file exists, None otherwise
        """
        manifest_path = self.resolve() / "manifest.yaml"
        if not manifest_path.exists():
            return None

        with open(manifest_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        # Parse templates
        templates = {}
        for name, config in data.get('templates', {}).items():
            templates[name] = TemplateDefinition(
                name=name,
                path=config['path'],
                type=config.get('type', 'cookiecutter'),
                variables=config.get('variables', {}),
                description=config.get('description')
            )

        # Parse toolbelt
        toolbelt = None
        if 'toolbelt' in data:
            toolbelt_data = data['toolbelt']
            required_tools = [
                ToolbeltTool(
                    name=tool['name'],
                    command=tool['command'],
                    description=tool['description'],
                    install=tool['install'],
                    version=tool.get('version')
                )
                for tool in toolbelt_data.get('required', [])
            ]
            optional_tools = [
                ToolbeltTool(
                    name=tool['name'],
                    command=tool['command'],
                    description=tool['description'],
                    install=tool['install'],
                    version=tool.get('version')
                )
                for tool in toolbelt_data.get('optional', [])
            ]
            toolbelt = ToolbeltDefinition(required=required_tools, optional=optional_tools)

        return TemplateManifest(
            version=data.get('version', 1),
            source=data.get('source', 'templates'),
            templates=templates,
            metadata=data.get('metadata'),
            toolbelt=toolbelt
        )

    def list_templates(self) -> List[str]:
        """
        List available templates from this source.

        Returns:
            List of template names
        """
        manifest = self.load_manifest()
        if manifest:
            return list(manifest.templates.keys())

        # Fallback: scan for cookiecutter.json files
        resolved = self.resolve()
        templates = []
        for item in resolved.iterdir():
            if item.is_dir() and (item / "cookiecutter.json").exists():
                templates.append(item.name)
        return templates

    def get_template_path(self, template_name: str) -> Path:
        """
        Get the full path to a specific template.

        Args:
            template_name: Name of the template (e.g., "claude-config")

        Returns:
            Path to the template directory
        """
        manifest = self.load_manifest()
        resolved = self.resolve()

        if manifest and template_name in manifest.templates:
            template_def = manifest.templates[template_name]
            source_dir = resolved / manifest.source
            return source_dir / template_def.path

        # Fallback: look for directory with that name
        template_path = resolved / template_name
        if template_path.exists():
            return template_path

        # Try adding -template suffix
        template_path = resolved / f"{template_name}-template"
        if template_path.exists():
            return template_path

        raise ValueError(f"Template not found: {template_name}")

    def get_template_variables(self, template_name: str) -> Dict[str, Any]:
        """
        Get default variables for a template from the manifest.

        Args:
            template_name: Name of the template

        Returns:
            Dictionary of variables to pass to cookiecutter
        """
        manifest = self.load_manifest()
        if manifest and template_name in manifest.templates:
            return manifest.templates[template_name].variables.copy()
        return {}

    def cleanup(self) -> None:
        """Clean up temporary directories."""
        if self._temp_dir and self._temp_dir.exists():
            shutil.rmtree(self._temp_dir, ignore_errors=True)

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup temp files."""
        self.cleanup()


def get_builtin_templates() -> TemplateSource:
    """Get the builtin template source."""
    return TemplateSource(None)


def create_template_source(source_url: Optional[str]) -> TemplateSource:
    """
    Create a template source from a URL or path.

    Args:
        source_url: Path, URL, or GitHub shorthand. None for builtin.

    Returns:
        TemplateSource instance
    """
    return TemplateSource(source_url)
