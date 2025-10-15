---
sidebar_position: 2
---

# Architecture

Understanding mem8's design and component organization.

## System Overview

mem8 is designed as a three-tier system:

```
┌─────────────────┐
│   CLI (Phase 1) │  ← Standalone Python CLI
│   mem8 command  │
└────────┬────────┘
         │
         ├─────────────────┐
         │                 │
┌────────▼────────┐  ┌────▼──────────┐
│ Frontend (P3)   │  │ Backend (P2)  │
│ Next.js / React │◄─┤ FastAPI       │
└─────────────────┘  └───────┬───────┘
                             │
                     ┌───────▼───────┐
                     │  PostgreSQL   │
                     └───────────────┘
```

## Component Layers

### 1. CLI Layer (Phase 1)

**Location:** `mem8/`

**Purpose:** Standalone CLI tool for memory management

**Key Components:**
- `cli_typer.py` - Command definitions (Typer framework)
- `core/` - Core functionality
  - `memory.py` - Memory/thought operations
  - `sync.py` - Bidirectional sync logic
  - `search.py` - Full-text and semantic search
  - `template_source.py` - External template loading
  - `config.py` - Configuration management
- `integrations/` - External service integrations
  - `github.py` - GitHub CLI integration

**Design Principles:**
- Works completely offline (no backend required)
- Rich terminal UI (emoji support on Windows)
- Hierarchical configuration (user → project → runtime)
- Defensive data protection

### 2. Backend Layer (Phase 2)

**Location:** `backend/src/mem8_api/`

**Purpose:** REST API and real-time sync for teams

**Key Components:**
- `main.py` - FastAPI application entry
- `routes/` - API endpoints
  - `auth.py` - GitHub OAuth
  - `thoughts.py` - CRUD operations
  - `teams.py` - Team management
  - `sync.py` - WebSocket sync
- `models/` - Database models
- `database.py` - Database connection

**Technology Stack:**
- FastAPI - Async Python web framework
- PostgreSQL - Primary database
- SQLAlchemy - ORM
- WebSockets - Real-time sync

### 3. Frontend Layer (Phase 3)

**Location:** `frontend/`

**Purpose:** Web interface for memory management

**Key Components:**
- `src/app/` - Next.js app router
- `src/components/` - React components
- `src/lib/` - Utilities and API client

**Technology Stack:**
- Next.js 15 - React framework
- React 19 - UI library
- TanStack Query - Data fetching
- Tailwind CSS - Styling
- Socket.io - WebSocket client

## Data Flow

### CLI Workflow

```
User Command
    ↓
CLI Parser (Typer)
    ↓
Core Logic (memory.py, sync.py)
    ↓
Local Filesystem
    ├─→ .mem8/ (config)
    ├─→ memory/ (local thoughts)
    └─→ ~/shared-memories/ (shared thoughts)
```

### API Workflow

```
HTTP Request
    ↓
FastAPI Router
    ↓
Business Logic
    ↓
Database (PostgreSQL)
    ↓
HTTP Response
```

### Real-time Sync

```
WebSocket Connection
    ↓
Backend Sync Handler
    ↓
Broadcast to Team Members
    ↓
Frontend Updates
```

## Directory Structure

```
mem8/
├── mem8/                    # CLI package
│   ├── cli_typer.py        # Command definitions
│   ├── core/               # Core functionality
│   │   ├── memory.py       # Memory operations
│   │   ├── sync.py         # Sync logic
│   │   ├── search.py       # Search engine
│   │   ├── config.py       # Configuration
│   │   └── template_source.py  # Templates
│   └── integrations/       # External services
│       └── github.py       # GitHub CLI
│
├── backend/                # Backend API
│   ├── src/mem8_api/
│   │   ├── main.py        # FastAPI app
│   │   ├── routes/        # API endpoints
│   │   ├── models/        # Database models
│   │   └── database.py    # DB connection
│   └── Dockerfile
│
├── frontend/              # Web UI
│   ├── src/
│   │   ├── app/          # Next.js pages
│   │   ├── components/   # React components
│   │   └── lib/          # Utilities
│   └── Dockerfile
│
├── tests/                # Test suite
│   ├── test_cli.py
│   ├── test_memory.py
│   └── test_sync.py
│
├── documentation/        # Docusaurus site
│   └── docs/
│
└── scripts/             # Utility scripts
```

## Configuration System

### Hierarchy

```
Runtime Flags (--flag)
    ↓ (overrides)
Project Config (.mem8/config.yaml)
    ↓ (overrides)
User Config (~/.mem8/config.yaml)
    ↓ (overrides)
System Defaults (mem8/core/config.py)
```

### Configuration Files

**User Config:** `~/.mem8/config.yaml`
```yaml
templates:
  default_source: killerapp/mem8-plugin
shared:
  default_location: ~/Documents/mem8-Shared
```

**Project Config:** `.mem8/config.yaml`
```yaml
templates:
  default_source: acme-corp/custom-templates
```

## Template System

Templates are loaded from external sources:

1. **Builtin** - Default to `killerapp/mem8-plugin`
2. **GitHub** - `org/repo` or `org/repo@tag`
3. **Git URL** - `https://github.com/org/repo.git`
4. **Local** - `/path/to/templates`

Templates are ephemeral - cloned to temp directory, used, then cleaned up.

## Database Schema (Phase 2)

```sql
users
├── id (uuid, pk)
├── github_id (text, unique)
├── username (text)
└── created_at (timestamp)

teams
├── id (uuid, pk)
├── name (text)
├── owner_id (uuid, fk → users)
└── created_at (timestamp)

team_members
├── team_id (uuid, fk → teams)
├── user_id (uuid, fk → users)
└── role (text)

thoughts
├── id (uuid, pk)
├── team_id (uuid, fk → teams)
├── author_id (uuid, fk → users)
├── title (text)
├── content (text)
├── file_path (text)
└── updated_at (timestamp)
```

## Extension Points

### Adding a New CLI Command

1. Add command in `mem8/cli_typer.py`
2. Implement logic in `mem8/core/`
3. Add tests in `tests/`
4. Update docs in `documentation/docs/`

### Adding a Backend Endpoint

1. Define route in `backend/src/mem8_api/routes/`
2. Add database model if needed
3. Update API client in frontend
4. Add tests

### Adding a Template

1. Create cookiecutter template
2. Add to manifest.yaml
3. Test with `mem8 init --template-source`

## Testing Strategy

```
Unit Tests (70%)
├── Core logic (memory, sync, search)
├── Configuration loading
└── Template resolution

Integration Tests (20%)
├── CLI commands end-to-end
├── API endpoints
└── Database operations

E2E Tests (10%)
├── Full user workflows
└── Docker compose validation
```

## Next Steps

- [Development Setup](./setup) - Set up your environment
- [Back to Contributing](./) - Main contributing guide
