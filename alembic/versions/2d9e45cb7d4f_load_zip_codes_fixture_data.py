"""load_zip_codes_fixture_data

Revision ID: 2d9e45cb7d4f
Revises: ad8300609de2
Create Date: 2025-09-17 17:48:38.536884

"""

from pathlib import Path

import pandas as pd
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "2d9e45cb7d4f"
down_revision = "ad8300609de2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Load ZIP code data fixture into the database."""
    # Use the comprehensive US ZIP codes file
    zip_file = "USZipsWithLatLon_20231227.csv"
    if not Path(zip_file).exists():
        print(f"ZIP code data file not found: {zip_file}")
        print("Please ensure USZipsWithLatLon_20231227.csv is in the project root")
        return

    try:
        # Load ZIP code data
        df = pd.read_csv(zip_file)
        print(f"Loading {len(df)} US ZIP codes...")

        # Filter for US ZIP codes only and clean the data
        df = df[df["country code"] == "US"].copy()
        df = df.dropna(subset=["postal code", "latitude", "longitude"])

        # Clean postal codes (remove any non-numeric characters and ensure 5 digits)
        df["postal code"] = df["postal code"].astype(str).str.strip()
        df = df[df["postal code"].str.match(r"^\d{5}$")]  # Only 5-digit ZIP codes

        print(f"Processing {len(df)} valid US ZIP codes...")

        # Insert ZIP code data using raw SQL
        connection = op.get_bind()

        # Use batch processing for better performance
        batch_size = 1000
        total_inserted = 0

        for i in range(0, len(df), batch_size):
            batch = df.iloc[i : i + batch_size]

            for _, row in batch.iterrows():
                zip_code = row["postal code"]
                latitude = float(row["latitude"])
                longitude = float(row["longitude"])

                connection.execute(
                    sa.text(
                        """
                        INSERT INTO zip_codes (zip_code, latitude, longitude)
                        VALUES (:zip_code, :latitude, :longitude)
                        ON CONFLICT (zip_code) DO NOTHING
                    """
                    ),
                    {
                        "zip_code": zip_code,
                        "latitude": latitude,
                        "longitude": longitude,
                    },
                )
                total_inserted += 1

            if i % 5000 == 0:  # Progress update every 5000 records
                print(f"Processed {i} ZIP codes...")

        print(f"Successfully loaded {total_inserted} US ZIP codes into database")

    except Exception as e:
        print(f"Error loading ZIP code fixture: {e}")
        # Don't fail the migration if ZIP code loading fails
        pass


def downgrade() -> None:
    """Remove ZIP code data from the database."""
    op.execute(sa.text("DELETE FROM zip_codes"))
