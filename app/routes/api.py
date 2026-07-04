"""
General API utilities — county centroids, facility suggest, geospatial setup.
"""
from fastapi import APIRouter, HTTPException
from app.services.supabase_service import get_client

router = APIRouter(prefix="/api", tags=["API"])

# All 47 Kenya county centroids (WGS84)
KENYA_COUNTIES = [
    {"county_name": "Baringo",         "latitude":  0.8555, "longitude": 36.0885},
    {"county_name": "Bomet",           "latitude": -0.7820, "longitude": 35.3419},
    {"county_name": "Bungoma",         "latitude":  0.5635, "longitude": 34.5606},
    {"county_name": "Busia",           "latitude":  0.3355, "longitude": 34.1211},
    {"county_name": "Elgeyo Marakwet", "latitude":  1.0507, "longitude": 35.4804},
    {"county_name": "Embu",            "latitude": -0.5399, "longitude": 37.4556},
    {"county_name": "Garissa",         "latitude": -0.4532, "longitude": 39.6461},
    {"county_name": "Homa Bay",        "latitude": -0.5273, "longitude": 34.4571},
    {"county_name": "Isiolo",          "latitude":  0.3540, "longitude": 38.4792},
    {"county_name": "Kajiado",         "latitude": -2.0984, "longitude": 36.7819},
    {"county_name": "Kakamega",        "latitude":  0.2827, "longitude": 34.7519},
    {"county_name": "Kericho",         "latitude": -0.3689, "longitude": 35.2863},
    {"county_name": "Kiambu",          "latitude": -1.0313, "longitude": 36.8073},
    {"county_name": "Kilifi",          "latitude": -3.5108, "longitude": 39.6480},
    {"county_name": "Kirinyaga",       "latitude": -0.5590, "longitude": 37.2697},
    {"county_name": "Kisii",           "latitude": -0.6812, "longitude": 34.7660},
    {"county_name": "Kisumu",          "latitude": -0.1022, "longitude": 34.7617},
    {"county_name": "Kitui",           "latitude": -1.3668, "longitude": 38.0106},
    {"county_name": "Kwale",           "latitude": -4.1703, "longitude": 39.4516},
    {"county_name": "Laikipia",        "latitude":  0.3606, "longitude": 36.7870},
    {"county_name": "Lamu",            "latitude": -2.2686, "longitude": 40.9020},
    {"county_name": "Machakos",        "latitude": -1.5177, "longitude": 37.2634},
    {"county_name": "Makueni",         "latitude": -2.2527, "longitude": 37.6248},
    {"county_name": "Mandera",         "latitude":  3.9366, "longitude": 41.5627},
    {"county_name": "Marsabit",        "latitude":  2.3284, "longitude": 37.9962},
    {"county_name": "Meru",            "latitude":  0.0477, "longitude": 37.6493},
    {"county_name": "Migori",          "latitude": -1.0634, "longitude": 34.4731},
    {"county_name": "Mombasa",         "latitude": -4.0435, "longitude": 39.6682},
    {"county_name": "Murang'a",        "latitude": -0.7830, "longitude": 37.0419},
    {"county_name": "Nairobi",         "latitude": -1.2921, "longitude": 36.8219},
    {"county_name": "Nakuru",          "latitude": -0.3031, "longitude": 36.0800},
    {"county_name": "Nandi",           "latitude":  0.1836, "longitude": 35.1236},
    {"county_name": "Narok",           "latitude": -1.0817, "longitude": 35.8719},
    {"county_name": "Nyamira",         "latitude": -0.5669, "longitude": 34.9349},
    {"county_name": "Nyandarua",       "latitude": -0.1818, "longitude": 36.5243},
    {"county_name": "Nyeri",           "latitude": -0.4166, "longitude": 36.9517},
    {"county_name": "Samburu",         "latitude":  1.4165, "longitude": 36.8716},
    {"county_name": "Siaya",           "latitude":  0.0617, "longitude": 34.2422},
    {"county_name": "Taita Taveta",    "latitude": -3.3160, "longitude": 38.3577},
    {"county_name": "Tana River",      "latitude": -1.5364, "longitude": 39.5474},
    {"county_name": "Tharaka Nithi",   "latitude": -0.2956, "longitude": 37.8968},
    {"county_name": "Trans Nzoia",     "latitude":  1.1176, "longitude": 34.9500},
    {"county_name": "Turkana",         "latitude":  3.1238, "longitude": 35.5955},
    {"county_name": "Uasin Gishu",     "latitude":  0.5519, "longitude": 35.2697},
    {"county_name": "Vihiga",          "latitude":  0.0748, "longitude": 34.7241},
    {"county_name": "Wajir",           "latitude":  1.7471, "longitude": 40.0573},
    {"county_name": "West Pokot",      "latitude":  1.6215, "longitude": 35.3937},
]


@router.get("/counties/centroids")
def get_county_centroids():
    """Return all 47 Kenya county centroids (for accessibility map layer)."""
    return {"counties": KENYA_COUNTIES, "total": len(KENYA_COUNTIES)}


@router.post("/admin/seed-counties")
def seed_counties():
    """
    Seed all 47 Kenya counties into the gis.counties table.
    Safe to run multiple times (upserts on county_name).
    """
    supabase = get_client()
    inserted = 0
    errors = []

    for county in KENYA_COUNTIES:
        try:
            supabase.schema("gis").table("counties").upsert(
                {"county_name": county["county_name"]},
                on_conflict="county_name",
            ).execute()
            inserted += 1
        except Exception as e:
            errors.append({"county": county["county_name"], "error": str(e)})

    return {
        "inserted": inserted,
        "total": len(KENYA_COUNTIES),
        "errors": errors[:5] if errors else [],
        "note": "Run supabase/setup_geospatial.sql in the Supabase SQL Editor to enable PostGIS spatial queries.",
    }


@router.get("/stats")
def platform_stats():
    """Quick platform health check with live facility count."""
    supabase = get_client()
    try:
        result = supabase.table("facilities").select("facility_id", count="exact").limit(1).execute()
        total = result.count or 0
        op_result = supabase.table("facilities").select("facility_id", count="exact").eq("operational_status", "Operational").limit(1).execute()
        operational = op_result.count or 0
    except Exception as e:
        raise HTTPException(500, f"Database query failed: {e}")

    return {
        "total_facilities": total,
        "operational_facilities": operational,
        "counties": 47,
        "data_source": "Supabase",
        "routing_engine": "OSRM (OpenStreetMap)",
    }
