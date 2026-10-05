"""
AgriClutch Geodesic Distance Engine.
Calculates spherical Haversine distances between geographical coordinates.
Strictly distinguishes straight-line distance from road distance and never fabricates route geometry.
SIH26132 — Strengthening Market Linkages and Price Discovery for Farmers.
"""

import math

from ml.logistics.contracts import (
    DistanceType,
    EconomicProvenance,
    ProvenanceStatus,
    TransitTimeStatus,
)

EARTH_RADIUS_KM = 6371.0


def calculate_haversine_distance(
    lat1: float | None,
    lon1: float | None,
    lat2: float | None,
    lon2: float | None,
) -> tuple[float | None, DistanceType, EconomicProvenance]:
    """
    Computes great-circle distance between two WGS84 coordinate pairs via Haversine formula.

    Equations:
        a = sin²(Δφ / 2) + cos(φ1) × cos(φ2) × sin²(Δλ / 2)
        c = 2 × atan2(√a, √(1-a))
        d = R × c

    Args:
        lat1: Origin latitude in degrees [-90, 90]
        lon1: Origin longitude in degrees [-180, 180]
        lat2: Destination latitude in degrees [-90, 90]
        lon2: Destination longitude in degrees [-180, 180]

    Returns:
        Tuple of (distance_km, distance_type, provenance)
    """
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return (
            None,
            DistanceType.UNKNOWN_DISTANCE,
            EconomicProvenance(
                source_name="HAVERSINE_SPHERICAL_ENGINE",
                status=ProvenanceStatus.UNAVAILABLE,
                is_demo=False,
                justification="One or both geographic coordinate pairs are missing.",
            ),
        )

    # Validate coordinate boundaries
    if not (-90.0 <= lat1 <= 90.0 and -90.0 <= lat2 <= 90.0):
        raise ValueError(f"Latitude out of bounds [-90, 90]: lat1={lat1}, lat2={lat2}")
    if not (-180.0 <= lon1 <= 180.0 and -180.0 <= lon2 <= 180.0):
        raise ValueError(f"Longitude out of bounds [-180, 180]: lon1={lon1}, lon2={lon2}")

    # Identical coordinates
    if abs(lat1 - lat2) < 1e-7 and abs(lon1 - lon2) < 1e-7:
        return (
            0.0,
            DistanceType.STRAIGHT_LINE_DISTANCE,
            EconomicProvenance(
                source_name="HAVERSINE_SPHERICAL_ENGINE",
                status=ProvenanceStatus.EMPIRICAL,
                is_demo=False,
                justification="Identical origin and destination coordinates (intra-location).",
            ),
        )

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    # Clip to [0, 1] to avoid float precision domain errors in asin/atan2
    a = min(1.0, max(0.0, a))
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    distance_km = EARTH_RADIUS_KM * c

    return (
        distance_km,
        DistanceType.STRAIGHT_LINE_DISTANCE,
        EconomicProvenance(
            source_name="HAVERSINE_SPHERICAL_ENGINE",
            status=ProvenanceStatus.EMPIRICAL,
            is_demo=False,
            justification=f"Geodesic great-circle distance calculated with earth radius R={EARTH_RADIUS_KM} km. Note: Straight-line distance, not road distance.",
        ),
    )


def resolve_transit_time(
    distance_km: float | None,
    speed_kmh: float | None = None,
    observed_duration_hours: float | None = None,
    provenance_status: ProvenanceStatus = ProvenanceStatus.CONFIGURED,
    is_demo: bool = True,
) -> tuple[float | None, TransitTimeStatus, EconomicProvenance]:
    """
    Determines transit duration without silently inventing road speeds.

    Returns:
        Tuple of (duration_hours, transit_time_status, provenance)
    """
    if observed_duration_hours is not None:
        if observed_duration_hours < 0:
            raise ValueError(f"Observed duration cannot be negative: {observed_duration_hours}")
        return (
            observed_duration_hours,
            TransitTimeStatus.OBSERVED,
            EconomicProvenance(
                source_name="HISTORICAL_TRANSIT_LOG",
                status=ProvenanceStatus.EMPIRICAL,
                is_demo=False,
                justification="Empirically documented historical route haulage duration.",
            ),
        )

    if distance_km is not None and speed_kmh is not None and speed_kmh > 0:
        duration_hours = distance_km / speed_kmh
        return (
            duration_hours,
            TransitTimeStatus.CONFIGURED,
            EconomicProvenance(
                source_name="CONFIGURED_HAULAGE_SPEED_MODEL",
                status=provenance_status,
                is_demo=is_demo,
                justification=f"Estimated from straight-line distance ({distance_km:.1f} km) and configured vehicle speed ({speed_kmh:.1f} km/h).",
            ),
        )

    return (
        None,
        TransitTimeStatus.TRANSIT_TIME_UNAVAILABLE,
        EconomicProvenance(
            source_name="TRANSIT_TIME_ENGINE",
            status=ProvenanceStatus.UNAVAILABLE,
            is_demo=False,
            justification="No observed transit duration or configured speed parameter available. Road travel time cannot be fabricated.",
        ),
    )


class DistanceEngine:
    """Unified Distance and Transit Time Engine."""

    @classmethod
    def haversine_distance(
        cls,
        lat1: float | None,
        lon1: float | None,
        lat2: float | None,
        lon2: float | None,
    ) -> float:
        """Computes geodesic distance in kilometers between two points."""
        dist, _, _ = calculate_haversine_distance(lat1, lon1, lat2, lon2)
        if dist is None:
            raise ValueError("Coordinates are incomplete or invalid.")
        return dist

    @classmethod
    def resolve_route_distance(
        cls,
        origin_lat: float | None,
        origin_lon: float | None,
        dest_lat: float | None,
        dest_lon: float | None,
        road_distance_km: float | None = None,
    ) -> tuple[float | None, DistanceType]:
        """
        Resolves road distance if provided, otherwise falls back to straight-line distance.
        Explicitly distinguishes DistanceType.ROAD_DISTANCE from STRAIGHT_LINE_DISTANCE.
        """
        if road_distance_km is not None and road_distance_km >= 0:
            return road_distance_km, DistanceType.ROAD_DISTANCE

        dist, d_type, _ = calculate_haversine_distance(origin_lat, origin_lon, dest_lat, dest_lon)
        return dist, d_type

    @classmethod
    def calculate_transit_time(
        cls,
        distance_km: float | None,
        speed_kmh: float | None = None,
        observed_duration_hours: float | None = None,
    ) -> tuple[float | None, TransitTimeStatus]:
        """Calculates transit time and returns (hours, status)."""
        duration, status, _ = resolve_transit_time(
            distance_km=distance_km,
            speed_kmh=speed_kmh,
            observed_duration_hours=observed_duration_hours,
        )
        return duration, status
