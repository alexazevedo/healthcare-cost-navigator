#!/usr/bin/env python3
"""
Load minimal test data for testing.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Set test database URL
os.environ["DATABASE_URL"] = (
    "postgresql+asyncpg://postgres:password@localhost:5432/healthcare_cost_navigator_test"
)

from sqlalchemy import text

from app.core.database import get_async_session_local


async def load_test_data():
    """Load minimal test data for testing."""
    async with get_async_session_local()() as session:
        # Create tables
        await session.execute(
            text(
                "CREATE TABLE IF NOT EXISTS providers (provider_id VARCHAR(6) PRIMARY KEY, provider_name VARCHAR(255), provider_city VARCHAR(100), provider_state VARCHAR(2), provider_zip_code VARCHAR(10));"
            )
        )
        await session.execute(
            text(
                "CREATE TABLE IF NOT EXISTS drg_prices (id SERIAL PRIMARY KEY, provider_id VARCHAR(6), ms_drg_definition VARCHAR(255), total_discharges INTEGER, average_covered_charges NUMERIC(10,2), average_total_payments NUMERIC(10,2), average_medicare_payments NUMERIC(10,2));"
            )
        )
        await session.execute(
            text(
                "CREATE TABLE IF NOT EXISTS ratings (id SERIAL PRIMARY KEY, provider_id VARCHAR(6), rating INTEGER CHECK (rating >= 1 AND rating <= 10));"
            )
        )
        await session.execute(
            text(
                "CREATE TABLE IF NOT EXISTS zip_codes (zip_code VARCHAR(10) PRIMARY KEY, latitude FLOAT, longitude FLOAT);"
            )
        )

        # Insert minimal test data
        await session.execute(
            text(
                "INSERT INTO providers VALUES ('330001', 'Test Hospital 1', 'New York', 'NY', '10001')"
            )
        )
        await session.execute(
            text(
                "INSERT INTO drg_prices VALUES (1, '330001', 'TEST DRG', 10, 50000.00, 10000.00, 8000.00)"
            )
        )
        await session.execute(text("INSERT INTO ratings VALUES (1, '330001', 8)"))
        await session.execute(
            text("INSERT INTO zip_codes VALUES ('10001', 40.7505, -73.9934)")
        )

        await session.commit()
        print("Test data loaded successfully")


if __name__ == "__main__":
    asyncio.run(load_test_data())
