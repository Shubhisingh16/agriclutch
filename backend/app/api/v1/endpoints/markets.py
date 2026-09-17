"""
Markets (Mandis) Read-Only API Endpoints for AgriClutch.
Provides access to physical APMC markets, geospatial coordinates, and terminal market status.
"""

from typing import List, Optional

from app.config import settings
from app.db.seeds.seed_data import SEED_MARKETS, filter_seed_markets
from app.db.session import get_db
from app.repositories.market_repo import MarketRepository
from app.schemas.market import MarketResponse
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/markets", tags=["Markets"])


@router.get(
    "",
    response_model=List[MarketResponse],
    summary="List APMC Mandis",
    description="Retrieve registered APMC physical markets with optional state and terminal market filters.",
)
async def list_markets(
    response: Response,
    state: Optional[str] = Query(None, description="Filter by Indian State / UT name"),
    is_terminal: Optional[bool] = Query(
        None, description="Filter by terminal destination market status"
    ),
    db: AsyncSession = Depends(get_db),
) -> List[MarketResponse]:
    """Returns list of registered APMC mandis with explicit data mode semantics."""
    if settings.DATA_MODE == "demo":
        response.headers["X-AgriClutch-Data-Mode"] = "DEMO"
        response.headers["X-AgriClutch-DataSource"] = "SYNTHETIC_TEST_FIXTURE"
        return filter_seed_markets(state=state, is_terminal=is_terminal)

    try:
        repo = MarketRepository(db)
        models = await repo.list_all(state=state, is_terminal=is_terminal)
        response.headers["X-AgriClutch-Data-Mode"] = "DATABASE"
        response.headers["X-AgriClutch-DataSource"] = "POSTGRESQL"
        return [MarketResponse.model_validate(m) for m in models]
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Database service is unavailable. Automatic fallback to synthetic data "
                "is disabled in database mode to prevent silent data contamination."
            ),
        ) from exc


@router.get(
    "/{market_id}",
    response_model=MarketResponse,
    summary="Get Market Details",
    description="Fetch master attributes for a specific APMC mandi by canonical ID.",
)
async def get_market(
    market_id: str,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> MarketResponse:
    """Returns specific mandi with explicit data mode semantics."""
    if settings.DATA_MODE == "demo":
        for seed in SEED_MARKETS:
            if seed.id.lower() == market_id.lower():
                response.headers["X-AgriClutch-Data-Mode"] = "DEMO"
                response.headers["X-AgriClutch-DataSource"] = "SYNTHETIC_TEST_FIXTURE"
                return seed
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Market with ID '{market_id}' not found in demo fixture.",
        )

    try:
        repo = MarketRepository(db)
        model = await repo.get_by_id(market_id)
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Market with ID '{market_id}' not found.",
            )
        response.headers["X-AgriClutch-Data-Mode"] = "DATABASE"
        response.headers["X-AgriClutch-DataSource"] = "POSTGRESQL"
        return MarketResponse.model_validate(model)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Database service is unavailable. Automatic fallback to synthetic data "
                "is disabled in database mode."
            ),
        ) from exc
