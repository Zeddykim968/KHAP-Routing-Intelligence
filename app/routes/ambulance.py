from fastapi import APIRouter, Query, HTTPException
from app.services.supabase_service import supabase
from app.recommendation_engine import calculate_score

router = APIRouter(prefix="/ambulance", tags=["Emergency"])


@router.get("")
def emergency_nearest(
    lat: float = Query(..., description="Emergency latitude"),
    lon: float = Query(..., description="Emergency longitude"),
    require_beds: bool = Query(True, description="Only return facilities with beds"),
):
    """
    Returns the single closest facility capable of handling an emergency.
    Prioritises hospitals and health centres with beds, open 24 hours.
    """
    EMERGENCY_TYPES = [
        "District Hospital",
        "Provincial General Hospital",
        "Sub-District Hospital",
        "Other Hospital",
        "Medical Centre",
        "Health Centre",
    ]

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

    return {
        "emergency": True,
        "user_location": {"latitude": lat, "longitude": lon},
        "nearest_facility": {
            **best,
            "distance_km": dist_km,
            "estimated_drive_minutes": round((dist_km / 60) * 60),
        },
        "alternatives": [
            {**f, "distance_km": d, "estimated_drive_minutes": round((d / 60) * 60)}
            for _, d, f in scored[1:4]
        ],
    }
