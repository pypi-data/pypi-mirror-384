---
sidebar_position: 10
---

# Contributing to mem8

This guide will help you contribute to mem8, whether you're fixing bugs, adding features, or improving documentation.

## Prerequisites

- **Python 3.12+** - For mem8 CLI and backend
- **uv** - Package manager (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- **Node.js 18+** - For frontend development (optional)
- **Docker Desktop** - For backend/teams development (optional)
- **Git** - For version control

## Choose Your Development Path

### Path 1: CLI-Only Development

**Best for:** Working on CLI commands, search, templates, metadata extraction

```bash
# Clone the repository
git clone https://github.com/killerapp/mem8.git
cd mem8

# Install mem8 CLI in editable mode
uv tool install --editable .

# Verify installation
mem8 --version
mem8 status

# Run tests
uv run pytest
```

**What you can work on:**
- ✅ CLI commands (`mem8 status`, `mem8 search`, `mem8 find`, etc.)
- ✅ Template system and cookiecutter integration
- ✅ Git worktree management
- ✅ Metadata extraction
- ❌ Backend API features (requires Docker)
- ❌ Team collaboration features (requires Docker)

---

### Path 2: Full-Stack Development

**Best for:** Working on backend API, teams, authentication, database features

```bash
# Clone the repository
git clone https://github.com/killerapp/mem8.git
cd mem8

# 1. Install CLI dependencies
uv tool install --editable .

# 2. Start Docker services (backend + database + frontend)
docker-compose --env-file .env.dev up -d --build

# 3. View logs to verify everything started
docker-compose logs -f

# Services available at:
# - Frontend: http://localhost:22211
# - Backend API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
# - PostgreSQL: localhost:5433
```

**What you can work on:**
- ✅ All CLI features
- ✅ Backend API endpoints
- ✅ Team collaboration features
- ✅ Authentication and authorization
- ✅ Database models and migrations
- ✅ Frontend UI components

---

### Path 3: Hybrid Development

**Best for:** Frontend-focused work with faster refresh

```bash
# Start backend services only
docker-compose --env-file .env.dev up -d backend db

# Run frontend natively
cd frontend
npm install
npm run dev

# Frontend: http://localhost:22211 (native)
# Backend: http://localhost:8000 (Docker)
```

## Development Workflow

### Making Changes

1. **Create a branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Add tests for new features
   - Update documentation
   - Follow existing code patterns

3. **Test your changes**
   ```bash
   # Run all tests
   uv run pytest

   # Run specific tests
   uv run pytest tests/test_file.py

   # Run with coverage
   make test-cov
   ```

4. **Commit with conventional commits**
   ```bash
   git commit -m "feat: add new feature"
   git commit -m "fix: resolve bug in search"
   git commit -m "docs: update installation guide"
   ```

5. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

### Running Tests

```bash
# All tests
uv run pytest

# With HTML report
make test-ui

# With coverage
make test-cov

# Specific marker
uv run pytest -m unit
```

### Code Quality

```bash
# Format code
make format

# Check linting
make lint

# Type checking
uv run mypy mem8
```

## Project Structure

```
mem8/
├── mem8/                 # Main CLI package
│   ├── cli_typer.py     # CLI commands
│   ├── core/            # Core functionality
│   └── integrations/    # External integrations
├── backend/             # FastAPI backend
│   └── src/mem8_api/
├── frontend/            # Next.js frontend
├── tests/               # Test suite
├── documentation/       # Docusaurus docs
└── scripts/             # Utility scripts
```

## Commit Message Convention

We use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting)
- `refactor:` - Code refactoring
- `test:` - Test changes
- `chore:` - Build process or auxiliary tools

**Examples:**
```
feat: add semantic search support
fix: resolve template cloning issue
docs: update contributing guidelines
refactor: simplify config loading
test: add unit tests for search
chore: update dependencies
```

## Pull Request Process

1. **Update tests** - Add or update tests for your changes
2. **Update docs** - Document new features or changed behavior
3. **Verify CI passes** - All tests and checks must pass
4. **Semantic versioning** - PRs trigger automatic releases when merged to main
5. **Code review** - Maintainers will review and provide feedback

## Getting Help

- **Issues:** [github.com/killerapp/mem8/issues](https://github.com/killerapp/mem8/issues)
- **Discussions:** [github.com/killerapp/mem8/discussions](https://github.com/killerapp/mem8/discussions)
- **Documentation:** [docs.codebasecontext.org](https://docs.codebasecontext.org)

## Next Steps

- [Development Setup](./setup) - Detailed environment setup
- [Architecture](./architecture) - System design and components
