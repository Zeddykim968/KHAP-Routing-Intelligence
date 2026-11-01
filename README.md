# KHAP — Kenya Health Access Platform

> A healthcare-finder and live-routing platform built with Django, Django REST Framework, Next.js, MapLibre GL, and OSRM.

---

## Overview

KHAP helps people in Kenya find the nearest health facility from their location, see what services and insurance schemes each facility accepts, and get live turn-by-turn driving directions to it.

The project combines:

- **Django + Django REST Framework** for the API backend.
- **SQLite by default / PostgreSQL via `DATABASE_URL`** — no PostGIS required (haversine + Python distance math), so it runs anywhere.
- **OSRM** for road routing and turn-by-turn navigation steps.
- **Next.js** for the web app: a Google-Maps-style interface with a MapLibre GL map, floating search, bottom sheet, filters, route HUD, live navigation mode, and dark mode.

---

## Architecture

```
                   Browser (Next.js — map + search + navigation UI)
                                     │  /api/* (Next.js rewrites)
                                     ▼
                              Django + DRF
                    (facilities, search, meta, route)
                         │                    │
                    SQLite/Postgres        OSRM Engine
                    (facility data)     (road routing)
```

---

## Technology Stack

| Layer          | Technology                       |
|----------------|----------------------------------|
| Backend        | Django 6 + Django REST Framework |
| Database       | SQLite (default) / PostgreSQL    |
| Routing Engine | OSRM (public demo by default)    |
| Frontend       | Next.js (App Router)             |
| Mapping        | MapLibre GL (CARTO styles)       |
| Icons          | lucide-react                     |

---

## Project Structure

```
KHAP/
│
├── backend/
│   ├── manage.py
│   ├── khap/                     # Django project (settings, urls, wsgi, asgi)
│   └── facilities/               # Django app
│       ├── models.py             # Service, Insurance, Facility
│       ├── serializers.py
│       ├── views.py              # /api/health/ /api/meta/ /api/facilities/ /api/search/ /api/route/
│       ├── urls.py
│       ├── services.py           # haversine, opening-hours parsing, OSRM client
│       ├── admin.py
│       ├── migrations/
│       └── management/commands/seed_facilities.py   # 54 Kenyan facilities
│
├── frontend/                     # Next.js web UI
│   ├── app/                      # App Router pages + layout
│   ├── components/               # Map, SearchBar, BottomSheet, FacilityCard, ...
│   ├── lib/                      # API client, formatting helpers
│   └── next.config.js            # rewrites /api/* → Django
│
├── database/                     # Legacy PostGIS schema notes
├── osrm/                         # Local OSRM setup notes (Docker)
├── requirements.txt
├── .env.example
└── README.md                     ← you are here
```

---

## API Endpoints

All endpoints are prefixed with `/api`.

### Health

```
GET /api/health/
```

### Meta (filter options)

```
GET /api/meta/
```

Returns facility types, service catalogue, insurance schemes, and counties.

### Facilities

```
GET /api/facilities/                       list (paginated; filterable)
GET /api/facilities/{id}/                  single facility
GET /api/facilities/nearest/?lat=&lon=&limit=N
```

Filters on `/api/facilities/`: `facility_type`, `county`, `town`, `service` (slug), `insurance` (slug), `emergency`, `wheelchair`, `search`, `open_now`.

### Search (typeahead)

```
GET /api/search/?q=aga&lat=-1.29&lon=36.82
```

### Routing

```
POST /api/route/
Body: { "start_lat": -1.29, "start_lon": 36.82, "end_lat": -1.30, "end_lon": 36.81 }

Response: { distance_m, duration_s, geometry, route: [[lon,lat], ...], steps: [...] }
```

Each step has an `instruction`, `name`, `distance_m`, `duration_s`, and location — used for turn-by-turn navigation.

---

## Application Workflow

```
User opens app → Next.js map loads (CARTO positron / dark-matter style)
 ↓
"Use my location" (GPS) or typed search
 ↓
Django: /api/facilities/nearest/ (haversine) or /api/search/
 ↓
Bottom sheet shows nearest facilities with distance + open/closed status
 ↓
Facility selected → services + accepted insurances shown
 ↓
"Directions" → Django /api/route/ → OSRM (road route + turn-by-turn steps)
 ↓
Route drawn on map; live navigation mode tracks GPS (watchPosition) and re-routes
```

---

## Quick Start

### 1. Backend

```bash
# Create a virtualenv and install dependencies
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# Configure environment (optional — SQLite works out of the box)
cp .env.example .env

# Migrate + seed 54 Kenyan facilities
.venv/bin/python backend/manage.py migrate
.venv/bin/python backend/manage.py seed_facilities

# Run the API on :8000
.venv/bin/python backend/manage.py runserver 0.0.0.0:8000
```

Health check: http://localhost:8000/api/health/
Admin: http://localhost:8000/admin/ (create a superuser with `manage.py createsuperuser`)

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

App at http://localhost:3000. Next.js rewrites `/api/*` to the Django backend, so no extra configuration is needed. To point elsewhere, set `NEXT_PUBLIC_API_URL` in `frontend/.env.local`.

### 3. Routing

The default routing engine is the **public OSRM demo server** — no setup required. For production, run your own OSRM instance (see `osrm/README.md`) and set `OSRM_URL`.

---

## Environment Variables

| Variable                | Description                            | Default                              |
|-------------------------|----------------------------------------|--------------------------------------|
| `DATABASE_URL`          | PostgreSQL connection string           | *(unset → SQLite `db.sqlite3`)*      |
| `DJANGO_SECRET_KEY`     | Django secret key                      | insecure dev default                 |
| `DJANGO_DEBUG`          | Debug mode                             | `true`                               |
| `DJANGO_ALLOWED_HOSTS`  | Comma-separated hosts                  | `*`                                  |
| `CORS_ALLOWED_ORIGINS`  | Comma-separated CORS origins           | `*`                                  |
| `OSRM_URL`              | OSRM routing engine base URL           | `http://router.project-osrm.org`     |
| `NEXT_PUBLIC_API_URL`   | Frontend override for the API host     | `/api` (same-origin rewrite)         |

---

## Features

- **Find nearest facilities** from GPS location or any searched place.
- **Service & insurance transparency** — every facility lists its services (maternity, dialysis, ICU, surgery, ...) and accepted insurance (SHA, NHIF legacy, private insurers, cash/self-pay).
- **Live routing** — road-accurate routes with turn-by-turn instructions via OSRM.
- **Navigation mode** — live GPS tracking with automatic re-routing when you drift off route.
- **Google-Maps-style UI** — floating search with typeahead, draggable snapping bottom sheet, filter chips, route HUD with ETA, place pins.
- **Dark mode** — UI and map style switch together (CARTO positron ↔ dark-matter).
- **Opening status** — open/closed detection from OSM-style opening hours.

---

## License

MIT License

---

## Author

**Zedrick Kimutai Biwott**
BSc Applied Statistics & Data Science
The Co-operative University of Kenya
Kenya
