from fastapi import APIRouter, Query, HTTPException
from app.services.supabase_service import supabase
from app.recommendation_engine import calculate_score, haversine

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.get("")
def get_recommendations(
    lat: float = Query(..., description="User's latitude"),
    lon: float = Query(..., description="User's longitude"),
    limit: int = Query(10, ge=1, le=50, description="Number of results to return"),
    type: str = Query(None, description="Filter by facility type"),
    county: str = Query(None, description="Filter by county"),
    radius_km: float = Query(None, description="Only return facilities within this radius (km)"),
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

    facilities = [f for f in facilities if f.get("latitude") is not None and f.get("longitude") is not None]

    if not facilities:
        raise HTTPException(status_code=404, detail="No facilities found matching the criteria")

    scored = []
    for facility in facilities:
        score, distance_km = calculate_score(facility, lat, lon)
        if radius_km is not None and distance_km > radius_km:
            continue
        scored.append({
            **facility,
            "distance_km": distance_km,
            "score": round(score, 4),
        })

    if not scored:
        raise HTTPException(
            status_code=404,
            detail=f"No facilities found within {radius_km}km of the given location",
        )

    scored.sort(key=lambda x: x["score"], reverse=True)

    return {
        "user_location": {"latitude": lat, "longitude": lon},
        "filters": {
            "type": type,
            "county": county,
            "radius_km": radius_km,
            "operational_only": operational_only,
        },
        "total_found": len(scored),
        "results": scored[:limit],
    }


@router.get("/nearby")
def get_nearby(
    lat: float = Query(..., description="User's latitude"),
    lon: float = Query(..., description="User's longitude"),
    radius_km: float = Query(20, description="Search radius in km"),
    limit: int = Query(5, ge=1, le=20),
):
    return get_recommendations(
        lat=lat, lon=lon, limit=limit, type=None,
        county=None, radius_km=radius_km, operational_only=True,
    )


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


@router.get("/list")
def list_facilities(
    county: str = Query(None, description="Filter by county"),
    type: str = Query(None, description="Filter by facility type"),
    operational_only: bool = Query(True),
    limit: int = Query(500, ge=1, le=2000),
):
    """Returns all facilities without requiring coordinates — used for map rendering."""
    query = supabase.table("facilities").select("*")
    if operational_only:
        query = query.eq("operational_status", "Operational")
    if type:
        query = query.eq("type", type)
    if county:
        query = query.eq("county", county)
    response = query.execute()
    facilities = [
        f for f in response.data
        if f.get("latitude") is not None and f.get("longitude") is not None
    ]
    return {"results": facilities[:limit], "total": len(facilities)}


@router.get("/facility/{facility_id}")
def get_facility(facility_id: int):
    response = supabase.table("facilities").select("*").eq("facility_id", facility_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Facility not found")
    return response.data[0]


@router.get("/search")
def search_facilities(
    q: str = Query(..., min_length=2, description="Search term — facility name or town"),
    limit: int = Query(10, ge=1, le=50),
    operational_only: bool = Query(True),
):
    """
    Full-text name search across all 7,406 facilities.
    Matches on facility name OR nearest town (case-insensitive, substring match).
    Filters are pushed to Supabase so the full dataset is searched.
    """
    term = q.strip()
    pattern = f"%{term}%"

    by_name = supabase.table("facilities").select("*").ilike("name", pattern)
    by_town = supabase.table("facilities").select("*").ilike("nearest_town", pattern)

    if operational_only:
        by_name = by_name.eq("operational_status", "Operational")
        by_town = by_town.eq("operational_status", "Operational")

    name_results = by_name.limit(limit).execute().data
    town_results = by_town.limit(limit).execute().data

    seen_ids = set()
    merged = []
    for f in name_results + town_results:
        fid = f.get("facility_id")
        if fid not in seen_ids:
            seen_ids.add(fid)
            merged.append(f)

    term_lower = term.lower()
    merged.sort(key=lambda f: (
        not (f.get("name") or "").lower().startswith(term_lower),
        (f.get("name") or "").lower(),
    ))

    return {
        "query": q,
        "total_found": len(merged),
        "results": merged[:limit],
    }
