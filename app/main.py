from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.recommendatons import router as recommendations_router
from app.routes.ussd import router as ussd_router
from app.routes.sms import router as sms_router

app = FastAPI(
    title="KHAP Routing Intelligence",
    version="1.0",
    description="Routing Intelligence API for the Kenya Health Access Platform — Web, USSD, and SMS.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://kenya-health-access.vercel.app",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(recommendations_router)
app.include_router(ussd_router)
app.include_router(sms_router)


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
