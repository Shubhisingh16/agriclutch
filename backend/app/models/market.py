"""
Market (Mandi) ORM Model for AgriClutch.
Represents APMC physical markets, geolocation coordinates, and DCA mapping.
"""

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class MarketModel(Base):
    """SQLAlchemy model for physical APMC mandis."""

    __tablename__ = "mandis"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    apmc_code: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    state: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    district: Mapped[str] = mapped_column(String(64), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    is_terminal_market: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    dca_centre_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_market_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
