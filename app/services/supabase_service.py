"""
Supabase client — sole database for KHAP.
Uses the service role key to bypass Row Level Security on the facilities table.
"""

import os
from supabase import create_client, Client

_raw_url = os.getenv("SUPABASE_URL", "")
# The stored secret sometimes has a trailing /rest/v1/ path — strip it so the
# Supabase client can construct all URLs correctly.
_SUPABASE_URL = _raw_url.replace("/rest/v1", "").rstrip("/")

_SUPABASE_KEY = (
    os.getenv("SUPABASE_SERVICE_KEY")
    or os.getenv("SUPABASE_KEY", "")
)

if not _SUPABASE_URL or not _SUPABASE_KEY:
    raise RuntimeError(
        "SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in Replit Secrets.\n"
        "SUPABASE_URL  → Project Settings → API → Project URL\n"
        "SUPABASE_SERVICE_KEY → Project Settings → API → service_role secret"
    )

supabase: Client = create_client(_SUPABASE_URL, _SUPABASE_KEY)

PAGE_SIZE = 1000


def get_client() -> Client:
    """Return the raw Supabase client for custom queries."""
    return supabase


def fetch_all(columns: str = "*", filters: dict | None = None) -> list[dict]:
    """
    Fetch all rows from the facilities table with optional equality filters.
    Paginates automatically through Supabase's 1,000-row default limit.
    """
    all_rows: list[dict] = []
    offset = 0
    while True:
        q = supabase.table("facilities").select(columns).range(offset, offset + PAGE_SIZE - 1)
        if filters:
            for key, val in filters.items():
                if val is not None:
                    q = q.eq(key, val)
        result = q.execute()
        batch: list[dict] = result.data or []
        all_rows.extend(batch)
        if len(batch) < PAGE_SIZE:
            break
        offset += PAGE_SIZE
    return all_rows


def fetch_one(facility_id: int) -> dict | None:
    """Fetch a single facility by integer ID."""
    result = (
        supabase.table("facilities")
        .select("*")
        .eq("facility_id", facility_id)
        .limit(1)
        .execute()
    )
    data = result.data or []
    return data[0] if data else None


def search_ilike(column: str, term: str, operational_only: bool = True, limit: int = 50) -> list[dict]:
    """Case-insensitive substring search on a single column."""
    q = supabase.table("facilities").select("*").ilike(column, f"%{term}%").limit(limit)
    if operational_only:
        q = q.eq("operational_status", "Operational")
    result = q.execute()
    return result.data or []
