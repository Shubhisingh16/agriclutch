"""
AgriClutch Risk & Uncertainty Subsystem.
Propagates price distribution uncertainty and cost/loss parameter bounds.
SIH26132 — Market Linkages and Price Discovery for Farmers.
"""

from typing import Dict

from ml.decision.contracts import EconomicProvenance, ProvenanceStatus, RiskSpec


class RiskModel:
    """
    Manages uncertainty propagation across price quantiles and cost scenarios.
    Never invents arbitrary probabilities or conflates NOT_MODELED with ZERO_RISK.
    """

    @staticmethod
    def get_default_risk_spec() -> RiskSpec:
        """Returns standard baseline risk specification where operational risk penalty is not modeled."""
        prov = EconomicProvenance(
            source="AGRICLUTCH_RISK_POLICY",
            status=ProvenanceStatus.CONFIGURED,
            effective_date="2024-09-15",
            is_demo=True,
            description="Operational risk penalty not modeled (cost=0.0, status=NOT_MODELED). Uncertainty captured via P10-P90 forecast quantiles.",
        )
        return RiskSpec(
            price_uncertainty="MODELED_QUANTILES_P10_P90",
            cost_uncertainty="NOT_MODELED",
            operational_risk_cost=0.0,
            risk_status="NOT_MODELED",
            provenance=prov,
        )

    @staticmethod
    def get_scenario_cost_multipliers(scenario_type: str) -> Dict[str, float]:
        """
        Returns documented cost and loss stress multipliers for sensitivity/scenario analysis.
        Labels: EXPECTED, CONSERVATIVE, OPTIMISTIC.
        """
        norm_type = scenario_type.strip().upper()
        if norm_type == "CONSERVATIVE":
            # Downside price (P10) combined with stressed friction costs and higher loss
            return {
                "price_quantile": 0.10,
                "transport_multiplier": 1.15,
                "handling_multiplier": 1.15,
                "storage_multiplier": 1.20,
                "loss_multiplier": 1.25,
            }
        elif norm_type == "OPTIMISTIC":
            # Upside price (P90) combined with efficient friction costs and lower loss
            return {
                "price_quantile": 0.90,
                "transport_multiplier": 0.90,
                "handling_multiplier": 0.90,
                "storage_multiplier": 1.00,
                "loss_multiplier": 0.90,
            }
        else:
            # Baseline expected realization (P50) with standard documented costs
            return {
                "price_quantile": 0.50,
                "transport_multiplier": 1.00,
                "handling_multiplier": 1.00,
                "storage_multiplier": 1.00,
                "loss_multiplier": 1.00,
            }
