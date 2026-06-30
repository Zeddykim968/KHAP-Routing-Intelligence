"""
V3 Facilities API — CRUD + search + filtering via local PostgreSQL.
"""

from fastapi import APIRouter, Query, HTTPException, Request
from app.services.db import query, query_one
from app.cache.store import cache
from app.cache.rate_limit import limiter, PUBLIC_LIMIT

router = APIRouter(prefix="/api/v3/facilities", tags=["V3 · Facilities"])


def _build_where(county=None, facility_type=None, operational_only=True):
    clauses, params = [], []
    if operational_only:
        clauses.append("operational_status = %s"); params.append("Operational")
    if county:
        clauses.append("county = %s"); params.append(county)
    if facility_type:
        clauses.append("type = %s"); params.append(facility_type)
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    return where, params


@router.get("")
@limiter.limit(PUBLIC_LIMIT)
def list_facilities(
    request: Request,
    county: str = Query(None),
    facility_type: str = Query(None, alias="type"),
    operational_only: bool = Query(True),
    limit: int = Query(500, ge=1, le=2000),
    offset: int = Query(0, ge=0),
):
    where, params = _build_where(county, facility_type, operational_only)
    total_rows = query(f"SELECT COUNT(*) AS n FROM facilities {where}", params)
    total = total_rows[0]["n"] if total_rows else 0
    rows = query(
        f"SELECT * FROM facilities {where} ORDER BY facility_id LIMIT %s OFFSET %s",
        params + [limit, offset],
    )
    return {"total": total, "offset": offset, "limit": limit, "results": rows}


@router.get("/counties")
@limiter.limit(PUBLIC_LIMIT)
def get_counties(request: Request):
    hit = cache.get("counties")
    if hit:
        return {"counties": hit}
    rows = query("SELECT DISTINCT county FROM facilities WHERE county IS NOT NULL ORDER BY county")
    counties = [r["county"] for r in rows]
    cache.set("counties", counties, ttl=3600)
    return {"counties": counties}


@router.get("/types")
@limiter.limit(PUBLIC_LIMIT)
def get_types(request: Request):
    hit = cache.get("facility_types")
    if hit:
        return {"types": hit}
    rows = query("SELECT DISTINCT type FROM facilities WHERE type IS NOT NULL ORDER BY type")
    types = [r["type"] for r in rows]
    cache.set("facility_types", types, ttl=3600)
    return {"types": types}


@router.get("/stats")
@limiter.limit(PUBLIC_LIMIT)
def facility_stats(request: Request, county: str = Query(None)):
    key = f"stats:{county}"
    hit = cache.get(key)
    if hit:
        return hit
    where = "WHERE county = %s" if county else ""
    params = [county] if county else []

    totals = query_one(
        f"""SELECT
            COUNT(*) AS total,
            COUNT(*) FILTER (WHERE operational_status='Operational') AS operational,
            COUNT(*) FILTER (WHERE open_24_hours=TRUE) AS open_24h,
            COALESCE(SUM(beds + cots),0) AS total_beds_cots
        FROM facilities {where}""",
        params,
    )
    by_type = query(
        f"SELECT type, COUNT(*) AS n FROM facilities {where} GROUP BY type ORDER BY n DESC",
        params,
    )
    by_county = query(
        f"SELECT county, COUNT(*) AS n FROM facilities {where} GROUP BY county ORDER BY n DESC",
        params,
    ) if not county else []

    result = {
        **(totals or {}),
        "by_type": {r["type"]: r["n"] for r in by_type},
        "by_county": {r["county"]: r["n"] for r in by_county},
    }
    cache.set(key, result, ttl=600)
    return result


@router.get("/{facility_id}")
@limiter.limit(PUBLIC_LIMIT)
def get_facility(request: Request, facility_id: int):
    key = f"facility:{facility_id}"
    hit = cache.get(key)
    if hit:
        return hit
    row = query_one("SELECT * FROM facilities WHERE facility_id = %s", [facility_id])
    if not row:
        raise HTTPException(status_code=404, detail="Facility not found")
    cache.set(key, row, ttl=600)
    return row
