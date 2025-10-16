---
sidebar_position: 1
---

# Development Setup

Detailed setup instructions for all development scenarios.

## Prerequisites

### Required
- **Python 3.12+** - [Download Python](https://www.python.org/downloads/)
- **uv** - Fast Python package manager
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
- **Git** - Version control

### Optional (depending on work)
- **Node.js 18+** - For frontend development
- **Docker Desktop** - For backend/database work
- **GitHub CLI (gh)** - For GitHub integration features
  ```bash
  # macOS
  brew install gh

  # Windows
  winget install GitHub.cli
  ```

## CLI-Only Development

Perfect for working on CLI commands, templates, and search without Docker overhead.

### Setup

```bash
# Clone repository
git clone https://github.com/killerapp/mem8.git
cd mem8

# Install in editable mode
uv tool install --editable .

# Verify installation
mem8 --version
mem8 status

# Run tests
uv run pytest
```

### What Works

✅ **Available:**
- All `mem8` CLI commands
- Template initialization (`mem8 init`)
- Search and find operations
- Git worktree management
- Metadata extraction
- Full test suite

❌ **Not Available:**
- Backend API (`mem8 serve`)
- Web interface
- Team collaboration features
- Database operations

### Development Workflow

```bash
# Make changes to code
vim mem8/cli_typer.py

# Reinstall to pick up changes (if needed)
uv tool install --editable . --force

# Test changes
mem8 status
uv run pytest
```

## Full-Stack Development

Work on backend API, database models, authentication, and web UI.

### Setup

```bash
# Clone repository
git clone https://github.com/killerapp/mem8.git
cd mem8

# Install CLI
uv tool install --editable .

# Start all services with Docker
docker-compose --env-file .env.dev up -d --build

# View logs
docker-compose logs -f
```

### Services

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:22211 | Next.js web UI |
| Backend API | http://localhost:8000 | FastAPI server |
| API Docs | http://localhost:8000/docs | Swagger UI |
| Database | localhost:5433 | PostgreSQL |

### Development Workflow

**Backend changes:**
```bash
# Edit backend code
vim backend/src/mem8_api/routes/thoughts.py

# Changes auto-reload via Docker volume mount
# Check logs
docker-compose logs -f backend
```

**Frontend changes:**
```bash
# Edit frontend code
vim frontend/src/app/page.tsx

# Changes auto-reload via Docker volume mount
# View at http://localhost:22211
```

**Database changes:**
```bash
# Connect to database
docker-compose exec db psql -U mem8user -d mem8db

# Or use your favorite SQL client
# Host: localhost
# Port: 5433
# Database: mem8db
# User: mem8user
# Password: mem8password
```

### Stopping Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

## Hybrid Development

Best for frontend-focused work with faster refresh times.

### Setup

```bash
# Start backend services only
docker-compose --env-file .env.dev up -d backend db

# Install frontend dependencies
cd frontend
npm install

# Run frontend natively
npm run dev
```

### Why This Approach

✅ **Benefits:**
- Faster frontend hot reload (no Docker overhead)
- Native Node.js tooling
- Better debugging experience
- Backend still properly configured with database

### Access Points

- Frontend: http://localhost:22211 (native npm)
- Backend: http://localhost:8000 (Docker)
- Database: localhost:5433 (Docker)

## Environment Variables

### CLI Development

No environment variables needed for basic CLI work.

### Backend Development

Copy and customize environment files:

```bash
# For Docker development
cp .env.dev.example .env.dev

# For local backend (no Docker)
cp .env.example backend/.env
```

**Key variables:**

```bash
# Database
DATABASE_URL=postgresql://mem8user:mem8password@localhost:5433/mem8db

# Security
SECRET_KEY=your-secret-key-here

# CORS (for frontend)
ALLOWED_ORIGINS=http://localhost:22211,http://127.0.0.1:22211

# Optional: GitHub OAuth
GITHUB_CLIENT_ID=your_client_id
GITHUB_CLIENT_SECRET=your_client_secret
```

## Troubleshooting

### Command not found: mem8

```bash
# Check uv bin directory is in PATH
echo $PATH | grep uv

# Add to PATH (if needed)
export PATH="$HOME/.local/bin:$PATH"
```

### Permission errors

```bash
# Make binary executable
chmod +x ~/.local/bin/mem8
```

### Docker issues

```bash
# Rebuild containers
docker-compose down
docker-compose --env-file .env.dev up -d --build

# Clean everything
docker-compose down -v
docker system prune -a
```

### Port conflicts

If ports 22211 or 8000 are in use:

```bash
# Check what's using the port
lsof -i :22211
lsof -i :8000

# Kill the process or change ports in docker-compose.yml
```

## Next Steps

- [Architecture](./architecture) - Understand the system design
- [Back to Contributing](./) - Main contributing guide
