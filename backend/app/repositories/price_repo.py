"""
Price Observation Repository for AgriClutch.
Encapsulates database access and high-performance querying for historical market rates.
"""

from datetime import date
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.price_observation import PriceObservationModel
from app.schemas.price_observation import PriceObservationCreate


class PriceObservationRepository:
    """Repository handling database operations for daily market price records."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, observation_id: UUID) -> Optional[PriceObservationModel]:
        """Fetch a price observation by its surrogate UUID."""
        result = await self.session.execute(
            select(PriceObservationModel).where(
                PriceObservationModel.observation_id == observation_id
            )
        )
        return result.scalar_one_or_none()

    async def filter_prices(
        self,
        commodity_id: Optional[str] = None,
        market_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[PriceObservationModel], int]:
        """
        Query price observations with multi-dimensional filters and pagination.

        Returns:
            Tuple of (records_list, total_count).
        """
        stmt = select(PriceObservationModel)
        count_stmt = select(func.count()).select_from(PriceObservationModel)

        if commodity_id:
            stmt = stmt.where(PriceObservationModel.commodity_id == commodity_id)
            count_stmt = count_stmt.where(PriceObservationModel.commodity_id == commodity_id)

        if market_id:
            stmt = stmt.where(PriceObservationModel.market_id == market_id)
            count_stmt = count_stmt.where(PriceObservationModel.market_id == market_id)

        if start_date:
            stmt = stmt.where(PriceObservationModel.record_date >= start_date)
            count_stmt = count_stmt.where(PriceObservationModel.record_date >= start_date)

        if end_date:
            stmt = stmt.where(PriceObservationModel.record_date <= end_date)
            count_stmt = count_stmt.where(PriceObservationModel.record_date <= end_date)

        # Ordering: newest records first, then by market
        stmt = stmt.order_by(
            PriceObservationModel.record_date.desc(), PriceObservationModel.market_id
        )
        stmt = stmt.limit(limit).offset(offset)

        total_res = await self.session.execute(count_stmt)
        total_count = total_res.scalar() or 0

        result = await self.session.execute(stmt)
        records = list(result.scalars().all())

        return records, total_count

    async def bulk_insert(self, records: List[PriceObservationCreate]) -> int:
        """
        Inserts a batch of normalized price observations.
        """
        count = 0
        for item in records:
            model = PriceObservationModel(
                observation_id=item.observation_id,
                source_name=item.source_name,
                source_record_id=item.source_record_id,
                source_market_id=item.source_market_id,
                source_commodity_id=item.source_commodity_id,
                record_date=item.record_date,
                market_id=item.market_id,
                commodity_id=item.commodity_id,
                variety=item.variety,
                grade=item.grade,
                original_modal_price=item.original_modal_price,
                original_min_price=item.original_min_price,
                original_max_price=item.original_max_price,
                original_price_unit=item.original_price_unit,
                normalized_modal_price=item.normalized_modal_price,
                normalized_min_price=item.normalized_min_price,
                normalized_max_price=item.normalized_max_price,
                normalized_price_unit=item.normalized_price_unit,
                arrival_tonnes=item.arrival_tonnes,
                is_interpolated=item.is_interpolated,
                is_outlier=item.is_outlier,
            )
            self.session.add(model)
            count += 1
        await self.session.flush()
        return count
