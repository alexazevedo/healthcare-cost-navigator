# Ticket OFH-1: Project Setup

## Description
Set up the initial project structure for a healthcare cost navigator application using FastAPI with PostgreSQL database.

## AI Prompt
You are an expert Python backend engineer.  
Create a new FastAPI project using Python 3.13 with async SQLAlchemy and Alembic migrations.
Use pipenv (Pipfile) as package manager
Add Docker and Docker Compose with PostgreSQL service.  
Include configuration files: Pipfile, alembic.ini, .env.example, docker-compose.yml, and a basic Dockerfile for the API. 
Include linting/formatting tools as dev dependencies (ruff, black8, isort)
Create a Makefile with some basic operations to start/stop the service, lint, format etc. Don't over-engineer it adding functionalities that won't be used. Make it run python commands through pipenv.
Create just initial structure, no need to create seed data at this point. Do not add any extra features beyond what is required.

## Acceptance Criteria
- [x] FastAPI project created with Python 3.13
- [x] Async SQLAlchemy configured
- [x] Alembic migrations set up  
- [x] Docker and Docker Compose configured  
- [x] PostgreSQL service included  
- [x] All required configuration files present  
- [x] Basic Dockerfile for API created  
