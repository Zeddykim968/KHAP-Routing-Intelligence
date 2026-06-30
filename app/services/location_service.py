import re
import httpx
from app.services.db_service import query

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
HEADERS = {"User-Agent": "KHAP-Routing-Intelligence/1.0 (kenya-health-access.replit.app)"}

KE_BBOX   = "33.9,-4.7,41.9,5.0"
KE_LAT_MIN, KE_LAT_MAX = -4.7, 5.0
KE_LON_MIN, KE_LON_MAX = 33.9, 41.9

_STRIP_WORDS = re.compile(
    r"\b(town|city|area|ward|estate|centre|center|cbd|market|stage|road|street|avenue|drive)\b",
    re.IGNORECASE,
)


def _in_kenya(lat: float, lon: float) -> bool:
    return KE_LAT_MIN <= lat <= KE_LAT_MAX and KE_LON_MIN <= lon <= KE_LON_MAX


def _nominatim_query(q: str) -> dict | None:
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
    stop = {"town", "city", "area", "ward", "estate", "centre", "center",
            "cbd", "market", "stage", "road", "street", "avenue", "kenya"}
    search_words = {w.lower() for w in name.split() if w.lower() not in stop and len(w) > 2}
    label_lower = label.lower()
    return any(w in label_lower for w in search_words)


def _geocode_nominatim(name: str) -> dict | None:
    base = name.strip()
    stripped = _STRIP_WORDS.sub("", base).strip()
    first_word = stripped.split()[0] if stripped.split() else base.split()[0]

    queries = []
    if stripped and stripped.lower() != base.lower():
        queries.append(f"{stripped} Kenya")
    queries.append(f"{first_word} Kenya")
    if base.lower() not in (stripped.lower(), f"{first_word}".lower()):
        queries.append(f"{base} Kenya")

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
    term = name.strip()
    pattern = f"%{term}%"

    for column in ("nearest_town", "district", "county"):
        rows = query(
            f"""
            SELECT latitude, longitude, {column}
            FROM facilities
            WHERE {column} ILIKE %s
              AND operational_status = 'Operational'
              AND latitude IS NOT NULL
              AND longitude IS NOT NULL
            LIMIT 1
            """,
            (pattern,)
        )
        if rows:
            row = rows[0]
            lat, lon = row["latitude"], row["longitude"]
            if _in_kenya(lat, lon):
                return {
                    "latitude":  lat,
                    "longitude": lon,
                    "label":     row.get(column, term),
                }
    return None


def resolve_location(name: str) -> dict | None:
    result = _geocode_nominatim(name)
    if result:
        return result
    return _geocode_database(name)
