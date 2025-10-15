# mem8 Development Makefile
.PHONY: help test test-ui test-dashboard test-watch install-dev lint format clean \
	backend-install-dev backend-dev frontend-install frontend-dev compose-up compose-down compose-logs

help:  ## Show this help message
	@echo "mem8 Development Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install-dev:  ## Install development dependencies
	uv sync --extra dev

test:  ## Run tests with basic output
	uv run pytest

test-ui:  ## Generate HTML test report and open in browser  
	uv run python scripts/test-ui.py html

test-basic:  ## Run basic tests with terminal output  
	uv run python scripts/test-ui.py basic

test-watch:  ## Run tests in watch mode (requires pytest-xdist)
	uv run python scripts/test-ui.py watch

test-cov:  ## Run tests with coverage report
	uv run pytest --cov=mem8 --cov-report=html --cov-report=term

lint:  ## Run linting with mypy and format checks
	uv run black --check .
	uv run isort --check-only .
	uv run mypy mem8

format:  ## Format code with black and isort
	uv run black .
	uv run isort .

clean:  ## Clean up generated files
	rm -rf htmlcov/ reports/ .coverage .pytest_cache/ __pycache__/
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.pyc" -delete

build:  ## Build wheel package
	uv build

install-local:  ## Install mem8 locally in editable mode
	uv tool install --editable .

release:  ## Create a new release (semantic-release)
	uv run semantic-release publish

# ---------------------------------------------------------------------------
# Convenience targets for local development
# ---------------------------------------------------------------------------

backend-install-dev:  ## Install backend development dependencies
	cd backend && uv sync --extra dev

backend-dev:  ## Start FastAPI dev server on :8000
	cd backend && uv run uvicorn mem8_api.main:app --reload --host 127.0.0.1 --port 8000

frontend-install:  ## Install frontend dependencies
	cd frontend && npm install

frontend-dev:  ## Start Next.js dev server on :22211
	cd frontend && npm run dev

compose-up:  ## Start full stack (postgres, redis, backend, frontend)
	docker-compose --env-file .env.dev up

compose-down:  ## Stop stack and remove containers
	docker-compose --env-file .env.dev down

compose-logs:  ## Tail docker compose logs
	docker-compose logs -f
