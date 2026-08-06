---
name: KHAP new project structure
description: Restructured layout — backend/app/ for FastAPI, frontend/src/pages+components+services for React+Leaflet.
---

## Structure

- Backend: `backend/app/{api,database,schemas,services,core,main.py}`
- Frontend: `frontend/src/{components/{Map,SearchBar,FacilityCard,RouteSummary},pages/{Dashboard,Facilities,Routing},services/{api.js,routing.js}}`
- Support dirs: `database/`, `osrm/data/`, `osrm/profiles/`

## Workflows

- `Start application`: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload` (port 8000, console)
- `Start dashboard`: `cd frontend && npm run dev` (port 5173, webview)

**Why:** Old flat `app/` layout was replaced per user's architecture doc. Supabase removed; PostgreSQL+PostGIS+SQLAlchemy is the only database layer.

## Routing

- OSRM via HTTP: `backend/app/services/osrm_service.py` calls `POST /route/v1/driving/...`
- `OSRM_URL` env var — defaults to public demo `http://router.project-osrm.org`
- pgRouting vertex snapping available in `routing_service.py` via `routing.edges_vertices_pgr`

## Key env vars

- `DATABASE_URL` — PostgreSQL connection string (required for DB queries)
- `OSRM_URL` — OSRM engine URL (optional, has public demo fallback)
- `VITE_API_URL` — backend URL for frontend (optional, vite proxy handles it in dev)
