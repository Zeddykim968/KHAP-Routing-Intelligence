"""
Facility load analysis — estimates demand pressure on each facility
based on how many other facilities share the local population catchment.

Load Score = inverse of facility density in the surrounding area.
High load = few facilities serving a large area = overloaded.
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


CATCHMENT_RADIUS_KM = 15


def compute_facility_loads(facilities: List[Dict]) -> List[Dict]:
    """
    For each facility, counts how many other facilities fall within the
    catchment radius and computes a load pressure score.

    Load pressure:
      - 0–2 neighbours  → Critical (score 0–30)
      - 3–5 neighbours  → High     (score 30–55)
      - 6–10 neighbours → Moderate (score 55–75)
      - 11+  neighbours → Low      (score 75–100)
    """
    valid = [f for f in facilities if f.get("latitude") and f.get("longitude")]
    results = []

    for f in valid:
        neighbours = [
            other for other in valid
            if other.get("facility_id") != f.get("facility_id")
            and _haversine(
                f["latitude"], f["longitude"],
                other["latitude"], other["longitude"]
            ) <= CATCHMENT_RADIUS_KM
        ]
        n = len(neighbours)

        if n <= 2:
            pressure = "Critical"
            load_score = round(10 + n * 10, 1)
        elif n <= 5:
            pressure = "High"
            load_score = round(30 + (n - 3) * 8.3, 1)
        elif n <= 10:
            pressure = "Moderate"
            load_score = round(55 + (n - 6) * 4, 1)
        else:
            pressure = "Low"
            load_score = min(100, round(75 + (n - 11) * 1.5, 1))

        results.append({
            "facility_id": f.get("facility_id"),
            "name": f.get("name"),
            "county": f.get("county"),
            "type": f.get("type"),
            "latitude": f["latitude"],
            "longitude": f["longitude"],
            "neighbours_within_15km": n,
            "load_pressure": pressure,
            "load_score": load_score,
        })

    results.sort(key=lambda x: x["load_score"])
    return results


def county_load_summary(facilities: List[Dict]) -> List[Dict]:
    """
    Returns average load pressure per county.
    """
    loads = compute_facility_loads(facilities)
    by_county: Dict[str, List] = {}
    for item in loads:
        county = item.get("county", "Unknown")
        by_county.setdefault(county, []).append(item["load_score"])

    summary = []
    for county, scores in by_county.items():
        avg = sum(scores) / len(scores)
        critical_count = sum(1 for s in scores if s < 30)
        summary.append({
            "county": county,
            "facility_count": len(scores),
            "avg_load_score": round(avg, 1),
            "critical_facilities": critical_count,
        })

    summary.sort(key=lambda x: x["avg_load_score"])
    return summary
