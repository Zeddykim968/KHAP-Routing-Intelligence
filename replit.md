# KHAP Routing Intelligence — Microservice

## What this project is

This is the **Routing Intelligence microservice** for the [Kenya Health Access Platform](https://kenya-health-access.vercel.app) (KHAP).

The **main platform** is a Django app that provides:
- A web portal for facility search
- An admin panel for managing facilities and health content
- USSD access via `*384#` (Africa's Talking)
- SMS access
- Health education articles

**This microservice** sits alongside it and powers the heavy lifting:
- Smart facility finding across 7,406 verified MoH facilities
- Location resolution by name (type "Kibera Nairobi", get GPS coordinates)
- Emergency routing with OSRM road directions
- Insurance and financial level filtering
- GIS analytics: coverage, catchment zones, county accessibility rankings
- A dedicated USSD sub-menu (`*384*43149#`) for facility finding
- An SMS command handler compatible with Africa's Talking webhooks
- A `/health` diagnostic endpoint for pre-demo checks

## Architecture

```
User dials *384# or visits web portal
          │
          ▼
  Django main platform
  (handles auth, content, admin)
          │
          ▼ calls this API for facility data
  FastAPI Routing Intelligence (this project)
  port 5000 — Supabase PostgreSQL
          │
          ▼
  7,406 facilities from Ministry of Health
```

## Workflows

| Workflow | Command | Port |
|---|---|---|
| `Start application` | `uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload` | 5000 |
| `Start dashboard` | `cd frontend && npm run dev` | 5173 |

## Environment secrets

| Secret | Where to get it |
|---|---|
| `SUPABASE_URL` | Supabase → Project Settings → API → Project URL |
| `SUPABASE_SERVICE_KEY` | Supabase → Project Settings → API → service_role |
| `SUPABASE_KEY` | Supabase → Project Settings → API → anon public |

> The `SUPABASE_URL` secret may contain a trailing `/rest/v1/` — the app strips this automatically.

## Database

- **Host:** Supabase (free tier — pauses after ~1 week idle, restore at supabase.com)
- **Table:** `public.facilities` — 7,406 rows from MoH CSV
- **Columns:** facility_id, name, county, district, type, owner, nearest_town, beds, cots, open_24_hours, open_weekends, operational_status, latitude, longitude
- **Pagination:** Supabase default limit is 1,000 rows; all bulk endpoints paginate automatically

## Key files

| File | Purpose |
|---|---|
| `app/main.py` | FastAPI app, CORS, router registration, health endpoint |
| `app/routes/recommendatons.py` | `/recommendations` — facility search, list, suggest |
| `app/routes/ussd.py` | `/ussd` — Africa's Talking USSD webhook handler |
| `app/routes/sms.py` | `/sms` — Africa's Talking SMS webhook handler |
| `app/routes/ambulance.py` | `/ambulance` — nearest emergency facility |
| `app/routes/analytics.py` | `/analytics` — county rankings, national summary |
| `app/routes/gis.py` | `/gis` — coverage, catchment, travel time |
| `app/routes/smart_routing.py` | `/smart` — insurance/emergency routing |
| `app/services/location_service.py` | Nominatim geocoding + DB fallback |
| `app/services/supabase_service.py` | Supabase client, pagination |
| `app/recommendation_engine.py` | Scoring algorithm (distance + type + beds) |
| `frontend/src/` | React map dashboard (port 5173) |

## How the Django main platform calls this service

```python
# In your Django view or service layer:
import requests

BASE = "https://your-routing-service.replit.app"

# Find nearest facilities to a location
resp = requests.get(f"{BASE}/recommendations", params={
    "location": "Kibera Nairobi",
    "limit": 5,
    "type": "Hospital",
})
facilities = resp.json()["results"]

# Ambulance emergency routing
resp = requests.get(f"{BASE}/ambulance", params={
    "location": "Westlands Nairobi",
})
nearest = resp.json()["nearest_facility"]

# County analytics
resp = requests.get(f"{BASE}/analytics/counties")
rankings = resp.json()["counties"]
```

## Africa's Talking integration

**USSD:** Register `https://your-service.replit.app/ussd` as your AT USSD callback URL.
The handler accepts `sessionId`, `serviceCode`, `phoneNumber`, `text` (form POST).
Returns `CON ...` to continue the session or `END ...` to close it.

**SMS:** Register `https://your-service.replit.app/sms/webhook` as your AT SMS callback URL.
Accepts AT's form-encoded POST (`from`, `text`, `date`, `id`, `linkId`, `to`).
Returns JSON with `to`, `message`, `sender` — forward this back via the AT SDK to reply.

## Checking platform health

```bash
curl https://your-service.replit.app/health
```

- `"healthy"` → all good, 7,000+ facilities live
- `"degraded"` → DB connected but low row count — check Supabase table
- `"unhealthy"` → cannot reach Supabase — go to supabase.com and restore the project

## User preferences

- Keep insurance and financial level derived at runtime from the `owner` field (not stored in DB)
- OSRM public demo server for road routing with straight-line fallback
- Dark theme is the default for the map dashboard
- Note the typo in the recommendations router filename: `recommendatons.py` (missing 'i') — do not rename, it is referenced everywhere
