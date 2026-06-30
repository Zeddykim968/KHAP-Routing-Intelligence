from fastapi import APIRouter, Query, HTTPException
from app.services.db_service import query
from app.services.location_service import resolve_location
from app.recommendation_engine import calculate_score, haversine

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


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
        detail="Provide either lat+lon coordinates or a location name (e.g. location=Kisumu)."
    )


def _build_facilities_query(operational_only, type_, county):
    conditions = []
    params = []
    if operational_only:
        conditions.append("operational_status = %s")
        params.append("Operational")
    if type_:
        conditions.append("type = %s")
        params.append(type_)
    if county:
        conditions.append("county = %s")
        params.append(county)
    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    sql = f"SELECT * FROM facilities {where}"
    return sql, params


@router.get("")
def get_recommendations(
    lat: float = Query(None, description="User's latitude"),
    lon: float = Query(None, description="User's longitude"),
    location: str = Query(None, description="Town or area name e.g. 'Westlands', 'Kisumu'"),
    limit: int = Query(10, ge=1, le=50, description="Number of results to return"),
    type: str = Query(None, description="Filter by facility type"),
    county: str = Query(None, description="Filter by county"),
    radius_km: float = Query(None, description="Only return facilities within this radius (km)"),
    operational_only: bool = Query(True, description="Only return operational facilities"),
):
    lat, lon, resolved_label = _resolve_coords(lat, lon, location)

    sql, params = _build_facilities_query(operational_only, type, county)
    facilities = [f for f in query(sql, params) if f.get("latitude") is not None and f.get("longitude") is not None]

    if not facilities:
        raise HTTPException(status_code=404, detail="No facilities found matching the criteria")

    scored = []
    for facility in facilities:
        score, distance_km = calculate_score(facility, lat, lon)
        if radius_km is not None and distance_km > radius_km:
            continue
        scored.append({**facility, "distance_km": distance_km, "score": round(score, 4)})

    if not scored:
        raise HTTPException(
            status_code=404,
            detail=f"No facilities found within {radius_km}km of the given location",
        )

    scored.sort(key=lambda x: x["score"], reverse=True)

    return {
        "user_location": {
            "latitude": lat,
            "longitude": lon,
            **({"resolved_from": resolved_label} if resolved_label else {}),
        },
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
    lat: float = Query(None, description="User's latitude"),
    lon: float = Query(None, description="User's longitude"),
    location: str = Query(None, description="Town or area name e.g. 'Nakuru', 'Thika'"),
    radius_km: float = Query(20, description="Search radius in km"),
    limit: int = Query(5, ge=1, le=20),
):
    lat, lon, resolved_label = _resolve_coords(lat, lon, location)
    return get_recommendations(
        lat=lat, lon=lon, location=None,
        limit=limit, type=None, county=None,
        radius_km=radius_km, operational_only=True,
    )


@router.get("/types")
def get_facility_types():
    rows = query("SELECT DISTINCT type FROM facilities WHERE type IS NOT NULL ORDER BY type")
    return {"types": [r["type"] for r in rows]}


@router.get("/counties")
def get_counties():
    rows = query("SELECT DISTINCT county FROM facilities WHERE county IS NOT NULL ORDER BY county")
    return {"counties": [r["county"] for r in rows]}


@router.get("/list")
def list_facilities(
    county: str = Query(None, description="Filter by county"),
    type: str = Query(None, description="Filter by facility type"),
    operational_only: bool = Query(True),
    limit: int = Query(500, ge=1, le=2000),
):
    sql, params = _build_facilities_query(operational_only, type, county)
    facilities = [f for f in query(sql, params) if f.get("latitude") is not None and f.get("longitude") is not None]
    return {"results": facilities[:limit], "total": len(facilities)}


@router.get("/facility/{facility_id}")
def get_facility(facility_id: int):
    rows = query("SELECT * FROM facilities WHERE facility_id = %s", (facility_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="Facility not found")
    return rows[0]


@router.get("/search")
def search_facilities(
    q: str = Query(..., min_length=2, description="Search term — facility name or town"),
    limit: int = Query(10, ge=1, le=50),
    operational_only: bool = Query(True),
):
    term = q.strip()
    pattern = f"%{term}%"

    op_filter = "AND operational_status = 'Operational'" if operational_only else ""

    by_name = query(
        f"SELECT * FROM facilities WHERE name ILIKE %s {op_filter} LIMIT %s",
        (pattern, limit)
    )
    by_town = query(
        f"SELECT * FROM facilities WHERE nearest_town ILIKE %s {op_filter} LIMIT %s",
        (pattern, limit)
    )

    seen_ids = set()
    merged = []
    for f in by_name + by_town:
        fid = f.get("facility_id")
        if fid not in seen_ids:
            seen_ids.add(fid)
            merged.append(f)

    term_lower = term.lower()
    merged.sort(key=lambda f: (
        not (f.get("name") or "").lower().startswith(term_lower),
        (f.get("name") or "").lower(),
    ))

    return {"query": q, "total_found": len(merged), "results": merged[:limit]}
