"""
AgriClutch Step 14: Unit and Regression Tests for Decision Optimization Engine.
Tests objective formulations, supply & demand constraints, SciPy LP solver,
plan validation, counterfactual What-If simulation, and sensitivity analysis.
SIH26132 — Strengthening Market Linkages and Price Discovery for Farmers.
"""

from typing import Any

import numpy as np
import pytest

from ml.decision.optimizer import (
    DecisionCandidatePipeline,
    DecisionObjectiveEngine,
    DecisionPlanAssembler,
    DecisionSolver,
    LiquidityPreference,
    RiskPreference,
    SolverStatus,
    ValidationStatus,
    WhatIfSimulatorEngine,
)


@pytest.fixture
def tomato_candidates() -> list[Any]:
    return DecisionCandidatePipeline.build_demo_candidates(commodity_id="tomato")


def test_decision_objective_risk_weights() -> None:
    assert DecisionObjectiveEngine.get_risk_weight(RiskPreference.RISK_NEUTRAL) == 0.0
    assert DecisionObjectiveEngine.get_risk_weight(RiskPreference.RISK_AWARE) == 0.5
    assert DecisionObjectiveEngine.get_risk_weight(RiskPreference.RISK_AVERSE) == 1.0


def test_decision_objective_coefficients(tomato_candidates: list[Any]) -> None:
    c_neutral = DecisionObjectiveEngine.compute_candidate_coefficients(
        tomato_candidates, RiskPreference.RISK_NEUTRAL
    )
    c_averse = DecisionObjectiveEngine.compute_candidate_coefficients(
        tomato_candidates, RiskPreference.RISK_AVERSE
    )
    # Risk averse coefficients should be strictly less than or equal to risk neutral
    assert np.all(c_averse <= c_neutral + 1e-6)


def test_supply_constraint_conservation(tomato_candidates: list[Any]) -> None:
    total_supply = 3000.0
    solver_res = DecisionSolver.solve(
        candidates=tomato_candidates,
        total_supply_kg=total_supply,
        risk_preference=RiskPreference.RISK_AWARE,
        liquidity_preference=LiquidityPreference.BALANCED,
    )
    assert solver_res.status == SolverStatus.OPTIMAL
    allocated = float(np.sum(solver_res.x_solution))
    assert allocated <= total_supply + 1e-4


def test_liquidity_immediate_constraint(tomato_candidates: list[Any]) -> None:
    total_supply = 2000.0
    # IMMEDIATE preference demands >= 60% in immediate window (Day 0-1)
    solver_res = DecisionSolver.solve(
        candidates=tomato_candidates,
        total_supply_kg=total_supply,
        liquidity_preference=LiquidityPreference.IMMEDIATE,
    )
    assert solver_res.status == SolverStatus.OPTIMAL
    imm_qty = sum(
        float(solver_res.x_solution[idx])
        for idx, c in enumerate(tomato_candidates)
        if c.is_immediate_window
    )
    assert imm_qty >= (0.60 * total_supply) - 1e-4


def test_buyer_demand_limits(tomato_candidates: list[Any]) -> None:
    total_supply = 10000.0
    solver_res = DecisionSolver.solve(
        candidates=tomato_candidates,
        total_supply_kg=total_supply,
    )
    assert solver_res.status == SolverStatus.OPTIMAL

    # Check that each buyer allocation respects max demand
    for idx, c in enumerate(tomato_candidates):
        if c.buyer_id:
            alloc_qty = float(solver_res.x_solution[idx])
            assert alloc_qty <= c.max_demand_kg + 1e-4


def test_plan_assembly_and_validation(tomato_candidates: list[Any]) -> None:
    total_supply = 2500.0
    solver_res = DecisionSolver.solve(
        candidates=tomato_candidates,
        total_supply_kg=total_supply,
    )
    plan = DecisionPlanAssembler.assemble(
        candidates=tomato_candidates,
        solver_res=solver_res,
        commodity_id="tomato",
        total_supply_kg=total_supply,
    )
    assert plan.validation_status == ValidationStatus.PASSED
    assert plan.total_allocated_kg > 0.0
    assert plan.expected_total_nrv > 0.0
    assert len(plan.allocations) > 0
    assert plan.constraint_summary is not None
    assert len(plan.constraint_summary.violated_constraints) == 0


def test_what_if_transport_cost_sensitivity(tomato_candidates: list[Any]) -> None:
    total_supply = 2500.0
    sim = WhatIfSimulatorEngine.run_simulation(
        baseline_candidates=tomato_candidates,
        total_supply_kg=total_supply,
        transport_cost_multiplier=1.50,  # 50% increase in transport cost
    )
    # Higher transport cost must reduce or maintain net realizable value
    assert sim.counterfactual_plan.expected_total_nrv <= sim.baseline_plan.expected_total_nrv
    assert sim.comparison.nrv_delta <= 0.0


def test_sensitivity_sweep_sweep_range(tomato_candidates: list[Any]) -> None:
    total_supply = 2000.0
    sweep = WhatIfSimulatorEngine.run_sensitivity_sweep(
        candidates=tomato_candidates,
        total_supply_kg=total_supply,
        parameter_type="PRICE_SHOCK",
        sweep_range=[0.8, 1.0, 1.2],
    )
    assert len(sweep.points) == 3
    # With higher price shock multipliers, NRV must strictly increase
    assert sweep.points[0].expected_total_nrv < sweep.points[1].expected_total_nrv < sweep.points[2].expected_total_nrv


def test_solver_determinism(tomato_candidates: list[Any]) -> None:
    total_supply = 2500.0
    res1 = DecisionSolver.solve(tomato_candidates, total_supply)
    res2 = DecisionSolver.solve(tomato_candidates, total_supply)
    assert np.allclose(res1.x_solution, res2.x_solution)
    assert abs(res1.objective_value - res2.objective_value) < 1e-6


def test_risk_metrics_honest_terminology_and_provenance(tomato_candidates: list[Any]) -> None:
    total_supply = 2500.0
    solver_res = DecisionSolver.solve(tomato_candidates, total_supply)
    plan = DecisionPlanAssembler.assemble(
        candidates=tomato_candidates,
        solver_res=solver_res,
        commodity_id="tomato",
        total_supply_kg=total_supply,
    )
    risk = plan.risk_metrics
    assert risk is not None
    # 1. Honest terminology assertions
    assert hasattr(risk, "portfolio_downside_spread")
    assert hasattr(risk, "configured_tail_stress_estimate")
    assert hasattr(risk, "tail_stress_multiplier")
    assert hasattr(risk, "tail_stress_provenance")
    assert risk.tail_stress_multiplier == 1.25
    assert risk.confidence_level == 0.90
    assert risk.tail_stress_provenance.value == "CONFIGURED"

    # 2. Mathematical relationship
    expected_spread = max(0.0, risk.p50_total_nrv - risk.p10_total_nrv)
    assert abs(risk.portfolio_downside_spread - expected_spread) < 1e-4
    assert abs(risk.configured_tail_stress_estimate - expected_spread * 1.25) < 1e-4

    # 3. Backward-compatibility properties
    assert abs(risk.var_95 - risk.portfolio_downside_spread) < 1e-6
    assert abs(risk.cvar_95 - risk.configured_tail_stress_estimate) < 1e-6

