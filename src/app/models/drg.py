from __future__ import annotations

from sqlalchemy import Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.database import Base


class DRG(Base):
    __tablename__ = "drgs"

    drg_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ms_drg_definition: Mapped[str] = mapped_column(String(255), nullable=False)

    # Relationships
    drg_prices: Mapped[list[DRGPrice]] = relationship("DRGPrice", back_populates="drg", cascade="all, delete-orphan")

    __table_args__ = (Index("idx_drgs_definition", "ms_drg_definition"),)

    def __repr__(self) -> str:
        return f"<DRG(drg_id='{self.drg_id}', definition='{self.ms_drg_definition[:40]}...')>"
