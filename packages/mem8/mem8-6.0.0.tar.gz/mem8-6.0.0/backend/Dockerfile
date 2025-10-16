# Backend Dockerfile for mem8 with integrated CLI
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast Python package management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set work directory
WORKDIR /app

# Copy the entire mem8 project (for CLI)
COPY pyproject.toml README.md ./
COPY mem8/ ./mem8/

# Copy backend files
COPY backend/ ./backend/

# Install mem8 CLI with uv
RUN uv pip install --system -e .

# Install backend dependencies
WORKDIR /app/backend
RUN uv pip install --system fastapi uvicorn[standard] sqlalchemy asyncpg aiosqlite pydantic pydantic-settings redis prometheus-client python-multipart python-jose[cryptography] passlib[bcrypt] httpx email-validator alembic websockets python-json-logger PyJWT

# Set Python path to include backend src
ENV PYTHONPATH=/app/backend/src:$PYTHONPATH

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Use mem8 serve command for cleaner entry point
CMD ["mem8", "serve", "--host", "0.0.0.0", "--port", "8000"]