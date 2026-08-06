"""
OSRM service — communicates with the OSRM routing engine.

OSRM endpoint used:
    GET {OSRM_URL}/route/v1/driving/{lon1},{lat1};{lon2},{lat2}
        ?overview=full&geometries=geojson&steps=false

Returns distance (metres), duration (seconds), and a GeoJSON LineString
geometry (list of [lon, lat] coordinate pairs).

If OSRM cannot find a route it returns code "NoRoute" — we raise a
ValueError so the caller can return a 404 to the client.
"""
import httpx
from app.core.config import settings


def get_route(
    start_lon: float,
    start_lat: float,
    end_lon: float,
    end_lat: float,
) -> dict:
    """
    Call OSRM and return a normalised route dict.

    Raises
    ------
    ValueError
        When OSRM returns code "NoRoute" (disconnected road graph).
    RuntimeError
        On any unexpected OSRM error or HTTP failure.
    """
    url = (
        f"{settings.OSRM_URL}/route/v1/driving/"
        f"{start_lon},{start_lat};{end_lon},{end_lat}"
    )
    params = {
        "overview": "full",
        "geometries": "geojson",
        "steps": "false",
    }

    try:
        resp = httpx.get(url, params=params, timeout=10.0)
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise RuntimeError(f"OSRM request failed: {exc}") from exc

    data = resp.json()
    code = data.get("code", "")

    if code == "NoRoute":
        raise ValueError("OSRM: no route between the requested points")
    if code != "Ok":
        raise RuntimeError(f"OSRM error: {code} — {data.get('message', '')}")

    leg = data["routes"][0]
    geometry_coords = leg["geometry"]["coordinates"]  # [[lon, lat], ...]

    return {
        "distance_m": leg["distance"],
        "duration_s": leg["duration"],
        "route":      geometry_coords,
        "start":      {"lon": start_lon, "lat": start_lat},
        "end":        {"lon": end_lon,   "lat": end_lat},
    }
