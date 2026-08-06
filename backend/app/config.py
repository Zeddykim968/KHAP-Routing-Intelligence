"""
Two connection strings, matching the two-database split.
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    routing_database_url: str      # roads/topology/OSM data -- large
    facilities_database_url: str   # Supabase -- small, facilities only

    class Config:
        env_file = ".env"


settings = Settings()
