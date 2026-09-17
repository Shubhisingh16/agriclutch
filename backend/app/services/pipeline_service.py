"""
Pipeline Service for AgriClutch.
Orchestrates raw data ingestion, column mapping, validation, normalization, and persistence.
"""

from typing import Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.commodity_repo import CommodityRepository
from app.repositories.market_repo import MarketRepository
from app.repositories.price_repo import PriceObservationRepository
from app.schemas.commodity import CommodityCreate, CropCategory
from app.schemas.market import MarketCreate
from app.schemas.price_observation import PriceObservationCreate
from app.schemas.validation import ValidationReport
from pipeline.cleaning.normalizer import DataNormalizer
from pipeline.ingestion.column_mapper import ColumnMapper
from pipeline.ingestion.csv_adapter import LocalCSVSourceAdapter
from pipeline.ingestion.market_resolver import MarketResolver, default_market_resolver
from pipeline.validation.validator import AgriDataValidator


class PipelineService:
    """
    Coordinates end-to-end data processing for agricultural observation files.
    Decouples parsing and validation from database persistence.
    """

    def __init__(
        self,
        market_resolver: Optional[MarketResolver] = None,
        validator: Optional[AgriDataValidator] = None,
        normalizer: Optional[DataNormalizer] = None,
    ) -> None:
        self.market_resolver = market_resolver or default_market_resolver
        self.validator = validator or AgriDataValidator(market_resolver=self.market_resolver)
        self.normalizer = normalizer or DataNormalizer(market_resolver=self.market_resolver)

    async def _ensure_prerequisites(
        self,
        session: AsyncSession,
        normalized_records: list[PriceObservationCreate],
    ) -> None:
        """
        Ensures foreign key targets (commodities and mandis) exist prior to observation insertion.
        Seeds standard metadata from the authoritative market resolver if absent.
        """
        comm_repo = CommodityRepository(session)
        market_repo = MarketRepository(session)

        # Standard baseline commodities definitions
        standard_crops = {
            "tomato": CommodityCreate(
                id="tomato",
                name="Tomato",
                hindi_name="टमाटर",
                category=CropCategory.PERISHABLE,
                default_spoilage_rate=0.08,
                max_ambient_holding_days=4,
                standard_moisture_pct=94.0,
            ),
            "onion": CommodityCreate(
                id="onion",
                name="Onion",
                hindi_name="प्याज़",
                category=CropCategory.SEMI_PERISHABLE,
                default_spoilage_rate=0.015,
                max_ambient_holding_days=60,
                standard_moisture_pct=86.0,
            ),
            "potato": CommodityCreate(
                id="potato",
                name="Potato",
                hindi_name="आलू",
                category=CropCategory.STORABLE,
                default_spoilage_rate=0.005,
                max_ambient_holding_days=180,
                standard_moisture_pct=79.0,
            ),
        }

        needed_crops = {rec.commodity_id for rec in normalized_records}
        for crop_id in needed_crops:
            existing = await comm_repo.get_by_id(crop_id)
            if not existing:
                if crop_id in standard_crops:
                    await comm_repo.upsert(standard_crops[crop_id])
                else:
                    fallback_crop = CommodityCreate(
                        id=crop_id,
                        name=crop_id.capitalize(),
                        hindi_name=None,
                        category=CropCategory.PERISHABLE,
                        default_spoilage_rate=0.05,
                        max_ambient_holding_days=7,
                        standard_moisture_pct=14.0,
                    )
                    await comm_repo.upsert(fallback_crop)

        # Ensure mandis exist
        needed_markets = {rec.market_id for rec in normalized_records}
        for m_id in needed_markets:
            existing_mandi = await market_repo.get_by_id(m_id)
            if not existing_mandi:
                m_entry = self.market_resolver.resolve_market(m_id)
                if m_entry:
                    m_create = MarketCreate(
                        id=m_entry.market_id,
                        apmc_code=m_entry.apmc_code,
                        name=m_entry.name,
                        state=m_entry.state,
                        district=m_entry.district,
                        latitude=m_entry.latitude,
                        longitude=m_entry.longitude,
                        is_terminal_market=m_entry.is_terminal_market,
                        dca_centre_id=m_entry.dca_centre_id,
                        source_market_id=m_entry.name,
                    )
                    await market_repo.upsert(m_create)
                else:
                    fallback_mandi = MarketCreate(
                        id=m_id,
                        apmc_code=9999,
                        name=m_id.replace("mandi_", "").replace("_", " ").title(),
                        state="Unknown",
                        district="Unknown",
                        latitude=28.6139,
                        longitude=77.2090,
                        is_terminal_market=False,
                        source_market_id=m_id,
                    )
                    await market_repo.upsert(fallback_mandi)

        await session.flush()

    async def process_file(
        self,
        file_path: str,
        source_name: str = "LOCAL_CSV",
        format_name: str = "canonical",
        dry_run: bool = False,
        session: Optional[AsyncSession] = None,
    ) -> Tuple[ValidationReport, int]:
        """
        Executes the full pipeline for a given CSV file.

        Args:
            file_path: Path to target file.
            source_name: Source origin identifier.
            format_name: 'canonical', 'agmarknet', or 'auto'.
            dry_run: If True, performs parsing and validation without writing to DB.
            session: Optional SQLAlchemy async session.

        Returns:
            Tuple of (ValidationReport, inserted_records_count).
        """
        adapter = LocalCSVSourceAdapter(source_name=source_name)
        raw_records = adapter.read_records(file_path)

        if not raw_records:
            empty_report = ValidationReport(
                source=source_name,
                total_records=0,
                valid_records=0,
                warning_records=0,
                invalid_records=0,
                duplicate_records=0,
                health_score=100.0,
            )
            return empty_report, 0

        # Step 2: Map columns
        mapped_records = [
            ColumnMapper.map_record(r.payload, format_name=format_name) for r in raw_records
        ]

        # Step 3: Validate
        valid_records, report = self.validator.validate_batch(
            mapped_records, source_name=source_name
        )

        # Step 4: Normalize
        normalized_records = self.normalizer.normalize_batch(
            valid_records, source_name=source_name
        )

        inserted_count = 0
        # Step 5: Persist if not dry-run and session available
        if not dry_run and session is not None and normalized_records:
            await self._ensure_prerequisites(session, normalized_records)
            price_repo = PriceObservationRepository(session)
            inserted_count = await price_repo.bulk_insert(normalized_records)
            await session.commit()

        return report, inserted_count
