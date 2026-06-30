"""
V3 Routing API — road routing, travel times, nearest facility.
Uses local PostgreSQL for facility data.
"""

from fastapi import APIRouter, Query, HTTPException, Request
from app.cache.store import cache
from app.cache.rate_limit import limiter, PUBLIC_LIMIT
from app.routing.travel_time import get_travel_time
from app.routing.shortest_path import get_route_geometry
from app.gis.spatial import nearest_facilities
from app.services.db import query

router = APIRouter(prefix="/api/v3/routing", tags=["V3 · Routing"])


def _get_facilities(ftype=None):
    if ftype:
        return query(
            "SELECT * FROM facilities WHERE operational_status='Operational' AND type=%s AND latitude IS NOT NULL AND longitude IS NOT NULL",
            [ftype],
        )
    return query(
        "SELECT * FROM facilities WHERE operational_status='Operational' AND latitude IS NOT NULL AND longitude IS NOT NULL"
    )


@router.get("/nearest-facility")
@limiter.limit(PUBLIC_LIMIT)
async def nearest_facility(
    request: Request,
    lat: float = Query(...),
    lon: float = Query(...),
    facility_type: str = Query(None),
    radius_km: float = Query(50),
    limit: int = Query(5, ge=1, le=20),
    with_route: bool = Query(False),
):
    cache_key = f"nearest:{lat:.4f}:{lon:.4f}:{facility_type}:{radius_km}:{limit}:{with_route}"
    hit = cache.get(cache_key)
    if hit:
        return hit

    facilities = _get_facilities(ftype=facility_type)
    nearby = nearest_facilities(lat, lon, facilities, limit=limit, radius_km=radius_km)
    if not nearby:
        raise HTTPException(404, "No facilities found within radius")

    results = []
    for f in nearby:
        entry = {**f}
        if with_route:
            travel = await get_travel_time(lat, lon, f["latitude"], f["longitude"])
            route = await get_route_geometry(lat, lon, f["latitude"], f["longitude"])
            entry["travel"] = travel
            entry["route_geometry"] = route.get("geometry")
        results.append(entry)

    result = {
        "query": {"lat": lat, "lon": lon, "radius_km": radius_km},
        "count": len(results),
        "facilities": results,
    }
    cache.set(cache_key, result, ttl=180)
    return result


@router.get("/route")
@limiter.limit(PUBLIC_LIMIT)
async def get_route(
    request: Request,
    from_lat: float = Query(...),
    from_lon: float = Query(...),
    to_lat: float = Query(...),
    to_lon: float = Query(...),
):
    cache_key = f"route:{from_lat:.4f}:{from_lon:.4f}:{to_lat:.4f}:{to_lon:.4f}"
    hit = cache.get(cache_key)
    if hit:
        return hit
    result = await get_route_geometry(from_lat, from_lon, to_lat, to_lon)
    cache.set(cache_key, result, ttl=600)
    return result


@router.get("/travel-time")
@limiter.limit(PUBLIC_LIMIT)
async def travel_time(
    request: Request,
    from_lat: float = Query(...),
    from_lon: float = Query(...),
    to_lat: float = Query(...),
    to_lon: float = Query(...),
):
    cache_key = f"tt:{from_lat:.4f}:{from_lon:.4f}:{to_lat:.4f}:{to_lon:.4f}"
    hit = cache.get(cache_key)
    if hit:
        return hit
    result = await get_travel_time(from_lat, from_lon, to_lat, to_lon)
    cache.set(cache_key, result, ttl=600)
    return result


@router.get("/driving-routes")
@limiter.limit(PUBLIC_LIMIT)
async def driving_routes(
    request: Request,
    from_lat: float = Query(...),
    from_lon: float = Query(...),
    to_lat: float = Query(...),
    to_lon: float = Query(...),
):
    route = await get_route_geometry(from_lat, from_lon, to_lat, to_lon)
    travel = await get_travel_time(from_lat, from_lon, to_lat, to_lon)
    return {
        "origin": {"lat": from_lat, "lon": from_lon},
        "destination": {"lat": to_lat, "lon": to_lon},
        "distance_km": travel["distance_km"],
        "duration_minutes": travel["duration_minutes"],
        "routing_method": travel["method"],
        "geometry": route.get("geometry"),
    }
