"""ZipCode model for geographic data."""

from __future__ import annotations

from sqlalchemy import Float, Index
from sqlalchemy.dialects.postgresql import VARCHAR
from sqlalchemy.orm import Mapped, mapped_column

from ..core.database import Base


class ZipCode(Base):
    """ZipCode model for storing ZIP code to latitude/longitude mapping."""

    __tablename__ = "zip_codes"

    zip_code: Mapped[str] = mapped_column(VARCHAR(10), primary_key=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)

    # Indexes for performance
    __table_args__ = (
        Index("idx_zip_latitude", "latitude"),
        Index("idx_zip_longitude", "longitude"),
        Index("idx_zip_coordinates", "latitude", "longitude"),
    )

    def __repr__(self) -> str:
        return f"<ZipCode(zip_code='{self.zip_code}', lat={self.latitude}, lon={self.longitude})>"
