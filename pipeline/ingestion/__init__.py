"""
AgriClutch Pipeline Ingestion Package.
Modular ingestion adapters, authoritative market resolvers, and column mappers.
"""

from pipeline.ingestion.base import BaseSourceAdapter, RawRecord
from pipeline.ingestion.column_mapper import ColumnMapper
from pipeline.ingestion.csv_adapter import LocalCSVSourceAdapter
from pipeline.ingestion.market_resolver import (
    AuthoritativeMarketEntry,
    MarketResolver,
    default_market_resolver,
)

__all__ = [
    "RawRecord",
    "BaseSourceAdapter",
    "LocalCSVSourceAdapter",
    "ColumnMapper",
    "MarketResolver",
    "AuthoritativeMarketEntry",
    "default_market_resolver",
]
