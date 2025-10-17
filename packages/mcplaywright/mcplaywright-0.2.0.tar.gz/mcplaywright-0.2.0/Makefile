# MCPlaywright Development Makefile

.PHONY: help install dev test lint clean build docker-dev docker-test

# Default target
help:
	@echo "MCPlaywright Development Commands"
	@echo "================================="
	@echo ""
	@echo "Setup & Installation:"
	@echo "  install         Install dependencies with uv"
	@echo "  install-dev     Install with development dependencies"
	@echo "  playwright      Install Playwright browsers"
	@echo ""
	@echo "Development:"
	@echo "  dev             Start development server with hot-reload"
	@echo "  test            Run test suite with pytest"
	@echo "  test-fast       Run tests without slow/integration tests"
	@echo "  test-watch      Run tests in watch mode"
	@echo "  lint            Run code linting and formatting"
	@echo "  format          Format code with black and isort"
	@echo ""
	@echo "Server Operations:"
	@echo "  serve           Start production server"
	@echo "  health          Check server health"
	@echo "  info            Show server information"
	@echo ""
	@echo "Docker:"
	@echo "  docker-dev      Start containerized development environment" 
	@echo "  docker-test     Run tests in Docker container"
	@echo "  docker-build    Build Docker image"
	@echo ""
	@echo "Utilities:"
	@echo "  clean           Clean build artifacts and cache"
	@echo "  build           Build distribution packages"
	@echo ""

# Installation targets
install:
	@echo "Installing MCPlaywright with uv..."
	uv sync

install-dev:
	@echo "Installing MCPlaywright with development dependencies..."
	uv sync --dev

playwright:
	@echo "Installing Playwright browsers..."
	uv run playwright install chromium firefox webkit
	@echo "✓ Playwright browsers installed"

# Development targets  
dev:
	@echo "Starting development server with hot-reload..."
	uv run python scripts/dev_server.py

serve:
	@echo "Starting production server..."
	uv run mcplaywright serve

health:
	@echo "Checking server health..."
	uv run mcplaywright health

info:
	@echo "Server information:"
	uv run mcplaywright info

# Testing targets
test:
	@echo "Running test suite..."
	uv run pytest -v

test-fast:
	@echo "Running fast tests (excluding slow/integration)..."
	uv run pytest -v -m "not slow and not integration"

test-watch:
	@echo "Running tests in watch mode..."
	uv run pytest -v --tb=short -x -s --lf

test-playwright:
	@echo "Testing Playwright installation..."
	uv run mcplaywright test-playwright

# Code quality targets
lint:
	@echo "Running code linting..."
	uv run ruff check src/ tests/
	uv run mypy src/mcplaywright
	@echo "✓ Linting passed"

format:
	@echo "Formatting code..."
	uv run black src/ tests/ scripts/
	uv run isort src/ tests/ scripts/
	uv run ruff format src/ tests/
	@echo "✓ Code formatted"

# Docker targets
docker-build:
	@echo "Building Docker image..."
	docker build -t mcplaywright:latest .
	docker build -t mcplaywright:dev --target dev .

docker-dev:
	@echo "Starting containerized development environment..."
	docker-compose up --build mcplaywright-dev

docker-test:
	@echo "Running tests in Docker..."
	docker run --rm mcplaywright:dev uv run pytest -v

# Utility targets
clean:
	@echo "Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf reports/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	@echo "✓ Cleaned"

build:
	@echo "Building distribution packages..."
	uv run python -m build
	@echo "✓ Built packages in dist/"

# Development setup (first time)
setup: install-dev playwright
	@echo "Setting up development environment..."
	mkdir -p logs artifacts/{videos,screenshots,requests}
	@echo "✓ Development environment ready"
	@echo ""
	@echo "Next steps:"
	@echo "  make dev     - Start development server"
	@echo "  make test    - Run test suite"

# Performance benchmarks
benchmark:
	@echo "Running performance benchmarks..."
	uv run pytest -v tests/performance/ --benchmark-only

# Generate test reports
test-report:
	@echo "Generating comprehensive test report..."
	uv run pytest --html=reports/test_report.html --cov=src/mcplaywright --cov-report=html:reports/coverage_html
	@echo "✓ Test report generated in reports/"

# Check for security vulnerabilities
security:
	@echo "Checking for security vulnerabilities..."
	uv run pip-audit
	@echo "✓ Security check completed"

# Docker Compose Redis Environment
.PHONY: dev-up prod-up redis-test test-storage stop-all clean-all logs redis-cli

dev-up: ## Start development environment with Redis
	@echo "🚀 Starting development environment with Redis..."
	docker compose --profile dev up -d
	@echo "📊 MCPlaywright Dev: http://localhost:8000"
	@echo "🔍 Redis Commander: http://localhost:8081"
	@echo "💡 Run 'make test-redis' to test Redis storage backend"

prod-up: ## Start production environment
	@echo "🚀 Starting production environment..."
	docker compose up -d mcplaywright redis

stop-all: ## Stop all Docker services
	docker compose --profile dev down

clean-all: ## Stop and remove containers, volumes, and images
	docker compose --profile dev down -v --rmi all
	docker system prune -f

logs: ## Show logs for all services
	docker compose --profile dev logs -f

redis-cli: ## Connect to Redis CLI
	docker compose exec redis redis-cli

# Redis Storage Testing
test-redis: ## Test Redis storage backend in Docker
	@echo "🔄 Testing Redis storage backend..."
	docker compose --profile dev run --rm \
		-e STORAGE_BACKEND=redis \
		-e REDIS_HOST=redis \
		mcplaywright-dev uv run python test_storage_backends.py

test-storage: ## Test all storage backends in Docker
	@echo "🔄 Testing all storage backends..."
	docker compose --profile dev run --rm mcplaywright-dev uv run python test_storage_backends.py

test-large-cursors-redis: ## Test large cursors with Redis
	@echo "🔄 Testing large cursors with Redis..."
	docker compose --profile dev run --rm \
		-e STORAGE_BACKEND=redis \
		-e REDIS_HOST=redis \
		mcplaywright-dev uv run python test_large_cursor_payloads.py

# Storage Backend Switching
switch-redis: ## Switch to Redis storage backend
	@sed -i 's/^STORAGE_BACKEND=.*/STORAGE_BACKEND=redis/' .env
	@echo "✅ Switched to Redis backend"

switch-memory: ## Switch to Memory storage backend
	@sed -i 's/^STORAGE_BACKEND=.*/STORAGE_BACKEND=memory/' .env
	@echo "✅ Switched to Memory backend"

switch-sqlite: ## Switch to SQLite storage backend
	@sed -i 's/^STORAGE_BACKEND=.*/STORAGE_BACKEND=sqlite/' .env
	@echo "✅ Switched to SQLite backend"

# Comprehensive testing
test-all-backends: test-storage test-redis test-large-cursors-redis ## Test all storage backends comprehensively
	@echo "✅ All storage backend tests completed!"