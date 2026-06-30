from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.recommendatons import router as recommendations_router
from app.routes.ussd import router as ussd_router
from app.routes.sms import router as sms_router
from app.routes.ambulance import router as ambulance_router
from app.routes.analytics import router as analytics_router
from app.routes.gis import router as gis_router

app = FastAPI(
    title="KHAP Routing Intelligence",
    version="1.0",
    description="Routing Intelligence API for the Kenya Health Access Platform — Web, USSD, and SMS.",
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


@app.get("/", tags=["Meta"])
def root():
    return {
        "service": "KHAP Routing Intelligence",
        "version": "1.0",
        "status": "operational",
        "channels": ["web", "ussd", "sms"],
        "docs": "/docs",
    }


@app.get("/health", tags=["Meta"])
def health():
    return {"status": "ok"}
