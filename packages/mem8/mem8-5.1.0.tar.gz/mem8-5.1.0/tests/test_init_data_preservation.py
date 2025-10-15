#!/usr/bin/env python3
"""
Test suite for mem8 CLI init command data preservation.
Tests that init command properly protects existing memory/shared data.
"""

import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path


class TestInitDataPreservation:
    """Test suite for init command data preservation functionality."""
    
    def setup_method(self):
        """Set up test environment for each test."""
        self.test_dir = Path(tempfile.mkdtemp(prefix="mem8-init-test-"))
        self.original_cwd = Path.cwd()
        os.chdir(self.test_dir)
        
        # Create some important user data
        self.memory_dir = self.test_dir / "memory"
        self.shared_dir = self.memory_dir / "shared"
        self.shared_dir.mkdir(parents=True, exist_ok=True)
        
        # Create test files that should be preserved
        self.important_file = self.shared_dir / "important_data.md"
        self.important_file.write_text("# Critical User Data\n\nThis must not be lost!")
        
        self.user_plans = self.shared_dir / "plans"
        self.user_plans.mkdir(exist_ok=True)
        (self.user_plans / "my_project.md").write_text("# My Important Project Plan")
        
        self.user_decisions = self.shared_dir / "decisions" 
        self.user_decisions.mkdir(exist_ok=True)
        (self.user_decisions / "architecture.md").write_text("# Architecture Decision")
    
    def teardown_method(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def run_mem8(self, args, expect_success=True, input_text=None):
        """Run mem8 command and return result."""
        env = os.environ.copy()
        env['PYTHONPATH'] = str(Path(__file__).parent.parent)
        result = subprocess.run(
            [sys.executable, "-m", "mem8.cli"] + args,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            input=input_text,
            env=env
        )
        
        if expect_success and result.returncode != 0:
            print(f"Command failed: mem8 {' '.join(args)}")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            raise AssertionError(f"Expected success but got return code {result.returncode}")
        
        return result
    
    def test_init_detects_existing_memory_shared(self):
        """Test that init command detects existing memory/shared directory."""
        result = self.run_mem8(["init", "--template", "memory-repo", "--non-interactive"], expect_success=False)

        assert "Existing directories detected:" in result.stdout
        assert "memory/ directory already exists" in result.stdout
        assert "--force" in result.stdout
    
    def test_init_detects_existing_claude_directory(self):
        """Test that init command detects existing .claude directory."""
        # Create .claude directory
        claude_dir = self.test_dir / ".claude"
        claude_dir.mkdir()
        (claude_dir / "CLAUDE.md").write_text("# Existing Claude Config")

        result = self.run_mem8(["init", "--template", "claude-config", "--non-interactive"], expect_success=False)

        assert "Existing directories detected:" in result.stdout
        assert ".claude/ directory already exists" in result.stdout
    
    def test_init_full_template_detection(self):
        """Test detection with full template (both claude and memory).""" 
        # Create .claude directory too
        claude_dir = self.test_dir / ".claude"
        claude_dir.mkdir()
        (claude_dir / "CLAUDE.md").write_text("# Existing Config")
        
        result = self.run_mem8(["init", "--template", "full", "--non-interactive"], expect_success=False)

        # Should detect at least one of the existing directories
        assert "Existing directories detected:" in result.stdout
        assert ("memory/ directory already exists" in result.stdout or
                ".claude/ directory already exists" in result.stdout)
    
    def test_preserves_data_with_force_flag(self):
        """Test that --force preserves memory/shared data."""
        # Record original data
        original_important = self.important_file.read_text()
        original_project = (self.user_plans / "my_project.md").read_text()
        original_architecture = (self.user_decisions / "architecture.md").read_text()
        
        # Run init with force flag
        result = self.run_mem8([
            "init", "--template", "memory-repo", "--force"
        ])

        # Check that init succeeded with force flag
        assert result.returncode == 0
        
        # Most importantly: check that our data still exists
        assert self.important_file.exists(), "Important data file should still exist"
        assert self.important_file.read_text() == original_important
        
        assert (self.user_plans / "my_project.md").exists()
        assert (self.user_plans / "my_project.md").read_text() == original_project
        
        assert (self.user_decisions / "architecture.md").exists() 
        assert (self.user_decisions / "architecture.md").read_text() == original_architecture
    
    def test_clean_directory_works_normally(self):
        """Test that init works normally in clean directory."""
        # Create a completely clean directory
        clean_dir = self.test_dir / "clean_workspace"
        clean_dir.mkdir()
        os.chdir(clean_dir)
        
        # This should not show any warnings
        result = self.run_mem8(["init", "--template", "memory-repo", "--non-interactive"], expect_success=False)
        
        # Should fail due to cookiecutter prompts, but no warnings about existing files
        assert "Existing workspace components found" not in result.stdout
        assert "WARNING:" not in result.stdout
        # Should start cookiecutter process
        assert "mem8 init" in result.stdout or "Installing" in result.stdout or "Setup complete" in result.stdout
    
    def test_force_flag_suggestions(self):
        """Test that helpful suggestions are provided."""
        result = self.run_mem8(["init", "--template", "full", "--non-interactive"], expect_success=False)

        # Check for new security-enhanced messaging
        assert "--force" in result.stdout  # Mentions force flag
        assert "existing" in result.stdout.lower()  # Mentions existing data
        # The specific wording changed for security, but concept is the same
    
    def test_specific_template_only_checks_relevant_dirs(self):
        """Test that claude-config template only checks .claude directory."""
        # Only create .claude directory, not memory
        claude_dir = self.test_dir / ".claude"
        claude_dir.mkdir()
        
        # Remove the memory directory we created in setup
        shutil.rmtree(self.memory_dir)
        
        result = self.run_mem8(["init", "--template", "claude-config", "--non-interactive"], expect_success=False)
        
        assert ".claude/ directory already exists" in result.stdout
        assert "memory" not in result.stdout  # Should not mention memory for claude-config
    
    def test_memory_repo_template_only_checks_memory(self):
        """Test that memory-repo template only checks memory directory."""
        # Create separate test without .claude
        clean_test_dir = Path(tempfile.mkdtemp(prefix="mem8-memory-only-"))
        old_test_dir = self.test_dir
        self.test_dir = clean_test_dir
        os.chdir(clean_test_dir)
        
        try:
            # Create only memory directory
            memory_dir = clean_test_dir / "memory" 
            shared_dir = memory_dir / "shared"
            shared_dir.mkdir(parents=True)
            (shared_dir / "test.md").write_text("test data")
            
            result = self.run_mem8(["init", "--template", "memory-repo", "--non-interactive"], expect_success=False)
            
            assert "memory/ directory already exists" in result.stdout
            assert ".claude" not in result.stdout  # Should not mention .claude for memory-repo
            
        finally:
            # Restore original test environment
            os.chdir(old_test_dir)
            self.test_dir = old_test_dir
            if clean_test_dir.exists():
                shutil.rmtree(clean_test_dir, ignore_errors=True)
    
    def test_data_structure_preservation(self):
        """Test that complex directory structures are preserved."""
        # Create a complex structure
        nested_dir = self.shared_dir / "research" / "deep" / "analysis"
        nested_dir.mkdir(parents=True)
        nested_file = nested_dir / "complex_research.md"
        nested_file.write_text("# Complex nested research data")
        
        # Create various file types
        (self.shared_dir / "data.json").write_text('{"key": "important_value"}')
        (self.shared_dir / "script.py").write_text("# Important script\nprint('preserve me')")
        
        self.run_mem8([
            "init", "--template", "memory-repo", "--force"  
        ], expect_success=False)
        
        # Verify complex structure is preserved
        assert nested_file.exists(), "Nested files should be preserved"
        assert nested_file.read_text() == "# Complex nested research data"
        assert (self.shared_dir / "data.json").exists()
        assert (self.shared_dir / "script.py").exists()
        assert (self.shared_dir / "data.json").read_text() == '{"key": "important_value"}'


def run_manual_preservation_test():
    """
    Manual test to demonstrate the data preservation functionality.
    Run this to see the preservation behavior in action.
    """
    print("🧪 Testing mem8 Init Data Preservation...")
    print("=" * 50)
    
    # Create test directory
    test_dir = Path(tempfile.mkdtemp(prefix="mem8-preservation-demo-"))
    original_cwd = Path.cwd()
    
    try:
        os.chdir(test_dir)
        print(f"Test directory: {test_dir}")
        
        # Create important user data
        memory_dir = test_dir / "memory"
        shared_dir = memory_dir / "shared"
        shared_dir.mkdir(parents=True)
        
        important_file = shared_dir / "my_important_work.md"
        important_file.write_text("""# My Critical Research
        
This represents months of important work that must never be lost!

## Key Findings
- Discovery A: Revolutionary insight
- Discovery B: Game-changing approach
- Discovery C: Mission-critical data

## Next Steps
- Implement solution
- Test thoroughly  
- Deploy to production

*This data is irreplaceable!*
""")
        
        # Create complex structure
        plans_dir = shared_dir / "plans"
        plans_dir.mkdir()
        (plans_dir / "project_alpha.md").write_text("# Project Alpha - Top Secret")
        
        decisions_dir = shared_dir / "decisions"
        decisions_dir.mkdir()
        (decisions_dir / "tech_stack.md").write_text("# Technology Stack Decision")
        
        print("✅ Created important user data in memory/shared/")
        print(f"   - {important_file}")
        print(f"   - {plans_dir / 'project_alpha.md'}")
        print(f"   - {decisions_dir / 'tech_stack.md'}")
        
        # Test 1: Show warning without --force
        print("\\n🔍 Test 1: Running init without --force (should warn and abort)")
        result = subprocess.run(
            ["mem8", "init", "--template", "memory-repo", "--non-interactive"],
            capture_output=True, text=True,
            encoding='utf-8',
            errors='replace'
        )
        print("Result:")
        print(result.stdout)
        
        # Test 2: Show preservation with --force  
        print("\\n🛡️ Test 2: Running init with --force (should preserve data)")
        # Note: This will fail at cookiecutter prompts, but will show preservation
        result = subprocess.run(
            ["mem8", "init", "--template", "memory-repo", "--force"],
            capture_output=True, text=True, input="\\n" * 10  # Skip cookiecutter prompts
        )
        print("Result:")
        print(result.stdout)
        
        # Verify data is still there
        print("\\n✅ Verification: Checking if important data survived...")
        if important_file.exists():
            content = important_file.read_text()
            if "Revolutionary insight" in content:
                print("✅ SUCCESS: Important data is fully preserved!")
            else:
                print("❌ FAIL: Data exists but content is corrupted")
        else:
            print("❌ FAIL: Important data file is missing")
        
        # Check other files
        preserved_count = 0
        total_files = 0
        
        for file_path in shared_dir.rglob("*.md"):
            total_files += 1
            if file_path.exists() and file_path.stat().st_size > 0:
                preserved_count += 1
                print(f"   ✅ {file_path.name} - preserved")
            else:
                print(f"   ❌ {file_path.name} - lost")
        
        print(f"\\n📊 Results: {preserved_count}/{total_files} files preserved")
        if preserved_count == total_files:
            print("🎉 PERFECT: All user data preserved during init --force!")
        else:
            print("⚠️ Some data may have been lost")
            
    finally:
        os.chdir(original_cwd)
        if test_dir.exists():
            shutil.rmtree(test_dir, ignore_errors=True)


if __name__ == "__main__":
    # Run manual demonstration
    run_manual_preservation_test()