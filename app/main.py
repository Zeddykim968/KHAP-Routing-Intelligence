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

app = FastAPI(
    title="KHAP — Kenya Health Access Platform",
    version="3.0",
    description=(
        "Routing Intelligence API for the Kenya Health Access Platform. "
        "Maps 7,390 verified Kenyan healthcare facilities across 47 counties. "
        "Provides emergency-type routing, insurance/financial filtering, OSRM road directions, "
        "population monitoring, GIS coverage analysis, USSD, and SMS channels."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
    return {"status": "ok"}
