"""
Accessibility scoring per county.

Score = 40% Travel Time component + 30% Facility Density + 20% Coverage + 10% Facility Level

All computed from the facilities table — no external population data required.
Output categories:
  0–20   Critical
  20–40  Poor
  40–60  Moderate
  60–80  Good
  80–100 Excellent
"""

import math
from typing import List, Dict


LEVEL_WEIGHTS = {
    "District Hospital": 100,
    "Provincial General Hospital": 100,
    "Sub-District Hospital": 80,
    "Other Hospital": 75,
    "Medical Centre": 70,
    "Health Centre": 60,
    "Nursing Home": 50,
    "Maternity Home": 45,
    "Medical Clinic": 40,
    "Dispensary": 30,
    "Dental Clinic": 25,
    "Eye Centre": 25,
    "Radiology Unit": 25,
    "Laboratory (Stand-alone)": 20,
    "VCT Centre (Stand-Alone)": 20,
    "Health Programme": 15,
}

SCORE_BANDS = [
    (80, "Excellent"),
    (60, "Good"),
    (40, "Moderate"),
    (20, "Poor"),
    (0, "Critical"),
]


def _haversine(lat1, lon1, lat2, lon2) -> float:
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _band(score: float) -> str:
    for threshold, label in SCORE_BANDS:
        if score >= threshold:
            return label
    return "Critical"


def score_county(facilities: List[Dict]) -> Dict:
    """
    Computes an accessibility score for a county given its list of facilities.
    """
    if not facilities:
        return {"score": 0, "band": "Critical", "facility_count": 0, "details": {}}

    valid = [f for f in facilities if f.get("latitude") and f.get("longitude")]
    n = len(valid)

    if n == 0:
        return {"score": 0, "band": "Critical", "facility_count": 0, "details": {}}

    # --- Travel Time Component (40%) ---
    # Proxy: average nearest-neighbour distance between facilities.
    # Smaller average distance = better coverage = higher score.
    if n >= 2:
        total_nn_dist = 0.0
        for i, f1 in enumerate(valid):
            dists = [
                _haversine(f1["latitude"], f1["longitude"], f2["latitude"], f2["longitude"])
                for j, f2 in enumerate(valid) if i != j
            ]
            total_nn_dist += min(dists)
        avg_nn_km = total_nn_dist / n
    else:
        avg_nn_km = 50.0

    travel_score = max(0, min(100, 100 - avg_nn_km * 1.5))

    # --- Facility Density Component (30%) ---
    # Scaled against Kenya benchmark: ~1 facility per 10,000 people.
    # We use count directly, normalised to a reasonable ceiling of 200.
    density_score = min(100, (n / 200) * 100)

    # --- Coverage Component (20%) ---
    # Proportion of facilities offering 24h or weekend service.
    covered = sum(1 for f in valid if f.get("open_24_hours") or f.get("open_weekends"))
    coverage_score = (covered / n) * 100 if n > 0 else 0

    # --- Facility Level Component (10%) ---
    level_scores = [LEVEL_WEIGHTS.get(f.get("type", ""), 20) for f in valid]
    level_score = sum(level_scores) / len(level_scores) if level_scores else 20

    composite = (
        0.40 * travel_score +
        0.30 * density_score +
        0.20 * coverage_score +
        0.10 * level_score
    )
    composite = round(composite, 1)

    return {
        "score": composite,
        "band": _band(composite),
        "facility_count": n,
        "details": {
            "travel_time_score": round(travel_score, 1),
            "density_score": round(density_score, 1),
            "coverage_score": round(coverage_score, 1),
            "level_score": round(level_score, 1),
            "avg_nearest_neighbour_km": round(avg_nn_km, 2),
            "facilities_24h_or_weekend": covered,
        },
    }


def score_all_counties(all_facilities: List[Dict]) -> List[Dict]:
    """
    Groups facilities by county and computes accessibility scores for each.
    Returns a list sorted by score ascending (worst first).
    """
    by_county: Dict[str, List] = {}
    for f in all_facilities:
        county = f.get("county", "Unknown")
        by_county.setdefault(county, []).append(f)

    results = []
    for county, facilities in by_county.items():
        result = score_county(facilities)
        results.append({"county": county, **result})

    results.sort(key=lambda x: x["score"])
    return results
