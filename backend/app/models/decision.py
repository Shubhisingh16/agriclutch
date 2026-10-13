"""
AgriClutch Step 14: Decision Intelligence, Selling Plans & What-If Simulator Database Models.
SQLAlchemy 2.0 declarative ORM models preserving full auditability, inputs, and solver state.
SIH26132 — Strengthening Market Linkages and Price Discovery for Farmers.
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class OptimalSellingPlanModel(Base):
    """
    Persisted record of an optimal selling plan.
    Stores comprehensive solver run results, economic metrics, and reproducibility hashes.
    """
    __tablename__ = "optimal_selling_plans"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: f"plan_{uuid.uuid4().hex[:12]}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    input_snapshot_id: Mapped[str] = mapped_column(String(64), nullable=False, default="snap_default")

    # Farmer Produce Spec
    commodity_id: Mapped[str] = mapped_column(String(32), nullable=False)
    variety: Mapped[str] = mapped_column(String(64), default="Standard", nullable=False)
    quality_grade: Mapped[str] = mapped_column(String(32), default="GRADE_A", nullable=False)
    total_supply_kg: Mapped[float] = mapped_column(Float, nullable=False)

    # Preferences
    decision_horizon_days: Mapped[int] = mapped_column(Integer, default=7, nullable=False)
    risk_preference: Mapped[str] = mapped_column(String(32), default="RISK_AWARE", nullable=False)
    liquidity_preference: Mapped[str] = mapped_column(String(32), default="BALANCED", nullable=False)

    # Aggregated Quantities & Economics
    total_allocated_kg: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_unallocated_kg: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_effective_kg: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    expected_gross_revenue: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_friction_cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    expected_total_nrv: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    risk_adjusted_nrv: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Solver Run Metadata
    solver_status: Mapped[str] = mapped_column(String(32), default="OPTIMAL", nullable=False)
    validation_status: Mapped[str] = mapped_column(String(32), default="PASSED", nullable=False)
    solver_message: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    solver_duration_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    solver_version: Mapped[str] = mapped_column(String(64), default="AgriClutch-LinearOptimizer-1.0", nullable=False)
    configuration_hash: Mapped[str] = mapped_column(String(64), default="", nullable=False)

    # Text & Structure
    executive_summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    structured_explanations: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    risk_metrics_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    constraint_summary_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)

    # Provenance
    provenance_status: Mapped[str] = mapped_column(String(32), default="DEMO", nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    allocations = relationship("PlanAllocationModel", back_populates="plan", cascade="all, delete-orphan")


class PlanAllocationModel(Base):
    """
    Individual segment allocated by the optimization solver.
    """
    __tablename__ = "plan_allocations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: f"alloc_{uuid.uuid4().hex[:8]}")
    plan_id: Mapped[str] = mapped_column(String(64), ForeignKey("optimal_selling_plans.id"), nullable=False)

    destination_type: Mapped[str] = mapped_column(String(32), nullable=False)  # BUYER / MARKET / STORAGE_HOLD
    destination_id: Mapped[str] = mapped_column(String(64), nullable=False)
    destination_name: Mapped[str] = mapped_column(String(128), nullable=False)
    sale_day_offset: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sale_date: Mapped[str] = mapped_column(String(32), nullable=False)

    # Quantities
    allocated_quantity_kg: Mapped[float] = mapped_column(Float, nullable=False)
    effective_quantity_kg: Mapped[float] = mapped_column(Float, nullable=False)
    allocation_percentage: Mapped[float] = mapped_column(Float, nullable=False)

    # Economics
    expected_price_per_kg: Mapped[float] = mapped_column(Float, nullable=False)
    expected_nrv_per_kg: Mapped[float] = mapped_column(Float, nullable=False)
    gross_revenue: Mapped[float] = mapped_column(Float, nullable=False)
    total_freight_cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_storage_cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_handling_cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_market_fee: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    expected_total_nrv: Mapped[float] = mapped_column(Float, nullable=False)

    # Decay & Quality
    quality_factor: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    mass_retention_factor: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)

    # Context & Explanation
    pathway_id: Mapped[str] = mapped_column(String(64), nullable=True)
    buyer_id: Mapped[str] = mapped_column(String(64), nullable=True)
    market_id: Mapped[str] = mapped_column(String(64), nullable=True)
    storage_facility_id: Mapped[str] = mapped_column(String(64), nullable=True)
    explanation: Mapped[str] = mapped_column(Text, default="", nullable=False)

    # Relationship
    plan = relationship("OptimalSellingPlanModel", back_populates="allocations")
