#!/usr/bin/env python3
"""
Interactive init tests using minimal prompts to avoid template installation.
"""

import os
import sys
import subprocess
from pathlib import Path

import pytest


@pytest.mark.cli
def test_init_interactive_minimal(tmp_path):
    """Run `mem8 init` (interactive by default) answering with 'none' to skip templates and accept defaults."""
    ws = tmp_path / "ws"
    ws.mkdir()
    os.chdir(ws)

    # Initialize a git repo to avoid extra prompts (skip test if git missing)
    import shutil
    if not shutil.which("git"):
        pytest.skip("git not available in test environment")
    subprocess.run(["git", "init"], check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], check=True)

    # Provide minimal interactive answers for new flow:
    # 1) workflow provider -> none
    # 2) template -> none
    # 3) username -> accept default (blank line)
    # 4) include repos -> n (default)
    # 5) enable shared -> n (default)
    input_text = "none\nnone\n\nn\nn\n"

    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).parent.parent)
    result = subprocess.run(
        [sys.executable, "-m", "mem8.cli", "init"],
        capture_output=True,
        text=True,
        input=input_text,
        env=env,
        encoding="utf-8",
        errors="replace",
    )

    # Should not crash
    assert result.returncode == 0
    # Memory directory should be created
    assert (ws / "memory").exists()
    # Shared should NOT be created when disabled (default)
    assert not (ws / "memory" / "shared").exists()


@pytest.mark.cli
@pytest.mark.skip(reason="Shared memory test needs investigation - may be related to Windows junction handling")
def test_init_with_shared_enabled(tmp_path):
    """Test enabling shared memory during init."""
    ws = tmp_path / "ws"
    shared_path = tmp_path / "shared_mem8"
    ws.mkdir()
    shared_path.mkdir()
    os.chdir(ws)

    # Initialize a git repo to avoid extra prompts (skip test if git missing)
    import shutil
    if not shutil.which("git"):
        pytest.skip("git not available in test environment")
    subprocess.run(["git", "init"], check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], check=True)

    # Provide interactive answers for new flow:
    # Since we have a git repo, no git warning prompt
    # 1) workflow provider -> none
    # 2) template -> memory-repo (need this for shared functionality)
    # 3) username -> testuser
    # 4) include repos -> n (default)
    # 5) enable shared -> y
    # 6) shared path -> <shared_path>
    input_text = f"none\nmemory-repo\ntestuser\nn\ny\n{shared_path}\n"

    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).parent.parent)
    result = subprocess.run(
        [sys.executable, "-m", "mem8.cli", "init"],
        capture_output=True,
        text=True,
        input=input_text,
        env=env,
        encoding="utf-8",
        errors="replace",
    )

    # Should not crash
    assert result.returncode == 0
    # Memory directory should be created
    assert (ws / "memory").exists()
    # User directory should be created with the provided username
    assert (ws / "memory" / "testuser").exists()
    # Shared link should be created (could be symlink, junction, or directory on Windows)
    shared_path_obj = ws / "memory" / "shared"
    # Check multiple ways since Windows junctions behave differently
    assert shared_path_obj.exists() or shared_path_obj.is_dir() or shared_path_obj.is_symlink()
    # Shared memory root should be created
    assert (shared_path / "memory").exists()
    # Verify subdirectories were created
    assert (shared_path / "memory" / "shared" / "decisions").exists()
    assert (shared_path / "memory" / "shared" / "plans").exists()

    # Check that output includes link type information
    output = result.stdout + result.stderr
    # Should mention junction on Windows or symlink on Unix
    import platform
    if platform.system().lower() == 'windows':
        # Could be junction or fallback directory
        assert any(term in output.lower() for term in ['junction', 'directory', 'fallback'])
    else:
        assert 'symbolic link' in output.lower() or 'symlink' in output.lower()
