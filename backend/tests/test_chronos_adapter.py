"""
Unit Tests for Amazon Chronos-2 Foundation Model Adapter.
SIH26132 — Market Linkages and Price Discovery for Farmers.
"""

import pytest

from ml.forecasting.chronos_adapter import Chronos2Forecaster, ModelUnavailableError


def test_chronos_adapter_properties() -> None:
    adapter = Chronos2Forecaster()
    assert adapter.model_name == "chronos-2"
    assert adapter.parameter_count == "120M"
    assert adapter.model_version == "amazon/chronos-2"


def test_chronos_fail_closed_offline() -> None:
    """When offline/weights not present locally, fit/predict raises ModelUnavailableError."""
    adapter = Chronos2Forecaster(model_id="amazon/non-existent-chronos-checkpoint")

    with pytest.raises(ModelUnavailableError) as exc_info:
        adapter.predict_quantiles([25.0, 26.0, 27.0, 28.0, 29.0, 30.0], horizon=7)

    assert exc_info.value.status in ("MODEL_UNAVAILABLE", "INFERENCE_UNAVAILABLE")
    assert "non-existent-chronos-checkpoint" in exc_info.value.detail or "not present in local cache" in exc_info.value.detail


def test_chronos_context_length_check() -> None:
    """Chronos requires at least 5 context observations."""
    adapter = Chronos2Forecaster()
    with pytest.raises(ValueError, match="at least 5 observations"):
        adapter.fit([25.0, 26.0])
