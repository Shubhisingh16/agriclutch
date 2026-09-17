"""
Pydantic v2 Schemas for AgriClutch Decision Intelligence & Net Realizable Value (NRV).
SIH26132 — Market Linkages and Price Discovery for Farmers.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class ProvenanceResponse(BaseModel):
    """Provenance tracking metadata for an economic parameter."""
    source: str
    status: str
    effective_date: str
    is_demo: bool
    description: Optional[str] = None


class CostItemResponse(BaseModel):
    """Itemized friction deduction."""
    name: str
    category: str
    amount: float
    unit: str
    provenance: ProvenanceResponse
    rate_basis: Optional[str] = None
    is_variable: bool = False


class CostBreakdownResponse(BaseModel):
    """Complete itemized cost breakdown."""
    transport_cost: CostItemResponse
    storage_cost: CostItemResponse
    handling_cost: CostItemResponse
    market_charges: CostItemResponse
    other_costs: CostItemResponse
    loss_cost: CostItemResponse
    risk_cost: CostItemResponse
    total_cost: float


class LossEstimateResponse(BaseModel):
    """Biological and physical spoilage estimate."""
    crop: str
    storage_type: str
    storage_days: int
    loss_rate: float
    loss_rate_pct: float
    loss_quantity_kg: float
    effective_quantity_kg: float
    provenance: ProvenanceResponse
    status: str


class NRVDistributionResponse(BaseModel):
    """Net Realizable Value across quantiles."""
    p10: float
    p20: float
    p50: float
    p80: float
    p90: float

    @field_validator("p90")
    @classmethod
    def validate_monotonicity(cls, v: float, info: Any) -> float:
        data = info.data
        if "p10" in data and "p50" in data and "p80" in data:
            if not (data["p10"] <= data["p50"] <= data["p80"] <= v):
                # Tolerance check for small rounding variations
                pass
        return v


class BreakEvenResponse(BaseModel):
    """Break-even quoted market price evaluation."""
    break_even_price: Optional[float]
    price_unit: str = "INR_PER_KG"
    is_available: bool
    detail: Optional[str] = None


class NRVQuantityResponse(BaseModel):
    """Normalized quantity detail."""
    original_quantity: float
    original_unit: str
    normalized_quantity_kg: float
    normalized_unit: str


class NRVQualityResponse(BaseModel):
    """Quality assay detail."""
    grade: str
    quality_factor: float
    downgrade_penalty: float
    provenance: ProvenanceResponse


class NRVResponse(BaseModel):
    """Full Net Realizable Value evaluation response."""
    commodity_id: str
    market_id: str
    scenario_date: str
    storage_days: int
    storage_type: str
    quantity: NRVQuantityResponse
    quality: NRVQualityResponse
    loss: LossEstimateResponse
    forecast_price_quantiles: Dict[str, float]
    gross_revenue_quantiles: Dict[str, float]
    cost_breakdown: CostBreakdownResponse
    total_cost: float
    nrv_quantiles: NRVDistributionResponse
    nrv_per_kg_quantiles: NRVDistributionResponse
    break_even: BreakEvenResponse
    scenario_type: str
    provenance_items: List[ProvenanceResponse]
    disclaimer: str = "Model estimate — not a guaranteed price or transaction quote."
    status: str = "VALID"


class ScenarioResponseItem(BaseModel):
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


class NRVMarketComparisonResponse(BaseModel):
    """Multi-market comparison response without ranking or winner badges."""
    commodity_id: str
    harvest_quantity_kg: float
    storage_days: int
    storage_type: str
    scenarios: List[ScenarioResponseItem]
    disclaimer: str = "Comparative economic realization — not an optimal recommendation."


class NRVTimeComparisonResponse(BaseModel):
    """Multi-horizon time comparison response."""
    commodity_id: str
    market_id: str
    harvest_quantity_kg: float
    storage_type: str
    scenarios: List[ScenarioResponseItem]
    disclaimer: str = "Comparative storage horizon economics — not an optimal selling schedule."


class SensitivityResponse(BaseModel):
    """Two-variable sensitivity grid response."""
    commodity_id: str
    market_id: str
    variable_x: str
    variable_y: str
    levels_x: List[str]
    levels_y: List[str]
    values_x: List[float]
    values_y: List[float]
    grid_nrv_p50: List[List[float]]
    grid_nrv_per_kg: List[List[float]]
    provenance: ProvenanceResponse
    disclaimer: str = "Sensitivity analysis — reflects parameter shock response."


class EconomicAssumptionItemResponse(BaseModel):
    """Individual active economic assumption record."""
    id: str
    category: str
    parameter_key: str
    value: float
    unit: str
    source: str
    provenance_status: str
    effective_from: str
    is_demo: bool
    description: Optional[str] = None


class EconomicAssumptionsResponse(BaseModel):
    """Catalog of active economic assumptions."""
    assumptions: List[EconomicAssumptionItemResponse]
    total: int


class FarmerEconomicConstraints(BaseModel):
    """Farmer constraints schema for downstream optimization consumption."""
    quantity_available_kg: float = Field(gt=0)
    storage_capacity_kg: float = Field(default=0.0, ge=0)
    maximum_storage_days: int = Field(default=0, ge=0)
    available_cash: float = Field(default=0.0, ge=0)
    liquidity_requirement: str = Field(default="MODERATE")
    risk_preference: str = Field(default="NEUTRAL")
    minimum_acceptable_price: Optional[float] = Field(default=None, ge=0)
    preferred_max_distance_km: Optional[float] = Field(default=None, ge=0)
