.PHONY: help install install-dev test test-verbose test-cov lint lint-fix format format-check check-all clean start stop restart logs db-migrate db-revision db-history db-current shell dev-server python-shell check-deps security-check update-deps lock-deps sync-deps

# Default target
help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Dependency Management
install: ## Install production dependencies
	pipenv install

install-dev: ## Install development dependencies
	pipenv install --dev

update-deps: ## Update all dependencies to latest versions
	pipenv update

lock-deps: ## Lock dependencies to Pipfile.lock
	pipenv lock

sync-deps: ## Sync dependencies from Pipfile.lock
	pipenv sync

check-deps: ## Check for outdated dependencies and security issues
	pipenv check

# Testing
test: ## Run tests
	pipenv run pytest

test-verbose: ## Run tests with verbose output
	pipenv run pytest -v

test-cov: ## Run tests with coverage report
	pipenv run pytest --cov=src --cov-report=html --cov-report=term

# Code Quality
lint: ## Run linting with ruff
	pipenv run ruff check src/ tests/

lint-fix: ## Run ruff and auto-fix issues
	pipenv run ruff check --fix src/ tests/

format: ## Format code with black and isort
	pipenv run black src/ tests/
	pipenv run isort src/ tests/

format-check: ## Check code formatting without making changes
	pipenv run black --check src/ tests/
	pipenv run isort --check-only src/ tests/

check-all: ## Run all checks (lint + format-check + test)
	pipenv run ruff check src/ tests/
	pipenv run black --check src/ tests/
	pipenv run isort --check-only src/ tests/
	pipenv run pytest

security-check: ## Run security checks with safety
	pipenv run safety check

# Database Operations
db-migrate: ## Run database migrations
	pipenv run alembic upgrade head

db-revision: ## Create a new database migration (usage: make db-revision MESSAGE="your message")
	pipenv run alembic revision --autogenerate -m "$(MESSAGE)"

db-history: ## Show migration history
	pipenv run alembic history

db-current: ## Show current migration
	pipenv run alembic current

db-downgrade: ## Downgrade database by one migration
	pipenv run alembic downgrade -1

# Development Server
dev-server: ## Start development server locally
	pipenv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

python-shell: ## Open Python shell with app context
	pipenv run python -c "from app.main import app; print('App loaded successfully')"

# Scripts
download-sample-ny-data: ## Download and extract NY healthcare data from CMS
	pipenv run python scripts/extract_ny_data.py

run-etl: ## Run the ETL pipeline to load data into PostgreSQL
	pipenv run python scripts/etl.py

run-script: ## Run a script from the scripts/ directory (usage: make run-script SCRIPT=script_name.py)
	pipenv run python scripts/$(SCRIPT)

# Docker Operations
start: ## Start the application with Docker Compose
	docker compose up -d

stop: ## Stop the application
	docker compose down

restart: ## Restart the application
	docker compose restart

logs: ## Show application logs
	docker compose logs -f

shell: ## Open a shell in the running container
	docker compose exec api /bin/bash

# Cleanup
clean: ## Clean up temporary files and caches
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".coverage" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +

# Utility Commands
env-info: ## Show environment information
	@echo "Python version:"
	@pipenv run python --version
	@echo "\nPipenv version:"
	@pipenv --version
	@echo "\nInstalled packages:"
	@pipenv graph

pre-commit: ## Run pre-commit checks (if pre-commit is installed)
	pipenv run pre-commit run --all-files

setup-dev: install-dev ## Setup development environment
	@echo "Setting up development environment..."
	pipenv install --dev
	@echo "Development environment ready!"
