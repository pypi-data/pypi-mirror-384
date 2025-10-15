# Mem8 Project Overview

This document provides a high-level overview of the Mem8 project and key information for developers.

## About Mem8

Mem8 is a tool designed to augment developer workflows by providing a persistent memory layer and a suite of CLI commands to interact with it. It integrates with various tools and platforms to streamline development tasks.

## Development Environment

The Mem8 project is a monorepo containing the CLI, a frontend, a backend, and documentation.

- **Frontend/Backend**: The frontend and backend are containerized using Docker. Use the instructions in `DOCKER.md` to set up the services with hot-reloading for development.
- **Documentation**: The `documentation` directory contains a Docusaurus instance. This is the source of truth for all project documentation. Make sure to keep it updated.

## CLI Development with `uv`

**CRITICAL**: This project uses `uv` for all Python dependency and environment management. Do not use `pip`, `venv`, or `python` directly.

To work on the `mem8` CLI, you must install it in editable mode. This ensures that your changes are immediately reflected and that you are testing the CLI in a way that mirrors the end-user experience.

```bash
# 1. Install the CLI in editable mode at the start of each session
uv tool install . --editable

# 2. Test CLI commands
mem8 --help
mem8 status

# 3. Re-install after making changes to the CLI's command structure (e.g., in `cli_typer.py`)
uv tool install . --editable
```

### Other `uv` Commands

| Task                  | Command                         | Description                                           |
| --------------------- | ------------------------------- | ----------------------------------------------------- |
| **Install/Sync Deps** | `uv sync`                       | Install/update all dependencies from `pyproject.toml`.|
| **Add Dependency**    | `uv add <package>`              | Add a new runtime dependency.                         |
| **Add Dev Dependency**| `uv add --dev <package>`        | Add a new development dependency.                     |
| **Run Tests**         | `uv run pytest`                 | Execute the test suite.                               |
| **Run Scripts**       | `uv run python <script.py>`     | Run a Python script in the project's environment.     |
| **Type Checking**     | `uv run mypy mem8`              | Run the Mypy type checker.                            |

## Template Management

- The `.claude` directory is generated from the cookiecutter template located in `mem8/templates/claude-dot-md-template`.
- To update agents or commands, **always modify the cookiecutter template**.
- The local `.claude` directory is for testing the `mem8` CLI itself and will be overwritten by the template.
- The `memory` directory is a Git submodule that points to the `killerapp/mem8-memory` repository for shared organizational knowledge.

## Conventional Commits

This project uses conventional commits and `semantic-release` to automate releases. Please follow the conventional commit format for all your commits. This is enforced by the GitHub Action in `.github/workflows/release.yml`.
