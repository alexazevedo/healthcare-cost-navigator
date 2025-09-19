#!/usr/bin/env python3
"""
ETL Pipeline for Healthcare Cost Navigator

This script loads CMS CSV data into PostgreSQL, normalizing columns and generating mock ratings.
"""

import asyncio
import logging
import random
import sys
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app.core.database import get_async_session_local
from app.core.logging import setup_logging
from app.models.drg import DRG
from app.models.drg_price import DRGPrice
from app.models.provider import Provider
from app.models.rating import Rating
from app.models.zip_code import ZipCode

# Set up logging
setup_logging()
logger = logging.getLogger(__name__)


class ETLPipeline:
    """ETL Pipeline for loading healthcare data into PostgreSQL."""

    def __init__(self, csv_file_path: str, test_session: AsyncSession = None):
        self.csv_file_path = csv_file_path
        self.test_session = test_session
        self.processed_providers = set()
        self.provider_data = {}
        self.drg_data = []
        self.drgs_data = []
        self.ratings_data = []
        self.zip_csv_path = "zip_lat_lon.csv"

    def _get_session(self):
        """Get database session (test session if provided, otherwise create new one)."""
        if self.test_session:
            return self.test_session
        else:
            return get_async_session_local()()

    async def _clear_existing_data(self) -> None:
        """Clear existing data from all tables before loading new data."""
        if self.test_session:
            session = self.test_session
            await self._clear_existing_data_with_session(session)
        else:
            async with get_async_session_local()() as session:
                await self._clear_existing_data_with_session(session)

    async def _clear_existing_data_with_session(self, session: AsyncSession) -> None:
        """Clear existing data from all tables with given session."""
        try:
            # Clear data in reverse order of dependencies
            await session.execute(text("TRUNCATE TABLE ratings CASCADE"))
            await session.execute(text("TRUNCATE TABLE drg_prices CASCADE"))
            await session.execute(text("TRUNCATE TABLE drgs CASCADE"))
            await session.execute(text("TRUNCATE TABLE providers CASCADE"))
            # Note: We don't clear zip_codes as they're loaded from a separate file
            # and are used by the application for geographic lookups

            if not self.test_session:  # Only commit if not using test session
                await session.commit()
            logger.info("Existing data cleared successfully")
        except Exception as e:
            logger.warning(f"Could not clear existing data: {e}")
            # Continue with the ETL process even if clearing fails

    async def run(self) -> None:
        """Run the complete ETL pipeline."""
        logger.info("=" * 60)
        logger.info("Healthcare Cost Navigator - ETL Pipeline")
        logger.info("=" * 60)

        try:
            # Step 0: Clear existing data
            logger.info("Step 0: Clearing existing data...")
            await self._clear_existing_data()

            # Step 1: Read and validate CSV
            logger.info("Step 1: Reading CSV data...")
            await self._read_csv()

            # Step 2: Normalize and prepare data
            logger.info("Step 2: Normalizing and preparing data...")
            await self._normalize_data()

            # Step 3: Load providers
            logger.info("Step 3: Loading providers...")
            await self._load_providers()

            # Step 4: Load DRGs
            logger.info("Step 4: Loading DRGs...")
            await self._load_drgs()

            # Step 5: Load DRG prices
            logger.info("Step 5: Loading DRG prices...")
            await self._load_drg_prices()

            # Step 6: Generate and load ratings
            logger.info("Step 6: Generating and loading ratings...")
            await self._generate_and_load_ratings()
            await self._load_zip_codes()

            logger.info("\n" + "=" * 60)
            logger.info("ETL Pipeline completed successfully!")
            logger.info(f"Processed {len(self.processed_providers)} providers")
            logger.info(f"Loaded {len(self.drgs_data)} unique DRGs")
            logger.info(f"Loaded {len(self.drg_data)} DRG price records")
            logger.info(f"Generated {len(self.ratings_data)} ratings")
            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"ETL Pipeline failed: {e}")
            raise

    async def _read_csv(self) -> None:
        """Read and validate the CSV file."""
        if not Path(self.csv_file_path).exists():
            raise FileNotFoundError(f"CSV file not found: {self.csv_file_path}")

        # Read CSV with proper encoding
        try:
            self.df = pd.read_csv(self.csv_file_path, encoding="utf-8")
        except UnicodeDecodeError:
            try:
                self.df = pd.read_csv(self.csv_file_path, encoding="latin-1")
            except UnicodeDecodeError:
                self.df = pd.read_csv(self.csv_file_path, encoding="cp1252")

        logger.info(f"CSV loaded: {len(self.df)} records, {len(self.df.columns)} columns")
        logger.debug(f"Columns: {list(self.df.columns)}")

        # Validate required columns
        required_columns = [
            "provider_id",
            "provider_name",
            "provider_city",
            "provider_state",
            "provider_zip_code",
            "ms_drg_definition",
            "total_discharges",
            "average_covered_charges",
            "average_total_payments",
            "average_medicare_payments",
        ]
        
        # Optional columns
        optional_columns = ["drg_id"]

        missing_columns = [
            col for col in required_columns if col not in self.df.columns
        ]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")

    async def _normalize_data(self) -> None:
        """Normalize and prepare data for loading."""
        # Clean and validate data
        self.df = self.df.dropna(
            subset=["provider_id", "provider_name", "ms_drg_definition"]
        )

        # Ensure numeric columns are properly formatted
        numeric_columns = [
            "total_discharges",
            "average_covered_charges",
            "average_total_payments",
            "average_medicare_payments",
        ]

        for col in numeric_columns:
            if col in self.df.columns:
                self.df[col] = pd.to_numeric(self.df[col], errors="coerce")

        # Remove rows with invalid numeric data
        self.df = self.df.dropna(subset=numeric_columns)

        # Clean string columns
        string_columns = ["provider_name", "provider_city", "ms_drg_definition"]
        for col in string_columns:
            if col in self.df.columns:
                self.df[col] = self.df[col].astype(str).str.strip()

        # Clean provider_id and zip_code
        self.df["provider_id"] = self.df["provider_id"].astype(str).str.strip()
        self.df["provider_zip_code"] = (
            self.df["provider_zip_code"].astype(str).str.strip()
        )
        
        # Extract or clean drg_id if it exists, otherwise create from ms_drg_definition
        if "drg_id" in self.df.columns:
            self.df["drg_id"] = pd.to_numeric(self.df["drg_id"], errors="coerce").astype("Int64")
        else:
            # Extract DRG ID from ms_drg_definition (usually starts with a number)
            extracted_ids = self.df["ms_drg_definition"].str.extract(r'^(\d+)')[0]
            self.df["drg_id"] = pd.to_numeric(extracted_ids, errors="coerce").astype("Int64")
            # For definitions that don't start with numbers, create synthetic IDs starting from 9000
            mask = self.df["drg_id"].isna()
            synthetic_ids = range(9000, 9000 + mask.sum())
            self.df.loc[mask, "drg_id"] = synthetic_ids

        logger.info(f"Data normalized: {len(self.df)} valid records")

    async def _load_providers(self) -> None:
        """Load unique providers into the database."""
        if self.test_session:
            session = self.test_session
            # Don't use context manager for test session
            await self._load_providers_with_session(session)
        else:
            async with get_async_session_local()() as session:
                await self._load_providers_with_session(session)

    async def _load_providers_with_session(self, session: AsyncSession) -> None:
        """Load unique providers into the database with given session."""
        # Get unique providers
        unique_providers = self.df.groupby("provider_id").first().reset_index()

        for _, row in unique_providers.iterrows():
            provider_id = row["provider_id"]

            # Check if provider already exists
            result = await session.execute(
                select(Provider).where(Provider.provider_id == provider_id)
            )
            existing_provider = result.scalar_one_or_none()

            if not existing_provider:
                provider = Provider(
                    provider_id=provider_id,
                    provider_name=row["provider_name"],
                    provider_city=row["provider_city"],
                    provider_state=row["provider_state"],
                    provider_zip_code=row["provider_zip_code"],
                )
                session.add(provider)
                self.processed_providers.add(provider_id)
                self.provider_data[provider_id] = provider
            else:
                self.processed_providers.add(provider_id)
                self.provider_data[provider_id] = existing_provider

        if not self.test_session:  # Only commit if not using test session
            await session.commit()
        logger.info(f"Loaded {len(self.processed_providers)} providers")

    async def _load_drgs(self) -> None:
        """Load unique DRGs into the database."""
        if self.test_session:
            session = self.test_session
            await self._load_drgs_with_session(session)
        else:
            async with get_async_session_local()() as session:
                await self._load_drgs_with_session(session)

    async def _load_drgs_with_session(self, session: AsyncSession) -> None:
        """Load unique DRGs into the database with given session."""
        # Get unique DRG combinations
        unique_drgs = self.df[["drg_id", "ms_drg_definition"]].drop_duplicates()
        
        for _, row in unique_drgs.iterrows():
            drg_id = int(row["drg_id"])  # Convert to int
            ms_drg_definition = row["ms_drg_definition"]
            
            # Check if DRG already exists
            existing_drg = await session.get(DRG, drg_id)
            if not existing_drg:
                drg = DRG(
                    drg_id=drg_id,
                    ms_drg_definition=ms_drg_definition
                )
                session.add(drg)
                self.drgs_data.append(drg)
        
        if not self.test_session:  # Only commit if not using test session
            await session.commit()
        logger.info(f"Loaded {len(self.drgs_data)} unique DRGs")

    async def _load_drg_prices(self) -> None:
        """Load DRG prices into the database."""
        if self.test_session:
            session = self.test_session
            await self._load_drg_prices_with_session(session)
        else:
            async with get_async_session_local()() as session:
                await self._load_drg_prices_with_session(session)

    async def _load_drg_prices_with_session(self, session: AsyncSession) -> None:
        """Load DRG prices into the database with given session."""
        for _, row in self.df.iterrows():
            provider_id = row["provider_id"]
            drg_id = int(row["drg_id"])  # Convert to int

            # Get the provider from our loaded data
            if provider_id not in self.provider_data:
                continue

            # Create DRG price record (DRG should already exist from previous step)
            drg_price = DRGPrice(
                provider_id=provider_id,
                drg_id=drg_id,
                total_discharges=int(row["total_discharges"]),
                average_covered_charges=float(row["average_covered_charges"]),
                average_total_payments=float(row["average_total_payments"]),
                average_medicare_payments=float(row["average_medicare_payments"]),
            )
            session.add(drg_price)
            self.drg_data.append(drg_price)

        if not self.test_session:  # Only commit if not using test session
            await session.commit()
        logger.info(f"Loaded {len(self.drg_data)} DRG price records")

    async def _generate_and_load_ratings(self) -> None:
        """Generate mock ratings for all providers and load into database."""
        if self.test_session:
            session = self.test_session
            await self._generate_and_load_ratings_with_session(session)
        else:
            async with get_async_session_local()() as session:
                await self._generate_and_load_ratings_with_session(session)

    async def _generate_and_load_ratings_with_session(
        self, session: AsyncSession
    ) -> None:
        """Generate mock ratings for all providers and load into database with given session."""
        for provider_id in self.processed_providers:
            # Generate random rating between 1 and 10
            rating_value = random.randint(1, 10)

            rating = Rating(provider_id=provider_id, rating=rating_value)
            session.add(rating)
            self.ratings_data.append(rating)

        if not self.test_session:  # Only commit if not using test session
            await session.commit()
        logger.info(f"Generated {len(self.ratings_data)} ratings")

    async def _load_zip_codes(self) -> None:
        """Load ZIP code data from CSV into database."""
        zip_csv_path = "zip_lat_lon.csv"

        if not Path(zip_csv_path).exists():
            logger.warning(f"ZIP code CSV file not found: {zip_csv_path}")
            logger.warning("Please run 'python scripts/build_zip_latlon.py' first")
            return

        logger.info(f"Loading ZIP code data from: {zip_csv_path}")

        try:
            # Read ZIP code data
            df = pd.read_csv(zip_csv_path)
            logger.info(f"Found {len(df)} ZIP codes")

            if self.test_session:
                # Use test session if provided
                session = self.test_session
                # Clear existing ZIP code data
                await session.execute(text("DELETE FROM zip_codes"))

                # Load new ZIP code data
                for _, row in df.iterrows():
                    # Convert ZIP code to integer first to remove decimal point, then back to string
                    zip_code_str = str(int(float(row["zip_code"])))
                    zip_code = ZipCode(
                        zip_code=zip_code_str,
                        latitude=float(row["latitude"]),
                        longitude=float(row["longitude"]),
                    )
                    session.add(zip_code)

                # Don't commit for test session - let the test handle it
                logger.info(f"Loaded {len(df)} ZIP codes into database")
            else:
                # Use new session for production
                async with get_async_session_local()() as session:
                    # Clear existing ZIP code data
                    await session.execute(text("DELETE FROM zip_codes"))

                    # Load new ZIP code data
                    for _, row in df.iterrows():
                        # Convert ZIP code to integer first to remove decimal point, then back to string
                        zip_code_str = str(int(float(row["zip_code"])))
                        zip_code = ZipCode(
                            zip_code=zip_code_str,
                            latitude=float(row["latitude"]),
                            longitude=float(row["longitude"]),
                        )
                        session.add(zip_code)

                    await session.commit()
                    logger.info(f"Loaded {len(df)} ZIP codes into database")

        except Exception as e:
            logger.error(f"Error loading ZIP code data: {e}")
            raise

    async def get_statistics(self) -> dict[str, Any]:
        """Get statistics about the loaded data."""
        if self.test_session:
            # Use test session if provided
            session = self.test_session
            # Count providers
            provider_count = await session.execute(select(Provider))
            provider_count = len(provider_count.scalars().all())

            # Count DRGs
            drgs_count = await session.execute(select(DRG))
            drgs_count = len(drgs_count.scalars().all())

            # Count DRG prices
            drg_count = await session.execute(select(DRGPrice))
            drg_count = len(drg_count.scalars().all())

            # Count ratings
            rating_count = await session.execute(select(Rating))
            rating_count = len(rating_count.scalars().all())

            # Count ZIP codes
            zip_count = await session.execute(select(ZipCode))
            zip_count = len(zip_count.scalars().all())

            return {
                "Providers": provider_count,
                "DRGs": drgs_count,
                "DRG Prices": drg_count,
                "Ratings": rating_count,
                "ZIP Codes": zip_count,
            }
        else:
            # Use new session for production
            async with get_async_session_local()() as session:
                # Count providers
                provider_count = await session.execute(select(Provider))
                provider_count = len(provider_count.scalars().all())

                # Count DRGs
                drgs_count = await session.execute(select(DRG))
                drgs_count = len(drgs_count.scalars().all())

                # Count DRG prices
                drg_count = await session.execute(select(DRGPrice))
                drg_count = len(drg_count.scalars().all())

                # Count ratings
                rating_count = await session.execute(select(Rating))
                rating_count = len(rating_count.scalars().all())

                # Count ZIP codes
                zip_count = await session.execute(select(ZipCode))
                zip_count = len(zip_count.scalars().all())

                return {
                    "Providers": provider_count,
                    "DRGs": drgs_count,
                    "DRG Prices": drg_count,
                    "Ratings": rating_count,
                    "ZIP Codes": zip_count,
                }


async def main():
    """Main function to run the ETL pipeline."""
    csv_file = "sample_prices_ny.csv"

    if not Path(csv_file).exists():
        logger.error(
            f"Error: {csv_file} not found. Please run 'make download-sample-ny-data' first."
        )
        return

    etl = ETLPipeline(csv_file)
    await etl.run()

    # Display final statistics
    stats = await etl.get_statistics()
    logger.info("\nFinal Statistics:")
    logger.info(f"  Providers: {stats['Providers']}")
    logger.info(f"  DRGs: {stats['DRGs']}")
    logger.info(f"  DRG Prices: {stats['DRG Prices']}")
    logger.info(f"  Ratings: {stats['Ratings']}")
    logger.info(f"  ZIP Codes: {stats['ZIP Codes']}")


if __name__ == "__main__":
    asyncio.run(main())
