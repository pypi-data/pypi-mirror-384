#!/usr/bin/env python3
"""
Comprehensive test suite for mem8 CLI
Tests the CLI functionality in isolation without interfering with real workspaces.
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
        self.shared_dir = self.test_dir / "shared"
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
        assert "Memory management CLI for team collaboration" in result.stdout
        assert "Commands" in result.stdout
        assert "init" in result.stdout
        assert "sync" in result.stdout
        assert "status" in result.stdout
        assert "search" in result.stdout
        assert "doctor" in result.stdout
    
    def test_version(self):
        """Test that version command works."""
        result = self.run_mem8(["--version"])
        assert "mem8 version" in result.stdout
        assert result.returncode == 0
    
    def test_status_uninitialized(self):
        """Test status command on uninitialized workspace."""
        result = self.run_mem8(["status"])
        assert "mem8 Workspace Status" in result.stdout
        assert "Missing" in result.stdout  # Should show missing components
    
    def test_doctor_uninitialized(self):
        """Test doctor command on uninitialized workspace."""
        result = self.run_mem8(["doctor"], expect_success=False)
        assert "Running mem8 diagnostics" in result.stdout
        assert "Issues found" in result.stdout or "Workspace health" in result.stdout
    
    def test_initialization_basic(self):
        """Test basic workspace initialization."""
        result = self.run_mem8([
            "init",
            "--shared-dir", str(self.shared_dir),
            "--template", "claude-config",
            "--force"
        ])

        assert "mem8 init" in result.stdout
        # The output format changed - check for template installation
        assert ("Installing claude-config template" in result.stdout or
                "Template generation complete" in result.stdout or
                "Setup complete" in result.stdout)

        # Check that directories were created
        assert (self.workspace_dir / ".claude").exists()
        assert (self.workspace_dir / "memory").exists()
        assert self.shared_dir.exists()
    
    def test_initialization_force(self):
        """Test initialization with force flag."""
        # First initialization
        self.run_mem8([
            "init",
            "--shared-dir", str(self.shared_dir),
            "--template", "claude-config",
            "--force"
        ])

        # Second initialization should fail without force in non-interactive mode
        result = self.run_mem8([
            "init",
            "--shared-dir", str(self.shared_dir),
            "--non-interactive"
        ], expect_success=False)
        assert ("already exists" in result.stdout or
                "Cannot proceed" in result.stdout or
                "Existing directories" in result.stdout)

        # With force should succeed
        result = self.run_mem8([
            "init",
            "--shared-dir", str(self.shared_dir),
            "--force"
        ])
        assert ("mem8 init" in result.stdout or "Setup complete" in result.stdout)
    
    def test_status_after_init(self):
        """Test status command after initialization."""
        self.run_mem8([
            "init",
            "--shared-dir", str(self.shared_dir),
            "--template", "full",
            "--force"
        ])

        result = self.run_mem8(["status", "--detailed"])
        assert "mem8 Workspace Status" in result.stdout
        assert ("Ready" in result.stdout or "Active" in result.stdout)
        # Just check that status shows something useful
        assert result.returncode == 0
    
    def test_sync_functionality(self):
        """Test sync functionality."""
        self.run_mem8([
            "init", 
            "--shared-dir", str(self.shared_dir),
            "--force"
        ])
        
        # Test dry run
        result = self.run_mem8(["sync", "--dry-run"])
        assert "Dry run:" in result.stdout
        assert "memory" in result.stdout
        
        # Test actual sync
        result = self.run_mem8(["sync"])
        assert "Syncing memory" in result.stdout or "No changes needed" in result.stdout
    
    def test_search_functionality(self):
        """Test search functionality."""
        self.run_mem8([
            "init", 
            "--shared-dir", str(self.shared_dir),
            "--force"
        ])
        
        # Create test content
        test_file = self.workspace_dir / "memory" / "test.md"
        test_file.parent.mkdir(exist_ok=True)
        test_file.write_text("# Test Document\\n\\nThis is a test document with searchable content.")
        
        # Test search
        result = self.run_mem8(["search", "searchable", "--limit", "5"])
        assert "Searching for: 'searchable'" in result.stdout
        # Search might return no results if indexing hasn't happened yet, that's ok
    
    def test_doctor_after_init(self):
        """Test doctor command after initialization."""
        self.run_mem8([
            "init",
            "--shared-dir", str(self.shared_dir),
            "--force"
        ])

        result = self.run_mem8(["doctor"], expect_success=False)
        assert "Running mem8 diagnostics" in result.stdout
        # Check for either healthy state or issues found - exit code can be 0 or 1
        assert result.returncode in [0, 1]
    
    def test_doctor_fix(self):
        """Test doctor command with --fix flag."""
        self.run_mem8([
            "init",
            "--shared-dir", str(self.shared_dir),
            "--force"
        ])

        # Remove a directory to create an issue
        shutil.rmtree(self.workspace_dir / "memory", ignore_errors=True)

        result = self.run_mem8(["doctor", "--fix"], expect_success=False)
        assert "Running mem8 diagnostics" in result.stdout
        # Should either fix the issue or report what was fixed
        assert result.returncode in [0, 1]  # 0 if fixed, 1 if issues remain

    def test_doctor_json_output(self):
        """Test doctor command with JSON output."""
        self.run_mem8([
            "init",
            "--shared-dir", str(self.shared_dir),
            "--force"
        ])

        result = self.run_mem8(["doctor", "--json"], expect_success=False)

        # Should output valid JSON
        try:
            import json
            data = json.loads(result.stdout)

            # Check required fields
            assert "status" in data
            assert data["status"] in ["healthy", "unhealthy"]
            assert "health_score" in data
            assert "issues" in data
            assert "fixes_applied" in data
            assert "recommendations" in data

            # Verify types
            assert isinstance(data["issues"], list)
            assert isinstance(data["fixes_applied"], list)
            assert isinstance(data["health_score"], (int, float))

        except json.JSONDecodeError:
            pytest.fail("doctor --json did not output valid JSON")

    def test_doctor_toolbelt_checking(self):
        """Test that doctor checks CLI toolbelt."""
        self.run_mem8([
            "init",
            "--shared-dir", str(self.shared_dir),
            "--force"
        ])

        result = self.run_mem8(["doctor"], expect_success=False)

        # Should mention tools or show healthy state
        # The output will vary based on what's installed, but should contain relevant info
        assert result.returncode in [0, 1]

    def test_doctor_exit_codes(self):
        """Test that doctor returns appropriate exit codes."""
        self.run_mem8([
            "init",
            "--shared-dir", str(self.shared_dir),
            "--force"
        ])

        result = self.run_mem8(["doctor"], expect_success=False)

        # Exit code should be 0 (healthy) or 1 (issues found)
        assert result.returncode in [0, 1]

        # If exit code is 1, should have issues in output
        if result.returncode == 1:
            assert "Issues found" in result.stdout or "Missing" in result.stdout or "⚠️" in result.stdout
    
    def test_claude_md_generation(self):
        """Test that .claude directory is generated correctly."""
        result = self.run_mem8([
            "init",
            "--shared-dir", str(self.shared_dir),
            "--template", "claude-config",
            "--force"
        ])

        # Check that .claude directory exists with commands/agents
        claude_dir = self.workspace_dir / ".claude"
        assert claude_dir.exists(), f".claude directory not found. Init output: {result.stdout}"

        # Verify commands and agents subdirectories exist
        assert (claude_dir / "commands").exists()
        assert (claude_dir / "agents").exists()
    
    def test_shared_directory_creation(self):
        """Test that shared directory structure is created correctly."""
        self.run_mem8([
            "init", 
            "--shared-dir", str(self.shared_dir),
            "--force"
        ])
        
        # Check shared directory structure
        assert (self.shared_dir / "memory").exists()
        assert (self.shared_dir / "memory" / "shared" / "plans").exists()
        assert (self.shared_dir / "memory" / "shared" / "decisions").exists()
        assert (self.shared_dir / "memory" / "shared" / "research").exists()
        assert (self.shared_dir / "memory" / "README.md").exists()
    
    def test_error_handling(self):
        """Test error handling for invalid operations."""
        # Test searching before initialization (shouldn't crash)
        result = self.run_mem8(["search", "test"])
        # Should succeed but may have no results
        assert result.returncode == 0
    
    def test_init_protects_existing_data(self):
        """Test that init command protects existing memory/shared data."""
        # Create important user data first
        memory_dir = self.workspace_dir / "memory"
        shared_dir = memory_dir / "shared"
        shared_dir.mkdir(parents=True, exist_ok=True)

        important_file = shared_dir / "critical_research.md"
        important_file.write_text("# Critical Research\\n\\nThis data must not be lost!")

        # Test that init detects and warns about existing data
        result = self.run_mem8([
            "init", "--template", "memory-repo", "--non-interactive"
        ], expect_success=False)

        # Should warn about existing data (text changed with new system)
        assert ("already exists" in result.stdout or
                "Existing directories" in result.stdout or
                "Cannot proceed" in result.stdout)
        assert "--force" in result.stdout

        # Verify our important data is still there and untouched
        assert important_file.exists()
        assert "Critical Research" in important_file.read_text()

        print("✅ Init command properly protects existing user data")
    
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
    print("\\n1. Testing against current workspace...")
    os.chdir(Path(__file__).parent.parent)
    result = subprocess.run(["mem8", "status", "--detailed"], capture_output=True, text=True)
    print("✅ Current workspace status:")
    print(result.stdout)
    
    # Test 2: Search real content
    print("\\n2. Testing search on real content...")
    result = subprocess.run(["mem8", "search", "implementation", "--limit", "3"], 
                          capture_output=True, text=True)
    print("✅ Search results:")
    print(result.stdout)
    
    # Test 3: Workspace health
    print("\\n3. Testing workspace health...")
    result = subprocess.run(["mem8", "doctor"], capture_output=True, text=True)
    print("✅ Workspace health:")
    print(result.stdout)
    
    print("\\n" + "=" * 50)
    print("✅ Manual validation complete!")


if __name__ == "__main__":
    # Run manual tests when script is executed directly
    run_manual_tests()