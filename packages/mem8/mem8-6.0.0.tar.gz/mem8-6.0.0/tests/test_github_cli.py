#!/usr/bin/env python3
"""Smoke tests for mem8 gh helpers.

These tests do not require an actual GitHub login; they validate that the
command runs and produces a sensible message in both cases.
"""

import os
import sys
import subprocess


def run_mem8(args):
    env = os.environ.copy()
    env['PYTHONPATH'] = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    return subprocess.run(
        [sys.executable, "-m", "mem8.cli"] + args,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )


def test_gh_whoami_smoke():
    res = run_mem8(["gh", "whoami"])  # no host, defaults to github.com
    assert res.returncode == 0
    out = res.stdout.lower()
    # Either shows logged-in user or a helpful not-detected message
    assert ("logged in to" in out) or ("gh not detected" in out)

