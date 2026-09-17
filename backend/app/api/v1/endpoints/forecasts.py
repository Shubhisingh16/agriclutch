"""
Agricultural Commodity Price Forecasting API Endpoints for AgriClutch.
Exposes multi-horizon probabilistic forecasts, model metadata, and rolling-origin benchmarks.
SIH26132 — Market Linkages and Price Discovery for Farmers.
"""

from typing import List, Optional

from app.config import settings
from app.db.session import get_db
from app.schemas.forecast import (
    ForecastInsufficiencyResponse,
    ForecastRequest,
    ForecastResponse,
    ModelComparisonResponse,
    ModelUnavailableResponse,
    RegisteredModelInfo,
)
from app.services.forecast_service import ForecastService
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/forecasts", tags=["Forecasting"])


@router.get(
    "",
    response_model=ForecastResponse,
    responses={
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "model": ForecastInsufficiencyResponse,
            "description": "Insufficient trading history (fewer than 30 observations).",
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ModelUnavailableResponse,
            "description": "Requested model engine is unavailable or uninitialized on host.",
        },
    },
    summary="Generate Probabilistic Price Forecast",
    description=(
        "Produces multi-horizon quantile price forecasts P(y[t+h] | x[<=t]) for a given commodity "
        "and mandi. Strictly enforces data sufficiency (>= 30 observations) and returns "
        "auditable probability distributions (P10, P20, P50, P80, P90)."
    ),
)
async def get_price_forecast(
    response: Response,
    commodity: str = Query(..., description="Commodity slug ID (e.g., 'tomato', 'onion', 'potato')"),
    market: str = Query(..., description="Canonical APMC mandi ID (e.g., 'mandi_ch_49', 'mandi_dl_164')"),
    horizon: int = Query(14, ge=1, le=60, description="Forecast horizon in days (e.g., 7, 14, 28)"),
    model: str = Query("chronos-2", description="Model engine ('chronos-2', 'gradient_boosting', 'statistical', 'seasonal_naive', 'naive')"),
    quantiles: Optional[str] = Query(None, description="Comma-delimited float quantiles, default: 0.1,0.2,0.5,0.8,0.9"),
    db: AsyncSession = Depends(get_db),
) -> ForecastResponse:
    parsed_quantiles = [0.1, 0.2, 0.5, 0.8, 0.9]
    if quantiles:
        try:
            parsed_quantiles = [float(q.strip()) for q in quantiles.split(",") if q.strip()]
        except ValueError as err:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid quantiles format. Must be comma-delimited floats between 0 and 1.",
            ) from err

    req = ForecastRequest(
        commodity_id=commodity,
        market_id=market,
        horizon=horizon,
        quantiles=parsed_quantiles,
        model_name=model,
    )

    service = ForecastService(db=db if settings.DATA_MODE != "demo" else None)
    result = await service.generate_forecast(request=req)

    if isinstance(result, ForecastInsufficiencyResponse):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=result.model_dump(),
            headers={"X-AgriClutch-Data-Sufficiency": "INSUFFICIENT"},
        )

    if isinstance(result, ModelUnavailableResponse):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=result.model_dump(),
            headers={"X-AgriClutch-Model-Status": "UNAVAILABLE"},
        )

    # Success
    response.headers["X-AgriClutch-Data-Mode"] = "DEMO" if result.metadata.is_demo else "DATABASE"
    response.headers["X-AgriClutch-DataSource"] = result.metadata.data_source
    response.headers["X-AgriClutch-Model"] = result.metadata.model_name
    return result


@router.get(
    "/models",
    response_model=List[RegisteredModelInfo],
    summary="List Registered Forecasting Engines",
    description="Returns metadata and live availability status for all supported forecasting engines and baselines.",
)
def list_forecasting_models() -> List[RegisteredModelInfo]:
    service = ForecastService()
    return service.get_registered_models()


@router.get(
    "/evaluation",
    response_model=ModelComparisonResponse,
    responses={
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "model": ForecastInsufficiencyResponse,
            "description": "Insufficient history to perform temporal cross-validation folds.",
        }
    },
    summary="Compare Model Performance via Rolling-Origin Evaluation",
    description=(
        "Executes strictly chronological walk-forward rolling-origin evaluation across all available "
        "models on identical folds, returning MAE, RMSE, sMAPE, MASE, Pinball loss, and 80% coverage."
    ),
)
async def compare_forecast_models(
    commodity: str = Query(..., description="Commodity slug ID"),
    market: str = Query(..., description="Canonical APMC mandi ID"),
    horizon: int = Query(14, ge=1, le=30, description="Evaluation horizon in days"),
    db: AsyncSession = Depends(get_db),
) -> ModelComparisonResponse:
    service = ForecastService(db=db if settings.DATA_MODE != "demo" else None)
    result = await service.compare_models(
        commodity_id=commodity,
        market_id=market,
        horizon=horizon,
    )

    if isinstance(result, ForecastInsufficiencyResponse):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=result.model_dump(),
        )

    return result
