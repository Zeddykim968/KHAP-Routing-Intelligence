from app.services.supabase_service import supabase


def resolve_location(name: str):
    """
    Resolve a human location name (town, area, district, or county) to
    (latitude, longitude, matched_label).

    Search order:
      1. nearest_town  — most granular, covers estates/towns
      2. district      — sub-county level
      3. county        — broadest fallback

    Returns a dict with keys: latitude, longitude, label
    Returns None if nothing matches.
    """
    term = name.strip()
    pattern = f"%{term}%"

    searches = [
        ("nearest_town", "nearest_town"),
        ("district",     "district"),
        ("county",       "county"),
    ]

    for column, label_field in searches:
        r = (
            supabase.table("facilities")
            .select(f"latitude,longitude,{label_field}")
            .ilike(column, pattern)
            .eq("operational_status", "Operational")
            .not_.is_("latitude", "null")
            .not_.is_("longitude", "null")
            .limit(1)
            .execute()
        )
        if r.data:
            row = r.data[0]
            return {
                "latitude":  row["latitude"],
                "longitude": row["longitude"],
                "label":     row.get(label_field, term),
            }

    return None
