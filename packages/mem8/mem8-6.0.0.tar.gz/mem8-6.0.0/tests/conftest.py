"""
Pytest configuration and fixtures for mem8 tests.
Adds cross-platform, isolated test harness utilities for mocked repos.
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Callable, Dict

import pytest

# Add the parent directory to sys.path so we can import mem8
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(autouse=True)
def isolate_mem8_env(tmp_path, monkeypatch):
    """Isolate mem8 config/data and disable home shortcut side-effects.

    - Config dir:   MEM8_CONFIG_DIR=<tmp>/.mem8-config
    - Data dir:     MEM8_DATA_DIR=<tmp>/.mem8-data
    - Disable link: MEM8_DISABLE_HOME_SHORTCUT=1
    """
    config_dir = tmp_path / ".mem8-config"
    data_dir = tmp_path / ".mem8-data"
    config_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setenv("MEM8_CONFIG_DIR", str(config_dir))
    monkeypatch.setenv("MEM8_DATA_DIR", str(data_dir))
    monkeypatch.setenv("MEM8_DISABLE_HOME_SHORTCUT", "1")


@pytest.fixture
def temp_workspace(tmp_path) -> Dict[str, Path]:
    """Create a temporary workspace and shared folder for tests."""
    workspace = tmp_path / "workspace"
    shared = tmp_path / "shared"
    workspace.mkdir()
    shared.mkdir()
    return {"workspace": workspace, "shared": shared, "tmp_path": tmp_path}


@pytest.fixture
def git_available() -> bool:
    """Check if git is available; used by tests to skip when missing."""
    try:
        subprocess.run(["git", "--version"], check=True, capture_output=True)
        return True
    except Exception:
        return False


def _init_git_repo(path: Path):
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)
    # Configure minimal identity for commits
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=path, check=True)
    # Initial commit
    (path / "README.md").write_text("# Test Repo\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=path, check=True, capture_output=True)


@pytest.fixture
def make_repo(tmp_path) -> Callable[..., Path]:
    """Factory to create a mock git repo with optional memory content.

    Usage: repo_path = make_repo(name="repo1", with_memory=True)
    """

    def _factory(name: str = "repo", with_memory: bool = True, files: int = 2) -> Path:
        repo = tmp_path / name
        _init_git_repo(repo)
        if with_memory:
            memory = repo / "memory"
            (memory / "shared").mkdir(parents=True, exist_ok=True)
            for i in range(files):
                (memory / f"file_{i+1}.md").write_text(
                    f"# Thought {i+1}\n\nSome content.", encoding="utf-8"
                )
        return repo

    return _factory


@pytest.fixture
def chdir():
    """Context-style fixture to change directories within a test."""
    original = Path.cwd()

    def _cd(path: Path):
        nonlocal original
        os.chdir(path)

    yield _cd
    os.chdir(original)
