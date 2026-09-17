"""
Price Observation ORM Model for AgriClutch.
Hypertable-ready model preserving dual pricing (original vs normalized) and source provenance.
"""

from datetime import date, datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class PriceObservationModel(Base):
    """SQLAlchemy model for daily APMC mandi commodity prices."""

    __tablename__ = "mandi_daily_records"

    # Surrogate Primary Key
    observation_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Source Provenance
    source_name: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_record_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    source_market_id: Mapped[str] = mapped_column(String(128), nullable=False)
    source_commodity_id: Mapped[str] = mapped_column(String(128), nullable=False)

    # Dimensional Keys
    record_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    market_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("mandis.id", ondelete="CASCADE"), nullable=False, index=True
    )
    commodity_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("commodities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    variety: Mapped[str] = mapped_column(String(64), nullable=False, default="Common")
    grade: Mapped[str] = mapped_column(String(16), nullable=False, default="FAQ")

    # Original Source Observation
    original_modal_price: Mapped[float] = mapped_column(Float, nullable=False)
    original_min_price: Mapped[float] = mapped_column(Float, nullable=False)
    original_max_price: Mapped[float] = mapped_column(Float, nullable=False)
    original_price_unit: Mapped[str] = mapped_column(String(32), nullable=False)

    # Normalized Canonical Observation (INR/kg)
    normalized_modal_price: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    normalized_min_price: Mapped[float] = mapped_column(Float, nullable=False)
    normalized_max_price: Mapped[float] = mapped_column(Float, nullable=False)
    normalized_price_unit: Mapped[str] = mapped_column(
        String(32), nullable=False, default="INR_PER_KG"
    )

    # Analytical Metrics & Flags
    arrival_tonnes: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    is_interpolated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_outlier: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "record_date",
            "market_id",
            "commodity_id",
            "variety",
            "grade",
            name="uq_mandi_daily_natural",
        ),
    )
