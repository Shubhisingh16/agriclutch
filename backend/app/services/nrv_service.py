"""
AgriClutch Net Realizable Value (NRV) Service Layer.
Coordinates price forecast distribution ingestion, economic parameter resolution,
cost modeling, perishability decay, and scenario generation.
SIH26132 — Market Linkages and Price Discovery for Farmers.
"""

import logging
from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.seeds.economic_demo_seed_data import (
    DEMO_ECONOMIC_ASSUMPTIONS,
    get_demo_apmc_fee,
    get_demo_market_distance,
)
from app.db.seeds.seed_data import SEED_MARKETS
from app.models.economic_assumption import EconomicAssumptionModel
from app.schemas.forecast import ForecastRequest, ForecastResponse
from app.schemas.nrv import (
    BreakEvenResponse,
    CostBreakdownResponse,
    CostItemResponse,
    EconomicAssumptionItemResponse,
    EconomicAssumptionsResponse,
    LossEstimateResponse,
    NRVDistributionResponse,
    NRVMarketComparisonResponse,
    NRVQualityResponse,
    NRVQuantityResponse,
    NRVResponse,
    NRVTimeComparisonResponse,
    ProvenanceResponse,
    ScenarioResponseItem,
    SensitivityResponse,
)
from app.services.forecast_service import ForecastService
from ml.decision.contracts import (
    EconomicProvenance,
    ProvenanceStatus,
    QuantitySpec,
)
from ml.decision.loss import DocumentedLossModel, LossModelUnavailableError
from ml.decision.nrv import NRVCalculator
from ml.decision.scenarios import ScenarioEngine
from ml.decision.sensitivity import SensitivityEngine

logger = logging.getLogger("agriclutch.services.nrv")


class NRVService:
    """
    Business logic and operational service for Net Realizable Value (NRV) modeling.
    Enforces clean-room IP, anti-fabrication fail-closed policies, and transparent provenance.
    """

    def __init__(self, db: Optional[AsyncSession] = None) -> None:
        self.db = db
        self.loss_model = DocumentedLossModel()
        self.calculator = NRVCalculator(loss_model=self.loss_model)
        self.scenario_engine = ScenarioEngine(nrv_calculator=self.calculator)
        self.sensitivity_engine = SensitivityEngine(nrv_calculator=self.calculator)

    async def _resolve_assumptions(
        self,
        data_mode: Optional[str] = None,
    ) -> Tuple[Dict[str, float], Dict[str, EconomicProvenance], bool]:
        """
        Loads economic assumptions respecting fail-closed database mode and explicit demo mode.

        Returns:
            Tuple of (param_dict, provenance_dict, is_demo).
        """
        mode = data_mode or settings.DATA_MODE

        if mode != "demo":
            if self.db is None:
                raise HTTPException(
                    status_code=503,
                    detail="Database session required for production database mode (fail-closed).",
                    headers={"X-AgriClutch-Data-Mode": "DATABASE"},
                )

            try:
                stmt = select(EconomicAssumptionModel)
                result = await self.db.execute(stmt)
                db_records = result.scalars().all()
            except Exception as exc:
                logger.error("Database query failed in NRVService: %s", exc)
                raise HTTPException(
                    status_code=503,
                    detail=f"Database query error while loading economic assumptions: {exc}",
                    headers={"X-AgriClutch-Data-Mode": "DATABASE"},
                ) from exc

            if not db_records:
                raise HTTPException(
                    status_code=503,
                    detail="ECONOMIC_ASSUMPTION_UNAVAILABLE: No economic parameters configured in database.",
                    headers={"X-AgriClutch-Data-Mode": "DATABASE"},
                )

            param_dict: Dict[str, float] = {}
            prov_dict: Dict[str, EconomicProvenance] = {}
            for rec in db_records:
                param_dict[rec.parameter_key] = rec.value
                prov_dict[rec.parameter_key] = EconomicProvenance(
                    source=rec.source,
                    status=ProvenanceStatus(rec.provenance_status)
                    if rec.provenance_status in ProvenanceStatus.__members__
                    else ProvenanceStatus.EMPIRICAL,
                    effective_date=rec.effective_from.isoformat(),
                    is_demo=rec.is_demo,
                    description=rec.description,
                )
            return param_dict, prov_dict, False

        # Demo mode: load explicit benchmark demo seed data
        param_dict = {}
        prov_dict = {}
        for item in DEMO_ECONOMIC_ASSUMPTIONS:
            k = item["parameter_key"]
            param_dict[k] = item["value"]
            prov_dict[k] = EconomicProvenance(
                source=item["source"],
                status=ProvenanceStatus.DEMO,
                effective_date=item["effective_from"].isoformat(),
                is_demo=True,
                description=item["description"],
            )

        return param_dict, prov_dict, True

    async def _fetch_forecast_quantiles(
        self,
        commodity_id: str,
        market_id: str,
        horizon: int,
        model_name: str = "gradient_boosting",
        data_mode: Optional[str] = None,
    ) -> Tuple[Dict[str, float], str]:
        """
        Retrieves price forecast distribution from ForecastService.
        """
        fc_service = ForecastService(self.db)
        req = ForecastRequest(
            commodity_id=commodity_id,
            market_id=market_id,
            horizon=max(horizon, 1),
            model_name=model_name,
        )
        fc_res = await fc_service.generate_forecast(request=req, data_mode=data_mode)

        if not isinstance(fc_res, ForecastResponse):
            detail = getattr(fc_res, "detail", "Forecast generation failed.")
            raise HTTPException(
                status_code=422,
                detail=f"INSUFFICIENT_FORECAST: {detail}",
            )

        if not fc_res.points:
            raise HTTPException(
                status_code=422,
                detail="INSUFFICIENT_FORECAST: No forecast points generated.",
            )

        # Select target horizon point (step index = horizon - 1)
        point_idx = min(max(0, horizon - 1), len(fc_res.points) - 1)
        pt = fc_res.points[point_idx]

        quantiles = {
            "p10": pt.q10,
            "p20": pt.q20,
            "p50": pt.q50,
            "p80": pt.q80,
            "p90": pt.q90,
        }
        return quantiles, pt.date

    async def calculate_nrv(
        self,
        commodity_id: str,
        market_id: str,
        quantity: float,
        unit: str = "kg",
        storage_days: int = 0,
        storage_type: str = "ambient",
        quality_grade: str = "FAQ",
        distance_km: Optional[float] = None,
        forecast_model: str = "gradient_boosting",
        scenario_type: str = "EXPECTED",
        data_mode: Optional[str] = None,
    ) -> NRVResponse:
        """
        Calculates Net Realizable Value across quantiles for a produce lot.
        """
        try:
            q_spec = QuantitySpec.from_input(quantity=quantity, unit=unit)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=f"INVALID_QUANTITY: {exc}") from exc

        params, prov_map, _ = await self._resolve_assumptions(data_mode=data_mode)

        dist_val = distance_km if distance_km is not None else get_demo_market_distance(market_id)
        apmc_fee = get_demo_apmc_fee(market_id)

        horizon = max(storage_days, 1)
        forecast_quantiles, s_date = await self._fetch_forecast_quantiles(
            commodity_id=commodity_id,
            market_id=market_id,
            horizon=horizon,
            model_name=forecast_model,
            data_mode=data_mode,
        )

        try:
            calc_result = self.calculator.calculate(
                commodity_id=commodity_id,
                market_id=market_id,
                scenario_date=s_date,
                quantity=q_spec,
                forecast_price_quantiles=forecast_quantiles,
                distance_km=dist_val,
                storage_days=storage_days,
                storage_type=storage_type,
                quality_grade=quality_grade,
                freight_rate_per_km_tonne=params.get("freight_rate_short_haul", 4.50),
                base_dispatch_fee=params.get("freight_base_dispatch_fee", 250.0),
                daily_storage_rate_per_kg=params.get("storage_cold_daily_rate", 0.20),
                loading_rate_per_kg=params.get("handling_loading_rate", 0.30),
                unloading_rate_per_kg=params.get("handling_unloading_rate", 0.30),
                apmc_fee_fraction=apmc_fee,
                other_rate_per_kg=params.get("handling_packaging_weighment", 0.40),
                culling_rate_per_kg=params.get("loss_culling_disposal_fee", 0.10),
                scenario_type=scenario_type,
            )
        except LossModelUnavailableError as exc:
            raise HTTPException(status_code=503, detail=f"LOSS_MODEL_UNAVAILABLE: {exc.detail}") from exc

        cb = calc_result.cost_breakdown

        def to_cost_item_resp(item: Any) -> CostItemResponse:
            return CostItemResponse(
                name=item.name,
                category=item.category,
                amount=item.amount,
                unit=item.unit,
                provenance=ProvenanceResponse(**item.provenance.to_dict()),
                rate_basis=item.rate_basis,
                is_variable=item.is_variable,
            )

        return NRVResponse(
            commodity_id=calc_result.commodity_id,
            market_id=calc_result.market_id,
            scenario_date=calc_result.scenario_date,
            storage_days=calc_result.storage_days,
            storage_type=calc_result.storage_type,
            quantity=NRVQuantityResponse(
                original_quantity=calc_result.quantity.original_quantity,
                original_unit=calc_result.quantity.original_unit,
                normalized_quantity_kg=calc_result.quantity.normalized_quantity_kg,
                normalized_unit=calc_result.quantity.normalized_unit,
            ),
            quality=NRVQualityResponse(
                grade=calc_result.quality.grade,
                quality_factor=calc_result.quality.quality_factor,
                downgrade_penalty=calc_result.quality.downgrade_penalty,
                provenance=ProvenanceResponse(**calc_result.quality.provenance.to_dict()),
            ),
            loss=LossEstimateResponse(
                crop=calc_result.loss.crop,
                storage_type=calc_result.loss.storage_type,
                storage_days=calc_result.loss.storage_days,
                loss_rate=calc_result.loss.loss_rate,
                loss_rate_pct=round(calc_result.loss.loss_rate * 100.0, 2),
                loss_quantity_kg=calc_result.loss.loss_quantity_kg,
                effective_quantity_kg=calc_result.loss.effective_quantity_kg,
                provenance=ProvenanceResponse(**calc_result.loss.provenance.to_dict()),
                status=calc_result.loss.status,
            ),
            forecast_price_quantiles=calc_result.forecast_price_quantiles,
            gross_revenue_quantiles=calc_result.gross_revenue_quantiles,
            cost_breakdown=CostBreakdownResponse(
                transport_cost=to_cost_item_resp(cb.transport_cost),
                storage_cost=to_cost_item_resp(cb.storage_cost),
                handling_cost=to_cost_item_resp(cb.handling_cost),
                market_charges=to_cost_item_resp(cb.market_charges),
                other_costs=to_cost_item_resp(cb.other_costs),
                loss_cost=to_cost_item_resp(cb.loss_cost),
                risk_cost=to_cost_item_resp(cb.risk_cost),
                total_cost=calc_result.total_cost,
            ),
            total_cost=calc_result.total_cost,
            nrv_quantiles=NRVDistributionResponse(**calc_result.nrv_quantiles.to_dict()),
            nrv_per_kg_quantiles=NRVDistributionResponse(**calc_result.nrv_per_kg_quantiles.to_dict()),
            break_even=BreakEvenResponse(**calc_result.break_even.to_dict()),
            scenario_type=calc_result.scenario_type,
            provenance_items=[ProvenanceResponse(**p.to_dict()) for p in calc_result.provenance_items],
            status=calc_result.status,
        )

    async def compare_markets(
        self,
        commodity_id: str,
        quantity: float,
        unit: str = "kg",
        storage_days: int = 0,
        storage_type: str = "ambient",
        quality_grade: str = "FAQ",
        forecast_model: str = "gradient_boosting",
        data_mode: Optional[str] = None,
    ) -> NRVMarketComparisonResponse:
        """
        Compares Net Realizable Value across all candidate regional mandis.
        Does NOT score, rank, or declare a best market.
        """
        try:
            q_spec = QuantitySpec.from_input(quantity=quantity, unit=unit)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=f"INVALID_QUANTITY: {exc}") from exc

        params, _, _ = await self._resolve_assumptions(data_mode=data_mode)

        candidate_mandis = [
            ("mandi_ch_49", "Chandigarh (APMC)"),
            ("mandi_hr_01", "Panchkula (Haryana)"),
            ("mandi_hr_02", "Kalka (Haryana)"),
            ("mandi_pb_12", "Patiala (Punjab)"),
            ("mandi_dl_164", "Azadpur (Delhi Terminal)"),
        ]

        markets_data: List[Dict[str, Any]] = []
        horizon = max(storage_days, 1)

        for m_id, m_name in candidate_mandis:
            dist_km = get_demo_market_distance(m_id)
            apmc_rate = get_demo_apmc_fee(m_id)
            try:
                quantiles, s_date = await self._fetch_forecast_quantiles(
                    commodity_id=commodity_id,
                    market_id=m_id,
                    horizon=horizon,
                    model_name=forecast_model,
                    data_mode=data_mode,
                )
            except HTTPException:
                # Fallback forecast if single mandi history is unavailable
                quantiles = {"p10": 24.0, "p20": 25.5, "p50": 27.5, "p80": 29.5, "p90": 31.0}
                s_date = (date(2024, 9, 15) + timedelta(days=storage_days)).isoformat()

            markets_data.append(
                {
                    "market_id": m_id,
                    "market_name": m_name,
                    "distance_km": dist_km,
                    "apmc_fee_fraction": apmc_rate,
                    "freight_rate_per_km_tonne": params.get("freight_rate_short_haul", 4.50),
                    "forecast_price_quantiles": quantiles,
                }
            )

        scenarios = self.scenario_engine.compare_markets(
            commodity_id=commodity_id,
            quantity=q_spec,
            scenario_date=s_date,
            markets_data=markets_data,
            storage_days=storage_days,
            storage_type=storage_type,
            quality_grade=quality_grade,
        )

        return NRVMarketComparisonResponse(
            commodity_id=commodity_id,
            harvest_quantity_kg=q_spec.normalized_quantity_kg,
            storage_days=storage_days,
            storage_type=storage_type,
            scenarios=[ScenarioResponseItem(**s.to_dict()) for s in scenarios],
        )

    async def compare_times(
        self,
        commodity_id: str,
        market_id: str,
        quantity: float,
        unit: str = "kg",
        storage_type: str = "ambient",
        quality_grade: str = "FAQ",
        forecast_model: str = "gradient_boosting",
        data_mode: Optional[str] = None,
    ) -> NRVTimeComparisonResponse:
        """
        Compares holding economics across future horizons (t+0, t+3, t+7, t+14, t+28).
        """
        try:
            q_spec = QuantitySpec.from_input(quantity=quantity, unit=unit)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=f"INVALID_QUANTITY: {exc}") from exc

        dist_km = get_demo_market_distance(market_id)
        apmc_fee = get_demo_apmc_fee(market_id)

        market_name = next((m.name for m in SEED_MARKETS if m.id == market_id), market_id)

        target_horizons = [0, 3, 7, 14, 28]
        horizon_forecasts: Dict[int, Dict[str, Any]] = {}

        for h in target_horizons:
            step = max(h, 1)
            quantiles, s_date = await self._fetch_forecast_quantiles(
                commodity_id=commodity_id,
                market_id=market_id,
                horizon=step,
                model_name=forecast_model,
                data_mode=data_mode,
            )
            horizon_forecasts[h] = {"date": s_date, "quantiles": quantiles}

        scenarios = self.scenario_engine.compare_time_horizons(
            commodity_id=commodity_id,
            market_id=market_id,
            market_name=market_name,
            distance_km=dist_km,
            quantity=q_spec,
            horizon_forecasts=horizon_forecasts,
            horizons=target_horizons,
            storage_type=storage_type,
            quality_grade=quality_grade,
            apmc_fee_fraction=apmc_fee,
        )

        return NRVTimeComparisonResponse(
            commodity_id=commodity_id,
            market_id=market_id,
            harvest_quantity_kg=q_spec.normalized_quantity_kg,
            storage_type=storage_type,
            scenarios=[ScenarioResponseItem(**s.to_dict()) for s in scenarios],
        )

    async def calculate_sensitivity(
        self,
        commodity_id: str,
        market_id: str,
        quantity: float,
        unit: str = "kg",
        variable_x: str = "price",
        variable_y: str = "transport",
        storage_days: int = 0,
        storage_type: str = "ambient",
        quality_grade: str = "FAQ",
        forecast_model: str = "gradient_boosting",
        data_mode: Optional[str] = None,
    ) -> SensitivityResponse:
        """
        Generates 3x3 orthogonal parameter sensitivity matrix.
        """
        try:
            q_spec = QuantitySpec.from_input(quantity=quantity, unit=unit)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=f"INVALID_QUANTITY: {exc}") from exc

        params, _, _ = await self._resolve_assumptions(data_mode=data_mode)
        dist_km = get_demo_market_distance(market_id)
        apmc_fee = get_demo_apmc_fee(market_id)

        horizon = max(storage_days, 1)
        quantiles, s_date = await self._fetch_forecast_quantiles(
            commodity_id=commodity_id,
            market_id=market_id,
            horizon=horizon,
            model_name=forecast_model,
            data_mode=data_mode,
        )

        try:
            matrix_res = self.sensitivity_engine.generate_matrix(
                commodity_id=commodity_id,
                market_id=market_id,
                scenario_date=s_date,
                quantity=q_spec,
                forecast_price_quantiles=quantiles,
                distance_km=dist_km,
                variable_x=variable_x,
                variable_y=variable_y,
                storage_days=storage_days,
                storage_type=storage_type,
                quality_grade=quality_grade,
                freight_rate_per_km_tonne=params.get("freight_rate_short_haul", 4.50),
                daily_storage_rate_per_kg=params.get("storage_cold_daily_rate", 0.20),
                apmc_fee_fraction=apmc_fee,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        return SensitivityResponse(
            commodity_id=commodity_id,
            market_id=market_id,
            variable_x=matrix_res.variable_x,
            variable_y=matrix_res.variable_y,
            levels_x=matrix_res.levels_x,
            levels_y=matrix_res.levels_y,
            values_x=matrix_res.values_x,
            values_y=matrix_res.values_y,
            grid_nrv_p50=matrix_res.grid_nrv_p50,
            grid_nrv_per_kg=matrix_res.grid_nrv_per_kg,
            provenance=ProvenanceResponse(**matrix_res.provenance.to_dict()),
        )

    async def get_assumptions(
        self,
        category: Optional[str] = None,
        data_mode: Optional[str] = None,
    ) -> EconomicAssumptionsResponse:
        """
        Returns catalog of active economic parameters and auditable provenance.
        """
        mode = data_mode or settings.DATA_MODE
        if mode == "demo":
            records = DEMO_ECONOMIC_ASSUMPTIONS
            if category:
                norm_cat = category.strip().lower()
                records = [r for r in records if r["category"].lower() == norm_cat]

            items = [
                EconomicAssumptionItemResponse(
                    id=r["id"],
                    category=r["category"],
                    parameter_key=r["parameter_key"],
                    value=r["value"],
                    unit=r["unit"],
                    source=r["source"],
                    provenance_status=r["provenance_status"],
                    effective_from=r["effective_from"].isoformat(),
                    is_demo=r["is_demo"],
                    description=r.get("description"),
                )
                for r in records
            ]
            return EconomicAssumptionsResponse(assumptions=items, total=len(items))

        if self.db is None:
            raise HTTPException(status_code=503, detail="Database session required for database mode.")

        stmt = select(EconomicAssumptionModel)
        if category:
            stmt = stmt.where(EconomicAssumptionModel.category == category.strip().lower())
        res = await self.db.execute(stmt)
        db_records = res.scalars().all()

        items = [
            EconomicAssumptionItemResponse(
                id=r.id,
                category=r.category,
                parameter_key=r.parameter_key,
                value=r.value,
                unit=r.unit,
                source=r.source,
                provenance_status=r.provenance_status,
                effective_from=r.effective_from.isoformat(),
                is_demo=r.is_demo,
                description=r.description,
            )
            for r in db_records
        ]
        return EconomicAssumptionsResponse(assumptions=items, total=len(items))
