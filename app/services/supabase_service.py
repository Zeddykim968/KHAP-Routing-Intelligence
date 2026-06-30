"""
Supabase client — async version for use inside FastAPI async endpoints.
Also exports a sync client for legacy routes that still use it.
"""

from supabase import create_client, acreate_client, AsyncClient, Client
from app.config import SUPABASE_URL, SUPABASE_KEY, SUPABASE_SERVICE_KEY
import asyncio

_key = SUPABASE_SERVICE_KEY or SUPABASE_KEY

if not SUPABASE_URL or not _key:
    raise RuntimeError(
        "Supabase credentials missing. Set SUPABASE_URL and either "
        "SUPABASE_SERVICE_KEY or SUPABASE_KEY in Replit Secrets."
    )

# Sync client — kept for legacy V1/V2 routes
supabase: Client = create_client(SUPABASE_URL, _key)

# Async client — used by all V3 routes
_async_client: AsyncClient | None = None


async def get_async_client() -> AsyncClient:
    global _async_client
    if _async_client is None:
        _async_client = await acreate_client(SUPABASE_URL, _key)
    return _async_client


# Convenience alias — call as: db = await async_db()
async_db = get_async_client
