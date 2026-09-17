"""
Abstract Base Forecaster Interface for AgriClutch.
Enforces probabilistic quantile forecasting across foundation models and baselines.
SIH26132 — Market Linkages and Price Discovery for Farmers.
"""

from abc import ABC, abstractmethod
from collections.abc import Sequence


class BaseForecaster(ABC):
    """
    Abstract contract for agricultural commodity price probabilistic forecasters.
    Decoupled from specific foundation models (e.g. Chronos-2) or statistical baselines.
    """

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Unique identifier for the forecasting engine."""

    @property
    @abstractmethod
    def model_version(self) -> str:
        """Version or checkpoint identifier."""

    @property
    @abstractmethod
    def parameter_count(self) -> str:
        """Human-readable parameter count (e.g., '120M', '0')."""

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """True if the model dependencies and runtime are operational on host."""

    @abstractmethod
    def fit(
        self,
        history_prices: Sequence[float],
        history_dates: Sequence[str] | None = None,
    ) -> None:
        """
        Calibrate or prepare the forecaster with historical context data.

        Args:
            history_prices: Sequence of past normalized modal prices (INR/kg).
            history_dates: Optional sequence of corresponding session dates (YYYY-MM-DD).
        """

    @abstractmethod
    def predict_quantiles(
        self,
        history_prices: Sequence[float],
        horizon: int = 14,
        quantiles: list[float] | None = None,
        history_dates: Sequence[str] | None = None,
    ) -> dict[float, list[float]]:
        """
        Produce multi-horizon probabilistic forecasts at requested quantiles.

        Args:
            history_prices: Sequence of past normalized modal prices (INR/kg).
            horizon: Number of days forward to predict (e.g., 7, 14, 28).
            quantiles: List of float quantiles in (0, 1). Defaults to [0.10, 0.20, 0.50, 0.80, 0.90].
            history_dates: Optional sequence of past session dates.

        Returns:
            Dictionary mapping float quantile (e.g. 0.5) to a list of floats of length `horizon`.
        """
