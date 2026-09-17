"""
Commodity Repository for AgriClutch.
Encapsulates database access and query logic for commodities.
"""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.commodity import CommodityModel
from app.schemas.commodity import CommodityCreate


class CommodityRepository:
    """Repository handling CRUD operations for agricultural commodities."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, commodity_id: str) -> Optional[CommodityModel]:
        """Fetch a commodity by its unique slug ID."""
        result = await self.session.execute(
            select(CommodityModel).where(CommodityModel.id == commodity_id)
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Optional[CommodityModel]:
        """Fetch a commodity by exact standardized English name."""
        result = await self.session.execute(
            select(CommodityModel).where(CommodityModel.name == name)
        )
        return result.scalar_one_or_none()

    async def list_all(self, category: Optional[str] = None) -> List[CommodityModel]:
        """List commodities, optionally filtered by perishability category."""
        stmt = select(CommodityModel)
        if category:
            stmt = stmt.where(CommodityModel.category == category)
        stmt = stmt.order_by(CommodityModel.name)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def upsert(self, data: CommodityCreate) -> CommodityModel:
        """Create or update a commodity entry."""
        existing = await self.get_by_id(data.id)
        if existing:
            existing.name = data.name
            existing.hindi_name = data.hindi_name
            existing.category = data.category.value
            existing.default_spoilage_rate = data.default_spoilage_rate
            existing.max_ambient_holding_days = data.max_ambient_holding_days
            existing.standard_moisture_pct = data.standard_moisture_pct
            existing.price_unit = data.price_unit
            existing.weight_unit = data.weight_unit
            return existing
        else:
            model = CommodityModel(
                id=data.id,
                name=data.name,
                hindi_name=data.hindi_name,
                category=data.category.value,
                default_spoilage_rate=data.default_spoilage_rate,
                max_ambient_holding_days=data.max_ambient_holding_days,
                standard_moisture_pct=data.standard_moisture_pct,
                price_unit=data.price_unit,
                weight_unit=data.weight_unit,
            )
            self.session.add(model)
            return model

    async def bulk_upsert(self, items: List[CommodityCreate]) -> int:
        """Upsert a list of commodities and return count of processed items."""
        count = 0
        for item in items:
            await self.upsert(item)
            count += 1
        await self.session.flush()
        return count
