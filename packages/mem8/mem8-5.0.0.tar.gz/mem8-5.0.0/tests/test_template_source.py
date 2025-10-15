"""Tests for external template source functionality."""

import pytest
import tempfile
from pathlib import Path
from mem8.core.template_source import (
    TemplateSource,
    TemplateSourceType,
    create_template_source,
    get_builtin_templates,
)


def test_builtin_template_source():
    """Test builtin template source."""
    source = get_builtin_templates()
    assert source.source_type == TemplateSourceType.BUILTIN

    path = source.resolve()
    assert path.exists()
    assert (path / "manifest.yaml").exists()


def test_local_template_source():
    """Test local directory template source."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create a simple template structure
        template_dir = tmppath / "test-template"
        template_dir.mkdir()
        (template_dir / "cookiecutter.json").write_text('{"test": "value"}')

        source = create_template_source(str(tmppath))
        assert source.source_type == TemplateSourceType.LOCAL

        resolved = source.resolve()
        assert resolved == tmppath


def test_github_shorthand_parsing():
    """Test GitHub shorthand URL parsing."""
    source = TemplateSource("org/repo")
    assert source.source_type == TemplateSourceType.GITHUB
    assert hasattr(source, '_base_url')
    assert source._base_url == "org/repo"


def test_github_shorthand_with_ref():
    """Test GitHub shorthand with git ref."""
    source = TemplateSource("org/repo@v1.0.0")
    assert source.source_type == TemplateSourceType.GITHUB
    assert source.git_ref == "v1.0.0"


def test_github_shorthand_with_subdir():
    """Test GitHub shorthand with subdirectory."""
    source = TemplateSource("org/repo#subdir=templates")
    assert source.source_type == TemplateSourceType.GITHUB
    assert source.subdir == "templates"


def test_github_shorthand_with_ref_and_subdir():
    """Test GitHub shorthand with both ref and subdirectory."""
    source = TemplateSource("org/repo@v1.0.0#subdir=templates")
    assert source.source_type == TemplateSourceType.GITHUB
    assert source.git_ref == "v1.0.0"
    assert source.subdir == "templates"


def test_git_url_detection():
    """Test Git URL detection."""
    source = TemplateSource("https://github.com/org/repo.git")
    assert source.source_type == TemplateSourceType.GIT


def test_manifest_loading():
    """Test manifest loading from builtin templates."""
    source = get_builtin_templates()
    manifest = source.load_manifest()

    assert manifest is not None
    assert manifest.version == 1
    assert "claude-config" in manifest.templates
    assert "memory-repo" in manifest.templates
    assert "full" in manifest.templates


def test_template_list():
    """Test listing templates from source."""
    source = get_builtin_templates()
    templates = source.list_templates()

    assert len(templates) > 0
    assert "claude-config" in templates or "full" in templates


def test_get_template_path():
    """Test resolving template path."""
    source = get_builtin_templates()

    # This should work for a known template
    path = source.get_template_path("claude-dot-md-template")
    assert path.exists()
    assert (path / "cookiecutter.json").exists()


def test_get_template_path_not_found():
    """Test getting path for non-existent template."""
    source = get_builtin_templates()

    with pytest.raises(ValueError, match="Template not found"):
        source.get_template_path("nonexistent-template")


@pytest.mark.skip(reason="Cleanup may be delayed on Windows due to file locks")
def test_context_manager_cleanup():
    """Test that context manager cleans up temp directories."""
    source_url = "killerapp/mem8-plugin"

    temp_path = None
    with create_template_source(source_url) as source:
        if source.source_type in [TemplateSourceType.GIT, TemplateSourceType.GITHUB]:
            # For git sources, _temp_dir is created on resolve()
            source.resolve()
            temp_path = source._temp_dir

    # After exiting context, temp directory should be cleaned up
    # Note: On Windows, this may fail due to file locks
    if temp_path:
        assert not temp_path.exists()


def test_multiple_source_types():
    """Test detection of different source types."""
    # Local path
    source1 = TemplateSource("./templates")
    assert source1.source_type == TemplateSourceType.LOCAL

    # GitHub shorthand
    source2 = TemplateSource("org/repo")
    assert source2.source_type == TemplateSourceType.GITHUB

    # Git URL
    source3 = TemplateSource("https://github.com/org/repo.git")
    assert source3.source_type == TemplateSourceType.GIT

    # Builtin
    source4 = TemplateSource(None)
    assert source4.source_type == TemplateSourceType.BUILTIN
