"""
ETL data validation for health facility records.
Each validator returns (is_valid, list_of_issues).
"""

from typing import Dict, List, Tuple

KENYA_BOUNDS = {"lat_min": -4.7, "lat_max": 4.6, "lon_min": 34.0, "lon_max": 42.0}

REQUIRED_FIELDS = ["name", "county", "type", "latitude", "longitude"]

VALID_FACILITY_TYPES = {
    "District Hospital", "Provincial General Hospital", "Sub-District Hospital",
    "Other Hospital", "Medical Centre", "Health Centre", "Nursing Home",
    "Maternity Home", "Medical Clinic", "Dispensary", "Dental Clinic",
    "Eye Centre", "Radiology Unit", "Laboratory (Stand-alone)",
    "VCT Centre (Stand-Alone)", "Health Programme",
}


def validate_facility(record: Dict) -> Tuple[bool, List[str]]:
    issues = []

    for field in REQUIRED_FIELDS:
        if not record.get(field):
            issues.append(f"Missing required field: {field}")

    lat = record.get("latitude")
    lon = record.get("longitude")
    if lat is not None and lon is not None:
        b = KENYA_BOUNDS
        if not (b["lat_min"] <= float(lat) <= b["lat_max"]):
            issues.append(f"Latitude {lat} out of Kenya bounds ({b['lat_min']}–{b['lat_max']})")
        if not (b["lon_min"] <= float(lon) <= b["lon_max"]):
            issues.append(f"Longitude {lon} out of Kenya bounds ({b['lon_min']}–{b['lon_max']})")

    ftype = record.get("type", "")
    if ftype and ftype not in VALID_FACILITY_TYPES:
        issues.append(f"Unknown facility type: '{ftype}'")

    name = record.get("name", "")
    if name and len(name) < 3:
        issues.append(f"Facility name too short: '{name}'")

    return len(issues) == 0, issues


def validate_batch(records: List[Dict]) -> Dict:
    valid, invalid = [], []
    for r in records:
        ok, issues = validate_facility(r)
        if ok:
            valid.append(r)
        else:
            invalid.append({"record": r, "issues": issues})
    return {
        "total": len(records),
        "valid": len(valid),
        "invalid": len(invalid),
        "valid_records": valid,
        "invalid_records": invalid,
    }
