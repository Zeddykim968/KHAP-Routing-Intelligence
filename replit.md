# KHAP — Kenya Health Access Platform

A geospatial healthcare routing platform built with PostgreSQL, PostGIS, FastAPI, React, and OSRM.

## Project Structure

```
KHAP/
├── backend/app/
│   ├── api/          facilities.py  routing.py  search.py  health.py
│   ├── database/     session.py  models.py
│   ├── schemas/      facility.py  route.py
│   ├── services/     facility_service.py  osrm_service.py  routing_service.py
│   ├── core/         config.py  security.py
│   └── main.py
├── frontend/src/
│   ├── components/   Map/  SearchBar/  FacilityCard/  RouteSummary/
│   ├── pages/        Dashboard/  Facilities/  Routing/
│   ├── services/     api.js  routing.js
│   └── App.jsx
├── database/         README.md (schema setup)
├── osrm/             README.md  data/  profiles/
├── .env.example
├── requirements.txt
└── README.md
```

## Workflows

| Workflow          | Command                                                    | Port |
|-------------------|------------------------------------------------------------|------|
| Start application | `cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload` | 8000 |
| Start dashboard   | `cd frontend && npm run dev`                               | 5173 |

## Environment Variables

| Variable       | Description                          |
|----------------|--------------------------------------|
| `DATABASE_URL` | PostgreSQL connection string         |
| `OSRM_URL`     | OSRM routing engine URL              |

Set these in `.env` (backend) and `frontend/.env.local` (frontend).  
See `.env.example` for the full template.

## Database Schemas

- `gis.health_facilities` — facilities from OpenStreetMap (id, name, facility_type, operator, phone, website, emergency, opening_hours, wheelchair, geom, vertex_id)
- `routing.edges` — road network for pgRouting
- `routing.edges_vertices_pgr` — graph vertices

## User Preferences

- PostgreSQL + PostGIS is the sole database (no Supabase)
- OSRM for road routing; pgRouting vertices available via `vertex_id` for future isochrone/multi-stop work
- Public OSRM demo server as default fallback (`http://router.project-osrm.org`)
- Leaflet (react-leaflet) for mapping
- CSS Modules for component styling
- Note the typo in the old recommendations router (`recommendatons.py`) — that file is now gone; the new structure uses `backend/app/api/facilities.py`
