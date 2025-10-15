"""
Tests to verify mem8 doctor correctly loads and uses manifest.yaml manifest.

This validates that the toolbelt definitions from the builtin templates
are properly loaded and used during diagnosis.
"""
import subprocess
import json
import pytest


class TestDoctorManifestIntegration:
    """Test that doctor command uses manifest.yaml correctly."""

    def test_builtin_manifest_loads(self):
        """Verify that builtin templates manifest loads correctly."""
        from mem8.core.template_source import TemplateSource

        # Load builtin templates (None = builtin)
        source = TemplateSource(None)
        manifest = source.load_manifest()

        # Should have loaded successfully
        assert manifest is not None, "Builtin manifest failed to load"
        assert manifest.toolbelt is not None, "No toolbelt in manifest"

        # Should have required and optional tools
        assert len(manifest.toolbelt.required) > 0, "No required tools defined"
        assert len(manifest.toolbelt.optional) > 0, "No optional tools defined"

        # Verify expected tools are present
        required_names = [t.name for t in manifest.toolbelt.required]
        assert "ripgrep" in required_names or "rg" in [t.command for t in manifest.toolbelt.required]
        assert "fd" in [t.command for t in manifest.toolbelt.required]
        assert "git" in [t.command for t in manifest.toolbelt.required]
        assert "gh" in [t.command for t in manifest.toolbelt.required]

    def test_manifest_location(self):
        """Verify manifest is accessible from builtin template source."""
        from mem8.core.template_source import get_builtin_templates

        # Builtin now uses external templates, so manifest should be accessible
        source = get_builtin_templates()
        manifest_path = source.resolve() / "manifest.yaml"

        assert manifest_path.exists(), f"Manifest not found at {manifest_path}"

        # Read and verify it has toolbelt section
        import yaml
        with open(manifest_path, 'r') as f:
            data = yaml.safe_load(f)

        assert "toolbelt" in data, "No toolbelt section in manifest"
        assert "required" in data["toolbelt"], "No required tools in toolbelt"
        assert "optional" in data["toolbelt"], "No optional tools in toolbelt"

    def test_doctor_uses_manifest_tools(self):
        """Test that doctor command checks tools from manifest."""
        result = subprocess.run(
            ["mem8", "doctor", "--json"],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )

        data = json.loads(result.stdout)

        # Should have checked for tools
        has_tool_issues = any(
            "tools" in str(issue).lower() or "missing_tools" in issue
            for issue in data["issues"]
        )

        # Either has tool issues, or all tools are present
        if has_tool_issues:
            # Find the tool issue
            tool_issue = next(
                (issue for issue in data["issues"] if "missing_tools" in issue),
                None
            )

            assert tool_issue is not None, "Expected missing_tools in issues"

            # Verify tools match manifest
            missing_tools = tool_issue["missing_tools"]
            tool_commands = [t["command"] for t in missing_tools]

            # Should be checking for known tools from manifest
            known_commands = ["rg", "fd", "gh", "git", "jq", "bat", "delta", "yq", "fzf", "sd", "ast-grep"]
            for cmd in tool_commands:
                assert cmd in known_commands, f"Unknown tool checked: {cmd}"

    def test_manifest_tool_structure(self):
        """Test that manifest tools have required fields."""
        from mem8.core.template_source import TemplateSource

        source = TemplateSource(None)
        manifest = source.load_manifest()

        # Check required tools structure
        for tool in manifest.toolbelt.required:
            assert tool.name, f"Tool missing name: {tool}"
            assert tool.command, f"Tool {tool.name} missing command"
            assert tool.description, f"Tool {tool.name} missing description"
            assert tool.install, f"Tool {tool.name} missing install dict"

            # Should have install commands for at least one platform
            assert len(tool.install) > 0, f"Tool {tool.name} has no install commands"

            # Common platforms should be present
            platforms = set(tool.install.keys())
            common_platforms = {"windows", "macos", "linux", "all"}
            assert len(platforms & common_platforms) > 0, \
                f"Tool {tool.name} missing common platform install commands"

        # Check optional tools structure
        for tool in manifest.toolbelt.optional:
            assert tool.name, f"Optional tool missing name: {tool}"
            assert tool.command, f"Optional tool {tool.name} missing command"
            assert tool.description, f"Optional tool {tool.name} missing description"
            assert tool.install, f"Optional tool {tool.name} missing install dict"

    def test_manifest_version_requirements(self):
        """Test that version requirements are properly formatted."""
        from mem8.core.template_source import TemplateSource

        source = TemplateSource(None)
        manifest = source.load_manifest()

        # Check all tools with version requirements
        all_tools = manifest.toolbelt.required + manifest.toolbelt.optional

        for tool in all_tools:
            if tool.version:
                # Version should be a string with operator
                assert isinstance(tool.version, str), \
                    f"Tool {tool.name} version should be string, got {type(tool.version)}"

                # Should match pattern like ">=2.60" or "==1.0.0"
                import re
                version_pattern = r'^[><=!]+\s*v?\d+\.\d+(?:\.\d+)?$'
                assert re.match(version_pattern, tool.version), \
                    f"Tool {tool.name} has invalid version format: {tool.version}"

    def test_doctor_reports_version_mismatches(self):
        """Test that doctor reports when installed version doesn't meet requirements."""
        from mem8.core.template_source import TemplateSource

        source = TemplateSource(None)
        manifest = source.load_manifest()

        # Find a tool with version requirement
        versioned_tool = next(
            (t for t in manifest.toolbelt.required if t.version),
            None
        )

        if versioned_tool:
            # Run doctor and check if version info is reported
            result = subprocess.run(
                ["mem8", "doctor"],
                capture_output=True,
                text=True,
            encoding='utf-8',
            errors='replace'
            )

            # If the tool is installed but wrong version, should show both versions
            if versioned_tool.command in result.stdout and "Current:" in result.stdout:
                # Should show required version
                assert versioned_tool.version.replace(">=", "") in result.stdout or \
                       "requires" in result.stdout, \
                       "Version requirement not shown in output"

    def test_platform_specific_install_commands_from_manifest(self):
        """Test that doctor uses platform-specific commands from manifest."""
        import platform

        result = subprocess.run(
            ["mem8", "doctor"],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )

        if "Install:" in result.stdout:
            platform.system().lower()

            # Load manifest to check install commands
            from mem8.core.template_source import TemplateSource
            source = TemplateSource(None)
            manifest = source.load_manifest()

            # Get platform key
            from mem8.core.memory import MemoryManager
            from mem8.core.config import Config
            manager = MemoryManager(Config())
            platform_key = manager._get_platform_key()

            # Verify install commands match platform
            for tool in manifest.toolbelt.required:
                if tool.command in result.stdout:
                    expected_install = tool.install.get(
                        platform_key,
                        tool.install.get('all', '')
                    )

                    if expected_install and expected_install != 'See documentation':
                        # The install command from manifest should appear in output
                        # (might be partial match due to formatting)
                        assert any(
                            part in result.stdout
                            for part in expected_install.split()[:2]  # Check first 2 words
                        ), f"Platform-specific install for {tool.name} not found in output"

    def test_manifest_includes_essential_tools(self):
        """Test that manifest includes essential tools for AI workflows."""
        from mem8.core.template_source import TemplateSource

        source = TemplateSource(None)
        manifest = source.load_manifest()

        all_commands = [t.command for t in manifest.toolbelt.required + manifest.toolbelt.optional]

        # Essential tools for AI/automation workflows
        essential = ["rg", "fd", "jq", "gh", "git"]

        for cmd in essential:
            assert cmd in all_commands, \
                f"Essential tool {cmd} not in manifest toolbelt"

    def test_doctor_json_includes_manifest_tool_info(self):
        """Test that JSON output includes full tool information from manifest."""
        result = subprocess.run(
            ["mem8", "doctor", "--json"],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )

        data = json.loads(result.stdout)

        # Find tool issues
        tool_issues = [
            issue for issue in data["issues"]
            if "missing_tools" in issue
        ]

        if tool_issues:
            for issue in tool_issues:
                for tool in issue["missing_tools"]:
                    # Should have fields from manifest
                    assert "name" in tool
                    assert "command" in tool
                    assert "description" in tool
                    assert "install" in tool

                    # Install command should be platform-specific (not empty)
                    assert tool["install"] != ""
                    assert "See documentation" in tool["install"] or \
                           any(pkg in tool["install"] for pkg in ["winget", "brew", "apt", "cargo", "scoop"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
