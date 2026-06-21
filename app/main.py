import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.routes.recommendatons import router as recommendations_router
from app.routes.ussd import router as ussd_router
from app.routes.sms import router as sms_router
from app.routes.routing import router as routing_router
from app.routes.analytics import router as analytics_router

app = FastAPI(
    title="KHAP Routing Intelligence v2.0",
    version="2.0",
    description=(
        "Kenya Health Access Platform — Geospatial Intelligence API. "
        "Powers Web, USSD, SMS channels with OSM routing, accessibility analytics, and gap analysis."
    ),
)

_allowed_origins = [
    "https://kenya-health-access.vercel.app",
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:5000",
]
_replit_domain = os.environ.get("REPLIT_DEV_DOMAIN")
if _replit_domain:
    _allowed_origins.append(f"https://{_replit_domain}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(recommendations_router)
app.include_router(ussd_router)
app.include_router(sms_router)
app.include_router(routing_router)
app.include_router(analytics_router)

FRONTEND_BUILD = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.isdir(FRONTEND_BUILD):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_BUILD, "assets")), name="assets")

    @app.get("/dashboard", include_in_schema=False)
    @app.get("/dashboard/{path:path}", include_in_schema=False)
    def serve_dashboard(path: str = ""):
        return FileResponse(os.path.join(FRONTEND_BUILD, "index.html"))


@app.get("/")
def home():
    return {
        "service": "KHAP Routing Intelligence",
        "version": "2.0",
        "status": "operational",
        "channels": ["web", "ussd", "sms"],
        "new_in_v2": [
            "OSM-based road routing via /api/routing",
            "Accessibility scoring via /api/analytics/accessibility",
            "Coverage analysis via /api/analytics/coverage",
            "Facility load analysis via /api/analytics/facility-load",
            "Gap analysis & new facility impact via /api/analytics/gap-analysis",
            "React/Leaflet dashboard at /dashboard",
        ],
        "docs": "/docs",
    }
