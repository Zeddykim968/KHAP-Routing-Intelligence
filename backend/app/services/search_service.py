"""
Nearest-facility search, spanning both databases:
  - geocode_place()            -> routing DB (OSM named places)
  - search_nearest_facilities  -> facilities DB (Supabase)
  - get_insurance_providers    -> facilities DB (Supabase)
Combined here in Python, since the two databases can't be joined
directly in SQL.
"""
from asyncpg import Pool


async def geocode_place(routing_pool: Pool, query: str, limit: int = 1) -> list[dict]:
    rows = await routing_pool.fetch(
        "SELECT * FROM routing.geocode_place($1, $2)", query, limit
    )
    return [dict(r) for r in rows]


async def search_nearest_facilities(
    routing_pool: Pool,
    facilities_pool: Pool,
    lon: float | None,
    lat: float | None,
    query: str | None,
    limit: int = 3,
    insurance: list[str] | None = None,
) -> dict:
    resolved_location = None

    if lon is None or lat is None:
        if not query:
            raise ValueError("Provide either lon & lat, or a text query")
        matches = await geocode_place(routing_pool, query, limit=1)
        if not matches:
            return {"resolved_location": None, "facilities": []}
        top = matches[0]
        lon, lat = top["lon"], top["lat"]
        resolved_location = {"matched_name": top["name"], "lon": lon, "lat": lat}

    rows = await facilities_pool.fetch(
        "SELECT * FROM nearest_facilities($1, $2, $3, $4)", lon, lat, limit, insurance
    )
    return {
        "resolved_location": resolved_location,
        "facilities": [dict(r) for r in rows],
    }


async def get_insurance_providers(facilities_pool: Pool) -> list[str]:
    rows = await facilities_pool.fetch("SELECT name FROM insurance_providers ORDER BY name")
    return [r["name"] for r in rows]
