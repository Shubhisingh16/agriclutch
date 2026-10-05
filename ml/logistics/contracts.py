"""
AgriClutch Logistics, Storage & Perishability Feasibility Engine Contracts.
Strictly typed data structures, enums, and domain contracts for physical transit,
storage facility allocations, decoupled perishability decay, and multi-stage pathways.
SIH26132 — Strengthening Market Linkages and Price Discovery for Farmers.
"""

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Any


class StorageType(str, Enum):
    """Classification of crop storage facility environment."""
    AMBIENT = "AMBIENT"
    COLD = "COLD"
    VENTILATED = "VENTILATED"
    UNKNOWN = "UNKNOWN"


class DistanceType(str, Enum):
    """Geographic distance determination methodology."""
    STRAIGHT_LINE_DISTANCE = "STRAIGHT_LINE_DISTANCE"
    ESTIMATED_ROUTE_DISTANCE = "ESTIMATED_ROUTE_DISTANCE"
    ROAD_DISTANCE = "ROAD_DISTANCE"
    UNKNOWN_DISTANCE = "UNKNOWN_DISTANCE"


class TransitTimeStatus(str, Enum):
    """Provenance and determination of transit duration."""
    OBSERVED = "OBSERVED"
    CONFIGURED = "CONFIGURED"
    TRANSIT_TIME_UNAVAILABLE = "TRANSIT_TIME_UNAVAILABLE"


class FeasibilityStatus(str, Enum):
    """Deterministic physical and operational constraint satisfaction."""
    FEASIBLE = "FEASIBLE"
    PARTIALLY_FEASIBLE = "PARTIALLY_FEASIBLE"
    INFEASIBLE = "INFEASIBLE"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    UNAVAILABLE = "UNAVAILABLE"


class EconomicStatus(str, Enum):
    """Aggregate integrity and provenance status of commercial costing."""
    COMPLETE_EMPIRICAL = "COMPLETE_EMPIRICAL"
    COMPLETE_MIXED_PROVENANCE = "COMPLETE_MIXED_PROVENANCE"
    DEMO_ASSUMPTION = "DEMO_ASSUMPTION"
    INCOMPLETE = "INCOMPLETE"
    UNAVAILABLE = "UNAVAILABLE"


class ProvenanceStatus(str, Enum):
    """Authoritative source classification."""
    EMPIRICAL = "EMPIRICAL"
    OFFICIAL = "OFFICIAL"
    RESEARCH = "RESEARCH"
    CONFIGURED = "CONFIGURED"
    DEMO = "DEMO"
    UNAVAILABLE = "UNAVAILABLE"


class HandlingStageType(str, Enum):
    """Standardized physical produce handling operations."""
    LOADING = "LOADING"
    UNLOADING = "UNLOADING"
    SORTING = "SORTING"
    GRADING = "GRADING"
    PACKAGING = "PACKAGING"
    INTERMEDIATE_TRANSFER = "INTERMEDIATE_TRANSFER"
    STORAGE_ENTRY = "STORAGE_ENTRY"
    STORAGE_EXIT = "STORAGE_EXIT"


class CostUnitBasis(str, Enum):
    """Denomination basis for freight and handling fees."""
    INR_PER_KM = "INR_PER_KM"
    INR_PER_KG = "INR_PER_KG"
    INR_PER_QUINTAL = "INR_PER_QUINTAL"
    INR_PER_TONNE = "INR_PER_TONNE"
    INR_PER_KM_TONNE = "INR_PER_KM_TONNE"
    INR_PER_TRIP = "INR_PER_TRIP"
    INR_PER_KG_DAY = "INR_PER_KG_DAY"
    INR_FIXED = "INR_FIXED"


@dataclass(frozen=True)
class EconomicProvenance:
    """Verifiable lineage metadata for physical and economic parameters."""
    source_name: str
    source_record_id: str | None = None
    source_reference: str | None = None
    observed_at: str | None = None
    effective_from: str | None = None
    effective_to: str | None = None
    validity_range: str | None = None
    status: ProvenanceStatus = ProvenanceStatus.DEMO
    is_demo: bool = True
    justification: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_name": self.source_name,
            "source_record_id": self.source_record_id,
            "source_reference": self.source_reference,
            "observed_at": self.observed_at,
            "effective_from": self.effective_from,
            "effective_to": self.effective_to,
            "validity_range": self.validity_range,
            "status": self.status.value,
            "is_demo": self.is_demo,
            "justification": self.justification,
        }


@dataclass
class ProduceInput:
    """Farmer produce lot specification for logistics and shelf-life evaluation."""
    produce_id: str
    commodity_id: str
    quantity_kg: float
    quality_grade: str
    origin_location: str
    available_from: date
    available_until: date
    variety: str | None = None
    origin_latitude: float | None = None
    origin_longitude: float | None = None
    unit: str = "KG"
    initial_quality_factor: float = 1.0
    provenance: EconomicProvenance = field(
        default_factory=lambda: EconomicProvenance(source_name="FARMER_SUPPLY_SPEC")
    )

    def __post_init__(self) -> None:
        if self.quantity_kg <= 0:
            raise ValueError(f"Produce quantity must be strictly positive: {self.quantity_kg}")
        if self.available_from > self.available_until:
            raise ValueError(f"Available from ({self.available_from}) exceeds available until ({self.available_until})")
        if not (0.0 <= self.initial_quality_factor <= 1.0):
            raise ValueError(f"Initial quality factor must be in [0, 1]: {self.initial_quality_factor}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "produce_id": self.produce_id,
            "commodity_id": self.commodity_id,
            "variety": self.variety,
            "quantity_kg": self.quantity_kg,
            "quality_grade": self.quality_grade,
            "origin_location": self.origin_location,
            "origin_latitude": self.origin_latitude,
            "origin_longitude": self.origin_longitude,
            "available_from": self.available_from.isoformat(),
            "available_until": self.available_until.isoformat(),
            "unit": self.unit,
            "initial_quality_factor": self.initial_quality_factor,
            "provenance": self.provenance.to_dict(),
        }


@dataclass
class Destination:
    """Geographic delivery destination (buyer, mandi, storage facility)."""
    destination_id: str
    name: str
    destination_type: str  # "BUYER", "MANDI", "STORAGE_FACILITY", "HANDLING_HUB"
    location: str
    latitude: float | None = None
    longitude: float | None = None
    delivery_window_start: date | None = None
    delivery_window_end: date | None = None
    max_acceptable_distance_km: float | None = None
    provenance: EconomicProvenance = field(
        default_factory=lambda: EconomicProvenance(source_name="DESTINATION_SPEC")
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "destination_id": self.destination_id,
            "name": self.name,
            "destination_type": self.destination_type,
            "location": self.location,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "delivery_window_start": self.delivery_window_start.isoformat() if self.delivery_window_start else None,
            "delivery_window_end": self.delivery_window_end.isoformat() if self.delivery_window_end else None,
            "max_acceptable_distance_km": self.max_acceptable_distance_km,
            "provenance": self.provenance.to_dict(),
        }


@dataclass
class TransportModeSpec:
    """Vehicle or haulage equipment specification."""
    mode_id: str
    display_name: str
    vehicle_type: str  # "TRACTOR_TROLLEY", "LCV", "HEAVY_TRUCK", "REEFER"
    capacity_kg: float
    base_dispatch_fee: float
    cost_per_km: float | None = None
    cost_per_km_tonne: float | None = None
    speed_kmh: float | None = None
    temperature_controlled: bool = False
    provenance: EconomicProvenance = field(
        default_factory=lambda: EconomicProvenance(source_name="TRANSPORT_MODE_SPEC")
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode_id": self.mode_id,
            "display_name": self.display_name,
            "vehicle_type": self.vehicle_type,
            "capacity_kg": self.capacity_kg,
            "base_dispatch_fee": self.base_dispatch_fee,
            "cost_per_km": self.cost_per_km,
            "cost_per_km_tonne": self.cost_per_km_tonne,
            "speed_kmh": self.speed_kmh,
            "temperature_controlled": self.temperature_controlled,
            "provenance": self.provenance.to_dict(),
        }


@dataclass
class StorageFacility:
    """Storage warehouse, silo, or cold-chain holding unit."""
    facility_id: str
    name: str
    storage_type: StorageType
    location: str
    capacity_kg: float
    available_capacity_kg: float
    cost_per_kg_day: float
    latitude: float | None = None
    longitude: float | None = None
    min_duration_days: int = 1
    max_duration_days: int = 90
    temperature_celsius: float | None = None
    humidity_pct: float | None = None
    availability_start: date | None = None
    availability_end: date | None = None
    provenance: EconomicProvenance = field(
        default_factory=lambda: EconomicProvenance(source_name="STORAGE_FACILITY_SPEC")
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "facility_id": self.facility_id,
            "name": self.name,
            "storage_type": self.storage_type.value,
            "location": self.location,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "capacity_kg": self.capacity_kg,
            "available_capacity_kg": self.available_capacity_kg,
            "cost_per_kg_day": self.cost_per_kg_day,
            "min_duration_days": self.min_duration_days,
            "max_duration_days": self.max_duration_days,
            "temperature_celsius": self.temperature_celsius,
            "humidity_pct": self.humidity_pct,
            "availability_start": self.availability_start.isoformat() if self.availability_start else None,
            "availability_end": self.availability_end.isoformat() if self.availability_end else None,
            "provenance": self.provenance.to_dict(),
        }


@dataclass
class LogisticsCostItem:
    """Itemized logistics or handling fee line item."""
    component_name: str
    amount: float
    currency: str = "INR"
    unit_basis: CostUnitBasis = CostUnitBasis.INR_FIXED
    quantity_basis_kg: float | None = None
    distance_basis_km: float | None = None
    duration_days: float | None = None
    provenance: EconomicProvenance = field(
        default_factory=lambda: EconomicProvenance(source_name="LOGISTICS_COST_ITEM")
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "component_name": self.component_name,
            "amount": round(self.amount, 2),
            "currency": self.currency,
            "unit_basis": self.unit_basis.value,
            "quantity_basis_kg": self.quantity_basis_kg,
            "distance_basis_km": self.distance_basis_km,
            "duration_days": self.duration_days,
            "provenance": self.provenance.to_dict(),
        }


@dataclass
class LogisticsCostBreakdown:
    """Decomposed logistics costing with transparent economic provenance."""
    total_cost: float
    transport_cost: float
    loading_cost: float
    unloading_cost: float
    handling_cost: float
    other_cost: float
    items: list[LogisticsCostItem]
    economic_status: EconomicStatus
    provenance: EconomicProvenance

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_cost": round(self.total_cost, 2),
            "transport_cost": round(self.transport_cost, 2),
            "loading_cost": round(self.loading_cost, 2),
            "unloading_cost": round(self.unloading_cost, 2),
            "handling_cost": round(self.handling_cost, 2),
            "other_cost": round(self.other_cost, 2),
            "items": [it.to_dict() for it in self.items],
            "economic_status": self.economic_status.value,
            "provenance": self.provenance.to_dict(),
        }


@dataclass
class PerishabilityModelSpec:
    """Documented decay parameters for a specific crop and storage regime."""
    crop: str
    storage_type: StorageType
    decay_parameter_delta: float  # Quantity decay rate delta in S(t) = exp(-delta * t)
    quality_decay_beta: float     # Quality decay rate beta in F(t) = F0 * exp(-beta * t)
    unit: str = "PER_DAY"
    max_supported_days: int = 30
    equation: str = "S(t) = exp(-delta * t); Q_eff(t) = Q0 * S(t); F_qual(t) = F0 * exp(-beta * t)"
    assumptions: str = "Homogeneous temperature and ventilation; constant daily loss rate."
    calibration_status: str = "NOT_CALIBRATED"
    provenance: EconomicProvenance = field(
        default_factory=lambda: EconomicProvenance(
            source_name="CONFIGURED_CROP_PERISHABILITY_PARAMETER",
            status=ProvenanceStatus.DEMO,
            is_demo=True,
            justification="Configured/demo crop perishability parameters; not empirically calibrated laboratory constants.",
        )
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "crop": self.crop,
            "storage_type": self.storage_type.value,
            "decay_parameter_delta": self.decay_parameter_delta,
            "quality_decay_beta": self.quality_decay_beta,
            "unit": self.unit,
            "max_supported_days": self.max_supported_days,
            "equation": self.equation,
            "assumptions": self.assumptions,
            "calibration_status": self.calibration_status,
            "provenance": self.provenance.to_dict(),
        }


@dataclass
class PerishabilityPoint:
    """Discrete daily state of produce along a physical timeline."""
    day: int
    elapsed_hours: float
    quantity_kg: float
    quantity_loss_kg: float
    survival_factor: float
    quality_factor: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "day": self.day,
            "elapsed_hours": round(self.elapsed_hours, 1),
            "quantity_kg": round(self.quantity_kg, 2),
            "quantity_loss_kg": round(self.quantity_loss_kg, 2),
            "survival_factor": round(self.survival_factor, 4),
            "quality_factor": round(self.quality_factor, 4),
        }


@dataclass
class PerishabilityTrajectory:
    """Trajectory of physical deterioration over modeled duration."""
    commodity_id: str
    storage_type: StorageType
    initial_quantity_kg: float
    final_quantity_kg: float
    final_quality_factor: float
    duration_days: int
    trajectory: list[PerishabilityPoint]
    model_spec: PerishabilityModelSpec | None
    status: str  # "CALCULATED" or "LOSS_MODEL_UNAVAILABLE"
    provenance: EconomicProvenance

    def to_dict(self) -> dict[str, Any]:
        return {
            "commodity_id": self.commodity_id,
            "storage_type": self.storage_type.value,
            "initial_quantity_kg": round(self.initial_quantity_kg, 2),
            "final_quantity_kg": round(self.final_quantity_kg, 2),
            "final_quality_factor": round(self.final_quality_factor, 4),
            "duration_days": self.duration_days,
            "trajectory": [p.to_dict() for p in self.trajectory],
            "model_spec": self.model_spec.to_dict() if self.model_spec else None,
            "status": self.status,
            "provenance": self.provenance.to_dict(),
        }


@dataclass
class HandlingStage:
    """Intermediate physical handling or processing stage."""
    stage_id: str
    stage_type: HandlingStageType
    duration_hours: float
    cost: float
    quantity_loss_pct: float = 0.0
    quality_impact_pct: float = 0.0
    provenance: EconomicProvenance = field(
        default_factory=lambda: EconomicProvenance(source_name="HANDLING_STAGE_SPEC")
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage_id": self.stage_id,
            "stage_type": self.stage_type.value,
            "duration_hours": self.duration_hours,
            "cost": round(self.cost, 2),
            "quantity_loss_pct": self.quantity_loss_pct,
            "quality_impact_pct": self.quality_impact_pct,
            "provenance": self.provenance.to_dict(),
        }


@dataclass
class StorageFeasibilityResult:
    """Capacity and duration constraint check for a storage facility."""
    facility_id: str
    facility_name: str
    storage_type: StorageType
    requested_quantity_kg: float
    available_capacity_kg: float
    stored_quantity_kg: float
    unstored_quantity_kg: float
    requested_duration_days: int
    min_supported_days: int
    max_supported_days: int
    storage_cost: float
    status: FeasibilityStatus
    warnings: list[str]
    provenance: EconomicProvenance

    def to_dict(self) -> dict[str, Any]:
        return {
            "facility_id": self.facility_id,
            "facility_name": self.facility_name,
            "storage_type": self.storage_type.value,
            "requested_quantity_kg": round(self.requested_quantity_kg, 2),
            "available_capacity_kg": round(self.available_capacity_kg, 2),
            "stored_quantity_kg": round(self.stored_quantity_kg, 2),
            "unstored_quantity_kg": round(self.unstored_quantity_kg, 2),
            "requested_duration_days": self.requested_duration_days,
            "min_supported_days": self.min_supported_days,
            "max_supported_days": self.max_supported_days,
            "storage_cost": round(self.storage_cost, 2),
            "status": self.status.value,
            "warnings": self.warnings,
            "provenance": self.provenance.to_dict(),
        }


@dataclass
class LogisticsFeasibilityResult:
    """Comprehensive factual constraint satisfaction check."""
    feasible: bool
    status: FeasibilityStatus
    transportable_quantity_kg: float
    untransportable_quantity_kg: float
    distance_km: float | None
    distance_type: DistanceType
    transit_duration_hours: float | None
    transit_time_status: TransitTimeStatus
    failed_constraints: list[str]
    warnings: list[str]
    assumptions: list[str]
    provenance: EconomicProvenance

    def to_dict(self) -> dict[str, Any]:
        return {
            "feasible": self.feasible,
            "status": self.status.value,
            "transportable_quantity_kg": round(self.transportable_quantity_kg, 2),
            "untransportable_quantity_kg": round(self.untransportable_quantity_kg, 2),
            "distance_km": round(self.distance_km, 1) if self.distance_km is not None else None,
            "distance_type": self.distance_type.value,
            "transit_duration_hours": round(self.transit_duration_hours, 1) if self.transit_duration_hours is not None else None,
            "transit_time_status": self.transit_time_status.value,
            "failed_constraints": self.failed_constraints,
            "warnings": self.warnings,
            "assumptions": self.assumptions,
            "provenance": self.provenance.to_dict(),
        }


@dataclass
class LogisticsScenario:
    """Modeled multi-stage pathway from farmer origin to destination."""
    scenario_id: str
    scenario_name: str
    destination: Destination
    stages: list[HandlingStage]
    storage_facility: StorageFacility | None
    transport_mode: TransportModeSpec
    distance_km: float | None
    distance_type: DistanceType
    transit_duration_hours: float | None
    transit_time_status: TransitTimeStatus
    storage_duration_days: int
    total_elapsed_hours: float
    initial_quantity_kg: float
    transportable_quantity_kg: float
    effective_delivered_quantity_kg: float
    final_quality_factor: float
    logistics_cost: LogisticsCostBreakdown
    storage_cost: float
    total_pathway_cost: float
    feasibility: LogisticsFeasibilityResult
    storage_feasibility: StorageFeasibilityResult | None
    perishability: PerishabilityTrajectory | None
    economic_status: EconomicStatus
    provenance: EconomicProvenance

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "scenario_name": self.scenario_name,
            "destination": self.destination.to_dict(),
            "stages": [s.to_dict() for s in self.stages],
            "storage_facility": self.storage_facility.to_dict() if self.storage_facility else None,
            "transport_mode": self.transport_mode.to_dict(),
            "distance_km": round(self.distance_km, 1) if self.distance_km is not None else None,
            "distance_type": self.distance_type.value,
            "transit_duration_hours": round(self.transit_duration_hours, 1) if self.transit_duration_hours is not None else None,
            "transit_time_status": self.transit_time_status.value,
            "storage_duration_days": self.storage_duration_days,
            "total_elapsed_hours": round(self.total_elapsed_hours, 1),
            "initial_quantity_kg": round(self.initial_quantity_kg, 2),
            "transportable_quantity_kg": round(self.transportable_quantity_kg, 2),
            "effective_delivered_quantity_kg": round(self.effective_delivered_quantity_kg, 2),
            "final_quality_factor": round(self.final_quality_factor, 4),
            "logistics_cost": self.logistics_cost.to_dict(),
            "storage_cost": round(self.storage_cost, 2),
            "total_pathway_cost": round(self.total_pathway_cost, 2),
            "feasibility": self.feasibility.to_dict(),
            "storage_feasibility": self.storage_feasibility.to_dict() if self.storage_feasibility else None,
            "perishability": self.perishability.to_dict() if self.perishability else None,
            "economic_status": self.economic_status.value,
            "provenance": self.provenance.to_dict(),
        }
