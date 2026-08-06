"""
Two separate connection pools:
  - routing_pool     -> wherever the big roads/OSM/pgRouting data
                         lives (local Postgres, or a self-hosted /
                         managed instance with real storage headroom)
  - facilities_pool  -> Supabase, holding just the small facilities
                         table (fits comfortably in the free tier)

There are no cross-database joins between them -- when a query needs
both (e.g. geocode a typed place, then search facilities near it),
the service layer calls each pool separately and combines results
in Python.
"""
import asyncpg
from app.config import settings

routing_pool: asyncpg.Pool | None = None
facilities_pool: asyncpg.Pool | None = None


async def connect_db():
    global routing_pool, facilities_pool
    routing_pool = await asyncpg.create_pool(
        settings.routing_database_url, min_size=1, max_size=10
    )
    facilities_pool = await asyncpg.create_pool(
        settings.facilities_database_url,
        min_size=1,
        max_size=10,
        # Required if FACILITIES_DATABASE_URL uses Supabase's pooled
        # connection (port 6543) -- that PgBouncer runs in transaction
        # mode, which doesn't support asyncpg's prepared-statement
        # caching. Harmless (a no-op) on the direct connection (5432).
        statement_cache_size=0,
    )


async def close_db():
    if routing_pool:
        await routing_pool.close()
    if facilities_pool:
        await facilities_pool.close()


def get_routing_pool() -> asyncpg.Pool:
    assert routing_pool is not None, "Routing DB pool not initialised"
    return routing_pool


def get_facilities_pool() -> asyncpg.Pool:
    assert facilities_pool is not None, "Facilities DB pool not initialised"
    return facilities_pool
