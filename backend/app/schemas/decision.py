"""
AgriClutch Step 14: Decision Intelligence & Optimal Selling Plan Pydantic Schemas.
Pydantic v2 validation contracts for selling plan optimization, What-If counterfactuals,
and sensitivity sweep requests/responses.
SIH26132 — Strengthening Market Linkages and Price Discovery for Farmers.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from ml.decision.optimizer.contracts import (
    DestinationType,
    LiquidityPreference,
    RiskPreference,
    SolverStatus,
    ValidationStatus,
)


class OptimizePlanRequest(BaseModel):
    """Request payload for running the multi-channel optimal selling solver."""
    model_config = ConfigDict(extra="forbid")

    commodity_id: str = Field(..., description="Crop identifier, e.g. tomato, onion, potato")
    variety: str = Field(default="Standard", description="Crop variety classification")
    quality_grade: str = Field(default="GRADE_A", description="Physical quality assay grade")
    total_supply_kg: float = Field(..., gt=0.0, description="Farmer available produce quantity in kilograms")
    decision_horizon_days: int = Field(default=7, ge=1, le=30, description="Decision planning window in days")
    risk_preference: RiskPreference = Field(default=RiskPreference.RISK_AWARE, description="Farmer downside risk profile")
    liquidity_preference: LiquidityPreference = Field(default=LiquidityPreference.BALANCED, description="Immediate cash requirement profile")
    origin_latitude: Optional[float] = Field(default=30.8350, description="Farmgate GPS latitude")
    origin_longitude: Optional[float] = Field(default=76.9350, description="Farmgate GPS longitude")


class PlanAllocationResponse(BaseModel):
    """Detailed response for an individual allocation block."""
    allocation_id: str
    candidate_id: str
    destination_type: DestinationType
    destination_id: str
    destination_name: str
    sale_day_offset: int
    sale_date: str
    allocated_quantity_kg: float
    effective_quantity_kg: float
    allocation_percentage: float
    expected_price_per_kg: float
    expected_nrv_per_kg: float
    gross_revenue: float
    total_freight_cost: float
    total_storage_cost: float
    total_handling_cost: float
    total_market_fee: float
    expected_total_nrv: float
    nrv_p10_total: float
    nrv_p50_total: float
    nrv_p90_total: float
    quality_factor: float
    mass_retention_factor: float
    limiting_constraints: List[str]
    explanation: str


class RiskMetricsResponse(BaseModel):
    """Portfolio risk metrics and downside dispersion summary."""
    risk_preference: RiskPreference
    risk_penalty_weight: float
    # Honest statistical dispersion fields
    portfolio_downside_spread: float = Field(description="max(0, P50_total - P10_total) lower quantile spread")
    configured_tail_stress_estimate: float = Field(description="Configured parametric tail stress approximation (1.25x spread)")
    expected_total_nrv: float
    risk_adjusted_nrv: float
    downside_spread_penalty: float = Field(description="Linear penalty applied during optimization")
    confidence_level: float = 0.90
    p10_total_nrv: float
    p50_total_nrv: float
    p90_total_nrv: float
    tail_stress_multiplier: float = 1.25
    tail_stress_provenance: str = "CONFIGURED"
    provenance_status: str
    is_demo: bool = True
    # Backward compatibility aliases
    var_95: float = 0.0
    cvar_95: float = 0.0
    downside_cvar_penalty: float = 0.0
    tail_risk_multiplier: float = 1.25
    tail_risk_provenance: str = "CONFIGURED"


class ConstraintItemResponse(BaseModel):
    """Audit entry for an individual constraint."""
    constraint_name: str
    status: str
    lhs_value: float
    rhs_bound: float
    unit: str
    slack: float
    description: str


class ConstraintSummaryResponse(BaseModel):
    """Complete constraint audit report."""
    supply_constraint_status: str
    liquidity_constraint_status: str
    demand_constraint_status: str
    transport_constraint_status: str
    storage_constraint_status: str
    perishability_constraint_status: str
    items: List[ConstraintItemResponse]
    violated_constraints: List[str]


class OptimalSellingPlanResponse(BaseModel):
    """Authoritative API response contract for Optimal Selling Plans."""
    plan_id: str
    created_at: str
    commodity_id: str
    variety: str
    quality_grade: str
    total_supply_kg: float
    decision_horizon_days: int
    risk_preference: RiskPreference
    liquidity_preference: LiquidityPreference
    allocations: List[PlanAllocationResponse]
    total_allocated_kg: float
    total_unallocated_kg: float
    total_effective_kg: float
    expected_gross_revenue: float
    total_friction_cost: float
    expected_total_nrv: float
    risk_adjusted_nrv: float
    risk_metrics: Optional[RiskMetricsResponse] = None
    constraint_summary: Optional[ConstraintSummaryResponse] = None
    solver_status: SolverStatus
    validation_status: ValidationStatus
    solver_message: str
    solver_duration_ms: float
    solver_version: str
    configuration_hash: str
    executive_summary: str
    structured_explanations: List[str]
    is_demo: bool = True
    provenance: Dict[str, Any]


class WhatIfSimulationRequest(BaseModel):
    """Request for running counterfactual comparison against baseline plan."""
    model_config = ConfigDict(extra="forbid")

    commodity_id: str = Field(default="tomato")
    total_supply_kg: float = Field(default=2500.0, gt=0.0)
    decision_horizon_days: int = Field(default=7, ge=1, le=30)
    baseline_risk: RiskPreference = Field(default=RiskPreference.RISK_AWARE)
    baseline_liquidity: LiquidityPreference = Field(default=LiquidityPreference.BALANCED)

    # Counterfactual overrides
    cf_supply_kg: Optional[float] = Field(default=None, gt=0.0)
    cf_risk: Optional[RiskPreference] = Field(default=None)
    cf_liquidity: Optional[LiquidityPreference] = Field(default=None)
    transport_cost_multiplier: float = Field(default=1.0, ge=0.1, le=5.0)
    storage_cost_multiplier: float = Field(default=1.0, ge=0.1, le=5.0)
    buyer_demand_multiplier: float = Field(default=1.0, ge=0.0, le=5.0)
    price_shock_multiplier: float = Field(default=1.0, ge=0.1, le=3.0)
    additional_storage_days: int = Field(default=0, ge=-5, le=14)
    scenario_label: str = Field(default="Counterfactual What-If Scenario")


class CounterfactualDeltaResponse(BaseModel):
    """Differential delta comparing baseline to counterfactual."""
    parameter_changed: str
    baseline_value: str
    counterfactual_value: str
    baseline_nrv: float
    counterfactual_nrv: float
    nrv_delta: float
    nrv_percentage_change: float
    baseline_allocated_kg: float
    counterfactual_allocated_kg: float
    allocation_shift_summary: str
    baseline_input_hash: str = ""
    counterfactual_input_hash: str = ""
    baseline_solver_status: SolverStatus = SolverStatus.OPTIMAL
    new_solver_status: SolverStatus = SolverStatus.OPTIMAL
    feasibility_changed: bool = False
    cvar_delta: float = 0.0
    allocation_delta_kg: float = 0.0


class WhatIfSimulationResponse(BaseModel):
    """API response for counterfactual What-If simulation."""
    simulation_id: str
    baseline_plan: OptimalSellingPlanResponse
    counterfactual_plan: OptimalSellingPlanResponse
    comparison: CounterfactualDeltaResponse
    is_demo: bool = True


class SensitivityRequest(BaseModel):
    """Request payload for running a multi-point parameter sensitivity sweep."""
    model_config = ConfigDict(extra="forbid")

    commodity_id: str = Field(default="tomato")
    total_supply_kg: float = Field(default=2500.0, gt=0.0)
    parameter_type: str = Field(default="TRANSPORT_COST", description="TRANSPORT_COST / BUYER_DEMAND / PRICE_SHOCK")
    sweep_multipliers: Optional[List[float]] = Field(default=None)
    risk_preference: RiskPreference = Field(default=RiskPreference.RISK_AWARE)
    liquidity_preference: LiquidityPreference = Field(default=LiquidityPreference.BALANCED)


class SensitivityPointResponse(BaseModel):
    """Single point in a sensitivity curve."""
    step_index: int
    parameter_value: float
    parameter_label: str
    expected_total_nrv: float
    risk_adjusted_nrv: float
    allocated_percentage: float
    is_feasible: bool
    solver_status: SolverStatus


class SensitivitySweepResponse(BaseModel):
    """Full sensitivity sweep curve response."""
    parameter_name: str
    baseline_value: float
    unit: str
    points: List[SensitivityPointResponse]
    interpretation: str
