"""
Abstract Base Anomaly Detector Interface for AgriClutch.
Provides contracts for robust statistical outlier identification on agricultural time series.
"""

from abc import ABC, abstractmethod
from typing import Any


class BaseAnomalyDetector(ABC):
    """
    Abstract contract for detecting reporting errors, extreme spikes, and structural shifts.
    """

    @property
    @abstractmethod
    def detector_name(self) -> str:
        """Identifier for the anomaly detection algorithm."""

    @abstractmethod
    def score_series(
        self,
        values: list[float],
        timestamps: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Evaluate time series values and assign anomaly scores and boolean flags.

        Args:
            values: Numerical sequence of prices or arrival tonnages.
            timestamps: Optional corresponding date strings.

        Returns:
            List of dictionaries containing score, is_anomaly, and deviation metrics.
        """
