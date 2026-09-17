"""
AgriClutch Forecasting Domain Schemas & Pydantic v2 Contracts.
Defines typed request/response models for multi-horizon probabilistic price forecasts.
SIH26132 — Market Linkages and Price Discovery for Farmers.
"""

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ForecastRequest(BaseModel):
    """Payload contract for price forecast queries."""

    model_config = ConfigDict(extra="forbid")

    commodity_id: str = Field(
        ...,
        description="Commodity slug ID (e.g., 'tomato', 'onion', 'potato')",
        min_length=1,
    )
    market_id: str = Field(
        ...,
        description="Canonical mandi identifier (e.g., 'mandi_ch_49', 'mandi_dl_164')",
        min_length=1,
    )
    horizon: int = Field(
        default=14,
        ge=1,
        le=60,
        description="Forecast horizon in days forward (e.g., 7, 14, 28)",
    )
    quantiles: List[float] = Field(
        default=[0.1, 0.2, 0.5, 0.8, 0.9],
        description="Quantile distribution levels in (0, 1) to evaluate",
    )
    model_name: Optional[str] = Field(
        default="chronos-2",
        description="Forecasting model to execute ('chronos-2', 'gradient_boosting', 'statistical', 'seasonal_naive', 'naive')",
    )


class ForecastPoint(BaseModel):
    """Daily probabilistic forecast point across canonical quantiles."""

    model_config = ConfigDict(extra="forbid")

    date: str = Field(..., description="Calendar forecast date (YYYY-MM-DD)")
    q10: float = Field(..., description="10th percentile floor estimate (INR/kg)")
    q20: float = Field(..., description="20th percentile estimate (INR/kg)")
    q50: float = Field(..., description="50th percentile median forecast (INR/kg)")
    q80: float = Field(..., description="80th percentile estimate (INR/kg)")
    q90: float = Field(..., description="90th percentile ceiling estimate (INR/kg)")
    quantile_adjusted: bool = Field(
        default=False,
        description="Indicates whether monotonic rearrangement was applied to rectify crossing",
    )


class ForecastMetadata(BaseModel):
    """Auditable technical metadata for the forecasting engine."""

    model_config = ConfigDict(extra="forbid")

    model_name: str = Field(..., description="Identifier of the executing model engine")
    model_version: str = Field(..., description="Model version or Hugging Face checkpoint")
    parameter_count: str = Field(..., description="Approximate parameter count (e.g., '120M', '0')")
    context_length: int = Field(..., description="Number of historical sessions fed to the model")
    device: str = Field(..., description="Execution device ('cpu', 'cuda')")
    data_source: str = Field(..., description="Source provenance identifier of the context series")
    quantiles: List[float] = Field(..., description="Quantiles evaluated")
    is_demo: bool = Field(
        default=False,
        description="True if generated from synthetic demo fixtures rather than production database",
    )
    disclaimer: str = Field(
        default="Model forecast — not a guaranteed price.",
        description="Mandatory user-facing uncertainty disclaimer",
    )


class ForecastResponse(BaseModel):
    """Top-level response payload for agricultural price forecasts."""

    model_config = ConfigDict(extra="forbid")

    status: str = Field(default="SUCCESS", description="Execution status ('SUCCESS')")
    commodity_id: str = Field(..., description="Target commodity slug")
    market_id: str = Field(..., description="Target mandi ID")
    origin_date: str = Field(..., description="Last observed physical trading date (YYYY-MM-DD)")
    horizon: int = Field(..., description="Forecast horizon length in days")
    unit: str = Field(default="INR_PER_KG", description="Canonical currency and mass unit")
    points: List[ForecastPoint] = Field(..., description="Daily quantile predictions")
    metadata: ForecastMetadata = Field(..., description="Execution provenance and model metadata")
    generated_at: str = Field(..., description="ISO 8601 generation timestamp")


class ForecastInsufficiencyResponse(BaseModel):
    """Typed error returned when a series contains fewer than the required observations."""

    model_config = ConfigDict(extra="forbid")

    status: str = Field(default="INSUFFICIENT_HISTORY", description="Insufficiency indicator")
    commodity_id: str = Field(..., description="Target commodity slug")
    market_id: str = Field(..., description="Target mandi ID")
    available_records: int = Field(..., description="Number of valid historical records found")
    required_minimum: int = Field(..., description="Minimum historical sessions required (default 30)")
    detail: str = Field(..., description="Explanatory message and guidance")


class ModelUnavailableResponse(BaseModel):
    """Typed error returned when a requested model cannot be initialized on host."""

    model_config = ConfigDict(extra="forbid")

    status: str = Field(default="MODEL_UNAVAILABLE", description="Model unavailability indicator")
    model_name: str = Field(..., description="Requested model identifier")
    detail: str = Field(..., description="Reason for model unavailability")


class ModelEvaluationMetric(BaseModel):
    """Quantitative performance metrics on held-out temporal cross-validation folds."""

    model_config = ConfigDict(extra="forbid")

    model_name: str = Field(..., description="Model identifier evaluated")
    horizon: int = Field(..., description="Evaluation horizon in days")
    mae: float = Field(..., description="Mean Absolute Error (INR/kg)")
    rmse: float = Field(..., description="Root Mean Squared Error (INR/kg)")
    smape: float = Field(..., description="Symmetric Mean Absolute Percentage Error (%)")
    mase: float = Field(..., description="Mean Absolute Scaled Error relative to naive random walk")
    pinball_loss: float = Field(..., description="Average pinball quantile loss across evaluated quantiles")
    coverage_80: float = Field(..., description="Empirical coverage percentage of the P10-P90 interval")
    windows_evaluated: int = Field(..., description="Number of walk-forward rolling folds evaluated")


class ModelComparisonResponse(BaseModel):
    """Comparative benchmarking results across all candidate models."""

    model_config = ConfigDict(extra="forbid")

    commodity_id: str = Field(..., description="Evaluated commodity")
    market_id: str = Field(..., description="Evaluated mandi")
    horizon: int = Field(..., description="Evaluated horizon in days")
    evaluations: List[ModelEvaluationMetric] = Field(..., description="Metrics for each model")
    evaluation_strategy: str = Field(
        default="ROLLING_ORIGIN",
        description="Temporal cross-validation strategy employed",
    )
    split_count: int = Field(..., description="Total temporal evaluation folds executed")
    generated_at: str = Field(..., description="Evaluation timestamp")


class RegisteredModelInfo(BaseModel):
    """Descriptor for an available forecasting engine."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="Internal slug ID")
    name: str = Field(..., description="Display title")
    family: str = Field(..., description="'foundation' | 'statistical' | 'baseline' | 'ml'")
    description: str = Field(..., description="Brief description of methodology")
    is_available: bool = Field(..., description="Whether engine dependencies are operational on host")
    supported_quantiles: List[float] = Field(..., description="Supported quantiles")
