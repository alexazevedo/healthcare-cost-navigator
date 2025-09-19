import asyncio
import os
import sys
import tempfile
from collections.abc import AsyncGenerator, Generator
from pathlib import Path

import httpx
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app.core.database import Base, get_db
from app.main import app

# Test database configuration
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:password@localhost:5432/healthcare_cost_navigator_test"
TEST_DATABASE_URL_SYNC = "postgresql://postgres:password@localhost:5432/healthcare_cost_navigator_test"

# Override settings for testing
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

# Set test OpenAI key if not already set
if "OPENAI_API_KEY" not in os.environ:
    os.environ["OPENAI_API_KEY"] = "test-key"

# Create test engine with proper configuration
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    pool_pre_ping=False,
    pool_recycle=300,
    pool_size=1,
    max_overflow=0,
)
TestSessionLocal = sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession]:
    """Create a fresh database session for each test."""
    # Create a new engine for each test to avoid connection conflicts
    test_engine_local = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        pool_pre_ping=False,
        pool_recycle=300,
        pool_size=1,
        max_overflow=0,
    )

    # Create tables
    async with test_engine_local.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    TestSessionLocalLocal = sessionmaker(bind=test_engine_local, class_=AsyncSession, expire_on_commit=False)
    session = TestSessionLocalLocal()
    try:
        yield session
    finally:
        await session.close()
        await test_engine_local.dispose()

    # Clean up - drop all tables after each test
    async with test_engine_local.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def client() -> Generator[TestClient]:
    """Create a test client for synchronous tests."""
    return TestClient(app)


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient]:
    """Create an async test client for integration tests."""
    async with AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def override_get_db(db_session: AsyncSession):
    """Override the database dependency for testing."""

    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def temp_data_dir() -> Generator[Path]:
    """Create a temporary directory for test data files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def sample_csv_data(temp_data_dir: Path) -> Path:
    """Create sample CSV data for testing."""
    csv_content = """provider_id,provider_name,provider_city,provider_state,provider_zip_code,drg_id,ms_drg_definition,total_discharges,average_covered_charges,average_total_payments,average_medicare_payments
330001,Test Hospital 1,New York,NY,10001,470,"MAJOR HIP AND KNEE JOINT REPLACEMENT OR REATTACHMENT OF LOWER EXTREMITY WITHOUT MCC",10,50000.00,10000.00,8000.00
330002,Test Hospital 2,New York,NY,10002,871,"SEPTICEMIA OR SEVERE SEPSIS WITHOUT MV >96 HOURS WITH MCC",15,45000.00,9500.00,7500.00
330003,Test Hospital 3,Brooklyn,NY,11201,872,"SEPTICEMIA OR SEVERE SEPSIS WITHOUT MV >96 HOURS WITHOUT MCC",20,30000.00,12000.00,9000.00
330004,Test Hospital 4,Albany,NY,12201,470,"MAJOR HIP AND KNEE JOINT REPLACEMENT OR REATTACHMENT OF LOWER EXTREMITY WITHOUT MCC",8,60000.00,11000.00,8500.00
330005,Test Hospital 5,New York,NY,10003,871,"SEPTICEMIA OR SEVERE SEPSIS WITHOUT MV >96 HOURS WITH MCC",12,48000.00,10500.00,8200.00"""

    csv_file = temp_data_dir / "test_data.csv"
    csv_file.write_text(csv_content)
    return csv_file


@pytest.fixture
def sample_zip_data(temp_data_dir: Path) -> Path:
    """Create sample ZIP code data for testing."""
    zip_content = """zip_code,latitude,longitude
10001,40.7505,-73.9934
10002,40.7156,-73.9873
10003,40.7323,-73.9894
11201,40.6943,-73.9903
12201,42.6526,-73.7562"""

    zip_file = temp_data_dir / "test_zip_data.csv"
    zip_file.write_text(zip_content)
    return zip_file


async def load_sample_data(db_session: AsyncSession):
    """Helper function to load sample data for integration tests."""
    from app.models.drg import DRG
    from app.models.drg_price import DRGPrice
    from app.models.provider import Provider
    from app.models.rating import Rating
    from app.models.zip_code import ZipCode

    # Create sample providers
    providers = [
        Provider(
            provider_id="330001",
            provider_name="Test Hospital 1",
            provider_city="New York",
            provider_state="NY",
            provider_zip_code="10001",
        ),
        Provider(
            provider_id="330002",
            provider_name="Test Hospital 2",
            provider_city="New York",
            provider_state="NY",
            provider_zip_code="10002",
        ),
        Provider(
            provider_id="330003",
            provider_name="Test Hospital 3",
            provider_city="Brooklyn",
            provider_state="NY",
            provider_zip_code="11201",
        ),
    ]

    for provider in providers:
        db_session.add(provider)

    # Create sample DRGs first
    drgs = [
        DRG(drg_id=470, ms_drg_definition="MAJOR HIP AND KNEE JOINT REPLACEMENT OR REATTACHMENT OF LOWER EXTREMITY WITHOUT MCC"),
        DRG(drg_id=871, ms_drg_definition="SEPTICEMIA OR SEVERE SEPSIS WITHOUT MV >96 HOURS WITH MCC"),
        DRG(drg_id=872, ms_drg_definition="SEPTICEMIA OR SEVERE SEPSIS WITHOUT MV >96 HOURS WITHOUT MCC"),
    ]

    for drg in drgs:
        db_session.add(drg)

    # Create sample DRG prices
    drg_prices = [
        DRGPrice(
            provider_id="330001",
            drg_id=470,
            total_discharges=10,
            average_covered_charges=50000.00,
            average_total_payments=10000.00,
            average_medicare_payments=8000.00,
        ),
        DRGPrice(
            provider_id="330002",
            drg_id=871,
            total_discharges=15,
            average_covered_charges=45000.00,
            average_total_payments=9500.00,
            average_medicare_payments=7500.00,
        ),
        DRGPrice(
            provider_id="330003",
            drg_id=872,
            total_discharges=20,
            average_covered_charges=30000.00,
            average_total_payments=12000.00,
            average_medicare_payments=9000.00,
        ),
    ]

    for drg_price in drg_prices:
        db_session.add(drg_price)

    # Create sample ratings
    ratings = [
        Rating(provider_id="330001", rating=8),
        Rating(provider_id="330002", rating=7),
        Rating(provider_id="330003", rating=9),
    ]

    for rating in ratings:
        db_session.add(rating)

    # Create sample ZIP codes
    zip_codes = [
        ZipCode(zip_code="10001", latitude=40.7505, longitude=-73.9934),
        ZipCode(zip_code="10002", latitude=40.7156, longitude=-73.9873),
        ZipCode(zip_code="11201", latitude=40.6943, longitude=-73.9903),
    ]

    for zip_code in zip_codes:
        db_session.add(zip_code)

    await db_session.commit()


# Test configuration
pytest_plugins = ["pytest_asyncio"]
