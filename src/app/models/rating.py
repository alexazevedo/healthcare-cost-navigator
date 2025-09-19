from __future__ import annotations

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer
from sqlalchemy.dialects.postgresql import VARCHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.database import Base


class Rating(Base):
    __tablename__ = "ratings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    provider_id: Mapped[str] = mapped_column(VARCHAR(6), ForeignKey("providers.provider_id"), nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationships
    provider: Mapped[Provider] = relationship("Provider", back_populates="ratings")  # noqa: F821

    # Constraints and indexes
    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 10", name="check_rating_range"),
        Index("idx_rating_provider_id", "provider_id"),
        Index("idx_rating_value", "rating"),
    )

    def __repr__(self) -> str:
        return f"<Rating(id={self.id}, provider_id='{self.provider_id}', rating={self.rating})>"
