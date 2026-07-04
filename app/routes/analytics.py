from fastapi import APIRouter, HTTPException, Path
from collections import Counter, defaultdict
from app.services.supabase_service import fetch_all

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/summary")
def get_summary():
    rows = fetch_all(columns="type,owner,beds,cots,open_24_hours,open_weekends,operational_status,county")

    total = len(rows)
    operational = sum(1 for r in rows if r.get("operational_status") == "Operational")
    total_beds = sum((r.get("beds") or 0) + (r.get("cots") or 0) for r in rows)
    open_24h = sum(1 for r in rows if r.get("open_24_hours"))
    open_weekends = sum(1 for r in rows if r.get("open_weekends"))
    counties = len(set(r["county"] for r in rows if r.get("county")))

    type_counts = Counter(r["type"] for r in rows if r.get("type"))
    owner_counts = Counter(r["owner"] for r in rows if r.get("owner"))

    owner_buckets: defaultdict = defaultdict(int)
    for owner, count in owner_counts.items():
        o = (owner or "").lower()
        if "ministry" in o or "government" in o or "county" in o:
            owner_buckets["Government"] += count
        elif "mission" in o or "church" in o or "catholic" in o or "protestant" in o or "episcopal" in o:
            owner_buckets["Faith-Based"] += count
        elif "private" in o or "enterprise" in o:
            owner_buckets["Private"] += count
        elif "ngo" in o or "non-governmental" in o:
            owner_buckets["NGO"] += count
        else:
            owner_buckets["Other"] += count

    return {
        "total_facilities": total,
        "operational": operational,
        "non_operational": total - operational,
        "operational_rate_pct": round(operational / total * 100, 1) if total else 0,
        "total_beds_and_cots": total_beds,
        "open_24h_facilities": open_24h,
        "open_weekends_facilities": open_weekends,
        "counties_covered": counties,
        "facility_type_breakdown": dict(type_counts.most_common()),
        "ownership_breakdown": dict(owner_buckets),
    }


@router.get("/counties")
def get_county_rankings():
    rows = fetch_all(columns="county,type,beds,cots,open_24_hours,operational_status")
    operational = [r for r in rows if r.get("operational_status") == "Operational"]

    county_data: defaultdict = defaultdict(lambda: {
        "facilities": 0, "beds": 0, "hospitals": 0,
        "health_centres": 0, "dispensaries": 0, "open_24h": 0,
    })

    HOSPITAL_TYPES = {
        "District Hospital", "Provincial General Hospital",
        "Sub-District Hospital", "Other Hospital", "Medical Centre",
    }
    HEALTH_CENTRE_TYPES = {"Health Centre", "Maternity Home"}
    DISPENSARY_TYPES = {"Dispensary", "Clinic"}

    for r in operational:
        county = r.get("county")
        if not county:
            continue
        d = county_data[county]
        d["facilities"] += 1
        d["beds"] += (r.get("beds") or 0) + (r.get("cots") or 0)
        if r.get("type") in HOSPITAL_TYPES:
            d["hospitals"] += 1
        if r.get("type") in HEALTH_CENTRE_TYPES:
            d["health_centres"] += 1
        if r.get("type") in DISPENSARY_TYPES:
            d["dispensaries"] += 1
        if r.get("open_24_hours"):
            d["open_24h"] += 1

    max_f = max((v["facilities"] for v in county_data.values()), default=1)
    max_b = max((v["beds"] for v in county_data.values()), default=1)
    max_h = max((v["hospitals"] for v in county_data.values()), default=1)

    results = []
    for county, d in county_data.items():
        score = round(
            (d["facilities"] / max_f) * 40
            + (d["beds"] / max_b) * 40
            + (d["hospitals"] / max_h) * 20,
            1,
        )
        results.append({"county": county, **d, "accessibility_score": score})

    results.sort(key=lambda x: x["accessibility_score"], reverse=True)
    for i, r in enumerate(results, 1):
        r["rank"] = i

    return {"total_counties": len(results), "counties": results}


@router.get("/county/{county_name}")
def get_county_detail(county_name: str = Path(..., description="County name e.g. Nairobi")):
    rows = fetch_all(
        columns="county,type,owner,beds,cots,open_24_hours,open_weekends,operational_status,district,name",
        filters={"county": county_name},
    )

    if not rows:
        # Try case-insensitive fallback
        all_rows = fetch_all(columns="county,type,owner,beds,cots,open_24_hours,open_weekends,operational_status,district,name")
        rows = [r for r in all_rows if (r.get("county") or "").lower() == county_name.lower()]

    if not rows:
        raise HTTPException(status_code=404, detail=f"County '{county_name}' not found.")

    operational = [r for r in rows if r.get("operational_status") == "Operational"]
    total_beds = sum((r.get("beds") or 0) + (r.get("cots") or 0) for r in operational)
    open_24h = [r for r in operational if r.get("open_24_hours")]
    open_wknd = [r for r in operational if r.get("open_weekends")]

    type_breakdown = dict(Counter(r["type"] for r in operational if r.get("type")).most_common())
    district_breakdown = dict(Counter(r["district"] for r in operational if r.get("district")).most_common())
    owner_breakdown = dict(Counter(r["owner"] for r in operational if r.get("owner")).most_common(10))

    highest_bed = max(operational, key=lambda r: (r.get("beds") or 0), default=None)

    return {
        "county": rows[0]["county"],
        "total_facilities": len(rows),
        "operational": len(operational),
        "total_beds_and_cots": total_beds,
        "open_24h_count": len(open_24h),
        "open_weekends_count": len(open_wknd),
        "facility_type_breakdown": type_breakdown,
        "district_breakdown": district_breakdown,
        "top_owners": owner_breakdown,
        "largest_facility": {
            "name": highest_bed["name"],
            "type": highest_bed["type"],
            "beds": (highest_bed.get("beds") or 0) + (highest_bed.get("cots") or 0),
        } if highest_bed else None,
        "open_24h_facilities": [
            {"name": r["name"], "type": r["type"], "district": r.get("district")}
            for r in open_24h[:10]
        ],
    }
