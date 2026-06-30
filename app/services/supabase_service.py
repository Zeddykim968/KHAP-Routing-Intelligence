from supabase import create_client, Client
from app.config import SUPABASE_URL, SUPABASE_SERVICE_KEY, SUPABASE_KEY

_key = SUPABASE_SERVICE_KEY or SUPABASE_KEY

if not SUPABASE_URL or not _key:
    raise RuntimeError(
        "Missing Supabase credentials. Set SUPABASE_URL and SUPABASE_SERVICE_KEY in Secrets."
    )

supabase: Client = create_client(SUPABASE_URL, _key)
