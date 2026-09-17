"""
Abstract Base Transformer Interface for AgriClutch.
Defines contracts for feature engineering, lag creation, and lead-lag market graph construction.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BaseTransformer(ABC):
    """
    Abstract interface for transforming cleaned records into structured feature matrices.
    """

    @abstractmethod
    def transform_for_forecasting(
        self,
        cleaned_records: List[Dict[str, Any]],
        lags: List[int] | None = None,
    ) -> Dict[str, Any]:
        """
        Generate time-indexed arrays or DataFrames suitable for time-series forecasters.

        Args:
            cleaned_records: List of normalized records.
            lags: Optional list of integer day offsets for autoregressive features.

        Returns:
            Dictionary containing timestamps, target series, and exogenous features.
        """
        pass

    @abstractmethod
    def compute_lead_lag_matrix(
        self,
        multi_market_records: Dict[str, List[Dict[str, Any]]],
        max_lag_days: int = 14,
    ) -> Dict[str, Any]:
        """
        Calculate cross-correlation matrices across regional mandis to identify leader-follower dynamics.

        Args:
            multi_market_records: Dict of market_id -> list of daily records.
            max_lag_days: Maximum cross-correlation lag window.

        Returns:
            Adjacency matrix and lead-lag directional edges.
        """
        pass
