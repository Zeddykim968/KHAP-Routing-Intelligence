---
name: KHAP Supabase table name
description: The correct facilities table name in Supabase for the KHAP routing microservice, to avoid PGRST205 schema errors.
---

The KHAP routing microservice's single Supabase table is `public.facilities` (7,406 rows).

**Why:** A legacy edit introduced `health_facilities` as the table name in `app/services/supabase_service.py` and `app/routes/api.py`, but that table doesn't exist — it caused `postgrest.exceptions.APIError: PGRST205 ... Perhaps you meant 'public.facilities'` on every call to `fetch_all`/`fetch_one`/`search_ilike`, silently breaking the `/ambulance` endpoint and any other route depending on those helpers.

**How to apply:** If you see PGRST205 "table not found" errors from Supabase, grep for `supabase.table(` calls and confirm they all reference `"facilities"`, not any other name. The `/health` endpoint's direct Supabase check is a reliable reference for the correct table name since it's less often touched.
