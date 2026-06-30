from fastapi import APIRouter, Query, HTTPException
from app.services.supabase_service import supabase
from app.services.location_service import resolve_location
from app.recommendation_engine import calculate_score

router = APIRouter(prefix="/ambulance", tags=["Emergency"])

EMERGENCY_TYPES = [
    "District Hospital",
    "Provincial General Hospital",
    "Sub-District Hospital",
    "Other Hospital",
    "Medical Centre",
    "Health Centre",
    "National Referral Hospital",
]


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
    """
    Returns the single closest emergency-capable facility plus 3 alternatives.
    Accepts either lat/lon coordinates or a plain location name.
    """
    lat, lon, resolved_label = _resolve_coords(lat, lon, location)

    response = (
        supabase.table("facilities")
        .select("*")
        .eq("operational_status", "Operational")
        .in_("type", EMERGENCY_TYPES)
        .execute()
    )
    facilities = [
        f for f in response.data
        if f.get("latitude") is not None and f.get("longitude") is not None
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
    _, dist_km, best = scored[0]

    def fmt(f, d):
        return {
            **f,
            "distance_km": d,
            "estimated_drive_minutes": round((d * 1.35 / 60) * 60),
        }

    return {
        "emergency": True,
        "search_location": resolved_label or {"latitude": lat, "longitude": lon},
        "nearest_facility": fmt(best, dist_km),
        "alternatives": [fmt(f, d) for _, d, f in scored[1:4]],
    }
