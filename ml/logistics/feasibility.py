"""
AgriClutch Logistics Feasibility Evaluator.
Evaluates physical, operational, capacity, and timing constraints without ranking or optimization.
SIH26132 — Strengthening Market Linkages and Price Discovery for Farmers.
"""


from ml.logistics.contracts import (
    Destination,
    DistanceType,
    EconomicProvenance,
    FeasibilityStatus,
    LogisticsFeasibilityResult,
    ProduceInput,
    ProvenanceStatus,
    StorageFacility,
    StorageFeasibilityResult,
    TransitTimeStatus,
    TransportModeSpec,
)


class LogisticsFeasibilityEvaluator:
    """
    Evaluates physical, spatial, capacity, and operational constraints for logistics pathways.
    Exclusively factual: reports feasible/infeasible/partially_feasible with explicit reasons.
    Strictly zero recommendation, ranking, or scoring logic.
    """

    @staticmethod
    def evaluate(
        produce: ProduceInput,
        destination: Destination,
        transport_mode: TransportModeSpec,
        distance_km: float | None,
        distance_type: DistanceType,
        transit_duration_hours: float | None,
        transit_time_status: TransitTimeStatus,
        storage_facility: StorageFacility | None = None,
        storage_feasibility: StorageFeasibilityResult | None = None,
        storage_duration_days: int = 0,
        quality_factor: float = 1.0,
        provenance: EconomicProvenance | None = None,
    ) -> LogisticsFeasibilityResult:
        """
        Evaluate all physical and operational constraints for the specified delivery pathway.
        """
        failed_constraints: list[str] = []
        warnings: list[str] = []
        assumptions: list[str] = []

        if provenance is None:
            provenance = EconomicProvenance(
                source_name="LOGISTICS_FEASIBILITY_EVALUATOR",
                status=ProvenanceStatus.CONFIGURED,
                is_demo=True,
                justification="Deterministic physical and operational constraint verification",
            )

        # 1. Spatial & Distance Validation
        if distance_km is None or distance_type == DistanceType.UNKNOWN_DISTANCE:
            failed_constraints.append("Geographic distance is unknown or coordinates could not be resolved.")
        elif distance_km < 0:
            failed_constraints.append(f"Invalid negative distance: {distance_km} km")
        elif distance_type == DistanceType.STRAIGHT_LINE_DISTANCE:
            assumptions.append(
                f"Straight-line geodesic distance ({distance_km:.1f} km) used as proxy for road network transit."
            )

        # Destination max acceptable distance check
        if (
            distance_km is not None
            and destination.max_acceptable_distance_km is not None
            and distance_km > destination.max_acceptable_distance_km
        ):
            failed_constraints.append(
                f"Route distance {distance_km:.1f} km exceeds destination max acceptable distance of "
                f"{destination.max_acceptable_distance_km:.1f} km."
            )

        # 2. Vehicle Capacity vs Quantity Validation
        transportable_kg = produce.quantity_kg
        untransportable_kg = 0.0

        if transport_mode.capacity_kg <= 0:
            failed_constraints.append(f"Invalid transport vehicle capacity: {transport_mode.capacity_kg} kg")
            transportable_kg = 0.0
            untransportable_kg = produce.quantity_kg
        elif produce.quantity_kg > transport_mode.capacity_kg:
            transportable_kg = transport_mode.capacity_kg
            untransportable_kg = produce.quantity_kg - transport_mode.capacity_kg
            warnings.append(
                f"Produce quantity ({produce.quantity_kg:.1f} kg) exceeds single vehicle capacity "
                f"({transport_mode.capacity_kg:.1f} kg). {untransportable_kg:.1f} kg requires additional dispatch."
            )

        # 3. Transit Time Status Validation
        if transit_time_status == TransitTimeStatus.TRANSIT_TIME_UNAVAILABLE:
            failed_constraints.append("Transit time could not be determined due to missing speed or distance.")
        elif transit_time_status == TransitTimeStatus.CONFIGURED:
            assumptions.append("Transit duration estimated from configured vehicle cruise speed assumption.")

        # 4. Storage Constraint Validation
        if storage_facility is not None:
            if storage_feasibility is not None:
                if storage_feasibility.status == FeasibilityStatus.INFEASIBLE:
                    failed_constraints.extend(storage_feasibility.warnings)
                elif storage_feasibility.status == FeasibilityStatus.PARTIALLY_FEASIBLE:
                    warnings.extend(storage_feasibility.warnings)
            elif storage_duration_days > 0:
                # Direct check if storage feasibility object was not supplied
                if storage_facility.available_capacity_kg < produce.quantity_kg:
                    warnings.append(
                        f"Facility available capacity ({storage_facility.available_capacity_kg:.1f} kg) "
                        f"is below produce quantity ({produce.quantity_kg:.1f} kg)."
                    )
                if storage_duration_days > storage_facility.max_duration_days:
                    failed_constraints.append(
                        f"Storage duration {storage_duration_days} days exceeds facility maximum of "
                        f"{storage_facility.max_duration_days} days."
                    )

        # 5. Delivery Window / Timing Validation
        if destination.delivery_window_end is not None:
            # Check if transit and storage would cause arrival after window end
            elapsed_days = (transit_duration_hours or 0.0) / 24.0 + storage_duration_days
            from datetime import timedelta
            estimated_arrival = produce.available_from + timedelta(days=int(elapsed_days))
            if estimated_arrival > destination.delivery_window_end:
                failed_constraints.append(
                    f"Estimated delivery date ({estimated_arrival}) exceeds destination delivery window end "
                    f"({destination.delivery_window_end})."
                )

        # 6. Quality Factor Degradation Check
        if quality_factor < 0.20:
            warnings.append(
                f"Modeled quality factor deteriorated severely to {quality_factor:.2f}, "
                "which may violate minimum buyer grade acceptance standards."
            )

        # Determine Final Status
        if distance_type == DistanceType.UNKNOWN_DISTANCE or distance_km is None:
            status = FeasibilityStatus.INSUFFICIENT_DATA
            feasible = False
        elif len(failed_constraints) > 0:
            status = FeasibilityStatus.INFEASIBLE
            feasible = False
        elif untransportable_kg > 0:
            status = FeasibilityStatus.PARTIALLY_FEASIBLE
            feasible = True  # Feasible for the transportable portion
        elif storage_feasibility is not None and storage_feasibility.status == FeasibilityStatus.PARTIALLY_FEASIBLE:
            status = FeasibilityStatus.PARTIALLY_FEASIBLE
            feasible = True
        else:
            status = FeasibilityStatus.FEASIBLE
            feasible = True

        return LogisticsFeasibilityResult(
            feasible=feasible,
            status=status,
            transportable_quantity_kg=transportable_kg,
            untransportable_quantity_kg=untransportable_kg,
            distance_km=distance_km,
            distance_type=distance_type,
            transit_duration_hours=transit_duration_hours,
            transit_time_status=transit_time_status,
            failed_constraints=failed_constraints,
            warnings=warnings,
            assumptions=assumptions,
            provenance=provenance,
        )
