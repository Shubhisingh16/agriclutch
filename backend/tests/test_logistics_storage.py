"""
Unit Tests for AgriClutch Storage Feasibility Engine.
Verifies capacity allocations, duration horizon bounds, holding fees,
and partial capacity partitioning.
SIH26132 — Strengthening Market Linkages and Price Discovery for Farmers.
"""

import math

import pytest

from ml.logistics.contracts import (
    FeasibilityStatus,
    StorageFacility,
    StorageType,
)
from ml.logistics.storage import StorageEngine


@pytest.fixture
def sample_facility() -> StorageFacility:
    return StorageFacility(
        facility_id="DEMO_COLD_STORAGE_NORTH",
        name="Demo Northern Cold Chain Terminal",
        storage_type=StorageType.COLD,
        location="Zirakpur Logistics Park",
        capacity_kg=100000.0,
        available_capacity_kg=20000.0,
        cost_per_kg_day=0.20,
        min_duration_days=3,
        max_duration_days=60,
    )


def test_storage_full_capacity_available(sample_facility: StorageFacility) -> None:
    res = StorageEngine.evaluate_storage(
        facility=sample_facility,
        requested_quantity_kg=10000.0,
        requested_duration_days=10,
    )
    assert res.status == FeasibilityStatus.FEASIBLE
    assert res.stored_quantity_kg == 10000.0
    assert res.unstored_quantity_kg == 0.0
    assert math.isclose(res.storage_cost, 10000.0 * 10 * 0.20, rel_tol=1e-3)


def test_storage_partial_capacity_allocation(sample_facility: StorageFacility) -> None:
    # Requested 25,000 kg, but only 20,000 kg available
    res = StorageEngine.evaluate_storage(
        facility=sample_facility,
        requested_quantity_kg=25000.0,
        requested_duration_days=14,
    )
    assert res.status == FeasibilityStatus.PARTIALLY_FEASIBLE
    assert res.stored_quantity_kg == 20000.0
    assert res.unstored_quantity_kg == 5000.0
    assert math.isclose(res.storage_cost, 20000.0 * 14 * 0.20, rel_tol=1e-3)
    assert any("shortfall" in w or "cannot be stored" in w for w in res.warnings)


def test_storage_duration_bounds(sample_facility: StorageFacility) -> None:
    # Exceeding maximum duration (60 days)
    res_over = StorageEngine.evaluate_storage(
        facility=sample_facility,
        requested_quantity_kg=5000.0,
        requested_duration_days=65,
    )
    assert res_over.status == FeasibilityStatus.INFEASIBLE
    assert any("exceeds facility maximum" in w for w in res_over.warnings)

    # Below minimum duration (3 days)
    res_under = StorageEngine.evaluate_storage(
        facility=sample_facility,
        requested_quantity_kg=5000.0,
        requested_duration_days=1,
    )
    assert any("is below facility minimum" in w for w in res_under.warnings)


def test_storage_negative_inputs_rejected(sample_facility: StorageFacility) -> None:
    with pytest.raises(ValueError, match="must be strictly positive"):
        StorageEngine.evaluate_storage(
            facility=sample_facility,
            requested_quantity_kg=-100.0,
            requested_duration_days=5,
        )

    with pytest.raises(ValueError, match="cannot be negative"):
        StorageEngine.evaluate_storage(
            facility=sample_facility,
            requested_quantity_kg=100.0,
            requested_duration_days=-1,
        )
