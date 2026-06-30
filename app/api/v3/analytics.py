"""
V3 Analytics API — accessibility, coverage, load, gaps, county rankings.
Uses local PostgreSQL via app/services/db.py.
"""

from fastapi import APIRouter, Query, HTTPException, Request
from app.cache.store import cache
from app.cache.rate_limit import limiter, ANALYTICS_LIMIT, PUBLIC_LIMIT
from app.services.db import query
from app.analytics.accessibility import score_all_counties, score_county
from app.analytics.coverage import underserved_check
from app.analytics.facility_load import compute_facility_loads, county_load_summary
from app.analytics.gap_analysis import find_coverage_gaps, estimate_new_facility_impact, top_candidate_locations

router = APIRouter(prefix="/api/v3/analytics", tags=["V3 · Analytics"])


def _fetch(county=None):
    if county:
        return query(
            "SELECT * FROM facilities WHERE operational_status='Operational' AND county=%s",
            [county],
        )
    return query("SELECT * FROM facilities WHERE operational_status='Operational'")


@router.get("/accessibility")
@limiter.limit(ANALYTICS_LIMIT)
def accessibility(request: Request, county: str = Query(None)):
    key = f"access:{county}"
    hit = cache.get(key)
    if hit:
        return hit
    facilities = _fetch(county)
    if not facilities:
        raise HTTPException(404, "No facilities found")
    if county:
        result = {"county": county, **score_county(facilities)}
    else:
        scores = score_all_counties(facilities)
        result = {
            "total_counties": len(scores),
            "counties": scores,
            "summary": {b: sum(1 for s in scores if s["band"] == b)
                        for b in ["Critical", "Poor", "Moderate", "Good", "Excellent"]},
        }
    cache.set(key, result, ttl=600)
    return result


@router.get("/coverage")
@limiter.limit(PUBLIC_LIMIT)
def coverage(
    request: Request,
    lat: float = Query(...),
    lon: float = Query(...),
    county: str = Query(None),
):
    facilities = _fetch(county)
    if not facilities:
        raise HTTPException(404, "No facilities found")
    return underserved_check(lat, lon, facilities)


@router.get("/facility-load")
@limiter.limit(ANALYTICS_LIMIT)
def facility_load(
    request: Request,
    county: str = Query(None),
    summary: bool = Query(False),
):
    key = f"load:{county}:{summary}"
    hit = cache.get(key)
    if hit:
        return hit
    facilities = _fetch(county)
    if not facilities:
        raise HTTPException(404, "No facilities found")
    if summary:
        result = {"counties": county_load_summary(facilities)}
    else:
        loads = compute_facility_loads(facilities)
        result = {
            "total": len(loads),
            "critical": sum(1 for f in loads if f["load_pressure"] == "Critical"),
            "facilities": loads,
        }
    cache.set(key, result, ttl=600)
    return result


@router.get("/gap-analysis")
@limiter.limit(ANALYTICS_LIMIT)
def gap_analysis(
    request: Request,
    county: str = Query(None),
    top_candidates: bool = Query(False),
):
    key = f"gaps:{county}:{top_candidates}"
    hit = cache.get(key)
    if hit:
        return hit
    facilities = _fetch(county)
    if not facilities:
        raise HTTPException(404, "No facilities found")
    if top_candidates:
        result = {"top_candidate_locations": top_candidate_locations(facilities)}
    else:
        gaps = find_coverage_gaps(facilities)
        result = {
            "coverage_gaps": len(gaps),
            "estimated_population_without_access": len(gaps) * 8000,
            "worst_gaps": gaps[:20],
        }
    cache.set(key, result, ttl=900)
    return result


@router.get("/impact")
@limiter.limit(ANALYTICS_LIMIT)
def new_facility_impact(
    request: Request,
    lat: float = Query(...),
    lon: float = Query(...),
    county: str = Query(None),
    radius_km: float = Query(15),
):
    facilities = _fetch(county)
    if not facilities:
        raise HTTPException(404, "No facilities found")
    return estimate_new_facility_impact(lat, lon, facilities, coverage_radius_km=radius_km)


@router.get("/county-rankings")
@limiter.limit(ANALYTICS_LIMIT)
def county_rankings(request: Request):
    hit = cache.get("county_rankings")
    if hit:
        return hit
    facilities = _fetch()
    if not facilities:
        raise HTTPException(404, "No facilities found")
    scores = score_all_counties(facilities)
    load = county_load_summary(facilities)
    load_map = {c["county"]: c for c in load}
    ranked = [
        {"rank": i, **s,
         "avg_load_score": load_map.get(s["county"], {}).get("avg_load_score"),
         "critical_facilities": load_map.get(s["county"], {}).get("critical_facilities")}
        for i, s in enumerate(reversed(scores), 1)
    ]
    result = {"rankings": ranked, "total": len(ranked)}
    cache.set("county_rankings", result, ttl=900)
    return result
