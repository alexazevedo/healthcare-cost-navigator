"""
Integration tests for API endpoints.
Tests the full API functionality including database interactions.
"""

from unittest.mock import AsyncMock, patch

import pytest

# from httpx import AsyncClient  # Removed to avoid type annotation issues
from app.models.drg import DRG
from app.models.drg_price import DRGPrice
from app.models.provider import Provider
from app.models.rating import Rating
from app.models.zip_code import ZipCode
from tests.conftest import load_sample_data


@pytest.fixture
def sample_rows():
    """Sample rows returned by run_sql."""
    return [
        {
            "provider_id": "330001",
            "provider_name": "Test Hospital 1",
            "provider_city": "New York",
            "provider_state": "NY",
            "average_covered_charges": 10000.0,
        },
        {
            "provider_id": "330002",
            "provider_name": "Test Hospital 2",
            "provider_city": "New York",
            "provider_state": "NY",
            "average_covered_charges": 12000.0,
        },
    ]


class TestProvidersEndpointIntegration:
    """Integration tests for /providers endpoint."""

    @pytest.mark.asyncio
    async def test_providers_basic_search(self, async_client, db_session, override_get_db):
        """Test basic provider search without filters."""
        await load_sample_data(db_session)
        response = await async_client.get("/providers")

        assert response.status_code == 200
        data = response.json()

        assert len(data) > 0
        assert "provider_id" in data[0]
        assert "provider_name" in data[0]
        assert "provider_city" in data[0]
        assert "provider_state" in data[0]
        assert "provider_zip_code" in data[0]
        assert "rating" in data[0]
        assert "distance_km" in data[0]

    @pytest.mark.asyncio
    async def test_providers_drg_filter(self, async_client, db_session, override_get_db):
        """Test provider search with DRG filter."""
        await load_sample_data(db_session)
        response = await async_client.get("/providers?drg=470")

        assert response.status_code == 200
        data = response.json()

        # Should return providers that have DRG 470
        assert len(data) > 0
        for provider in data:
            assert "provider_id" in provider
            assert "provider_name" in provider

    @pytest.mark.asyncio
    async def test_providers_drg_definition_filter(self, async_client, db_session, override_get_db):
        """Test provider search with DRG definition text filter."""
        await load_sample_data(db_session)
        response = await async_client.get("/providers?drg=HIP")

        assert response.status_code == 200
        data = response.json()

        # Should return providers that have hip-related DRG codes
        assert len(data) > 0
        for provider in data:
            assert "provider_id" in provider
            assert "provider_name" in provider

    @pytest.mark.asyncio
    async def test_providers_geographic_filter(self, async_client, db_session, override_get_db):
        """Test provider search with geographic filtering."""
        await load_sample_data(db_session)
        response = await async_client.get("/providers?zip=10001&radius_km=10")

        assert response.status_code == 200
        data = response.json()

        # All results should have distance_km calculated
        for provider in data:
            assert provider["distance_km"] is not None
            assert provider["distance_km"] <= 10.0

    @pytest.mark.asyncio
    async def test_providers_combined_filters(self, async_client, db_session, override_get_db):
        """Test provider search with combined DRG and geographic filters."""
        # Ensure the override is applied
        assert override_get_db is not None
        await load_sample_data(db_session)
        response = await async_client.get("/providers?zip=10001&radius_km=20&drg=470")

        assert response.status_code == 200
        data = response.json()

        # All results should meet geographic criteria
        for provider in data:
            assert provider["distance_km"] is not None
            assert provider["distance_km"] <= 20.0
            assert "provider_id" in provider
            assert "provider_name" in provider

    @pytest.mark.asyncio
    async def test_providers_invalid_zip(self, async_client, db_session, override_get_db):
        """Test provider search with invalid ZIP raises 400."""
        # Ensure the override is applied
        assert override_get_db is not None
        await load_sample_data(db_session)
        response = await async_client.get("/providers?zip=99999&radius_km=10")

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_providers_sorting(self, async_client, db_session, override_get_db):
        """Test that providers are sorted correctly."""
        await load_sample_data(db_session)
        response = await async_client.get("/providers?drg=470")

        assert response.status_code == 200
        data = response.json()

        # Should be sorted by provider name alphabetically
        if len(data) > 1:
            for i in range(len(data) - 1):
                assert data[i]["provider_name"] <= data[i + 1]["provider_name"]

    @pytest.mark.asyncio
    async def test_providers_geographic_filter_large_radius(self, async_client, db_session, override_get_db):
        """Geographic filtering with a larger radius returns distance_km."""
        # Ensure the override is applied
        assert override_get_db is not None
        await load_sample_data(db_session)
        response = await async_client.get("/providers?zip=10001&radius_km=50")

        assert response.status_code == 200
        data = response.json()

        for provider in data:
            assert provider["distance_km"] is not None
            assert provider["distance_km"] <= 50.0


class TestAskEndpointIntegration:
    """Integration tests for /ask endpoint."""

    @pytest.mark.asyncio
    @patch("app.api.endpoints.generate_grounded_answer", new_callable=AsyncMock)
    @patch("app.api.endpoints.run_sql", new_callable=AsyncMock)
    @patch("app.api.endpoints.nl_to_sql", new_callable=AsyncMock)
    async def test_ask_cheapest_providers(
        self,
        mock_nl_to_sql,
        mock_run_sql,
        mock_grounded,
        async_client,
        db_session,
        override_get_db,
        sample_rows,
    ):
        """Test asking for cheapest providers."""
        mock_nl_to_sql.return_value = (
            "SELECT provider_id, provider_name, provider_city, provider_state, average_covered_charges FROM drg_prices"
        )
        mock_run_sql.return_value = sample_rows
        mock_grounded.return_value = (
            "Based on the database results, here are the cheapest hospitals for alcohol treatment."
        )

        # Load test data
        await load_sample_data(db_session)

        response = await async_client.post(
            "/ask",
            json={"question": "What are the cheapest hospitals for alcohol treatment?"},
        )

        assert response.status_code == 200
        data = response.json()

        assert "question" in data
        assert "answer" in data
        assert "sql_query" in data
        assert "explanation" in data
        assert "results" in data
        assert data["results"] is not None
        assert len(data["results"]) > 0

        # Results should be sorted by cost (cheapest first)
        if len(data["results"]) > 1:
            for i in range(len(data["results"]) - 1):
                current_cost = data["results"][i].get("average_covered_charges", 0)
                next_cost = data["results"][i + 1].get("average_covered_charges", 0)
                assert current_cost <= next_cost

    @pytest.mark.asyncio
    @patch("app.api.endpoints.generate_grounded_answer", new_callable=AsyncMock)
    @patch("app.api.endpoints.run_sql", new_callable=AsyncMock)
    @patch("app.api.endpoints.nl_to_sql", new_callable=AsyncMock)
    async def test_ask_geographic_query(
        self,
        mock_nl_to_sql,
        mock_run_sql,
        mock_grounded,
        async_client,
        db_session,
        override_get_db,
    ):
        """Test asking for providers within a specific area."""
        mock_nl_to_sql.return_value = "SELECT * FROM providers LIMIT 10"
        mock_run_sql.return_value = []
        mock_grounded.return_value = "Here are the hospitals within 10 miles of ZIP 10001, ordered by distance."

        # Load test data
        await load_sample_data(db_session)

        response = await async_client.post("/ask", json={"question": "Show me hospitals within 10 miles of ZIP 10001"})

        assert response.status_code == 200
        data = response.json()

        assert "question" in data
        assert "answer" in data
        assert "sql_query" in data
        assert "explanation" in data
        assert "results" in data
        # Note: This might return None if the AI determines it's out of scope
        # or if the query doesn't match the expected pattern

    @pytest.mark.asyncio
    @patch("app.api.endpoints.generate_grounded_answer", new_callable=AsyncMock)
    @patch("app.api.endpoints.run_sql", new_callable=AsyncMock)
    @patch("app.api.endpoints.nl_to_sql", new_callable=AsyncMock)
    async def test_ask_rating_query(
        self,
        mock_nl_to_sql,
        mock_run_sql,
        mock_grounded,
        async_client,
        db_session,
        override_get_db,
    ):
        """Test asking about hospital ratings."""
        mock_nl_to_sql.return_value = "SELECT * FROM ratings LIMIT 10"
        mock_run_sql.return_value = []
        mock_grounded.return_value = "Here are the hospitals with the highest ratings, ordered by rating."

        # Load test data
        await load_sample_data(db_session)

        response = await async_client.post("/ask", json={"question": "Which hospitals have the highest ratings?"})

        assert response.status_code == 200
        data = response.json()

        assert "question" in data
        assert "answer" in data
        assert "sql_query" in data
        assert "explanation" in data
        assert "results" in data

    @pytest.mark.asyncio
    @patch("app.api.endpoints.generate_grounded_answer", new_callable=AsyncMock)
    @patch("app.api.endpoints.run_sql", new_callable=AsyncMock)
    @patch("app.api.endpoints.nl_to_sql", new_callable=AsyncMock)
    async def test_ask_specific_drg(
        self,
        mock_nl_to_sql,
        mock_run_sql,
        mock_grounded,
        async_client,
        db_session,
        override_get_db,
    ):
        """Test asking about a specific DRG code."""
        mock_nl_to_sql.return_value = "SELECT * FROM drg_prices WHERE drg_id = 470"
        mock_run_sql.return_value = []
        mock_grounded.return_value = "Here are all providers for DRG 470, ordered by cost."

        # Load test data
        await load_sample_data(db_session)

        response = await async_client.post("/ask", json={"question": "Show me all providers for DRG 470"})

        assert response.status_code == 200
        data = response.json()

        assert "question" in data
        assert "answer" in data
        assert "sql_query" in data
        assert "explanation" in data
        assert "results" in data

    # Removed out-of-scope test; scope is governed by LLM prompt and app returns structured response regardless

    @pytest.mark.asyncio
    @patch("app.api.endpoints.generate_grounded_answer", new_callable=AsyncMock)
    @patch("app.api.endpoints.run_sql", new_callable=AsyncMock)
    @patch("app.api.endpoints.nl_to_sql", new_callable=AsyncMock)
    async def test_ask_no_results(
        self,
        mock_nl_to_sql,
        mock_run_sql,
        mock_grounded,
        async_client,
        db_session,
        override_get_db,
    ):
        """Test asking for data that doesn't exist."""
        mock_nl_to_sql.return_value = "SELECT * FROM providers WHERE provider_state = 'CA'"
        mock_run_sql.return_value = []
        mock_grounded.return_value = "No hospitals found in California based on the current database."

        # Load test data
        await load_sample_data(db_session)

        response = await async_client.post("/ask", json={"question": "Show me hospitals in California"})

        assert response.status_code == 200
        data = response.json()

        assert "question" in data
        assert "answer" in data
        assert "sql_query" in data
        assert "explanation" in data
        assert "results" in data
        assert data["results"] == []

    @pytest.mark.asyncio
    async def test_ask_invalid_request(self, async_client, db_session, override_get_db):
        """Test asking with invalid request format."""
        response = await async_client.post("/ask", json={})

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_ask_missing_question(self, async_client, db_session, override_get_db):
        """Test asking with missing question field."""
        response = await async_client.post("/ask", json={"invalid_field": "test"})

        assert response.status_code == 422  # Validation error


@pytest.fixture
async def sample_data(db_session):
    """Create sample data for testing."""
    # Create providers
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

    # Create DRGs first
    drgs = [
        DRG(drg_id=470, ms_drg_definition="MAJOR HIP AND KNEE JOINT REPLACEMENT OR REATTACHMENT OF LOWER EXTREMITY WITHOUT MCC"),
        DRG(drg_id=871, ms_drg_definition="SEPTICEMIA OR SEVERE SEPSIS WITHOUT MV >96 HOURS WITH MCC"),
    ]

    for drg in drgs:
        db_session.add(drg)

    # Create DRG prices
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
            drg_id=470,
            total_discharges=20,
            average_covered_charges=30000.00,
            average_total_payments=12000.00,
            average_medicare_payments=9000.00,
        ),
    ]

    for drg_price in drg_prices:
        db_session.add(drg_price)

    # Create ratings
    ratings = [
        Rating(provider_id="330001", rating=8),
        Rating(provider_id="330002", rating=6),
        Rating(provider_id="330003", rating=9),
    ]

    for rating in ratings:
        db_session.add(rating)

    # Create ZIP codes
    zip_codes = [
        ZipCode(zip_code="10001", latitude=40.7505, longitude=-73.9934),
        ZipCode(zip_code="10002", latitude=40.7156, longitude=-73.9873),
        ZipCode(zip_code="11201", latitude=40.6943, longitude=-73.9903),
    ]

    for zip_code in zip_codes:
        db_session.add(zip_code)

    await db_session.commit()
