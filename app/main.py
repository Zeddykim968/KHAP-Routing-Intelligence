import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.recommendatons import router as recommendations_router
from app.routes.ussd import router as ussd_router
from app.routes.sms import router as sms_router
from app.routes.ambulance import router as ambulance_router
from app.routes.analytics import router as analytics_router
from app.routes.gis import router as gis_router
from app.routes.smart_routing import router as smart_router
from app.routes.api import router as api_router

_START_TIME = time.time()

app = FastAPI(
    title="KHAP Routing Intelligence",
    version="3.0",
    description=(
        "Routing Intelligence microservice for the Kenya Health Access Platform (KHAP). "
        "Powers facility finding, smart emergency routing, and GIS analytics for the main "
        "Django platform at kenya-health-access.vercel.app. "
        "Serves 7,406 verified MoH facilities across Kenya's 47 counties via REST API, "
        "Africa's Talking USSD (*384*43149#), and SMS webhooks. "
        "See /health for live platform status."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://kenya-health-access.vercel.app",
        "https://*.vercel.app",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:5173",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(recommendations_router)
app.include_router(ussd_router)
app.include_router(sms_router)
app.include_router(ambulance_router)
app.include_router(analytics_router)
app.include_router(gis_router)
app.include_router(smart_router)
app.include_router(api_router)


@app.get("/", tags=["Meta"])
def root():
    return {
        "service": "KHAP Routing Intelligence",
        "version": "3.0",
        "status": "operational",
        "channels": ["web", "ussd", "sms"],
        "docs": "/docs",
    }


@app.get("/health", tags=["Meta"])
def health():
    from app.services.supabase_service import supabase

    checks: dict = {}
    overall = "healthy"

    # ── Supabase: row count + response time ──────────────────────────────────
    try:
        t0 = time.time()
        r = supabase.table("facilities").select("facility_id", count="exact").limit(1).execute()
        db_ms = round((time.time() - t0) * 1000)
        total = r.count or 0
        checks["database"] = {
            "status":        "ok",
            "total_facilities": total,
            "response_ms":   db_ms,
            "note": "ok" if total >= 7000 else "⚠️ row count lower than expected",
        }
        if total < 7000:
            overall = "degraded"
    except Exception as exc:
        checks["database"] = {"status": "error", "detail": str(exc)}
        overall = "unhealthy"

    # ── Operational subset ────────────────────────────────────────────────────
    try:
        r2 = (
            supabase.table("facilities")
            .select("facility_id", count="exact")
            .eq("operational_status", "Operational")
            .limit(1)
            .execute()
        )
        checks["database"]["operational_facilities"] = r2.count or 0
    except Exception:
        pass

    # ── Uptime ────────────────────────────────────────────────────────────────
    elapsed = int(time.time() - _START_TIME)
    h, rem  = divmod(elapsed, 3600)
    m, s    = divmod(rem, 60)

    return {
        "status":  overall,
        "version": "3.0",
        "uptime":  f"{h}h {m}m {s}s",
        "uptime_seconds": elapsed,
        "checks":  checks,
        "channels": {
            "web":  "https://kenya-health-access.vercel.app",
            "ussd": "*384*43149#",
            "sms":  "/sms",
        },
    }
