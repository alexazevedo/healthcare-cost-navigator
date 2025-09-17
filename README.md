# Healthcare Cost Navigator

A FastAPI-based healthcare cost navigator application built with Python 3.13, async SQLAlchemy, and PostgreSQL.

## Project Structure

```
├── src/
│   └── app/
│       ├── api/
│       │   ├── __init__.py
│       │   └── endpoints.py
│       ├── core/
│       │   ├── __init__.py
│       │   ├── config.py
│       │   └── database.py
│       ├── models/
│       │   └── __init__.py
│       ├── schemas/
│       │   └── __init__.py
│       ├── services/
│       ├── __init__.py
│       └── main.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   └── test_main.py
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── tasks/
│   ├── OFH-1.md
│   ├── OFH-2.md
│   ├── OFH-3.md
│   ├── OFH-4.md
│   ├── OFH-5.md
│   └── OFH-6.md
├── scripts/
│   └── extract_ny_data.py
├── Pipfile
├── Pipfile.lock
├── alembic.ini
├── docker-compose.yml
├── Dockerfile
├── Makefile
└── pyproject.toml
```

## Quick Start

### Using Docker (Recommended)

1. Start all services:
   ```bash
   make start
   ```

2. View logs:
   ```bash
   make logs
   ```

The API will be available at `http://localhost:8000`

### Local Development

1. Setup development environment:
   ```bash
   make setup-dev
   ```

2. Start PostgreSQL database:
   ```bash
   make start
   ```

3. Run database migrations:
   ```bash
   make db-migrate
   ```

4. Start the development server:
   ```bash
   make dev-server
   ```

## Available Commands

### Development
- `make setup-dev` - Setup development environment
- `make dev-server` - Start development server locally
- `make python-shell` - Open Python shell with app context

### Testing & Quality
- `make test` - Run tests
- `make test-verbose` - Run tests with verbose output
- `make test-cov` - Run tests with coverage report
- `make lint` - Run linting with ruff
- `make lint-fix` - Run ruff and auto-fix issues
- `make format` - Format code with black and isort
- `make format-check` - Check code formatting
- `make check-all` - Run all checks (lint + format + test)
- `make security-check` - Run security checks

### Database Operations
- `make db-migrate` - Run database migrations
- `make db-revision MESSAGE="message"` - Create new migration
- `make db-history` - Show migration history
- `make db-current` - Show current migration
- `make db-downgrade` - Downgrade by one migration

### Docker Operations
- `make start` - Start application with Docker Compose
- `make stop` - Stop application
- `make restart` - Restart application
- `make logs` - Show application logs
- `make shell` - Open shell in running container

### Dependencies
- `make install` - Install production dependencies
- `make install-dev` - Install development dependencies
- `make update-deps` - Update all dependencies
- `make check-deps` - Check for outdated dependencies
- `make lock-deps` - Lock dependencies to Pipfile.lock
- `make sync-deps` - Sync dependencies from Pipfile.lock

### Utilities
- `make clean` - Clean up temporary files and caches
- `make env-info` - Show environment information
- `make help` - Show all available commands

## API Documentation

Once the server is running, you can access:
- Interactive API docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Health check: `http://localhost:8000/health`

## Environment Variables

The application uses the following environment variables (with defaults):
- `POSTGRES_USER` (default: postgres)
- `POSTGRES_PASSWORD` (default: password)
- `POSTGRES_DB` (default: healthcare_cost_navigator)
- `DATABASE_URL` (auto-generated from above)

## Scripts

The `scripts/` directory contains utility scripts for data processing and maintenance:

- **`extract_ny_data.py`**: Downloads and processes CMS healthcare data for New York state, creating a normalized CSV file ready for ETL processing.

### Running Scripts

```bash
# Download and extract NY healthcare data from CMS
make download-sample-ny-data

# Run other scripts (generic command)
make run-script SCRIPT=script_name.py

# Or run directly with pipenv
pipenv run python scripts/extract_ny_data.py
```

## Technology Stack

- **Python**: 3.13
- **Framework**: FastAPI
- **Database**: PostgreSQL with async SQLAlchemy
- **Migrations**: Alembic
- **Package Manager**: Pipenv
- **Containerization**: Docker & Docker Compose
- **Code Quality**: Ruff, Black, isort
- **Testing**: Pytest with async support