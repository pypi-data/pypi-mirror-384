#!/usr/bin/env python3
"""
Tests for memory discovery behavior in single-repo and multi-repo setups.
"""


import pytest

from mem8.core.config import Config
from mem8.core.thought_discovery import ThoughtDiscoveryService


@pytest.mark.unit
def test_discover_single_repo_only(tmp_path, make_repo, chdir):
    # Create one repo with memory
    repo = make_repo(name="repo-single", with_memory=True, files=3)
    # Add a nested thought file
    nested = repo / "memory" / "research" / "topic.md"
    nested.parent.mkdir(parents=True, exist_ok=True)
    nested.write_text("# Nested Research\n\nLinks to [other](file_1.md)", encoding="utf-8")

    # Run discovery from within the repo
    chdir(repo)
    config = Config()
    svc = ThoughtDiscoveryService(config)
    entities = svc.discover_all_memory(force_rescan=True)

    # Expect at least 4 memory (3 root files + 1 nested)
    assert len(entities) >= 4
    # All paths should be under this repo's memory directory
    for e in entities:
        assert str(repo / "memory") in str(e.path)


@pytest.mark.unit
def test_discover_across_sibling_repos(tmp_path, make_repo, chdir, git_available):
    if not git_available:
        pytest.skip("git not available in test environment")

    # Create a shared parent with two sibling repos
    parent = tmp_path / "projects"
    parent.mkdir()
    repo1 = make_repo(name="projects/repo1", with_memory=True, files=1)
    repo2 = make_repo(name="projects/repo2", with_memory=True, files=1)

    # Add distinctive files to repo2
    (repo2 / "memory" / "special.md").write_text("# Unique in repo2", encoding="utf-8")

    # Run discovery from repo1
    chdir(repo1)
    config = Config()
    # Enable cross-repo discovery for this test case
    config.set('discovery.cross_repo', True)
    svc = ThoughtDiscoveryService(config)
    entities = svc.discover_all_memory(force_rescan=True)

    # Should find entities from both repos
    paths = [str(e.path) for e in entities]
    assert any(str(repo1 / "memory") in p for p in paths)
    assert any(str(repo2 / "memory") in p for p in paths)
