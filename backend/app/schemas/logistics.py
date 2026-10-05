"""
Pydantic v2 Schemas for AgriClutch Logistics, Storage & Perishability Feasibility Engine.
Strictly typed data contracts for physical transit, storage allocations, decay trajectories,
and auditable multi-stage pathways.
Strictly NO recommendation, ranking, or scoring fields.
SIH26132 — Strengthening Market Linkages and Price Discovery for Farmers.
"""

from datetime import date
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class EconomicProvenanceSchema(BaseModel):
    """Verifiable data source metadata."""
    model_config = ConfigDict(from_attributes=True)

    source_name: str
    source_record_id: Optional[str] = None
    source_reference: Optional[str] = None
    observed_at: Optional[str] = None
    effective_from: Optional[str] = None
    effective_to: Optional[str] = None
    validity_range: Optional[str] = None
    status: str = "DEMO"
    is_demo: bool = True
    justification: Optional[str] = None


class TransportModeResponse(BaseModel):
    """Transport vehicle equipment specification."""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: Optional[str] = None
    mode_id: Optional[str] = None
    display_name: str
    vehicle_type: str
    capacity_kg: float
    base_dispatch_fee: float
    cost_per_km: Optional[float] = None
    cost_per_km_tonne: Optional[float] = None
    speed_kmh: Optional[float] = None
    temperature_controlled: bool = False
    active_status: bool = True
    source_name: str = "DEMO_VEHICLE_ARCHETYPE_SCHEDULE"
    provenance_status: str = "DEMO"
    is_demo: bool = True

    @model_validator(mode="before")
    @classmethod
    def reconcile_identifiers(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "mode_id" in data and "id" not in data:
                data["id"] = data["mode_id"]
            elif "id" in data and "mode_id" not in data:
                data["mode_id"] = data["id"]
        return data


class StorageFacilityResponse(BaseModel):
    """Storage warehouse or cold storage facility."""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: Optional[str] = None
    facility_id: Optional[str] = None
    facility_name: Optional[str] = None
    name: Optional[str] = None
    storage_type: str
    location: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    total_capacity_kg: Optional[float] = None
    capacity_kg: Optional[float] = None
    available_capacity_kg: float
    cost_per_kg_day: float
    min_duration_days: int = 1
    max_duration_days: int = 90
    temperature_celsius: Optional[float] = None
    humidity_pct: Optional[float] = None
    active_status: bool = True
    source_name: str = "DEMO_FACILITY_BENCHMARK_SCHEDULE"
    provenance_status: str = "DEMO"
    is_demo: bool = True

    @model_validator(mode="before")
    @classmethod
    def reconcile_identifiers(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "facility_id" in data and "id" not in data:
                data["id"] = data["facility_id"]
            elif "id" in data and "facility_id" not in data:
                data["facility_id"] = data["id"]
            if "name" in data and "facility_name" not in data:
                data["facility_name"] = data["name"]
            elif "facility_name" in data and "name" not in data:
                data["name"] = data["facility_name"]
            if "capacity_kg" in data and "total_capacity_kg" not in data:
                data["total_capacity_kg"] = data["capacity_kg"]
            elif "total_capacity_kg" in data and "capacity_kg" not in data:
                data["capacity_kg"] = data["total_capacity_kg"]
        return data


class StorageAvailabilityResponse(BaseModel):
    """Storage capacity query response."""
    facility_id: str
    facility_name: str
    storage_type: str
    available_capacity_kg: float
    total_capacity_kg: float
    cost_per_kg_day: float
    is_available: bool
    provenance: EconomicProvenanceSchema


class DistanceCalculationRequest(BaseModel):
    """Request to compute geodesic distance and transit duration."""
    origin_lat: Optional[float] = Field(None, ge=-90.0, le=90.0)
    origin_lon: Optional[float] = Field(None, ge=-180.0, le=180.0)
    dest_lat: Optional[float] = Field(None, ge=-90.0, le=90.0)
    dest_lon: Optional[float] = Field(None, ge=-180.0, le=180.0)
    road_distance_km: Optional[float] = Field(None, ge=0.0)
    transport_mode_id: Optional[str] = None
    speed_kmh: Optional[float] = Field(None, gt=0.0)


class DistanceCalculationResponse(BaseModel):
    """Response containing distance and duration metrics."""
    distance_km: Optional[float]
    distance_type: str  # STRAIGHT_LINE_DISTANCE, ESTIMATED_ROUTE_DISTANCE, ROAD_DISTANCE, UNKNOWN_DISTANCE
    straight_line_distance_km: Optional[float] = None
    circuity_factor: Optional[float] = None
    estimated_route_distance_km: Optional[float] = None
    transit_duration_hours: Optional[float]
    transit_time_status: str  # OBSERVED, CONFIGURED, TRANSIT_TIME_UNAVAILABLE
    provenance: EconomicProvenanceSchema


class LogisticsCostItemSchema(BaseModel):
    """Itemized friction cost line item."""
    component_name: str
    amount: float
    currency: str = "INR"
    unit_basis: str
    quantity_basis_kg: Optional[float] = None
    distance_basis_km: Optional[float] = None
    duration_days: Optional[float] = None
    provenance: EconomicProvenanceSchema


class LogisticsCostBreakdownResponse(BaseModel):
    """Decomposed logistics costing with transparent economic provenance."""
    total_cost: float
    transport_cost: float
    loading_cost: float
    unloading_cost: float
    handling_cost: float
    other_cost: float
    items: List[LogisticsCostItemSchema]
    economic_status: str  # COMPLETE_EMPIRICAL, COMPLETE_MIXED_PROVENANCE, DEMO_ASSUMPTION, INCOMPLETE, UNAVAILABLE
    provenance: EconomicProvenanceSchema


class PerishabilityPointSchema(BaseModel):
    """Daily produce loss point."""
    day: int
    elapsed_hours: float
    quantity_kg: float
    quantity_loss_kg: float
    survival_factor: float
    quality_factor: float


class PerishabilityModelSpecResponse(BaseModel):
    """Documented decay parameters."""
    crop: str
    storage_type: str
    decay_parameter_delta: float
    quality_decay_beta: float
    unit: str = "PER_DAY"
    max_supported_days: int = 30
    equation: str
    assumptions: str
    calibration_status: str = "NOT_CALIBRATED"
    provenance: EconomicProvenanceSchema


class PerishabilityTrajectoryResponse(BaseModel):
    """Decayed state timeline."""
    commodity_id: str
    storage_type: str
    initial_quantity_kg: float
    final_quantity_kg: float
    final_quality_factor: float
    duration_days: int
    trajectory: List[PerishabilityPointSchema]
    model_spec: Optional[PerishabilityModelSpecResponse] = None
    status: str
    provenance: EconomicProvenanceSchema


class HandlingStageSchema(BaseModel):
    """Physical handling operation."""
    stage_id: str
    stage_type: str
    duration_hours: float
    cost: float
    quantity_loss_pct: float = 0.0
    quality_impact_pct: float = 0.0
    provenance: EconomicProvenanceSchema


class StorageFeasibilityResponse(BaseModel):
    """Storage capacity check."""
    facility_id: str
    facility_name: str
    storage_type: str
    requested_quantity_kg: float
    available_capacity_kg: float
    stored_quantity_kg: float
    unstored_quantity_kg: float
    requested_duration_days: int
    min_supported_days: int
    max_supported_days: int
    storage_cost: float
    status: str  # FEASIBLE, PARTIALLY_FEASIBLE, INFEASIBLE, UNAVAILABLE
    warnings: List[str]
    provenance: EconomicProvenanceSchema


class LogisticsFeasibilityResponse(BaseModel):
    """Factual feasibility check."""
    feasible: bool
    status: str  # FEASIBLE, PARTIALLY_FEASIBLE, INFEASIBLE, INSUFFICIENT_DATA, UNAVAILABLE
    transportable_quantity_kg: float
    untransportable_quantity_kg: float
    distance_km: Optional[float] = None
    distance_type: str
    transit_duration_hours: Optional[float] = None
    transit_time_status: str
    failed_constraints: List[str]
    warnings: List[str]
    assumptions: List[str]
    provenance: EconomicProvenanceSchema


class LogisticsScenarioResponse(BaseModel):
    """Modeled multi-stage pathway."""
    scenario_id: str
    scenario_name: str
    destination: Dict[str, Any]
    stages: List[HandlingStageSchema]
    storage_facility: Optional[StorageFacilityResponse] = None
    transport_mode: TransportModeResponse
    distance_km: Optional[float] = None
    distance_type: str
    transit_duration_hours: Optional[float] = None
    transit_time_status: str
    storage_duration_days: int
    total_elapsed_hours: float
    initial_quantity_kg: float
    transportable_quantity_kg: float
    effective_delivered_quantity_kg: float
    final_quality_factor: float
    logistics_cost: LogisticsCostBreakdownResponse
    storage_cost: float
    total_pathway_cost: float
    feasibility: LogisticsFeasibilityResponse
    storage_feasibility: Optional[StorageFeasibilityResponse] = None
    perishability: Optional[PerishabilityTrajectoryResponse] = None
    economic_status: str
    provenance: EconomicProvenanceSchema


class EvaluatePathwaysRequest(BaseModel):
    """Request to evaluate physical pathways for a produce lot."""
    commodity_id: str
    quantity_kg: float = Field(..., gt=0)
    quality_grade: str = "GRADE_A"
    origin_location: str
    origin_latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    origin_longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    available_from: date
    available_until: date
    transport_mode_id: Optional[str] = None
    storage_facility_id: Optional[str] = None
    storage_duration_days: int = Field(0, ge=0)
    destination_ids: Optional[List[str]] = None


class EvaluatePathwaysResponse(BaseModel):
    """Collection of evaluated physical pathways."""
    lot_summary: Dict[str, Any]
    scenarios: List[LogisticsScenarioResponse]
    economic_status: str
    provenance: EconomicProvenanceSchema
