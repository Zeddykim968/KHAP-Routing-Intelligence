from fastapi import APIRouter, Query, HTTPException
from app.services.supabase_service import supabase
from app.analytics.accessibility import score_all_counties, score_county
from app.analytics.coverage import coverage_from_point, underserved_check
from app.analytics.facility_load import compute_facility_loads, county_load_summary
from app.analytics.gap_analysis import (
    find_coverage_gaps,
    estimate_new_facility_impact,
    top_candidate_locations,
)

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


def _fetch_facilities(county: str = None, operational_only: bool = True):
    query = supabase.table("facilities").select("*")
    if operational_only:
        query = query.eq("operational_status", "Operational")
    if county:
        query = query.eq("county", county)
    return query.execute().data


@router.get("/accessibility")
def accessibility_scores(
    county: str = Query(None, description="Filter to a single county (omit for all Kenya)"),
):
    """
    Returns accessibility scores for all counties (or a single county).
    Score = 40% Travel Time + 30% Facility Density + 20% Coverage + 10% Facility Level.
    """
    facilities = _fetch_facilities(county)
    if not facilities:
        raise HTTPException(status_code=404, detail="No facilities found")

    if county:
        result = score_county(facilities)
        return {"county": county, **result}

    results = score_all_counties(facilities)
    return {
        "total_counties": len(results),
        "counties": results,
        "summary": {
            "critical": sum(1 for r in results if r["band"] == "Critical"),
            "poor": sum(1 for r in results if r["band"] == "Poor"),
            "moderate": sum(1 for r in results if r["band"] == "Moderate"),
            "good": sum(1 for r in results if r["band"] == "Good"),
            "excellent": sum(1 for r in results if r["band"] == "Excellent"),
        },
    }


@router.get("/coverage")
def coverage_analysis(
    lat: float = Query(..., description="Latitude of point to analyse"),
    lon: float = Query(..., description="Longitude of point to analyse"),
    county: str = Query(None, description="Limit facilities to a county"),
):
    """
    Returns facility counts within 5, 10, 20, and 50 km of the given point.
    Also flags whether the location is underserved.
    """
    facilities = _fetch_facilities(county)
    if not facilities:
        raise HTTPException(status_code=404, detail="No facilities found")
    return underserved_check(lat, lon, facilities)


@router.get("/facility-load")
def facility_load(
    county: str = Query(None, description="Filter to a county"),
    summary: bool = Query(False, description="Return county-level summary instead of per-facility"),
):
    """
    Returns load pressure scores for facilities.
    High load = few neighbours within 15 km catchment.
    """
    facilities = _fetch_facilities(county)
    if not facilities:
        raise HTTPException(status_code=404, detail="No facilities found")

    if summary:
        return {"counties": county_load_summary(facilities)}

    loads = compute_facility_loads(facilities)
    return {
        "total_facilities": len(loads),
        "critical_count": sum(1 for f in loads if f["load_pressure"] == "Critical"),
        "facilities": loads,
    }


@router.get("/gap-analysis")
def gap_analysis(
    county: str = Query(None, description="Limit analysis to a county"),
    top_candidates: bool = Query(False, description="Return top candidate locations for a new facility"),
):
    """
    Identifies geographic areas with no health facility within 15 km.
    Optionally returns the best locations to place a new facility.
    """
    facilities = _fetch_facilities(county)
    if not facilities:
        raise HTTPException(status_code=404, detail="No facilities found")

    if top_candidates:
        candidates = top_candidate_locations(facilities)
        return {
            "top_candidate_locations": candidates,
            "note": "Locations ranked by estimated number of people who would gain access.",
        }

    gaps = find_coverage_gaps(facilities)
    total_population_in_gaps = len(gaps) * 8000
    return {
        "coverage_gaps": len(gaps),
        "estimated_population_without_access": total_population_in_gaps,
        "worst_gaps": gaps[:20],
    }


@router.get("/impact")
def new_facility_impact(
    lat: float = Query(..., description="Candidate facility latitude"),
    lon: float = Query(..., description="Candidate facility longitude"),
    county: str = Query(None, description="Limit analysis to a county"),
    radius_km: float = Query(15, description="Coverage radius of the new facility"),
):
    """
    Estimates how many people would gain access to care if a new facility
    were built at the given location.
    """
    facilities = _fetch_facilities(county)
    if not facilities:
        raise HTTPException(status_code=404, detail="No facilities found")
    return estimate_new_facility_impact(lat, lon, facilities, coverage_radius_km=radius_km)
