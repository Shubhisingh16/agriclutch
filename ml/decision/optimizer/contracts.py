"""
AgriClutch Step 14: Decision Intelligence, Optimization & Selling Plan Contracts.
Strict, auditable mathematical contracts for multi-destination split optimization,
downside risk adjustments (CVaR), liquidity constraints, and explainable selling plans.
SIH26132 — Strengthening Market Linkages and Price Discovery for Farmers.
"""

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class SolverStatus(str, Enum):
    """Execution status of the mathematical optimizer."""
    OPTIMAL = "OPTIMAL"
    FEASIBLE = "FEASIBLE"
    INFEASIBLE = "INFEASIBLE"
    NO_FEASIBLE_PLAN = "NO_FEASIBLE_PLAN"
    UNAVAILABLE = "UNAVAILABLE"
    TIME_LIMIT = "TIME_LIMIT"
    ERROR = "ERROR"


class RiskPreference(str, Enum):
    """
    Farmer risk profile defining the objective risk penalty:
    - RISK_NEUTRAL: Maximize Expected NRV (alpha=0.0).
    - RISK_AWARE: Balanced objective with moderate downside CVaR penalty (alpha=0.5, confidence=0.90).
    - RISK_AVERSE: Heavy downside preservation penalizing lower quantile shortfall (alpha=1.0, confidence=0.95).
    """
    RISK_NEUTRAL = "RISK_NEUTRAL"
    RISK_AWARE = "RISK_AWARE"
    RISK_AVERSE = "RISK_AVERSE"


class LiquidityPreference(str, Enum):
    """
    Farmer cash requirement window:
    - IMMEDIATE: Minimum 60% of total quantity must be liquidated within Day 0-1.
    - BALANCED: Minimum 30% liquidated immediately, up to 70% delayed or stored.
    - DELAY_TOLERANT: Up to 100% may be stored/delayed subject to perishability and storage bounds.
    """
    IMMEDIATE = "IMMEDIATE"
    BALANCED = "BALANCED"
    DELAY_TOLERANT = "DELAY_TOLERANT"


class DestinationType(str, Enum):
    """Target destination of produce allocation."""
    BUYER = "BUYER"
    MARKET = "MARKET"
    STORAGE_HOLD = "STORAGE_HOLD"


class DecisionProvenanceStatus(str, Enum):
    """Provenance tracking for data points feeding the optimizer."""
    EMPIRICAL = "EMPIRICAL"
    OFFICIAL = "OFFICIAL"
    RESEARCH = "RESEARCH"
    CONFIGURED = "CONFIGURED"
    DEMO = "DEMO"
    UNAVAILABLE = "UNAVAILABLE"


class ValidationStatus(str, Enum):
    """Post-solve plan audit status."""
    PASSED = "PASSED"
    FAILED = "FAILED"


@dataclass
class DecisionProvenance:
    """Provenance audit metadata for an optimization output or input."""
    source_name: str
    provenance_status: DecisionProvenanceStatus = DecisionProvenanceStatus.DEMO
    is_demo: bool = True
    recorded_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_name": self.source_name,
            "provenance_status": self.provenance_status.value,
            "is_demo": self.is_demo,
            "recorded_at": self.recorded_at,
            "notes": self.notes,
        }


@dataclass
class AllocationCandidate:
    """
    Candidate allocation option feeding the mathematical solver.
    Pre-filtered for commodity, grade, physical feasibility, and temporal overlap.
    """
    candidate_id: str
    destination_type: DestinationType
    destination_id: str
    destination_name: str
    sale_day_offset: int  # days from harvest/availability date
    sale_date: str

    # Economics & Forecast
    expected_price_per_kg: float
    price_p10: float
    price_p50: float
    price_p90: float
    expected_nrv_per_kg: float
    nrv_p10: float
    nrv_p50: float
    nrv_p90: float

    # Friction deductions (per kg)
    freight_cost_per_kg: float
    handling_cost_per_kg: float
    storage_cost_per_kg: float
    market_fee_per_kg: float

    # Physical decay & handling factors
    mass_retention_factor: float  # S(t) <= 1.0
    quality_factor: float         # F(t) <= 1.0

    # Capacity & Constraints
    max_demand_kg: float          # Buyer demand or market throughput bound
    max_transport_kg: float       # Fleet vehicle limit
    max_storage_kg: float         # Warehouse limit (if storage involved)
    is_immediate_window: bool     # True if sale_day_offset <= 1

    # Provenance references
    pathway_id: Optional[str] = None
    buyer_id: Optional[str] = None
    market_id: Optional[str] = None
    storage_facility_id: Optional[str] = None
    forecast_model: str = "Chronos-2"
    provenance_status: DecisionProvenanceStatus = DecisionProvenanceStatus.DEMO
    is_demo: bool = True


@dataclass
class PlanAllocation:
    """Individual assigned allocation segment in the optimal selling plan."""
    allocation_id: str = field(default_factory=lambda: f"alloc_{uuid.uuid4().hex[:8]}")
    candidate_id: str = ""
    destination_type: DestinationType = DestinationType.BUYER
    destination_id: str = ""
    destination_name: str = ""
    sale_day_offset: int = 0
    sale_date: str = ""

    # Quantities
    allocated_quantity_kg: float = 0.0
    effective_quantity_kg: float = 0.0  # allocated * mass_retention_factor
    allocation_percentage: float = 0.0

    # Economics
    expected_price_per_kg: float = 0.0
    expected_nrv_per_kg: float = 0.0
    gross_revenue: float = 0.0
    total_freight_cost: float = 0.0
    total_storage_cost: float = 0.0
    total_handling_cost: float = 0.0
    total_market_fee: float = 0.0
    expected_total_nrv: float = 0.0

    # Uncertainty & Risk
    nrv_p10_total: float = 0.0
    nrv_p50_total: float = 0.0
    nrv_p90_total: float = 0.0
    downside_cvar_penalty: float = 0.0

    # Physical & Quality
    quality_factor: float = 1.0
    mass_retention_factor: float = 1.0

    # Metadata & Tracking
    pathway_id: Optional[str] = None
    buyer_id: Optional[str] = None
    market_id: Optional[str] = None
    storage_facility_id: Optional[str] = None
    limiting_constraints: List[str] = field(default_factory=list)
    explanation: str = ""
    provenance: Optional[DecisionProvenance] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["destination_type"] = self.destination_type.value
        if self.provenance:
            d["provenance"] = self.provenance.to_dict()
        return d


@dataclass
class RiskMetrics:
    """
    Downside dispersion and tail stress summary for the aggregated plan (post-solve evaluation).

    MATHEMATICAL AUDIT SPECIFICATION:
    - portfolio_downside_spread = max(0, Σ x_i* NRV_p50,i - Σ x_i* NRV_p10,i).
      This is the lower-quantile spread / downside dispersion between median and 10th percentile.
      It is NOT standard Value at Risk at 95% (VaR95).
    - configured_tail_stress_estimate = portfolio_downside_spread * tail_stress_multiplier.
      This is a configured parametric stress approximation (default 1.25x), NOT standard CVaR95 / Expected Shortfall.
    """
    risk_preference: RiskPreference
    risk_penalty_weight: float
    portfolio_downside_spread: float  # max(0, P50_total - P10_total)
    configured_tail_stress_estimate: float  # portfolio_downside_spread * tail_stress_multiplier
    expected_total_nrv: float
    risk_adjusted_nrv: float  # Expected NRV - Optimization Downside Penalty
    downside_spread_penalty: float  # Total optimization penalty applied
    confidence_level: float = 0.90  # Reflects the 10th percentile lower quantile used
    p10_total_nrv: float = 0.0
    p50_total_nrv: float = 0.0
    p90_total_nrv: float = 0.0
    tail_stress_multiplier: float = 1.25  # Configured tail stress multiplier (NOT intrinsic CVaR)
    tail_stress_provenance: DecisionProvenanceStatus = DecisionProvenanceStatus.CONFIGURED
    provenance_status: DecisionProvenanceStatus = DecisionProvenanceStatus.CONFIGURED
    is_demo: bool = True

    # Compatibility properties for legacy callers
    @property
    def var_95(self) -> float:
        return self.portfolio_downside_spread

    @property
    def cvar_95(self) -> float:
        return self.configured_tail_stress_estimate

    @property
    def downside_cvar_penalty(self) -> float:
        return self.downside_spread_penalty

    @property
    def tail_risk_multiplier(self) -> float:
        return self.tail_stress_multiplier

    @property
    def tail_risk_provenance(self) -> DecisionProvenanceStatus:
        return self.tail_stress_provenance

    def to_dict(self) -> Dict[str, Any]:
        return {
            "risk_preference": self.risk_preference.value,
            "risk_penalty_weight": self.risk_penalty_weight,
            "portfolio_downside_spread": round(self.portfolio_downside_spread, 2),
            "configured_tail_stress_estimate": round(self.configured_tail_stress_estimate, 2),
            "expected_total_nrv": round(self.expected_total_nrv, 2),
            "risk_adjusted_nrv": round(self.risk_adjusted_nrv, 2),
            "downside_spread_penalty": round(self.downside_spread_penalty, 2),
            "confidence_level": self.confidence_level,
            "p10_total_nrv": round(self.p10_total_nrv, 2),
            "p50_total_nrv": round(self.p50_total_nrv, 2),
            "p90_total_nrv": round(self.p90_total_nrv, 2),
            "tail_stress_multiplier": self.tail_stress_multiplier,
            "tail_stress_provenance": self.tail_stress_provenance.value,
            "provenance_status": self.provenance_status.value,
            "is_demo": self.is_demo,
            # Backward compatibility fields
            "var_95": round(self.var_95, 2),
            "cvar_95": round(self.cvar_95, 2),
            "downside_cvar_penalty": round(self.downside_cvar_penalty, 2),
            "tail_risk_multiplier": self.tail_risk_multiplier,
            "tail_risk_provenance": self.tail_risk_provenance.value,
        }


@dataclass
class ConstraintAuditItem:
    """Itemized constraint check report."""
    constraint_name: str
    status: str  # "SATISFIED", "BINDING", "VIOLATED", "NOT_CONFIGURED"
    lhs_value: float
    rhs_bound: float
    unit: str
    slack: float
    description: str


@dataclass
class ConstraintSummary:
    """Overall constraint satisfaction audit."""
    supply_constraint_status: str = "SATISFIED"
    liquidity_constraint_status: str = "SATISFIED"
    demand_constraint_status: str = "SATISFIED"
    transport_constraint_status: str = "SATISFIED"
    storage_constraint_status: str = "SATISFIED"
    perishability_constraint_status: str = "SATISFIED"
    items: List[ConstraintAuditItem] = field(default_factory=list)
    violated_constraints: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "supply_constraint_status": self.supply_constraint_status,
            "liquidity_constraint_status": self.liquidity_constraint_status,
            "demand_constraint_status": self.demand_constraint_status,
            "transport_constraint_status": self.transport_constraint_status,
            "storage_constraint_status": self.storage_constraint_status,
            "perishability_constraint_status": self.perishability_constraint_status,
            "items": [asdict(i) for i in self.items],
            "violated_constraints": self.violated_constraints,
        }


@dataclass
class OptimalSellingPlan:
    """
    Authoritative Step 14 Optimal Selling Plan object.
    Complete mathematically validated decision output.
    """
    plan_id: str = field(default_factory=lambda: f"plan_{uuid.uuid4().hex[:12]}")
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    input_snapshot_id: str = ""

    # Farmer Produce Spec
    commodity_id: str = ""
    variety: str = "Standard"
    quality_grade: str = "GRADE_A"
    total_supply_kg: float = 0.0

    # Decision Preferences
    decision_horizon_days: int = 7
    risk_preference: RiskPreference = RiskPreference.RISK_AWARE
    liquidity_preference: LiquidityPreference = LiquidityPreference.BALANCED

    # Optimization Allocations
    allocations: List[PlanAllocation] = field(default_factory=list)
    total_allocated_kg: float = 0.0
    total_unallocated_kg: float = 0.0
    total_effective_kg: float = 0.0

    # Financial Aggregates
    expected_gross_revenue: float = 0.0
    total_friction_cost: float = 0.0
    expected_total_nrv: float = 0.0
    risk_adjusted_nrv: float = 0.0

    # Risk & Constraints
    risk_metrics: Optional[RiskMetrics] = None
    constraint_summary: Optional[ConstraintSummary] = None

    # Solver Run Metadata
    solver_status: SolverStatus = SolverStatus.OPTIMAL
    validation_status: ValidationStatus = ValidationStatus.PASSED
    solver_message: str = "Deterministic SciPy LP solver identified global optimal split."
    solver_duration_ms: float = 0.0
    solver_version: str = "AgriClutch-LinearOptimizer-1.0"
    input_hash: str = ""
    configuration_hash: str = ""

    # Interpretive Explanations
    executive_summary: str = ""
    structured_explanations: List[str] = field(default_factory=list)

    # Provenance & Audit
    provenance: DecisionProvenance = field(default_factory=lambda: DecisionProvenance("AgriClutch-Optimization-Engine"))
    is_demo: bool = True

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "plan_id": self.plan_id,
            "created_at": self.created_at,
            "input_snapshot_id": self.input_snapshot_id,
            "commodity_id": self.commodity_id,
            "variety": self.variety,
            "quality_grade": self.quality_grade,
            "total_supply_kg": self.total_supply_kg,
            "decision_horizon_days": self.decision_horizon_days,
            "risk_preference": self.risk_preference.value,
            "liquidity_preference": self.liquidity_preference.value,
            "allocations": [a.to_dict() for a in self.allocations],
            "total_allocated_kg": round(self.total_allocated_kg, 2),
            "total_unallocated_kg": round(self.total_unallocated_kg, 2),
            "total_effective_kg": round(self.total_effective_kg, 2),
            "expected_gross_revenue": round(self.expected_gross_revenue, 2),
            "total_friction_cost": round(self.total_friction_cost, 2),
            "expected_total_nrv": round(self.expected_total_nrv, 2),
            "risk_adjusted_nrv": round(self.risk_adjusted_nrv, 2),
            "risk_metrics": self.risk_metrics.to_dict() if self.risk_metrics else None,
            "constraint_summary": self.constraint_summary.to_dict() if self.constraint_summary else None,
            "solver_status": self.solver_status.value,
            "validation_status": self.validation_status.value,
            "solver_message": self.solver_message,
            "solver_duration_ms": self.solver_duration_ms,
            "solver_version": self.solver_version,
            "input_hash": self.input_hash,
            "configuration_hash": self.configuration_hash,
            "executive_summary": self.executive_summary,
            "structured_explanations": self.structured_explanations,
            "provenance": self.provenance.to_dict(),
            "is_demo": self.is_demo,
        }
        return d


@dataclass
class CounterfactualDelta:
    """Quantitative comparison between baseline plan and counterfactual plan."""
    parameter_changed: str
    baseline_value: Any
    counterfactual_value: Any
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

    def to_dict(self) -> Dict[str, Any]:
        return {
            "parameter_changed": self.parameter_changed,
            "baseline_value": str(self.baseline_value),
            "counterfactual_value": str(self.counterfactual_value),
            "baseline_nrv": round(self.baseline_nrv, 2),
            "counterfactual_nrv": round(self.counterfactual_nrv, 2),
            "nrv_delta": round(self.nrv_delta, 2),
            "nrv_percentage_change": round(self.nrv_percentage_change, 2),
            "baseline_allocated_kg": round(self.baseline_allocated_kg, 2),
            "counterfactual_allocated_kg": round(self.counterfactual_allocated_kg, 2),
            "allocation_shift_summary": self.allocation_shift_summary,
            "baseline_input_hash": self.baseline_input_hash,
            "counterfactual_input_hash": self.counterfactual_input_hash,
            "baseline_solver_status": self.baseline_solver_status.value,
            "new_solver_status": self.new_solver_status.value,
            "feasibility_changed": self.feasibility_changed,
            "cvar_delta": round(self.cvar_delta, 2),
            "allocation_delta_kg": round(self.allocation_delta_kg, 2),
        }


@dataclass
class WhatIfSimulationResult:
    """Full counterfactual simulation result comparing baseline to alternative."""
    simulation_id: str = field(default_factory=lambda: f"sim_{uuid.uuid4().hex[:8]}")
    baseline_plan: OptimalSellingPlan = field(default_factory=OptimalSellingPlan)
    counterfactual_plan: OptimalSellingPlan = field(default_factory=OptimalSellingPlan)
    comparison: CounterfactualDelta = field(default_factory=lambda: CounterfactualDelta("", "", "", 0, 0, 0, 0, 0, 0, ""))
    is_demo: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "simulation_id": self.simulation_id,
            "baseline_plan": self.baseline_plan.to_dict(),
            "counterfactual_plan": self.counterfactual_plan.to_dict(),
            "comparison": self.comparison.to_dict(),
            "is_demo": self.is_demo,
        }


@dataclass
class SensitivityPoint:
    """Individual evaluated sensitivity step point."""
    step_index: int
    parameter_value: float
    parameter_label: str
    expected_total_nrv: float
    risk_adjusted_nrv: float
    allocated_percentage: float
    is_feasible: bool
    solver_status: SolverStatus

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_index": self.step_index,
            "parameter_value": self.parameter_value,
            "parameter_label": self.parameter_label,
            "expected_total_nrv": round(self.expected_total_nrv, 2),
            "risk_adjusted_nrv": round(self.risk_adjusted_nrv, 2),
            "allocated_percentage": round(self.allocated_percentage, 2),
            "is_feasible": self.is_feasible,
            "solver_status": self.solver_status.value,
        }


@dataclass
class SensitivitySweepResult:
    """Multi-point sensitivity curve across a varied parameter."""
    parameter_name: str
    baseline_value: float
    unit: str
    points: List[SensitivityPoint] = field(default_factory=list)
    break_even_or_switch_points: List[str] = field(default_factory=list)
    interpretation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "parameter_name": self.parameter_name,
            "baseline_value": self.baseline_value,
            "unit": self.unit,
            "points": [p.to_dict() for p in self.points],
            "break_even_or_switch_points": self.break_even_or_switch_points,
            "interpretation": self.interpretation,
        }
