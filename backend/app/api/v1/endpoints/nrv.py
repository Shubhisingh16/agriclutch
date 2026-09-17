"""
AgriClutch REST API Endpoints for Net Realizable Value (NRV).
Translates price forecasts into economic realization without recommendation leakage.
SIH26132 — Market Linkages and Price Discovery for Farmers.
"""

from typing import Optional

from app.config import settings
from app.db.session import get_db
from app.schemas.nrv import (
    EconomicAssumptionsResponse,
    NRVMarketComparisonResponse,
    NRVResponse,
    NRVTimeComparisonResponse,
    SensitivityResponse,
)
from app.services.nrv_service import NRVService
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/nrv", tags=["Net Realizable Value Engine"])


def _apply_headers(response: Response, data_mode: Optional[str] = None) -> None:
    mode = data_mode or settings.DATA_MODE
    if mode.lower() == "demo":
        response.headers["X-AgriClutch-Data-Mode"] = "DEMO"
        response.headers["X-AgriClutch-DataSource"] = "DEMO_BENCHMARK_SEED"
    else:
        response.headers["X-AgriClutch-Data-Mode"] = "DATABASE"
        response.headers["X-AgriClutch-DataSource"] = "POSTGRESQL"


@router.get(
    "",
    response_model=NRVResponse,
    summary="Calculate Net Realizable Value for Produce Lot",
    description="Calculates gross revenue, itemized friction costs, and NRV distribution without recommendation.",
)
async def calculate_nrv(
    response: Response,
    commodity_id: str = Query(..., description="Commodity identifier (e.g. 'tomato', 'onion', 'potato')"),
    market_id: str = Query(..., description="Target mandi identifier (e.g. 'mandi_ch_49')"),
    quantity: float = Query(1000.0, description="Harvested lot quantity", gt=0),
    unit: str = Query("kg", description="Quantity unit ('kg', 'quintal', 'tonne')"),
    storage_days: int = Query(0, description="Storage holding duration in days", ge=0),
    storage_type: str = Query("ambient", description="Storage environment ('ambient', 'cold_storage')"),
    quality_grade: str = Query("FAQ", description="Produce quality grade ('FAQ', 'Grade_A', 'Grade_B')"),
    distance_km: Optional[float] = Query(None, description="Custom road transit distance in km"),
    forecast_model: str = Query("gradient_boosting", description="Forecasting model to consume"),
    scenario_type: str = Query("EXPECTED", description="Scenario parameter stress ('EXPECTED', 'CONSERVATIVE', 'OPTIMISTIC')"),
    data_mode: Optional[str] = Query(None, description="Operational data mode override ('demo', 'database')"),
    db: AsyncSession = Depends(get_db),
) -> NRVResponse:
    _apply_headers(response, data_mode)
    service = NRVService(db=db)
    return await service.calculate_nrv(
        commodity_id=commodity_id,
        market_id=market_id,
        quantity=quantity,
        unit=unit,
        storage_days=storage_days,
        storage_type=storage_type,
        quality_grade=quality_grade,
        distance_km=distance_km,
        forecast_model=forecast_model,
        scenario_type=scenario_type,
        data_mode=data_mode,
    )


@router.get(
    "/markets",
    response_model=NRVMarketComparisonResponse,
    summary="Compare Net Realizable Value Across Mandis",
    description="Evaluates economic realization across all candidate regional APMC mandis without declaring a winner.",
)
async def compare_markets(
    response: Response,
    commodity_id: str = Query("tomato", description="Commodity identifier"),
    quantity: float = Query(1000.0, description="Harvested quantity", gt=0),
    unit: str = Query("kg", description="Quantity unit ('kg', 'quintal', 'tonne')"),
    storage_days: int = Query(0, description="Holding duration in days", ge=0),
    storage_type: str = Query("ambient", description="Storage environment ('ambient', 'cold_storage')"),
    quality_grade: str = Query("FAQ", description="Quality grade ('FAQ', 'Grade_A', 'Grade_B')"),
    forecast_model: str = Query("gradient_boosting", description="Forecasting model to consume"),
    data_mode: Optional[str] = Query(None, description="Operational data mode override"),
    db: AsyncSession = Depends(get_db),
) -> NRVMarketComparisonResponse:
    _apply_headers(response, data_mode)
    service = NRVService(db=db)
    return await service.compare_markets(
        commodity_id=commodity_id,
        quantity=quantity,
        unit=unit,
        storage_days=storage_days,
        storage_type=storage_type,
        quality_grade=quality_grade,
        forecast_model=forecast_model,
        data_mode=data_mode,
    )


@router.get(
    "/times",
    response_model=NRVTimeComparisonResponse,
    summary="Compare Economic Realization Across Storage Horizons",
    description="Evaluates holding economics across t+0, t+3, t+7, t+14, and t+28 days without selecting a preferred time.",
)
async def compare_times(
    response: Response,
    commodity_id: str = Query("tomato", description="Commodity identifier"),
    market_id: str = Query("mandi_ch_49", description="Target mandi identifier"),
    quantity: float = Query(1000.0, description="Harvested quantity", gt=0),
    unit: str = Query("kg", description="Quantity unit"),
    storage_type: str = Query("ambient", description="Storage environment"),
    quality_grade: str = Query("FAQ", description="Quality grade"),
    forecast_model: str = Query("gradient_boosting", description="Forecasting model to consume"),
    data_mode: Optional[str] = Query(None, description="Operational data mode override"),
    db: AsyncSession = Depends(get_db),
) -> NRVTimeComparisonResponse:
    _apply_headers(response, data_mode)
    service = NRVService(db=db)
    return await service.compare_times(
        commodity_id=commodity_id,
        market_id=market_id,
        quantity=quantity,
        unit=unit,
        storage_type=storage_type,
        quality_grade=quality_grade,
        forecast_model=forecast_model,
        data_mode=data_mode,
    )


@router.get(
    "/sensitivity",
    response_model=SensitivityResponse,
    summary="Two-Variable Parameter Sensitivity Grid",
    description="Generates reproducible 3x3 sensitivity grid over orthogonal parameter shocks.",
)
async def calculate_sensitivity(
    response: Response,
    commodity_id: str = Query("tomato", description="Commodity identifier"),
    market_id: str = Query("mandi_ch_49", description="Target mandi identifier"),
    quantity: float = Query(1000.0, description="Harvested quantity", gt=0),
    unit: str = Query("kg", description="Quantity unit"),
    variable_x: str = Query("price", description="First variable ('price', 'transport', 'storage', 'loss')"),
    variable_y: str = Query("transport", description="Second variable ('price', 'transport', 'storage', 'loss')"),
    storage_days: int = Query(0, description="Storage days", ge=0),
    storage_type: str = Query("ambient", description="Storage type"),
    quality_grade: str = Query("FAQ", description="Quality grade"),
    forecast_model: str = Query("gradient_boosting", description="Forecasting model"),
    data_mode: Optional[str] = Query(None, description="Data mode override"),
    db: AsyncSession = Depends(get_db),
) -> SensitivityResponse:
    _apply_headers(response, data_mode)
    service = NRVService(db=db)
    return await service.calculate_sensitivity(
        commodity_id=commodity_id,
        market_id=market_id,
        quantity=quantity,
        unit=unit,
        variable_x=variable_x,
        variable_y=variable_y,
        storage_days=storage_days,
        storage_type=storage_type,
        quality_grade=quality_grade,
        forecast_model=forecast_model,
        data_mode=data_mode,
    )


@router.get(
    "/assumptions",
    response_model=EconomicAssumptionsResponse,
    summary="List Active Economic Assumptions & Provenance",
    description="Returns full catalog of active economic parameters with auditable provenance metadata.",
)
async def get_assumptions(
    response: Response,
    category: Optional[str] = Query(None, description="Filter by category ('transport', 'storage', 'handling', 'other', 'loss')"),
    data_mode: Optional[str] = Query(None, description="Data mode override"),
    db: AsyncSession = Depends(get_db),
) -> EconomicAssumptionsResponse:
    _apply_headers(response, data_mode)
    service = NRVService(db=db)
    return await service.get_assumptions(category=category, data_mode=data_mode)
