from fastapi import FastAPI
from app.routes.recommendatons import router

app = FastAPI(
    title = "KHAP Routing Intelligence",
    version = "1.0"
)

app.include_router(router)

@app.get("/")
def home():
    return {
        "message": "KHAP Routing Intelligence working"
    }