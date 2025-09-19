"""
Unit tests for database models.
Tests model validation, relationships, and constraints.
"""

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.drg import DRG
from app.models.drg_price import DRGPrice
from app.models.provider import Provider
from app.models.rating import Rating
from app.models.zip_code import ZipCode


class TestProviderModel:
    """Unit tests for Provider model."""

    @pytest.mark.asyncio
    async def test_provider_creation(self, db_session):
        """Test creating a provider with valid data."""
        provider = Provider(
            provider_id="330001",
            provider_name="Test Hospital",
            provider_city="New York",
            provider_state="NY",
            provider_zip_code="10001",
        )

        db_session.add(provider)
        await db_session.commit()

        # Verify provider was created
        assert provider.provider_id == "330001"
        assert provider.provider_name == "Test Hospital"
        assert provider.provider_city == "New York"
        assert provider.provider_state == "NY"
        assert provider.provider_zip_code == "10001"

    @pytest.mark.asyncio
    async def test_provider_required_fields(self, db_session):
        """Test that required fields are enforced."""
        provider = Provider()

        with pytest.raises(IntegrityError):
            db_session.add(provider)
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_provider_primary_key(self, db_session):
        """Test that provider_id is the primary key."""
        provider1 = Provider(
            provider_id="330001",
            provider_name="Test Hospital 1",
            provider_city="New York",
            provider_state="NY",
            provider_zip_code="10001",
        )
        provider2 = Provider(
            provider_id="330001",  # Same ID
            provider_name="Test Hospital 2",
            provider_city="Brooklyn",
            provider_state="NY",
            provider_zip_code="11201",
        )

        db_session.add(provider1)
        await db_session.commit()

        with pytest.raises(IntegrityError):
            db_session.add(provider2)
            await db_session.commit()


class TestDRGModel:
    """Unit tests for DRG model."""

    @pytest.mark.asyncio
    async def test_drg_creation(self, db_session):
        """Test creating a DRG with valid data."""
        drg = DRG(
            drg_id=470,
            ms_drg_definition="MAJOR HIP AND KNEE JOINT REPLACEMENT OR REATTACHMENT OF LOWER EXTREMITY WITHOUT MCC"
        )

        db_session.add(drg)
        await db_session.commit()

        # Verify DRG was created
        assert drg.drg_id == 470
        assert drg.ms_drg_definition == "MAJOR HIP AND KNEE JOINT REPLACEMENT OR REATTACHMENT OF LOWER EXTREMITY WITHOUT MCC"

    @pytest.mark.asyncio
    async def test_drg_primary_key(self, db_session):
        """Test that drg_id is the primary key."""
        drg1 = DRG(drg_id=470, ms_drg_definition="TEST DRG 1")
        drg2 = DRG(drg_id=470, ms_drg_definition="TEST DRG 2")  # Same ID

        db_session.add(drg1)
        await db_session.commit()

        with pytest.raises(IntegrityError):
            db_session.add(drg2)
            await db_session.commit()


class TestDRGPriceModel:
    """Unit tests for DRGPrice model."""

    @pytest.mark.asyncio
    async def test_drg_price_creation(self, db_session):
        """Test creating a DRG price with valid data."""
        # First create a provider
        provider = Provider(
            provider_id="330001",
            provider_name="Test Hospital",
            provider_city="New York",
            provider_state="NY",
            provider_zip_code="10001",
        )
        db_session.add(provider)

        # Create a DRG
        drg = DRG(drg_id=470, ms_drg_definition="TEST DRG")
        db_session.add(drg)
        await db_session.commit()

        drg_price = DRGPrice(
            provider_id="330001",
            drg_id=470,
            total_discharges=10,
            average_covered_charges=50000.00,
            average_total_payments=10000.00,
            average_medicare_payments=8000.00,
        )

        db_session.add(drg_price)
        await db_session.commit()

        # Verify DRG price was created
        assert drg_price.provider_id == "330001"
        assert drg_price.drg_id == 470
        assert drg_price.total_discharges == 10
        assert drg_price.average_covered_charges == 50000.00

    @pytest.mark.asyncio
    async def test_drg_price_foreign_key_constraint(self, db_session):
        """Test that foreign key constraint is enforced."""
        # Test non-existent provider
        drg_price = DRGPrice(
            provider_id="999999",  # Non-existent provider
            drg_id=470,
            total_discharges=10,
            average_covered_charges=50000.00,
            average_total_payments=10000.00,
            average_medicare_payments=8000.00,
        )

        with pytest.raises(IntegrityError):
            db_session.add(drg_price)
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_drg_price_drg_foreign_key_constraint(self, db_session):
        """Test that DRG foreign key constraint is enforced."""
        # First create a provider
        provider = Provider(
            provider_id="330001",
            provider_name="Test Hospital",
            provider_city="New York",
            provider_state="NY",
            provider_zip_code="10001",
        )
        db_session.add(provider)
        await db_session.commit()

        # Test non-existent DRG
        drg_price = DRGPrice(
            provider_id="330001",
            drg_id=999,  # Non-existent DRG
            total_discharges=10,
            average_covered_charges=50000.00,
            average_total_payments=10000.00,
            average_medicare_payments=8000.00,
        )

        with pytest.raises(IntegrityError):
            db_session.add(drg_price)
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_drg_price_required_fields(self, db_session):
        """Test that required fields are enforced."""
        # First create a provider and DRG
        provider = Provider(
            provider_id="330001",
            provider_name="Test Hospital",
            provider_city="New York",
            provider_state="NY",
            provider_zip_code="10001",
        )
        db_session.add(provider)

        drg = DRG(drg_id=470, ms_drg_definition="TEST DRG")
        db_session.add(drg)
        await db_session.commit()

        # Try to create DRGPrice with missing required fields
        drg_price = DRGPrice(provider_id="330001", drg_id=470)

        with pytest.raises(IntegrityError):
            db_session.add(drg_price)
            await db_session.commit()


class TestRatingModel:
    """Unit tests for Rating model."""

    @pytest.mark.asyncio
    async def test_rating_creation(self, db_session):
        """Test creating a rating with valid data."""
        # First create a provider
        provider = Provider(
            provider_id="330001",
            provider_name="Test Hospital",
            provider_city="New York",
            provider_state="NY",
            provider_zip_code="10001",
        )
        db_session.add(provider)
        await db_session.commit()

        rating = Rating(provider_id="330001", rating=8)

        db_session.add(rating)
        await db_session.commit()

        # Verify rating was created
        assert rating.provider_id == "330001"
        assert rating.rating == 8

    @pytest.mark.asyncio
    async def test_rating_range_constraint(self, db_session):
        """Test that rating range constraint is enforced."""
        # First create a provider
        provider = Provider(
            provider_id="330001",
            provider_name="Test Hospital",
            provider_city="New York",
            provider_state="NY",
            provider_zip_code="10001",
        )
        db_session.add(provider)
        await db_session.commit()

        # Test rating too low
        rating_low = Rating(provider_id="330001", rating=0)
        db_session.add(rating_low)
        with pytest.raises(IntegrityError):
            await db_session.commit()
        await db_session.rollback()

        # Test rating too high
        rating_high = Rating(provider_id="330001", rating=11)
        db_session.add(rating_high)
        with pytest.raises(IntegrityError):
            await db_session.commit()
        await db_session.rollback()

    @pytest.mark.asyncio
    async def test_rating_foreign_key_constraint(self, db_session):
        """Test that foreign key constraint is enforced."""
        rating = Rating(provider_id="999999", rating=8)  # Non-existent provider

        with pytest.raises(IntegrityError):
            db_session.add(rating)
            await db_session.commit()


class TestZipCodeModel:
    """Unit tests for ZipCode model."""

    @pytest.mark.asyncio
    async def test_zip_code_creation(self, db_session):
        """Test creating a ZIP code with valid data."""
        zip_code = ZipCode(zip_code="10001", latitude=40.7505, longitude=-73.9934)

        db_session.add(zip_code)
        await db_session.commit()

        # Verify ZIP code was created
        assert zip_code.zip_code == "10001"
        assert zip_code.latitude == 40.7505
        assert zip_code.longitude == -73.9934

    @pytest.mark.asyncio
    async def test_zip_code_primary_key(self, db_session):
        """Test that zip_code is the primary key."""
        zip_code1 = ZipCode(zip_code="10001", latitude=40.7505, longitude=-73.9934)
        zip_code2 = ZipCode(zip_code="10001", latitude=40.7506, longitude=-73.9935)  # Same ZIP code

        db_session.add(zip_code1)
        await db_session.commit()

        with pytest.raises(IntegrityError):
            db_session.add(zip_code2)
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_zip_code_required_fields(self, db_session):
        """Test that required fields are enforced."""
        zip_code = ZipCode()

        with pytest.raises(IntegrityError):
            db_session.add(zip_code)
            await db_session.commit()


class TestModelRelationships:
    """Unit tests for model relationships."""

    @pytest.mark.asyncio
    async def test_provider_drg_relationship(self, db_session):
        """Test Provider-DRGPrice relationship."""
        from sqlalchemy import select

        # Create provider
        provider = Provider(
            provider_id="330001",
            provider_name="Test Hospital",
            provider_city="New York",
            provider_state="NY",
            provider_zip_code="10001",
        )
        db_session.add(provider)

        # Create DRG
        drg = DRG(drg_id=470, ms_drg_definition="TEST DRG")
        db_session.add(drg)
        await db_session.commit()

        # Create DRG price
        drg_price = DRGPrice(
            provider_id="330001",
            drg_id=470,
            total_discharges=10,
            average_covered_charges=50000.00,
            average_total_payments=10000.00,
            average_medicare_payments=8000.00,
        )
        db_session.add(drg_price)
        await db_session.commit()

        # Test relationship by querying directly
        result = await db_session.execute(select(DRGPrice).where(DRGPrice.provider_id == "330001"))
        drg_prices = result.scalars().all()

        assert len(drg_prices) == 1
        assert drg_prices[0].drg_id == 470

    @pytest.mark.asyncio
    async def test_provider_rating_relationship(self, db_session):
        """Test Provider-Rating relationship."""
        from sqlalchemy import select

        # Create provider
        provider = Provider(
            provider_id="330001",
            provider_name="Test Hospital",
            provider_city="New York",
            provider_state="NY",
            provider_zip_code="10001",
        )
        db_session.add(provider)
        await db_session.commit()

        # Create rating
        rating = Rating(provider_id="330001", rating=8)
        db_session.add(rating)
        await db_session.commit()

        # Test relationship by querying directly
        result = await db_session.execute(select(Rating).where(Rating.provider_id == "330001"))
        ratings = result.scalars().all()

        assert len(ratings) == 1
        assert ratings[0].rating == 8
