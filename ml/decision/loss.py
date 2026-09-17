"""
AgriClutch Perishability & Spoilage Loss Subsystem.
Implements documented exponential crop decay curves and quality downgrade penalties.
SIH26132 — Market Linkages and Price Discovery for Farmers.
"""

import math
from abc import ABC, abstractmethod
from typing import Dict, Optional, Tuple

from ml.decision.contracts import EconomicProvenance, LossEstimate, ProvenanceStatus


class LossModelUnavailableError(Exception):
    """Raised when no defensible perishability parameters exist for a crop/storage pair."""

    def __init__(self, crop: str, storage_type: str, detail: str) -> None:
        super().__init__(f"Loss model unavailable for '{crop}' in '{storage_type}': {detail}")
        self.crop = crop
        self.storage_type = storage_type
        self.detail = detail


class BaseLossModel(ABC):
    """Abstract interface for crop perishability loss estimation."""

    @abstractmethod
    def estimate_loss(
        self,
        crop: str,
        storage_type: str,
        storage_days: int,
        initial_quantity_kg: float,
    ) -> LossEstimate:
        """Estimates surviving effective quantity, lost quantity, and loss rate."""
        pass


class DocumentedLossModel(BaseLossModel):
    """
    Clean-room implementation of documented crop decay curves.
    Formula: Q_usable(t) = Q_0 * exp(-delta * t)
    All parameters carry explicit DEMO/RESEARCH provenance.
    """

    # Decay rate delta (day^-1), max_days, and downgrade_days
    BENCHMARK_PARAMETERS: Dict[str, Dict[str, Dict[str, float]]] = {
        "tomato": {
            "ambient": {"delta": 0.045, "max_days": 5.0, "downgrade_days": 3.0},
            "cold_storage": {"delta": 0.008, "max_days": 21.0, "downgrade_days": 14.0},
        },
        "onion": {
            "ambient": {"delta": 0.008, "max_days": 60.0, "downgrade_days": 30.0},
            "cold_storage": {"delta": 0.002, "max_days": 180.0, "downgrade_days": 90.0},
        },
        "potato": {
            "ambient": {"delta": 0.004, "max_days": 45.0, "downgrade_days": 30.0},
            "cold_storage": {"delta": 0.0008, "max_days": 240.0, "downgrade_days": 120.0},
        },
    }

    def __init__(self, custom_parameters: Optional[Dict[str, Dict[str, Dict[str, float]]]] = None) -> None:
        self.params = custom_parameters or self.BENCHMARK_PARAMETERS

    def get_decay_params(self, crop: str, storage_type: str) -> Tuple[float, float, float]:
        norm_crop = crop.strip().lower()
        norm_type = storage_type.strip().lower()

        crop_params = self.params.get(norm_crop)
        if not crop_params:
            raise LossModelUnavailableError(
                crop=crop,
                storage_type=storage_type,
                detail=f"Crop '{crop}' does not have verified perishability parameters.",
            )

        type_params = crop_params.get(norm_type)
        if not type_params:
            raise LossModelUnavailableError(
                crop=crop,
                storage_type=storage_type,
                detail=f"Storage type '{storage_type}' is not calibrated for crop '{crop}'.",
            )

        return type_params["delta"], type_params["max_days"], type_params["downgrade_days"]

    def estimate_loss(
        self,
        crop: str,
        storage_type: str,
        storage_days: int,
        initial_quantity_kg: float,
    ) -> LossEstimate:
        if initial_quantity_kg <= 0:
            raise ValueError(f"Initial quantity must be positive, received: {initial_quantity_kg}")
        if storage_days < 0:
            raise ValueError(f"Storage days cannot be negative, received: {storage_days}")

        norm_crop = crop.strip().lower()
        norm_type = storage_type.strip().lower()

        delta, max_days, downgrade_days = self.get_decay_params(norm_crop, norm_type)

        # Exponential decay: Q_eff = Q_0 * exp(-delta * t)
        effective_qty = initial_quantity_kg * math.exp(-delta * storage_days)
        effective_qty = max(0.0, round(effective_qty, 4))
        loss_qty = round(initial_quantity_kg - effective_qty, 4)
        loss_rate = round(loss_qty / initial_quantity_kg, 4)

        prov = EconomicProvenance(
            source="ICAR_CIPHET_POST_HARVEST_BENCHMARK",
            status=ProvenanceStatus.DEMO,
            effective_date="2024-09-15",
            is_demo=True,
            description=f"Decay delta={delta}/day, max_safe_holding={max_days}d for {norm_crop} in {norm_type}.",
        )

        status = "VALID"
        if storage_days > max_days:
            status = "EXCEEDS_SAFE_HOLDING_LIMIT"

        return LossEstimate(
            crop=crop,
            storage_type=storage_type,
            storage_days=storage_days,
            loss_rate=loss_rate,
            loss_quantity_kg=loss_qty,
            effective_quantity_kg=effective_qty,
            provenance=prov,
            status=status,
        )

    def check_downgrade(self, crop: str, storage_type: str, storage_days: int) -> float:
        """Returns quality downgrade penalty fraction (e.g. 0.15) if holding exceeds downgrade threshold."""
        try:
            _, _, downgrade_days = self.get_decay_params(crop, storage_type)
            if storage_days > downgrade_days:
                return 0.15  # 15% discount penalty
        except LossModelUnavailableError:
            pass
        return 0.0
