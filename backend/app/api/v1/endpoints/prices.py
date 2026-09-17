"""
Price Observations Read-Only API Endpoints for AgriClutch.
Provides multi-dimensional querying for historical APMC mandi daily rates.
"""

from datetime import date
from typing import List, Optional

from app.config import settings
from app.db.seeds.seed_data import filter_seed_prices
from app.db.session import get_db
from app.repositories.price_repo import PriceObservationRepository
from app.schemas.price_observation import PriceObservationResponse
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/prices", tags=["Prices"])


@router.get(
    "",
    response_model=List[PriceObservationResponse],
    summary="Query Market Price Observations",
    description=(
        "Retrieve historical daily market price observations. "
        "Supports filtering by commodity, market, date range, with limit and offset pagination."
    ),
)
async def query_prices(
    response: Response,
    commodity: Optional[str] = Query(
        None, description="Commodity slug ID (e.g., 'tomato', 'onion', 'potato')"
    ),
    market: Optional[str] = Query(
        None, description="Canonical mandi ID (e.g., 'mandi_ch_49', 'mandi_dl_164')"
    ),
    start_date: Optional[date] = Query(
        None, description="Lower bound trading date (inclusive, YYYY-MM-DD)"
    ),
    end_date: Optional[date] = Query(
        None, description="Upper bound trading date (inclusive, YYYY-MM-DD)"
    ),
    limit: int = Query(100, ge=1, le=1000, description="Max records to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: AsyncSession = Depends(get_db),
) -> List[PriceObservationResponse]:
    """Returns price observations with explicit data mode semantics."""
    if settings.DATA_MODE == "demo":
        seed_records, seed_total = filter_seed_prices(
            commodity_id=commodity,
            market_id=market,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset,
        )
        response.headers["X-Total-Count"] = str(seed_total)
        response.headers["X-Limit"] = str(limit)
        response.headers["X-Offset"] = str(offset)
        response.headers["X-AgriClutch-Data-Mode"] = "DEMO"
        response.headers["X-AgriClutch-DataSource"] = "SYNTHETIC_TEST_FIXTURE"
        return seed_records

    try:
        repo = PriceObservationRepository(db)
        records, total = await repo.filter_prices(
            commodity_id=commodity,
            market_id=market,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset,
        )
        response.headers["X-Total-Count"] = str(total)
        response.headers["X-Limit"] = str(limit)
        response.headers["X-Offset"] = str(offset)
        response.headers["X-AgriClutch-Data-Mode"] = "DATABASE"
        response.headers["X-AgriClutch-DataSource"] = "POSTGRESQL"
        return [PriceObservationResponse.model_validate(r) for r in records]
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Database service is unavailable. Automatic fallback to synthetic data "
                "is disabled in database mode to prevent silent data contamination."
            ),
        ) from exc
