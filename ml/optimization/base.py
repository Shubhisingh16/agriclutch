"""
Abstract Base Selling Plan Optimizer Interface for AgriClutch.
Core optimization contract answering:
Optimal Selling Plan = f(Crop, Quantity, Quality, Location, Storage, Liquidity, Risk).
"""

from abc import ABC, abstractmethod
from typing import Any


class BaseSellingPlanOptimizer(ABC):
    """
    Abstract contract for decision optimization engine.
    Solves for multi-strategy split allocations maximizing Net Realizable Value (NRV).
    """

    @abstractmethod
    def solve_plan(
        self,
        lot_profile: dict[str, Any],
        farmer_constraints: dict[str, Any],
        market_forecasts: dict[str, Any],
        buyer_bids: list[dict[str, Any]],
        logistics_lookup: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Compute the optimal split selling plan across immediate sale and storage strategies.

        Args:
            lot_profile: Quantity, commodity, quality grade, moisture, harvest date.
            farmer_constraints: Max storage days, immediate liquidity requirement %, risk preference.
            market_forecasts: Probabilistic price quantiles (P10, P50, P90) across reachable mandis.
            buyer_bids: Direct verified buyer bids.
            logistics_lookup: Freight rates, loading costs, and mandi fees.

        Returns:
            Dictionary containing:
                - recommended_plan: Strategy allocations summing to 100% of quantity
                - comparison_strategies: baseline strategies (e.g. 100% immediate APMC, 100% store)
                - net_realizable_value: Expected and risk-adjusted realization in INR
                - mathematical_justification: Detailed breakdown of trade-offs and cost deductions
        """
