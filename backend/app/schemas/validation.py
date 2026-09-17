"""
Validation & Quality Audit Schemas for AgriClutch Data Pipeline.
Captures issues, row references, and overall batch health scorecards.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, List, Optional

from pydantic import BaseModel, Field


class ValidationStatus(str, Enum):
    """Classification status for evaluated agricultural records."""

    VALID = "VALID"
    WARNING = "WARNING"
    INVALID = "INVALID"


class ValidationSeverity(str, Enum):
    """Severity of a detected validation issue."""

    ERROR = "ERROR"
    WARNING = "WARNING"


class ValidationIssue(BaseModel):
    """Specific error or warning raised during record validation."""

    severity: ValidationSeverity = Field(..., description="Issue severity")
    field: str = Field(..., description="Target field with violation")
    message: str = Field(..., description="Human-readable explanation")
    raw_value: Optional[Any] = Field(default=None, description="Problematic input value")
    row_number: Optional[int] = Field(default=None, description="Source file row number")


class ValidationReport(BaseModel):
    """Comprehensive dataset health scorecard produced prior to storage ingestion."""

    source: str = Field(..., description="Source identifier")
    total_records: int = Field(default=0, ge=0)
    valid_records: int = Field(default=0, ge=0)
    warning_records: int = Field(default=0, ge=0)
    invalid_records: int = Field(default=0, ge=0)
    duplicate_records: int = Field(default=0, ge=0)
    errors: List[ValidationIssue] = Field(default_factory=list)
    warnings: List[ValidationIssue] = Field(default_factory=list)
    health_score: float = Field(default=100.0, ge=0.0, le=100.0)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def is_acceptable(self) -> bool:
        """Returns True if no fatal errors exist and health score is above threshold."""
        return self.invalid_records == 0 and self.health_score >= 80.0
