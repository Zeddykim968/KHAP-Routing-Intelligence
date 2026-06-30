from fastapi import APIRouter, Query, HTTPException
from collections import Counter, defaultdict
from app.services.supabase_service import supabase
from app.services.location_service import resolve_location
from app.recommendation_engine import haversine

router = APIRouter(prefix="/gis", tags=["GIS Intelligence"])

AVG_SPEED_KMH = 40


def _fetch_all(columns: str):
    """Fetch ALL rows via pagination, bypassing Supabase's 1,000-row server cap."""
    all_rows, page_size, offset = [], 1000, 0
    while True:
        batch = (
            supabase.table("facilities")
            .select(columns)
            .range(offset, offset + page_size - 1)
            .execute()
            .data
        )
        all_rows.extend(batch)
        if len(batch) < page_size:
            break
        offset += page_size
    return all_rows


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


# ─── Coverage Analysis ───────────────────────────────────────────────────────

@router.get("/coverage")
def coverage_analysis(
    lat: float = Query(None, description="Centre latitude"),
    lon: float = Query(None, description="Centre longitude"),
    location: str = Query(None, description="Town or area name e.g. 'Nakuru', 'Mombasa'"),
    radius_km: float = Query(10, ge=1, le=200, description="Radius in km"),
):
    lat, lon, resolved_label = _resolve_coords(lat, lon, location)

    rows = _fetch_all("latitude,longitude,type,owner,beds,cots,open_24_hours,operational_status,name,county")
    operational = [
        r for r in rows
        if r.get("operational_status") == "Operational"
        and r.get("latitude") and r.get("longitude")
    ]

    within = []
    for r in operational:
        d = haversine(lat, lon, r["latitude"], r["longitude"])
        if d <= radius_km:
            within.append({**r, "distance_km": round(d, 2)})

    within.sort(key=lambda x: x["distance_km"])

    type_counts = dict(Counter(r["type"] for r in within if r.get("type")).most_common())

    owner_buckets = defaultdict(int)
    for r in within:
        o = (r.get("owner") or "").lower()
        if "ministry" in o or "county" in o:
            owner_buckets["Government"] += 1
        elif "mission" in o or "church" in o or "catholic" in o or "protestant" in o or "episcopal" in o:
            owner_buckets["Faith-Based"] += 1
        elif "private" in o:
            owner_buckets["Private"] += 1
        else:
            owner_buckets["Other"] += 1

    total_beds = sum((r.get("beds") or 0) + (r.get("cots") or 0) for r in within)
    open_24h = sum(1 for r in within if r.get("open_24_hours"))
    nearest = within[0] if within else None

    return {
        "centre": resolved_label or {"latitude": lat, "longitude": lon},
        "radius_km": radius_km,
        "total_facilities": len(within),
        "total_beds_and_cots": total_beds,
        "open_24h_facilities": open_24h,
        "facility_type_breakdown": type_counts,
        "ownership_breakdown": dict(owner_buckets),
        "nearest_facility": {
            "name": nearest["name"],
            "type": nearest["type"],
            "county": nearest["county"],
            "distance_km": nearest["distance_km"],
        } if nearest else None,
        "facilities": [
            {"name": r["name"], "type": r["type"],
             "county": r["county"], "distance_km": r["distance_km"]}
            for r in within[:20]
        ],
    }


# ─── Travel-Time Estimate ────────────────────────────────────────────────────

@router.get("/travel-time")
def travel_time(
    from_lat: float = Query(None),
    from_lon: float = Query(None),
    from_location: str = Query(None, description="Origin town e.g. 'Thika'"),
    to_lat: float = Query(None),
    to_lon: float = Query(None),
    to_location: str = Query(None, description="Destination town e.g. 'Nairobi'"),
):
    """Straight-line distance converted to estimated road travel time."""
    from_lat, from_lon, from_label = _resolve_coords(from_lat, from_lon, from_location)
    to_lat, to_lon, to_label = _resolve_coords(to_lat, to_lon, to_location)

    straight_km = haversine(from_lat, from_lon, to_lat, to_lon)
    road_km = round(straight_km * 1.35, 2)
    minutes = round((road_km / AVG_SPEED_KMH) * 60)

    return {
        "from": from_label or {"latitude": from_lat, "longitude": from_lon},
        "to": to_label or {"latitude": to_lat, "longitude": to_lon},
        "straight_line_km": round(straight_km, 2),
        "estimated_road_km": road_km,
        "estimated_minutes": minutes,
        "note": "Estimate based on 1.35 tortuosity factor and 40 km/h average speed.",
    }


# ─── Accessibility Scoring ───────────────────────────────────────────────────

@router.get("/accessibility")
def accessibility_score(
    lat: float = Query(None),
    lon: float = Query(None),
    location: str = Query(None, description="Town or area name e.g. 'Garissa', 'Turkana'"),
):
    lat, lon, resolved_label = _resolve_coords(lat, lon, location)

    rows = _fetch_all("latitude,longitude,type,beds,cots,open_24_hours,operational_status")
    operational = [
        r for r in rows
        if r.get("operational_status") == "Operational"
        and r.get("latitude") and r.get("longitude")
    ]

    bands = {"5km": [], "15km": [], "50km": []}
    for r in operational:
        d = haversine(lat, lon, r["latitude"], r["longitude"])
        if d <= 5:
            bands["5km"].append(r)
        if d <= 15:
            bands["15km"].append(r)
        if d <= 50:
            bands["50km"].append(r)

    score_5  = min(len(bands["5km"]) / 5, 1) * 50
    score_15 = min(len(bands["15km"]) / 10, 1) * 30
    score_50 = min(len(bands["50km"]) / 30, 1) * 20
    total_score = round(score_5 + score_15 + score_50, 1)

    beds_5km = sum((r.get("beds") or 0) + (r.get("cots") or 0) for r in bands["5km"])
    open_24h_5km = sum(1 for r in bands["5km"] if r.get("open_24_hours"))

    if total_score >= 70:
        rating = "Excellent"
    elif total_score >= 45:
        rating = "Good"
    elif total_score >= 20:
        rating = "Moderate"
    else:
        rating = "Poor"

    return {
        "location": resolved_label or {"latitude": lat, "longitude": lon},
        "accessibility_score": total_score,
        "rating": rating,
        "catchment_summary": {
            "within_5km": {
                "facilities": len(bands["5km"]),
                "beds": beds_5km,
                "open_24h": open_24h_5km,
            },
            "within_15km": {"facilities": len(bands["15km"])},
            "within_50km": {"facilities": len(bands["50km"])},
        },
    }


# ─── Catchment Analysis ──────────────────────────────────────────────────────

@router.get("/catchment")
def catchment_analysis(
    lat: float = Query(None),
    lon: float = Query(None),
    location: str = Query(None, description="Town or area name e.g. 'Kisii', 'Embu'"),
    radius_km: float = Query(20, ge=1, le=100),
    facility_type: str = Query(None, description="Filter by type e.g. 'Dispensary'"),
):
    lat, lon, resolved_label = _resolve_coords(lat, lon, location)

    rows = _fetch_all("facility_id,name,type,county,district,beds,cots,open_24_hours,operational_status,latitude,longitude,owner")
    operational = [
        r for r in rows
        if r.get("operational_status") == "Operational"
        and r.get("latitude") and r.get("longitude")
    ]

    if facility_type:
        operational = [r for r in operational if (r.get("type") or "").lower() == facility_type.lower()]

    results = []
    for r in operational:
        d = haversine(lat, lon, r["latitude"], r["longitude"])
        if d <= radius_km:
            road_km = round(d * 1.35, 2)
            minutes = round((road_km / AVG_SPEED_KMH) * 60)
            results.append({
                **r,
                "distance_km": round(d, 2),
                "estimated_road_km": road_km,
                "estimated_minutes": minutes,
            })

    results.sort(key=lambda x: x["distance_km"])

    return {
        "centre": resolved_label or {"latitude": lat, "longitude": lon},
        "radius_km": radius_km,
        "filter_type": facility_type,
        "total_serving_facilities": len(results),
        "catchment": results[:50],
    }
