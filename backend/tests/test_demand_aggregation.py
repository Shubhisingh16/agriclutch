"""
Unit Tests for AgriClutch Regional Demand Aggregation & Price Dispersion Engine.
Verifies volume aggregation, quality breakdown, HHI market concentration, and N >= 3 distribution gating.
SIH26132 — Strengthening Market Linkages and Price Discovery for Farmers.
"""

from datetime import date
from typing import List

import pytest

from ml.buyer.aggregation import DemandAggregationEngine
from ml.buyer.contracts import (
    BuyerDemand,
    DistributionStatus,
)


@pytest.fixture
def sample_demands() -> List[BuyerDemand]:
    return [
        BuyerDemand(
            demand_id="d1",
            buyer_id="b1",
            commodity_id="tomato",
            variety="Hybrid",
            quantity_kg=3000.0,
            quality_requirement="GRADE_A",
            date_window_start=date(2024, 9, 15),
            date_window_end=date(2024, 9, 22),
            location="Chandigarh",
            price_per_kg=30.0,
        ),
        BuyerDemand(
            demand_id="d2",
            buyer_id="b2",
            commodity_id="tomato",
            variety="Hybrid",
            quantity_kg=5000.0,
            quality_requirement="GRADE_A",
            date_window_start=date(2024, 9, 16),
            date_window_end=date(2024, 9, 25),
            location="Panchkula",
            price_per_kg=32.0,
        ),
        BuyerDemand(
            demand_id="d3",
            buyer_id="b3",
            commodity_id="tomato",
            variety="Desi",
            quantity_kg=2000.0,
            quality_requirement="GRADE_B",
            date_window_start=date(2024, 9, 17),
            date_window_end=date(2024, 9, 30),
            location="Sonipat",
            price_per_kg=28.0,
        ),
    ]


def test_demand_aggregation_totals(sample_demands: List[BuyerDemand]) -> None:
    """Verifies sum of quantities, buyer counts, and breakdown mappings."""
    engine = DemandAggregationEngine()
    agg = engine.aggregate(sample_demands, "tomato")

    assert agg.total_demand_kg == 10000.0
    assert agg.buyer_count == 3
    assert agg.demand_by_quality["GRADE_A"] == 8000.0
    assert agg.demand_by_quality["GRADE_B"] == 2000.0

    # Top buyer is b2 with 5000 / 10000 = 50.0%
    assert agg.top_buyer_share_pct == 50.0


def test_hhi_market_concentration(sample_demands: List[BuyerDemand]) -> None:
    """
    Verifies Herfindahl-Hirschman Index calculation:
    Shares: b1 = 30%, b2 = 50%, b3 = 20%
    HHI = 30^2 + 50^2 + 20^2 = 900 + 2500 + 400 = 3800.0
    """
    engine = DemandAggregationEngine()
    agg = engine.aggregate(sample_demands, "tomato")

    assert agg.hhi_concentration is not None
    assert abs(agg.hhi_concentration - 3800.0) < 1e-4


def test_hhi_monopoly() -> None:
    """Single buyer with 100% share must yield maximum HHI = 10000."""
    engine = DemandAggregationEngine()
    demands = [
        BuyerDemand(
            demand_id="d1",
            buyer_id="b1",
            commodity_id="tomato",
            quantity_kg=10000.0,
            quality_requirement="GRADE_A",
            date_window_start=date(2024, 9, 15),
            date_window_end=date(2024, 9, 22),
            location="Chandigarh",
        )
    ]
    agg = engine.aggregate(demands, "tomato")
    assert agg.hhi_concentration == 10000.0


def test_price_distribution_gating_n_less_than_3() -> None:
    """Demands with fewer than 3 observations must fail closed with INSUFFICIENT_DATA."""
    engine = DemandAggregationEngine()
    demands = [
        BuyerDemand(
            demand_id="d1",
            buyer_id="b1",
            commodity_id="tomato",
            quantity_kg=1000.0,
            quality_requirement="GRADE_A",
            date_window_start=date(2024, 9, 15),
            date_window_end=date(2024, 9, 22),
            location="Chandigarh",
            price_per_kg=30.0,
        ),
        BuyerDemand(
            demand_id="d2",
            buyer_id="b2",
            commodity_id="tomato",
            quantity_kg=2000.0,
            quality_requirement="GRADE_A",
            date_window_start=date(2024, 9, 15),
            date_window_end=date(2024, 9, 22),
            location="Chandigarh",
            price_per_kg=32.0,
        ),
    ]
    dist = engine.calculate_distribution(demands, "tomato")

    assert dist.status == DistributionStatus.INSUFFICIENT_DATA
    assert dist.observation_count == 2
    assert dist.mean_kg is None
    assert dist.median_kg is None


def test_price_distribution_sufficient_sample(sample_demands: List[BuyerDemand]) -> None:
    """Demands with N >= 3 must return accurate empirical percentiles."""
    engine = DemandAggregationEngine()
    dist = engine.calculate_distribution(sample_demands, "tomato")

    assert dist.status == DistributionStatus.VALID
    assert dist.observation_count == 3
    assert dist.min_kg == 2000.0
    assert dist.max_kg == 5000.0
    assert dist.median_kg == 3000.0
    assert dist.mean_kg == pytest.approx(3333.33, rel=1e-2)
