"""
Forecasting Service Layer for AgriClutch.
Coordinates historical time-series extraction, sufficiency verification, model inference,
quantile monotonicity checking, and rolling-origin comparative evaluation.
SIH26132 — Market Linkages and Price Discovery for Farmers.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, List, Optional, Tuple, Union

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.seeds.forecast_seed_data import generate_demo_forecast_records
from app.repositories.price_repo import PriceObservationRepository
from app.schemas.forecast import (
    ForecastInsufficiencyResponse,
    ForecastMetadata,
    ForecastPoint,
    ForecastRequest,
    ForecastResponse,
    ModelComparisonResponse,
    ModelEvaluationMetric,
    ModelUnavailableResponse,
    RegisteredModelInfo,
)
from ml.forecasting.chronos_adapter import ModelUnavailableError
from ml.forecasting.dataset import TimeSeriesDataset
from ml.forecasting.registry import forecast_registry

logger = logging.getLogger("agriclutch.services.forecast")


class ForecastService:
    """
    Business logic and operational service for agricultural commodity price forecasting.
    Enforces clean-room IP, anti-fabrication fail-closed policies, and transparent provenance.
    """

    def __init__(self, db: Optional[AsyncSession] = None) -> None:
        self.db = db

    async def _fetch_history(
        self,
        commodity_id: str,
        market_id: str,
        data_mode: Optional[str] = None,
    ) -> Tuple[List[Any], bool]:
        """
        Retrieves historical records respecting explicit data mode semantics.

        Returns:
            Tuple of (records, is_demo).
        """
        mode = data_mode or settings.DATA_MODE
        if mode == "demo":
            demo_records: list[Any] = generate_demo_forecast_records(
                commodity_id=commodity_id,
                market_id=market_id,
                days=90,
            )
            return demo_records, True

        if self.db is None:
            raise RuntimeError("Database session required for production database mode.")

        repo = PriceObservationRepository(self.db)
        db_records, _ = await repo.filter_prices(
            commodity_id=commodity_id,
            market_id=market_id,
            limit=5000,
            offset=0,
        )
        # Sort ascending for dataset construction
        asc_records: list[Any] = sorted(db_records, key=lambda r: r.record_date)
        return asc_records, False

    async def generate_forecast(
        self,
        request: ForecastRequest,
        data_mode: Optional[str] = None,
    ) -> Union[ForecastResponse, ForecastInsufficiencyResponse, ModelUnavailableResponse]:
        """
        Executes probabilistic price forecast across requested horizon and quantiles.
        """
        records, is_demo = await self._fetch_history(
            commodity_id=request.commodity_id,
            market_id=request.market_id,
            data_mode=data_mode,
        )

        dataset = TimeSeriesDataset.from_records(
            records=records,
            commodity_id=request.commodity_id,
            market_id=request.market_id,
        )

        # 1. Data Sufficiency Verification Gate
        is_sufficient, count, msg = dataset.check_sufficiency(min_observations=30)
        if not is_sufficient:
            logger.warning(
                "Forecasting aborted: Insufficient history for %s in %s (%d records).",
                request.commodity_id,
                request.market_id,
                count,
            )
            return ForecastInsufficiencyResponse(
                commodity_id=request.commodity_id,
                market_id=request.market_id,
                available_records=count,
                required_minimum=30,
                detail=msg,
            )

        # 2. Model Resolution
        model_name = request.model_name or "chronos-2"
        try:
            model = forecast_registry.get_model(model_name)
        except KeyError:
            return ModelUnavailableResponse(
                model_name=model_name,
                detail=f"Model engine '{model_name}' is not registered in AgriClutch.",
            )

        # 3. Model Inference (Fail-Closed)
        quantiles = sorted(request.quantiles)
        try:
            q_preds = model.predict_quantiles(
                history_prices=dataset.prices,
                horizon=request.horizon,
                quantiles=quantiles,
                history_dates=dataset.dates,
            )
        except ModelUnavailableError as exc:
            logger.warning("Model '%s' is unavailable: %s", model_name, exc.detail)
            return ModelUnavailableResponse(
                model_name=model_name,
                detail=exc.detail,
            )
        except Exception as exc:
            logger.error("Unexpected error during %s inference: %s", model_name, exc)
            return ModelUnavailableResponse(
                model_name=model_name,
                detail=f"Inference execution failed: {exc}",
            )

        # 4. Generate Future Calendar Dates from Physical Origin
        assert dataset.origin_date is not None
        origin_d = datetime.strptime(dataset.origin_date, "%Y-%m-%d").date()

        points: List[ForecastPoint] = []
        crossings_detected = getattr(model, "quantile_crossings_detected", 0) > 0

        for step_idx in range(request.horizon):
            future_d = origin_d + timedelta(days=step_idx + 1)
            p10 = q_preds.get(0.10, [q_preds[quantiles[0]][step_idx]])[step_idx]
            p20 = q_preds.get(0.20, [q_preds[quantiles[min(1, len(quantiles) - 1)]][step_idx]])[step_idx]
            p50 = q_preds.get(0.50, [q_preds[quantiles[len(quantiles) // 2]][step_idx]])[step_idx]
            p80 = q_preds.get(0.80, [q_preds[quantiles[max(0, len(quantiles) - 2)]][step_idx]])[step_idx]
            p90 = q_preds.get(0.90, [q_preds[quantiles[-1]][step_idx]])[step_idx]

            points.append(
                ForecastPoint(
                    date=future_d.isoformat(),
                    q10=round(p10, 2),
                    q20=round(p20, 2),
                    q50=round(p50, 2),
                    q80=round(p80, 2),
                    q90=round(p90, 2),
                    quantile_adjusted=crossings_detected,
                )
            )

        # 5. Metadata Assembly
        device = getattr(model, "device", "cpu")
        metadata = ForecastMetadata(
            model_name=model.model_name,
            model_version=model.model_version,
            parameter_count=model.parameter_count,
            context_length=len(dataset.prices),
            device=device,
            data_source="SYNTHETIC_DEMO_FIXTURE" if is_demo else "POSTGRESQL_TIMESCALE",
            quantiles=quantiles,
            is_demo=is_demo,
            disclaimer="Model forecast — not a guaranteed price.",
        )

        return ForecastResponse(
            status="SUCCESS",
            commodity_id=request.commodity_id,
            market_id=request.market_id,
            origin_date=dataset.origin_date,
            horizon=request.horizon,
            unit="INR_PER_KG",
            points=points,
            metadata=metadata,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    def get_registered_models(self) -> List[RegisteredModelInfo]:
        """Returns catalog of all registered forecasting engines."""
        raw_list = forecast_registry.list_models()
        return [RegisteredModelInfo(**item) for item in raw_list]

    async def compare_models(
        self,
        commodity_id: str,
        market_id: str,
        horizon: int = 14,
        data_mode: Optional[str] = None,
    ) -> Union[ModelComparisonResponse, ForecastInsufficiencyResponse]:
        """
        Runs rolling-origin walk-forward evaluation across all available models.
        """
        records, _ = await self._fetch_history(
            commodity_id=commodity_id,
            market_id=market_id,
            data_mode=data_mode,
        )
        dataset = TimeSeriesDataset.from_records(
            records=records,
            commodity_id=commodity_id,
            market_id=market_id,
        )

        is_sufficient, count, msg = dataset.check_sufficiency(min_observations=30)
        if not is_sufficient:
            return ForecastInsufficiencyResponse(
                commodity_id=commodity_id,
                market_id=market_id,
                available_records=count,
                required_minimum=30,
                detail=msg,
            )

        raw_eval = forecast_registry.evaluate_all(
            dataset=dataset,
            horizon=horizon,
            max_splits=3,
        )

        metrics = [ModelEvaluationMetric(**m) for m in raw_eval["evaluations"]]
        return ModelComparisonResponse(
            commodity_id=commodity_id,
            market_id=market_id,
            horizon=horizon,
            evaluations=metrics,
            evaluation_strategy=raw_eval["evaluation_strategy"],
            split_count=raw_eval["split_count"],
            generated_at=raw_eval["generated_at"],
        )
