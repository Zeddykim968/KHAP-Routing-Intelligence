"""
Thin wrapper around routing.shortest_route_geojson().
All the actual pathfinding lives in Postgres/pgRouting -- this
function just calls it and hands back a plain dict.
"""
import json
from asyncpg import Pool


async def get_shortest_route(
    pool: Pool, start_lon: float, start_lat: float, end_lon: float, end_lat: float
) -> dict | None:
    row = await pool.fetchrow(
        "SELECT routing.shortest_route_geojson($1, $2, $3, $4) AS result",
        start_lon, start_lat, end_lon, end_lat,
    )
    result = json.loads(row["result"])

    if result.get("route") is None:
        # pgr_dijkstra found no path -- usually means the two points
        # fall in disconnected components of the road graph, or
        # snapped to the same vertex. Not an error, just "no route".
        return None
    return result
