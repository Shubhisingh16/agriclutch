"""
Arrival Observation ORM Model for AgriClutch.
Hypertable-ready model for physical market arrivals and logistics volume tracking.
"""

from datetime import date, datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ArrivalObservationModel(Base):
    """SQLAlchemy model for daily APMC physical arrival volumes."""

    __tablename__ = "mandi_daily_arrivals"

    observation_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    source_name: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_record_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    source_market_id: Mapped[str] = mapped_column(String(128), nullable=False)
    source_commodity_id: Mapped[str] = mapped_column(String(128), nullable=False)

    record_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    market_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("mandis.id", ondelete="CASCADE"), nullable=False, index=True
    )
    commodity_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("commodities.id", ondelete="CASCADE"), nullable=False, index=True
    )

    arrival_tonnes: Mapped[float] = mapped_column(Float, nullable=False)
    original_arrival_unit: Mapped[str] = mapped_column(String(32), nullable=False, default="Tonnes")
    normalized_arrival_unit: Mapped[str] = mapped_column(
        String(32), nullable=False, default="METRIC_TONNE"
    )
    truck_count_estimate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("record_date", "market_id", "commodity_id", name="uq_mandi_arrival_natural"),
    )
