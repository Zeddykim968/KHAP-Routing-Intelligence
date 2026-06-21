"""
Travel time estimation using OSRM public API with Haversine fallback.
OSRM returns actual road-network travel times; fallback uses straight-line
distance at an assumed average speed of 40 km/h.
"""

import httpx
from app.geo_utils import haversine

OSRM_BASE = "http://router.project-osrm.org/route/v1/driving"
FALLBACK_SPEED_KMH = 40


async def get_travel_time(
    origin_lat: float, origin_lon: float,
    dest_lat: float, dest_lon: float,
) -> dict:
    """
    Returns travel time in minutes and road distance in km between two points.
    Uses OSRM for real road routing; falls back to Haversine estimate on error.
    """
    url = f"{OSRM_BASE}/{origin_lon},{origin_lat};{dest_lon},{dest_lat}"
    params = {"overview": "false", "annotations": "false"}

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            route = data["routes"][0]
            duration_min = round(route["duration"] / 60, 1)
            distance_km = round(route["distance"] / 1000, 2)
            return {
                "duration_minutes": duration_min,
                "distance_km": distance_km,
                "method": "osrm",
            }
    except Exception:
        straight_km = haversine(origin_lat, origin_lon, dest_lat, dest_lon)
        estimated_min = round((straight_km / FALLBACK_SPEED_KMH) * 60, 1)
        return {
            "duration_minutes": estimated_min,
            "distance_km": round(straight_km, 2),
            "method": "haversine_fallback",
        }
