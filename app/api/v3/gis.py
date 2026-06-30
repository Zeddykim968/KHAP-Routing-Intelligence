"""
V3 GIS API — spatial analysis, buffers, catchments, emergency zones, network analysis.
Uses local PostgreSQL via app/services/db.py.
"""

from fastapi import APIRouter, Query, HTTPException, Request
from app.cache.store import cache
from app.cache.rate_limit import limiter, PUBLIC_LIMIT, ANALYTICS_LIMIT
from app.gis.spatial import (
    catchment_area, buffer_circle, nearest_facilities,
    network_analysis_summary, emergency_response_zones, point_in_kenya,
)
from app.services.db import query

router = APIRouter(prefix="/api/v3/gis", tags=["V3 · GIS"])


def _fetch(county=None, operational_only=True):
    clauses = []
    params = []
    if operational_only:
        clauses.append("operational_status = 'Operational'")
    if county:
        clauses.append("county = %s"); params.append(county)
    clauses.append("latitude IS NOT NULL AND longitude IS NOT NULL")
    where = "WHERE " + " AND ".join(clauses)
    return query(f"SELECT * FROM facilities {where}", params or None)


@router.get("/buffer")
@limiter.limit(PUBLIC_LIMIT)
def buffer_analysis(
    request: Request,
    lat: float = Query(...),
    lon: float = Query(...),
    radius_km: float = Query(10, ge=0.5, le=200),
    points: int = Query(64, ge=8, le=128),
):
    if not point_in_kenya(lat, lon):
        raise HTTPException(400, "Coordinates are outside Kenya")
    coords = buffer_circle(lat, lon, radius_km, points)
    return {
        "type": "Feature",
        "geometry": {"type": "Polygon", "coordinates": [coords]},
        "properties": {"center": [lon, lat], "radius_km": radius_km},
    }


@router.get("/catchment")
@limiter.limit(ANALYTICS_LIMIT)
def catchment(
    request: Request,
    lat: float = Query(...),
    lon: float = Query(...),
    radius_km: float = Query(15, ge=1, le=100),
    county: str = Query(None),
):
    facilities = _fetch(county)
    if not facilities:
        raise HTTPException(404, "No facilities found")
    return catchment_area(lat, lon, facilities, radius_km)


@router.get("/nearest")
@limiter.limit(PUBLIC_LIMIT)
def nearest(
    request: Request,
    lat: float = Query(...),
    lon: float = Query(...),
    radius_km: float = Query(50),
    facility_type: str = Query(None),
    limit: int = Query(10, ge=1, le=50),
):
    cache_key = f"gis_nearest:{lat:.4f}:{lon:.4f}:{radius_km}:{facility_type}:{limit}"
    hit = cache.get(cache_key)
    if hit:
        return hit
    facilities = _fetch()
    results = nearest_facilities(lat, lon, facilities, limit=limit,
                                  radius_km=radius_km, facility_type=facility_type)
    if not results:
        raise HTTPException(404, "No facilities found within radius")
    result = {"query": {"lat": lat, "lon": lon, "radius_km": radius_km},
              "count": len(results), "facilities": results}
    cache.set(cache_key, result, ttl=180)
    return result


@router.get("/network-analysis")
@limiter.limit(ANALYTICS_LIMIT)
def network_analysis(request: Request, county: str = Query(None)):
    key = f"network:{county}"
    hit = cache.get(key)
    if hit:
        return hit
    facilities = _fetch(county)
    if not facilities:
        raise HTTPException(404, "No facilities found")
    result = network_analysis_summary(facilities)
    cache.set(key, result, ttl=900)
    return result


@router.get("/emergency-zones")
@limiter.limit(PUBLIC_LIMIT)
def emergency_zones(
    request: Request,
    lat: float = Query(...),
    lon: float = Query(...),
    speed_kmh: float = Query(60, ge=10, le=120),
    county: str = Query(None),
):
    facilities = _fetch(county)
    if not facilities:
        raise HTTPException(404, "No facilities found")
    return emergency_response_zones(lat, lon, facilities, speed_kmh)


@router.get("/county-analysis")
@limiter.limit(ANALYTICS_LIMIT)
def county_analysis(request: Request, county: str = Query(...)):
    key = f"county_analysis:{county}"
    hit = cache.get(key)
    if hit:
        return hit
    facilities = _fetch(county)
    if not facilities:
        raise HTTPException(404, f"No facilities found for county: {county}")

    from app.analytics.gap_analysis import find_coverage_gaps
    network = network_analysis_summary(facilities)
    gaps = find_coverage_gaps(facilities)
    facility_types: dict = {}
    for f in facilities:
        t = f.get("type", "Unknown")
        facility_types[t] = facility_types.get(t, 0) + 1

    result = {
        "county": county,
        "facility_count": len(facilities),
        "network": network,
        "coverage_gaps": len(gaps),
        "facility_types": facility_types,
    }
    cache.set(key, result, ttl=600)
    return result
