import math


def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


LEVEL_SCORES = {
    "District Hospital": 100,
    "Provincial General Hospital": 95,
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


def calculate_score(facility, user_lat, user_lon):
    distance_km = haversine(user_lat, user_lon, facility["latitude"], facility["longitude"])

    # Distance score: 40% weight — max 100 at 0km, 0 at 100km+
    distance_score = max(0, 100 - distance_km)

    # Service/capacity score: 30% weight — based on beds + cots
    beds = (facility.get("beds") or 0) + (facility.get("cots") or 0)
    service_score = min(100, beds * 2) if beds > 0 else 20

    # Hospital level score: 10% weight
    level_score = LEVEL_SCORES.get(facility.get("type", ""), 20)

    # Availability bonus: 20% weight
    availability_score = 0
    if facility.get("open_24_hours"):
        availability_score += 60
    if facility.get("open_weekends"):
        availability_score += 40

    score = (
        0.40 * distance_score +
        0.30 * service_score +
        0.10 * level_score +
        0.20 * availability_score
    )

    return score, round(distance_km, 2)
