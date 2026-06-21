"""
Coverage analysis — estimates how many facilities serve an area
within given radius thresholds (5 km, 10 km, 20 km, 50 km).
"""

import math
from typing import List, Dict


def _haversine(lat1, lon1, lat2, lon2) -> float:
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


RADIUS_BANDS_KM = [5, 10, 20, 50]


def coverage_from_point(
    lat: float,
    lon: float,
    facilities: List[Dict],
) -> Dict:
    """
    Returns facilities grouped by distance band from (lat, lon).
    Also returns the distance to the single nearest facility.
    """
    scored = []
    for f in facilities:
        if not (f.get("latitude") and f.get("longitude")):
            continue
        dist = _haversine(lat, lon, f["latitude"], f["longitude"])
        scored.append({**f, "distance_km": round(dist, 2)})

    scored.sort(key=lambda x: x["distance_km"])

    bands = {}
    for radius in RADIUS_BANDS_KM:
        within = [f for f in scored if f["distance_km"] <= radius]
        bands[f"within_{radius}km"] = {
            "count": len(within),
            "facilities": within[:10],
        }

    nearest = scored[0] if scored else None

    return {
        "query_location": {"latitude": lat, "longitude": lon},
        "nearest_facility": nearest,
        "coverage_bands": bands,
        "total_facilities_analysed": len(scored),
    }


def underserved_check(lat: float, lon: float, facilities: List[Dict]) -> Dict:
    """
    Checks whether a location is underserved.
    Underserved = no facility within 10 km, or only 1 within 20 km.
    """
    result = coverage_from_point(lat, lon, facilities)
    within_10 = result["coverage_bands"]["within_10km"]["count"]
    within_20 = result["coverage_bands"]["within_20km"]["count"]

    if within_10 == 0:
        status = "severely_underserved"
        message = "No health facility within 10 km."
    elif within_10 <= 1 and within_20 <= 2:
        status = "underserved"
        message = "Very few facilities nearby. Access is limited."
    elif within_20 <= 5:
        status = "moderate_access"
        message = "Limited facilities within 20 km."
    else:
        status = "adequate_access"
        message = "Adequate facility coverage in this area."

    return {
        **result,
        "access_status": status,
        "access_message": message,
    }
