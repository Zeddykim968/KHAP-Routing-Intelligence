from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # PostgreSQL + PostGIS
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/khap"

    # OSRM routing engine
    # Local (WSL):  http://localhost:5000
    # Public demo:  http://router.project-osrm.org
    OSRM_URL: str = "http://router.project-osrm.org"

    APP_NAME: str = "KHAP Routing Intelligence"
    APP_VERSION: str = "1.0.0"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
