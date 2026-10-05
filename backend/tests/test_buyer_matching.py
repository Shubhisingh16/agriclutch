"""
Unit Tests for AgriClutch Multi-Dimensional Compatibility Matching Engine.
Verifies commodity, variety, quality, bounded quantity, temporal, and spatial calculations.
Includes strict tests ensuring ZERO recommendation leakage.
SIH26132 — Strengthening Market Linkages and Price Discovery for Farmers.
"""

from datetime import date

import pytest

from ml.buyer.compatibility import (
    CompatibilityEngine,
    calculate_haversine_distance,
)
from ml.buyer.contracts import (
    BuyerRequirement,
    DeliveryMode,
    DistanceStatus,
    FarmerSupply,
    PaymentTerms,
    PriceBasis,
    QuantityMatchStatus,
    TemporalOverlapStatus,
)


@pytest.fixture
def sample_supply() -> FarmerSupply:
    return FarmerSupply(
        supply_id="sup_test",
        commodity_id="tomato",
        variety="Hybrid Red",
        quantity_kg=2500.0,
        quality_grade="GRADE_A",
        available_from=date(2024, 9, 15),
        available_until=date(2024, 9, 22),
        origin_location="Mohali",
        origin_latitude=30.6970,
        origin_longitude=76.6948,
    )


@pytest.fixture
def sample_requirement() -> BuyerRequirement:
    return BuyerRequirement(
        requirement_id="req_test",
        buyer_id="buyer_test",
        commodity_id="tomato",
        variety="Hybrid Red",
        minimum_quantity_kg=500.0,
        maximum_quantity_kg=5000.0,
        preferred_quality_grade="GRADE_A",
        acceptable_quality_range=["GRADE_A", "GRADE_B"],
        required_from=date(2024, 9, 15),
        required_until=date(2024, 9, 25),
        delivery_mode=DeliveryMode.BUYER_PREMISES,
        delivery_location="Chandigarh Sector 26",
        delivery_latitude=30.7333,
        delivery_longitude=76.7794,
        price_basis=PriceBasis.FIXED_QUOTE,
        quoted_price=29.50,
        payment_terms=PaymentTerms.NET_3_DAYS,
    )


def test_haversine_known_coordinates() -> None:
    """Verifies Haversine formula calculation against known geodesic distance."""
    dist, status = calculate_haversine_distance(30.6970, 76.6948, 30.7333, 76.7794)
    assert dist is not None
    assert 7.0 <= dist <= 12.0
    assert status == DistanceStatus.DISTANCE_GEODESIC

    # Same coordinate distance must be zero
    zero_dist, _ = calculate_haversine_distance(30.0, 75.0, 30.0, 75.0)
    assert zero_dist == 0.0


def test_perfect_compatibility(sample_supply: FarmerSupply, sample_requirement: BuyerRequirement) -> None:
    """Verifies evaluation when all constraints are fully satisfied."""
    engine = CompatibilityEngine()
    res = engine.match(sample_supply, sample_requirement, reference_date=date(2024, 9, 15))

    assert res.constraint_status == "COMPATIBLE"
    assert res.commodity_match is True
    assert res.variety_match is True
    assert res.quality_match is True
    assert res.quantity_match == QuantityMatchStatus.PARTIAL_MATCH  # 2500 < 5000 max capacity
    assert res.compatible_quantity_kg == 2500.0
    assert res.unmatched_supply_kg == 0.0
    assert res.temporal_overlap_status == TemporalOverlapStatus.FULL_OVERLAP
    assert res.distance_status == DistanceStatus.DISTANCE_GEODESIC


def test_quality_mismatch(sample_supply: FarmerSupply, sample_requirement: BuyerRequirement) -> None:
    """Verifies rejection when produce grade is not in buyer acceptable list."""
    engine = CompatibilityEngine()
    sample_supply.quality_grade = "GRADE_C"
    sample_requirement.acceptable_quality_range = ["GRADE_A", "GRADE_B"]

    res = engine.match(sample_supply, sample_requirement, reference_date=date(2024, 9, 15))
    assert res.constraint_status == "INCOMPATIBLE"
    assert res.quality_match is False
    assert any("Quality mismatch" in exp for exp in res.explanations)


def test_quantity_below_minimum(sample_supply: FarmerSupply, sample_requirement: BuyerRequirement) -> None:
    """Verifies quantity below minimum capacity fails constraint."""
    engine = CompatibilityEngine()
    sample_supply.quantity_kg = 200.0  # Min is 500.0
    res = engine.match(sample_supply, sample_requirement, reference_date=date(2024, 9, 15))

    assert res.constraint_status == "INCOMPATIBLE"
    assert res.quantity_match == QuantityMatchStatus.INSUFFICIENT_SUPPLY
    assert res.compatible_quantity_kg == 0.0
    assert res.unmatched_supply_kg == 200.0


def test_quantity_exceeds_maximum(sample_supply: FarmerSupply, sample_requirement: BuyerRequirement) -> None:
    """Verifies partial capacity allocation when lot exceeds max buyer capacity."""
    engine = CompatibilityEngine()
    sample_supply.quantity_kg = 8000.0  # Max is 5000.0
    res = engine.match(sample_supply, sample_requirement, reference_date=date(2024, 9, 15))

    assert res.constraint_status == "PARTIALLY_COMPATIBLE"
    assert res.quantity_match == QuantityMatchStatus.PARTIAL_MATCH
    assert res.compatible_quantity_kg == 5000.0
    assert res.unmatched_supply_kg == 3000.0


def test_temporal_overlap_types(sample_supply: FarmerSupply, sample_requirement: BuyerRequirement) -> None:
    """Verifies disjoint non-overlapping temporal windows."""
    engine = CompatibilityEngine()

    sample_supply.available_from = date(2024, 10, 1)
    sample_supply.available_until = date(2024, 10, 10)
    sample_requirement.required_from = date(2024, 9, 15)
    sample_requirement.required_until = date(2024, 9, 25)

    res = engine.match(sample_supply, sample_requirement, reference_date=date(2024, 9, 15))
    assert res.constraint_status == "INCOMPATIBLE"
    assert res.temporal_overlap_status == TemporalOverlapStatus.NO_OVERLAP


def test_zero_recommendation_leakage_in_explanations(
    sample_supply: FarmerSupply, sample_requirement: BuyerRequirement
) -> None:
    """
    CRITICAL SIH26132 GOVERNANCE TEST:
    Ensures that factual compatibility explanations contain ZERO recommendation words,
    ranking hints, or optimization advice.
    """
    forbidden_tokens = [
        "SELL NOW",
        "HOLD PRODUCE",
        "BUY NOW",
        "BEST BUYER",
        "OPTIMAL SELLING PLAN",
        "RECOMMENDED",
        "WINNER",
        "TOP CHOICE",
        "SHOULD SELL",
    ]

    engine = CompatibilityEngine()
    res = engine.match(sample_supply, sample_requirement, reference_date=date(2024, 9, 15))

    for exp in res.explanations:
        upper_exp = exp.upper()
        for token in forbidden_tokens:
            assert token not in upper_exp, f"Forbidden recommendation token '{token}' found in explanation: '{exp}'"
