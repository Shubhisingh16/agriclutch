"""
AgriClutch Step 14: Objective Function & Downside Risk (CVaR) Model.
Formulates the mathematical optimization objective:
Expected Net Realization - Downside Risk Adjustment (CVaR Penalty).
SIH26132 — Strengthening Market Linkages and Price Discovery for Farmers.
"""

from typing import Dict, List, Tuple

import numpy as np

from ml.decision.optimizer.contracts import (
    AllocationCandidate,
    DecisionProvenanceStatus,
    RiskMetrics,
    RiskPreference,
)


class DecisionObjectiveEngine:
    """
    Constructs transparent, mathematically grounded linear objective functions.

    Optimization Objective Formulation (LP Matrix Objective):
    Maximize:
        Z = Σ_i ( c_i * x_i )
    where:
        c_i = ExpectedNRV_i - λ * DownsideSpread_i
        DownsideSpread_i = max(0, ExpectedNRV_i - NRV_p10,i)

    Mathematical Meaning of DownsideSpread_i:
    - It represents the parametric lower-quantile downside spread (dispersion between the central expectation
      and the 10th percentile conservative realization).
    - It penalizes allocations to channels characterized by high lower-tail forecast volatility / uncertainty.
    - It is linear in x_i, enabling globally optimal solution via SciPy HiGHS Dual Simplex without non-linear solver heuristics.

    Configured Lambda (λ) Risk Penalty Weights:
    - RISK_NEUTRAL: λ = 0.0 (Optimizes pure expected economic realization; zero downside spread penalty).
    - RISK_AWARE:   λ = 0.5 (Configured policy weighting balancing expected gain with lower quantile spread).
    - RISK_AVERSE:  λ = 1.0 (Full 1:1 deduction of lower quantile spread to safeguard farmer floor price).
    Provenance Status of λ: CONFIGURED (system policy parameters, not empirically estimated farmer utility curves).
    """

    # Configured policy weights for downside uncertainty penalty
    RISK_WEIGHTS: Dict[RiskPreference, float] = {
        RiskPreference.RISK_NEUTRAL: 0.0,
        RiskPreference.RISK_AWARE: 0.5,
        RiskPreference.RISK_AVERSE: 1.0,
    }

    @classmethod
    def get_risk_weight(cls, preference: RiskPreference) -> float:
        return cls.RISK_WEIGHTS.get(preference, 0.5)

    @classmethod
    def compute_candidate_coefficients(
        cls,
        candidates: List[AllocationCandidate],
        risk_preference: RiskPreference,
    ) -> np.ndarray:
        """
        Computes the net economic objective coefficient for each allocation candidate.

        c_i = ExpectedNRV_per_kg_i - λ * max(0, ExpectedNRV_per_kg_i - NRV_p10_per_kg_i)

        Returns 1D numpy array of coefficients (INR / kg).
        """
        lambda_risk = cls.get_risk_weight(risk_preference)
        coefficients = []

        for cand in candidates:
            expected_nrv = cand.expected_nrv_per_kg
            # Downside shortfall measures distance from median/expected to 10th percentile
            downside_shortfall = max(0.0, expected_nrv - cand.nrv_p10)
            risk_penalty = lambda_risk * downside_shortfall
            net_coeff = expected_nrv - risk_penalty
            coefficients.append(net_coeff)

        return np.array(coefficients, dtype=np.float64)

    @classmethod
    def compute_aggregate_risk_metrics(
        cls,
        allocations: List[Tuple[AllocationCandidate, float]],
        risk_preference: RiskPreference,
    ) -> RiskMetrics:
        """
        Computes aggregated Value at Risk (VaR) and Conditional Value at Risk (CVaR)
        across the synthesized multi-destination portfolio.

        Allocations list: [(Candidate, allocated_kg), ...]
        """
        lambda_risk = cls.get_risk_weight(risk_preference)

        total_expected_nrv = 0.0
        total_p10_nrv = 0.0
        total_p50_nrv = 0.0
        total_p90_nrv = 0.0
        total_downside_penalty = 0.0

        for cand, qty in allocations:
            if qty <= 0.0:
                continue
            total_expected_nrv += qty * cand.expected_nrv_per_kg
            total_p10_nrv += qty * cand.nrv_p10
            total_p50_nrv += qty * cand.nrv_p50
            total_p90_nrv += qty * cand.nrv_p90

            shortfall = max(0.0, cand.expected_nrv_per_kg - cand.nrv_p10)
            total_downside_penalty += lambda_risk * shortfall * qty

        # --- Post-Solve Risk Evaluation (NOT directly in LP objective matrix) ---
        # Portfolio downside spread evaluated as lower-quantile dispersion (median to 10th percentile spread)
        downside_spread = max(0.0, total_p50_nrv - total_p10_nrv)
        # Configured tail stress estimate via parametric multiplier (1.25x)
        # NOTE: 1.25 is NOT an intrinsic mathematical constant of CVaR; it is a CONFIGURED policy assumption
        # representing a tail-stress approximation below P10. It is NOT standard CVaR95.
        tail_stress_mult = 1.25
        tail_stress_estimate = downside_spread * tail_stress_mult

        risk_adjusted_nrv = total_expected_nrv - total_downside_penalty

        return RiskMetrics(
            risk_preference=risk_preference,
            risk_penalty_weight=lambda_risk,
            portfolio_downside_spread=downside_spread,
            configured_tail_stress_estimate=tail_stress_estimate,
            expected_total_nrv=total_expected_nrv,
            risk_adjusted_nrv=risk_adjusted_nrv,
            downside_spread_penalty=total_downside_penalty,
            confidence_level=0.90,
            p10_total_nrv=total_p10_nrv,
            p50_total_nrv=total_p50_nrv,
            p90_total_nrv=total_p90_nrv,
            tail_stress_multiplier=tail_stress_mult,
            tail_stress_provenance=DecisionProvenanceStatus.CONFIGURED,
            provenance_status=DecisionProvenanceStatus.CONFIGURED,
            is_demo=True,
        )
