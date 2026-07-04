# KHAP — Kenya Health Access Platform

## Project overview

Full-stack geospatial health platform mapping 7,390 verified Kenyan healthcare facilities.

- **Backend:** FastAPI (Python 3.12) on port 5000, Replit PostgreSQL via psycopg2
- **Frontend:** React 18 + Vite + Leaflet on port 5173
- **Channels:** Web map UI, USSD (`*384*43149#`), SMS

Key features: smart emergency routing, OSRM road directions, insurance/financial filtering, population vs WHO benchmark monitoring, county analytics, coverage analysis.

## Workflows

| Workflow | Command | Port |
|---|---|---|
| `Start application` | `uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload` | 5000 |
| `Start dashboard` | `cd frontend && npm run dev` | 5173 |

## Environment variables

| Variable | Source |
|---|---|
| `DATABASE_URL` | Replit-provisioned PostgreSQL (automatic) |

## Database

- Table: `public.facilities` — 7,390 rows seeded from MoH CSV
- Columns: facility_id, name, county, district, type, owner, nearest_town, beds, cots, open_24_hours, open_weekends, operational_status, latitude, longitude, geom
- Seed script: `database/setup_local_db.py`

## Key files

- `app/main.py` — FastAPI app, CORS, router registration
- `app/routes/smart_routing.py` — `/smart/*` emergency intelligence endpoints
- `app/services/enrichment.py` — insurance/financial level/emergency capability derivation
- `app/services/db_service.py` — psycopg2 PostgreSQL client
- `frontend/src/App.jsx` — root component, state, layer management
- `frontend/src/components/Sidebar.jsx` — all sidebar panels
- `frontend/src/components/MapView.jsx` — Leaflet map, markers, route polylines
- `frontend/src/api/index.js` — all API fetch helpers
- `frontend/vite.config.js` — Vite proxy config (routes /smart, /gis, /api, etc. → :5000)

## User preferences

- Keep insurance and financial level derived at runtime from the `owner` field (not stored in DB)
- OSRM public demo server for road routing with straight-line fallback
- Dark theme is the default
