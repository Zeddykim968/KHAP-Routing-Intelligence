"""
Gap analysis — identifies underserved areas and estimates the impact of
placing a new facility at a candidate location.

Performance: uses a 0.5° grid (coarser) for national analysis to keep runtime
under 2 seconds. County-level queries use the finer 0.25° grid.
"""

import math
from typing import List, Dict, Tuple

KENYA_BOUNDS = {"lat_min": -4.7, "lat_max": 4.6, "lon_min": 34.0, "lon_max": 42.0}
COVERAGE_RADIUS_KM = 15
GRID_STEP_NATIONAL = 0.5   # ~55 km cells — fast for national queries
GRID_STEP_COUNTY = 0.25    # ~28 km cells — fine for county queries
AVG_POPULATION_PER_GRID_CELL = 8000


def _haversine(lat1, lon1, lat2, lon2) -> float:
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _grid_points(bounds: Dict = None, step: float = None) -> List[Tuple[float, float]]:
    b = bounds or KENYA_BOUNDS
    s = step or GRID_STEP_NATIONAL
    points = []
    lat = b["lat_min"]
    while lat <= b["lat_max"]:
        lon = b["lon_min"]
        while lon <= b["lon_max"]:
            points.append((round(lat, 4), round(lon, 4)))
            lon = round(lon + s, 4)
        lat = round(lat + s, 4)
    return points


def _auto_step(facilities: List[Dict]) -> float:
    """Use finer grid for small county datasets, coarser for national."""
    return GRID_STEP_COUNTY if len(facilities) < 500 else GRID_STEP_NATIONAL


def find_coverage_gaps(
    facilities: List[Dict],
    county_bounds: Dict = None,
    coverage_radius_km: float = COVERAGE_RADIUS_KM,
) -> List[Dict]:
    """
    Returns grid points NOT covered by any existing facility.
    Automatically selects grid resolution based on dataset size.
    """
    valid = [f for f in facilities if f.get("latitude") and f.get("longitude")]
    step = _auto_step(valid)
    grid = _grid_points(county_bounds, step)

    # Pre-extract coords for speed
    coords = [(f["latitude"], f["longitude"]) for f in valid]

    gaps = []
    for lat, lon in grid:
        nearest_dist = min((_haversine(lat, lon, flat, flon) for flat, flon in coords), default=999)
        if nearest_dist > coverage_radius_km:
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
    Scores candidate grid locations by impact (gap cells they'd cover).
    Shares a single gap-computation pass for efficiency.
    """
    valid = [f for f in facilities if f.get("latitude") and f.get("longitude")]
    gaps = find_coverage_gaps(valid, coverage_radius_km=coverage_radius_km)
    if not gaps:
        return []

    step = _auto_step(valid)
    candidates = _grid_points(step=step)
    gap_coords = [(g["latitude"], g["longitude"]) for g in gaps]

    scored = []
    for lat, lon in candidates:
        covered = sum(
            1 for glat, glon in gap_coords
            if _haversine(lat, lon, glat, glon) <= coverage_radius_km
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
