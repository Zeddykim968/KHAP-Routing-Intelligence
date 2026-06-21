from fastapi import APIRouter, Query, HTTPException
from app.services.supabase_service import supabase
from app.routing.travel_time import get_travel_time
from app.routing.shortest_path import get_route_geometry
from app.recommendation_engine import calculate_score

router = APIRouter(prefix="/api/routing", tags=["Routing"])


@router.get("/travel-time")
async def travel_time(
    from_lat: float = Query(..., description="Origin latitude"),
    from_lon: float = Query(..., description="Origin longitude"),
    to_lat: float = Query(..., description="Destination latitude"),
    to_lon: float = Query(..., description="Destination longitude"),
):
    result = await get_travel_time(from_lat, from_lon, to_lat, to_lon)
    return result


@router.get("/route")
async def get_route(
    from_lat: float = Query(..., description="Origin latitude"),
    from_lon: float = Query(..., description="Origin longitude"),
    to_lat: float = Query(..., description="Destination latitude"),
    to_lon: float = Query(..., description="Destination longitude"),
):
    result = await get_route_geometry(from_lat, from_lon, to_lat, to_lon)
    return result


@router.get("/nearest")
async def nearest_with_route(
    lat: float = Query(..., description="User latitude"),
    lon: float = Query(..., description="User longitude"),
    limit: int = Query(5, ge=1, le=20),
    facility_type: str = Query(None, description="Filter by facility type"),
):
    """
    Returns the nearest facilities with real road travel times via OSRM.
    """
    query = supabase.table("facilities").select("*").eq("operational_status", "Operational")
    if facility_type:
        query = query.eq("type", facility_type)

    response = query.execute()
    facilities = [
        f for f in response.data
        if f.get("latitude") and f.get("longitude")
    ]

    if not facilities:
        raise HTTPException(status_code=404, detail="No facilities found")

    scored = []
    for f in facilities:
        _, dist_km = calculate_score(f, lat, lon)
        scored.append((dist_km, f))

    scored.sort(key=lambda x: x[0])
    top = scored[:limit]

    results = []
    for dist_km, f in top:
        travel = await get_travel_time(lat, lon, f["latitude"], f["longitude"])
        results.append({
            **f,
            "straight_line_km": round(dist_km, 2),
            "road_distance_km": travel["distance_km"],
            "travel_time_minutes": travel["duration_minutes"],
            "routing_method": travel["method"],
        })

    return {
        "user_location": {"latitude": lat, "longitude": lon},
        "results": results,
    }
