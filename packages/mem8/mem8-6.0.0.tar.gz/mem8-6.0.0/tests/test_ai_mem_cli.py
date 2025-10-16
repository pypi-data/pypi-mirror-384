#!/usr/bin/env python3
"""
Basic test suite for mem8 CLI
Tests core CLI functionality without template/init dependencies.
"""

import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path
import pytest


class Testmem8CLI:
    """Test suite for mem8 CLI functionality."""

    def setup_method(self):
        """Set up test environment for each test."""
        self.test_dir = Path(tempfile.mkdtemp(prefix="mem8-test-"))
        self.workspace_dir = self.test_dir / "workspace"

        # Create workspace directory and initialize git
        self.workspace_dir.mkdir(parents=True)
        os.chdir(self.workspace_dir)

        # Initialize git repository
        subprocess.run(["git", "init"], check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], check=True)

        # Create initial commit
        (self.workspace_dir / "README.md").write_text("# Test Project")
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], check=True)

    def teardown_method(self):
        """Clean up test environment."""
        os.chdir(Path.home())
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def run_mem8(self, args, expect_success=True):
        """Run mem8 command and return result."""
        env = os.environ.copy()
        env['PYTHONPATH'] = str(Path(__file__).parent.parent.parent)
        result = subprocess.run(
            [sys.executable, "-m", "mem8.cli"] + args,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            env=env
        )

        if expect_success and result.returncode != 0:
            print(f"Command failed: mem8 {' '.join(args)}")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            raise AssertionError(f"Expected success but got return code {result.returncode}")

        return result

    def test_cli_help(self):
        """Test that CLI help works."""
        result = self.run_mem8(["--help"])
        assert "Memory management CLI" in result.stdout or "mem8" in result.stdout
        assert "Commands" in result.stdout
        assert "sync" in result.stdout
        assert "status" in result.stdout
        assert "search" in result.stdout
        assert "doctor" in result.stdout

    def test_version(self):
        """Test that version command works."""
        result = self.run_mem8(["--version"])
        assert "mem8 version" in result.stdout or "mem8" in result.stdout
        assert result.returncode == 0

    def test_status_uninitialized(self):
        """Test status command on uninitialized workspace."""
        result = self.run_mem8(["status"])
        assert "mem8 Workspace Status" in result.stdout or "Workspace" in result.stdout
        # Should show missing components or status info
        assert result.returncode == 0

    def test_doctor_uninitialized(self):
        """Test doctor command on uninitialized workspace."""
        result = self.run_mem8(["doctor"], expect_success=False)
        assert "Running mem8 diagnostics" in result.stdout or "diagnostics" in result.stdout
        # Exit code can be 0 (healthy) or 1 (issues found)
        assert result.returncode in [0, 1]

    def test_error_handling(self):
        """Test error handling for invalid operations."""
        # Test searching without memory directory (shouldn't crash)
        result = self.run_mem8(["search", "test"])
        # Should succeed but may have no results
        assert result.returncode == 0

    def test_unicode_support(self):
        """Test that Unicode characters are handled properly."""
        # This test validates our UTF-8 encoding fixes
        result = self.run_mem8(["--help"])
        # Should not crash with encoding errors
        assert result.returncode == 0
        assert len(result.stdout) > 0


def run_manual_tests():
    """
    Run manual validation tests that require human verification.
    These tests validate real-world scenarios.
    """
    print("🧪 Running manual validation tests...")
    print("=" * 50)

    # Test 1: Validate against current workspace
    print("\n1. Testing against current workspace...")
    os.chdir(Path(__file__).parent.parent)
    result = subprocess.run(["mem8", "status", "--detailed"], capture_output=True, text=True)
    print("✅ Current workspace status:")
    print(result.stdout)

    # Test 2: Search real content
    print("\n2. Testing search on real content...")
    result = subprocess.run(["mem8", "search", "implementation", "--limit", "3"],
                          capture_output=True, text=True)
    print("✅ Search results:")
    print(result.stdout)

    # Test 3: Workspace health
    print("\n3. Testing workspace health...")
    result = subprocess.run(["mem8", "doctor"], capture_output=True, text=True)
    print("✅ Workspace health:")
    print(result.stdout)

    print("\n" + "=" * 50)
    print("✅ Manual validation complete!")


if __name__ == "__main__":
    # Run manual tests when script is executed directly
    run_manual_tests()
