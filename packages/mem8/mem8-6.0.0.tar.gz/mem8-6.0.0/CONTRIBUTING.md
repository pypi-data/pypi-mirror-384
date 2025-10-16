# Contributing to mem8

Thank you for your interest in contributing to mem8!

## Quick Start

```bash
# Clone and install
git clone https://github.com/killerapp/mem8.git
cd mem8
uv tool install --editable .

# Run tests
uv run pytest

# Make your changes, then test
mem8 --version
```

## Development Paths

**CLI Development** (no Docker needed)
- Work on CLI commands, templates, search
- `uv tool install --editable .`

**Full-Stack Development** (Docker required)
- Backend API, teams, web UI
- `docker-compose --env-file .env.dev up`

## Documentation

Full contributing documentation is available at:

**📚 [codebasecontext.org/docs/contributing](https://codebasecontext.org/docs/contributing)**

Topics covered:
- Development setup (CLI-only vs full-stack)
- Architecture overview
- Testing guidelines
- Code style and conventions
- Pull request process

## Quick Links

- **Issues:** [github.com/killerapp/mem8/issues](https://github.com/killerapp/mem8/issues)
- **Discussions:** [github.com/killerapp/mem8/discussions](https://github.com/killerapp/mem8/discussions)
- **Documentation:** [codebasecontext.org](https://codebasecontext.org)

## Code of Conduct

Please be respectful and constructive in all interactions.
