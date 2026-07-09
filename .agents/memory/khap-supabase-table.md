---
name: KHAP Supabase table name
description: The facilities table name in Supabase for the KHAP routing microservice — verify, don't assume.
---

The correct table name is **project-specific** and has flipped between `public.facilities` and `public.health_facilities` across different Supabase instances connected to this repl over time. Do not trust either name from memory.

**Why:** Past sessions assumed a fixed name and got PGRST205 "table not found" errors when the connected Supabase project actually used the other name. As of 2026-07-09, the live Supabase project uses `public.health_facilities`.

**How to apply:** If `/health`, `/recommendations/*`, or `/ambulance` return PGRST205 or "unhealthy" with a schema-cache error, don't just grep-and-guess. Run a live query against the current `SUPABASE_URL`/`SUPABASE_SERVICE_KEY` (e.g. `supabase.table("<name>").select("*").limit(1).execute()`, or read the PGRST205 error's "Perhaps you meant" hint) to find the real table name, then grep for all `supabase.table(...)` calls across `app/main.py`, `app/routes/*.py`, and `app/services/supabase_service.py` and make them consistent.
