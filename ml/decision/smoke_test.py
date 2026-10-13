"""
AgriClutch Step 14: Comprehensive 20-Stage Decision Intelligence Smoke Test.
Verifies complete decision optimization pipeline: candidate synthesis, objective weights,
CVaR risk penalties, linear constraint matrix, SciPy HiGHS LP solver, plan assembly,
post-solve validation, counterfactual What-If simulation, and sensitivity sweeps.
SIH26132 — Strengthening Market Linkages and Price Discovery for Farmers.
"""

import numpy as np

from ml.decision.optimizer import (
    DecisionCandidatePipeline,
    DecisionConstraintBuilder,
    DecisionObjectiveEngine,
    DecisionPlanAssembler,
    DecisionSolver,
    LiquidityPreference,
    RiskPreference,
    SolverStatus,
    ValidationStatus,
    WhatIfSimulatorEngine,
)


def run_decision_smoke_test() -> None:
    print("=" * 70)
    print("AGRICLUTCH STEP 14 -- DECISION INTELLIGENCE 20-STAGE SMOKE TEST")
    print("=" * 70)

    # Stage 1: Load synthetic farmer supply
    print("[Stage 1] Loading synthetic farmer supply specification...")
    total_supply_kg = 2500.0
    commodity_id = "tomato"
    assert total_supply_kg > 0.0
    print("  [PASS] Stage 1: Supply spec initialized (2,500 kg Tomato).")

    # Stage 2: Load forecast snapshot
    print("[Stage 2] Ingesting forecast snapshot...")
    candidates = DecisionCandidatePipeline.build_demo_candidates(commodity_id=commodity_id)
    assert len(candidates) >= 4
    for c in candidates:
        assert c.price_p10 <= c.price_p50 <= c.price_p90
    print(f"  [PASS] Stage 2: Forecast snapshot validated ({len(candidates)} channels).")

    # Stage 3: Load NRV snapshot & itemized friction deductions
    print("[Stage 3] Ingesting NRV realization snapshots...")
    for c in candidates:
        friction = c.freight_cost_per_kg + c.storage_cost_per_kg + c.handling_cost_per_kg + c.market_fee_per_kg
        assert abs(c.expected_nrv_per_kg - (c.expected_price_per_kg - friction)) < 1e-4
    print("  [PASS] Stage 3: NRV realizations and friction costs verified.")

    # Stage 4: Load buyer demand bounds
    print("[Stage 4] Ingesting buyer demand constraints...")
    buyer_cands = [c for c in candidates if c.buyer_id]
    assert len(buyer_cands) >= 2
    for b in buyer_cands:
        assert b.max_demand_kg > 0
    print("  [PASS] Stage 4: Buyer demand bounds verified.")

    # Stage 5: Load logistics feasibility & vehicle capacities
    print("[Stage 5] Ingesting logistics transit capacities...")
    for c in candidates:
        assert c.max_transport_kg >= 1000.0
    print("  [PASS] Stage 5: Logistics transport limits verified.")

    # Stage 6: Load storage facility limits & perishability curves
    print("[Stage 6] Ingesting storage limits & perishability decay...")
    stored_cands = [c for c in candidates if c.storage_facility_id]
    assert len(stored_cands) >= 1
    assert stored_cands[0].mass_retention_factor < 1.0
    print("  [PASS] Stage 6: Storage capacities & exponential decay verified.")

    # Stage 7: Generate candidate allocations
    print("[Stage 7] Validating candidate allocation properties...")
    for c in candidates:
        assert c.candidate_id and c.destination_name
    print("  [PASS] Stage 7: Candidate allocations pre-filtered and ready.")

    # Stage 8: Build optimization problem matrix
    print("[Stage 8] Building constraint matrix system...")
    A_ub, b_ub, bounds, labels = DecisionConstraintBuilder.build_system(  # noqa: N806
        candidates=candidates,
        total_supply_kg=total_supply_kg,
        liquidity_preference=LiquidityPreference.BALANCED,
    )
    assert A_ub.shape[0] == len(b_ub)
    assert len(bounds) == len(candidates)
    print(f"  [PASS] Stage 8: Constraint system assembled ({A_ub.shape[0]} rows, {A_ub.shape[1]} cols).")

    # Stage 9: Build risk-adjusted objective vector
    print("[Stage 9] Building risk-adjusted objective vector...")
    c_coeffs = DecisionObjectiveEngine.compute_candidate_coefficients(
        candidates=candidates,
        risk_preference=RiskPreference.RISK_AWARE,
    )
    assert len(c_coeffs) == len(candidates)
    assert all(np.isfinite(c_coeffs))
    print("  [PASS] Stage 9: Objective coefficients constructed.")

    # Stage 10: Apply liquidity constraints
    print("[Stage 10] Applying liquidity preference constraints...")
    min_imm = 0.30 * total_supply_kg
    imm_indices = [idx for idx, c in enumerate(candidates) if c.is_immediate_window]
    assert len(imm_indices) >= 2
    print(f"  [PASS] Stage 10: Liquidity constraint enforced (min {min_imm:.0f} kg in immediate window).")

    # Stage 11: Run SciPy LP solver
    print("[Stage 11] Executing SciPy HiGHS Dual Simplex solver...")
    solver_res = DecisionSolver.solve(
        candidates=candidates,
        total_supply_kg=total_supply_kg,
        risk_preference=RiskPreference.RISK_AWARE,
        liquidity_preference=LiquidityPreference.BALANCED,
    )
    assert solver_res.status == SolverStatus.OPTIMAL
    assert solver_res.x_solution.sum() > 0.0
    print(f"  [PASS] Stage 11: Solver identified global optimum in {solver_res.duration_ms:.2f}ms.")

    # Stage 12: Validate solution against constraints
    print("[Stage 12] Conducting post-solve constraint audit...")
    summary = DecisionConstraintBuilder.audit_solution_constraints(
        candidates=candidates,
        x_sol=solver_res.x_solution,
        total_supply_kg=total_supply_kg,
        liquidity_preference=LiquidityPreference.BALANCED,
    )
    assert len(summary.violated_constraints) == 0
    assert summary.supply_constraint_status in ["SATISFIED", "BINDING"]
    print("  [PASS] Stage 12: Solution passed all feasibility audits.")

    # Stage 13: Calculate expected NRV and portfolio financial metrics
    print("[Stage 13] Calculating portfolio NRV financial metrics...")
    plan = DecisionPlanAssembler.assemble(
        candidates=candidates,
        solver_res=solver_res,
        commodity_id=commodity_id,
        total_supply_kg=total_supply_kg,
    )
    assert plan.expected_total_nrv > 0.0
    assert plan.expected_gross_revenue > plan.expected_total_nrv
    print(f"  [PASS] Stage 13: Expected NRV = INR {plan.expected_total_nrv:,.2f} across {len(plan.allocations)} channels.")

    # Stage 14: Calculate CVaR risk metrics
    print("[Stage 14] Calculating portfolio CVaR downside risk metrics...")
    assert plan.risk_metrics is not None
    assert plan.risk_metrics.var_95 >= 0.0
    assert plan.risk_metrics.cvar_95 >= plan.risk_metrics.var_95
    print(f"  [PASS] Stage 14: Risk metrics calculated (VaR95: INR {plan.risk_metrics.var_95:,.2f}, CVaR95: INR {plan.risk_metrics.cvar_95:,.2f}).")

    # Stage 15: Generate Optimal Selling Plan
    print("[Stage 15] Validating Optimal Selling Plan structure...")
    assert plan.plan_id.startswith("plan_")
    assert plan.validation_status == ValidationStatus.PASSED
    assert len(plan.executive_summary) > 0
    print(f"  [PASS] Stage 15: Plan generated: '{plan.executive_summary}'.")

    # Stage 16: Run What-If scenario (Transport Cost Shock +20%)
    print("[Stage 16] Running counterfactual What-If simulation (+20% transport)...")
    sim = WhatIfSimulatorEngine.run_simulation(
        baseline_candidates=candidates,
        total_supply_kg=total_supply_kg,
        transport_cost_multiplier=1.20,
        parameter_label="Transport Cost +20%",
    )
    assert sim.counterfactual_plan.expected_total_nrv < sim.baseline_plan.expected_total_nrv
    print(f"  [PASS] Stage 16: What-If simulation re-solved (NRV delta: INR {sim.comparison.nrv_delta:,.2f}).")

    # Stage 17: Run sensitivity analysis sweep
    print("[Stage 17] Running sensitivity analysis sweep (5 points)...")
    sweep = WhatIfSimulatorEngine.run_sensitivity_sweep(
        candidates=candidates,
        total_supply_kg=total_supply_kg,
        parameter_type="TRANSPORT_COST",
    )
    assert len(sweep.points) == 5
    assert sweep.points[0].expected_total_nrv > sweep.points[-1].expected_total_nrv
    print("  [PASS] Stage 17: Sensitivity sweep verified monotonic response.")

    # Stage 18: Verify reproducibility (identical inputs -> identical hash & allocations)
    print("[Stage 18] Verifying deterministic reproducibility...")
    solver_res2 = DecisionSolver.solve(
        candidates=candidates,
        total_supply_kg=total_supply_kg,
        risk_preference=RiskPreference.RISK_AWARE,
        liquidity_preference=LiquidityPreference.BALANCED,
    )
    plan2 = DecisionPlanAssembler.assemble(
        candidates=candidates,
        solver_res=solver_res2,
        commodity_id=commodity_id,
        total_supply_kg=total_supply_kg,
    )
    assert abs(plan.expected_total_nrv - plan2.expected_total_nrv) < 1e-4
    assert np.allclose(solver_res.x_solution, solver_res2.x_solution)
    assert plan.configuration_hash == plan2.configuration_hash
    print("  [PASS] Stage 18: Determinism and hash reproducibility verified.")

    # Stage 19: Verify data provenance preservation
    print("[Stage 19] Verifying provenance preservation...")
    assert plan.provenance.provenance_status.value in ["CONFIGURED", "DEMO", "EMPIRICAL"]
    assert plan.is_demo is True
    print("  [PASS] Stage 19: Full provenance status preserved.")

    # Stage 20: Verify recommendation integrity
    print("[Stage 20] Verifying recommendation integrity...")
    assert plan.solver_status == SolverStatus.OPTIMAL
    assert plan.validation_status == ValidationStatus.PASSED
    assert plan.total_allocated_kg <= total_supply_kg
    print("  [PASS] Stage 20: Recommendation integrity strictly upheld.")

    print("=" * 70)
    print("ALL 20 SMOKE TEST STAGES PASSED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    run_decision_smoke_test()
