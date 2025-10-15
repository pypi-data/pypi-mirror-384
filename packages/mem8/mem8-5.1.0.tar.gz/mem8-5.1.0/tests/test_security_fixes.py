"""Security tests for mem8 CLI hardening."""

import pytest
from mem8.core.memory import MemoryManager
from mem8.core.config import Config
from mem8.core.worktree import _validate_branch_name


class TestPathTraversalProtection:
    """Test path traversal protection in search_content."""

    def test_rejects_double_dot_traversal(self, tmp_path):
        """Should reject path filters with .. pattern."""
        config = Config()
        memory = MemoryManager(config)

        with pytest.raises(ValueError, match="path traversal detected"):
            memory.search_content("query", path_filter="../../../etc")

    def test_rejects_absolute_unix_paths(self, tmp_path):
        """Should reject absolute Unix paths."""
        config = Config()
        memory = MemoryManager(config)

        with pytest.raises(ValueError, match="absolute paths not allowed"):
            memory.search_content("query", path_filter="/etc/passwd")

    def test_rejects_absolute_windows_paths(self, tmp_path):
        """Should reject absolute Windows paths."""
        config = Config()
        memory = MemoryManager(config)

        with pytest.raises(ValueError, match="absolute paths not allowed"):
            memory.search_content("query", path_filter="C:/Windows")

    def test_allows_relative_paths(self, tmp_path):
        """Should allow valid relative paths."""
        config = Config()
        memory = MemoryManager(config)

        # This should not raise (though search may return no results)
        result = memory.search_content("query", path_filter="shared/plans")
        assert result is not None


class TestBranchNameValidation:
    """Test branch name validation in worktree creation."""

    def test_rejects_command_injection_semicolon(self):
        """Should reject branch names with semicolons."""
        with pytest.raises(ValueError, match="dangerous character"):
            _validate_branch_name("main; rm -rf /")

    def test_rejects_command_injection_pipe(self):
        """Should reject branch names with pipe."""
        with pytest.raises(ValueError, match="dangerous character"):
            _validate_branch_name("main | cat /etc/passwd")

    def test_rejects_command_injection_backtick(self):
        """Should reject branch names with backticks."""
        with pytest.raises(ValueError, match="dangerous character"):
            _validate_branch_name("main`whoami`")

    def test_rejects_path_traversal(self):
        """Should reject branch names with path traversal."""
        with pytest.raises(ValueError, match="path traversal"):
            _validate_branch_name("../../bad-branch")

    def test_rejects_absolute_paths(self):
        """Should reject absolute paths as branch names."""
        with pytest.raises(ValueError, match="absolute path"):
            _validate_branch_name("/etc/passwd")

    def test_rejects_invalid_git_refs(self):
        """Should reject invalid git ref patterns."""
        # Branch starting with dot
        with pytest.raises(ValueError, match="git ref naming rules"):
            _validate_branch_name(".hidden")

        # Branch ending with .lock
        with pytest.raises(ValueError, match="git ref naming rules"):
            _validate_branch_name("branch.lock")

        # Branch with @{
        with pytest.raises(ValueError, match="git ref naming rules"):
            _validate_branch_name("branch@{1}")

    def test_allows_valid_branch_names(self):
        """Should allow valid branch names."""
        # These should not raise
        _validate_branch_name("feature/ticket-123")
        _validate_branch_name("fix-bug-456")
        _validate_branch_name("main")
        _validate_branch_name("develop")
        _validate_branch_name("release/v1.2.3")


class TestSymlinkSafety:
    """Test symlink creation safety."""

    def test_symlink_without_force_skips_existing(self, tmp_path):
        """Should not replace existing symlink without force flag."""
        from mem8.core.utils import create_symlink

        target = tmp_path / "target"
        target.mkdir()

        link = tmp_path / "link"
        link.symlink_to(target)

        # Try to create symlink again without force
        result = create_symlink(target, link, force=False)
        assert result is False  # Should fail to replace

    def test_symlink_with_force_replaces_existing(self, tmp_path):
        """Should replace existing symlink with force flag."""
        from mem8.core.utils import create_symlink

        target1 = tmp_path / "target1"
        target1.mkdir()

        target2 = tmp_path / "target2"
        target2.mkdir()

        link = tmp_path / "link"
        link.symlink_to(target1)

        # Try to create symlink again with force
        result = create_symlink(target2, link, force=True)
        assert result is True  # Should succeed

        # Verify link now points to target2
        assert link.resolve() == target2.resolve()

    def test_symlink_never_overwrites_real_directory(self, tmp_path):
        """Should never overwrite real directories."""
        from mem8.core.utils import create_symlink

        target = tmp_path / "target"
        target.mkdir()

        existing_dir = tmp_path / "existing"
        existing_dir.mkdir()

        # Try to create symlink over real directory (even with force)
        result = create_symlink(target, existing_dir, force=True)
        assert result is False  # Should fail

        # Verify directory still exists and is not a symlink
        assert existing_dir.exists()
        assert existing_dir.is_dir()
        assert not existing_dir.is_symlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
