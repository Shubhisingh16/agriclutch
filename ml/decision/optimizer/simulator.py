"""
AgriClutch Step 14: Counterfactual What-If Simulator & Sensitivity Engine.
Allows dynamic perturbation of parameters (transport cost, storage duration, demand, risk, liquidity)
and reruns the mathematical solver deterministically to contrast Baseline vs Counterfactual.
SIH26132 — Strengthening Market Linkages and Price Discovery for Farmers.
"""

import copy
from typing import List, Optional

from ml.decision.optimizer.contracts import (
    AllocationCandidate,
    CounterfactualDelta,
    LiquidityPreference,
    RiskPreference,
    SensitivityPoint,
    SensitivitySweepResult,
    WhatIfSimulationResult,
)
from ml.decision.optimizer.solution import DecisionPlanAssembler
from ml.decision.optimizer.solver import DecisionSolver


class WhatIfSimulatorEngine:
    """
    Reruns the mathematical optimization model under counterfactual parameter shifts.
    Never synthesizes or extrapolates fake outcomes: every scenario runs through SciPy LP.
    """

    @classmethod
    def run_simulation(
        cls,
        baseline_candidates: List[AllocationCandidate],
        total_supply_kg: float,
        commodity_id: str = "tomato",
        variety: str = "Standard",
        quality_grade: str = "GRADE_A",
        decision_horizon_days: int = 7,
        baseline_risk: RiskPreference = RiskPreference.RISK_AWARE,
        baseline_liquidity: LiquidityPreference = LiquidityPreference.BALANCED,
        # Counterfactual override options
        cf_supply_kg: Optional[float] = None,
        cf_risk: Optional[RiskPreference] = None,
        cf_liquidity: Optional[LiquidityPreference] = None,
        transport_cost_multiplier: float = 1.0,
        storage_cost_multiplier: float = 1.0,
        buyer_demand_multiplier: float = 1.0,
        price_shock_multiplier: float = 1.0,
        additional_storage_days: int = 0,
        parameter_label: str = "Multi-Parameter What-If Scenario",
    ) -> WhatIfSimulationResult:
        """
        Executes baseline vs counterfactual solve comparison.
        """
        # 1. Solve Baseline
        base_solver = DecisionSolver.solve(
            candidates=baseline_candidates,
            total_supply_kg=total_supply_kg,
            risk_preference=baseline_risk,
            liquidity_preference=baseline_liquidity,
        )
        baseline_plan = DecisionPlanAssembler.assemble(
            candidates=baseline_candidates,
            solver_res=base_solver,
            commodity_id=commodity_id,
            total_supply_kg=total_supply_kg,
            variety=variety,
            quality_grade=quality_grade,
            decision_horizon_days=decision_horizon_days,
            risk_preference=baseline_risk,
            liquidity_preference=baseline_liquidity,
            input_snapshot_id="snap_baseline",
        )

        # 2. Build Counterfactual Candidates
        cf_candidates: List[AllocationCandidate] = []
        for c in baseline_candidates:
            c_copy = copy.deepcopy(c)
            # Apply multipliers
            c_copy.freight_cost_per_kg *= transport_cost_multiplier
            c_copy.storage_cost_per_kg *= storage_cost_multiplier
            c_copy.max_demand_kg *= buyer_demand_multiplier
            c_copy.expected_price_per_kg *= price_shock_multiplier
            c_copy.price_p10 *= price_shock_multiplier
            c_copy.price_p50 *= price_shock_multiplier
            c_copy.price_p90 *= price_shock_multiplier

            # Recompute net NRV per kg
            total_friction = (
                c_copy.freight_cost_per_kg
                + c_copy.storage_cost_per_kg
                + c_copy.handling_cost_per_kg
                + c_copy.market_fee_per_kg
            )
            c_copy.expected_nrv_per_kg = c_copy.expected_price_per_kg - total_friction
            c_copy.nrv_p10 = c_copy.price_p10 - total_friction
            c_copy.nrv_p50 = c_copy.price_p50 - total_friction
            c_copy.nrv_p90 = c_copy.price_p90 - total_friction

            if additional_storage_days != 0 and c_copy.storage_facility_id:
                c_copy.sale_day_offset += additional_storage_days
                # Slightly adjust decay factor
                c_copy.mass_retention_factor = max(0.5, c_copy.mass_retention_factor - 0.01 * additional_storage_days)

            cf_candidates.append(c_copy)

        target_supply = cf_supply_kg if cf_supply_kg is not None else total_supply_kg
        target_risk = cf_risk if cf_risk is not None else baseline_risk
        target_liquidity = cf_liquidity if cf_liquidity is not None else baseline_liquidity

        # 3. Solve Counterfactual
        cf_solver = DecisionSolver.solve(
            candidates=cf_candidates,
            total_supply_kg=target_supply,
            risk_preference=target_risk,
            liquidity_preference=target_liquidity,
        )
        cf_plan = DecisionPlanAssembler.assemble(
            candidates=cf_candidates,
            solver_res=cf_solver,
            commodity_id=commodity_id,
            total_supply_kg=target_supply,
            variety=variety,
            quality_grade=quality_grade,
            decision_horizon_days=decision_horizon_days,
            risk_preference=target_risk,
            liquidity_preference=target_liquidity,
            input_snapshot_id="snap_counterfactual",
        )

        # 4. Compute Comparison Delta
        nrv_delta = cf_plan.expected_total_nrv - baseline_plan.expected_total_nrv
        pct_change = (nrv_delta / baseline_plan.expected_total_nrv * 100.0) if baseline_plan.expected_total_nrv > 0 else 0.0
        cvar_base = baseline_plan.risk_metrics.cvar_95 if baseline_plan.risk_metrics else 0.0
        cvar_cf = cf_plan.risk_metrics.cvar_95 if cf_plan.risk_metrics else 0.0
        cvar_delta = cvar_cf - cvar_base
        alloc_delta = cf_plan.total_allocated_kg - baseline_plan.total_allocated_kg

        shift_desc = f"Allocated: {baseline_plan.total_allocated_kg:,.0f} kg -> {cf_plan.total_allocated_kg:,.0f} kg."
        if cf_plan.allocations and baseline_plan.allocations:
            shift_desc += f" Dominant channel: {cf_plan.allocations[0].destination_name} ({cf_plan.allocations[0].allocation_percentage:.0f}%)."

        delta = CounterfactualDelta(
            parameter_changed=parameter_label,
            baseline_value=f"Base (Supply: {total_supply_kg}kg, Risk: {baseline_risk.value})",
            counterfactual_value=f"CF (Supply: {target_supply}kg, Risk: {target_risk.value})",
            baseline_nrv=baseline_plan.expected_total_nrv,
            counterfactual_nrv=cf_plan.expected_total_nrv,
            nrv_delta=nrv_delta,
            nrv_percentage_change=pct_change,
            baseline_allocated_kg=baseline_plan.total_allocated_kg,
            counterfactual_allocated_kg=cf_plan.total_allocated_kg,
            allocation_shift_summary=shift_desc,
            baseline_input_hash=baseline_plan.input_hash or baseline_plan.configuration_hash,
            counterfactual_input_hash=cf_plan.input_hash or cf_plan.configuration_hash,
            baseline_solver_status=baseline_plan.solver_status,
            new_solver_status=cf_plan.solver_status,
            feasibility_changed=(baseline_plan.solver_status != cf_plan.solver_status),
            cvar_delta=cvar_delta,
            allocation_delta_kg=alloc_delta,
        )

        return WhatIfSimulationResult(
            baseline_plan=baseline_plan,
            counterfactual_plan=cf_plan,
            comparison=delta,
            is_demo=True,
        )

    @classmethod
    def run_sensitivity_sweep(
        cls,
        candidates: List[AllocationCandidate],
        total_supply_kg: float,
        parameter_type: str,  # "TRANSPORT_COST", "BUYER_DEMAND", "PRICE_SHOCK"
        sweep_range: Optional[List[float]] = None,
        commodity_id: str = "tomato",
        risk_preference: RiskPreference = RiskPreference.RISK_AWARE,
        liquidity_preference: LiquidityPreference = LiquidityPreference.BALANCED,
    ) -> SensitivitySweepResult:
        """
        Evaluates a structured multi-point sensitivity curve by sweeping a parameter.
        """
        if sweep_range is None:
            # Default multipliers from -30% to +30%
            sweep_range = [0.70, 0.85, 1.00, 1.15, 1.30]

        points: List[SensitivityPoint] = []
        unit = "multiplier"
        baseline_val = 1.0

        for idx, mult in enumerate(sweep_range):
            t_mult = mult if parameter_type == "TRANSPORT_COST" else 1.0
            d_mult = mult if parameter_type == "BUYER_DEMAND" else 1.0
            p_mult = mult if parameter_type == "PRICE_SHOCK" else 1.0

            sim = cls.run_simulation(
                baseline_candidates=candidates,
                total_supply_kg=total_supply_kg,
                commodity_id=commodity_id,
                baseline_risk=risk_preference,
                baseline_liquidity=liquidity_preference,
                transport_cost_multiplier=t_mult,
                buyer_demand_multiplier=d_mult,
                price_shock_multiplier=p_mult,
            )

            plan = sim.counterfactual_plan
            is_feas = (plan.solver_status == plan.solver_status.OPTIMAL)
            pct_alloc = (plan.total_allocated_kg / total_supply_kg * 100.0) if total_supply_kg > 0 else 0.0

            pt = SensitivityPoint(
                step_index=idx,
                parameter_value=mult,
                parameter_label=f"{mult*100:.0f}% of baseline",
                expected_total_nrv=plan.expected_total_nrv,
                risk_adjusted_nrv=plan.risk_adjusted_nrv,
                allocated_percentage=pct_alloc,
                is_feasible=is_feas,
                solver_status=plan.solver_status,
            )
            points.append(pt)

        interp = (
            f"Sensitivity sweep across {len(points)} points for {parameter_type} completed. "
            f"NRV ranges from INR {min(p.expected_total_nrv for p in points):,.0f} to INR {max(p.expected_total_nrv for p in points):,.0f}."
        )

        return SensitivitySweepResult(
            parameter_name=parameter_type,
            baseline_value=baseline_val,
            unit=unit,
            points=points,
            interpretation=interp,
        )
