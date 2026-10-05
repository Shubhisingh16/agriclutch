"""
AgriClutch REST API Endpoints for Regional Demand Aggregation & Concentration.
Analyzes active procurement demand volume, quality distributions, and market concentration (HHI).
SIH26132 — Strengthening Market Linkages and Price Discovery for Farmers.
"""

from typing import Optional

from app.config import settings
from app.db.session import get_db
from app.schemas.buyer import (
    DemandAggregateResponse,
    DemandDistributionResponse,
)
from app.services.buyer_service import BuyerService
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/demand", tags=["Demand Aggregation Engine"])


def _apply_headers(response: Response, data_mode: Optional[str] = None) -> None:
    mode = data_mode or settings.DATA_MODE
    if mode.lower() == "demo":
        response.headers["X-AgriClutch-Data-Mode"] = "DEMO"
        response.headers["X-AgriClutch-DataSource"] = "DEMO_BENCHMARK_SEED"
    else:
        response.headers["X-AgriClutch-Data-Mode"] = "DATABASE"
        response.headers["X-AgriClutch-DataSource"] = "POSTGRESQL"


@router.get(
    "/aggregate",
    response_model=DemandAggregateResponse,
    summary="Get Regional Demand Aggregate & Concentration Metrics",
    description="Aggregates active buyer demand volume with breakdown by quality, buyer type, and Herfindahl-Hirschman Index.",
)
async def get_demand_aggregate(
    response: Response,
    commodity_id: str = Query("tomato", description="Target commodity identifier (e.g. 'tomato', 'onion', 'potato')"),
    region: Optional[str] = Query(None, description="Optional regional filter (e.g. 'Chandigarh', 'Panchkula', 'Sonipat')"),
    data_mode: Optional[str] = Query(None, description="Operational data mode override ('demo', 'database')"),
    db: AsyncSession = Depends(get_db),
) -> DemandAggregateResponse:
    _apply_headers(response, data_mode)
    service = BuyerService(db=db)
    return await service.get_demand_aggregate(
        commodity_id=commodity_id,
        region=region,
        data_mode=data_mode,
    )


@router.get(
    "/distribution",
    response_model=DemandDistributionResponse,
    summary="Get Demand Price Dispersion Distribution",
    description="Calculates empirical price percentiles (P25, P50, P75) across active demand orders (N >= 3 gating).",
)
async def get_demand_distribution(
    response: Response,
    commodity_id: str = Query("tomato", description="Target commodity identifier (e.g. 'tomato', 'onion', 'potato')"),
    region: Optional[str] = Query(None, description="Optional regional filter"),
    data_mode: Optional[str] = Query(None, description="Operational data mode override ('demo', 'database')"),
    db: AsyncSession = Depends(get_db),
) -> DemandDistributionResponse:
    _apply_headers(response, data_mode)
    service = BuyerService(db=db)
    return await service.get_demand_distribution(
        commodity_id=commodity_id,
        region=region,
        data_mode=data_mode,
    )


@router.get(
    "/concentration",
    response_model=DemandAggregateResponse,
    summary="Get Demand Market Concentration (HHI) Analysis",
    description="Alias endpoint returning regional aggregation focusing on Herfindahl-Hirschman concentration index.",
)
async def get_demand_concentration(
    response: Response,
    commodity_id: str = Query("tomato", description="Target commodity identifier"),
    region: Optional[str] = Query(None, description="Optional regional filter"),
    data_mode: Optional[str] = Query(None, description="Operational data mode override ('demo', 'database')"),
    db: AsyncSession = Depends(get_db),
) -> DemandAggregateResponse:
    _apply_headers(response, data_mode)
    service = BuyerService(db=db)
    return await service.get_demand_aggregate(
        commodity_id=commodity_id,
        region=region,
        data_mode=data_mode,
    )
