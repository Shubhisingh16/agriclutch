"""
Abstract Base Normalizer Interface for AgriClutch.
Specifies standards for deterministic type normalization, string cleaning, and unit scaling.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from app.schemas.price_observation import PriceObservationCreate


class BaseDataNormalizer(ABC):
    """
    Abstract contract for deterministic record normalization.
    Converts validated raw dictionaries into strongly-typed canonical domain models.
    """

    @abstractmethod
    def normalize_record(
        self,
        record: Dict[str, Any],
        source_name: str,
    ) -> PriceObservationCreate:
        """
        Normalize an individual validated record.

        Args:
            record: Validated input dictionary.
            source_name: Origin source identifier.

        Returns:
            Strongly-typed PriceObservationCreate instance.
        """
        pass

    @abstractmethod
    def normalize_batch(
        self,
        records: List[Dict[str, Any]],
        source_name: str,
    ) -> List[PriceObservationCreate]:
        """
        Normalize a list of validated records.

        Args:
            records: Validated input records.
            source_name: Origin source identifier.

        Returns:
            List of PriceObservationCreate instances.
        """
        pass
