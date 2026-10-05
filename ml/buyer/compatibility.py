"""
AgriClutch Deterministic Buyer–Produce Compatibility Engine.
Evaluates multi-dimensional feasibility across commodity, variety, quality grade,
quantity bounds, temporal overlap, and geodesic distance.
SIH26132 — Strengthening Market Linkages and Price Discovery for Farmers.
"""

import math
from datetime import date, datetime, timezone

from ml.buyer.contracts import (
    BuyerRequirement,
    CompatibilityResult,
    DistanceStatus,
    FarmerSupply,
    QuantityMatchStatus,
    TemporalOverlapStatus,
)


def calculate_haversine_distance(
    lat1: float | None,
    lon1: float | None,
    lat2: float | None,
    lon2: float | None,
) -> tuple[float | None, DistanceStatus]:
    """
    Computes geodesic distance in kilometers between two geographic coordinates using the Haversine formula.

    Returns:
        Tuple of (distance_km, DistanceStatus).
    """
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return None, DistanceStatus.DISTANCE_UNAVAILABLE

    # Earth radius in kilometers
    r_earth = 6371.0

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2)
    )
    # Clip to prevent floating point domain errors in sqrt
    a = min(1.0, max(0.0, a))
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    distance_km = round(r_earth * c, 2)

    return distance_km, DistanceStatus.DISTANCE_GEODESIC


class CompatibilityEngine:
    """
    Deterministic compatibility solver between producer supply lots and buyer procurement requirements.
    Outputs factual constraint evaluations and additive explanations without recommendation bias.
    """

    @staticmethod
    def evaluate_commodity(supply_commodity: str, req_commodity: str) -> tuple[bool, str]:
        s_norm = supply_commodity.strip().lower()
        r_norm = req_commodity.strip().lower()
        if s_norm == r_norm:
            return True, f"Commodity matches '{supply_commodity}'."
        return False, f"Commodity mismatch: supply is '{supply_commodity}' but buyer requires '{req_commodity}'."

    @staticmethod
    def evaluate_variety(
        supply_variety: str | None, req_variety: str | None
    ) -> tuple[bool, str]:
        if not req_variety or req_variety.strip().upper() in ["ANY", "ALL", "NONE", ""]:
            return True, "Buyer accepts any variety."
        if not supply_variety:
            return False, f"Supply variety unspecified; buyer strictly requires variety '{req_variety}'."
        if supply_variety.strip().lower() == req_variety.strip().lower():
            return True, f"Variety matches '{supply_variety}'."
        return False, f"Variety mismatch: supply is '{supply_variety}' but buyer requires '{req_variety}'."

    @staticmethod
    def evaluate_quality(
        supply_grade: str,
        preferred_grade: str,
        acceptable_grades: list[str],
    ) -> tuple[bool, str]:
        s_norm = supply_grade.strip().upper()
        p_norm = preferred_grade.strip().upper()
        acc_norms = [g.strip().upper() for g in acceptable_grades]

        if s_norm == p_norm:
            return True, f"Quality matches preferred grade '{supply_grade}'."
        if s_norm in acc_norms:
            return True, f"Quality '{supply_grade}' is within acceptable grade range {acceptable_grades}."
        return False, f"Quality mismatch: supply grade '{supply_grade}' not in acceptable range {acceptable_grades}."

    @staticmethod
    def evaluate_quantity(
        supply_qty_kg: float,
        min_qty_kg: float,
        max_qty_kg: float,
    ) -> tuple[QuantityMatchStatus, float, float, float, str]:
        """
        Quantity matching arithmetic:
        - If supply < min_qty: Insufficient supply to meet buyer minimum lot size.
        - If supply >= min_qty: Compatible quantity is min(supply, max_qty).
        """
        if supply_qty_kg < min_qty_kg:
            compat = 0.0
            unmatched_s = supply_qty_kg
            unmatched_d = max_qty_kg
            explanation = (
                f"Insufficient supply: available {supply_qty_kg:.1f} kg is below "
                f"buyer minimum lot requirement of {min_qty_kg:.1f} kg."
            )
            return QuantityMatchStatus.INSUFFICIENT_SUPPLY, compat, unmatched_s, unmatched_d, explanation

        compat = min(supply_qty_kg, max_qty_kg)
        unmatched_s = max(0.0, supply_qty_kg - compat)
        unmatched_d = max(0.0, max_qty_kg - compat)

        if supply_qty_kg == max_qty_kg:
            status = QuantityMatchStatus.EXACT_MATCH
            explanation = f"Exact quantity match of {compat:.1f} kg."
        elif supply_qty_kg < max_qty_kg:
            status = QuantityMatchStatus.PARTIAL_MATCH
            explanation = (
                f"Partial demand absorption: entire supply of {compat:.1f} kg absorbed; "
                f"buyer has {unmatched_d:.1f} kg remaining capacity."
            )
        else:
            status = QuantityMatchStatus.PARTIAL_MATCH
            explanation = (
                f"Partial supply match: buyer maximum capacity of {compat:.1f} kg satisfied; "
                f"{unmatched_s:.1f} kg supply remains unabsorbed."
            )

        return status, compat, unmatched_s, unmatched_d, explanation

    @staticmethod
    def evaluate_temporal(
        supply_from: date,
        supply_until: date,
        req_from: date,
        req_until: date,
        reference_date: date | None = None,
    ) -> tuple[bool, TemporalOverlapStatus, str]:
        today = reference_date or datetime.now(timezone.utc).date()


        if req_until < today:
            return False, TemporalOverlapStatus.EXPIRED_REQUIREMENT, (
                f"Buyer requirement expired on {req_until.isoformat()} (prior to reference date {today.isoformat()})."
            )

        start_overlap = max(supply_from, req_from)
        end_overlap = min(supply_until, req_until)

        if start_overlap > end_overlap:
            return False, TemporalOverlapStatus.NO_OVERLAP, (
                f"No temporal overlap: supply available {supply_from.isoformat()} to {supply_until.isoformat()}, "
                f"buyer requires {req_from.isoformat()} to {req_until.isoformat()}."
            )

        is_full = (start_overlap == supply_from) and (end_overlap == supply_until)
        status = TemporalOverlapStatus.FULL_OVERLAP if is_full else TemporalOverlapStatus.PARTIAL_OVERLAP
        explanation = (
            f"Temporal window compatible from {start_overlap.isoformat()} to {end_overlap.isoformat()} "
            f"({status.value.replace('_', ' ').title()})."
        )
        return True, status, explanation

    def match(
        self,
        supply: FarmerSupply,
        requirement: BuyerRequirement,
        reference_date: date | None = None,
    ) -> CompatibilityResult:
        """
        Evaluates complete multi-attribute compatibility between supply and requirement.
        """
        explanations: list[str] = []

        # 1. Commodity
        comm_match, comm_exp = self.evaluate_commodity(supply.commodity_id, requirement.commodity_id)
        explanations.append(comm_exp)

        # 2. Variety
        var_match, var_exp = self.evaluate_variety(supply.variety, requirement.variety)
        explanations.append(var_exp)

        # 3. Quality
        qual_match, qual_exp = self.evaluate_quality(
            supply.quality_grade,
            requirement.preferred_quality_grade,
            requirement.acceptable_quality_range,
        )
        explanations.append(qual_exp)

        # 4. Quantity
        qty_status, compat_qty, unmatched_s, unmatched_d, qty_exp = self.evaluate_quantity(
            supply.quantity_kg,
            requirement.minimum_quantity_kg,
            requirement.maximum_quantity_kg,
        )
        explanations.append(qty_exp)

        # 5. Temporal
        time_match, time_status, time_exp = self.evaluate_temporal(
            supply.available_from,
            supply.available_until,
            requirement.required_from,
            requirement.required_until,
            reference_date=reference_date,
        )
        explanations.append(time_exp)

        # 6. Geodesic Distance
        buyer_lat = requirement.delivery_latitude
        buyer_lon = requirement.delivery_longitude
        distance_km, dist_status = calculate_haversine_distance(
            supply.origin_latitude,
            supply.origin_longitude,
            buyer_lat,
            buyer_lon,
        )
        if distance_km is not None:
            explanations.append(f"Geodesic transit distance: {distance_km:.1f} km.")
        else:
            explanations.append("Geographic coordinates unavailable for origin or destination.")

        # Overall constraint status
        is_all_strict = comm_match and var_match and qual_match and time_match and (compat_qty > 0)

        if is_all_strict and (compat_qty == supply.quantity_kg):
            constraint_status = "COMPATIBLE"
        elif is_all_strict:
            constraint_status = "PARTIALLY_COMPATIBLE"
        else:
            constraint_status = "INCOMPATIBLE"

        return CompatibilityResult(
            buyer_id=requirement.buyer_id,
            supply_id=supply.supply_id,
            requirement_id=requirement.requirement_id,
            commodity_match=comm_match,
            variety_match=var_match,
            quality_match=qual_match,
            quantity_match=qty_status,
            temporal_match=time_match,
            delivery_constraint_match=True,  # Documented constraint flag
            compatible_quantity_kg=compat_qty,
            unmatched_supply_kg=unmatched_s,
            unmatched_demand_kg=unmatched_d,
            distance_km=distance_km,
            distance_status=dist_status,
            temporal_overlap_status=time_status,
            constraint_status=constraint_status,
            explanations=explanations,
            provenance=requirement.provenance,
        )
