"""
AgriClutch Regional Buyer Demand Aggregation & Concentration Engine.
Aggregates demand volumes across commodities, regions, and quality grades,
and calculates descriptive statistical distributions and market concentration metrics.
SIH26132 — Strengthening Market Linkages and Price Discovery for Farmers.
"""

from collections import defaultdict

import numpy as np

from ml.buyer.contracts import (
    BuyerDemand,
    DemandAggregationResult,
    DemandDistributionResult,
    DistributionStatus,
    EconomicProvenance,
    ProvenanceStatus,
)


class DemandAggregationEngine:
    """
    Computes regional market depth, order size distributions, and market concentration.
    Neutral, descriptive analytics with zero prescriptive ranking.
    """

    @staticmethod
    def aggregate(
        demands: list[BuyerDemand],
        commodity_id: str,
        region: str | None = None,
    ) -> DemandAggregationResult:
        """
        Aggregates active buyer demands for a specified commodity and optional regional filter.
        """
        norm_c = commodity_id.strip().lower()
        norm_r = region.strip().lower() if region else None

        filtered = [
            d for d in demands
            if d.commodity_id.strip().lower() == norm_c
            and (norm_r is None or norm_r in d.location.strip().lower())
        ]

        total_kg = 0.0
        by_buyer: dict[str, float] = defaultdict(float)
        by_quality: dict[str, float] = defaultdict(float)
        by_region: dict[str, float] = defaultdict(float)
        by_time: dict[str, float] = defaultdict(float)
        by_type: dict[str, float] = defaultdict(float)

        all_demo = True
        for d in filtered:
            total_kg += d.quantity_kg
            by_buyer[d.buyer_id] += d.quantity_kg
            by_quality[d.quality_requirement] += d.quantity_kg
            by_region[d.location] += d.quantity_kg

            # Group by ISO year-month for temporal aggregation
            ym = d.date_window_start.strftime("%Y-%m")
            by_time[ym] += d.quantity_kg
            by_type[d.demand_type.value] += d.quantity_kg

            if not d.provenance.is_demo:
                all_demo = False

        buyer_count = len(by_buyer)

        # Market Concentration Metrics
        top_share: float | None = None
        hhi: float | None = None

        if total_kg > 0 and buyer_count > 0:
            shares = [(qty / total_kg) * 100.0 for qty in by_buyer.values()]
            top_share = max(shares)
            # Herfindahl-Hirschman Index: sum of squared percentage market shares
            hhi = sum(s ** 2 for s in shares)

        prov = EconomicProvenance(
            source_name="AGGREGATED_DEMAND_SERIES",
            status=ProvenanceStatus.DEMO if all_demo else ProvenanceStatus.EMPIRICAL,
            is_demo=all_demo,
            description=f"Aggregated from {len(filtered)} buyer demand observations across {buyer_count} distinct buyers.",
        )

        return DemandAggregationResult(
            commodity_id=commodity_id,
            region=region,
            total_demand_kg=total_kg,
            buyer_count=buyer_count,
            demand_by_quality=dict(by_quality),
            demand_by_region=dict(by_region),
            demand_by_time_window=dict(by_time),
            demand_by_type=dict(by_type),
            top_buyer_share_pct=top_share,
            hhi_concentration=hhi,
            provenance=prov,
        )

    @staticmethod
    def calculate_distribution(
        demands: list[BuyerDemand],
        commodity_id: str,
        region: str | None = None,
    ) -> DemandDistributionResult:
        """
        Calculates summary statistics of order sizes with statistical sufficiency gating.
        Enforces N >= 3 requirement; returns INSUFFICIENT_DATA otherwise.
        """
        norm_c = commodity_id.strip().lower()
        norm_r = region.strip().lower() if region else None

        quantities = [
            d.quantity_kg
            for d in demands
            if d.commodity_id.strip().lower() == norm_c
            and (norm_r is None or norm_r in d.location.strip().lower())
        ]

        n = len(quantities)
        if n < 3:
            return DemandDistributionResult(
                commodity_id=commodity_id,
                status=DistributionStatus.INSUFFICIENT_DATA,
                observation_count=n,
                provenance=EconomicProvenance(
                    source_name="DEMAND_DISTRIBUTION",
                    status=ProvenanceStatus.DEMO,
                    is_demo=True,
                    description=f"Insufficient sample size ({n} < 3 observations) to compute reliable order distribution.",
                ),
            )

        arr = np.array(quantities, dtype=np.float64)

        return DemandDistributionResult(
            commodity_id=commodity_id,
            status=DistributionStatus.VALID,
            observation_count=n,
            min_kg=float(np.min(arr)),
            max_kg=float(np.max(arr)),
            mean_kg=float(np.mean(arr)),
            median_kg=float(np.median(arr)),
            p10_kg=float(np.percentile(arr, 10)),
            p25_kg=float(np.percentile(arr, 25)),
            p50_kg=float(np.percentile(arr, 50)),
            p75_kg=float(np.percentile(arr, 75)),
            p90_kg=float(np.percentile(arr, 90)),
            provenance=EconomicProvenance(
                source_name="DEMAND_DISTRIBUTION",
                status=ProvenanceStatus.DEMO,
                is_demo=True,
                description=f"Empirical quantile distribution estimated over {n} validated buyer demand observations.",
            ),
        )
