"""
Unit Tests for AgriClutch Geodesic Distance Engine.
Verifies Haversine formula, boundary conditions, coordinate validation,
and road vs straight-line distance resolution.
SIH26132 — Strengthening Market Linkages and Price Discovery for Farmers.
"""

import pytest

from ml.logistics.contracts import DistanceType, ProvenanceStatus, TransitTimeStatus
from ml.logistics.distance import (
    DistanceEngine,
    calculate_haversine_distance,
    resolve_transit_time,
)


def test_haversine_distance_known_coordinates() -> None:
    # Kalka (30.8350, 76.9350) to Chandigarh APMC (30.7050, 76.7900)
    dist = DistanceEngine.haversine_distance(30.8350, 76.9350, 30.7050, 76.7900)
    assert 18.0 <= dist <= 24.0


def test_haversine_identical_coordinates() -> None:
    dist = DistanceEngine.haversine_distance(30.8350, 76.9350, 30.8350, 76.9350)
    assert dist == 0.0


def test_haversine_out_of_bounds_latitude() -> None:
    with pytest.raises(ValueError, match="Latitude out of bounds"):
        DistanceEngine.haversine_distance(91.0, 76.0, 30.0, 76.0)

    with pytest.raises(ValueError, match="Latitude out of bounds"):
        DistanceEngine.haversine_distance(-95.0, 76.0, 30.0, 76.0)


def test_haversine_out_of_bounds_longitude() -> None:
    with pytest.raises(ValueError, match="Longitude out of bounds"):
        DistanceEngine.haversine_distance(30.0, 185.0, 30.0, 76.0)

    with pytest.raises(ValueError, match="Longitude out of bounds"):
        DistanceEngine.haversine_distance(30.0, -185.0, 30.0, 76.0)


def test_haversine_missing_coordinates() -> None:
    dist, d_type, prov = calculate_haversine_distance(None, 76.0, 30.0, 76.0)
    assert dist is None
    assert d_type == DistanceType.UNKNOWN_DISTANCE
    assert prov.status == ProvenanceStatus.UNAVAILABLE


def test_resolve_route_distance_road_preferred() -> None:
    dist, d_type = DistanceEngine.resolve_route_distance(
        origin_lat=30.8350,
        origin_lon=76.9350,
        dest_lat=30.7050,
        dest_lon=76.7900,
        road_distance_km=28.5,
    )
    assert dist == 28.5
    assert d_type == DistanceType.ROAD_DISTANCE


def test_resolve_route_distance_straight_line_fallback() -> None:
    dist, d_type = DistanceEngine.resolve_route_distance(
        origin_lat=30.8350,
        origin_lon=76.9350,
        dest_lat=30.7050,
        dest_lon=76.7900,
        road_distance_km=None,
    )
    assert dist is not None and dist > 0
    assert d_type == DistanceType.STRAIGHT_LINE_DISTANCE


def test_calculate_transit_time_with_speed() -> None:
    hours, status = DistanceEngine.calculate_transit_time(distance_km=90.0, speed_kmh=45.0)
    assert hours == 2.0
    assert status == TransitTimeStatus.CONFIGURED


def test_calculate_transit_time_without_speed() -> None:
    hours, status = DistanceEngine.calculate_transit_time(distance_km=90.0, speed_kmh=None)
    assert hours is None
    assert status == TransitTimeStatus.TRANSIT_TIME_UNAVAILABLE


def test_resolve_transit_time_observed_priority() -> None:
    duration, status, prov = resolve_transit_time(
        distance_km=100.0,
        speed_kmh=50.0,
        observed_duration_hours=1.8,
    )
    assert duration == 1.8
    assert status == TransitTimeStatus.OBSERVED
    assert prov.status == ProvenanceStatus.EMPIRICAL
