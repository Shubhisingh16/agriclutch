"""
Strictly Past-Derived Feature Engineering for Tabular Time-Series Models.
Guarantees that no future information or target leaks into predictor columns.
SIH26132 — Market Linkages and Price Discovery for Farmers.
"""

from collections.abc import Sequence
from datetime import date
from typing import ClassVar

import numpy as np


class PastFeatureExtractor:
    """
    Constructs past-lagged, rolling statistical, and calendar features.
    Every feature is strictly derived from observations available at or before index t.
    """

    LAG_DAYS: ClassVar[list[int]] = [1, 3, 7, 14, 28]
    ROLLING_WINDOWS: ClassVar[list[int]] = [7, 14, 28]

    @classmethod
    def get_feature_names(cls) -> list[str]:
        """Returns ordered list of feature column names."""
        names = [f"lag_{lag}" for lag in cls.LAG_DAYS]
        for w in cls.ROLLING_WINDOWS:
            names.extend([f"roll_mean_{w}", f"roll_std_{w}", f"roll_median_{w}"])
        names.extend(["day_of_week", "day_of_month", "month"])
        return names

    @classmethod
    def extract_features_at_step(
        cls,
        history: Sequence[float],
        current_date_str: str | None = None,
    ) -> list[float]:
        """
        Extracts feature vector using history strictly available up to the current step.

        Args:
            history: Sequence of past prices up to the forecast origin [y_0 ... y_t].
            current_date_str: ISO string of the current date for calendar features.

        Returns:
            List of float feature values matching get_feature_names().
        """
        n = len(history)
        if n == 0:
            raise ValueError("History cannot be empty for feature extraction.")

        features: list[float] = []

        # 1. Lags (fill with oldest available if history is shorter than lag)
        for lag in cls.LAG_DAYS:
            if n > lag:
                val = history[-1 - lag]
            else:
                val = history[0]
            features.append(float(val))

        # 2. Rolling Statistics over past observations
        for w in cls.ROLLING_WINDOWS:
            sub = history[-w:] if n >= w else history
            arr = np.array(sub, dtype=np.float64)
            features.append(float(np.mean(arr)))
            features.append(float(np.std(arr)))
            features.append(float(np.median(arr)))

        # 3. Calendar Features (Derived solely from current calendar date)
        if current_date_str:
            dt = date.fromisoformat(current_date_str)
            features.append(float(dt.weekday()))  # 0=Monday, 6=Sunday
            features.append(float(dt.day))        # 1-31
            features.append(float(dt.month))      # 1-12
        else:
            features.extend([0.0, 1.0, 1.0])

        return features

    @classmethod
    def build_training_dataset(
        cls,
        prices: Sequence[float],
        dates: Sequence[str] | None = None,
        max_lag: int = 28,
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Builds matrix X and target y for 1-step autoregressive model training.
        For every row i >= max_lag, features use strictly prices[:i], predicting prices[i].
        """
        n = len(prices)
        if n <= max_lag:
            raise ValueError(f"Insufficient history ({n}) for max_lag ({max_lag}).")

        x_rows: list[list[float]] = []
        y_rows: list[float] = []

        for i in range(max_lag, n):
            target = prices[i]
            # Context strictly up to i - 1
            hist_sub = prices[:i]
            d_str = dates[i - 1] if dates and len(dates) > i - 1 else None
            feat = cls.extract_features_at_step(hist_sub, d_str)
            x_rows.append(feat)
            y_rows.append(float(target))

        return np.array(x_rows, dtype=np.float64), np.array(y_rows, dtype=np.float64)
