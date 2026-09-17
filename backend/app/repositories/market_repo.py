"""
Market (Mandi) Repository for AgriClutch.
Encapsulates database access for APMC physical markets.
"""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.market import MarketModel
from app.schemas.market import MarketCreate


class MarketRepository:
    """Repository handling database operations for APMC mandis."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, market_id: str) -> Optional[MarketModel]:
        """Fetch a mandi by its canonical market ID."""
        result = await self.session.execute(
            select(MarketModel).where(MarketModel.id == market_id)
        )
        return result.scalar_one_or_none()

    async def get_by_apmc_code(self, apmc_code: int) -> Optional[MarketModel]:
        """Fetch a mandi by its Agmarknet APMC integer code."""
        result = await self.session.execute(
            select(MarketModel).where(MarketModel.apmc_code == apmc_code)
        )
        return result.scalar_one_or_none()

    async def list_all(
        self,
        state: Optional[str] = None,
        is_terminal: Optional[bool] = None,
    ) -> List[MarketModel]:
        """List mandis with optional state and terminal market filters."""
        stmt = select(MarketModel)
        if state:
            stmt = stmt.where(MarketModel.state.ilike(f"%{state}%"))
        if is_terminal is not None:
            stmt = stmt.where(MarketModel.is_terminal_market == is_terminal)
        stmt = stmt.order_by(MarketModel.name)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def upsert(self, data: MarketCreate) -> MarketModel:
        """Create or update a market record."""
        existing = await self.get_by_id(data.id)
        if existing:
            existing.apmc_code = data.apmc_code
            existing.name = data.name
            existing.state = data.state
            existing.district = data.district
            existing.latitude = data.latitude
            existing.longitude = data.longitude
            existing.is_terminal_market = data.is_terminal_market
            existing.dca_centre_id = data.dca_centre_id
            existing.source_market_id = data.source_market_id
            return existing
        else:
            model = MarketModel(
                id=data.id,
                apmc_code=data.apmc_code,
                name=data.name,
                state=data.state,
                district=data.district,
                latitude=data.latitude,
                longitude=data.longitude,
                is_terminal_market=data.is_terminal_market,
                dca_centre_id=data.dca_centre_id,
                source_market_id=data.source_market_id,
            )
            self.session.add(model)
            return model

    async def bulk_upsert(self, items: List[MarketCreate]) -> int:
        """Upsert multiple markets."""
        count = 0
        for item in items:
            await self.upsert(item)
            count += 1
        await self.session.flush()
        return count
