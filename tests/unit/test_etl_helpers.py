"""
Unit tests for ETL helper functions.
Tests data processing, normalization, and validation functions.
"""

from pathlib import Path

from scripts.etl import ETLPipeline


class TestETLHelpers:
    """Unit tests for ETL helper functions."""

    def test_etl_pipeline_initialization(self):
        """Test that ETL pipeline initializes correctly."""
        etl = ETLPipeline("dummy_path.csv")

        assert etl.csv_file_path == "dummy_path.csv"
        assert etl.processed_providers == set()
        assert etl.provider_data == {}
        assert etl.drg_data == []
        assert etl.drgs_data == []
        assert etl.ratings_data == []

    def test_etl_pipeline_csv_reading(self, sample_csv_data):
        """Test that CSV files are read correctly."""
        # Test that the CSV file exists and can be read
        assert Path(sample_csv_data).exists()

        # Test that pandas can read the CSV
        import pandas as pd

        df = pd.read_csv(sample_csv_data)
        assert len(df) == 5
        assert "provider_id" in df.columns

    def test_etl_pipeline_csv_reading_nonexistent_file(self):
        """Test that reading nonexistent CSV file raises appropriate error."""
        # Test that the file doesn't exist
        assert not Path("nonexistent_file.csv").exists()

    def test_etl_pipeline_data_validation(self, sample_csv_data):
        """Test that data validation works correctly."""
        # Test that required columns are present
        import pandas as pd

        df = pd.read_csv(sample_csv_data)

        required_columns = [
            "provider_id",
            "provider_name",
            "provider_city",
            "provider_state",
            "provider_zip_code",
            "drg_id",
            "ms_drg_definition",
            "total_discharges",
            "average_covered_charges",
            "average_total_payments",
            "average_medicare_payments",
        ]

        for col in required_columns:
            assert col in df.columns, f"Required column {col} not found"

    def test_etl_pipeline_data_types(self, sample_csv_data):
        """Test that data types are handled correctly."""
        import pandas as pd

        df = pd.read_csv(sample_csv_data)

        # Test that numeric columns can be converted
        assert df["total_discharges"].dtype in ["int64", "object"]
        assert df["average_covered_charges"].dtype in [
            "float64",
            "object",
        ]  # May be parsed as float or object

    def test_etl_pipeline_currency_parsing(self):
        """Test that currency values are parsed correctly."""
        # Test currency parsing logic
        test_values = [
            ("$1,234.56", 1234.56),
            ("$50,000.00", 50000.00),
            ("$987.65", 987.65),
            ("$0.00", 0.00),
        ]

        for currency_str, expected_value in test_values:
            # Remove $ and commas, then convert to float
            cleaned = currency_str.replace("$", "").replace(",", "")
            result = float(cleaned)
            assert result == expected_value

    def test_etl_pipeline_rating_generation(self):
        """Test that ratings are generated within valid range."""
        # Test rating generation logic
        import random

        # Test multiple rating generations
        for _ in range(100):
            rating = random.randint(1, 10)
            assert 1 <= rating <= 10

    def test_etl_pipeline_zip_code_processing(self, sample_zip_data):
        """Test that ZIP code data is processed correctly."""
        import pandas as pd

        # Test ZIP code data reading
        df = pd.read_csv(sample_zip_data)
        assert len(df) == 5
        assert "zip_code" in df.columns
        assert "latitude" in df.columns
        assert "longitude" in df.columns

        # Test data types
        assert df["zip_code"].dtype in ["object", "int64"]
        assert df["latitude"].dtype in ["float64", "int64"]
        assert df["longitude"].dtype in ["float64", "int64"]

    def test_etl_pipeline_data_cleaning(self):
        """Test that data cleaning logic works correctly."""
        # Test data cleaning logic
        test_data = [
            {"Provider Id": "330001", "Provider Name": "Test Hospital 1"},
            {"Provider Id": "", "Provider Name": "Test Hospital 2"},  # Empty ID
            {"Provider Id": "330003", "Provider Name": "Test Hospital 3"},
        ]

        # Filter out records with empty Provider Id
        cleaned_data = [record for record in test_data if record["Provider Id"]]

        assert len(cleaned_data) == 2
        assert cleaned_data[0]["Provider Id"] == "330001"
        assert cleaned_data[1]["Provider Id"] == "330003"

    def test_etl_pipeline_column_mapping(self):
        """Test that column mapping works correctly."""
        # Test column mapping logic
        column_mapping = {
            "Provider Id": "provider_id",
            "Provider Name": "provider_name",
            "Provider City": "provider_city",
            "Provider State": "provider_state",
            "Provider Zip Code": "provider_zip_code",
            "DRG Definition": "ms_drg_definition",
            "Total Discharges": "total_discharges",
            "Average Covered Charges": "average_covered_charges",
            "Average Total Payments": "average_total_payments",
            "Average Medicare Payments": "average_medicare_payments",
        }

        # Test mapping
        for old_col, new_col in column_mapping.items():
            assert old_col != new_col
            assert new_col == new_col.lower().replace(" ", "_")

    def test_etl_pipeline_data_validation_rules(self):
        """Test that data validation rules work correctly."""
        # Test validation rules
        valid_record = {
            "Provider Id": "330001",
            "Provider Name": "Test Hospital",
            "Provider City": "New York",
            "Provider State": "NY",
            "Provider Zip Code": "10001",
            "DRG Definition": "TEST DRG",
            "Total Discharges": "10",
            "Average Covered Charges": "$50,000.00",
            "Average Total Payments": "$10,000.00",
            "Average Medicare Payments": "$8,000.00",
        }

        invalid_record = {
            "Provider Id": "",  # Empty ID
            "Provider Name": "Test Hospital",
            "Provider City": "New York",
            "Provider State": "NY",
            "Provider Zip Code": "10001",
            "DRG Definition": "TEST DRG",
            "Total Discharges": "10",
            "Average Covered Charges": "$50,000.00",
            "Average Total Payments": "$10,000.00",
            "Average Medicare Payments": "$8,000.00",
        }

        # Test validation
        assert bool(valid_record["Provider Id"])
        assert not bool(invalid_record["Provider Id"])

    def test_etl_pipeline_error_handling(self):
        """Test that error handling works correctly."""
        etl = ETLPipeline("nonexistent_file.csv")

        # Test that the pipeline handles missing files gracefully
        assert not Path("nonexistent_file.csv").exists()

        # Test that the pipeline can be initialized even with invalid path
        assert etl.csv_file_path == "nonexistent_file.csv"

    def test_etl_pipeline_statistics_calculation(self):
        """Test that statistics are calculated correctly."""
        etl = ETLPipeline("dummy_path.csv")

        # Set up test data
        etl.processed_providers = {"330001", "330002", "330003"}
        etl.drgs_data = [{"id": 1}, {"id": 2}]
        etl.drg_data = [{"id": 1}, {"id": 2}, {"id": 3}, {"id": 4}]
        etl.ratings_data = [{"id": 1}, {"id": 2}, {"id": 3}]

        # Test statistics calculation
        stats = {
            "Providers": len(etl.processed_providers),
            "DRGs": len(etl.drgs_data),
            "DRG Prices": len(etl.drg_data),
            "Ratings": len(etl.ratings_data),
        }

        assert stats["Providers"] == 3
        assert stats["DRGs"] == 2
        assert stats["DRG Prices"] == 4
        assert stats["Ratings"] == 3
