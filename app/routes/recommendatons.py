from fastapi import APIRouter, Query, HTTPException
from app.services.supabase_service import fetch_all, fetch_one, search_ilike
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


def _fetch_facilities(operational_only: bool, type_: str | None, county: str | None) -> list[dict]:
    filters: dict = {}
    if operational_only:
        filters["operational_status"] = "Operational"
    if type_:
        filters["type"] = type_
    if county:
        filters["county"] = county
    return [f for f in fetch_all(filters=filters) if f.get("latitude") is not None and f.get("longitude") is not None]


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
    facilities = _fetch_facilities(operational_only, type, county)

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
    lat, lon, _ = _resolve_coords(lat, lon, location)
    return get_recommendations(
        lat=lat, lon=lon, location=None,
        limit=limit, type=None, county=None,
        radius_km=radius_km, operational_only=True,
    )


@router.get("/types")
def get_facility_types():
    rows = fetch_all(columns="type")
    types = sorted(set(r["type"] for r in rows if r.get("type")))
    return {"types": types}


@router.get("/counties")
def get_counties():
    rows = fetch_all(columns="county")
    counties = sorted(set(r["county"] for r in rows if r.get("county")))
    return {"counties": counties}


@router.get("/list")
def list_facilities(
    county: str = Query(None, description="Filter by county"),
    type: str = Query(None, description="Filter by facility type"),
    operational_only: bool = Query(True),
    limit: int = Query(None, ge=1, description="Max results to return; omit to return all"),
):
    facilities = _fetch_facilities(operational_only, type, county)
    results = facilities[:limit] if limit else facilities
    return {"results": results, "total": len(facilities)}


@router.get("/facility/{facility_id}")
def get_facility(facility_id: int):
    facility = fetch_one(facility_id)
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")
    return facility


@router.get("/suggest")
def suggest_facilities(
    q: str = Query(..., min_length=1, description="Partial search term for autocomplete"),
    limit: int = Query(8, ge=1, le=20),
):
    term = q.strip()
    rows = search_ilike("name", term, operational_only=False, limit=limit)
    return {
        "suggestions": [
            {
                "facility_id": f.get("facility_id"),
                "name": f.get("name"),
                "type": f.get("type"),
                "county": f.get("county"),
                "operational_status": f.get("operational_status"),
                "latitude": f.get("latitude"),
                "longitude": f.get("longitude"),
            }
            for f in rows
        ]
    }


@router.get("/geocode")
def geocode(
    q: str = Query(..., min_length=2, description="Free-text place name — road, landmark, estate, town"),
):
    """
    Real geocoding for arbitrary place names (roads, landmarks, bus stops) —
    not limited to the facilities dataset. Backed by Nominatim (OpenStreetMap),
    scoped to Kenya, with a facilities-table fallback for local landmarks.
    Returns a single best-match pin, or null if nothing was found.
    """
    resolved = resolve_location(q.strip())
    if not resolved:
        return {"result": None}
    return {
        "result": {
            "label": resolved["label"],
            "latitude": resolved["latitude"],
            "longitude": resolved["longitude"],
            "source": "geocode",
        }
    }


@router.get("/search")
def search_facilities(
    q: str = Query(..., min_length=2, description="Search term — facility name or town"),
    limit: int = Query(10, ge=1, le=50),
    operational_only: bool = Query(True),
):
    term = q.strip()
    by_name = search_ilike("name", term, operational_only=operational_only, limit=limit)
    by_town = search_ilike("nearest_town", term, operational_only=operational_only, limit=limit)

    seen_ids: set = set()
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
