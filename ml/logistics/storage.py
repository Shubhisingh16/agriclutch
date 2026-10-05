"""
AgriClutch Storage Feasibility Engine.
Evaluates physical capacity, supported duration horizons, and holding costs for storage facilities.
Preserves partial storage capacity allocations without rounding away infeasibilities.
SIH26132 — Strengthening Market Linkages and Price Discovery for Farmers.
"""


from ml.logistics.contracts import (
    EconomicProvenance,
    FeasibilityStatus,
    ProvenanceStatus,
    StorageFacility,
    StorageFeasibilityResult,
    StorageType,
)


class StorageEngine:
    """
    Evaluates facility holding constraints and costs.
    Strictly partitions requested volume into stored vs unstored segments.
    """

    @staticmethod
    def evaluate_storage(
        facility: StorageFacility | None,
        requested_quantity_kg: float,
        requested_duration_days: int,
    ) -> StorageFeasibilityResult:
        """
        Evaluates whether a produce lot can be stored at the specified facility.

        Formulas:
            stored_quantity = min(requested_quantity, available_capacity)
            unstored_quantity = max(0, requested_quantity - available_capacity)
            storage_cost = stored_quantity * duration_days * cost_per_kg_day
        """
        if requested_quantity_kg <= 0:
            raise ValueError(f"Requested storage quantity must be strictly positive: {requested_quantity_kg}")
        if requested_duration_days < 0:
            raise ValueError(f"Requested storage duration cannot be negative: {requested_duration_days}")

        # Case 1: No facility specified or storage unavailable
        if facility is None:
            return StorageFeasibilityResult(
                facility_id="NONE",
                facility_name="NO_STORAGE_SELECTED",
                storage_type=StorageType.UNKNOWN,
                requested_quantity_kg=requested_quantity_kg,
                available_capacity_kg=0.0,
                stored_quantity_kg=0.0,
                unstored_quantity_kg=requested_quantity_kg,
                requested_duration_days=requested_duration_days,
                min_supported_days=0,
                max_supported_days=0,
                storage_cost=0.0,
                status=FeasibilityStatus.UNAVAILABLE if requested_duration_days > 0 else FeasibilityStatus.FEASIBLE,
                warnings=["No storage facility specified for positive holding duration."] if requested_duration_days > 0 else [],
                provenance=EconomicProvenance(
                    source_name="STORAGE_ENGINE",
                    status=ProvenanceStatus.UNAVAILABLE,
                    is_demo=False,
                    justification="No storage facility assigned.",
                ),
            )

        warnings: list[str] = []
        avail_cap = max(0.0, facility.available_capacity_kg)
        stored_qty = min(requested_quantity_kg, avail_cap)
        unstored_qty = max(0.0, requested_quantity_kg - avail_cap)

        # Duration checks
        duration_valid = True
        if requested_duration_days < facility.min_duration_days:
            duration_valid = False
            warnings.append(
                f"Requested duration ({requested_duration_days} days) is below facility minimum ({facility.min_duration_days} days)."
            )
        if requested_duration_days > facility.max_duration_days:
            duration_valid = False
            warnings.append(
                f"Requested duration ({requested_duration_days} days) exceeds facility maximum ({facility.max_duration_days} days)."
            )

        # Capacity checks
        if unstored_qty > 0:
            warnings.append(
                f"Facility capacity shortfall: {unstored_qty:.1f} kg cannot be stored (available capacity: {avail_cap:.1f} kg)."
            )

        # Compute cost
        storage_cost = stored_qty * float(requested_duration_days) * facility.cost_per_kg_day

        # Feasibility classification
        if not duration_valid or avail_cap <= 0:
            status = FeasibilityStatus.INFEASIBLE
        elif unstored_qty > 0:
            status = FeasibilityStatus.PARTIALLY_FEASIBLE
        else:
            status = FeasibilityStatus.FEASIBLE

        return StorageFeasibilityResult(
            facility_id=facility.facility_id,
            facility_name=facility.name,
            storage_type=facility.storage_type,
            requested_quantity_kg=requested_quantity_kg,
            available_capacity_kg=avail_cap,
            stored_quantity_kg=stored_qty,
            unstored_quantity_kg=unstored_qty,
            requested_duration_days=requested_duration_days,
            min_supported_days=facility.min_duration_days,
            max_supported_days=facility.max_duration_days,
            storage_cost=storage_cost,
            status=status,
            warnings=warnings,
            provenance=facility.provenance,
        )
