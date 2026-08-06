from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import text


def get_facilities(db: Session, skip: int = 0, limit: int = 50) -> dict:
    """Return a paginated list of all facilities."""
    rows = db.execute(
        text("""
            SELECT
                id, name, facility_type, operator, phone, website,
                emergency, opening_hours, wheelchair,
                ST_Y(geom) AS lat,
                ST_X(geom) AS lon
            FROM gis.health_facilities
            WHERE geom IS NOT NULL
            ORDER BY id
            OFFSET :skip LIMIT :limit
        """),
        {"skip": skip, "limit": limit},
    ).fetchall()

    total = db.execute(
        text("SELECT COUNT(*) FROM gis.health_facilities WHERE geom IS NOT NULL")
    ).scalar()

    return {
        "total": total,
        "facilities": [dict(r._mapping) for r in rows],
    }


def get_facility_by_id(db: Session, facility_id: int) -> Optional[dict]:
    """Return a single facility by primary key."""
    row = db.execute(
        text("""
            SELECT
                id, name, facility_type, operator, phone, website,
                emergency, opening_hours, wheelchair,
                ST_Y(geom) AS lat,
                ST_X(geom) AS lon
            FROM gis.health_facilities
            WHERE id = :id
        """),
        {"id": facility_id},
    ).fetchone()
    return dict(row._mapping) if row else None


def get_nearest_facilities(
    db: Session,
    lon: float,
    lat: float,
    limit: int = 5,
    facility_type: Optional[str] = None,
) -> list[dict]:
    """
    Return the N nearest facilities to (lon, lat) using PostGIS geography
    distance.  The <-> KNN operator exploits the spatial index for speed.
    """
    type_filter = "AND facility_type ILIKE :ftype" if facility_type else ""

    rows = db.execute(
        text(f"""
            SELECT
                id, name, facility_type, operator, phone, website,
                emergency, opening_hours, wheelchair,
                ST_Y(geom) AS lat,
                ST_X(geom) AS lon,
                ST_Distance(
                    geom::geography,
                    ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography
                ) AS distance_m
            FROM gis.health_facilities
            WHERE geom IS NOT NULL
            {type_filter}
            ORDER BY geom <-> ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)
            LIMIT :limit
        """),
        {
            "lon": lon,
            "lat": lat,
            "limit": limit,
            **({"ftype": f"%{facility_type}%"} if facility_type else {}),
        },
    ).fetchall()

    return [dict(r._mapping) for r in rows]


def search_facilities(
    db: Session,
    q: Optional[str] = None,
    facility_type: Optional[str] = None,
    operator: Optional[str] = None,
    limit: int = 20,
) -> list[dict]:
    """
    Full-text search across name, facility_type, and operator.
    All parameters are optional and ANDed together.
    """
    clauses = ["geom IS NOT NULL"]
    params: dict = {"limit": limit}

    if q:
        clauses.append("(name ILIKE :q OR facility_type ILIKE :q OR operator ILIKE :q)")
        params["q"] = f"%{q}%"
    if facility_type:
        clauses.append("facility_type ILIKE :ftype")
        params["ftype"] = f"%{facility_type}%"
    if operator:
        clauses.append("operator ILIKE :operator")
        params["operator"] = f"%{operator}%"

    where = " AND ".join(clauses)

    rows = db.execute(
        text(f"""
            SELECT
                id, name, facility_type, operator, phone, website,
                emergency, opening_hours, wheelchair,
                ST_Y(geom) AS lat,
                ST_X(geom) AS lon
            FROM gis.health_facilities
            WHERE {where}
            ORDER BY name
            LIMIT :limit
        """),
        params,
    ).fetchall()

    return [dict(r._mapping) for r in rows]
