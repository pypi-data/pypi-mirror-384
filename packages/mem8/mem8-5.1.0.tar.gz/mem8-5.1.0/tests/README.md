mem8 Thoughts Test Harness

- Cross-platform fixtures create isolated temp git repos and config/data dirs.
- Env overrides ensure tests do not touch user home:
  - `MEM8_CONFIG_DIR`, `MEM8_DATA_DIR` are set per-test
  - `MEM8_DISABLE_HOME_SHORTCUT=1` prevents `~/.mem8` links

Quick runs

- Run all tests: `pytest -q`
- Thought discovery only: `pytest -q tests/test_thoughts_discovery.py`
- Interactive init minimal path: `pytest -q tests/test_init_interactive.py`

Notes

- Tests that need git skip when `git` is not available.
- Windows symlink creation may fallback to a real directory; assertions only require `thoughts/shared` to exist (link or directory).
