"""
KHAP Routing Intelligence — V3
Production-ready geospatial microservice for the Kenya Health Access Platform.
"""

import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.cache.rate_limit import limiter
from app.cache.store import cache

# Legacy V1/V2 routes (kept for backward compatibility)
from app.routes.recommendatons import router as legacy_recommendations
from app.routes.ussd import router as ussd_router
from app.routes.sms import router as sms_router
from app.routes.routing import router as legacy_routing
from app.routes.analytics import router as legacy_analytics

# V3 API modules
from app.api.v3.facilities import router as v3_facilities
from app.api.v3.routing import router as v3_routing
from app.api.v3.analytics import router as v3_analytics
from app.api.v3.gis import router as v3_gis
from app.api.v3.auth import router as v3_auth
from app.api.v3.admin import router as v3_admin
from app.api.v3.reports import router as v3_reports

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("KHAP V3 starting up — cache initialised")
    yield
    logger.info("KHAP V3 shutting down")


app = FastAPI(
    title="KHAP Routing Intelligence",
    version="3.0",
    description=(
        "Kenya Health Access Platform — Geospatial Intelligence Microservice V3. "
        "Provides routing, spatial analytics, healthcare accessibility intelligence, "
        "and location-based APIs for the Kenya Health Access Platform."
    ),
    contact={"name": "KHAP Team"},
    license_info={"name": "MIT"},
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── Rate limiting ──────────────────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── CORS ───────────────────────────────────────────────────────────────────────
_origins = [
    "https://kenya-health-access.vercel.app",
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:5000",
]
_replit_domain = os.environ.get("REPLIT_DEV_DOMAIN")
if _replit_domain:
    _origins.append(f"https://{_replit_domain}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── V3 API routes ──────────────────────────────────────────────────────────────
app.include_router(v3_auth)
app.include_router(v3_facilities)
app.include_router(v3_routing)
app.include_router(v3_analytics)
app.include_router(v3_gis)
app.include_router(v3_reports)
app.include_router(v3_admin)

# ── Legacy routes (V1/V2 — backward compatible) ────────────────────────────────
app.include_router(legacy_recommendations)
app.include_router(ussd_router)
app.include_router(sms_router)
app.include_router(legacy_routing)
app.include_router(legacy_analytics)

# ── Static frontend ────────────────────────────────────────────────────────────
FRONTEND_BUILD = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.isdir(FRONTEND_BUILD):
    app.mount(
        "/assets",
        StaticFiles(directory=os.path.join(FRONTEND_BUILD, "assets")),
        name="assets",
    )

    @app.get("/dashboard", include_in_schema=False)
    @app.get("/dashboard/{path:path}", include_in_schema=False)
    def serve_dashboard(path: str = ""):
        return FileResponse(os.path.join(FRONTEND_BUILD, "index.html"))


# ── Root ───────────────────────────────────────────────────────────────────────
@app.get("/", tags=["Meta"])
def root():
    return {
        "service": "KHAP Routing Intelligence",
        "version": "3.0",
        "status": "operational",
        "description": "Geospatial microservice for the Kenya Health Access Platform",
        "api_versions": {
            "v3": {
                "base": "/api/v3",
                "modules": [
                    "auth", "facilities", "routing",
                    "analytics", "gis", "reports", "admin",
                ],
            },
            "legacy": {
                "base": "/",
                "note": "V1/V2 endpoints kept for backward compatibility",
            },
        },
        "khap_integration_endpoints": {
            "nearest_facility": "/api/v3/routing/nearest-facility",
            "route": "/api/v3/routing/route",
            "travel_time": "/api/v3/routing/travel-time",
            "coverage": "/api/v3/analytics/coverage",
            "county_analysis": "/api/v3/gis/county-analysis",
            "services": "/api/v3/facilities/types",
            "facility": "/api/v3/facilities/{id}",
            "national_report": "/api/v3/reports/national-summary",
            "county_report": "/api/v3/reports/county-report",
        },
        "channels": ["web", "ussd", "sms", "api"],
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health", tags=["Meta"])
def health():
    return {"status": "ok", "version": "3.0"}
