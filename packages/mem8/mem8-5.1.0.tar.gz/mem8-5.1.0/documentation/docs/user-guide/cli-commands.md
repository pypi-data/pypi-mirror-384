---
sidebar_position: 2
---

# CLI Commands

Complete reference for all mem8 CLI commands.

## Initialize

### `mem8 init`

Initialize a new mem8 workspace.

```bash
# Interactive mode
mem8 init

# With external templates
mem8 init --template-source killerapp/mem8-plugin

# Non-interactive
mem8 init --template full --force --non-interactive
```

**Options:**
- `--template` - Template type: `full`, `claude-config`, `thoughts-repo`
- `--template-source` - GitHub repo or local path for templates
- `--force` - Overwrite existing files
- `--non-interactive` - Skip all prompts

## Search

### `mem8 search`

Search through your thoughts and documentation.

```bash
# Basic search
mem8 search "authentication"

# With filters
mem8 search "OAuth" --limit 5 --path memory/shared/research
```

**Options:**
- `--limit` - Maximum number of results (default: 10)
- `--path` - Search only in specific directory
- `--category` - Filter by category: `plans`, `research`, `decisions`, `shared`
- `--method` - Search method: `fulltext`, `semantic`

## Status

### `mem8 status`

Check workspace health and configuration.

```bash
# Quick status
mem8 status

# Detailed view
mem8 status --detailed
```

**Shows:**
- ✅ Installed components (.claude, thoughts)
- 📊 Thought statistics
- 🔗 Git repository status
- ⚠️ Issues and warnings

## Sync

### `mem8 sync`

Synchronize thoughts with remote repository.

```bash
# Two-way sync
mem8 sync

# Push only
mem8 sync --direction push

# Pull only
mem8 sync --direction pull

# Preview changes
mem8 sync --dry-run
```

**Options:**
- `--direction` - Sync direction: `push`, `pull`, `both`
- `--dry-run` - Show what would happen without making changes
- `--force` - Override local changes

## Doctor

### `mem8 doctor`

Run diagnostics and fix common issues.

```bash
# Check for issues
mem8 doctor

# Auto-fix problems
mem8 doctor --fix
```

**Checks:**
- Directory structure
- `.mem8/toolbelt.json` manifest (core tooling availability)
- Git configuration
- Template integrity
- Dependencies

When a project template ships a `.mem8/toolbelt.json` manifest, `mem8 doctor` reads it to verify that required CLI tools are on your `PATH` for the current operating system. Missing core tools are flagged as issues, while recommended tools appear as actionable suggestions.

## Templates

### `mem8 templates`

Manage template sources.

```bash
# List available templates
mem8 templates list

# Set default template source
mem8 templates set-default killerapp/mem8-plugin

# Show current default
mem8 templates show-default
```

## Tools

### `mem8 tools`

List toolbelt CLI tools and OS details for AI system prompts.

```bash
# List tools
mem8 tools

# Save toolbelt to .mem8/tools.md
mem8 tools --save
```

**Options:**
- `--save` - Save toolbelt to `.mem8/tools.md`
- `--verbose` - Enable verbose output

## Ports

### `mem8 ports`

Manage project port assignments to prevent conflicts across projects.

```bash
# Show current project's port assignments
mem8 ports --show

# Lease new ports for this project
mem8 ports --lease

# Release this project's port lease
mem8 ports --release

# List all port leases across all projects
mem8 ports --list-all

# Check for port conflicts
mem8 ports --check-conflicts

# Kill process using specified port
mem8 ports --kill 8080
```

**Options:**
- `--lease` - Lease new ports for this project
- `--start` - Starting port number (auto-assign if not specified)
- `--count` - Number of ports to lease
- `--release` - Release this project's port lease
- `--list-all` - List all port leases across all projects
- `--check-conflicts` - Check for port conflicts
- `--kill` - Kill process using specified port
- `--force` - Force kill port outside project range
- `--show` - Show current project's port assignments
- `--verbose` - Enable verbose output

## Version

### `mem8 version`

Show version information.

```bash
mem8 version
```

## Help

### `mem8 --help`

Show help for any command.

```bash
# General help
mem8 --help

# Command-specific help
mem8 search --help
mem8 init --help
```

## Global Options

All commands support:
- `--verbose` - Show detailed output
- `--quiet` - Minimal output
- `--help` - Show command help
- `--version` - Show version

## Examples

### Daily Workflow

```bash
# Morning: Pull team updates
mem8 sync --direction pull

# Check workspace
mem8 status

# Search for relevant info
mem8 search "authentication" --limit 5

# End of day: Push your changes
mem8 sync --direction push
```

### Project Setup

```bash
# New project
cd my-project
mem8 init --template-source myorg/templates

# Verify setup
mem8 status --detailed
mem8 doctor
```

### Troubleshooting

```bash
# Run diagnostics
mem8 doctor

# Check what's wrong
mem8 status --detailed

# Search for solutions
mem8 search "error message"
```

## Environment Variables

- `MEM8_USERNAME` - Default username for templates
- `MEM8_EMAIL` - Default email for templates
- `MEM8_TEMPLATE_SOURCE` - Default template source
- `MEM8_DEBUG` - Enable debug logging

Example:

```bash
export MEM8_USERNAME=yourname
export MEM8_TEMPLATE_SOURCE=killerapp/mem8-plugin
mem8 init
```

## Configuration File

mem8 looks for configuration in:
- `.mem8/config.yaml` (project-specific)
- `~/.mem8/config.yaml` (global)

Example config:

```yaml
template_source: killerapp/mem8-plugin
username: yourname
sync:
  auto: true
  direction: both
search:
  default_limit: 10
```

## Exit Codes

- `0` - Success
- `1` - General error
- `2` - Configuration error
- `3` - Network error
- `4` - Permission error

## Next Steps

- **[Workflows](./workflows)** - Common development patterns
- **[Getting Started](./getting-started)** - Your first steps
- **[Troubleshooting](./troubleshooting)** - Solve common issues