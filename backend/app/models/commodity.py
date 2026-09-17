"""
Commodity ORM Model for AgriClutch.
Represents crops, categorizations, perishability rates, and holding durability.
"""

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class CommodityModel(Base):
    """SQLAlchemy model for agricultural commodities."""

    __tablename__ = "commodities"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    hindi_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    category: Mapped[str] = mapped_column(String(32), nullable=False)
    default_spoilage_rate: Mapped[float] = mapped_column(Float, nullable=False)
    max_ambient_holding_days: Mapped[int] = mapped_column(Integer, nullable=False)
    standard_moisture_pct: Mapped[float] = mapped_column(Float, nullable=False, default=14.0)
    price_unit: Mapped[str] = mapped_column(String(16), nullable=False, default="INR_PER_KG")
    weight_unit: Mapped[str] = mapped_column(String(16), nullable=False, default="KG")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
