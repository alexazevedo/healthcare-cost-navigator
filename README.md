# Healthcare Cost Navigator

A FastAPI-based healthcare cost navigator application.

## Project Structure

```
├── src/
│   └── app/
│       ├── api/
│       │   └── api_v1/
│       │       ├── endpoints/
│       │       └── api.py
│       ├── core/
│       │   ├── config.py
│       │   └── database.py
│       ├── models/
│       ├── schemas/
│       ├── services/
│       └── main.py
├── tests/
├── alembic/
│   └── versions/
├── Pipfile
├── alembic.ini
├── docker-compose.yml
├── Dockerfile
└── .env.example
```

## Setup

### Using Docker (Recommended)

1. Copy the environment file:
   ```bash
   cp .env.example .env
   ```

2. Start the services:
   ```bash
   docker-compose up --build
   ```

The API will be available at `http://localhost:8000`

### Local Development

1. Install Python 3.13
2. Install pipenv:
   ```bash
   pip install pipenv
   ```

3. Install dependencies:
   ```bash
   pipenv install
   ```

4. Activate the virtual environment:
   ```bash
   pipenv shell
   ```

5. Copy the environment file:
   ```bash
   cp .env.example .env
   ```

6. Start PostgreSQL database:
   ```bash
   docker-compose up db
   ```

7. Run database migrations:
   ```bash
   alembic upgrade head
   ```

8. Start the development server:
   ```bash
   uvicorn src.app.main:app --reload
   ```

## API Documentation

Once the server is running, you can access:
- Interactive API docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Testing

Run tests with:
```bash
pytest
```

## Database Migrations

Create a new migration:
```bash
alembic revision --autogenerate -m "Description of changes"
```

Apply migrations:
```bash
alembic upgrade head
```