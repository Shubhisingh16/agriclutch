"""
Abstract Base Validator Interface for AgriClutch.
Specifies standards for evaluating agricultural observations and producing health scorecards.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

from app.schemas.validation import ValidationIssue, ValidationReport, ValidationStatus


class BaseDataValidator(ABC):
    """
    Abstract interface for validating agricultural records against domain contracts.
    """

    @abstractmethod
    def validate_record(
        self,
        record: Dict[str, Any],
        row_num: Optional[int] = None,
    ) -> Tuple[ValidationStatus, List[ValidationIssue]]:
        """
        Validate an individual mapped record.

        Args:
            record: Mapped record dictionary.
            row_num: Optional source row number.

        Returns:
            Tuple of (ValidationStatus, list of ValidationIssue items).
        """
        pass

    @abstractmethod
    def validate_batch(
        self,
        records: List[Dict[str, Any]],
        source_name: str,
    ) -> Tuple[List[Dict[str, Any]], ValidationReport]:
        """
        Validate a batch of records, evaluate duplicates, and produce a ValidationReport.

        Args:
            records: List of candidate records.
            source_name: Origin source identifier.

        Returns:
            Tuple of (valid_records, validation_report).
        """
        pass
