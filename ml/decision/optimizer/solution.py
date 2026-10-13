"""
AgriClutch Step 14: Solution Validation & Plan Assembler.
Transforms raw solver allocations into fully auditable, explainable OptimalSellingPlan objects.
SIH26132 — Strengthening Market Linkages and Price Discovery for Farmers.
"""

import hashlib
import json
from typing import List, Tuple

from ml.decision.optimizer.constraints import DecisionConstraintBuilder
from ml.decision.optimizer.contracts import (
    AllocationCandidate,
    DecisionProvenance,
    LiquidityPreference,
    OptimalSellingPlan,
    PlanAllocation,
    RiskPreference,
    SolverStatus,
    ValidationStatus,
)
from ml.decision.optimizer.objective import DecisionObjectiveEngine
from ml.decision.optimizer.solver import DecisionSolverResult


class DecisionPlanAssembler:
    """
    Validates solver results and assembles the complete OptimalSellingPlan.
    """

    @classmethod
    def assemble(
        cls,
        candidates: List[AllocationCandidate],
        solver_res: DecisionSolverResult,
        commodity_id: str,
        total_supply_kg: float,
        variety: str = "Standard",
        quality_grade: str = "GRADE_A",
        decision_horizon_days: int = 7,
        risk_preference: RiskPreference = RiskPreference.RISK_AWARE,
        liquidity_preference: LiquidityPreference = LiquidityPreference.BALANCED,
        input_snapshot_id: str = "snap_demo_01",
    ) -> OptimalSellingPlan:
        """
        Synthesizes the validated OptimalSellingPlan object.
        """
        plan = OptimalSellingPlan(
            commodity_id=commodity_id,
            variety=variety,
            quality_grade=quality_grade,
            total_supply_kg=total_supply_kg,
            decision_horizon_days=decision_horizon_days,
            risk_preference=risk_preference,
            liquidity_preference=liquidity_preference,
            input_snapshot_id=input_snapshot_id,
            solver_status=solver_res.status,
            solver_message=solver_res.message,
            solver_duration_ms=round(solver_res.duration_ms, 2),
        )

        # Hash input configuration for reproducibility auditing
        config_dict = {
            "commodity_id": commodity_id,
            "total_supply_kg": total_supply_kg,
            "decision_horizon_days": decision_horizon_days,
            "risk_preference": risk_preference.value,
            "liquidity_preference": liquidity_preference.value,
            "num_candidates": len(candidates),
        }
        plan.configuration_hash = hashlib.sha256(json.dumps(config_dict, sort_keys=True).encode()).hexdigest()[:16]

        if solver_res.status != SolverStatus.OPTIMAL:
            plan.validation_status = ValidationStatus.FAILED
            plan.total_unallocated_kg = total_supply_kg
            plan.executive_summary = f"Optimization halted: {solver_res.message}"
            plan.structured_explanations = [
                f"Solver terminated with status {solver_res.status.value}.",
                solver_res.message,
            ]
            return plan

        x_sol = solver_res.x_solution
        n = len(candidates)
        allocations: List[PlanAllocation] = []
        alloc_pairs: List[Tuple[AllocationCandidate, float]] = []

        total_allocated = 0.0
        total_effective = 0.0
        total_gross_rev = 0.0
        total_freight = 0.0
        total_storage = 0.0
        total_handling = 0.0
        total_market_fees = 0.0
        total_nrv = 0.0

        for idx in range(n):
            qty = float(x_sol[idx])
            if qty < 1e-3:  # Skip negligible rounding artifacts
                continue

            cand = candidates[idx]
            alloc_pairs.append((cand, qty))
            pct = (qty / total_supply_kg) * 100.0 if total_supply_kg > 0 else 0.0
            eff_qty = qty * cand.mass_retention_factor

            gross = qty * cand.expected_price_per_kg
            freight = qty * cand.freight_cost_per_kg
            storage = qty * cand.storage_cost_per_kg
            handling = qty * cand.handling_cost_per_kg
            mkt_fee = qty * cand.market_fee_per_kg
            alloc_nrv = qty * cand.expected_nrv_per_kg

            total_allocated += qty
            total_effective += eff_qty
            total_gross_rev += gross
            total_freight += freight
            total_storage += storage
            total_handling += handling
            total_market_fees += mkt_fee
            total_nrv += alloc_nrv

            # Identify limiting constraints for this allocation
            limits: List[str] = []
            if abs(qty - cand.max_demand_kg) < 1.0:
                limits.append(f"Buyer/Market demand limit ({int(cand.max_demand_kg)} kg)")
            if abs(qty - cand.max_transport_kg) < 1.0:
                limits.append(f"Transport vehicle capacity ({int(cand.max_transport_kg)} kg)")
            if cand.max_storage_kg > 0 and abs(qty - cand.max_storage_kg) < 1.0:
                limits.append(f"Storage facility capacity ({int(cand.max_storage_kg)} kg)")
            if not limits:
                limits.append("Optimally balanced by net economic return")

            # Explanation sentence
            timing_desc = "immediately (Day 0-1)" if cand.sale_day_offset <= 1 else f"after {cand.sale_day_offset} days"
            storage_desc = " via cold/ventilated holding" if cand.storage_facility_id else " with direct transit"
            explanation = (
                f"Sell {qty:,.1f} kg ({pct:.1f}%) to {cand.destination_name} {timing_desc}{storage_desc}. "
                f"Expected Net Realization: INR {cand.expected_nrv_per_kg:.2f}/kg after INR {freight+storage+handling+mkt_fee:,.1f} total friction."
            )

            alloc_rec = PlanAllocation(
                candidate_id=cand.candidate_id,
                destination_type=cand.destination_type,
                destination_id=cand.destination_id,
                destination_name=cand.destination_name,
                sale_day_offset=cand.sale_day_offset,
                sale_date=cand.sale_date,
                allocated_quantity_kg=round(qty, 2),
                effective_quantity_kg=round(eff_qty, 2),
                allocation_percentage=round(pct, 2),
                expected_price_per_kg=round(cand.expected_price_per_kg, 2),
                expected_nrv_per_kg=round(cand.expected_nrv_per_kg, 2),
                gross_revenue=round(gross, 2),
                total_freight_cost=round(freight, 2),
                total_storage_cost=round(storage, 2),
                total_handling_cost=round(handling, 2),
                total_market_fee=round(mkt_fee, 2),
                expected_total_nrv=round(alloc_nrv, 2),
                nrv_p10_total=round(qty * cand.nrv_p10, 2),
                nrv_p50_total=round(qty * cand.nrv_p50, 2),
                nrv_p90_total=round(qty * cand.nrv_p90, 2),
                quality_factor=cand.quality_factor,
                mass_retention_factor=cand.mass_retention_factor,
                pathway_id=cand.pathway_id,
                buyer_id=cand.buyer_id,
                market_id=cand.market_id,
                storage_facility_id=cand.storage_facility_id,
                limiting_constraints=limits,
                explanation=explanation,
                provenance=DecisionProvenance(
                    source_name=f"Optimization-Allocation-{cand.destination_name}",
                    provenance_status=cand.provenance_status,
                    is_demo=cand.is_demo,
                ),
            )
            allocations.append(alloc_rec)

        plan.allocations = allocations
        plan.total_allocated_kg = round(total_allocated, 2)
        plan.total_unallocated_kg = max(0.0, round(total_supply_kg - total_allocated, 2))
        plan.total_effective_kg = round(total_effective, 2)
        plan.expected_gross_revenue = round(total_gross_rev, 2)
        plan.total_friction_cost = round(total_freight + total_storage + total_handling + total_market_fees, 2)
        plan.expected_total_nrv = round(total_nrv, 2)

        # Risk Metrics Calculation
        risk_metrics = DecisionObjectiveEngine.compute_aggregate_risk_metrics(
            allocations=alloc_pairs,
            risk_preference=risk_preference,
        )
        plan.risk_metrics = risk_metrics
        plan.risk_adjusted_nrv = round(risk_metrics.risk_adjusted_nrv, 2)

        # Post-Solve Constraint Audit
        constraint_audit = DecisionConstraintBuilder.audit_solution_constraints(
            candidates=candidates,
            x_sol=x_sol,
            total_supply_kg=total_supply_kg,
            liquidity_preference=liquidity_preference,
        )
        plan.constraint_summary = constraint_audit

        # Validation Gate
        if constraint_audit.violated_constraints:
            plan.validation_status = ValidationStatus.FAILED
            plan.solver_status = SolverStatus.ERROR
            plan.solver_message = f"Post-solve validation failed: Violated constraints {constraint_audit.violated_constraints}"
        else:
            plan.validation_status = ValidationStatus.PASSED

        # Executive Summary Generation
        if len(allocations) == 1:
            a = allocations[0]
            plan.executive_summary = f"SELL 100% ({a.allocated_quantity_kg:,.0f} kg) to {a.destination_name} (Expected NRV: INR {plan.expected_total_nrv:,.0f})"
        elif len(allocations) > 1:
            parts = [f"{a.allocation_percentage:.0f}% to {a.destination_name}" for a in allocations]
            plan.executive_summary = f"SPLIT ALLOCATION: {', '.join(parts)} (Total Expected NRV: INR {plan.expected_total_nrv:,.0f})"
        else:
            plan.executive_summary = "NO ALLOCATION POSSIBLE: Constraints prevented feasible dispatch."

        plan.structured_explanations = [a.explanation for a in allocations]
        return plan
