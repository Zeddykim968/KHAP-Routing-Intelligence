"""
Advanced GIS / spatial analysis functions for KHAP V3.
All computations use pure Python + math.
Performance: network_analysis_summary uses sampling for large datasets.
"""

import math
import random
from typing import List, Dict, Tuple, Optional

KENYA_BOUNDS = {"lat_min": -4.7, "lat_max": 4.6, "lon_min": 34.0, "lon_max": 42.0}
EARTH_RADIUS_KM = 6371


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return EARTH_RADIUS_KM * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dlambda = math.radians(lon2 - lon1)
    x = math.sin(dlambda) * math.cos(phi2)
    y = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(dlambda)
    return (math.degrees(math.atan2(x, y)) + 360) % 360


def destination_point(lat: float, lon: float, bearing_deg: float, distance_km: float) -> Tuple[float, float]:
    d = distance_km / EARTH_RADIUS_KM
    b = math.radians(bearing_deg)
    phi1 = math.radians(lat)
    lam1 = math.radians(lon)
    phi2 = math.asin(math.sin(phi1) * math.cos(d) + math.cos(phi1) * math.sin(d) * math.cos(b))
    lam2 = lam1 + math.atan2(
        math.sin(b) * math.sin(d) * math.cos(phi1),
        math.cos(d) - math.sin(phi1) * math.sin(phi2)
    )
    return math.degrees(phi2), math.degrees(lam2)


def buffer_circle(lat: float, lon: float, radius_km: float, points: int = 64) -> List[List[float]]:
    coords = []
    for i in range(points + 1):
        angle = 360 * i / points
        p_lat, p_lon = destination_point(lat, lon, angle, radius_km)
        coords.append([p_lon, p_lat])
    return coords


def point_in_kenya(lat: float, lon: float) -> bool:
    b = KENYA_BOUNDS
    return b["lat_min"] <= lat <= b["lat_max"] and b["lon_min"] <= lon <= b["lon_max"]


def catchment_area(
    facility_lat: float, facility_lon: float,
    all_facilities: List[Dict],
    radius_km: float = 15.0,
) -> Dict:
    within = []
    for f in all_facilities:
        if not (f.get("latitude") and f.get("longitude")):
            continue
        dist = haversine(facility_lat, facility_lon, f["latitude"], f["longitude"])
        if dist <= radius_km:
            within.append({**f, "distance_km": round(dist, 2)})
    within.sort(key=lambda x: x["distance_km"])
    pop_estimate = len(within) * 500

    return {
        "catchment_radius_km": radius_km,
        "facilities_within": len(within),
        "population_estimate": pop_estimate,
        "buffer_polygon": {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [buffer_circle(facility_lat, facility_lon, radius_km)],
            },
        },
        "facilities": within,
    }


def nearest_facilities(
    lat: float, lon: float,
    facilities: List[Dict],
    limit: int = 10,
    radius_km: Optional[float] = None,
    facility_type: Optional[str] = None,
) -> List[Dict]:
    results = []
    for f in facilities:
        if not (f.get("latitude") and f.get("longitude")):
            continue
        if facility_type and f.get("type") != facility_type:
            continue
        dist = haversine(lat, lon, f["latitude"], f["longitude"])
        if radius_km and dist > radius_km:
            continue
        results.append({**f, "distance_km": round(dist, 2),
                        "bearing": round(bearing(lat, lon, f["latitude"], f["longitude"]), 1)})
    results.sort(key=lambda x: x["distance_km"])
    return results[:limit]


def network_analysis_summary(facilities: List[Dict], sample_size: int = 300) -> Dict:
    """
    Computes a network summary. For large datasets uses random sampling
    (sample_size facilities) to keep runtime under 1 second.
    """
    valid = [f for f in facilities if f.get("latitude") and f.get("longitude")]
    n = len(valid)
    if n < 2:
        return {"error": "Not enough facilities for network analysis"}

    # Sample for nearest-neighbour computation on large datasets
    sample = valid if n <= sample_size else random.sample(valid, sample_size)

    total_nn = 0.0
    isolated = 0
    for i, f1 in enumerate(sample):
        nn = min(
            haversine(f1["latitude"], f1["longitude"], f2["latitude"], f2["longitude"])
            for j, f2 in enumerate(sample) if i != j
        )
        total_nn += nn
        if nn > 20:
            isolated += 1

    by_county: Dict[str, int] = {}
    for f in valid:
        c = f.get("county", "Unknown")
        by_county[c] = by_county.get(c, 0) + 1

    sampled = n > sample_size
    return {
        "total_facilities": n,
        "avg_nearest_neighbour_km": round(total_nn / len(sample), 2),
        "isolated_facilities": round(isolated * (n / len(sample))),
        "isolated_pct": round(isolated / len(sample) * 100, 1),
        "counties_covered": len(by_county),
        "avg_facilities_per_county": round(n / len(by_county), 1) if by_county else 0,
        "county_distribution": sorted(by_county.items(), key=lambda x: x[1], reverse=True),
        "sampled": sampled,
        "sample_size": len(sample) if sampled else n,
    }


def emergency_response_zones(
    lat: float, lon: float, facilities: List[Dict],
    speed_kmh: float = 60.0,
) -> Dict:
    zones = {"critical": [], "urgent": [], "standard": [], "remote": []}
    for f in facilities:
        if not (f.get("latitude") and f.get("longitude")):
            continue
        dist = haversine(lat, lon, f["latitude"], f["longitude"])
        time_min = (dist / speed_kmh) * 60
        entry = {**f, "distance_km": round(dist, 2), "est_response_min": round(time_min, 1)}
        if time_min < 15:
            zones["critical"].append(entry)
        elif time_min < 30:
            zones["urgent"].append(entry)
        elif time_min < 60:
            zones["standard"].append(entry)
        else:
            zones["remote"].append(entry)
    for zone in zones.values():
        zone.sort(key=lambda x: x["est_response_min"])

    nearest = None
    for zone_name in ["critical", "urgent", "standard", "remote"]:
        if zones[zone_name]:
            nearest = zones[zone_name][0]
            break

    return {
        "query_location": {"latitude": lat, "longitude": lon},
        "speed_kmh": speed_kmh,
        "nearest_facility": nearest,
        "zones": {k: v[:5] for k, v in zones.items()},
        "summary": {k: len(v) for k, v in zones.items()},
    }
