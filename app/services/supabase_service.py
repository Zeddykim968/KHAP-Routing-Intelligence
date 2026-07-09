"""
Supabase client — sole database for KHAP.
Uses the service role key to bypass Row Level Security on the facilities table.
"""

import os
from supabase import create_client, Client

_SUPABASE_URL = os.getenv("SUPABASE_URL", "")
_SUPABASE_KEY = (
    os.getenv("SUPABASE_SERVICE_KEY")
    or os.getenv("SUPABASE_KEY", "")
)

if not _SUPABASE_URL or not _SUPABASE_KEY:
    raise RuntimeError(
        "SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in Replit Secrets. "
        "See ReadMe.md → Environment Variables."
    )

supabase: Client = create_client(_SUPABASE_URL, _SUPABASE_KEY)

PAGE_SIZE = 1000


def get_client() -> Client:
    """Return the raw Supabase client for custom queries."""
    return supabase


TABLE = "health_facilities"


def _coerce(row: dict) -> dict:
    """Normalise fields whose types differ across Supabase environments."""
    for field in ("open_24_hours", "open_weekends"):
        v = row.get(field)
        if isinstance(v, str):
            row[field] = v.lower() in ("t", "true", "1", "yes")
    return row


def fetch_page(
    columns: str = "*",
    filters: dict | None = None,
    limit: int = 2000,
    offset: int = 0,
    require_coords: bool = False,
) -> list[dict]:
    """
    Fetch up to `limit` rows, auto-paginating in 1,000-row chunks to work
    around Supabase PostgREST's per-request row cap.
    require_coords=True adds server-side NOT NULL filter on latitude/longitude.
    """
    all_rows: list[dict] = []
    chunk = min(PAGE_SIZE, limit)
    cur_offset = offset

    while len(all_rows) < limit:
        want = min(chunk, limit - len(all_rows))
        q = supabase.table(TABLE).select(columns).range(cur_offset, cur_offset + want - 1)
        if filters:
            for key, val in (filters or {}).items():
                if val is not None:
                    q = q.eq(key, val)
        if require_coords:
            q = q.not_.is_("latitude", "null").not_.is_("longitude", "null")
        result = q.execute()
        batch = result.data or []
        all_rows.extend([_coerce(r) for r in batch])
        if len(batch) < want:
            break
        cur_offset += want

    return all_rows[:limit]


def fetch_all(columns: str = "*", filters: dict | None = None) -> list[dict]:
    """
    Fetch ALL rows from the health_facilities table (paginated).
    Use only when you genuinely need every row (e.g. smart-recommend scoring).
    """
    all_rows: list[dict] = []
    offset = 0
    while True:
        q = supabase.table(TABLE).select(columns).range(offset, offset + PAGE_SIZE - 1)
        if filters:
            for key, val in filters.items():
                if val is not None:
                    q = q.eq(key, val)
        result = q.execute()
        batch: list[dict] = result.data or []
        all_rows.extend([_coerce(r) for r in batch])
        if len(batch) < PAGE_SIZE:
            break
        offset += PAGE_SIZE
    return all_rows


def fetch_one(facility_id: int) -> dict | None:
    """Fetch a single facility by integer ID."""
    result = (
        supabase.table(TABLE)
        .select("*")
        .eq("facility_id", facility_id)
        .limit(1)
        .execute()
    )
    data = result.data or []
    return data[0] if data else None


def search_ilike(column: str, term: str, operational_only: bool = True, limit: int = 50) -> list[dict]:
    """Case-insensitive substring search on a single column."""
    q = supabase.table(TABLE).select("*").ilike(column, f"%{term}%").limit(limit)
    if operational_only:
        q = q.eq("operational_status", "Operational")
    result = q.execute()
    return result.data or []
