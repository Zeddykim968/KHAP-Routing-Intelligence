"""
Gap analysis — identifies underserved areas and estimates the impact of
placing a new facility at a candidate location.

The "impact" of a new facility = number of existing "coverage gap" grid
points that would move from uncovered to covered if the facility existed.

This powers the key insight:
  "If a new Level 4 hospital were built here, X additional people would
   gain access to care within 30 minutes."
"""

import math
from typing import List, Dict, Tuple

KENYA_BOUNDS = {
    "lat_min": -4.7,
    "lat_max": 4.6,
    "lon_min": 34.0,
    "lon_max": 42.0,
}

COVERAGE_RADIUS_KM = 15
GRID_STEP_DEG = 0.25
AVG_POPULATION_PER_GRID_CELL = 8000


def _haversine(lat1, lon1, lat2, lon2) -> float:
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _grid_points(bounds: Dict = None) -> List[Tuple[float, float]]:
    b = bounds or KENYA_BOUNDS
    points = []
    lat = b["lat_min"]
    while lat <= b["lat_max"]:
        lon = b["lon_min"]
        while lon <= b["lon_max"]:
            points.append((round(lat, 4), round(lon, 4)))
            lon += GRID_STEP_DEG
        lat += GRID_STEP_DEG
    return points


def find_coverage_gaps(
    facilities: List[Dict],
    county_bounds: Dict = None,
    coverage_radius_km: float = COVERAGE_RADIUS_KM,
) -> List[Dict]:
    """
    Returns a list of grid points NOT covered by any existing facility.
    Each gap includes an estimated population affected.
    """
    valid = [f for f in facilities if f.get("latitude") and f.get("longitude")]
    grid = _grid_points(county_bounds)

    gaps = []
    for lat, lon in grid:
        covered = any(
            _haversine(lat, lon, f["latitude"], f["longitude"]) <= coverage_radius_km
            for f in valid
        )
        if not covered:
            nearest_dist = min(
                (_haversine(lat, lon, f["latitude"], f["longitude"]) for f in valid),
                default=999,
            )
            gaps.append({
                "latitude": lat,
                "longitude": lon,
                "nearest_facility_km": round(nearest_dist, 1),
                "estimated_population": AVG_POPULATION_PER_GRID_CELL,
            })

    gaps.sort(key=lambda x: x["nearest_facility_km"], reverse=True)
    return gaps


def estimate_new_facility_impact(
    candidate_lat: float,
    candidate_lon: float,
    facilities: List[Dict],
    coverage_radius_km: float = COVERAGE_RADIUS_KM,
) -> Dict:
    """
    Estimates how many previously uncovered grid cells would be covered
    if a new facility were placed at (candidate_lat, candidate_lon).
    """
    gaps = find_coverage_gaps(facilities, coverage_radius_km=coverage_radius_km)

    newly_covered = [
        g for g in gaps
        if _haversine(candidate_lat, candidate_lon, g["latitude"], g["longitude"])
        <= coverage_radius_km
    ]

    people_gaining_access = len(newly_covered) * AVG_POPULATION_PER_GRID_CELL

    return {
        "candidate_location": {"latitude": candidate_lat, "longitude": candidate_lon},
        "coverage_radius_km": coverage_radius_km,
        "currently_uncovered_cells": len(gaps),
        "cells_newly_covered": len(newly_covered),
        "estimated_people_gaining_access": people_gaining_access,
        "summary": (
            f"A new facility here would bring {people_gaining_access:,} additional people "
            f"within {coverage_radius_km} km of care."
        ),
    }


def top_candidate_locations(
    facilities: List[Dict],
    top_n: int = 10,
    coverage_radius_km: float = COVERAGE_RADIUS_KM,
) -> List[Dict]:
    """
    Scores a grid of candidate locations by their potential impact.
    Returns the top N locations that would cover the most gap cells.
    """
    valid = [f for f in facilities if f.get("latitude") and f.get("longitude")]
    gaps = find_coverage_gaps(valid, coverage_radius_km=coverage_radius_km)

    if not gaps:
        return []

    candidates = _grid_points()
    scored = []
    for lat, lon in candidates:
        covered = sum(
            1 for g in gaps
            if _haversine(lat, lon, g["latitude"], g["longitude"]) <= coverage_radius_km
        )
        if covered > 0:
            scored.append({
                "latitude": lat,
                "longitude": lon,
                "cells_covered": covered,
                "estimated_people_gaining_access": covered * AVG_POPULATION_PER_GRID_CELL,
            })

    scored.sort(key=lambda x: x["cells_covered"], reverse=True)
    return scored[:top_n]
