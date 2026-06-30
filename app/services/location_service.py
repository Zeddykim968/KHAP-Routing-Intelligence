import re
import httpx
from app.services.supabase_service import supabase

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
HEADERS = {"User-Agent": "KHAP-Routing-Intelligence/1.0 (kenya-health-access.vercel.app)"}

# Kenya strict bounding box  (lon_min, lat_min, lon_max, lat_max for Nominatim viewbox)
KE_BBOX   = "33.9,-4.7,41.9,5.0"
KE_LAT_MIN, KE_LAT_MAX = -4.7, 5.0
KE_LON_MIN, KE_LON_MAX = 33.9, 41.9

# Words that confuse Nominatim when appended to a place name
_STRIP_WORDS = re.compile(
    r"\b(town|city|area|ward|estate|centre|center|cbd|market|stage|road|street|avenue|drive)\b",
    re.IGNORECASE,
)


def _in_kenya(lat: float, lon: float) -> bool:
    return KE_LAT_MIN <= lat <= KE_LAT_MAX and KE_LON_MIN <= lon <= KE_LON_MAX


def _nominatim_query(q: str) -> dict | None:
    """Single Nominatim call, returns result only if it falls inside Kenya."""
    try:
        r = httpx.get(
            NOMINATIM_URL,
            params={
                "q":           q,
                "format":      "json",
                "limit":       1,
                "countrycodes":"ke",
                "viewbox":     KE_BBOX,
                "bounded":     1,
                "addressdetails": 0,
            },
            headers=HEADERS,
            timeout=6,
        )
        if r.status_code == 200 and r.json():
            hit = r.json()[0]
            lat, lon = float(hit["lat"]), float(hit["lon"])
            if _in_kenya(lat, lon):
                label = hit.get("display_name", q).split(",")[0].strip()
                return {"latitude": lat, "longitude": lon, "label": label}
    except Exception:
        pass
    return None


def _label_matches(label: str, name: str) -> bool:
    """
    Returns True if the Nominatim label contains at least one meaningful word
    from the user's search term (prevents accepting unrelated business names).
    """
    stop = {"town", "city", "area", "ward", "estate", "centre", "center",
            "cbd", "market", "stage", "road", "street", "avenue", "kenya"}
    search_words = {w.lower() for w in name.split() if w.lower() not in stop and len(w) > 2}
    label_lower = label.lower()
    return any(w in label_lower for w in search_words)


def _geocode_nominatim(name: str) -> dict | None:
    """
    Try Nominatim with progressively simpler queries — simplest first:
      1. Stripped name (modifier words removed) + "Kenya"
      2. First meaningful word only + "Kenya"
      3. Original name + "Kenya" (last resort)
    All bounded to Kenya. Validates coordinates are inside Kenya AND label
    contains at least one word from the original search before accepting.
    """
    base = name.strip()
    stripped = _STRIP_WORDS.sub("", base).strip()
    first_word = stripped.split()[0] if stripped.split() else base.split()[0]

    # Build query list — simplest / most specific to least specific
    queries = []
    if stripped and stripped.lower() != base.lower():
        queries.append(f"{stripped} Kenya")      # e.g. "Eldoret Kenya"
    queries.append(f"{first_word} Kenya")         # e.g. "Eldoret Kenya"
    if base.lower() not in (stripped.lower(), f"{first_word}".lower()):
        queries.append(f"{base} Kenya")           # e.g. "Eldoret Town Kenya"

    seen = []
    for q in queries:
        if q in seen:
            continue
        seen.append(q)
        result = _nominatim_query(q)
        if result and _label_matches(result["label"], base):
            return result
    return None


def _geocode_database(name: str) -> dict | None:
    """
    Fallback: search our facilities table for a matching nearest_town, district,
    or county and return that facility's coordinates.
    """
    term = name.strip()
    pattern = f"%{term}%"

    for column in ("nearest_town", "district", "county"):
        r = (
            supabase.table("facilities")
            .select(f"latitude,longitude,{column}")
            .ilike(column, pattern)
            .eq("operational_status", "Operational")
            .not_.is_("latitude", "null")
            .not_.is_("longitude", "null")
            .limit(1)
            .execute()
        )
        if r.data:
            row = r.data[0]
            lat, lon = row["latitude"], row["longitude"]
            if _in_kenya(lat, lon):
                return {
                    "latitude":  lat,
                    "longitude": lon,
                    "label":     row.get(column, term),
                }
    return None


def resolve_location(name: str) -> dict | None:
    """
    Resolve a human location name to {latitude, longitude, label}.

    Strategy:
      1. Nominatim (OpenStreetMap) — real GPS precision, bounded to Kenya.
         Tries original → stripped of modifier words → first word only.
      2. Database fallback — searches nearest_town → district → county
         in the facilities table if Nominatim returns nothing within Kenya.

    Returns None if both sources fail.
    """
    result = _geocode_nominatim(name)
    if result:
        return result
    return _geocode_database(name)
