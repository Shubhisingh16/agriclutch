"""
Pydantic v2 Schemas for Buyer Matching & Demand Aggregation Subsystem.
Strictly typed data contracts for buyers, requirements, demands, compatibility evaluation,
reliability metrics, and regional demand aggregation.
SIH26132 — Strengthening Market Linkages and Price Discovery for Farmers.
"""

from datetime import date, datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from ml.buyer.contracts import (
    BuyerType,
    DeliveryMode,
    DemandStatus,
    DemandType,
    DistanceStatus,
    DistributionStatus,
    PaymentTerms,
    PriceBasis,
    ProvenanceStatus,
    QuantityMatchStatus,
    ReliabilityStatus,
    TemporalOverlapStatus,
)


class BuyerBase(BaseModel):
    """Core institutional or wholesale produce buyer attributes."""

    id: str = Field(..., description="Canonical buyer identifier")
    display_name: str = Field(..., min_length=2, max_length=128, description="Standardized buyer entity name")
    buyer_type: BuyerType = Field(..., description="Categorical classification of buyer")
    location: str = Field(..., min_length=2, max_length=128, description="Headquarters or primary procurement hub")
    latitude: Optional[float] = Field(default=None, description="WGS84 latitude")
    longitude: Optional[float] = Field(default=None, description="WGS84 longitude")
    active_status: bool = Field(default=True, description="Whether buyer is actively procuring")
    source_name: str = Field(..., description="Data provenance registry or directory")
    source_record_id: Optional[str] = Field(default=None, description="External registration identifier")
    source_reference: Optional[str] = Field(default=None, description="Citation or legal reference")
    provenance_status: ProvenanceStatus = Field(default=ProvenanceStatus.DEMO, description="Data verification status")
    is_demo: bool = Field(default=True, description="True if synthetic demo benchmark")


class BuyerResponse(BuyerBase):
    """Public API response schema for buyer profile."""

    model_config = ConfigDict(from_attributes=True)
    created_at: Optional[datetime] = Field(default=None, description="Registration timestamp")


class BuyerRequirementBase(BaseModel):
    """Procurement specifications and commercial terms."""

    id: str = Field(..., description="Requirement identifier")
    buyer_id: str = Field(..., description="Associated buyer identifier")
    commodity_id: str = Field(..., description="Target commodity identifier")
    variety: Optional[str] = Field(default=None, description="Required crop variety or specification")
    minimum_quantity_kg: float = Field(..., gt=0, description="Minimum lot quantity accepted in kg")
    maximum_quantity_kg: float = Field(..., gt=0, description="Maximum procurement capacity in kg")
    preferred_quality_grade: str = Field(..., description="Primary preferred grade (e.g. GRADE_A)")
    acceptable_quality_range: List[str] = Field(..., description="List of acceptable grade classifications")
    required_from: date = Field(..., description="Start of delivery acceptance window")
    required_until: date = Field(..., description="End of delivery acceptance window")
    delivery_mode: DeliveryMode = Field(default=DeliveryMode.BUYER_PREMISES, description="Fulfillment location terms")
    delivery_location: Optional[str] = Field(default=None, description="Physical delivery destination")
    delivery_latitude: Optional[float] = Field(default=None, description="Delivery hub latitude")
    delivery_longitude: Optional[float] = Field(default=None, description="Delivery hub longitude")
    price_basis: PriceBasis = Field(default=PriceBasis.FIXED_QUOTE, description="Pricing mechanism")
    quoted_price: Optional[float] = Field(default=None, ge=0, description="Quoted baseline price per unit")
    currency: str = Field(default="INR", description="Currency ISO code")
    price_unit: str = Field(default="INR_PER_KG", description="Price denomination unit")
    payment_terms: PaymentTerms = Field(default=PaymentTerms.NET_7_DAYS, description="Settlement timeline terms")
    validity_start: Optional[date] = Field(default=None, description="Start date of quote validity")
    validity_end: Optional[date] = Field(default=None, description="End date of quote validity")
    provenance_status: ProvenanceStatus = Field(default=ProvenanceStatus.DEMO, description="Data verification status")
    is_demo: bool = Field(default=True, description="True if synthetic demo fixture")


class BuyerRequirementResponse(BuyerRequirementBase):
    """Public API response schema for buyer procurement specification."""

    model_config = ConfigDict(from_attributes=True)


class BuyerDemandBase(BaseModel):
    """Specific active demand order."""

    id: str = Field(..., description="Demand order identifier")
    buyer_id: str = Field(..., description="Associated buyer identifier")
    commodity_id: str = Field(..., description="Target commodity identifier")
    variety: Optional[str] = Field(default=None, description="Crop variety specification")
    quantity_kg: float = Field(..., gt=0, description="Demanded quantity in kg")
    quality_requirement: str = Field(..., description="Demanded quality specification")
    date_window_start: date = Field(..., description="Demand window start date")
    date_window_end: date = Field(..., description="Demand window end date")
    location: str = Field(..., description="Demand delivery location")
    price_per_kg: Optional[float] = Field(default=None, ge=0, description="Indicative demand price in INR/kg")
    price_unit: str = Field(default="INR_PER_KG", description="Price unit")
    demand_type: DemandType = Field(default=DemandType.DEMO_DEMAND, description="Type of demand order")
    demand_status: DemandStatus = Field(default=DemandStatus.ACTIVE, description="Status of demand order")
    provenance_status: ProvenanceStatus = Field(default=ProvenanceStatus.DEMO, description="Data verification status")
    is_demo: bool = Field(default=True, description="True if synthetic demo fixture")


class BuyerDemandResponse(BuyerDemandBase):
    """Public API response schema for active buyer demand."""

    model_config = ConfigDict(from_attributes=True)


class FarmerSupplyRequest(BaseModel):
    """Farmer or FPO produce supply lot for compatibility matching."""

    id: str = Field(default="supply_custom", description="Supply identifier")
    supply_reference_id: Optional[str] = Field(default=None, description="Lot registration tracking number")
    commodity_id: str = Field(..., description="Commodity identifier (e.g. 'tomato', 'onion', 'potato')")
    variety: Optional[str] = Field(default=None, description="Produce variety or cultivar")
    quantity_kg: float = Field(..., gt=0, description="Total available produce quantity in kg")
    quality_grade: str = Field(..., description="Standardized quality grade (e.g. 'GRADE_A', 'GRADE_B', 'GRADE_C')")
    available_from: date = Field(..., description="Earliest dispatch readiness date")
    available_until: date = Field(..., description="Perishability harvest window expiration date")
    origin_location: str = Field(..., min_length=2, description="Farmgate or aggregation center location")
    origin_latitude: Optional[float] = Field(default=None, description="Origin WGS84 latitude")
    origin_longitude: Optional[float] = Field(default=None, description="Origin WGS84 longitude")
    storage_available: bool = Field(default=False, description="Whether on-farm or nearby holding storage is available")
    storage_type: Optional[str] = Field(default=None, description="Storage mode if available")
    provenance_status: ProvenanceStatus = Field(default=ProvenanceStatus.DEMO, description="Supply verification status")
    is_demo: bool = Field(default=True, description="True if synthetic demo supply")


class CompatibilityResponse(BaseModel):
    """
    Evaluated multi-dimensional compatibility assessment for a single buyer requirement.
    Contains strictly factual constraint evaluations with zero normative ranking or recommendation scores.
    """

    buyer_id: str = Field(..., description="Evaluated buyer identifier")
    buyer_name: str = Field(..., description="Evaluated buyer display name")
    requirement_id: str = Field(..., description="Evaluated requirement specification ID")
    commodity_id: str = Field(..., description="Target commodity identifier")
    variety_match: bool = Field(..., description="Whether produce variety matches buyer specification")
    quality_match: bool = Field(..., description="Whether supply grade falls within buyer acceptable quality range")
    preferred_grade: str = Field(..., description="Buyer preferred quality grade")
    acceptable_grades: List[str] = Field(..., description="All acceptable grades")
    quantity_status: QuantityMatchStatus = Field(..., description="Lot quantity constraint evaluation")
    compatible_quantity_kg: float = Field(..., ge=0, description="Quantity within procurement capacity bounds")
    unmatched_supply_kg: float = Field(..., ge=0, description="Excess supply exceeding maximum capacity")
    temporal_status: TemporalOverlapStatus = Field(..., description="Temporal availability window overlap")
    overlap_days: int = Field(..., ge=0, description="Number of overlapping calendar days")
    distance_status: DistanceStatus = Field(..., description="Geodesic distance feasibility status")
    distance_km: Optional[float] = Field(default=None, ge=0, description="Haversine transit distance in km")
    delivery_mode: DeliveryMode = Field(..., description="Delivery terms (e.g. EX_FARM, BUYER_PREMISES)")
    delivery_location: Optional[str] = Field(default=None, description="Destination location")
    price_basis: PriceBasis = Field(..., description="Commercial pricing mechanism")
    quoted_price: Optional[float] = Field(default=None, description="Quoted baseline price in INR/kg")
    payment_terms: PaymentTerms = Field(..., description="Settlement terms (e.g. IMMEDIATE, NET_7_DAYS)")
    is_compatible: bool = Field(..., description="Strict boolean indicating all hard constraints are satisfied")
    explanations: List[str] = Field(..., description="Deterministic factual justification bullets")
    provenance_status: ProvenanceStatus = Field(default=ProvenanceStatus.DEMO, description="Data verification status")
    is_demo: bool = Field(default=True, description="True if synthetic demo evaluation")


class MatchingListResponse(BaseModel):
    """
    Candidate matching evaluation list for a farmer supply lot.
    Provides auditable compatibility assessments across registered buyers.
    """

    supply_id: str = Field(..., description="Evaluated supply lot identifier")
    commodity_id: str = Field(..., description="Target commodity identifier")
    total_supply_kg: float = Field(..., gt=0, description="Evaluated lot quantity in kg")
    matches_evaluated: int = Field(..., ge=0, description="Total buyer requirements inspected")
    compatible_matches_count: int = Field(..., ge=0, description="Count of fully compatible procurement options")
    matches: List[CompatibilityResponse] = Field(..., description="Unranked list of candidate matches")


class ReliabilityMetricsResponse(BaseModel):
    """
    Empirical reliability analytics derived exclusively from immutable transaction logs.
    Strictly gates on sample size N >= 3; otherwise returns INSUFFICIENT_HISTORY.
    """

    buyer_id: str = Field(..., description="Audited buyer identifier")
    status: ReliabilityStatus = Field(..., description="Statistical reliability audit status")
    sample_size: int = Field(..., ge=0, description="Number of historical completed orders evaluated")
    fulfillment_rate: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Ratio of delivered to agreed quantity")
    cancellation_rate: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Ratio of cancelled orders")
    avg_payment_delay_days: Optional[float] = Field(default=None, description="Average calendar days past due date")
    dispute_rate: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Ratio of disputed transactions")
    provenance_status: ProvenanceStatus = Field(default=ProvenanceStatus.DEMO, description="Audit record provenance")
    is_demo: bool = Field(default=True, description="True if calculated from demo transaction fixtures")
    audit_note: str = Field(..., description="Methodological disclosure and statistical gating notice")


class DemandAggregateResponse(BaseModel):
    """
    Regional and market-level demand summaries.
    Aggregates active buyer demand volume with descriptive market concentration metrics.
    """

    commodity_id: str = Field(..., description="Target commodity identifier")
    region: Optional[str] = Field(default=None, description="Target geographic region or corridor")
    total_demand_kg: float = Field(..., ge=0, description="Total aggregated demand volume in kg")
    buyer_count: int = Field(..., ge=0, description="Number of distinct active buyers in region")
    top_buyer_share_pct: Optional[float] = Field(default=None, ge=0, le=100.0, description="Market share of largest single buyer")
    hhi_concentration: Optional[float] = Field(default=None, ge=0, le=10000.0, description="Herfindahl-Hirschman Index")
    breakdown_by_quality: Dict[str, float] = Field(default_factory=dict, description="Demand breakdown by quality grade (kg)")
    breakdown_by_type: Dict[str, float] = Field(default_factory=dict, description="Demand breakdown by buyer type (kg)")
    provenance_status: ProvenanceStatus = Field(default=ProvenanceStatus.DEMO, description="Data verification status")
    is_demo: bool = Field(default=True, description="True if calculated from synthetic demo demands")


class DemandDistributionResponse(BaseModel):
    """
    Empirical order size and price dispersion statistics across active buyer demands.
    Strictly gates on sample size N >= 3; otherwise returns INSUFFICIENT_DATA.
    """

    commodity_id: str = Field(..., description="Target commodity identifier")
    status: DistributionStatus = Field(..., description="Statistical sufficiency status")
    sample_size: int = Field(..., ge=0, description="Number of active demand observations evaluated")
    min_kg: Optional[float] = Field(default=None, description="Minimum order size in kg")
    max_kg: Optional[float] = Field(default=None, description="Maximum order size in kg")
    mean_kg: Optional[float] = Field(default=None, description="Sample arithmetic mean order size in kg")
    median_kg: Optional[float] = Field(default=None, description="Median order size in kg")
    p10_kg: Optional[float] = Field(default=None, description="10th percentile order size in kg")
    p25_kg: Optional[float] = Field(default=None, description="25th percentile (Q1) order size in kg")
    p50_kg: Optional[float] = Field(default=None, description="50th percentile (P50) order size in kg")
    p75_kg: Optional[float] = Field(default=None, description="75th percentile (Q3) order size in kg")
    p90_kg: Optional[float] = Field(default=None, description="90th percentile order size in kg")
    provenance_status: ProvenanceStatus = Field(default=ProvenanceStatus.DEMO, description="Data verification status")
    is_demo: bool = Field(default=True, description="True if calculated from synthetic demo demands")

