"""
AgriClutch Perishability & Shelf-Life Engine.
Models decoupled physical quantity loss and quality grade assay deterioration over time.
Strictly documents mathematical decay functions and fails closed to LOSS_MODEL_UNAVAILABLE.
SIH26132 — Strengthening Market Linkages and Price Discovery for Farmers.
"""

import math

from ml.logistics.contracts import (
    EconomicProvenance,
    PerishabilityModelSpec,
    PerishabilityPoint,
    PerishabilityTrajectory,
    ProvenanceStatus,
    StorageType,
)

# Configured/Demo Crop Perishability Parameters (Explicitly Tagged as DEMO ASSUMPTIONS)
# Clean-room parameter dictionary: (crop_id, storage_type) -> PerishabilityModelSpec
CROP_STORAGE_MODELS: dict[tuple[str, StorageType], PerishabilityModelSpec] = {
    ("tomato", StorageType.AMBIENT): PerishabilityModelSpec(
        crop="tomato",
        storage_type=StorageType.AMBIENT,
        decay_parameter_delta=0.035,  # ~3.5% daily physical weight/spoilage loss
        quality_decay_beta=0.050,     # ~5.0% daily quality grade degradation
        unit="PER_DAY",
        max_supported_days=10,
        equation="S(t) = exp(-0.035 * t); Q_eff(t) = Q0 * S(t); F_qual(t) = F0 * exp(-0.050 * t)",
        assumptions="Uncontrolled ambient conditions (28-35°C, variable RH). Non-refrigerated holding.",
        calibration_status="NOT_CALIBRATED",
        provenance=EconomicProvenance(
            source_name="DEMO_PERISHABILITY_ASSUMPTION_SCHEDULE",
            status=ProvenanceStatus.DEMO,
            is_demo=True,
            justification="DEMO ASSUMPTION — Model based on indicative regional tomato shelf-life benchmarks; not an empirically certified laboratory constant.",
        ),
    ),
    ("tomato", StorageType.COLD): PerishabilityModelSpec(
        crop="tomato",
        storage_type=StorageType.COLD,
        decay_parameter_delta=0.008,  # ~0.8% daily loss
        quality_decay_beta=0.015,     # ~1.5% daily quality loss
        unit="PER_DAY",
        max_supported_days=28,
        equation="S(t) = exp(-0.008 * t); Q_eff(t) = Q0 * S(t); F_qual(t) = F0 * exp(-0.015 * t)",
        assumptions="Cold chain holding (10-12°C, 90-95% RH). Controlled atmosphere.",
        calibration_status="NOT_CALIBRATED",
        provenance=EconomicProvenance(
            source_name="DEMO_PERISHABILITY_ASSUMPTION_SCHEDULE",
            status=ProvenanceStatus.DEMO,
            is_demo=True,
            justification="DEMO ASSUMPTION — Commercial cold storage shelf-life benchmark.",
        ),
    ),
    ("onion", StorageType.AMBIENT): PerishabilityModelSpec(
        crop="onion",
        storage_type=StorageType.AMBIENT,
        decay_parameter_delta=0.005,  # ~0.5% daily loss
        quality_decay_beta=0.008,
        unit="PER_DAY",
        max_supported_days=60,
        equation="S(t) = exp(-0.005 * t); Q_eff(t) = Q0 * S(t); F_qual(t) = F0 * exp(-0.008 * t)",
        assumptions="Naturally ventilated village kanda chawl holding (dry, aerated).",
        calibration_status="NOT_CALIBRATED",
        provenance=EconomicProvenance(
            source_name="DEMO_PERISHABILITY_ASSUMPTION_SCHEDULE",
            status=ProvenanceStatus.DEMO,
            is_demo=True,
            justification="DEMO ASSUMPTION — Ventilated chawl storage loss benchmark.",
        ),
    ),
    ("onion", StorageType.COLD): PerishabilityModelSpec(
        crop="onion",
        storage_type=StorageType.COLD,
        decay_parameter_delta=0.001,
        quality_decay_beta=0.002,
        unit="PER_DAY",
        max_supported_days=180,
        equation="S(t) = exp(-0.001 * t); Q_eff(t) = Q0 * S(t); F_qual(t) = F0 * exp(-0.002 * t)",
        assumptions="Commercial cold storage (0-2°C, 65-70% RH). Dormancy maintenance.",
        calibration_status="NOT_CALIBRATED",
        provenance=EconomicProvenance(
            source_name="DEMO_PERISHABILITY_ASSUMPTION_SCHEDULE",
            status=ProvenanceStatus.DEMO,
            is_demo=True,
            justification="DEMO ASSUMPTION — Commercial refrigerated onion storage benchmark.",
        ),
    ),
    ("potato", StorageType.AMBIENT): PerishabilityModelSpec(
        crop="potato",
        storage_type=StorageType.AMBIENT,
        decay_parameter_delta=0.004,
        quality_decay_beta=0.006,
        unit="PER_DAY",
        max_supported_days=90,
        equation="S(t) = exp(-0.004 * t); Q_eff(t) = Q0 * S(t); F_qual(t) = F0 * exp(-0.006 * t)",
        assumptions="Traditional farm ambient heap / pit storage (dark, ventilated).",
        calibration_status="NOT_CALIBRATED",
        provenance=EconomicProvenance(
            source_name="DEMO_PERISHABILITY_ASSUMPTION_SCHEDULE",
            status=ProvenanceStatus.DEMO,
            is_demo=True,
            justification="DEMO ASSUMPTION — Farm-gate potato holding benchmark.",
        ),
    ),
    ("potato", StorageType.COLD): PerishabilityModelSpec(
        crop="potato",
        storage_type=StorageType.COLD,
        decay_parameter_delta=0.0008,
        quality_decay_beta=0.0015,
        unit="PER_DAY",
        max_supported_days=240,
        equation="S(t) = exp(-0.0008 * t); Q_eff(t) = Q0 * S(t); F_qual(t) = F0 * exp(-0.0015 * t)",
        assumptions="Commercial potato cold store (2-4°C, 95% RH with CIPC sprout suppression).",
        calibration_status="NOT_CALIBRATED",
        provenance=EconomicProvenance(
            source_name="DEMO_PERISHABILITY_ASSUMPTION_SCHEDULE",
            status=ProvenanceStatus.DEMO,
            is_demo=True,
            justification="DEMO ASSUMPTION — Industrial potato cold storage benchmark.",
        ),
    ),
}


class PerishabilityEngine:
    """
    Computes time-dependent physical quantity survival and quality degradation.
    """

    @staticmethod
    def calculate_decay_survival(decay_parameter_delta: float, days: float) -> float:
        """Computes quantity survival factor: S(t) = exp(-delta * t)."""
        return math.exp(-decay_parameter_delta * float(days))

    @staticmethod
    def calculate_quality_factor(
        initial_quality_factor: float, quality_decay_beta: float, days: float
    ) -> float:
        """Computes quality grade discount factor: F_qual(t) = F0 * exp(-beta * t)."""
        return max(0.0, min(1.0, initial_quality_factor * math.exp(-quality_decay_beta * float(days))))

    @classmethod
    def get_model_spec(cls, crop: str, storage_type: StorageType) -> PerishabilityModelSpec | None:
        """Looks up documented loss parameter specification."""
        norm_crop = crop.strip().lower()
        # Fallback handling: VENTILATED maps to AMBIENT curve if specific not found
        st = StorageType.AMBIENT if storage_type == StorageType.VENTILATED else storage_type
        return CROP_STORAGE_MODELS.get((norm_crop, st))

    @classmethod
    def calculate_trajectory(
        cls,
        crop: str | None = None,
        storage_type: StorageType = StorageType.AMBIENT,
        initial_quantity_kg: float = 1000.0,
        duration_days: int = 1,
        initial_quality_factor: float = 1.0,
        commodity_id: str | None = None,
    ) -> PerishabilityTrajectory:
        """
        Generates day-by-day deterioration trajectory:
            S(t) = exp(-delta * t)
            Q_eff(t) = Q_initial * S(t)
            F_qual(t) = F_initial * exp(-beta * t)

        Fails closed to LOSS_MODEL_UNAVAILABLE if crop or storage regime is unsupported.
        """
        target_crop = crop or commodity_id or "unknown"
        if initial_quantity_kg <= 0:
            raise ValueError(f"Initial quantity must be strictly positive: {initial_quantity_kg}")
        if duration_days < 0:
            raise ValueError(f"Duration cannot be negative: {duration_days}")
        if not (0.0 <= initial_quality_factor <= 1.0):
            raise ValueError(f"Initial quality factor must be in [0, 1]: {initial_quality_factor}")

        spec = cls.get_model_spec(target_crop, storage_type)

        if spec is None:
            return PerishabilityTrajectory(
                commodity_id=target_crop.lower(),
                storage_type=storage_type,
                initial_quantity_kg=initial_quantity_kg,
                final_quantity_kg=initial_quantity_kg,
                final_quality_factor=initial_quality_factor,
                duration_days=duration_days,
                trajectory=[],
                model_spec=None,
                status="LOSS_MODEL_UNAVAILABLE",
                provenance=EconomicProvenance(
                    source_name="PERISHABILITY_ENGINE",
                    status=ProvenanceStatus.UNAVAILABLE,
                    is_demo=False,
                    justification=f"No verified loss model available for crop '{target_crop}' under storage '{storage_type.value}'.",
                ),
            )

        points: list[PerishabilityPoint] = []
        delta = spec.decay_parameter_delta
        beta = spec.quality_decay_beta

        for t in range(duration_days + 1):
            s_t = math.exp(-delta * float(t))
            q_t = initial_quantity_kg * s_t
            q_loss = initial_quantity_kg - q_t
            f_t = max(0.0, min(1.0, initial_quality_factor * math.exp(-beta * float(t))))

            points.append(
                PerishabilityPoint(
                    day=t,
                    elapsed_hours=float(t * 24),
                    quantity_kg=q_t,
                    quantity_loss_kg=q_loss,
                    survival_factor=s_t,
                    quality_factor=f_t,
                )
            )

        final_pt = points[-1]

        return PerishabilityTrajectory(
            commodity_id=target_crop.lower(),
            storage_type=storage_type,
            initial_quantity_kg=initial_quantity_kg,
            final_quantity_kg=final_pt.quantity_kg,
            final_quality_factor=final_pt.quality_factor,
            duration_days=duration_days,
            trajectory=points,
            model_spec=spec,
            status="CALCULATED",
            provenance=spec.provenance,
        )
