"""Create zip_codes table for geographic data

Revision ID: ad8300609de2
Revises: dd4c46ba12a3
Create Date: 2025-09-17 15:25:03.524805

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "ad8300609de2"
down_revision = "dd4c46ba12a3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create zip_codes table
    op.create_table(
        "zip_codes",
        sa.Column("zip_code", sa.VARCHAR(length=10), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint("zip_code"),
    )

    # Create indexes for performance
    op.create_index("idx_zip_latitude", "zip_codes", ["latitude"])
    op.create_index("idx_zip_longitude", "zip_codes", ["longitude"])
    op.create_index("idx_zip_coordinates", "zip_codes", ["latitude", "longitude"])


def downgrade() -> None:
    # Drop zip_codes table
    op.drop_index("idx_zip_coordinates", table_name="zip_codes")
    op.drop_index("idx_zip_longitude", table_name="zip_codes")
    op.drop_index("idx_zip_latitude", table_name="zip_codes")
    op.drop_table("zip_codes")
