# KHAP — Kenya Health Access Platform

A healthcare-finder and live-routing platform built with Django, Django REST Framework, Next.js, MapLibre GL, and OpenRouteService.

## Project Structure

```
KHAP/
├── backend/
│   ├── manage.py
│   ├── khap/               # Django project (settings, urls, wsgi, asgi)
│   └── facilities/         # models, serializers, views, urls, OpenRouteService client, seed command
├── frontend/               # Next.js web UI (App Router, MapLibre GL map)
├── .env                    # local configuration (git-ignored)
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
| `ORS_API_KEY`          | OpenRouteService API key (required)  | unset → routing returns an error |
| `ORS_URL`              | OpenRouteService base URL            | `https://api.openrouteservice.org` |
| `ORS_PROFILE`          | Default ORS profile                  | `driving-car`                    |
| `DB_CONNECT_TIMEOUT`   | PostgreSQL connect timeout (seconds) | `5`                              |
| `NEXT_API_URL`         | Frontend API host override           | `/api` rewrite (same origin)     |

Set backend vars in `.env` (repo root or `backend/`); frontend vars in `frontend/.env.local`.
See the variable table above.

## API

- `GET  /api/health/` — health + DB/OpenRouteService status
- `GET  /api/meta/` — facility types, services, insurers, counties
- `GET  /api/facilities/` — list with filters (type, county, service, insurance, emergency, open_now, search)
- `GET  /api/facilities/nearest/?lat=&lon=&limit=&profile=` — nearest facilities ranked by ORS road distance (errors if ORS fails)
- `GET  /api/search/?q=` — typeahead search
- `POST /api/route/` — OpenRouteService route + turn-by-turn steps between two lat/lon points

## User Preferences

- Django + Django REST Framework backend; Next.js frontend (replaces FastAPI + Vite/React)
- PostgreSQL via `DATABASE_URL` (no PostGIS required — haversine distances); no silent SQLite fallback — a failed Postgres connection raises the driver error at startup
- OpenRouteService (matrix + directions) as the only routing engine — no OSRM or straight-line fallback; ORS failures surface as explicit errors
- MapLibre GL with free CARTO styles (positron light / dark-matter dark) for the map
- CSS Modules for component styling
- Google-Maps-style UI: floating search, bottom sheet, filters, route HUD, live navigation, dark mode
