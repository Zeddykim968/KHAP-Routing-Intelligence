"""
Smart routing — emergency-aware, insurance-aware, road-routed recommendations.
"""

import httpx
from fastapi import APIRouter, Query, HTTPException
from app.services.db_service import query
from app.services.location_service import resolve_location
from app.services.enrichment import (
    enrich_facility, emergency_type_score,
    EMERGENCY_CAPABILITIES, ALL_INSURANCE_PROVIDERS,
)
from app.recommendation_engine import haversine

router = APIRouter(prefix="/smart", tags=["Smart Routing"])

AVG_SPEED_KMH = 40


def _resolve_coords(lat, lon, location):
    if lat is not None and lon is not None:
        return lat, lon, None
    if location:
        resolved = resolve_location(location)
        if not resolved:
            raise HTTPException(404, f"Location '{location}' not found.")
        return resolved["latitude"], resolved["longitude"], resolved["label"]
    raise HTTPException(422, "Provide lat+lon or a location name.")


# ─── Meta ─────────────────────────────────────────────────────────────────────

@router.get("/emergency-types")
def list_emergency_types():
    return {
        "emergency_types": [
            {"id": k, "label": v["label"], "icon": v["icon"]}
            for k, v in EMERGENCY_CAPABILITIES.items()
        ]
    }


@router.get("/insurance-providers")
def list_insurance_providers():
    return {"insurance_providers": ALL_INSURANCE_PROVIDERS}


# ─── Smart Recommendations ────────────────────────────────────────────────────

@router.get("/recommend")
def smart_recommend(
    lat: float = Query(None, description="User latitude"),
    lon: float = Query(None, description="User longitude"),
    location: str = Query(None, description="Town / area name e.g. 'Westlands'"),
    emergency_type: str = Query("general", description="Emergency type id e.g. cardiac, trauma, maternity"),
    insurance: str = Query(None, description="Insurance provider e.g. NHIF, AAR, Jubilee"),
    financial_level: str = Query(None, description="Financial tier: Low / Medium / High / Free/Subsidized / Any"),
    radius_km: float = Query(50, ge=1, le=300, description="Search radius km"),
    limit: int = Query(10, ge=1, le=30),
):
    """
    Returns ranked hospitals/clinics for the given emergency type and
    optional insurance/financial-level filters.

    Scoring weights:
      - Distance     30 %
      - Emergency match 35 %
      - Availability 20 %
      - Capacity     15 %
    """
    lat, lon, resolved_label = _resolve_coords(lat, lon, location)

    cfg = EMERGENCY_CAPABILITIES.get(emergency_type, EMERGENCY_CAPABILITIES["general"])

    rows = query("SELECT * FROM facilities WHERE operational_status = 'Operational' AND latitude IS NOT NULL AND longitude IS NOT NULL")

    results = []
    for f in rows:
        dist = haversine(lat, lon, f["latitude"], f["longitude"])
        if dist > radius_km:
            continue

        enrich_facility(f)

        # Insurance filter
        if insurance:
            if insurance not in f["insurance_providers"]:
                continue

        # Financial level filter
        if financial_level and financial_level.lower() not in ("any", ""):
            if f["financial_level"].lower() != financial_level.lower():
                continue

        # Scoring
        dist_score  = max(0, 100 - (dist / radius_km) * 100)
        emerg_score = emergency_type_score(f, emergency_type)
        beds        = (f.get("beds") or 0) + (f.get("cots") or 0)
        cap_score   = min(100, beds * 2) if beds > 0 else 15
        avail_score = 0
        if f.get("open_24_hours"):
            avail_score += 60
        if f.get("open_weekends"):
            avail_score += 40

        composite = (
            0.30 * dist_score +
            0.35 * emerg_score +
            0.15 * cap_score +
            0.20 * avail_score
        )

        road_km  = round(dist * 1.35, 2)
        est_min  = round((road_km / AVG_SPEED_KMH) * 60)

        results.append({
            **f,
            "distance_km":          round(dist, 2),
            "estimated_road_km":    road_km,
            "estimated_minutes":    est_min,
            "score":                round(composite, 2),
            "emergency_match_score": round(emerg_score, 1),
            "match_reason":         _match_reason(f, emergency_type, cfg),
        })

    if not results:
        raise HTTPException(
            404,
            f"No facilities found within {radius_km}km matching your criteria. "
            "Try widening the radius or removing insurance/financial filters."
        )

    results.sort(key=lambda x: x["score"], reverse=True)

    return {
        "query": {
            "location": resolved_label or {"latitude": lat, "longitude": lon},
            "emergency_type": {"id": emergency_type, "label": cfg["label"], "icon": cfg["icon"]},
            "insurance_filter": insurance,
            "financial_filter": financial_level,
            "radius_km": radius_km,
        },
        "total_found": len(results),
        "results": results[:limit],
    }


def _match_reason(facility: dict, emergency_type: str, cfg: dict) -> str:
    reasons = []
    ftype = facility.get("type", "")
    preferred = cfg.get("preferred_types") or []

    if preferred and ftype == preferred[0]:
        reasons.append(f"Best facility type for {cfg['label']}")
    elif preferred and ftype in preferred:
        reasons.append(f"Suitable for {cfg['label']}")

    if facility.get("open_24_hours"):
        reasons.append("Open 24 hours")
    if facility.get("open_weekends"):
        reasons.append("Open weekends")

    beds = (facility.get("beds") or 0) + (facility.get("cots") or 0)
    if beds >= 50:
        reasons.append(f"{beds} beds/cots")
    elif beds > 0:
        reasons.append(f"{beds} beds/cots")

    ins = facility.get("insurance_providers", [])
    if ins:
        reasons.append(f"Accepts: {', '.join(ins[:3])}")

    fl = facility.get("financial_level", "")
    if fl:
        reasons.append(f"{fl} cost")

    return " · ".join(reasons) if reasons else "General facility"


# ─── Road Routing (OSRM) ─────────────────────────────────────────────────────

@router.get("/road-route")
def road_route(
    from_lat: float = Query(...),
    from_lon: float = Query(...),
    to_lat: float = Query(...),
    to_lon: float = Query(...),
):
    """
    Returns a real road route geometry using the OSRM public demo server.
    Falls back to straight-line estimate if OSRM is unavailable.
    """
    try:
        url = (
            f"https://router.project-osrm.org/route/v1/driving/"
            f"{from_lon},{from_lat};{to_lon},{to_lat}"
        )
        resp = httpx.get(
            url,
            params={"overview": "full", "geometries": "geojson", "steps": "false"},
            timeout=8,
            headers={"User-Agent": "KHAP-Routing/1.0"},
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("routes"):
                r = data["routes"][0]
                return {
                    "source": "osrm",
                    "distance_km": round(r["distance"] / 1000, 2),
                    "duration_minutes": round(r["duration"] / 60),
                    "geometry": r["geometry"],
                }
    except Exception:
        pass

    # Straight-line fallback
    dist = haversine(from_lat, from_lon, to_lat, to_lon)
    road_km = round(dist * 1.35, 2)
    return {
        "source": "estimate",
        "distance_km": road_km,
        "duration_minutes": round((road_km / AVG_SPEED_KMH) * 60),
        "geometry": {
            "type": "LineString",
            "coordinates": [[from_lon, from_lat], [to_lon, to_lat]],
        },
    }


# ─── Population Served ────────────────────────────────────────────────────────

@router.get("/population-served")
def population_served(
    lat: float = Query(None, description="Facility latitude"),
    lon: float = Query(None, description="Facility longitude"),
    location: str = Query(None, description="Facility location name"),
    radius_km: float = Query(10, ge=1, le=100, description="Catchment radius km"),
):
    """
    Estimates the catchment population and competing facilities around a point.
    Uses Kenya average population density (~100 persons/km²) as a baseline.
    """
    lat, lon, resolved_label = _resolve_coords(lat, lon, location)

    rows = query(
        """
        SELECT name, type, county, district, operational_status, latitude, longitude,
               beds, cots, open_24_hours
        FROM facilities
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL
        """
    )

    within = []
    for r in rows:
        d = haversine(lat, lon, r["latitude"], r["longitude"])
        if d <= radius_km:
            within.append({**r, "distance_km": round(d, 2)})

    within.sort(key=lambda x: x["distance_km"])

    area_km2 = 3.14159 * radius_km ** 2
    est_population = round(area_km2 * 100)

    operational = [f for f in within if f.get("operational_status") == "Operational"]
    total_capacity = sum(
        (f.get("beds") or 0) + (f.get("cots") or 0) for f in operational
    )

    if operational:
        beds_per_1000 = round((total_capacity / est_population) * 1000, 2)
        people_per_facility = round(est_population / len(operational))
    else:
        beds_per_1000 = 0
        people_per_facility = est_population

    who_benchmark = 10
    status = "Above WHO benchmark" if beds_per_1000 >= who_benchmark else "Below WHO benchmark"

    return {
        "centre": resolved_label or {"latitude": lat, "longitude": lon},
        "radius_km": radius_km,
        "catchment": {
            "estimated_population": est_population,
            "area_km2": round(area_km2, 1),
            "total_facilities": len(within),
            "operational_facilities": len(operational),
            "total_beds_cots": total_capacity,
            "beds_per_1000_people": beds_per_1000,
            "people_per_facility": people_per_facility,
            "who_beds_benchmark_per_1000": who_benchmark,
            "benchmark_status": status,
        },
        "nearest_facilities": [
            {
                "name": f["name"], "type": f["type"],
                "county": f["county"], "distance_km": f["distance_km"],
                "beds": (f.get("beds") or 0) + (f.get("cots") or 0),
                "open_24h": f.get("open_24_hours", False),
            }
            for f in within[:10]
        ],
    }
