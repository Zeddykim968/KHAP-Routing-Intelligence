"""
Smart routing — emergency-aware, insurance-aware, road-routed recommendations.
"""

import httpx
from fastapi import APIRouter, Query, HTTPException
from app.services.supabase_service import fetch_all
from app.services.location_service import resolve_location
from app.services.enrichment import (
    enrich_facility, emergency_type_score,
    EMERGENCY_CAPABILITIES, ALL_INSURANCE_PROVIDERS,
)
from app.recommendation_engine import haversine

router = APIRouter(prefix="/smart", tags=["Smart Routing"])

AVG_SPEED_KMH = 40
OSRM_BASE = "https://router.project-osrm.org/route/v1/driving"
OSRM_HEADERS = {"User-Agent": "KHAP-Routing/1.0"}

# ─── Turn-by-turn helpers ─────────────────────────────────────────────────────

_MANEUVER_TEXT = {
    ("depart",     "left"):        "Head left on",
    ("depart",     "right"):       "Head right on",
    ("depart",     "straight"):    "Head straight on",
    ("depart",     ""):            "Depart on",
    ("turn",       "left"):        "Turn left onto",
    ("turn",       "right"):       "Turn right onto",
    ("turn",       "sharp left"):  "Take a sharp left onto",
    ("turn",       "sharp right"): "Take a sharp right onto",
    ("turn",       "slight left"): "Keep slight left onto",
    ("turn",       "slight right"):"Keep slight right onto",
    ("turn",       "uturn"):       "Make a U-turn",
    ("continue",   "straight"):    "Continue straight on",
    ("continue",   "left"):        "Keep left on",
    ("continue",   "right"):       "Keep right on",
    ("fork",       "left"):        "Take the left fork onto",
    ("fork",       "right"):       "Take the right fork onto",
    ("merge",      "left"):        "Merge left onto",
    ("merge",      "right"):       "Merge right onto",
    ("roundabout", ""):            "Take the roundabout onto",
    ("rotary",     ""):            "Take the rotary onto",
    ("arrive",     ""):            "Arrive at your destination",
    ("arrive",     "left"):        "Arrive at destination on the left",
    ("arrive",     "right"):       "Arrive at destination on the right",
    ("arrive",     "straight"):    "Arrive at destination",
}

_STEP_ICONS = {
    "depart":     {"": "▶", "left": "↖", "right": "↗", "straight": "↑"},
    "turn":       {"left": "←", "right": "→", "sharp left": "↙", "sharp right": "↘", "slight left": "↖", "slight right": "↗", "uturn": "↩"},
    "continue":   {"straight": "↑", "left": "←", "right": "→"},
    "fork":       {"left": "↖", "right": "↗"},
    "merge":      {"left": "←", "right": "→"},
    "roundabout": {"": "⟳"},
    "rotary":     {"": "⟳"},
    "arrive":     {"": "🏥", "left": "🏥", "right": "🏥", "straight": "🏥"},
}


def _parse_osrm_steps(osrm_steps: list) -> list[dict]:
    """Parse OSRM step list into structured turn-by-turn instructions.
    Captures maneuver GPS location for active-step highlighting on the map."""
    steps = []
    for s in osrm_steps:
        m = s.get("maneuver", {})
        mtype    = m.get("type", "")
        modifier = m.get("modifier", "")
        name     = (s.get("name") or "").strip()
        dist_km  = round(s.get("distance", 0) / 1000, 2)
        dur_min  = round(s.get("duration", 0) / 60, 1)

        text = (
            _MANEUVER_TEXT.get((mtype, modifier))
            or _MANEUVER_TEXT.get((mtype, ""))
            or "Continue on"
        )
        instruction = f"{text} {name}".strip() if name else text

        icon_map = _STEP_ICONS.get(mtype, {})
        icon     = icon_map.get(modifier) or icon_map.get("") or "↑"

        # Capture the GPS location of this maneuver (lon, lat in OSRM)
        loc = m.get("location")  # [lon, lat]
        step_location = {"lat": loc[1], "lon": loc[0]} if loc and len(loc) >= 2 else None

        steps.append({
            "instruction": instruction,
            "distance_km": dist_km,
            "duration_min": dur_min,
            "type":         mtype,
            "modifier":     modifier,
            "icon":         icon,
            "name":         name,
            "location":     step_location,   # ← GPS of this turn/maneuver
        })
    return steps


def _parse_osrm_route(r: dict) -> dict:
    """Convert one OSRM route object into our standard format."""
    legs = r.get("legs", [{}])
    steps = _parse_osrm_steps(legs[0].get("steps", []) if legs else [])
    return {
        "distance_km":      round(r["distance"] / 1000, 2),
        "duration_minutes": round(r["duration"] / 60),
        "geometry":         r["geometry"],
        "steps":            steps,
    }


def _osrm_route(from_lon, from_lat, to_lon, to_lat, alternatives=False, timeout=8):
    """
    Call OSRM and return parsed routes list, or None on failure.
    When alternatives=True, returns up to 3 route options.
    """
    try:
        resp = httpx.get(
            f"{OSRM_BASE}/{from_lon},{from_lat};{to_lon},{to_lat}",
            params={
                "overview":     "full",
                "geometries":   "geojson",
                "steps":        "true",
                "annotations":  "false",
                "alternatives": "true" if alternatives else "false",
            },
            timeout=timeout,
            headers=OSRM_HEADERS,
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == "Ok" and data.get("routes"):
                return [_parse_osrm_route(r) for r in data["routes"][:3]]
    except Exception:
        pass
    return None


def _osrm_summary(from_lon, from_lat, to_lon, to_lat, timeout=5):
    """Lightweight OSRM call for road distance + duration only (no geometry/steps)."""
    try:
        resp = httpx.get(
            f"{OSRM_BASE}/{from_lon},{from_lat};{to_lon},{to_lat}",
            params={"overview": "false", "steps": "false"},
            timeout=timeout,
            headers=OSRM_HEADERS,
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == "Ok" and data.get("routes"):
                r = data["routes"][0]
                return {
                    "road_km":  round(r["distance"] / 1000, 2),
                    "dur_min":  round(r["duration"] / 60),
                }
    except Exception:
        pass
    return None


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
    lat: float = Query(None),
    lon: float = Query(None),
    location: str = Query(None),
    emergency_type: str = Query("general"),
    insurance: str = Query(None),
    financial_level: str = Query(None),
    radius_km: float = Query(50, ge=1, le=300),
    limit: int = Query(10, ge=1, le=30),
):
    lat, lon, resolved_label = _resolve_coords(lat, lon, location)
    cfg = EMERGENCY_CAPABILITIES.get(emergency_type, EMERGENCY_CAPABILITIES["general"])

    rows = fetch_all(filters={"operational_status": "Operational"})
    facilities = [f for f in rows if f.get("latitude") is not None and f.get("longitude") is not None]

    results = []
    for f in facilities:
        dist = haversine(lat, lon, f["latitude"], f["longitude"])
        if dist > radius_km:
            continue

        enrich_facility(f)

        if insurance and insurance not in f["insurance_providers"]:
            continue
        if financial_level and financial_level.lower() not in ("any", ""):
            if f["financial_level"].lower() != financial_level.lower():
                continue

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

        road_km = round(dist * 1.35, 2)
        est_min = round((road_km / AVG_SPEED_KMH) * 60)

        results.append({
            **f,
            "distance_km":           round(dist, 2),
            "estimated_road_km":     road_km,
            "estimated_minutes":     est_min,
            "score":                 round(composite, 2),
            "emergency_match_score": round(emerg_score, 1),
            "match_reason":          _match_reason(f, emergency_type, cfg),
        })

    if not results:
        raise HTTPException(
            404,
            f"No facilities found within {radius_km}km matching your criteria. "
            "Try widening the radius or removing filters."
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
        reasons.append(f"Best match for {cfg['label']}")
    elif preferred and ftype in preferred:
        reasons.append(f"Suitable for {cfg['label']}")

    if facility.get("open_24_hours"):
        reasons.append("Open 24 hours")
    if facility.get("open_weekends"):
        reasons.append("Open weekends")

    beds = (facility.get("beds") or 0) + (facility.get("cots") or 0)
    if beds > 0:
        reasons.append(f"{beds} beds/cots")

    ins = facility.get("insurance_providers", [])
    if ins:
        reasons.append(f"Accepts: {', '.join(ins[:3])}")

    fl = facility.get("financial_level", "")
    if fl:
        reasons.append(f"{fl} cost")

    return " · ".join(reasons) if reasons else "General facility"


# ─── Road Routing (OSRM) with turn-by-turn + alternatives ────────────────────

@router.get("/road-route")
def road_route(
    from_lat: float = Query(...),
    from_lon: float = Query(...),
    to_lat: float = Query(...),
    to_lon: float = Query(...),
):
    """
    Real road route via OSRM with full turn-by-turn steps and GPS locations
    per step (for active-step highlighting). Returns up to 3 alternate routes.
    Falls back to straight-line estimate if OSRM is unavailable.
    """
    routes = _osrm_route(from_lon, from_lat, to_lon, to_lat, alternatives=True)

    if routes:
        main = routes[0]
        return {
            "source":   "osrm",
            "routes":   routes,         # all routes (main + alternates)
            # top-level fields mirror the main route for backward compatibility
            "distance_km":      main["distance_km"],
            "duration_minutes": main["duration_minutes"],
            "geometry":         main["geometry"],
            "steps":            main["steps"],
        }

    # Straight-line fallback
    dist    = haversine(from_lat, from_lon, to_lat, to_lon)
    road_km = round(dist * 1.35, 2)
    dur_min = round((road_km / AVG_SPEED_KMH) * 60)
    fallback_route = {
        "distance_km":      road_km,
        "duration_minutes": dur_min,
        "geometry": {
            "type": "LineString",
            "coordinates": [[from_lon, from_lat], [to_lon, to_lat]],
        },
        "steps": [
            {"instruction": f"Estimated road route ({road_km} km)", "distance_km": road_km, "duration_min": dur_min, "type": "depart", "icon": "↑", "name": "", "location": {"lat": from_lat, "lon": from_lon}},
            {"instruction": "Arrive at your destination", "distance_km": 0, "duration_min": 0, "type": "arrive", "icon": "🏥", "name": "", "location": {"lat": to_lat, "lon": to_lon}},
        ],
    }
    return {
        "source":           "estimate",
        "routes":           [fallback_route],
        "distance_km":      road_km,
        "duration_minutes": dur_min,
        "geometry":         fallback_route["geometry"],
        "steps":            fallback_route["steps"],
    }


@router.get("/nearest")
def nearest_facility(
    lat: float = Query(...),
    lon: float = Query(...),
    emergency_type: str = Query("general"),
    limit: int = Query(1, ge=1, le=5),
):
    """
    Find the nearest facility and return real road ETAs via OSRM.
    Uses OSRM summary calls (no geometry) for speed — falls back to ×1.35 estimate.
    """
    cfg       = EMERGENCY_CAPABILITIES.get(emergency_type, EMERGENCY_CAPABILITIES["general"])
    preferred = cfg.get("preferred_types")

    rows = fetch_all(filters={"operational_status": "Operational"})
    candidates = [
        f for f in rows
        if f.get("latitude") is not None and f.get("longitude") is not None
        and (not preferred or f.get("type") in preferred)
    ]
    if not candidates:
        candidates = [f for f in rows if f.get("latitude") is not None and f.get("longitude") is not None]
    if not candidates:
        raise HTTPException(404, "No facilities found.")

    # Pre-cut by straight-line distance to bound how many OSRM calls we make,
    # but pull a generous pool so the *actual* road-nearest facility (which can
    # differ from the haversine-nearest one due to road layout, rivers, etc.)
    # is still in the candidate set we rank by real road distance.
    haversine_pool = sorted(
        candidates,
        key=lambda f: haversine(lat, lon, f["latitude"], f["longitude"])
    )[:max(limit * 3, 8)]

    scored = []
    for f in haversine_pool:
        dist = haversine(lat, lon, f["latitude"], f["longitude"])
        enrich_facility(f)

        # Try OSRM for real road distance + time
        osrm = _osrm_summary(lon, lat, f["longitude"], f["latitude"])
        if osrm:
            road_km = osrm["road_km"]
            dur_min = osrm["dur_min"]
            eta_source = "osrm"
        else:
            road_km = round(dist * 1.35, 2)
            dur_min = round((road_km / AVG_SPEED_KMH) * 60)
            eta_source = "estimate"

        scored.append({
            **f,
            "distance_km":        round(dist, 2),
            "estimated_road_km":  road_km,
            "estimated_minutes":  dur_min,
            "eta_source":         eta_source,
        })

    # Rank by real road distance (falls back to the estimate when OSRM failed),
    # not the straight-line distance — the nearest by road isn't always the
    # nearest as-the-crow-flies.
    scored.sort(key=lambda f: f["estimated_road_km"])
    results = scored[:limit]

    return {"results": results, "total": len(results)}


# ─── Population Served ────────────────────────────────────────────────────────

@router.get("/population-served")
def population_served(
    lat: float = Query(None),
    lon: float = Query(None),
    location: str = Query(None),
    radius_km: float = Query(10, ge=1, le=100),
):
    lat, lon, resolved_label = _resolve_coords(lat, lon, location)

    rows = fetch_all(
        columns="name,type,county,district,operational_status,latitude,longitude,beds,cots,open_24_hours"
    )
    all_facilities = [r for r in rows if r.get("latitude") is not None and r.get("longitude") is not None]

    within = []
    for r in all_facilities:
        d = haversine(lat, lon, r["latitude"], r["longitude"])
        if d <= radius_km:
            within.append({**r, "distance_km": round(d, 2)})

    within.sort(key=lambda x: x["distance_km"])

    area_km2       = 3.14159 * radius_km ** 2
    est_population = round(area_km2 * 100)

    operational    = [f for f in within if f.get("operational_status") == "Operational"]
    total_capacity = sum((f.get("beds") or 0) + (f.get("cots") or 0) for f in operational)

    if operational:
        beds_per_1000       = round((total_capacity / est_population) * 1000, 2) if est_population else 0
        people_per_facility = round(est_population / len(operational))
    else:
        beds_per_1000       = 0
        people_per_facility = est_population

    who_benchmark = 10
    status = "Above WHO benchmark" if beds_per_1000 >= who_benchmark else "Below WHO benchmark"

    return {
        "centre":   resolved_label or {"latitude": lat, "longitude": lon},
        "radius_km": radius_km,
        "catchment": {
            "estimated_population":        est_population,
            "area_km2":                    round(area_km2, 1),
            "total_facilities":            len(within),
            "operational_facilities":      len(operational),
            "total_beds_cots":             total_capacity,
            "beds_per_1000_people":        beds_per_1000,
            "people_per_facility":         people_per_facility,
            "who_beds_benchmark_per_1000": who_benchmark,
            "benchmark_status":            status,
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
