"""
Integration tests for mem8 doctor command.

Tests the complete doctor workflow including toolbelt checking,
JSON output, auto-fix, and exit codes.
"""
import json
import subprocess
import tempfile
import shutil
from pathlib import Path
import pytest


class TestDoctorIntegration:
    """Integration tests for mem8 doctor command."""

    def run_doctor(self, args=None, cwd=None):
        """Run mem8 doctor command."""
        cmd = ["mem8", "doctor"]
        if args:
            cmd.extend(args)

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            cwd=cwd or Path.cwd()
        )
        return result

    def test_doctor_basic_execution(self):
        """Test that doctor command runs without errors."""
        result = self.run_doctor()

        # Should complete (exit code 0 or 1 for issues)
        assert result.returncode in [0, 1]

        # Should have some output
        assert len(result.stdout) > 0 or len(result.stderr) > 0

    def test_doctor_help_flag(self):
        """Test doctor --help output."""
        result = subprocess.run(
            ["mem8", "doctor", "--help"],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )

        assert result.returncode == 0
        assert "--fix" in result.stdout
        assert "--json" in result.stdout
        assert "Diagnose" in result.stdout

    def test_doctor_json_structure(self):
        """Test that --json produces valid, well-structured JSON."""
        result = self.run_doctor(["--json"])

        # Should produce JSON regardless of health status
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            pytest.fail(f"Invalid JSON output: {e}\nOutput: {result.stdout}")

        # Validate structure
        required_fields = ["status", "health_score", "issues", "fixes_applied", "recommendations"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

        # Validate types
        assert isinstance(data["status"], str)
        assert data["status"] in ["healthy", "unhealthy"]
        assert isinstance(data["health_score"], (int, float))
        assert 0 <= data["health_score"] <= 100
        assert isinstance(data["issues"], list)
        assert isinstance(data["fixes_applied"], list)
        assert isinstance(data["recommendations"], list)

        # Validate issues structure if present
        for issue in data["issues"]:
            assert "severity" in issue
            assert issue["severity"] in ["error", "warning", "info"]
            assert "description" in issue

    def test_doctor_json_no_extra_output(self):
        """Test that --json doesn't include non-JSON output."""
        result = self.run_doctor(["--json"])

        # The entire stdout should be parseable as JSON
        # No "Running diagnostics..." or other human-readable text
        try:
            json.loads(result.stdout)
        except json.JSONDecodeError:
            # Check if there's non-JSON content
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1 or not result.stdout.strip().startswith('{'):
                pytest.fail(f"JSON output contains non-JSON content: {result.stdout}")

    def test_doctor_toolbelt_detection(self):
        """Test that doctor runs successfully and provides diagnostic output."""
        result = self.run_doctor()

        # Doctor should run successfully and provide output
        assert result.returncode in (0, 1)  # 0 = healthy, 1 = issues found
        output = result.stdout.lower()

        # Should show diagnostic information
        assert any(keyword in output for keyword in [
            "diagnostics",
            "running",
            "issues",
            "checks passed",
            "directory"
        ])

    def test_doctor_exit_code_with_issues(self):
        """Test that exit code is 1 when issues are found."""
        result = self.run_doctor()

        if result.returncode == 1:
            # Should have issues mentioned in output
            assert any(keyword in result.stdout for keyword in [
                "Issues found",
                "Missing",
                "required",
                "optional"
            ])

    def test_doctor_exit_code_healthy(self):
        """Test that exit code is 0 when workspace is healthy."""
        result = self.run_doctor()

        if result.returncode == 0:
            # Either explicitly states healthy or has no critical issues
            output = result.stdout.lower()
            # If healthy, shouldn't have critical errors (warnings/info are ok)
            if "issues found" in output:
                assert "error" not in output or "0 error" in output

    def test_doctor_in_workspace(self):
        """Test doctor inside an initialized workspace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)

            # Initialize workspace
            init_result = subprocess.run(
                ["mem8", "init", "--force"],
                cwd=workspace,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )

            if init_result.returncode != 0:
                pytest.skip("Could not initialize workspace for test")

            # Run doctor in workspace
            result = self.run_doctor(cwd=workspace)

            # Should check workspace components or show health status
            # Doctor may show various outputs depending on workspace state
            assert result.returncode in [0, 1]
            assert len(result.stdout) > 0

    def test_doctor_verbose_flag(self):
        """Test doctor with --verbose flag."""
        result = subprocess.run(
            ["mem8", "doctor", "--verbose"],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )

        # Verbose should provide more detailed output or at least run
        assert result.returncode in [0, 1]
        assert len(result.stdout) > 0

    def test_doctor_fix_flag(self):
        """Test that --fix flag is accepted and processes."""
        result = subprocess.run(
            ["mem8", "doctor", "--fix"],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )

        # Should complete (may or may not fix things)
        assert result.returncode in [0, 1]

        # Output should indicate fix mode
        if result.returncode == 1 and "Issues found" in result.stdout:
            # If issues remain, should show what wasn't fixed
            assert len(result.stdout) > 0

    def test_doctor_json_with_toolbelt_info(self):
        """Test that JSON output includes detailed toolbelt information."""
        result = self.run_doctor(["--json"])

        data = json.loads(result.stdout)

        # Check if toolbelt issues are present
        for issue in data["issues"]:
            if "missing_tools" in issue:
                # Validate tool information structure
                for tool in issue["missing_tools"]:
                    assert "name" in tool
                    assert "command" in tool
                    assert "description" in tool
                    assert "install" in tool
                    # version and current_version are optional
                    if "version" in tool and tool["version"]:
                        assert isinstance(tool["version"], str)

    def test_doctor_platform_specific_commands(self):
        """Test that install commands are appropriate for the platform."""
        import platform

        result = self.run_doctor()

        if "Missing" in result.stdout and "Install:" in result.stdout:
            # Check for platform-appropriate package managers
            system = platform.system().lower()

            if system == "windows" or "win" in system:
                # Should suggest winget or scoop
                assert any(pm in result.stdout for pm in ["winget", "scoop", "choco"])
            elif system == "darwin":
                # Should suggest brew
                assert "brew" in result.stdout
            elif system == "linux":
                # Should suggest apt, yum, or other Linux package managers
                assert any(pm in result.stdout for pm in ["apt", "yum", "dnf", "pacman"])

    def test_doctor_idempotent(self):
        """Test that running doctor multiple times gives consistent results."""
        result1 = self.run_doctor(["--json"])
        result2 = self.run_doctor(["--json"])

        data1 = json.loads(result1.stdout)
        data2 = json.loads(result2.stdout)

        # Results should be consistent
        assert data1["status"] == data2["status"]
        assert len(data1["issues"]) == len(data2["issues"])

        # Health scores should be the same
        assert data1["health_score"] == data2["health_score"]

    def test_doctor_with_missing_directory(self):
        """Test doctor detects missing workspace directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)

            # Initialize workspace
            subprocess.run(
                ["mem8", "init", "--force"],
                cwd=workspace,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )

            # Remove a directory
            memory_dir = workspace / "memory"
            if memory_dir.exists():
                # Windows permissions issue - use ignore_errors
                shutil.rmtree(memory_dir, ignore_errors=True)

            # Doctor should detect the issue if deletion succeeded
            result = self.run_doctor(cwd=workspace)

            # If directory was successfully deleted, should report issue
            # Otherwise just verify doctor runs
            assert result.returncode in [0, 1]
            if not memory_dir.exists():
                assert "memory" in result.stdout.lower() or "missing" in result.stdout.lower()


class TestDoctorPerformance:
    """Performance tests for doctor command."""

    def test_doctor_completes_quickly(self):
        """Test that doctor completes in reasonable time."""
        import time

        start = time.time()
        result = subprocess.run(
            ["mem8", "doctor", "--json"],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=10  # Should complete within 10 seconds
        )
        duration = time.time() - start

        assert result.returncode in [0, 1]
        assert duration < 10, f"Doctor took too long: {duration}s"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
