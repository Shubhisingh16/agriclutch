"""
Abstract Base Buyer Matcher Interface for AgriClutch.
Enforces transparent, non-black-box buyer ranking and additive scoring.
"""

from abc import ABC, abstractmethod
from typing import Any


class BaseBuyerMatcher(ABC):
    """
    Abstract contract for matching farmer produce lots against active buyer demands.
    """

    @abstractmethod
    def match_lot(
        self,
        lot_profile: dict[str, Any],
        active_demands: list[dict[str, Any]],
        max_matches: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Rank compatible buyers and return scored matches with transparent explanation factors.

        Args:
            lot_profile: Farmer produce lot details (commodity, grade, volume, location, harvest date).
            active_demands: List of verified institutional and APMC buyer orders.
            max_matches: Maximum number of ranked recommendations to return.

        Returns:
            Ranked list of buyer matches with net price estimate, reliability score, and additive reasons.
        """
