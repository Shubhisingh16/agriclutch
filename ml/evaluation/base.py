"""
Abstract Base Evaluator Interface for AgriClutch.
Enforces standard evaluation metrics for quantile forecasting and strategy backtesting.
"""

from abc import ABC, abstractmethod


class BaseEvaluator(ABC):
    """
    Abstract contract for evaluating model accuracy and decision optimization lift.
    """

    @abstractmethod
    def evaluate_forecasts(
        self,
        actuals: list[float],
        predictions: dict[str, list[float]],
    ) -> dict[str, float]:
        """
        Compute Pinball Loss, MASE, MAPE, and coverage probability on backtest horizons.

        Args:
            actuals: Observed ground truth commodity prices.
            predictions: Quantile predictions dict with 'p10', 'p50', 'p90'.

        Returns:
            Dictionary of metrics: {'mase': float, 'pinball_loss': float, 'coverage_90': float}.
        """

    @abstractmethod
    def evaluate_decision_lift(
        self,
        recommended_nrv: float,
        baseline_nrv: float,
    ) -> dict[str, float]:
        """
        Calculate realized percentage lift and absolute profit gain over default APMC liquidation.

        Args:
            recommended_nrv: Realized net return from optimal split plan.
            baseline_nrv: Realized net return from immediate default mandi sale.

        Returns:
            Dictionary with 'absolute_lift_inr' and 'percentage_lift'.
        """
