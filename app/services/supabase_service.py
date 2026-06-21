# connects to supabase database

from supabase import create_client
from app.config import SUPABASE_URL, SUPABASE_KEY, SUPABASE_SERVICE_KEY

_key = SUPABASE_SERVICE_KEY or SUPABASE_KEY

if not SUPABASE_URL or not _key:
    raise RuntimeError(
        "Supabase credentials missing. Set SUPABASE_URL and either "
        "SUPABASE_SERVICE_KEY or SUPABASE_KEY in Replit Secrets."
    )

supabase = create_client(SUPABASE_URL, _key)