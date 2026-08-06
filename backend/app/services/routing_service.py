"""
Routing service — orchestrates a full route request.

Flow
----
1.  Receive start (lon, lat) and end (lon, lat) from the API layer.
2.  (Optional) snap each point to the nearest road vertex in
    routing.edges_vertices_pgr via PostGIS for pgRouting consistency.
3.  Delegate the actual road-network calculation to OSRM via osrm_service.
4.  Return the route dict ready for the response schema.

The snapping step is kept as a helper and can be wired in later once
pgRouting-based isochrones or multi-stop routing are needed.
"""
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.services import osrm_service


def calculate_route(
    db: Session,
    start_lon: float,
    start_lat: float,
    end_lon: float,
    end_lat: float,
) -> dict:
    """
    Calculate a driving route from start to end using OSRM.

    Parameters
    ----------
    db : Session
        Active SQLAlchemy session (used for vertex snapping if needed).
    start_lon, start_lat : float
        Origin coordinates (WGS84).
    end_lon, end_lat : float
        Destination coordinates (WGS84).

    Returns
    -------
    dict matching RouteResponse schema.

    Raises
    ------
    ValueError  — no route exists (OSRM NoRoute).
    RuntimeError — OSRM is unreachable.
    """
    return osrm_service.get_route(start_lon, start_lat, end_lon, end_lat)


def snap_to_vertex(db: Session, lon: float, lat: float) -> dict:
    """
    Find the nearest pgRouting vertex in routing.edges_vertices_pgr.

    Returns a dict with keys: id, lon, lat, distance_m.
    Useful for pgRouting-based analysis (isochrones, multi-stop, etc.).
    """
    row = db.execute(
        text("""
            SELECT
                id,
                ST_X(the_geom) AS lon,
                ST_Y(the_geom) AS lat,
                ST_Distance(
                    the_geom::geography,
                    ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography
                ) AS distance_m
            FROM routing.edges_vertices_pgr
            ORDER BY the_geom <-> ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)
            LIMIT 1
        """),
        {"lon": lon, "lat": lat},
    ).fetchone()

    if not row:
        raise ValueError("No road vertices found in routing.edges_vertices_pgr")

    return dict(row._mapping)
