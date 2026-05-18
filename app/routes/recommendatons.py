from fastapi import APIRouter, Query, HTTPException
from app.services.supabase_service import supabase
from app.recommendation_engine import calculate_score, haversine

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("")
def get_recommendations(
    lat: float = Query(..., description="User's latitude"),
    lon: float = Query(..., description="User's longitude"),
    limit: int = Query(10, ge=1, le=50, description="Number of results to return"),
    type: str = Query(None, description="Filter by facility type"),
    county: str = Query(None, description="Filter by county"),
    operational_only: bool = Query(True, description="Only return operational facilities"),
):
    query = supabase.table("facilities").select("*")

    if operational_only:
        query = query.eq("operational_status", "Operational")
    if type:
        query = query.eq("type", type)
    if county:
        query = query.eq("county", county)

    response = query.execute()
    facilities = response.data

    # Filter out facilities without coordinates
    facilities = [f for f in facilities if f.get("latitude") is not None and f.get("longitude") is not None]

    if not facilities:
        raise HTTPException(status_code=404, detail="No facilities found matching the criteria")

    # Score and rank each facility
    scored = []
    for facility in facilities:
        score = calculate_score(facility, lat, lon)
        scored.append({**facility, "score": round(score, 4)})

    scored.sort(key=lambda x: x["score"], reverse=True)

    return {
        "user_location": {"latitude": lat, "longitude": lon},
        "total_found": len(scored),
        "results": scored[:limit],
    }


@router.get("/types")
def get_facility_types():
    response = supabase.table("facilities").select("type").execute()
    types = sorted(set(f["type"] for f in response.data if f.get("type")))
    return {"types": types}


@router.get("/counties")
def get_counties():
    response = supabase.table("facilities").select("county").execute()
    counties = sorted(set(f["county"] for f in response.data if f.get("county")))
    return {"counties": counties}
