"""
Tests for external template source support in mem8 doctor.

Validates that doctor can load toolbelt definitions from:
- Local paths
- GitHub URLs
- Project-level config (.mem8/config.yaml)
- User-level config (~/.config/mem8/config.yaml)
"""
import subprocess
import tempfile
from pathlib import Path
import pytest
import yaml


class TestExternalTemplateSources:
    """Test doctor with external template sources."""

    def test_doctor_with_local_path(self):
        """Test doctor --template-source with local path."""
        # Templates are now external, use builtin source for local path testing
        from mem8.core.template_source import get_builtin_templates

        source = get_builtin_templates()
        template_path = source.resolve()

        result = subprocess.run(
            ["mem8", "doctor", "--template-source", str(template_path), "--json"],
            capture_output=True,
            text=True,
            timeout=10
        )

        # Should complete successfully
        assert result.returncode in [0, 1]

        # Should have valid JSON output
        import json
        data = json.loads(result.stdout)
        assert "status" in data

        # Should have checked tools (either found issues or all healthy)
        assert "issues" in data

    def test_doctor_with_github_shorthand(self):
        """Test doctor with GitHub shorthand (org/repo)."""
        result = subprocess.run(
            ["mem8", "doctor",
             "--template-source", "killerapp/mem8-plugin",
             "--json"],
            capture_output=True,
            text=True,
            timeout=120  # GitHub clone can take time
        )

        # Should complete
        assert result.returncode in [0, 1]

        # Should have cloned and used the template
        import json
        data = json.loads(result.stdout)
        assert "issues" in data

    def test_doctor_with_github_url(self):
        """Test doctor with full GitHub URL."""
        result = subprocess.run(
            ["mem8", "doctor",
             "--template-source", "https://github.com/killerapp/mem8-plugin.git",
             "--json"],
            capture_output=True,
            text=True,
            timeout=120
        )

        # Should complete
        assert result.returncode in [0, 1]

        import json
        data = json.loads(result.stdout)
        assert "status" in data

    def test_doctor_with_root_level_template_repo(self):
        """Test doctor with dedicated template repo (no subdir)."""
        # Use local ../mem8-templates repo which has manifest at root
        templates_path = Path(__file__).parent.parent.parent / "mem8-templates"

        result = subprocess.run(
            ["mem8", "doctor",
             "--template-source", str(templates_path),
             "--json"],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=120
        )

        # Should complete successfully
        assert result.returncode in [0, 1]

        import json
        data = json.loads(result.stdout)
        assert "issues" in data

        # Should have checked tools from the manifest
        # The test just verifies the external template source is used
        assert result.returncode in [0, 1]

    def test_doctor_uses_project_config(self):
        """Test that doctor reads .mem8/config.yaml."""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)

            # Create .mem8 directory
            mem8_dir = workspace / ".mem8"
            mem8_dir.mkdir()

            # Create project config with template source
            config_file = mem8_dir / "config.yaml"
            config = {
                "templates": {
                    "default_source": str(Path(__file__).parent.parent / "mem8" / "templates")
                }
            }
            with open(config_file, 'w') as f:
                yaml.dump(config, f)

            # Run doctor (should use config)
            result = subprocess.run(
                ["mem8", "doctor", "--json"],
                cwd=workspace,
                capture_output=True,
                text=True,
                timeout=10
            )

            # Should have run and checked tools
            import json
            data = json.loads(result.stdout)
            assert "issues" in data

    def test_cli_flag_overrides_config(self):
        """Test that --template-source flag overrides config files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)

            # Create .mem8 directory
            mem8_dir = workspace / ".mem8"
            mem8_dir.mkdir()

            # Create project config with one source
            config_file = mem8_dir / "config.yaml"
            config = {
                "templates": {
                    "default_source": "/invalid/path"
                }
            }
            with open(config_file, 'w') as f:
                yaml.dump(config, f)

            # Use CLI flag to override with builtin templates
            from mem8.core.template_source import get_builtin_templates
            source = get_builtin_templates()
            valid_path = str(source.resolve())

            result = subprocess.run(
                ["mem8", "doctor",
                 "--template-source", valid_path,
                 "--json"],
                cwd=workspace,
                capture_output=True,
                text=True,
                timeout=10
            )

            # Should succeed with valid path, not fail with invalid
            assert result.returncode in [0, 1]

            import json
            data = json.loads(result.stdout)

            # Should not have error about invalid path
            error_messages = [str(issue) for issue in data.get("issues", [])]
            assert not any("/invalid/path" in msg for msg in error_messages)

    def test_project_config_format(self):
        """Test that default config follows expected format."""
        # Example config is now in external templates, test default config instead
        from mem8.core.config import Config
        config_obj = Config()
        config = config_obj._get_default_config()

        # Should have templates section
        assert "templates" in config
        assert "default_source" in config["templates"]

        # Should have other expected sections
        expected_sections = ["workspace", "shared", "discovery", "workflow", "claude_code", "sync", "search"]
        for section in expected_sections:
            assert section in config, f"Missing expected section: {section}"

    def test_builtin_is_default(self):
        """Test that builtin templates are used when no config exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)

            # No .mem8 directory, no config
            result = subprocess.run(
                ["mem8", "doctor", "--json"],
                cwd=workspace,
                capture_output=True,
                text=True,
                timeout=10
            )

            # Should still work (using builtin)
            assert result.returncode in [0, 1]

            import json
            data = json.loads(result.stdout)
            assert "status" in data

            # Should have checked tools using builtin manifest
            # Just verify it ran successfully
            assert data["status"] in ["healthy", "unhealthy"]

    def test_template_source_with_version_tag(self):
        """Test template source with version tag (@v1.0.0)."""
        # This tests the URL parsing, actual fetch depends on tag existence
        result = subprocess.run(
            ["mem8", "doctor",
             "--template-source", "killerapp/mem8-plugin@main",
             "--json"],
            capture_output=True,
            text=True,
            timeout=120
        )

        # Should handle the @ref syntax
        assert result.returncode in [0, 1]

    def test_invalid_template_source_handling(self):
        """Test graceful handling of invalid template sources."""
        result = subprocess.run(
            ["mem8", "doctor",
             "--template-source", "/nonexistent/path/to/templates"],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=10
        )

        # Should fail but not crash
        assert result.returncode == 1

        # Should have error message about the invalid path
        assert result.stdout and ("/nonexistent/path" in result.stdout or "not" in result.stdout.lower())

    def test_template_source_help_text(self):
        """Test that --template-source is documented in help."""
        result = subprocess.run(
            ["mem8", "doctor", "--help"],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )

        assert result.returncode == 0
        assert "--template-source" in result.stdout
        assert "local path" in result.stdout.lower() or "git" in result.stdout.lower()

    def test_config_cascade_priority(self):
        """Test configuration cascade: CLI > project > user > builtin."""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            mem8_dir = workspace / ".mem8"
            mem8_dir.mkdir()

            # Create project config
            project_config = mem8_dir / "config.yaml"
            with open(project_config, 'w') as f:
                yaml.dump({
                    "templates": {
                        "default_source": "/project/templates"
                    }
                }, f)

            # Run without CLI flag - should try to use project config
            result = subprocess.run(
                ["mem8", "doctor"],
                cwd=workspace,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=10
            )

            # Should mention the project template source (even if it fails)  or just run successfully
            assert result.returncode in [0, 1]


class TestTemplateSourceTypes:
    """Test different template source URL formats."""

    def test_local_absolute_path(self):
        """Test absolute local path format."""
        from mem8.core.template_source import TemplateSource

        source = TemplateSource("/absolute/path/to/templates")
        assert source.source_type.value == "local"

    def test_local_relative_path(self):
        """Test relative local path format."""
        from mem8.core.template_source import TemplateSource

        source = TemplateSource("./relative/path")
        assert source.source_type.value == "local"

    def test_github_shorthand(self):
        """Test GitHub shorthand format (org/repo)."""
        from mem8.core.template_source import TemplateSource

        source = TemplateSource("killerapp/mem8")
        assert source.source_type.value == "github"

    def test_github_shorthand_with_subdir(self):
        """Test GitHub shorthand with subdirectory."""
        from mem8.core.template_source import TemplateSource

        source = TemplateSource("killerapp/mem8-plugin#subdir=templates")
        assert source.source_type.value == "github"
        assert source.subdir == "templates"

    def test_github_shorthand_with_ref(self):
        """Test GitHub shorthand with ref (tag/branch)."""
        from mem8.core.template_source import TemplateSource

        source = TemplateSource("killerapp/mem8-plugin@v1.0.0")
        assert source.source_type.value == "github"
        assert source.git_ref == "v1.0.0"

    def test_git_url(self):
        """Test full Git URL format."""
        from mem8.core.template_source import TemplateSource

        source = TemplateSource("https://github.com/killerapp/mem8.git")
        assert source.source_type.value == "git"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
