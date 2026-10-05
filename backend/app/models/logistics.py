"""
SQLAlchemy 2.0 ORM Models for AgriClutch Logistics, Storage & Perishability Subsystem.
Defines persistent entities for transport modes, rates, storage facilities, route geometry,
perishability parameters, and logistics scenario audit trails.
SIH26132 — Strengthening Market Linkages and Price Discovery for Farmers.
"""

from datetime import date, datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import JSON, Boolean, Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class TransportModeModel(Base):
    """Vehicle or haulage equipment specification."""

    __tablename__ = "transport_modes"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(128), nullable=False)
    vehicle_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    capacity_kg: Mapped[float] = mapped_column(Float, nullable=False)
    base_dispatch_fee: Mapped[float] = mapped_column(Float, nullable=False)
    cost_per_km: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    cost_per_km_tonne: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    speed_kmh: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    temperature_controlled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    active_status: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    source_name: Mapped[str] = mapped_column(String(128), nullable=False)
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


class TransportRateModel(Base):
    """Corridor-specific freight rate schedule."""

    __tablename__ = "transport_rates"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    mode_id: Mapped[str] = mapped_column(String(64), ForeignKey("transport_modes.id"), nullable=False, index=True)
    origin_region: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    destination_region: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    effective_rate_per_km: Mapped[float] = mapped_column(Float, nullable=False)
    effective_rate_per_quintal: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    effective_date: Mapped[date] = mapped_column(Date, nullable=False)
    provenance_status: Mapped[str] = mapped_column(String(32), default="DEMO", nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class StorageFacilityModel(Base):
    """Storage warehouse, silo, or cold-chain holding unit."""

    __tablename__ = "storage_facilities"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    facility_name: Mapped[str] = mapped_column(String(128), nullable=False)
    storage_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    location: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_capacity_kg: Mapped[float] = mapped_column(Float, nullable=False)
    available_capacity_kg: Mapped[float] = mapped_column(Float, nullable=False)
    cost_per_kg_day: Mapped[float] = mapped_column(Float, nullable=False)
    min_duration_days: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    max_duration_days: Mapped[int] = mapped_column(Integer, default=90, nullable=False)
    temperature_celsius: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    humidity_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    active_status: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    source_name: Mapped[str] = mapped_column(String(128), nullable=False)
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


class LogisticsRouteModel(Base):
    """Documented route geometry and distance benchmark."""

    __tablename__ = "logistics_routes"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    origin_name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    destination_name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    origin_lat: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    origin_lon: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    destination_lat: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    destination_lon: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    straight_line_distance_km: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    road_distance_km: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    typical_duration_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    provenance_status: Mapped[str] = mapped_column(String(32), default="DEMO", nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class PerishabilityParameterModel(Base):
    """Calibrated or configured decay parameters for a crop and storage environment."""

    __tablename__ = "perishability_parameters"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    commodity_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    storage_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    decay_parameter_delta: Mapped[float] = mapped_column(Float, nullable=False)
    quality_decay_beta: Mapped[float] = mapped_column(Float, nullable=False)
    equation: Mapped[str] = mapped_column(String(256), nullable=False)
    assumptions: Mapped[str] = mapped_column(String(256), nullable=False)
    source_name: Mapped[str] = mapped_column(String(128), nullable=False)
    calibration_status: Mapped[str] = mapped_column(String(32), default="NOT_CALIBRATED", nullable=False)
    provenance_status: Mapped[str] = mapped_column(String(32), default="DEMO", nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class LogisticsScenarioAuditModel(Base):
    """Audit log of evaluated multi-stage logistics pathways."""

    __tablename__ = "logistics_scenario_audits"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    produce_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    destination_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    scenario_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    scenario_name: Mapped[str] = mapped_column(String(128), nullable=False)
    storage_facility_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    transport_mode_id: Mapped[str] = mapped_column(String(64), nullable=False)
    distance_km: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    transit_duration_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    storage_duration_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    delivered_quantity_kg: Mapped[float] = mapped_column(Float, nullable=False)
    final_quality_factor: Mapped[float] = mapped_column(Float, nullable=False)
    logistics_cost: Mapped[float] = mapped_column(Float, nullable=False)
    storage_cost: Mapped[float] = mapped_column(Float, nullable=False)
    total_pathway_cost: Mapped[float] = mapped_column(Float, nullable=False)
    feasibility_status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    economic_status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    provenance_status: Mapped[str] = mapped_column(String(32), default="DEMO", nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    audit_payload: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
