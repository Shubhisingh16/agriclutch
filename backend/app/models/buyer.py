"""
SQLAlchemy 2.0 ORM Models for AgriClutch Buyer Intelligence Subsystem.
Defines persistent entities for buyers, commodity requirements, demands, supplies,
historical transactions, and match audits.
SIH26132 — Strengthening Market Linkages and Price Discovery for Farmers.
"""

from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import JSON, Boolean, Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class BuyerModel(Base):
    """Institutional, wholesale, or aggregator produce buyer."""

    __tablename__ = "buyers"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(128), nullable=False)
    buyer_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    location: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    active_status: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    source_name: Mapped[str] = mapped_column(String(128), nullable=False)
    source_record_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    source_reference: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    provenance_status: Mapped[str] = mapped_column(String(32), default="DEMO", nullable=False, index=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    requirements: Mapped[List["BuyerCommodityRequirementModel"]] = relationship(
        "BuyerCommodityRequirementModel", back_populates="buyer", cascade="all, delete-orphan"
    )
    demands: Mapped[List["BuyerDemandModel"]] = relationship(
        "BuyerDemandModel", back_populates="buyer", cascade="all, delete-orphan"
    )
    transactions: Mapped[List["BuyerTransactionModel"]] = relationship(
        "BuyerTransactionModel", back_populates="buyer", cascade="all, delete-orphan"
    )


class BuyerCommodityRequirementModel(Base):
    """Granular procurement specifications and commercial terms."""

    __tablename__ = "buyer_commodity_requirements"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    buyer_id: Mapped[str] = mapped_column(String(64), ForeignKey("buyers.id", ondelete="CASCADE"), nullable=False, index=True)
    commodity_id: Mapped[str] = mapped_column(String(32), ForeignKey("commodities.id"), nullable=False, index=True)
    variety: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    minimum_quantity_kg: Mapped[float] = mapped_column(Float, nullable=False)
    maximum_quantity_kg: Mapped[float] = mapped_column(Float, nullable=False)
    preferred_quality_grade: Mapped[str] = mapped_column(String(32), nullable=False)
    acceptable_quality_range: Mapped[List[str]] = mapped_column(JSON, nullable=False)
    required_from: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    required_until: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    delivery_mode: Mapped[str] = mapped_column(String(32), default="BUYER_PREMISES", nullable=False)
    delivery_location: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    delivery_latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    delivery_longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    price_basis: Mapped[str] = mapped_column(String(32), default="FIXED_QUOTE", nullable=False)
    quoted_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    currency: Mapped[str] = mapped_column(String(16), default="INR", nullable=False)
    price_unit: Mapped[str] = mapped_column(String(32), default="INR_PER_KG", nullable=False)
    payment_terms: Mapped[str] = mapped_column(String(32), default="NET_7_DAYS", nullable=False)
    validity_start: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    validity_end: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    source_name: Mapped[str] = mapped_column(String(128), nullable=False)
    source_record_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    source_reference: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    provenance_status: Mapped[str] = mapped_column(String(32), default="DEMO", nullable=False, index=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    buyer: Mapped["BuyerModel"] = relationship("BuyerModel", back_populates="requirements")


class BuyerDemandModel(Base):
    """Specific active demand order observation."""

    __tablename__ = "buyer_demands"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    buyer_id: Mapped[str] = mapped_column(String(64), ForeignKey("buyers.id", ondelete="CASCADE"), nullable=False, index=True)
    commodity_id: Mapped[str] = mapped_column(String(32), ForeignKey("commodities.id"), nullable=False, index=True)
    variety: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    quantity_kg: Mapped[float] = mapped_column(Float, nullable=False)
    quality_requirement: Mapped[str] = mapped_column(String(32), nullable=False)
    date_window_start: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    date_window_end: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    location: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    price_per_kg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    price_unit: Mapped[str] = mapped_column(String(32), default="INR_PER_KG", nullable=False)
    demand_type: Mapped[str] = mapped_column(String(32), default="DEMO_DEMAND", nullable=False, index=True)
    demand_status: Mapped[str] = mapped_column(String(32), default="ACTIVE", nullable=False, index=True)
    provenance_status: Mapped[str] = mapped_column(String(32), default="DEMO", nullable=False, index=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    buyer: Mapped["BuyerModel"] = relationship("BuyerModel", back_populates="demands")


class FarmerSupplyModel(Base):
    """Anonymous or FPO-aggregated supply availability profile."""

    __tablename__ = "farmer_supplies"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    supply_reference_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    commodity_id: Mapped[str] = mapped_column(String(32), ForeignKey("commodities.id"), nullable=False, index=True)
    variety: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    quantity_kg: Mapped[float] = mapped_column(Float, nullable=False)
    quality_grade: Mapped[str] = mapped_column(String(32), nullable=False)
    available_from: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    available_until: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    origin_location: Mapped[str] = mapped_column(String(128), nullable=False)
    origin_latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    origin_longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    storage_available: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    storage_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    provenance_status: Mapped[str] = mapped_column(String(32), default="DEMO", nullable=False, index=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )


class BuyerTransactionModel(Base):
    """Historical transaction record for reliability auditing."""

    __tablename__ = "buyer_transactions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    buyer_id: Mapped[str] = mapped_column(String(64), ForeignKey("buyers.id", ondelete="CASCADE"), nullable=False, index=True)
    commodity_id: Mapped[str] = mapped_column(String(32), ForeignKey("commodities.id"), nullable=False, index=True)
    order_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    agreed_quantity_kg: Mapped[float] = mapped_column(Float, nullable=False)
    delivered_quantity_kg: Mapped[float] = mapped_column(Float, nullable=False)
    agreed_price_per_kg: Mapped[float] = mapped_column(Float, nullable=False)
    price_unit: Mapped[str] = mapped_column(String(32), default="INR_PER_KG", nullable=False)
    fulfillment_status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    payment_status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    agreed_payment_due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    actual_payment_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    dispute_status: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    provenance_status: Mapped[str] = mapped_column(String(32), default="DEMO", nullable=False, index=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    buyer: Mapped["BuyerModel"] = relationship("BuyerModel", back_populates="transactions")


class BuyerMatchingRecordModel(Base):
    """Audit log of evaluated compatibility matches."""

    __tablename__ = "buyer_matching_records"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    supply_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    buyer_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    requirement_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    compatible_quantity_kg: Mapped[float] = mapped_column(Float, nullable=False)
    unmatched_supply_kg: Mapped[float] = mapped_column(Float, nullable=False)
    distance_km: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    constraint_status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    explanations: Mapped[List[str]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )


class DemandAggregateModel(Base):
    """Persisted regional and quality demand summaries."""

    __tablename__ = "demand_aggregates"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    commodity_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    region: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    total_demand_kg: Mapped[float] = mapped_column(Float, nullable=False)
    buyer_count: Mapped[int] = mapped_column(Integer, nullable=False)
    top_buyer_share_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    hhi_concentration: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    breakdown_by_quality: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    breakdown_by_type: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
