"""
V3 Reports API — national, county, and emergency readiness reports.
Uses local PostgreSQL via app/services/db.py.
"""

from fastapi import APIRouter, Query, HTTPException, Request
from app.cache.store import cache
from app.cache.rate_limit import limiter, ANALYTICS_LIMIT
from app.analytics.accessibility import score_all_counties, score_county
from app.analytics.facility_load import county_load_summary, compute_facility_loads
from app.analytics.gap_analysis import find_coverage_gaps, top_candidate_locations
from app.gis.spatial import network_analysis_summary
from app.services.db import query
from datetime import datetime, timezone

router = APIRouter(prefix="/api/v3/reports", tags=["V3 · Reports"])


def _fetch_all(county=None, operational_only=True):
    sql = "SELECT * FROM facilities WHERE latitude IS NOT NULL AND longitude IS NOT NULL"
    params = []
    if operational_only:
        sql += " AND operational_status='Operational'"
    if county:
        sql += " AND county=%s"; params.append(county)
    return query(sql, params or None)


@router.get("/national-summary")
@limiter.limit(ANALYTICS_LIMIT)
def national_summary(request: Request):
    hit = cache.get("national_summary")
    if hit:
        return hit
    facilities = _fetch_all()
    if not facilities:
        raise HTTPException(404, "No facility data available")

    scores = score_all_counties(facilities)
    load = county_load_summary(facilities)
    network = network_analysis_summary(facilities)
    gaps = find_coverage_gaps(facilities)
    by_band = {b: [] for b in ["Critical", "Poor", "Moderate", "Good", "Excellent"]}
    for s in scores:
        by_band[s["band"]].append(s["county"])

    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "version": "3.0",
        "scope": "Kenya — all counties",
        "total_facilities": len(facilities),
        "network": network,
        "coverage_gaps": {
            "total_uncovered_cells": len(gaps),
            "estimated_population_without_access": len(gaps) * 8000,
        },
        "accessibility_summary": {
            "counties_assessed": len(scores),
            "by_band": {k: len(v) for k, v in by_band.items()},
            "counties_by_band": by_band,
            "best_county": scores[-1]["county"] if scores else None,
            "worst_county": scores[0]["county"] if scores else None,
        },
        "load_summary": {
            "high_pressure_counties": [c for c in load if c.get("avg_load_score", 100) < 40],
        },
        "top_intervention_sites": top_candidate_locations(facilities, top_n=5),
    }
    cache.set("national_summary", result, ttl=1800)
    return result


@router.get("/county-report")
@limiter.limit(ANALYTICS_LIMIT)
def county_report(request: Request, county: str = Query(...)):
    key = f"county_report:{county}"
    hit = cache.get(key)
    if hit:
        return hit

    all_f = query("SELECT * FROM facilities WHERE county=%s", [county])
    operational = [f for f in all_f if f.get("operational_status") == "Operational"
                   and f.get("latitude") and f.get("longitude")]
    if not operational:
        raise HTTPException(404, f"No operational facilities found for {county}")

    access = score_county(operational)
    loads = compute_facility_loads(operational)
    gaps = find_coverage_gaps(operational)
    candidates = top_candidate_locations(operational, top_n=3)
    facility_types: dict = {}
    for f in operational:
        t = f.get("type", "Unknown")
        facility_types[t] = facility_types.get(t, 0) + 1

    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "county": county,
        "total_facilities": len(all_f),
        "operational_facilities": len(operational),
        "facility_types": facility_types,
        "accessibility": access,
        "load_analysis": {
            "critical": sum(1 for f in loads if f["load_pressure"] == "Critical"),
            "high": sum(1 for f in loads if f["load_pressure"] == "High"),
            "top_overloaded": [f for f in loads if f["load_pressure"] == "Critical"][:3],
        },
        "coverage_gaps": len(gaps),
        "recommended_new_facility_sites": candidates,
    }
    cache.set(key, result, ttl=900)
    return result


@router.get("/emergency-readiness")
@limiter.limit(ANALYTICS_LIMIT)
def emergency_readiness(request: Request):
    hit = cache.get("emergency_readiness")
    if hit:
        return hit
    facilities = _fetch_all()
    scores = score_all_counties(facilities)
    load = county_load_summary(facilities)
    load_map = {c["county"]: c.get("avg_load_score", 50) for c in load}
    ranked = sorted([
        {
            "county": s["county"],
            "emergency_score": round(
                0.5 * s["score"] + 0.3 * load_map.get(s["county"], 50)
                + 0.2 * s["details"].get("coverage_score", 0), 1),
            "accessibility_band": s["band"],
            "facility_count": s["facility_count"],
        }
        for s in scores
    ], key=lambda x: x["emergency_score"])
    result = {"rankings": ranked, "total_counties": len(ranked)}
    cache.set("emergency_readiness", result, ttl=1800)
    return result
