"""
Unit Tests for AgriClutch Logistics Cost Engine.
Verifies additive cost decomposition, rate calculations, input validations,
and provenance integrity.
SIH26132 — Strengthening Market Linkages and Price Discovery for Farmers.
"""

import math

import pytest

from ml.logistics.contracts import (
    EconomicStatus,
    TransportModeSpec,
)
from ml.logistics.costs import LogisticsCostEngine


@pytest.fixture
def standard_lcv() -> TransportModeSpec:
    return TransportModeSpec(
        mode_id="DEMO_LCV_TATA_407",
        display_name="Light Commercial Vehicle (LCV)",
        vehicle_type="LCV",
        capacity_kg=2500.0,
        base_dispatch_fee=800.0,
        cost_per_km=25.0,
        cost_per_km_tonne=10.0,
        speed_kmh=45.0,
    )


def test_logistics_cost_decomposition_additive(standard_lcv: TransportModeSpec) -> None:
    # 2500 kg = 25 quintals = 2.5 tonnes. Distance = 40 km.
    # Base = 800
    # Transport (Distance) = 40 * 25 = 1000
    # Loading = 25 * 12 = 300
    # Unloading = 25 * 10 = 250
    # Extra Handling = 100
    # Total = 800 + 1000 + 300 + 250 + 100 = 2450
    breakdown = LogisticsCostEngine.calculate_cost_breakdown(
        transport_mode=standard_lcv,
        quantity_kg=2500.0,
        distance_km=40.0,
        loading_fee_per_quintal=12.0,
        unloading_fee_per_quintal=10.0,
        extra_handling_fee=100.0,
        is_demo=True,
    )

    assert math.isclose(breakdown.transport_cost, 1800.0, rel_tol=1e-3)
    assert math.isclose(breakdown.loading_cost, 300.0, rel_tol=1e-3)
    assert math.isclose(breakdown.unloading_cost, 250.0, rel_tol=1e-3)
    assert math.isclose(breakdown.handling_cost, 100.0, rel_tol=1e-3)
    assert math.isclose(breakdown.total_cost, 2450.0, rel_tol=1e-3)
    assert breakdown.economic_status == EconomicStatus.DEMO_ASSUMPTION


def test_logistics_cost_negative_inputs_rejected(standard_lcv: TransportModeSpec) -> None:
    with pytest.raises(ValueError, match="Quantity must be strictly positive"):
        LogisticsCostEngine.calculate_cost_breakdown(
            transport_mode=standard_lcv,
            quantity_kg=-500.0,
            distance_km=10.0,
        )

    with pytest.raises(ValueError, match="Distance cannot be negative"):
        LogisticsCostEngine.calculate_cost_breakdown(
            transport_mode=standard_lcv,
            quantity_kg=500.0,
            distance_km=-10.0,
        )


def test_logistics_cost_missing_distance_incomplete(standard_lcv: TransportModeSpec) -> None:
    breakdown = LogisticsCostEngine.calculate_cost_breakdown(
        transport_mode=standard_lcv,
        quantity_kg=1000.0,
        distance_km=None,
    )
    assert breakdown.economic_status == EconomicStatus.INCOMPLETE
    assert any(item.component_name == "HAULAGE_DISTANCE_FEE" and item.amount == 0.0 for item in breakdown.items)
