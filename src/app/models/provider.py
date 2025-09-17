from __future__ import annotations

from sqlalchemy import Index, String
from sqlalchemy.dialects.postgresql import VARCHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Provider(Base):
    __tablename__ = "providers"

    provider_id: Mapped[str] = mapped_column(VARCHAR(6), primary_key=True)
    provider_name: Mapped[str] = mapped_column(String(255), nullable=False)
    provider_city: Mapped[str] = mapped_column(String(100), nullable=False)
    provider_state: Mapped[str] = mapped_column(String(2), nullable=False)
    provider_zip_code: Mapped[str] = mapped_column(String(10), nullable=False)

    # Relationships
    drg_prices: Mapped[list[DRGPrice]] = relationship(  # noqa: F821
        "DRGPrice", back_populates="provider", cascade="all, delete-orphan"
    )
    ratings: Mapped[list[Rating]] = relationship(  # noqa: F821
        "Rating", back_populates="provider", cascade="all, delete-orphan"
    )

    # Indexes for performance
    __table_args__ = (
        Index("idx_provider_zip_code", "provider_zip_code"),
        Index("idx_provider_state", "provider_state"),
        Index("idx_provider_city", "provider_city"),
    )

    def __repr__(self) -> str:
        return (
            f"<Provider(provider_id='{self.provider_id}', name='{self.provider_name}')>"
        )
