"""
AgriClutch Buyer Matching & Demand Aggregation Service Layer.
Coordinates buyer profile retrieval, multi-dimensional compatibility matching,
empirical reliability auditing, and regional demand aggregation.
SIH26132 — Strengthening Market Linkages and Price Discovery for Farmers.
"""

import logging
from datetime import date, datetime
from typing import Dict, List, Optional

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.seeds.buyer_demo_seed_data import (
    DEMO_BUYER_DEMANDS,
    DEMO_BUYER_REQUIREMENTS,
    DEMO_BUYER_TRANSACTIONS,
    DEMO_BUYERS,
    DEMO_FARMER_SUPPLIES,
)
from app.models.buyer import (
    BuyerCommodityRequirementModel,
    BuyerDemandModel,
    BuyerModel,
    BuyerTransactionModel,
)
from app.schemas.buyer import (
    BuyerDemandResponse,
    BuyerRequirementResponse,
    BuyerResponse,
    CompatibilityResponse,
    DemandAggregateResponse,
    DemandDistributionResponse,
    FarmerSupplyRequest,
    MatchingListResponse,
    ReliabilityMetricsResponse,
)
from ml.buyer.aggregation import DemandAggregationEngine
from ml.buyer.compatibility import CompatibilityEngine
from ml.buyer.contracts import (
    BuyerDemand,
    BuyerRequirement,
    BuyerTransactionRecord,
    BuyerType,
    DeliveryMode,
    DemandStatus,
    DemandType,
    DistanceStatus,
    EconomicProvenance,
    FarmerSupply,
    PaymentTerms,
    PriceBasis,
    ProvenanceStatus,
    TemporalOverlapStatus,
)
from ml.buyer.reliability import BuyerReliabilityEngine

logger = logging.getLogger("agriclutch.services.buyer")


class BuyerService:
    """
    Business logic and operational service for Buyer Intelligence & Demand Aggregation.
    Enforces clean-room IP, anti-fabrication fail-closed policies, and transparent provenance.
    """

    def __init__(self, db: Optional[AsyncSession] = None) -> None:
        self.db = db
        self.compatibility_engine = CompatibilityEngine()
        self.aggregation_engine = DemandAggregationEngine()

    async def _is_demo_mode(self, data_mode: Optional[str] = None) -> bool:
        """Determines whether to operate in demo benchmark mode or live database mode."""
        mode = data_mode or settings.DATA_MODE
        return mode == "demo"

    # =========================================================================
    # 1. BUYER PROFILE ACCESS
    # =========================================================================

    async def list_buyers(
        self,
        buyer_type: Optional[str] = None,
        location: Optional[str] = None,
        commodity_id: Optional[str] = None,
        data_mode: Optional[str] = None,
    ) -> List[BuyerResponse]:
        """
        Retrieves registered buyers with optional filtering by type, location, and commodity.
        Fails closed in database mode if database is offline or unseeded.
        """
        is_demo = await self._is_demo_mode(data_mode)

        if not is_demo:
            if self.db is None:
                raise HTTPException(
                    status_code=503,
                    detail="Database session required for production database mode (fail-closed).",
                    headers={"X-AgriClutch-Data-Mode": "DATABASE"},
                )
            try:
                stmt = select(BuyerModel).where(BuyerModel.active_status.is_(True))
                if buyer_type:
                    stmt = stmt.where(BuyerModel.buyer_type == buyer_type)
                if location:
                    stmt = stmt.where(BuyerModel.location.ilike(f"%{location}%"))
                result = await self.db.execute(stmt)
                buyers = result.scalars().all()
            except Exception as exc:
                logger.error("Database query failed in list_buyers: %s", exc)
                raise HTTPException(
                    status_code=503,
                    detail=f"Database query error while loading buyers: {exc}",
                    headers={"X-AgriClutch-Data-Mode": "DATABASE"},
                ) from exc

            if not buyers:
                raise HTTPException(
                    status_code=503,
                    detail="BUYER_DATA_UNAVAILABLE: No active buyers configured in database.",
                    headers={"X-AgriClutch-Data-Mode": "DATABASE"},
                )

            return [
                BuyerResponse(
                    id=b.id,
                    display_name=b.display_name,
                    buyer_type=BuyerType(b.buyer_type),
                    location=b.location,
                    latitude=b.latitude,
                    longitude=b.longitude,
                    active_status=b.active_status,
                    source_name=b.source_name,
                    source_record_id=b.source_record_id,
                    source_reference=b.source_reference,
                    provenance_status=ProvenanceStatus(b.provenance_status),
                    is_demo=b.is_demo,
                    created_at=b.created_at,
                )
                for b in buyers
            ]

        # Demo mode: load explicit benchmark fixtures
        results: List[BuyerResponse] = []
        for raw in DEMO_BUYERS:
            if buyer_type and raw["buyer_type"] != buyer_type:
                continue
            if location and location.lower() not in raw["location"].lower():
                continue
            if commodity_id:
                has_comm = any(
                    r["buyer_id"] == raw["id"] and r["commodity_id"].lower() == commodity_id.lower()
                    for r in DEMO_BUYER_REQUIREMENTS
                )
                if not has_comm:
                    continue

            results.append(
                BuyerResponse(
                    id=raw["id"],
                    display_name=raw["display_name"],
                    buyer_type=BuyerType(raw["buyer_type"]),
                    location=raw["location"],
                    latitude=raw.get("latitude"),
                    longitude=raw.get("longitude"),
                    active_status=raw["active_status"],
                    source_name=raw["source_name"],
                    source_record_id=raw.get("source_record_id"),
                    source_reference=raw.get("source_reference"),
                    provenance_status=ProvenanceStatus(raw["provenance_status"]),
                    is_demo=raw["is_demo"],
                    created_at=datetime.now(),
                )
            )
        return results

    async def get_buyer(self, buyer_id: str, data_mode: Optional[str] = None) -> BuyerResponse:
        """Retrieves single buyer profile by identifier."""
        is_demo = await self._is_demo_mode(data_mode)
        if not is_demo:
            if self.db is None:
                raise HTTPException(
                    status_code=503,
                    detail="Database session required for production database mode (fail-closed).",
                    headers={"X-AgriClutch-Data-Mode": "DATABASE"},
                )
            try:
                stmt = select(BuyerModel).where(BuyerModel.id == buyer_id)
                res = await self.db.execute(stmt)
                buyer = res.scalar_one_or_none()
            except Exception as exc:
                raise HTTPException(status_code=503, detail=f"Database error: {exc}") from exc

            if not buyer:
                raise HTTPException(status_code=404, detail=f"Buyer not found: {buyer_id}")
            return BuyerResponse(
                id=buyer.id,
                display_name=buyer.display_name,
                buyer_type=BuyerType(buyer.buyer_type),
                location=buyer.location,
                latitude=buyer.latitude,
                longitude=buyer.longitude,
                active_status=buyer.active_status,
                source_name=buyer.source_name,
                source_record_id=buyer.source_record_id,
                source_reference=buyer.source_reference,
                provenance_status=ProvenanceStatus(buyer.provenance_status),
                is_demo=buyer.is_demo,
                created_at=buyer.created_at,
            )

        # Demo mode
        for raw in DEMO_BUYERS:
            if raw["id"] == buyer_id:
                return BuyerResponse(
                    id=raw["id"],
                    display_name=raw["display_name"],
                    buyer_type=BuyerType(raw["buyer_type"]),
                    location=raw["location"],
                    latitude=raw.get("latitude"),
                    longitude=raw.get("longitude"),
                    active_status=raw["active_status"],
                    source_name=raw["source_name"],
                    source_record_id=raw.get("source_record_id"),
                    source_reference=raw.get("source_reference"),
                    provenance_status=ProvenanceStatus(raw["provenance_status"]),
                    is_demo=raw["is_demo"],
                    created_at=datetime.now(),
                )
        raise HTTPException(status_code=404, detail=f"Buyer not found in demo benchmark: {buyer_id}")

    # =========================================================================
    # 2. REQUIREMENTS & DEMANDS
    # =========================================================================

    async def get_buyer_requirements(
        self,
        buyer_id: str,
        commodity_id: Optional[str] = None,
        data_mode: Optional[str] = None,
    ) -> List[BuyerRequirementResponse]:
        """Retrieves procurement specifications and commercial terms for a buyer."""
        is_demo = await self._is_demo_mode(data_mode)
        if not is_demo:
            if self.db is None:
                raise HTTPException(status_code=503, detail="Database session required.")
            try:
                stmt = select(BuyerCommodityRequirementModel).where(
                    BuyerCommodityRequirementModel.buyer_id == buyer_id
                )
                if commodity_id:
                    stmt = stmt.where(BuyerCommodityRequirementModel.commodity_id == commodity_id)
                res = await self.db.execute(stmt)
                records = res.scalars().all()
            except Exception as exc:
                raise HTTPException(status_code=503, detail=f"Database error: {exc}") from exc

            return [
                BuyerRequirementResponse(
                    id=r.id,
                    buyer_id=r.buyer_id,
                    commodity_id=r.commodity_id,
                    variety=r.variety,
                    minimum_quantity_kg=r.minimum_quantity_kg,
                    maximum_quantity_kg=r.maximum_quantity_kg,
                    preferred_quality_grade=r.preferred_quality_grade,
                    acceptable_quality_range=r.acceptable_quality_range,
                    required_from=r.required_from,
                    required_until=r.required_until,
                    delivery_mode=DeliveryMode(r.delivery_mode),
                    delivery_location=r.delivery_location,
                    delivery_latitude=r.delivery_latitude,
                    delivery_longitude=r.delivery_longitude,
                    price_basis=PriceBasis(r.price_basis),
                    quoted_price=r.quoted_price,
                    currency=r.currency,
                    price_unit=r.price_unit,
                    payment_terms=PaymentTerms(r.payment_terms),
                    validity_start=r.validity_start,
                    validity_end=r.validity_end,
                    provenance_status=ProvenanceStatus(r.provenance_status),
                    is_demo=r.is_demo,
                )
                for r in records
            ]

        # Demo mode
        out: List[BuyerRequirementResponse] = []
        for r in DEMO_BUYER_REQUIREMENTS:
            if r["buyer_id"] == buyer_id:
                if commodity_id and r["commodity_id"].lower() != commodity_id.lower():
                    continue
                out.append(
                    BuyerRequirementResponse(
                        id=r["id"],
                        buyer_id=r["buyer_id"],
                        commodity_id=r["commodity_id"],
                        variety=r.get("variety"),
                        minimum_quantity_kg=r["minimum_quantity_kg"],
                        maximum_quantity_kg=r["maximum_quantity_kg"],
                        preferred_quality_grade=r["preferred_quality_grade"],
                        acceptable_quality_range=r["acceptable_quality_range"],
                        required_from=r["required_from"],
                        required_until=r["required_until"],
                        delivery_mode=DeliveryMode(r["delivery_mode"]),
                        delivery_location=r.get("delivery_location"),
                        delivery_latitude=r.get("delivery_latitude"),
                        delivery_longitude=r.get("delivery_longitude"),
                        price_basis=PriceBasis(r["price_basis"]),
                        quoted_price=r.get("quoted_price"),
                        currency=r.get("currency", "INR"),
                        price_unit=r.get("price_unit", "INR_PER_KG"),
                        payment_terms=PaymentTerms(r["payment_terms"]),
                        validity_start=r.get("validity_start"),
                        validity_end=r.get("validity_end"),
                        provenance_status=ProvenanceStatus(r["provenance_status"]),
                        is_demo=r["is_demo"],
                    )
                )
        return out

    async def get_buyer_demands(
        self,
        buyer_id: str,
        commodity_id: Optional[str] = None,
        data_mode: Optional[str] = None,
    ) -> List[BuyerDemandResponse]:
        """Retrieves active spot demand orders for a buyer."""
        is_demo = await self._is_demo_mode(data_mode)
        if not is_demo:
            if self.db is None:
                raise HTTPException(status_code=503, detail="Database session required.")
            try:
                stmt = select(BuyerDemandModel).where(BuyerDemandModel.buyer_id == buyer_id)
                if commodity_id:
                    stmt = stmt.where(BuyerDemandModel.commodity_id == commodity_id)
                res = await self.db.execute(stmt)
                records = res.scalars().all()
            except Exception as exc:
                raise HTTPException(status_code=503, detail=f"Database error: {exc}") from exc

            return [
                BuyerDemandResponse(
                    id=d.id,
                    buyer_id=d.buyer_id,
                    commodity_id=d.commodity_id,
                    variety=d.variety,
                    quantity_kg=d.quantity_kg,
                    quality_requirement=d.quality_requirement,
                    date_window_start=d.date_window_start,
                    date_window_end=d.date_window_end,
                    location=d.location,
                    price_per_kg=d.price_per_kg,
                    price_unit=d.price_unit,
                    demand_type=DemandType(d.demand_type),
                    demand_status=DemandStatus(d.demand_status),
                    provenance_status=ProvenanceStatus(d.provenance_status),
                    is_demo=d.is_demo,
                )
                for d in records
            ]

        # Demo mode
        out: List[BuyerDemandResponse] = []
        for d in DEMO_BUYER_DEMANDS:
            if d["buyer_id"] == buyer_id:
                if commodity_id and d["commodity_id"].lower() != commodity_id.lower():
                    continue
                out.append(
                    BuyerDemandResponse(
                        id=d["id"],
                        buyer_id=d["buyer_id"],
                        commodity_id=d["commodity_id"],
                        variety=d.get("variety"),
                        quantity_kg=d["quantity_kg"],
                        quality_requirement=d["quality_requirement"],
                        date_window_start=d["date_window_start"],
                        date_window_end=d["date_window_end"],
                        location=d["location"],
                        price_per_kg=d.get("price_per_kg"),
                        price_unit=d.get("price_unit", "INR_PER_KG"),
                        demand_type=DemandType(d["demand_type"]),
                        demand_status=DemandStatus(d["demand_status"]),
                        provenance_status=ProvenanceStatus(d["provenance_status"]),
                        is_demo=d["is_demo"],
                    )
                )
        return out

    # =========================================================================
    # 3. EMPIRICAL RELIABILITY AUDITING
    # =========================================================================

    async def get_buyer_reliability(
        self,
        buyer_id: str,
        data_mode: Optional[str] = None,
    ) -> ReliabilityMetricsResponse:
        """
        Calculates empirical reliability analytics for a buyer strictly from immutable transaction logs.
        Enforces statistical sufficiency gating (N >= 3); returns INSUFFICIENT_HISTORY otherwise.
        """
        is_demo = await self._is_demo_mode(data_mode)
        tx_records: List[BuyerTransactionRecord] = []

        if not is_demo:
            if self.db is None:
                raise HTTPException(status_code=503, detail="Database session required.")
            try:
                stmt = select(BuyerTransactionModel).where(BuyerTransactionModel.buyer_id == buyer_id)
                res = await self.db.execute(stmt)
                db_txs = res.scalars().all()
            except Exception as exc:
                raise HTTPException(status_code=503, detail=f"Database error: {exc}") from exc

            for t in db_txs:
                tx_records.append(
                    BuyerTransactionRecord(
                        transaction_id=t.id,
                        buyer_id=t.buyer_id,
                        commodity_id=t.commodity_id,
                        order_date=t.order_date,
                        agreed_quantity_kg=t.agreed_quantity_kg,
                        delivered_quantity_kg=t.delivered_quantity_kg,
                        agreed_price_per_kg=t.agreed_price_per_kg,
                        fulfillment_status=t.fulfillment_status,
                        payment_status=t.payment_status,
                        agreed_payment_due_date=t.agreed_payment_due_date,
                        actual_payment_date=t.actual_payment_date,
                        dispute_status=t.dispute_status,
                        provenance=EconomicProvenance(
                            source_name="TRANSACTION_AUDIT_LOG",
                            status=ProvenanceStatus(t.provenance_status),
                            is_demo=t.is_demo,
                        ),
                    )
                )
        else:
            for demo_t in DEMO_BUYER_TRANSACTIONS:
                if demo_t["buyer_id"] == buyer_id:
                    tx_records.append(
                        BuyerTransactionRecord(
                            transaction_id=demo_t["id"],
                            buyer_id=demo_t["buyer_id"],
                            commodity_id=demo_t["commodity_id"],
                            order_date=demo_t["order_date"],
                            agreed_quantity_kg=demo_t["agreed_quantity_kg"],
                            delivered_quantity_kg=demo_t["delivered_quantity_kg"],
                            agreed_price_per_kg=demo_t["agreed_price_per_kg"],
                            fulfillment_status=demo_t["fulfillment_status"],
                            payment_status=demo_t["payment_status"],
                            agreed_payment_due_date=demo_t.get("agreed_payment_due_date"),
                            actual_payment_date=demo_t.get("actual_payment_date"),
                            dispute_status=demo_t["dispute_status"],
                            provenance=EconomicProvenance(
                                source_name="DEMO_TRANSACTION_AUDIT",
                                status=ProvenanceStatus(demo_t["provenance_status"]),
                                is_demo=demo_t["is_demo"],
                            ),
                        )
                    )

        metrics = BuyerReliabilityEngine.calculate(buyer_id=buyer_id, transactions=tx_records)
        return ReliabilityMetricsResponse(
            buyer_id=metrics.buyer_id,
            status=metrics.status,
            sample_size=metrics.sample_size,
            fulfillment_rate=metrics.fulfillment_rate,
            cancellation_rate=metrics.cancellation_rate,
            avg_payment_delay_days=metrics.average_payment_delay_days,
            dispute_rate=metrics.dispute_rate,
            provenance_status=metrics.provenance.status,
            is_demo=metrics.provenance.is_demo,
            audit_note=metrics.provenance.description or "",
        )

    # =========================================================================
    # 4. BUYER COMPATIBILITY MATCHING
    # =========================================================================

    async def match_supply(
        self,
        supply: FarmerSupplyRequest,
        max_distance_km: Optional[float] = None,
        data_mode: Optional[str] = None,
    ) -> MatchingListResponse:
        """
        Evaluates multi-dimensional compatibility between farmer produce supply and buyer specifications.
        Returns candidate matches with factual constraint assessments.
        CRITICAL: Contains ZERO normative rankings, scores, or recommendations.
        """
        is_demo = await self._is_demo_mode(data_mode)
        farmer_supply = FarmerSupply(
            supply_id=supply.id,
            farmer_or_fpo_reference=supply.supply_reference_id,
            commodity_id=supply.commodity_id.lower(),
            variety=supply.variety,
            quantity_kg=supply.quantity_kg,
            quality_grade=supply.quality_grade,
            available_from=supply.available_from,
            available_until=supply.available_until,
            origin_location=supply.origin_location,
            origin_latitude=supply.origin_latitude,
            origin_longitude=supply.origin_longitude,
            storage_available=supply.storage_available,
            storage_type=supply.storage_type,
            provenance=EconomicProvenance(
                source_name="SUPPLY_SPECIFICATION",
                status=supply.provenance_status,
                is_demo=supply.is_demo,
            ),
        )

        buyer_map: Dict[str, str] = {}
        candidate_requirements: List[BuyerRequirement] = []

        if not is_demo:
            if self.db is None:
                raise HTTPException(status_code=503, detail="Database session required.")
            try:
                stmt_buyers = select(BuyerModel).where(BuyerModel.active_status.is_(True))
                res_buyers = await self.db.execute(stmt_buyers)
                for b in res_buyers.scalars().all():
                    buyer_map[b.id] = b.display_name

                stmt_req = select(BuyerCommodityRequirementModel).where(
                    BuyerCommodityRequirementModel.commodity_id == supply.commodity_id.lower()
                )
                res_req = await self.db.execute(stmt_req)
                for r in res_req.scalars().all():
                    candidate_requirements.append(
                        BuyerRequirement(
                            requirement_id=r.id,
                            buyer_id=r.buyer_id,
                            commodity_id=r.commodity_id,
                            variety=r.variety,
                            minimum_quantity_kg=r.minimum_quantity_kg,
                            maximum_quantity_kg=r.maximum_quantity_kg,
                            preferred_quality_grade=r.preferred_quality_grade,
                            acceptable_quality_range=r.acceptable_quality_range,
                            required_from=r.required_from,
                            required_until=r.required_until,
                            delivery_mode=DeliveryMode(r.delivery_mode),
                            delivery_location=r.delivery_location,
                            delivery_latitude=r.delivery_latitude,
                            delivery_longitude=r.delivery_longitude,
                            price_basis=PriceBasis(r.price_basis),
                            quoted_price=r.quoted_price,
                            payment_terms=PaymentTerms(r.payment_terms),
                            provenance=EconomicProvenance(
                                source_name="BUYER_REQUIREMENT",
                                status=ProvenanceStatus(r.provenance_status),
                                is_demo=r.is_demo,
                            ),
                        )
                    )
            except Exception as exc:
                raise HTTPException(status_code=503, detail=f"Database error: {exc}") from exc
        else:
            for demo_b in DEMO_BUYERS:
                buyer_map[demo_b["id"]] = demo_b["display_name"]

            for demo_r in DEMO_BUYER_REQUIREMENTS:
                if demo_r["commodity_id"].lower() == supply.commodity_id.lower():
                    candidate_requirements.append(
                        BuyerRequirement(
                            requirement_id=demo_r["id"],
                            buyer_id=demo_r["buyer_id"],
                            commodity_id=demo_r["commodity_id"],
                            variety=demo_r.get("variety"),
                            minimum_quantity_kg=demo_r["minimum_quantity_kg"],
                            maximum_quantity_kg=demo_r["maximum_quantity_kg"],
                            preferred_quality_grade=demo_r["preferred_quality_grade"],
                            acceptable_quality_range=demo_r["acceptable_quality_range"],
                            required_from=demo_r["required_from"],
                            required_until=demo_r["required_until"],
                            delivery_mode=DeliveryMode(demo_r["delivery_mode"]),
                            delivery_location=demo_r.get("delivery_location"),
                            delivery_latitude=demo_r.get("delivery_latitude"),
                            delivery_longitude=demo_r.get("delivery_longitude"),
                            price_basis=PriceBasis(demo_r["price_basis"]),
                            quoted_price=demo_r.get("quoted_price"),
                            payment_terms=PaymentTerms(demo_r["payment_terms"]),
                            provenance=EconomicProvenance(
                                source_name="DEMO_BUYER_REQUIREMENT",
                                status=ProvenanceStatus(demo_r["provenance_status"]),
                                is_demo=demo_r["is_demo"],
                            ),
                        )
                    )

        results: List[CompatibilityResponse] = []
        for req in candidate_requirements:
            eval_res = self.compatibility_engine.match(
                supply=farmer_supply,
                requirement=req,
                reference_date=date(2024, 9, 15) if is_demo else None,
            )

            # Filter or flag if max_distance_km provided
            dist_status = eval_res.distance_status
            is_compatible = eval_res.constraint_status == "COMPATIBLE"
            explanations = list(eval_res.explanations)

            if max_distance_km is not None and eval_res.distance_km is not None:
                if eval_res.distance_km > max_distance_km:
                    dist_status = DistanceStatus.DISTANCE_GEODESIC
                    is_compatible = False
                    explanations.append(
                        f"Distance {eval_res.distance_km:.1f} km exceeds maximum radius of {max_distance_km:.1f} km."
                    )

            overlap_days = 0
            if eval_res.temporal_overlap_status in [
                TemporalOverlapStatus.FULL_OVERLAP,
                TemporalOverlapStatus.PARTIAL_OVERLAP,
            ]:
                start_o = max(farmer_supply.available_from, req.required_from)
                end_o = min(farmer_supply.available_until, req.required_until)
                overlap_days = max(0, (end_o - start_o).days + 1)

            results.append(
                CompatibilityResponse(
                    buyer_id=eval_res.buyer_id,
                    buyer_name=buyer_map.get(eval_res.buyer_id, eval_res.buyer_id),
                    requirement_id=eval_res.requirement_id,
                    commodity_id=farmer_supply.commodity_id,
                    variety_match=eval_res.variety_match,
                    quality_match=eval_res.quality_match,
                    preferred_grade=req.preferred_quality_grade,
                    acceptable_grades=req.acceptable_quality_range,
                    quantity_status=eval_res.quantity_match,
                    compatible_quantity_kg=eval_res.compatible_quantity_kg,
                    unmatched_supply_kg=eval_res.unmatched_supply_kg,
                    temporal_status=eval_res.temporal_overlap_status,
                    overlap_days=overlap_days,
                    distance_status=dist_status,
                    distance_km=eval_res.distance_km,
                    delivery_mode=req.delivery_mode,
                    delivery_location=req.delivery_location,
                    price_basis=req.price_basis,
                    quoted_price=req.quoted_price,
                    payment_terms=req.payment_terms,
                    is_compatible=is_compatible,
                    explanations=explanations,
                    provenance_status=eval_res.provenance.status,
                    is_demo=eval_res.provenance.is_demo,
                )
            )

        compatible_count = sum(1 for m in results if m.is_compatible)
        return MatchingListResponse(
            supply_id=supply.id,
            commodity_id=supply.commodity_id,
            total_supply_kg=supply.quantity_kg,
            matches_evaluated=len(results),
            compatible_matches_count=compatible_count,
            matches=results,
        )

    # =========================================================================
    # 5. DEMAND AGGREGATION & PRICE DISPERSION
    # =========================================================================

    async def get_demand_aggregate(
        self,
        commodity_id: str,
        region: Optional[str] = None,
        data_mode: Optional[str] = None,
    ) -> DemandAggregateResponse:
        """
        Aggregates active buyer demands for a commodity and computes market concentration (HHI).
        """
        is_demo = await self._is_demo_mode(data_mode)
        demands: List[BuyerDemand] = []

        if not is_demo:
            if self.db is None:
                raise HTTPException(status_code=503, detail="Database session required.")
            try:
                stmt = select(BuyerDemandModel).where(
                    BuyerDemandModel.commodity_id == commodity_id.lower(),
                    BuyerDemandModel.demand_status == "ACTIVE",
                )
                if region:
                    stmt = stmt.where(BuyerDemandModel.location.ilike(f"%{region}%"))
                res = await self.db.execute(stmt)
                for d in res.scalars().all():
                    demands.append(
                        BuyerDemand(
                            demand_id=d.id,
                            buyer_id=d.buyer_id,
                            commodity_id=d.commodity_id,
                            quantity_kg=d.quantity_kg,
                            quality_requirement=d.quality_requirement,
                            date_window_start=d.date_window_start,
                            date_window_end=d.date_window_end,
                            location=d.location,
                            variety=d.variety,
                            price_per_kg=d.price_per_kg,
                            price_unit=d.price_unit,
                            demand_type=DemandType(d.demand_type),
                            demand_status=DemandStatus(d.demand_status),
                            provenance=EconomicProvenance(
                                source_name="DATABASE_DEMAND",
                                status=ProvenanceStatus(d.provenance_status),
                                is_demo=d.is_demo,
                            ),
                        )
                    )
            except Exception as exc:
                raise HTTPException(status_code=503, detail=f"Database error: {exc}") from exc
        else:
            for demo_d in DEMO_BUYER_DEMANDS:
                if demo_d["commodity_id"].lower() == commodity_id.lower() and demo_d["demand_status"] == "ACTIVE":
                    if region and region.lower() not in demo_d["location"].lower():
                        continue
                    demands.append(
                        BuyerDemand(
                            demand_id=demo_d["id"],
                            buyer_id=demo_d["buyer_id"],
                            commodity_id=demo_d["commodity_id"],
                            quantity_kg=demo_d["quantity_kg"],
                            quality_requirement=demo_d["quality_requirement"],
                            date_window_start=demo_d["date_window_start"],
                            date_window_end=demo_d["date_window_end"],
                            location=demo_d["location"],
                            variety=demo_d.get("variety"),
                            price_per_kg=demo_d.get("price_per_kg"),
                            price_unit=demo_d.get("price_unit", "INR_PER_KG"),
                            demand_type=DemandType(demo_d["demand_type"]),
                            demand_status=DemandStatus(demo_d["demand_status"]),
                            provenance=EconomicProvenance(
                                source_name="DEMO_DEMAND_SEED",
                                status=ProvenanceStatus(demo_d["provenance_status"]),
                                is_demo=demo_d["is_demo"],
                            ),
                        )
                    )

        agg = self.aggregation_engine.aggregate(
            demands=demands,
            commodity_id=commodity_id.lower(),
            region=region,
        )
        return DemandAggregateResponse(
            commodity_id=agg.commodity_id,
            region=agg.region,
            total_demand_kg=agg.total_demand_kg,
            buyer_count=agg.buyer_count,
            top_buyer_share_pct=agg.top_buyer_share_pct,
            hhi_concentration=agg.hhi_concentration,
            breakdown_by_quality=agg.demand_by_quality,
            breakdown_by_type=agg.demand_by_type,
            provenance_status=agg.provenance.status,
            is_demo=agg.provenance.is_demo,
        )

    async def get_demand_distribution(
        self,
        commodity_id: str,
        region: Optional[str] = None,
        data_mode: Optional[str] = None,
    ) -> DemandDistributionResponse:
        """
        Computes order size distribution statistics across active buyer demands.
        Strictly gates on sample size N >= 3; returns INSUFFICIENT_DATA otherwise.
        """
        is_demo = await self._is_demo_mode(data_mode)
        demands: List[BuyerDemand] = []

        if not is_demo:
            if self.db is None:
                raise HTTPException(status_code=503, detail="Database session required.")
            try:
                stmt = select(BuyerDemandModel).where(
                    BuyerDemandModel.commodity_id == commodity_id.lower(),
                    BuyerDemandModel.demand_status == "ACTIVE",
                )
                if region:
                    stmt = stmt.where(BuyerDemandModel.location.ilike(f"%{region}%"))
                res = await self.db.execute(stmt)
                for d in res.scalars().all():
                    demands.append(
                        BuyerDemand(
                            demand_id=d.id,
                            buyer_id=d.buyer_id,
                            commodity_id=d.commodity_id,
                            quantity_kg=d.quantity_kg,
                            quality_requirement=d.quality_requirement,
                            date_window_start=d.date_window_start,
                            date_window_end=d.date_window_end,
                            location=d.location,
                            variety=d.variety,
                            price_per_kg=d.price_per_kg,
                            price_unit=d.price_unit,
                            demand_type=DemandType(d.demand_type),
                            demand_status=DemandStatus(d.demand_status),
                            provenance=EconomicProvenance(
                                source_name="DATABASE_DEMAND",
                                status=ProvenanceStatus(d.provenance_status),
                                is_demo=d.is_demo,
                            ),
                        )
                    )
            except Exception as exc:
                raise HTTPException(status_code=503, detail=f"Database error: {exc}") from exc
        else:
            for demo_d in DEMO_BUYER_DEMANDS:
                if demo_d["commodity_id"].lower() == commodity_id.lower() and demo_d["demand_status"] == "ACTIVE":
                    if region and region.lower() not in demo_d["location"].lower():
                        continue
                    demands.append(
                        BuyerDemand(
                            demand_id=demo_d["id"],
                            buyer_id=demo_d["buyer_id"],
                            commodity_id=demo_d["commodity_id"],
                            quantity_kg=demo_d["quantity_kg"],
                            quality_requirement=demo_d["quality_requirement"],
                            date_window_start=demo_d["date_window_start"],
                            date_window_end=demo_d["date_window_end"],
                            location=demo_d["location"],
                            variety=demo_d.get("variety"),
                            price_per_kg=demo_d.get("price_per_kg"),
                            price_unit=demo_d.get("price_unit", "INR_PER_KG"),
                            demand_type=DemandType(demo_d["demand_type"]),
                            demand_status=DemandStatus(demo_d["demand_status"]),
                            provenance=EconomicProvenance(
                                source_name="DEMO_DEMAND_SEED",
                                status=ProvenanceStatus(demo_d["provenance_status"]),
                                is_demo=demo_d["is_demo"],
                            ),
                        )
                    )

        dist = self.aggregation_engine.calculate_distribution(
            demands=demands,
            commodity_id=commodity_id.lower(),
            region=region,
        )
        return DemandDistributionResponse(
            commodity_id=dist.commodity_id,
            status=dist.status,
            sample_size=dist.observation_count,
            min_kg=dist.min_kg,
            max_kg=dist.max_kg,
            mean_kg=dist.mean_kg,
            median_kg=dist.median_kg,
            p10_kg=dist.p10_kg,
            p25_kg=dist.p25_kg,
            p50_kg=dist.p50_kg,
            p75_kg=dist.p75_kg,
            p90_kg=dist.p90_kg,
            provenance_status=dist.provenance.status,
            is_demo=dist.provenance.is_demo,
        )

    # =========================================================================
    # 6. DEMO FARMER SUPPLIES
    # =========================================================================

    async def get_sample_supplies(
        self,
        commodity_id: Optional[str] = None,
        data_mode: Optional[str] = None,
    ) -> List[FarmerSupplyRequest]:
        """Provides pre-configured benchmark farmer produce supplies for UI demonstration."""
        supplies: List[FarmerSupplyRequest] = []
        for s in DEMO_FARMER_SUPPLIES:
            if commodity_id and s["commodity_id"].lower() != commodity_id.lower():
                continue
            supplies.append(
                FarmerSupplyRequest(
                    id=s["id"],
                    supply_reference_id=s.get("supply_reference_id"),
                    commodity_id=s["commodity_id"],
                    variety=s.get("variety"),
                    quantity_kg=s["quantity_kg"],
                    quality_grade=s["quality_grade"],
                    available_from=s["available_from"],
                    available_until=s["available_until"],
                    origin_location=s["origin_location"],
                    origin_latitude=s.get("origin_latitude"),
                    origin_longitude=s.get("origin_longitude"),
                    storage_available=s.get("storage_available", False),
                    storage_type=s.get("storage_type"),
                    provenance_status=ProvenanceStatus(s["provenance_status"]),
                    is_demo=s["is_demo"],
                )
            )
        return supplies
