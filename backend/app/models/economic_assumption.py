"""
Economic Assumption ORM Model for AgriClutch.
Persists freight tariffs, storage rates, handling porterage, APMC cess, and decay parameters.
All records preserve auditable provenance metadata.
SIH26132 — Market Linkages and Price Discovery for Farmers.
"""

from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class EconomicAssumptionModel(Base):
    """SQLAlchemy model for economic parameters and provenance."""

    __tablename__ = "economic_assumptions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    category: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    parameter_key: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    commodity_id: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, index=True)
    market_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(32), nullable=False)
    source: Mapped[str] = mapped_column(String(128), nullable=False)
    provenance_status: Mapped[str] = mapped_column(String(32), nullable=False, default="DEMO")
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
