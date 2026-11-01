# KHAP — Kenya Health Access Platform

A healthcare-finder and live-routing platform built with Django, Django REST Framework, Next.js, MapLibre GL, and OSRM.

## Project Structure

```
KHAP/
├── backend/
│   ├── manage.py
│   ├── khap/               # Django project (settings, urls, wsgi, asgi)
│   └── facilities/         # models, serializers, views, urls, OSRM client, seed command
├── frontend/               # Next.js web UI (App Router, MapLibre GL map)
├── database/               # Legacy PostGIS schema notes
├── osrm/                   # Local OSRM setup notes (Docker)
├── .env.example
├── requirements.txt
└── README.md
```

## Workflows

| Workflow         | Command                                                             | Port |
|------------------|---------------------------------------------------------------------|------|
| Start backend    | `.venv/bin/python backend/manage.py runserver 0.0.0.0:8000`         | 8000 |
| Start frontend   | `cd frontend && npm run dev`                                        | 3000 |
| Migrate database | `.venv/bin/python backend/manage.py migrate`                        | —    |
| Seed facilities  | `.venv/bin/python backend/manage.py seed_facilities`                | —    |

## Environment Variables

| Variable               | Description                          | Default                          |
|------------------------|--------------------------------------|----------------------------------|
| `DATABASE_URL`         | PostgreSQL connection string         | unset → SQLite `db.sqlite3`      |
| `DJANGO_SECRET_KEY`    | Django secret key                    | insecure dev default             |
| `DJANGO_DEBUG`         | Debug mode                           | `true`                           |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated hosts                | `*`                              |
| `CORS_ALLOWED_ORIGINS` | Comma-separated CORS origins         | `*`                              |
| `OSRM_URL`             | OSRM routing engine URL              | `http://router.project-osrm.org` |
| `NEXT_PUBLIC_API_URL`  | Frontend API host override           | `/api` rewrite (same origin)     |

Set backend vars in `.env` (repo root or `backend/`); frontend vars in `frontend/.env.local`.
See `.env.example` for the full template.

## API

- `GET  /api/health/` — health + DB/OSRM status
- `GET  /api/meta/` — facility types, services, insurers, counties
- `GET  /api/facilities/` — list with filters (type, county, service, insurance, emergency, open_now, search)
- `GET  /api/facilities/nearest/?lat=&lon=&limit=` — nearest facilities by haversine distance
- `GET  /api/search/?q=` — typeahead search
- `POST /api/route/` — OSRM route + turn-by-turn steps between two lat/lon points

## User Preferences

- Django + Django REST Framework backend; Next.js frontend (replaces FastAPI + Vite/React)
- SQLite by default; PostgreSQL via `DATABASE_URL` (no PostGIS required — haversine distances)
- OSRM for road routing; public demo server as default fallback (`http://router.project-osrm.org`)
- MapLibre GL with free CARTO styles (positron light / dark-matter dark) for the map
- CSS Modules for component styling
- Google-Maps-style UI: floating search, bottom sheet, filters, route HUD, live navigation, dark mode
