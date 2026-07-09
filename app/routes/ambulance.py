import httpx
from fastapi import APIRouter, Query, HTTPException
from app.services.supabase_service import fetch_all
from app.services.location_service import resolve_location
from app.recommendation_engine import calculate_score

router = APIRouter(prefix="/ambulance", tags=["Emergency"])

OSRM_BASE = "https://router.project-osrm.org/route/v1/driving"
OSRM_HEADERS = {"User-Agent": "KHAP-Routing/1.0"}


def _osrm_summary(from_lon, from_lat, to_lon, to_lat, timeout=5):
    """Lightweight OSRM call for real road distance + duration (no geometry/steps)."""
    try:
        resp = httpx.get(
            f"{OSRM_BASE}/{from_lon},{from_lat};{to_lon},{to_lat}",
            params={"overview": "false", "steps": "false"},
            timeout=timeout,
            headers=OSRM_HEADERS,
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == "Ok" and data.get("routes"):
                r = data["routes"][0]
                return {
                    "road_km": round(r["distance"] / 1000, 2),
                    "dur_min": round(r["duration"] / 60),
                }
    except Exception:
        pass
    return None


EMERGENCY_TYPES = {
    "District Hospital",
    "Provincial General Hospital",
    "Sub-District Hospital",
    "Other Hospital",
    "Medical Centre",
    "Health Centre",
    "National Referral Hospital",
}


def _resolve_coords(lat, lon, location):
    if lat is not None and lon is not None:
        return lat, lon, None
    if location:
        resolved = resolve_location(location)
        if not resolved:
            raise HTTPException(
                status_code=404,
                detail=f"Location '{location}' not found. Try a town, area, or county name."
            )
        return resolved["latitude"], resolved["longitude"], resolved["label"]
    raise HTTPException(
        status_code=422,
        detail="Provide either lat+lon coordinates or a location name (e.g. location=Westlands)."
    )


@router.get("")
def emergency_nearest(
    lat: float = Query(None, description="Emergency latitude"),
    lon: float = Query(None, description="Emergency longitude"),
    location: str = Query(None, description="Town or area name e.g. 'Thika', 'Eldoret'"),
    require_beds: bool = Query(True, description="Only return facilities with beds"),
):
    lat, lon, resolved_label = _resolve_coords(lat, lon, location)

    rows = fetch_all(filters={"operational_status": "Operational"})
    facilities = [
        f for f in rows
        if f.get("type") in EMERGENCY_TYPES
        and f.get("latitude") is not None
        and f.get("longitude") is not None
    ]

    if require_beds:
        with_beds = [f for f in facilities if (f.get("beds") or 0) + (f.get("cots") or 0) > 0]
        if with_beds:
            facilities = with_beds

    if not facilities:
        raise HTTPException(status_code=404, detail="No emergency-capable facilities found.")

    scored = []
    for f in facilities:
        score, dist_km = calculate_score(f, lat, lon)
        scored.append((score, dist_km, f))

    scored.sort(key=lambda x: (x[0], -x[1]), reverse=True)
    top = scored[:4]  # best + up to 3 alternatives — try real OSRM routing on each

    def fmt(f, d):
        osrm = _osrm_summary(lon, lat, f["longitude"], f["latitude"])
        if osrm:
            road_km = osrm["road_km"]
            dur_min = osrm["dur_min"]
            eta_source = "osrm"
        else:
            road_km = round(d * 1.35, 2)
            dur_min = round((road_km / 40) * 60)
            eta_source = "estimate"
        return {
            **f,
            "distance_km": d,
            "estimated_road_km": road_km,
            "estimated_drive_minutes": dur_min,
            "eta_source": eta_source,
        }

    formatted = [fmt(f, d) for _, d, f in top]

    return {
        "emergency": True,
        "search_location": resolved_label or {"latitude": lat, "longitude": lon},
        "nearest_facility": formatted[0],
        "alternatives": formatted[1:],
    }
