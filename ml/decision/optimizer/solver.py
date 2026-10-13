"""
AgriClutch Step 14: Deterministic Mathematical Solver.
Wraps SciPy HiGHS Dual Simplex linear programming optimizer.
Provides strict status codes, execution timing, and error handling.
SIH26132 — Strengthening Market Linkages and Price Discovery for Farmers.
"""

import time
from typing import List

import numpy as np
from scipy.optimize import linprog

from ml.decision.optimizer.constraints import DecisionConstraintBuilder
from ml.decision.optimizer.contracts import (
    AllocationCandidate,
    LiquidityPreference,
    RiskPreference,
    SolverStatus,
)
from ml.decision.optimizer.objective import DecisionObjectiveEngine


class DecisionSolverResult:
    """Internal solver return container."""
    def __init__(
        self,
        status: SolverStatus,
        message: str,
        x_solution: np.ndarray,
        objective_value: float,
        duration_ms: float,
    ):
        self.status = status
        self.message = message
        self.x_solution = x_solution
        self.objective_value = objective_value
        self.duration_ms = duration_ms


class DecisionSolver:
    """
    Deterministic Linear Programming Solver using SciPy HiGHS Dual Simplex.
    Formulates standard maximization:
        max c^T x  <=>  min -c^T x
        s.t. A_ub x <= b_ub, 0 <= x <= bounds

    OPTIMALITY SCOPE:
    When the solver returns status OPTIMAL, SciPy HiGHS provides a mathematically guaranteed
    globally optimal solution to the FORMULATED LINEAR PROGRAM. It does NOT claim global optimality
    of the real-world agricultural market system or unmodeled external factors.
    """

    @classmethod
    def solve(
        cls,
        candidates: List[AllocationCandidate],
        total_supply_kg: float,
        risk_preference: RiskPreference = RiskPreference.RISK_AWARE,
        liquidity_preference: LiquidityPreference = LiquidityPreference.BALANCED,
        timeout_seconds: float = 5.0,
    ) -> DecisionSolverResult:
        """
        Solves the multi-destination selling allocation problem.
        """
        start_time = time.perf_counter()

        if not candidates or total_supply_kg <= 0.0:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            return DecisionSolverResult(
                status=SolverStatus.NO_FEASIBLE_PLAN,
                message="No feasible candidate allocations available or supply is zero.",
                x_solution=np.empty(0),
                objective_value=0.0,
                duration_ms=duration_ms,
            )

        # 1. Objective Vector (negated for SciPy minimization)
        c_coeffs = DecisionObjectiveEngine.compute_candidate_coefficients(
            candidates=candidates,
            risk_preference=risk_preference,
        )
        c_min = -c_coeffs

        # 2. Constraint System
        A_ub, b_ub, bounds, _ = DecisionConstraintBuilder.build_system(  # noqa: N806
            candidates=candidates,
            total_supply_kg=total_supply_kg,
            liquidity_preference=liquidity_preference,
        )

        # 3. Solve with SciPy linprog (HiGHS dual simplex method)
        try:
            res = linprog(
                c=c_min,
                A_ub=A_ub if A_ub.size > 0 else None,
                b_ub=b_ub if b_ub.size > 0 else None,
                bounds=bounds,
                method="highs",
                options={"time_limit": timeout_seconds},
            )
            duration_ms = (time.perf_counter() - start_time) * 1000.0

            if res.success:
                x_sol = np.maximum(0.0, res.x)
                # Maximize c^T x = -min_val
                max_obj = float(-res.fun)
                return DecisionSolverResult(
                    status=SolverStatus.OPTIMAL,
                    message="Global optimal split allocation identified by HiGHS solver.",
                    x_solution=x_sol,
                    objective_value=max_obj,
                    duration_ms=duration_ms,
                )
            elif res.status == 2:  # Infeasible
                return DecisionSolverResult(
                    status=SolverStatus.INFEASIBLE,
                    message=f"Problem is mathematically infeasible under given constraints: {res.message}",
                    x_solution=np.zeros(len(candidates)),
                    objective_value=0.0,
                    duration_ms=duration_ms,
                )
            elif res.status == 1:  # Time limit
                return DecisionSolverResult(
                    status=SolverStatus.TIME_LIMIT,
                    message="Solver exceeded allocated execution time limit.",
                    x_solution=np.zeros(len(candidates)),
                    objective_value=0.0,
                    duration_ms=duration_ms,
                )
            else:
                return DecisionSolverResult(
                    status=SolverStatus.ERROR,
                    message=f"Solver returned non-optimal termination: {res.message}",
                    x_solution=np.zeros(len(candidates)),
                    objective_value=0.0,
                    duration_ms=duration_ms,
                )

        except Exception as ex:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            return DecisionSolverResult(
                status=SolverStatus.ERROR,
                message=f"Internal mathematical solver exception: {str(ex)}",
                x_solution=np.zeros(len(candidates)),
                objective_value=0.0,
                duration_ms=duration_ms,
            )
