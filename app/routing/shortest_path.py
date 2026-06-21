"""
Route geometry retrieval using OSRM public API.
Returns a GeoJSON LineString representing the road path between two points.
Falls back to a straight-line geometry if OSRM is unavailable.
"""

import httpx

OSRM_BASE = "http://router.project-osrm.org/route/v1/driving"


async def get_route_geometry(
    origin_lat: float, origin_lon: float,
    dest_lat: float, dest_lon: float,
) -> dict:
    """
    Returns a GeoJSON-compatible route object with geometry, duration, and distance.
    """
    url = f"{OSRM_BASE}/{origin_lon},{origin_lat};{dest_lon},{dest_lat}"
    params = {"overview": "full", "geometries": "geojson"}

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            route = data["routes"][0]
            return {
                "geometry": route["geometry"],
                "duration_minutes": round(route["duration"] / 60, 1),
                "distance_km": round(route["distance"] / 1000, 2),
                "method": "osrm",
            }
    except Exception:
        return {
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [origin_lon, origin_lat],
                    [dest_lon, dest_lat],
                ],
            },
            "duration_minutes": None,
            "distance_km": None,
            "method": "straight_line_fallback",
        }
