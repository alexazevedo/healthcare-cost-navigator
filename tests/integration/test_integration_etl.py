"""
Integration tests for ETL pipeline.
Tests the full ETL process including data loading and database operations.
"""

from pathlib import Path

import pytest
from sqlalchemy import select

from app.models.drg import DRG
from app.models.drg_price import DRGPrice
from app.models.provider import Provider
from app.models.rating import Rating
from app.models.zip_code import ZipCode
from scripts.etl import ETLPipeline


class TestETLIntegration:
    """Integration tests for ETL pipeline."""

    @pytest.mark.asyncio
    async def test_etl_loads_providers(self, db_session, sample_csv_data, override_get_db):
        """Test that ETL loads provider data correctly."""
        # Create ETL pipeline with test data and test session
        etl = ETLPipeline(str(sample_csv_data), test_session=db_session)

        # Run ETL
        await etl.run()

        # Verify providers were loaded
        result = await db_session.execute(select(Provider))
        providers = result.scalars().all()

        assert len(providers) == 5
        assert providers[0].provider_id == "330001"
        assert providers[0].provider_name == "Test Hospital 1"
        assert providers[0].provider_city == "New York"
        assert providers[0].provider_state == "NY"
        assert providers[0].provider_zip_code == "10001"

    @pytest.mark.asyncio
    async def test_etl_loads_drgs(self, db_session, sample_csv_data, override_get_db):
        """Test that ETL loads DRG data correctly."""
        etl = ETLPipeline(str(sample_csv_data), test_session=db_session)
        await etl.run()

        # Verify DRGs were loaded
        result = await db_session.execute(select(DRG))
        drgs = result.scalars().all()

        assert len(drgs) >= 2  # At least 470 and 871
        
        # Check specific DRG
        drg_470 = next((d for d in drgs if d.drg_id == 470), None)
        assert drg_470 is not None
        assert "HIP" in drg_470.ms_drg_definition.upper()

    @pytest.mark.asyncio
    async def test_etl_loads_drg_prices(self, db_session, sample_csv_data, override_get_db):
        """Test that ETL loads DRG price data correctly."""
        etl = ETLPipeline(str(sample_csv_data), test_session=db_session)
        await etl.run()

        # Verify DRG prices were loaded
        result = await db_session.execute(select(DRGPrice))
        drg_prices = result.scalars().all()

        assert len(drg_prices) == 5

        # Check specific DRG price
        hip_drg = next((dp for dp in drg_prices if dp.drg_id == 470), None)
        assert hip_drg is not None
        assert hip_drg.provider_id == "330001"
        assert hip_drg.total_discharges == 10
        assert hip_drg.average_covered_charges == 50000.00
        assert hip_drg.average_total_payments == 10000.00
        assert hip_drg.average_medicare_payments == 8000.00

    @pytest.mark.asyncio
    async def test_etl_generates_ratings(self, db_session, sample_csv_data, override_get_db):
        """Test that ETL generates ratings for all providers."""
        etl = ETLPipeline(str(sample_csv_data), test_session=db_session)
        await etl.run()

        # Verify ratings were generated
        result = await db_session.execute(select(Rating))
        ratings = result.scalars().all()

        assert len(ratings) == 5  # One rating per provider

        # Check that all ratings are within valid range
        for rating in ratings:
            assert 1 <= rating.rating <= 10
            assert rating.provider_id in [
                "330001",
                "330002",
                "330003",
                "330004",
                "330005",
            ]

    @pytest.mark.asyncio
    async def test_etl_loads_zip_codes(self, db_session, sample_csv_data, sample_zip_data, override_get_db):
        """Test that ETL loads ZIP code data correctly."""
        # Copy sample ZIP data to expected location
        import shutil

        shutil.copy(sample_zip_data, "zip_lat_lon.csv")

        try:
            etl = ETLPipeline(str(sample_csv_data), test_session=db_session)
            await etl.run()

            # Verify ZIP codes were loaded
            result = await db_session.execute(select(ZipCode))
            zip_codes = result.scalars().all()

            assert len(zip_codes) == 5

            # Check specific ZIP code
            ny_zip = next((zc for zc in zip_codes if zc.zip_code == "10001"), None)
            assert ny_zip is not None
            assert ny_zip.latitude == 40.7505
            assert ny_zip.longitude == -73.9934

        finally:
            # Clean up
            if Path("zip_lat_lon.csv").exists():
                Path("zip_lat_lon.csv").unlink()

    @pytest.mark.asyncio
    async def test_etl_handles_missing_zip_data(self, db_session, sample_csv_data, override_get_db):
        """Test that ETL handles missing ZIP code data gracefully."""
        etl = ETLPipeline(str(sample_csv_data), test_session=db_session)

        # Should not raise exception even without ZIP data
        await etl.run()

        # Verify other data was still loaded
        result = await db_session.execute(select(Provider))
        providers = result.scalars().all()
        assert len(providers) == 5

    @pytest.mark.asyncio
    async def test_etl_data_relationships(self, db_session, sample_csv_data, override_get_db):
        """Test that ETL maintains proper data relationships."""
        etl = ETLPipeline(str(sample_csv_data), test_session=db_session)
        await etl.run()

        # Test provider-DRG relationship
        result = await db_session.execute(select(DRGPrice).where(DRGPrice.provider_id == "330001"))
        drg_prices = result.scalars().all()
        assert len(drg_prices) == 1
        assert drg_prices[0].provider_id == "330001"

        # Test provider-rating relationship
        result = await db_session.execute(select(Rating).where(Rating.provider_id == "330001"))
        ratings = result.scalars().all()
        assert len(ratings) == 1
        assert ratings[0].provider_id == "330001"

    @pytest.mark.asyncio
    async def test_etl_statistics(self, db_session, sample_csv_data, override_get_db):
        """Test that ETL statistics are accurate."""
        etl = ETLPipeline(str(sample_csv_data), test_session=db_session)
        await etl.run()

        stats = await etl.get_statistics()

        assert stats["Providers"] == 5
        assert stats["DRGs"] >= 2  # At least 470 and 871
        assert stats["DRG Prices"] == 5
        assert stats["Ratings"] == 5
        assert stats["ZIP Codes"] == 0  # No ZIP data in this test
