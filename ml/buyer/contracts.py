"""
AgriClutch Buyer Domain Contracts & Typed Data Structures.
Defines immutable models for buyers, requirements, demands, supplies,
compatibility evaluations, and reliability tracking.
SIH26132 — Strengthening Market Linkages and Price Discovery for Farmers.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any


class BuyerType(str, Enum):
    """Extensible classification of agricultural produce buyers."""
    WHOLESALER = "wholesaler"
    PROCESSOR = "processor"
    RETAILER = "retailer"
    INSTITUTIONAL_BUYER = "institutional_buyer"
    EXPORTER = "exporter"
    FPO = "fpo"
    COOPERATIVE = "cooperative"
    AGGREGATOR = "aggregator"
    TRADER = "trader"


class DeliveryMode(str, Enum):
    """Delivery and logistics handover points."""
    EX_FARM = "EX_FARM"
    MANDI_GATE = "MANDI_GATE"
    BUYER_PREMISES = "BUYER_PREMISES"
    WAREHOUSE = "WAREHOUSE"


class PriceBasis(str, Enum):
    """Pricing structure mechanism."""
    FIXED_QUOTE = "FIXED_QUOTE"
    APMC_INDEXED = "APMC_INDEXED"
    NEGOTIABLE = "NEGOTIABLE"
    UNAVAILABLE = "UNAVAILABLE"


class PaymentTerms(str, Enum):
    """Commercial settlement terms."""
    IMMEDIATE_CASH = "IMMEDIATE_CASH"
    ADVANCE_PARTIAL = "ADVANCE_PARTIAL"
    NET_3_DAYS = "NET_3_DAYS"
    NET_7_DAYS = "NET_7_DAYS"
    NET_15_DAYS = "NET_15_DAYS"
    UPON_DELIVERY = "UPON_DELIVERY"
    UNAVAILABLE = "UNAVAILABLE"


class DemandType(str, Enum):
    """Epistemic classification of buyer demand observations."""
    OBSERVED_DEMAND = "OBSERVED_DEMAND"
    QUOTED_DEMAND = "QUOTED_DEMAND"
    CONTRACTED_DEMAND = "CONTRACTED_DEMAND"
    ESTIMATED_DEMAND = "ESTIMATED_DEMAND"
    DEMO_DEMAND = "DEMO_DEMAND"
    UNAVAILABLE = "UNAVAILABLE"


class DemandStatus(str, Enum):
    """Operational lifecycle state of buyer demand."""
    ACTIVE = "ACTIVE"
    FULFILLED = "FULFILLED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class QuantityMatchStatus(str, Enum):
    """Quantity compatibility state."""
    EXACT_MATCH = "EXACT_MATCH"
    PARTIAL_MATCH = "PARTIAL_MATCH"
    INSUFFICIENT_SUPPLY = "INSUFFICIENT_SUPPLY"
    INSUFFICIENT_DEMAND = "INSUFFICIENT_DEMAND"
    ZERO_MATCH = "ZERO_MATCH"


class TemporalOverlapStatus(str, Enum):
    """Temporal availability window overlap."""
    FULL_OVERLAP = "FULL_OVERLAP"
    PARTIAL_OVERLAP = "PARTIAL_OVERLAP"
    NO_OVERLAP = "NO_OVERLAP"
    EXPIRED_REQUIREMENT = "EXPIRED_REQUIREMENT"
    FUTURE_REQUIREMENT = "FUTURE_REQUIREMENT"
    UNAVAILABLE = "UNAVAILABLE"


class DistanceStatus(str, Enum):
    """Provenance and method of transit distance calculation."""
    DISTANCE_GEODESIC = "DISTANCE_GEODESIC"
    DISTANCE_ROUTE = "DISTANCE_ROUTE"
    DISTANCE_UNAVAILABLE = "DISTANCE_UNAVAILABLE"


class ReliabilityStatus(str, Enum):
    """State of empirical buyer reliability analytics."""
    CALCULATED = "CALCULATED"
    INSUFFICIENT_HISTORY = "INSUFFICIENT_HISTORY"
    UNAVAILABLE = "UNAVAILABLE"


class DistributionStatus(str, Enum):
    """Sufficiency of sample size for statistical distribution."""
    VALID = "VALID"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class ProvenanceStatus(str, Enum):
    """Authoritative source provenance."""
    EMPIRICAL = "EMPIRICAL"
    OFFICIAL = "OFFICIAL"
    RESEARCH = "RESEARCH"
    CONFIGURED = "CONFIGURED"
    DEMO = "DEMO"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True)
class EconomicProvenance:
    """Verifiable source lineage metadata."""
    source_name: str
    source_record_id: str | None = None
    source_reference: str | None = None
    observed_at: str | None = None
    effective_from: str | None = None
    effective_to: str | None = None
    status: ProvenanceStatus = ProvenanceStatus.DEMO
    is_demo: bool = True
    description: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_name": self.source_name,
            "source_record_id": self.source_record_id,
            "source_reference": self.source_reference,
            "observed_at": self.observed_at,
            "effective_from": self.effective_from,
            "effective_to": self.effective_to,
            "status": self.status.value,
            "is_demo": self.is_demo,
            "description": self.description,
        }


@dataclass
class BuyerProfile:
    """Master record for an institutional or market produce buyer."""
    buyer_id: str
    display_name: str
    buyer_type: BuyerType
    location: str
    latitude: float | None = None
    longitude: float | None = None
    active_status: bool = True
    provenance: EconomicProvenance = field(
        default_factory=lambda: EconomicProvenance(source_name="DEMO_BUYER_SEED")
    )
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "buyer_id": self.buyer_id,
            "display_name": self.display_name,
            "buyer_type": self.buyer_type.value,
            "location": self.location,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "active_status": self.active_status,
            "provenance": self.provenance.to_dict(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


@dataclass
class BuyerRequirement:
    """Documented commodity specification and commercial procurement constraints."""
    requirement_id: str
    buyer_id: str
    commodity_id: str
    minimum_quantity_kg: float
    maximum_quantity_kg: float
    preferred_quality_grade: str
    acceptable_quality_range: list[str]
    required_from: date
    required_until: date
    variety: str | None = None
    delivery_mode: DeliveryMode = DeliveryMode.BUYER_PREMISES
    delivery_location: str | None = None
    delivery_latitude: float | None = None
    delivery_longitude: float | None = None
    price_basis: PriceBasis = PriceBasis.FIXED_QUOTE
    quoted_price: float | None = None
    currency: str = "INR"
    price_unit: str = "INR_PER_KG"
    payment_terms: PaymentTerms = PaymentTerms.NET_7_DAYS
    validity_start: date | None = None
    validity_end: date | None = None
    provenance: EconomicProvenance = field(
        default_factory=lambda: EconomicProvenance(source_name="DEMO_REQUIREMENT_SEED")
    )

    def __post_init__(self) -> None:
        if self.minimum_quantity_kg < 0:
            raise ValueError(f"Minimum quantity cannot be negative: {self.minimum_quantity_kg}")
        if self.maximum_quantity_kg < self.minimum_quantity_kg:
            raise ValueError(
                f"Maximum quantity ({self.maximum_quantity_kg}) cannot be less than minimum ({self.minimum_quantity_kg})"
            )
        if self.required_from > self.required_until:
            raise ValueError(
                f"Required from date ({self.required_from}) cannot be after required until ({self.required_until})"
            )
        if self.quoted_price is not None and self.quoted_price < 0:
            raise ValueError(f"Quoted price cannot be negative: {self.quoted_price}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "requirement_id": self.requirement_id,
            "buyer_id": self.buyer_id,
            "commodity_id": self.commodity_id,
            "variety": self.variety,
            "minimum_quantity_kg": self.minimum_quantity_kg,
            "maximum_quantity_kg": self.maximum_quantity_kg,
            "preferred_quality_grade": self.preferred_quality_grade,
            "acceptable_quality_range": self.acceptable_quality_range,
            "required_from": self.required_from.isoformat(),
            "required_until": self.required_until.isoformat(),
            "delivery_mode": self.delivery_mode.value,
            "delivery_location": self.delivery_location,
            "delivery_latitude": self.delivery_latitude,
            "delivery_longitude": self.delivery_longitude,
            "price_basis": self.price_basis.value,
            "quoted_price": self.quoted_price,
            "currency": self.currency,
            "price_unit": self.price_unit,
            "payment_terms": self.payment_terms.value,
            "validity_start": self.validity_start.isoformat() if self.validity_start else None,
            "validity_end": self.validity_end.isoformat() if self.validity_end else None,
            "provenance": self.provenance.to_dict(),
        }


@dataclass
class BuyerDemand:
    """Active demand observation from an individual buyer."""
    demand_id: str
    buyer_id: str
    commodity_id: str
    quantity_kg: float
    quality_requirement: str
    date_window_start: date
    date_window_end: date
    location: str
    variety: str | None = None
    price_per_kg: float | None = None
    price_unit: str = "INR_PER_KG"
    demand_type: DemandType = DemandType.DEMO_DEMAND
    demand_status: DemandStatus = DemandStatus.ACTIVE
    provenance: EconomicProvenance = field(
        default_factory=lambda: EconomicProvenance(source_name="DEMO_DEMAND_SEED")
    )

    def __post_init__(self) -> None:
        if self.quantity_kg <= 0:
            raise ValueError(f"Demand quantity must be strictly positive: {self.quantity_kg}")
        if self.date_window_start > self.date_window_end:
            raise ValueError(f"Date window start ({self.date_window_start}) exceeds end ({self.date_window_end})")
        if self.price_per_kg is not None and self.price_per_kg < 0:
            raise ValueError(f"Price cannot be negative: {self.price_per_kg}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "demand_id": self.demand_id,
            "buyer_id": self.buyer_id,
            "commodity_id": self.commodity_id,
            "variety": self.variety,
            "quantity_kg": self.quantity_kg,
            "quality_requirement": self.quality_requirement,
            "date_window_start": self.date_window_start.isoformat(),
            "date_window_end": self.date_window_end.isoformat(),
            "location": self.location,
            "price_per_kg": self.price_per_kg,
            "price_unit": self.price_unit,
            "demand_type": self.demand_type.value,
            "demand_status": self.demand_status.value,
            "provenance": self.provenance.to_dict(),
        }


@dataclass
class FarmerSupply:
    """Anonymous or FPO-aggregated farm supply profile."""
    supply_id: str
    commodity_id: str
    quantity_kg: float
    quality_grade: str
    available_from: date
    available_until: date
    origin_location: str
    variety: str | None = None
    farmer_or_fpo_reference: str | None = None
    origin_latitude: float | None = None
    origin_longitude: float | None = None
    storage_available: bool = False
    storage_type: str | None = None
    provenance: EconomicProvenance = field(
        default_factory=lambda: EconomicProvenance(source_name="DEMO_SUPPLY_SPEC")
    )

    def __post_init__(self) -> None:
        if self.quantity_kg <= 0:
            raise ValueError(f"Supply quantity must be strictly positive: {self.quantity_kg}")
        if self.available_from > self.available_until:
            raise ValueError(f"Available from ({self.available_from}) exceeds available until ({self.available_until})")

    def to_dict(self) -> dict[str, Any]:
        return {
            "supply_id": self.supply_id,
            "farmer_or_fpo_reference": self.farmer_or_fpo_reference,
            "commodity_id": self.commodity_id,
            "variety": self.variety,
            "quantity_kg": self.quantity_kg,
            "quality_grade": self.quality_grade,
            "available_from": self.available_from.isoformat(),
            "available_until": self.available_until.isoformat(),
            "origin_location": self.origin_location,
            "origin_latitude": self.origin_latitude,
            "origin_longitude": self.origin_longitude,
            "storage_available": self.storage_available,
            "storage_type": self.storage_type,
            "provenance": self.provenance.to_dict(),
        }


@dataclass
class CompatibilityResult:
    """Deterministic, explainable compatibility evaluation between supply and buyer requirement."""
    buyer_id: str
    supply_id: str
    requirement_id: str
    commodity_match: bool
    variety_match: bool
    quality_match: bool
    quantity_match: QuantityMatchStatus
    temporal_match: bool
    delivery_constraint_match: bool
    compatible_quantity_kg: float
    unmatched_supply_kg: float
    unmatched_demand_kg: float
    distance_km: float | None
    distance_status: DistanceStatus
    temporal_overlap_status: TemporalOverlapStatus
    constraint_status: str  # "COMPATIBLE", "PARTIALLY_COMPATIBLE", "INCOMPATIBLE"
    explanations: list[str]
    provenance: EconomicProvenance

    def to_dict(self) -> dict[str, Any]:
        return {
            "buyer_id": self.buyer_id,
            "supply_id": self.supply_id,
            "requirement_id": self.requirement_id,
            "commodity_match": self.commodity_match,
            "variety_match": self.variety_match,
            "quality_match": self.quality_match,
            "quantity_match": self.quantity_match.value,
            "temporal_match": self.temporal_match,
            "delivery_constraint_match": self.delivery_constraint_match,
            "compatible_quantity_kg": round(self.compatible_quantity_kg, 2),
            "unmatched_supply_kg": round(self.unmatched_supply_kg, 2),
            "unmatched_demand_kg": round(self.unmatched_demand_kg, 2),
            "distance_km": round(self.distance_km, 1) if self.distance_km is not None else None,
            "distance_status": self.distance_status.value,
            "temporal_overlap_status": self.temporal_overlap_status.value,
            "constraint_status": self.constraint_status,
            "explanations": self.explanations,
            "provenance": self.provenance.to_dict(),
        }


@dataclass
class BuyerTransactionRecord:
    """Immutable audit record of a past commercial transaction."""
    transaction_id: str
    buyer_id: str
    commodity_id: str
    order_date: date
    agreed_quantity_kg: float
    delivered_quantity_kg: float
    agreed_price_per_kg: float
    fulfillment_status: str  # "FULFILLED", "PARTIAL", "CANCELLED"
    payment_status: str      # "PAID_ON_TIME", "PAID_LATE", "PENDING", "DEFAULTED"
    price_unit: str = "INR_PER_KG"
    agreed_payment_due_date: date | None = None
    actual_payment_date: date | None = None
    dispute_status: bool = False
    provenance: EconomicProvenance = field(
        default_factory=lambda: EconomicProvenance(source_name="DEMO_TRANSACTION_AUDIT")
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "transaction_id": self.transaction_id,
            "buyer_id": self.buyer_id,
            "commodity_id": self.commodity_id,
            "order_date": self.order_date.isoformat(),
            "agreed_quantity_kg": self.agreed_quantity_kg,
            "delivered_quantity_kg": self.delivered_quantity_kg,
            "agreed_price_per_kg": self.agreed_price_per_kg,
            "price_unit": self.price_unit,
            "fulfillment_status": self.fulfillment_status,
            "payment_status": self.payment_status,
            "agreed_payment_due_date": self.agreed_payment_due_date.isoformat() if self.agreed_payment_due_date else None,
            "actual_payment_date": self.actual_payment_date.isoformat() if self.actual_payment_date else None,
            "dispute_status": self.dispute_status,
            "provenance": self.provenance.to_dict(),
        }


@dataclass
class ReliabilityMetrics:
    """Transparent reliability measurements derived strictly from historical transaction events."""
    buyer_id: str
    status: ReliabilityStatus
    sample_size: int
    fulfilled_orders: int
    confirmed_orders: int
    fulfillment_rate: float | None
    cancelled_orders: int
    cancellation_rate: float | None
    quantity_fulfillment_ratio: float | None
    average_payment_delay_days: float | None
    disputed_orders: int
    dispute_rate: float | None
    time_window_start: date | None = None
    time_window_end: date | None = None
    provenance: EconomicProvenance = field(
        default_factory=lambda: EconomicProvenance(source_name="TRANSACTION_LOG_METRICS")
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "buyer_id": self.buyer_id,
            "status": self.status.value,
            "sample_size": self.sample_size,
            "fulfilled_orders": self.fulfilled_orders,
            "confirmed_orders": self.confirmed_orders,
            "fulfillment_rate": round(self.fulfillment_rate, 4) if self.fulfillment_rate is not None else None,
            "cancelled_orders": self.cancelled_orders,
            "cancellation_rate": round(self.cancellation_rate, 4) if self.cancellation_rate is not None else None,
            "quantity_fulfillment_ratio": round(self.quantity_fulfillment_ratio, 4) if self.quantity_fulfillment_ratio is not None else None,
            "average_payment_delay_days": round(self.average_payment_delay_days, 1) if self.average_payment_delay_days is not None else None,
            "disputed_orders": self.disputed_orders,
            "dispute_rate": round(self.dispute_rate, 4) if self.dispute_rate is not None else None,
            "time_window_start": self.time_window_start.isoformat() if self.time_window_start else None,
            "time_window_end": self.time_window_end.isoformat() if self.time_window_end else None,
            "provenance": self.provenance.to_dict(),
        }


@dataclass
class DemandAggregationResult:
    """Aggregated regional and grade-level demand volume and market depth."""
    commodity_id: str
    region: str | None
    total_demand_kg: float
    buyer_count: int
    demand_by_quality: dict[str, float]
    demand_by_region: dict[str, float]
    demand_by_time_window: dict[str, float]
    demand_by_type: dict[str, float]
    top_buyer_share_pct: float | None
    hhi_concentration: float | None
    provenance: EconomicProvenance

    def to_dict(self) -> dict[str, Any]:
        return {
            "commodity_id": self.commodity_id,
            "region": self.region,
            "total_demand_kg": round(self.total_demand_kg, 2),
            "buyer_count": self.buyer_count,
            "demand_by_quality": {k: round(v, 2) for k, v in self.demand_by_quality.items()},
            "demand_by_region": {k: round(v, 2) for k, v in self.demand_by_region.items()},
            "demand_by_time_window": {k: round(v, 2) for k, v in self.demand_by_time_window.items()},
            "demand_by_type": {k: round(v, 2) for k, v in self.demand_by_type.items()},
            "top_buyer_share_pct": round(self.top_buyer_share_pct, 2) if self.top_buyer_share_pct is not None else None,
            "hhi_concentration": round(self.hhi_concentration, 1) if self.hhi_concentration is not None else None,
            "provenance": self.provenance.to_dict(),
        }


@dataclass
class DemandDistributionResult:
    """Descriptive statistics of buyer order sizes."""
    commodity_id: str
    status: DistributionStatus
    observation_count: int
    min_kg: float | None = None
    max_kg: float | None = None
    mean_kg: float | None = None
    median_kg: float | None = None
    p10_kg: float | None = None
    p25_kg: float | None = None
    p50_kg: float | None = None
    p75_kg: float | None = None
    p90_kg: float | None = None
    provenance: EconomicProvenance = field(
        default_factory=lambda: EconomicProvenance(source_name="DEMAND_DISTRIBUTION")
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "commodity_id": self.commodity_id,
            "status": self.status.value,
            "observation_count": self.observation_count,
            "min_kg": round(self.min_kg, 2) if self.min_kg is not None else None,
            "max_kg": round(self.max_kg, 2) if self.max_kg is not None else None,
            "mean_kg": round(self.mean_kg, 2) if self.mean_kg is not None else None,
            "median_kg": round(self.median_kg, 2) if self.median_kg is not None else None,
            "p10_kg": round(self.p10_kg, 2) if self.p10_kg is not None else None,
            "p25_kg": round(self.p25_kg, 2) if self.p25_kg is not None else None,
            "p50_kg": round(self.p50_kg, 2) if self.p50_kg is not None else None,
            "p75_kg": round(self.p75_kg, 2) if self.p75_kg is not None else None,
            "p90_kg": round(self.p90_kg, 2) if self.p90_kg is not None else None,
            "provenance": self.provenance.to_dict(),
        }
