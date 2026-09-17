"""
Amazon Chronos-2 Foundation Model Adapter for AgriClutch.
Provides zero-shot probabilistic quantile forecasting using chronos-forecasting pipeline.
SIH26132 — Market Linkages and Price Discovery for Farmers.
"""

import logging
from collections.abc import Sequence
from typing import Any

import torch

from ml.forecasting.base import BaseForecaster

logger = logging.getLogger("agriclutch.forecasting.chronos")


class ModelUnavailableError(Exception):
    """Raised when a foundation model cannot be initialized or executed."""

    def __init__(self, status: str, detail: str) -> None:
        super().__init__(detail)
        self.status = status
        self.detail = detail


class Chronos2Forecaster(BaseForecaster):
    """
    Adapter for Amazon Chronos-2 Foundation Model (120M parameters).
    Produces zero-shot probabilistic distributions P(y[t+h] | x[<=t]).
    Strictly fails closed if the model is unreachable — NEVER fabricates predictions.
    """

    DEFAULT_CHECKPOINT = "amazon/chronos-2"

    def __init__(
        self,
        model_id: str = DEFAULT_CHECKPOINT,
        device: str | None = None,
        torch_dtype: torch.dtype | None = None,
    ) -> None:
        self.model_id = model_id
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.torch_dtype = torch_dtype or (
            torch.bfloat16 if self.device == "cuda" else torch.float32
        )
        self._pipeline: Any | None = None
        self._init_attempted: bool = False
        self._init_error: str | None = None
        self.quantile_crossings_detected: int = 0

    @property
    def model_name(self) -> str:
        return "chronos-2"

    @property
    def model_version(self) -> str:
        return self.model_id

    @property
    def parameter_count(self) -> str:
        return "120M"

    @property
    def is_available(self) -> bool:
        if not self._init_attempted:
            self._lazy_init()
        return self._pipeline is not None

    def _lazy_init(self) -> None:
        """Attempts to load Chronos-2 weights into memory with caching."""
        if self._init_attempted:
            return

        self._init_attempted = True
        try:
            import os

            from chronos import Chronos2Pipeline

            allow_download = os.environ.get("CHRONOS_ALLOW_DOWNLOAD", "0").lower() in ("1", "true")
            logger.info("Checking Chronos-2 availability for '%s' on %s...", self.model_id, self.device)

            # First attempt: check if cached locally to avoid network blocking
            try:
                self._pipeline = Chronos2Pipeline.from_pretrained(
                    self.model_id,
                    device_map=self.device,
                    torch_dtype=self.torch_dtype,
                    local_files_only=True,
                )
                self._init_error = None
                logger.info("Chronos-2 pipeline loaded from local cache.")
                return
            except Exception:  # noqa: BLE001
                if not allow_download:
                    self._pipeline = None
                    self._init_error = (
                        f"Chronos-2 checkpoint '{self.model_id}' is not present in local cache. "
                        "Set CHRONOS_ALLOW_DOWNLOAD=1 to permit remote download from Hugging Face."
                    )
                    logger.info("Chronos-2 offline mode: %s", self._init_error)
                    return

            # If download permitted, attempt remote fetch
            logger.info("Downloading Chronos-2 from Hugging Face hub...")
            self._pipeline = Chronos2Pipeline.from_pretrained(
                self.model_id,
                device_map=self.device,
                torch_dtype=self.torch_dtype,
            )
            self._init_error = None
            logger.info("Chronos-2 pipeline successfully initialized from remote hub.")
        except Exception as exc:  # noqa: BLE001
            self._pipeline = None
            self._init_error = f"Failed to initialize Chronos-2 ({self.model_id}): {exc}"
            logger.warning("Chronos-2 is unavailable on this host: %s", self._init_error)

    def fit(
        self,
        history_prices: Sequence[float],
        history_dates: Sequence[str] | None = None,
    ) -> None:
        """
        Chronos-2 is zero-shot; fitting validates history length and initializes the pipeline.
        """
        if len(history_prices) < 5:
            raise ValueError(
                f"Chronos2Forecaster requires at least 5 observations for context (found {len(history_prices)})."
            )
        if not self.is_available:
            raise ModelUnavailableError(
                status="MODEL_UNAVAILABLE",
                detail=self._init_error or "Chronos-2 weights not available on host.",
            )

    def predict_quantiles(
        self,
        history_prices: Sequence[float],
        horizon: int = 14,
        quantiles: list[float] | None = None,
        history_dates: Sequence[str] | None = None,
    ) -> dict[float, list[float]]:
        target_quantiles = sorted(quantiles or [0.10, 0.20, 0.50, 0.80, 0.90])

        self.fit(history_prices, history_dates)
        if self._pipeline is None:
            raise ModelUnavailableError(
                status="MODEL_UNAVAILABLE",
                detail=self._init_error or "Chronos-2 pipeline is uninitialized.",
            )

        try:
            # Context input tensor: shape (1, context_len)
            context_tensor = torch.tensor(
                [list(history_prices)],
                dtype=torch.float32,
                device=self.device,
            )

            # Chronos-2 native predict_quantiles
            with torch.no_grad():
                quantiles_out, _ = self._pipeline.predict_quantiles(
                    inputs=context_tensor,
                    prediction_length=horizon,
                    quantile_levels=target_quantiles,
                )

            # quantiles_out is list of tensors of shape (num_quantiles, horizon)
            q_tensor = quantiles_out[0].cpu().numpy()  # (len(target_quantiles), horizon)

            results: dict[float, list[float]] = {}
            self.quantile_crossings_detected = 0

            for q_val in target_quantiles:
                results[q_val] = []

            # Step-by-step validation & monotonic isotonic rearrangement
            for step_idx in range(horizon):
                step_vals = [float(q_tensor[q_idx, step_idx]) for q_idx in range(len(target_quantiles))]

                # Verify monotonic ordering: P10 <= P20 <= P50 <= P80 <= P90
                if any(step_vals[i] > step_vals[i + 1] for i in range(len(step_vals) - 1)):
                    self.quantile_crossings_detected += 1
                    step_vals = sorted(step_vals)

                for q_idx, q_val in enumerate(target_quantiles):
                    results[q_val].append(round(max(0.1, step_vals[q_idx]), 2))

            return results

        except Exception as exc:
            logger.error("Inference execution failed inside Chronos-2: %s", exc)
            raise ModelUnavailableError(
                status="INFERENCE_UNAVAILABLE",
                detail=f"Inference error during Chronos-2 execution: {exc}",
            ) from exc
