from fastapi import APIRouter
from app.database.session import check_db
from app.core.config import settings
from app.services import osrm_service

router = APIRouter(tags=["Health"])


@router.get("/health")
def health():
    """
    Application health check.

    Verifies database connectivity and OSRM reachability.
    Returns overall status: healthy | degraded | unhealthy.
    """
    checks: dict = {}
    overall = "healthy"

    # ── PostgreSQL / PostGIS ──────────────────────────────────────────────────
    db_result = check_db()
    checks["database"] = db_result
    if db_result["status"] != "ok":
        overall = "unhealthy"
    elif db_result.get("facility_count", 0) == 0:
        overall = "degraded"
        checks["database"]["note"] = "PostGIS connected but no facilities found"

    # ── OSRM ─────────────────────────────────────────────────────────────────
    try:
        # Lightweight check: OSRM nearest-snap endpoint on Nairobi CBD
        import httpx
        resp = httpx.get(
            f"{settings.OSRM_URL}/nearest/v1/driving/36.8219,-1.2921",
            timeout=5.0,
        )
        if resp.status_code == 200:
            checks["osrm"] = {"status": "ok", "url": settings.OSRM_URL}
        else:
            checks["osrm"] = {"status": "degraded", "http_status": resp.status_code}
            if overall == "healthy":
                overall = "degraded"
    except Exception as exc:
        checks["osrm"] = {"status": "error", "detail": str(exc)}
        if overall == "healthy":
            overall = "degraded"

    return {
        "status":  overall,
        "version": settings.APP_VERSION,
        "checks":  checks,
    }
