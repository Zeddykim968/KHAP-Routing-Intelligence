from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api import facilities, routing, search, health

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Geospatial healthcare routing API for the Kenya Health Access Platform. "
        "Powered by PostgreSQL + PostGIS for facility data and OSRM for road routing. "
        "See /docs for the interactive Swagger UI."
    ),
)

# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(health.router)
app.include_router(facilities.router)
app.include_router(search.router)
app.include_router(routing.router)


@app.get("/", tags=["Meta"])
def root():
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs":    "/docs",
        "health":  "/health",
        "endpoints": {
            "facilities":        "GET  /facilities",
            "facility_detail":   "GET  /facilities/{id}",
            "nearest":           "GET  /facilities/nearest?lon=&lat=",
            "search":            "GET  /search?q=",
            "route":             "POST /route",
            "health":            "GET  /health",
        },
    }
