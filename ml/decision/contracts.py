"""
AgriClutch Decision Intelligence & Net Realizable Value (NRV) Contracts.
Strict typed dataclasses, enums, and domain contracts for economic calculations.
SIH26132 — Market Linkages and Price Discovery for Farmers.
"""

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ProvenanceStatus(str, Enum):
    """Authoritative provenance classification for all economic inputs."""
    EMPIRICAL = "EMPIRICAL"
    OFFICIAL = "OFFICIAL"
    RESEARCH = "RESEARCH"
    CONFIGURED = "CONFIGURED"
    DEMO = "DEMO"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True)
class EconomicProvenance:
    """Provenance tracking for any economic rate, tariff, or adjustment."""
    source: str
    status: ProvenanceStatus
    effective_date: str
    is_demo: bool = True
    description: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "status": self.status.value if isinstance(self.status, ProvenanceStatus) else str(self.status),
            "effective_date": self.effective_date,
            "is_demo": self.is_demo,
            "description": self.description,
        }


@dataclass(frozen=True)
class EconomicAssumption:
    """Typed representation of a stored or configured economic parameter."""
    key: str
    category: str
    value: float
    unit: str
    provenance: EconomicProvenance
    description: Optional[str] = None


@dataclass
class QuantitySpec:
    """
    Dimensional quantity container enforcing safe validation and conversion.
    Internal calculations normalize strictly to kilograms (kg).
    """
    original_quantity: float
    original_unit: str
    normalized_quantity_kg: float = field(init=False)
    normalized_unit: str = "KG"

    UNIT_MULTIPLIERS: Dict[str, float] = field(
        default_factory=lambda: {
            "kg": 1.0,
            "kilogram": 1.0,
            "kilograms": 1.0,
            "quintal": 100.0,
            "quintals": 100.0,
            "q": 100.0,
            "tonne": 1000.0,
            "tonnes": 1000.0,
            "ton": 1000.0,
            "tons": 1000.0,
            "mt": 1000.0,
        },
        init=False,
        repr=False,
    )

    def __post_init__(self) -> None:
        self._validate()

    def _validate(self) -> None:
        if not math.isfinite(self.original_quantity):
            raise ValueError(f"Quantity must be a finite number, received: {self.original_quantity}")
        if self.original_quantity <= 0:
            raise ValueError(f"Quantity must be strictly positive (>0), received: {self.original_quantity}")

        norm_u = self.original_unit.strip().lower()
        if norm_u not in self.UNIT_MULTIPLIERS:
            supported = list(self.UNIT_MULTIPLIERS.keys())
            raise ValueError(f"Unsupported quantity unit '{self.original_unit}'. Supported: {supported}")

        self.normalized_quantity_kg = round(self.original_quantity * self.UNIT_MULTIPLIERS[norm_u], 4)

    @classmethod
    def from_input(cls, quantity: float, unit: str = "kg") -> "QuantitySpec":
        return cls(original_quantity=quantity, original_unit=unit)


@dataclass(frozen=True)
class QualitySpec:
    """Quality assay and grade specification."""
    grade: str
    quality_factor: float
    provenance: EconomicProvenance
    downgrade_penalty: float = 0.0


@dataclass(frozen=True)
class CostItem:
    """Itemized friction deduction with provenance traceability."""
    name: str
    category: str
    amount: float
    unit: str
    provenance: EconomicProvenance
    rate_basis: Optional[str] = None
    is_variable: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "category": self.category,
            "amount": round(self.amount, 2),
            "unit": self.unit,
            "provenance": self.provenance.to_dict(),
            "rate_basis": self.rate_basis,
            "is_variable": self.is_variable,
        }


@dataclass
class CostBreakdown:
    """Itemized collection of all operational deductions."""
    transport_cost: CostItem
    storage_cost: CostItem
    handling_cost: CostItem
    market_charges: CostItem
    other_costs: CostItem
    loss_cost: CostItem
    risk_cost: CostItem
    total_cost: float = field(init=False)

    def __post_init__(self) -> None:
        self.total_cost = round(
            self.transport_cost.amount
            + self.storage_cost.amount
            + self.handling_cost.amount
            + self.market_charges.amount
            + self.other_costs.amount
            + self.loss_cost.amount
            + self.risk_cost.amount,
            2,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "transport_cost": self.transport_cost.to_dict(),
            "storage_cost": self.storage_cost.to_dict(),
            "handling_cost": self.handling_cost.to_dict(),
            "market_charges": self.market_charges.to_dict(),
            "other_costs": self.other_costs.to_dict(),
            "loss_cost": self.loss_cost.to_dict(),
            "risk_cost": self.risk_cost.to_dict(),
            "total_cost": self.total_cost,
        }


@dataclass(frozen=True)
class LossEstimate:
    """Biological and physical spoilage estimation."""
    crop: str
    storage_type: str
    storage_days: int
    loss_rate: float
    loss_quantity_kg: float
    effective_quantity_kg: float
    provenance: EconomicProvenance
    status: str = "VALID"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "crop": self.crop,
            "storage_type": self.storage_type,
            "storage_days": self.storage_days,
            "loss_rate": round(self.loss_rate, 4),
            "loss_rate_pct": round(self.loss_rate * 100.0, 2),
            "loss_quantity_kg": round(self.loss_quantity_kg, 2),
            "effective_quantity_kg": round(self.effective_quantity_kg, 2),
            "provenance": self.provenance.to_dict(),
            "status": self.status,
        }


@dataclass(frozen=True)
class RiskSpec:
    """Uncertainty specifications for price, logistics, and perishability."""
    price_uncertainty: str = "MODELED_QUANTILES"
    cost_uncertainty: str = "NOT_MODELED"
    operational_risk_cost: float = 0.0
    risk_status: str = "NOT_MODELED"
    provenance: EconomicProvenance = field(
        default_factory=lambda: EconomicProvenance(
            source="AGRICLUTCH_DEFAULT_RISK",
            status=ProvenanceStatus.CONFIGURED,
            effective_date="2024-09-15",
            is_demo=True,
            description="Operational risk set to 0.0 with status NOT_MODELED",
        )
    )


@dataclass(frozen=True)
class NRVDistribution:
    """Net Realizable Value across quantiles."""
    p10: float
    p20: float
    p50: float
    p80: float
    p90: float

    def to_dict(self) -> Dict[str, float]:
        return {
            "p10": round(self.p10, 2),
            "p20": round(self.p20, 2),
            "p50": round(self.p50, 2),
            "p80": round(self.p80, 2),
            "p90": round(self.p90, 2),
        }


@dataclass(frozen=True)
class BreakEvenResult:
    """Break-even quoted market price evaluation."""
    break_even_price: Optional[float]
    price_unit: str = "INR_PER_KG"
    is_available: bool = True
    detail: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "break_even_price": round(self.break_even_price, 2) if self.break_even_price is not None else None,
            "price_unit": self.price_unit,
            "is_available": self.is_available,
            "detail": self.detail,
        }


@dataclass
class NRVCalculationResult:
    """Complete, explainable Net Realizable Value result."""
    commodity_id: str
    market_id: str
    scenario_date: str
    storage_days: int
    storage_type: str
    quantity: QuantitySpec
    quality: QualitySpec
    loss: LossEstimate
    forecast_price_quantiles: Dict[str, float]
    gross_revenue_quantiles: Dict[str, float]
    cost_breakdown: CostBreakdown
    total_cost: float
    nrv_quantiles: NRVDistribution
    nrv_per_kg_quantiles: NRVDistribution
    break_even: BreakEvenResult
    scenario_type: str  # "EXPECTED", "CONSERVATIVE", "OPTIMISTIC"
    provenance_items: List[EconomicProvenance]
    status: str = "VALID"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "commodity_id": self.commodity_id,
            "market_id": self.market_id,
            "scenario_date": self.scenario_date,
            "storage_days": self.storage_days,
            "storage_type": self.storage_type,
            "quantity": {
                "original_quantity": self.quantity.original_quantity,
                "original_unit": self.quantity.original_unit,
                "normalized_quantity_kg": self.quantity.normalized_quantity_kg,
                "normalized_unit": self.quantity.normalized_unit,
            },
            "quality": {
                "grade": self.quality.grade,
                "quality_factor": self.quality.quality_factor,
                "downgrade_penalty": self.quality.downgrade_penalty,
                "provenance": self.quality.provenance.to_dict(),
            },
            "loss": self.loss.to_dict(),
            "forecast_price_quantiles": {k: round(v, 2) for k, v in self.forecast_price_quantiles.items()},
            "gross_revenue_quantiles": {k: round(v, 2) for k, v in self.gross_revenue_quantiles.items()},
            "cost_breakdown": self.cost_breakdown.to_dict(),
            "total_cost": self.total_cost,
            "nrv_quantiles": self.nrv_quantiles.to_dict(),
            "nrv_per_kg_quantiles": self.nrv_per_kg_quantiles.to_dict(),
            "break_even": self.break_even.to_dict(),
            "scenario_type": self.scenario_type,
            "provenance_items": [p.to_dict() for p in self.provenance_items],
            "status": self.status,
        }


@dataclass
class ScenarioResult:
    """Individual scenario entry for multi-market or multi-horizon comparisons."""
    scenario_id: str
    market_id: str
    market_name: str
    scenario_date: str
    storage_days: int
    storage_type: str
    distance_km: float
    effective_quantity_kg: float
    forecast_modal_price: float
    gross_revenue: float
    transport_cost: float
    storage_cost: float
    handling_cost: float
    market_charges: float
    other_costs: float
    spoilage_loss_cost: float
    total_cost: float
    nrv_p10: float
    nrv_p50: float
    nrv_p90: float
    nrv_per_kg_p50: float
    break_even_price: Optional[float]
    provenance_status: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "market_id": self.market_id,
            "market_name": self.market_name,
            "scenario_date": self.scenario_date,
            "storage_days": self.storage_days,
            "storage_type": self.storage_type,
            "distance_km": round(self.distance_km, 1),
            "effective_quantity_kg": round(self.effective_quantity_kg, 2),
            "forecast_modal_price": round(self.forecast_modal_price, 2),
            "gross_revenue": round(self.gross_revenue, 2),
            "transport_cost": round(self.transport_cost, 2),
            "storage_cost": round(self.storage_cost, 2),
            "handling_cost": round(self.handling_cost, 2),
            "market_charges": round(self.market_charges, 2),
            "other_costs": round(self.other_costs, 2),
            "spoilage_loss_cost": round(self.spoilage_loss_cost, 2),
            "total_cost": round(self.total_cost, 2),
            "nrv_p10": round(self.nrv_p10, 2),
            "nrv_p50": round(self.nrv_p50, 2),
            "nrv_p90": round(self.nrv_p90, 2),
            "nrv_per_kg_p50": round(self.nrv_per_kg_p50, 2),
            "break_even_price": round(self.break_even_price, 2) if self.break_even_price is not None else None,
            "provenance_status": self.provenance_status,
        }


@dataclass
class SensitivityMatrixResult:
    """Two-variable sensitivity analysis matrix."""
    variable_x: str
    variable_y: str
    levels_x: List[str]  # e.g. ["LOW", "BASE", "HIGH"]
    levels_y: List[str]
    values_x: List[float]
    values_y: List[float]
    grid_nrv_p50: List[List[float]]  # matrix: row y, col x
    grid_nrv_per_kg: List[List[float]]
    provenance: EconomicProvenance

    def to_dict(self) -> Dict[str, Any]:
        return {
            "variable_x": self.variable_x,
            "variable_y": self.variable_y,
            "levels_x": self.levels_x,
            "levels_y": self.levels_y,
            "values_x": [round(v, 2) for v in self.values_x],
            "values_y": [round(v, 2) for v in self.values_y],
            "grid_nrv_p50": [[round(val, 2) for val in row] for row in self.grid_nrv_p50],
            "grid_nrv_per_kg": [[round(val, 2) for val in row] for row in self.grid_nrv_per_kg],
            "provenance": self.provenance.to_dict(),
        }


@dataclass
class FarmerConstraints:
    """Typed container for future farmer constraints (stored, not used for recommendations in Step 11)."""
    quantity_available_kg: float
    storage_capacity_kg: float = 0.0
    maximum_storage_days: int = 0
    available_cash: float = 0.0
    liquidity_requirement: str = "MODERATE"  # HIGH, MODERATE, LOW
    risk_preference: str = "NEUTRAL"  # RISK_AVERSE, NEUTRAL, RISK_SEEKING
    minimum_acceptable_price: Optional[float] = None
    preferred_max_distance_km: Optional[float] = None
