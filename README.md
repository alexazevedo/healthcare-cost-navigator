# Healthcare Cost Navigator

A FastAPI-based application that helps users find healthcare providers and get answers to questions about hospital pricing and quality using natural language processing.

## Features

- **Provider Search**: Find healthcare providers by DRG (Diagnosis Related Group) with geographic distance filtering
- **Natural Language Queries**: Ask questions about healthcare costs and get AI-powered answers
- **Geographic Filtering**: Search for providers within a specified radius from any ZIP code
- **Cost Comparison**: Compare average covered charges, total payments, and Medicare payments
- **Quality Ratings**: View provider ratings alongside cost information

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- Pipenv (for dependency management)

### Setup with Docker Compose

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd healthcare-cost-navigator
   ```

2. **Start the services**
   ```bash
   docker compose up -d
   ```

3. **Run database migrations**
   ```bash
   make db-upgrade
   ```

4. **Download and load sample data**
   ```bash
   make download-sample-ny-data
   make run-etl
   ```

5. **Start the development server**
   ```bash
   make dev-server
   ```

The API will be available at `http://localhost:8000`

### Local Development Setup

1. **Install dependencies**
   ```bash
   pipenv install --dev
   pipenv shell
   ```

2. **Set up environment variables**
   ```bash
   # Quick setup
   ./setup_env.sh
   
   # Or manually
   cp env.example .env
   # Edit .env with your configuration
   ```

3. **Start PostgreSQL** (using Docker)
   ```bash
   docker compose up -d postgres
   ```

4. **Run migrations and load data**
   ```bash
   make db-upgrade
   make download-sample-ny-data
   make run-etl
   ```

5. **Start the development server**
   ```bash
   make dev-server
   ```

## API Usage

### Provider Search Endpoint

Search for healthcare providers with optional geographic and DRG filtering:

```bash
# Basic search (all providers)
curl "http://localhost:8000/providers"

# Search by DRG
curl "http://localhost:8000/providers?drg=ALCOHOL"

# Search within 10km of ZIP code 10001
curl "http://localhost:8000/providers?zip=10001&radius_km=10"

# Combined search: ALCOHOL-related DRGs within 5km of ZIP 10016
curl "http://localhost:8000/providers?zip=10016&radius_km=5&drg=ALCOHOL"
```

**Response includes:**
- Provider information (name, city, state, ZIP)
- DRG definition and discharge counts
- Cost information (covered charges, total payments, Medicare payments)
- Provider rating
- Distance from search ZIP (when filtering by location)

### Natural Language Query Endpoint

Ask questions about healthcare providers using natural language:

```bash
# Ask about cheapest providers for a specific condition
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the cheapest hospitals for alcohol treatment in New York?"}'

# Ask about average costs
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the average cost of heart surgery in Manhattan?"}'

# Ask about provider ratings
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "Which hospitals have the highest ratings for trauma care?"}'

# Ask about specific DRG codes
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "Show me all providers for DRG 470 in Brooklyn"}'

# Ask about geographic distribution
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "How many hospitals are there in each borough of New York?"}'
```

## Available Commands

### Development Commands
```bash
make dev-server          # Start development server
make test                # Run tests
make test-cov           # Run tests with coverage
make lint               # Run linting
make lint-fix           # Fix linting issues
make format             # Format code
```

### Database Commands
```bash
make db-upgrade         # Run database migrations
make db-downgrade       # Rollback last migration
make db-revision        # Create new migration
make db-reset           # Reset database (drop and recreate)
```

### Data Commands
```bash
make download-sample-ny-data  # Download NY healthcare data
make run-etl                  # Run ETL pipeline
make run-script <script>      # Run any script in scripts/
```

### Docker Commands
```bash
make docker-build       # Build Docker image
make docker-up          # Start services with Docker Compose
make docker-down        # Stop services
make docker-logs        # View service logs
```

## Project Structure

```
healthcare-cost-navigator/
├── src/
│   └── app/
│       ├── api/           # API endpoints
│       ├── core/          # Core configuration and database
│       ├── models/        # SQLAlchemy models
│       ├── schemas/       # Pydantic schemas
│       ├── services/      # Business logic services
│       └── utils/         # Utility functions
├── scripts/               # Data processing scripts
├── tests/                 # Test files
├── docs/                  # API documentation
├── alembic/              # Database migrations
├── docker-compose.yml    # Docker services configuration
└── Makefile              # Development commands
```

## Environment Variables

The project includes an `env.example` file with all necessary environment variables. To set up your environment:

```bash
# Quick setup (recommended)
./setup_env.sh

# Or manually
cp env.example .env
# Edit .env with your configuration
```

**Required Variables:**
- `DATABASE_URL`: PostgreSQL connection string
- `POSTGRES_USER`: Database username (default: postgres)
- `POSTGRES_PASSWORD`: Database password (default: password)
- `POSTGRES_DB`: Database name (default: healthcare_cost_navigator)
- `OPENAI_API_KEY`: Your OpenAI API key for natural language queries

**Optional Variables:**
- `PROJECT_NAME`: Application name (default: Healthcare Cost Navigator)
- `ENVIRONMENT`: Environment mode (default: development)
- `DEBUG`: Debug mode (default: true)

## Testing

The project uses a volatile test database approach for reliable, clean test runs:

```bash
# Run all tests with volatile database (recommended)
make test-volatile

# Run tests with full data setup
make test-setup

# Run only unit tests (no database required)
make test-unit

# Run with coverage
make test-cov

# Run specific test categories
make test-integration
```

### Test Database Strategy

- **Volatile Database**: Each test run creates a fresh database, runs migrations, loads minimal test data, runs tests, then cleans up
- **Clean State**: No test pollution between runs
- **Reliable**: Consistent test results every time
- **Fast**: Minimal test data for quick execution

## API Documentation

Once the server is running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

This project is licensed under the MIT License.