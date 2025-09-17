from __future__ import annotations

from sqlalchemy import ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import VARCHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class DRGPrice(Base):
    __tablename__ = "drg_prices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    provider_id: Mapped[str] = mapped_column(
        VARCHAR(6), ForeignKey("providers.provider_id"), nullable=False
    )
    ms_drg_definition: Mapped[str] = mapped_column(String(10), nullable=False)
    total_discharges: Mapped[int] = mapped_column(Integer, nullable=False)
    average_covered_charges: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False
    )
    average_total_payments: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False
    )
    average_medicare_payments: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False
    )

    # Relationships
    provider: Mapped[Provider] = relationship(  # noqa: F821
        "Provider", back_populates="drg_prices"
    )

    # Indexes for performance
    __table_args__ = (
        Index("idx_drg_provider_id", "provider_id"),
        Index("idx_drg_definition", "ms_drg_definition"),
        Index("idx_drg_provider_definition", "provider_id", "ms_drg_definition"),
    )

    def __repr__(self) -> str:
        return f"<DRGPrice(id={self.id}, provider_id='{self.provider_id}', drg='{self.ms_drg_definition}')>"
