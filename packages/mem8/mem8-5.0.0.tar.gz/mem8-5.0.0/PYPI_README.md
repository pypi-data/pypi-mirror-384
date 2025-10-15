# mem8

Context management toolkit for AI-assisted development. Manage memory, templates, and workflows with Claude Code and other AI tools.

## Quick Start

```bash
# Install
uv tool install mem8

# Initialize workspace
cd your-project
mem8 init

# Check status
mem8 status
```

## Core Features

### 🧠 Context Window Management
Persistent memory system for Claude Code with structured documentation. Keep AI context focused and relevant across long development sessions.

```bash
# Search your memory
mem8 search "authentication"

# Use Claude Code commands
/m8-research "payment system"
/m8-plan "add OAuth support"
/m8-implement memory/shared/plans/oauth.md
/m8-commit
```

### 🔧 Toolbelt Integration
Verify and manage CLI tools required for AI workflows.

```bash
# Check for missing tools
mem8 doctor

# Auto-install missing tools
mem8 doctor --fix

# List all tools and versions
mem8 tools
```

Verified tools include: `ripgrep`, `fd`, `jq`, `gh`, `git`, `bat`, `delta`, `ast-grep`, and more.

### 🚢 Port Management
Global port leasing system prevents conflicts across projects.

```bash
# Lease port range for project
mem8 ports --lease

# View assigned ports
mem8 ports

# Kill process on port (safe mode)
mem8 ports --kill 20000
```

### 🎨 External Templates
Share standardized configurations across teams using GitHub templates.

```bash
# Use official templates
mem8 init --template-source killerapp/mem8-plugin

# Use team templates
mem8 init --template-source your-org/templates

# Set default for all projects
mem8 templates set-default your-org/templates
```

### 🤖 Claude Code Integration
Custom commands and agents for enhanced AI workflows.

Commands installed by default:
- `/m8-research` - Parallel codebase exploration
- `/m8-plan` - Structured implementation planning
- `/m8-implement` - Execute plans with progress tracking
- `/m8-validate` - Verify implementation completeness
- `/m8-commit` - Create semantic commits
- `/m8-describe-pr` - Generate PR descriptions

## Documentation

**📚 Full documentation at [codebasecontext.org](https://codebasecontext.org)**

- [Getting Started](https://codebasecontext.org/docs/user-guide/getting-started)
- [CLI Commands](https://codebasecontext.org/docs/user-guide/cli-commands)
- [External Templates](https://codebasecontext.org/docs/external-templates)
- [Contributing](https://codebasecontext.org/docs/contributing)

## Development Workflow

mem8 provides a structured development cycle:

1. **Research** (`/m8-research`) - Understand existing patterns
2. **Plan** (`/m8-plan`) - Design with concrete steps
3. **Implement** (`/m8-implement`) - Execute with progress tracking
4. **Validate** (`/m8-validate`) - Verify completeness
5. **Commit** (`/m8-commit`) - Create semantic commits

## Project Structure

After running `mem8 init --template full`:

```
your-project/
├── .claude/
│   ├── commands/          # Custom slash commands
│   └── agents/           # Custom agent definitions
├── memory/
│   └── shared/
│       ├── research/     # Research documents
│       ├── plans/        # Implementation plans
│       ├── prs/         # PR descriptions
│       └── decisions/    # Technical decisions
└── .mem8/
    ├── config.yaml      # Configuration
    ├── ports.md         # Port assignments
    └── tools.md         # Tool inventory
```

## Requirements

- Python 3.11+
- uv (recommended) or pip

Optional:
- Docker (for backend API features)
- Node.js 18+ (for web interface)

## Support

- 📖 [Documentation](https://codebasecontext.org)
- 🐛 [Report Issues](https://github.com/killerapp/mem8/issues)
- 💬 [Discussions](https://github.com/killerapp/mem8/discussions)
- 🔧 [Template Repository](https://github.com/killerapp/mem8-plugin)

## License

MIT License - see LICENSE file for details.
