"""
Unit Tests for AgriClutch Crop Perishability & Shelf-Life Engine.
Verifies exponential decay equations, decoupled physical vs quality loss,
and fail-closed behavior on unsupported commodities.
SIH26132 — Strengthening Market Linkages and Price Discovery for Farmers.
"""

import math

import pytest

from ml.logistics.contracts import ProvenanceStatus, StorageType
from ml.logistics.perishability import PerishabilityEngine


def test_perishability_exponential_equations() -> None:
    # S(t) = exp(-delta * t), F(t) = F0 * exp(-beta * t)
    s_val = PerishabilityEngine.calculate_decay_survival(decay_parameter_delta=0.035, days=7)
    expected_s = math.exp(-0.035 * 7)
    assert math.isclose(s_val, expected_s, rel_tol=1e-5)

    q_val = PerishabilityEngine.calculate_quality_factor(
        initial_quality_factor=0.95, quality_decay_beta=0.050, days=7
    )
    expected_q = 0.95 * math.exp(-0.050 * 7)
    assert math.isclose(q_val, expected_q, rel_tol=1e-5)


def test_perishability_trajectory_ambient_vs_cold() -> None:
    traj_ambient = PerishabilityEngine.calculate_trajectory(
        commodity_id="tomato",
        storage_type=StorageType.AMBIENT,
        initial_quantity_kg=2000.0,
        duration_days=5,
    )
    traj_cold = PerishabilityEngine.calculate_trajectory(
        commodity_id="tomato",
        storage_type=StorageType.COLD,
        initial_quantity_kg=2000.0,
        duration_days=5,
    )

    assert traj_ambient.status == "CALCULATED"
    assert traj_cold.status == "CALCULATED"
    # Cold storage must preserve more quantity and quality
    assert traj_cold.final_quantity_kg > traj_ambient.final_quantity_kg
    assert traj_cold.final_quality_factor > traj_ambient.final_quality_factor
    assert len(traj_ambient.trajectory) == 6  # Day 0 to 5


def test_perishability_unsupported_crop_fail_closed() -> None:
    traj_unknown = PerishabilityEngine.calculate_trajectory(
        commodity_id="avocado",
        storage_type=StorageType.AMBIENT,
        initial_quantity_kg=1000.0,
        duration_days=5,
    )
    assert traj_unknown.status == "LOSS_MODEL_UNAVAILABLE"
    assert traj_unknown.model_spec is None
    assert traj_unknown.final_quantity_kg == 1000.0
    assert traj_unknown.provenance.status == ProvenanceStatus.UNAVAILABLE


def test_perishability_negative_inputs_rejected() -> None:
    with pytest.raises(ValueError, match="Initial quantity must be strictly positive"):
        PerishabilityEngine.calculate_trajectory(
            commodity_id="tomato",
            storage_type=StorageType.AMBIENT,
            initial_quantity_kg=-500.0,
            duration_days=5,
        )

    with pytest.raises(ValueError, match="Duration cannot be negative"):
        PerishabilityEngine.calculate_trajectory(
            commodity_id="tomato",
            storage_type=StorageType.AMBIENT,
            initial_quantity_kg=500.0,
            duration_days=-1,
        )
