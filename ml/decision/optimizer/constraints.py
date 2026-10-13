"""
AgriClutch Step 14: Optimization Problem Formulation & Constraints.
Defines linear constraints for farmer supply, buyer demand limits, storage capacities,
transport limits, liquidity windows, and perishability thresholds.
SIH26132 — Strengthening Market Linkages and Price Discovery for Farmers.
"""

from typing import Dict, List, Tuple

import numpy as np

from ml.decision.optimizer.contracts import (
    AllocationCandidate,
    ConstraintAuditItem,
    ConstraintSummary,
    DecisionProvenanceStatus,
    LiquidityPreference,
)


class DecisionConstraintBuilder:
    """
    Constructs the canonical inequality constraint matrix:
        A_ub @ x <= b_ub
    and variable bounds:
        0 <= x_i <= upper_bound_i

    Constraints:
    1. Total Supply Conservation:
       Σ_i x_i <= Q_total

    2. Liquidity Window Constraint:
       If IMMEDIATE: Σ_(i ∈ Immediate) x_i >= 0.60 * Q_total  =>  -Σ_(i ∈ Immediate) x_i <= -0.60 * Q_total
       If BALANCED:  Σ_(i ∈ Immediate) x_i >= 0.30 * Q_total  =>  -Σ_(i ∈ Immediate) x_i <= -0.30 * Q_total
       If DELAY_TOLERANT: No minimum immediate requirement.

    3. Buyer Demand Capacity Constraints:
       For each unique buyer b: Σ_(i ∈ b) x_i <= Demand_b

    4. Storage Facility Capacity Constraints:
       For each storage facility s: Σ_(i ∈ s) x_i <= StorageCapacity_s

    5. Vehicle / Route Transport Constraints:
       For each candidate i: x_i <= TransportCapacity_i
    """

    # Documented minimum immediate liquidation ratios (Day 0-1)
    # PROVENANCE: CONFIGURED (System policy conventions representing typical smallholder cash-flow urgency,
    # NOT empirically established universal farmer behavioral truths).
    LIQUIDITY_MIN_RATIOS: Dict[LiquidityPreference, float] = {
        LiquidityPreference.IMMEDIATE: 0.60,
        LiquidityPreference.BALANCED: 0.30,
        LiquidityPreference.DELAY_TOLERANT: 0.00,
    }
    LIQUIDITY_PROVENANCE: DecisionProvenanceStatus = DecisionProvenanceStatus.CONFIGURED

    @classmethod
    def build_system(
        cls,
        candidates: List[AllocationCandidate],
        total_supply_kg: float,
        liquidity_preference: LiquidityPreference,
    ) -> Tuple[np.ndarray, np.ndarray, List[Tuple[float, float]], List[str]]:
        """
        Builds the constraint system for SciPy linprog:
        - A_ub: 2D array of constraint coefficients
        - b_ub: 1D array of right-hand bounds
        - bounds: list of (0, upper_limit) for each variable
        - constraint_labels: descriptive name for each row in A_ub
        """
        n = len(candidates)
        if n == 0:
            return np.empty((0, 0)), np.empty(0), [], []

        rows: List[List[float]] = []
        b_vals: List[float] = []
        labels: List[str] = []

        # Constraint 1: Supply Conservation (Σ x_i <= Q_total)
        supply_row = [1.0] * n
        rows.append(supply_row)
        b_vals.append(float(total_supply_kg))
        labels.append("TOTAL_SUPPLY_CONSERVATION")

        # Constraint 2: Liquidity Preference
        min_immediate_ratio = cls.LIQUIDITY_MIN_RATIOS.get(liquidity_preference, 0.0)
        if min_immediate_ratio > 0.0:
            min_immediate_kg = min_immediate_ratio * total_supply_kg
            # -Σ_(i ∈ Immediate) x_i <= -min_immediate_kg
            liq_row = [
                -1.0 if cand.is_immediate_window else 0.0
                for cand in candidates
            ]
            rows.append(liq_row)
            b_vals.append(-float(min_immediate_kg))
            labels.append(f"LIQUIDITY_MIN_IMMEDIATE_{liquidity_preference.value}")

        # Constraint 3: Buyer Demand Grouping
        buyer_indices: Dict[str, List[int]] = {}
        buyer_demands: Dict[str, float] = {}
        for idx, cand in enumerate(candidates):
            if cand.buyer_id:
                buyer_indices.setdefault(cand.buyer_id, []).append(idx)
                buyer_demands[cand.buyer_id] = min(
                    buyer_demands.get(cand.buyer_id, float("inf")),
                    cand.max_demand_kg
                )

        for b_id, indices in buyer_indices.items():
            demand_limit = buyer_demands[b_id]
            if np.isfinite(demand_limit) and demand_limit > 0:
                row = [0.0] * n
                for i in indices:
                    row[i] = 1.0
                rows.append(row)
                b_vals.append(float(demand_limit))
                labels.append(f"BUYER_DEMAND_CAPACITY_{b_id}")

        # Constraint 4: Storage Facility Grouping
        storage_indices: Dict[str, List[int]] = {}
        storage_capacities: Dict[str, float] = {}
        for idx, cand in enumerate(candidates):
            if cand.storage_facility_id:
                storage_indices.setdefault(cand.storage_facility_id, []).append(idx)
                storage_capacities[cand.storage_facility_id] = min(
                    storage_capacities.get(cand.storage_facility_id, float("inf")),
                    cand.max_storage_kg
                )

        for s_id, indices in storage_indices.items():
            store_cap = storage_capacities[s_id]
            if np.isfinite(store_cap) and store_cap > 0:
                row = [0.0] * n
                for i in indices:
                    row[i] = 1.0
                rows.append(row)
                b_vals.append(float(store_cap))
                labels.append(f"STORAGE_FACILITY_CAPACITY_{s_id}")

        # Variable Bounds: 0 <= x_i <= min(Supply, Demand_i, Transport_i)
        bounds: List[Tuple[float, float]] = []
        for cand in candidates:
            upper = min(total_supply_kg, cand.max_demand_kg, cand.max_transport_kg)
            bounds.append((0.0, float(upper)))

        A_ub = np.array(rows, dtype=np.float64)  # noqa: N806
        b_ub = np.array(b_vals, dtype=np.float64)

        return A_ub, b_ub, bounds, labels

    @classmethod
    def audit_solution_constraints(
        cls,
        candidates: List[AllocationCandidate],
        x_sol: np.ndarray,
        total_supply_kg: float,
        liquidity_preference: LiquidityPreference,
        tolerance: float = 1e-4,
    ) -> ConstraintSummary:
        """
        Conducts an independent post-solve audit of all physical and economic constraints.
        Returns a structured ConstraintSummary object.
        """
        summary = ConstraintSummary()
        items: List[ConstraintAuditItem] = []
        violated: List[str] = []

        # 1. Total Supply Check
        total_allocated = float(np.sum(x_sol))
        supply_slack = total_supply_kg - total_allocated
        is_supply_violated = supply_slack < -tolerance
        status = "VIOLATED" if is_supply_violated else ("BINDING" if abs(supply_slack) <= tolerance else "SATISFIED")
        if is_supply_violated:
            summary.supply_constraint_status = "VIOLATED"
            violated.append("TOTAL_SUPPLY_CONSERVATION")
        else:
            summary.supply_constraint_status = status

        items.append(ConstraintAuditItem(
            constraint_name="TOTAL_SUPPLY_CONSERVATION",
            status=status,
            lhs_value=round(total_allocated, 2),
            rhs_bound=round(total_supply_kg, 2),
            unit="kg",
            slack=round(supply_slack, 2),
            description="Total allocations must not exceed farmer available produce",
        ))

        # 2. Liquidity Check
        min_immediate_ratio = cls.LIQUIDITY_MIN_RATIOS.get(liquidity_preference, 0.0)
        min_immediate_kg = min_immediate_ratio * total_supply_kg
        immediate_allocated = sum(
            float(x_sol[idx])
            for idx, c in enumerate(candidates)
            if c.is_immediate_window
        )
        liq_slack = immediate_allocated - min_immediate_kg
        is_liq_violated = liq_slack < -tolerance and min_immediate_ratio > 0.0
        status_liq = "VIOLATED" if is_liq_violated else ("BINDING" if abs(liq_slack) <= tolerance else "SATISFIED")
        if is_liq_violated:
            summary.liquidity_constraint_status = "VIOLATED"
            violated.append(f"LIQUIDITY_MIN_IMMEDIATE_{liquidity_preference.value}")
        else:
            summary.liquidity_constraint_status = status_liq

        items.append(ConstraintAuditItem(
            constraint_name=f"LIQUIDITY_MIN_IMMEDIATE_{liquidity_preference.value}",
            status=status_liq,
            lhs_value=round(immediate_allocated, 2),
            rhs_bound=round(min_immediate_kg, 2),
            unit="kg",
            slack=round(liq_slack, 2),
            description=f"Minimum {int(min_immediate_ratio*100)}% liquidation in immediate Day 0-1 window",
        ))

        # 3. Buyer Demand Check
        buyer_allocations: Dict[str, float] = {}
        buyer_limits: Dict[str, float] = {}
        for idx, c in enumerate(candidates):
            if c.buyer_id:
                buyer_allocations[c.buyer_id] = buyer_allocations.get(c.buyer_id, 0.0) + float(x_sol[idx])
                buyer_limits[c.buyer_id] = min(buyer_limits.get(c.buyer_id, float("inf")), c.max_demand_kg)

        for b_id, alloc in buyer_allocations.items():
            limit = buyer_limits[b_id]
            slack = limit - alloc
            is_viol = slack < -tolerance
            st = "VIOLATED" if is_viol else ("BINDING" if abs(slack) <= tolerance else "SATISFIED")
            if is_viol:
                summary.demand_constraint_status = "VIOLATED"
                violated.append(f"BUYER_DEMAND_{b_id}")
            items.append(ConstraintAuditItem(
                constraint_name=f"BUYER_DEMAND_{b_id}",
                status=st,
                lhs_value=round(alloc, 2),
                rhs_bound=round(limit, 2),
                unit="kg",
                slack=round(slack, 2),
                description=f"Produce allocated to buyer {b_id} must not exceed verified demand",
            ))

        summary.items = items
        summary.violated_constraints = violated
        return summary
