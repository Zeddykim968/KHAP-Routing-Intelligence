"""
V3 Admin API — ETL import, cache management, system health.
Uses local PostgreSQL via app/services/db.py.
"""

from fastapi import APIRouter, HTTPException, Depends, Request, Body
from typing import List, Dict
from app.auth.jwt import require_admin
from app.cache.store import cache
from app.etl.pipeline import run_pipeline
from app.etl.validators import validate_batch
from app.services.db import query, query_one
from app.cache.rate_limit import limiter

router = APIRouter(prefix="/api/v3/admin", tags=["V3 · Admin"])


@router.get("/health")
def system_health(request: Request):
    db_ok = False
    try:
        row = query_one("SELECT COUNT(*) AS n FROM facilities")
        db_ok = row is not None
    except Exception:
        pass
    return {
        "status": "operational" if db_ok else "degraded",
        "components": {"api": "ok", "database": "ok" if db_ok else "error", "cache": "ok"},
        "version": "3.0",
    }


@router.post("/etl/validate")
@limiter.limit("10/minute")
def validate_records(
    request: Request,
    records: List[Dict] = Body(...),
    admin: dict = Depends(require_admin),
):
    return validate_batch(records)


@router.post("/etl/import")
@limiter.limit("5/minute")
def import_records(
    request: Request,
    records: List[Dict] = Body(...),
    source: str = Body("api"),
    dry_run: bool = Body(False),
    admin: dict = Depends(require_admin),
):
    return run_pipeline(records, source=source, dry_run=dry_run)


@router.get("/etl/logs")
def import_logs(request: Request, limit: int = 20, admin: dict = Depends(require_admin)):
    try:
        rows = query(
            "SELECT * FROM import_logs ORDER BY imported_at DESC LIMIT %s", [limit]
        )
        return {"logs": rows}
    except Exception as e:
        raise HTTPException(500, f"Could not fetch logs: {e}")


@router.delete("/cache")
def clear_cache(request: Request, admin: dict = Depends(require_admin)):
    cache.clear()
    return {"message": "Cache cleared"}


@router.get("/stats")
def system_stats(request: Request, admin: dict = Depends(require_admin)):
    try:
        row = query_one(
            """SELECT
                COUNT(*) AS total_facilities,
                COUNT(*) FILTER (WHERE operational_status='Operational') AS operational_facilities
            FROM facilities"""
        )
        return row
    except Exception as e:
        raise HTTPException(500, str(e))
