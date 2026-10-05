"""
AgriClutch REST API Endpoints for Buyer Discovery & Profiles.
Provides access to institutional, wholesale, and retail buyers, their procurement
specifications, spot demand orders, and audited empirical reliability metrics.
SIH26132 — Strengthening Market Linkages and Price Discovery for Farmers.
"""

from typing import List, Optional

from app.config import settings
from app.db.session import get_db
from app.schemas.buyer import (
    BuyerDemandResponse,
    BuyerRequirementResponse,
    BuyerResponse,
    ReliabilityMetricsResponse,
)
from app.services.buyer_service import BuyerService
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/buyers", tags=["Buyer Intelligence Engine"])


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
    response_model=List[BuyerResponse],
    summary="List Registered Produce Buyers",
    description="Retrieves active commercial produce buyers with optional category, location, and commodity filters.",
)
async def list_buyers(
    response: Response,
    buyer_type: Optional[str] = Query(None, description="Filter by buyer type (e.g. WHOLESALER, PROCESSOR, RETAIL_CHAIN, FPO_AGGREGATOR, EXPORTER, COOPERATIVE)"),
    location: Optional[str] = Query(None, description="Filter by location substring"),
    commodity_id: Optional[str] = Query(None, description="Filter by commodity handled (e.g. 'tomato', 'onion', 'potato')"),
    data_mode: Optional[str] = Query(None, description="Operational data mode override ('demo', 'database')"),
    db: AsyncSession = Depends(get_db),
) -> List[BuyerResponse]:
    _apply_headers(response, data_mode)
    service = BuyerService(db=db)
    return await service.list_buyers(
        buyer_type=buyer_type,
        location=location,
        commodity_id=commodity_id,
        data_mode=data_mode,
    )


@router.get(
    "/{buyer_id}",
    response_model=BuyerResponse,
    summary="Get Buyer Profile by Identifier",
    description="Retrieves a single buyer entity profile including registration provenance.",
)
async def get_buyer(
    buyer_id: str,
    response: Response,
    data_mode: Optional[str] = Query(None, description="Operational data mode override ('demo', 'database')"),
    db: AsyncSession = Depends(get_db),
) -> BuyerResponse:
    _apply_headers(response, data_mode)
    service = BuyerService(db=db)
    return await service.get_buyer(buyer_id=buyer_id, data_mode=data_mode)


@router.get(
    "/{buyer_id}/requirements",
    response_model=List[BuyerRequirementResponse],
    summary="Get Buyer Procurement Requirements & Commercial Terms",
    description="Retrieves documented commodity requirements, quality thresholds, delivery terms, and price bases.",
)
async def get_buyer_requirements(
    buyer_id: str,
    response: Response,
    commodity_id: Optional[str] = Query(None, description="Filter requirements by commodity identifier"),
    data_mode: Optional[str] = Query(None, description="Operational data mode override ('demo', 'database')"),
    db: AsyncSession = Depends(get_db),
) -> List[BuyerRequirementResponse]:
    _apply_headers(response, data_mode)
    service = BuyerService(db=db)
    return await service.get_buyer_requirements(buyer_id=buyer_id, commodity_id=commodity_id, data_mode=data_mode)


@router.get(
    "/{buyer_id}/demand",
    response_model=List[BuyerDemandResponse],
    summary="Get Active Buyer Demand Orders",
    description="Retrieves active spot procurement demand orders for a specific buyer.",
)
async def get_buyer_demand(
    buyer_id: str,
    response: Response,
    commodity_id: Optional[str] = Query(None, description="Filter demands by commodity identifier"),
    data_mode: Optional[str] = Query(None, description="Operational data mode override ('demo', 'database')"),
    db: AsyncSession = Depends(get_db),
) -> List[BuyerDemandResponse]:
    _apply_headers(response, data_mode)
    service = BuyerService(db=db)
    return await service.get_buyer_demands(buyer_id=buyer_id, commodity_id=commodity_id, data_mode=data_mode)


@router.get(
    "/{buyer_id}/reliability",
    response_model=ReliabilityMetricsResponse,
    summary="Get Buyer Empirical Reliability Audit",
    description="Calculates objective performance metrics strictly from immutable past transactions (N >= 3 gating).",
)
async def get_buyer_reliability(
    buyer_id: str,
    response: Response,
    data_mode: Optional[str] = Query(None, description="Operational data mode override ('demo', 'database')"),
    db: AsyncSession = Depends(get_db),
) -> ReliabilityMetricsResponse:
    _apply_headers(response, data_mode)
    service = BuyerService(db=db)
    return await service.get_buyer_reliability(buyer_id=buyer_id, data_mode=data_mode)
