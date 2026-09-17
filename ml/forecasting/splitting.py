"""
Rolling-Origin (Walk-Forward) Temporal Cross-Validation Splitter.
Guarantees zero data leakage and strictly chronological train/test isolation.
SIH26132 — Market Linkages and Price Discovery for Farmers.
"""

from collections.abc import Iterator
from dataclasses import dataclass

from ml.forecasting.dataset import TimeSeriesDataset


@dataclass
class TemporalFold:
    """Represents a single walk-forward evaluation fold."""

    fold_index: int
    origin_index: int
    origin_date: str
    train_prices: list[float]
    train_dates: list[str]
    test_prices: list[float]
    test_dates: list[str]
    horizon: int


class RollingOriginSplitter:
    """
    Generates expanding-window temporal folds for honest time-series evaluation.
    At each fold k, the model is trained exclusively on data up to origin T_k,
    and evaluated on the strictly subsequent window [T_k + 1, T_k + H].
    """

    def __init__(
        self,
        initial_train_size: int = 30,
        horizon: int = 14,
        step_size: int = 7,
        max_splits: int | None = 5,
    ) -> None:
        if initial_train_size < 10:
            raise ValueError("initial_train_size must be at least 10 observations.")
        if horizon < 1:
            raise ValueError("horizon must be at least 1 day.")
        if step_size < 1:
            raise ValueError("step_size must be at least 1 day.")

        self.initial_train_size = initial_train_size
        self.horizon = horizon
        self.step_size = step_size
        self.max_splits = max_splits

    def split(self, dataset: TimeSeriesDataset) -> Iterator[TemporalFold]:
        """
        Yields TemporalFold instances across the dataset.

        Args:
            dataset: TimeSeriesDataset to split.

        Yields:
            TemporalFold objects in chronological order.
        """
        n_total = len(dataset.prices)
        min_required = self.initial_train_size + self.horizon
        if n_total < min_required:
            return

        # Calculate all valid origin indices
        # Origin must leave at least `horizon` observations for testing
        possible_origins: list[int] = []
        curr_origin = self.initial_train_size - 1
        while curr_origin + self.horizon < n_total:
            possible_origins.append(curr_origin)
            curr_origin += self.step_size

        if self.max_splits is not None and len(possible_origins) > self.max_splits:
            # Take the most recent `max_splits` folds to reflect modern market conditions
            possible_origins = possible_origins[-self.max_splits :]

        for fold_idx, origin_idx in enumerate(possible_origins):
            train_prices = dataset.prices[: origin_idx + 1]
            train_dates = dataset.dates[: origin_idx + 1]

            test_end_idx = origin_idx + 1 + self.horizon
            test_prices = dataset.prices[origin_idx + 1 : test_end_idx]
            test_dates = dataset.dates[origin_idx + 1 : test_end_idx]

            yield TemporalFold(
                fold_index=fold_idx,
                origin_index=origin_idx,
                origin_date=dataset.dates[origin_idx],
                train_prices=train_prices,
                train_dates=train_dates,
                test_prices=test_prices,
                test_dates=test_dates,
                horizon=len(test_prices),
            )
