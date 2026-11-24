# KHAP — Kenya Health Access Platform

> A healthcare-finder and live-routing platform built with Django, Django REST Framework, Next.js, MapLibre GL, and OpenRouteService.

---

## Overview

KHAP helps people in Kenya find the nearest health facility from their location, see what services and insurance schemes each facility accepts, and get live turn-by-turn driving directions to it.

The project combines:

- **Django + Django REST Framework** for the API backend.
- **SQLite by default / PostgreSQL via `DATABASE_URL`** — no PostGIS required (haversine + Python distance math), so it runs anywhere.
- **OpenRouteService** for road routing and turn-by-turn navigation steps.
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
                    SQLite/Postgres     OpenRouteService
                    (facility data)     (road routing)
```

---

## Technology Stack

| Layer          | Technology                       |
|----------------|----------------------------------|
| Backend        | Django 6 + Django REST Framework |
| Database       | SQLite (default) / PostgreSQL    |
| Routing Engine | OpenRouteService                  |
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
│       ├── services.py           # haversine, opening hours, OpenRouteService client
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
├── requirements.txt
├── .env                          # local configuration (git-ignored)
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
GET /api/facilities/nearest/?lat=&lon=&limit=N&profile=driving
```

`nearest` ranks facilities by **real road distance** from the user's location using the
OpenRouteService matrix API: the closest `ORS_MATRIX_CANDIDATES` facilities (by straight-line
distance) are sent to ORS, which returns travel distance and duration for each. The response
carries `travel_distance_m` / `travel_duration_s` per facility plus a `routing` block
(`engine: "openrouteservice"`, `profile`, `routed_count`, optional `note` / `unrouted_count`).
Facilities ORS cannot route to are omitted, never ranked by straight-line distance. If ORS is
not configured or fails, the endpoint returns `502` with the reason (`404` when nothing is routable).

`profile` accepts `driving` (driving-car), `walking` (foot-walking) or `cycling` (cycling-regular).

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

Each step has an `instruction`, `name`, `distance_m`, `duration_s`, and location — used for turn-by-turn navigation. Directions come from OpenRouteService (`engine: "openrouteservice"`) — the only routing engine, so ORS failures return an explicit error (`502`, or `404` when no route exists).

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
"Directions" → Django /api/route/ → OpenRouteService (road route + turn-by-turn steps)
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

# Configure environment (see Environment Variables below)
# Create a root .env with DATABASE_URL and ORS_API_KEY

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

App at http://localhost:3000. Next.js rewrites `/api/*` to the Django backend, so no extra configuration is needed. To point elsewhere, set `NEXT_API_URL` in `frontend/.env.local` (or export it before starting the dev server).

### 3. Routing

**OpenRouteService is the only routing engine**: set `ORS_API_KEY` in `.env` (get a key at
https://openrouteservice.org/dev/#/signup) and nearest-facility ranking plus directions use it.

There is no fallback engine. If `ORS_API_KEY` is missing, ORS is unreachable, or ORS rejects the
request, the API returns the reason as an error (`502`, or `404` when ORS finds no route) rather
than degraded or straight-line results.

---

## Environment Variables

| Variable                | Description                            | Default                              |
|-------------------------|----------------------------------------|--------------------------------------|
| `DATABASE_URL`          | PostgreSQL connection string (required to be reachable when set) | *(unset → SQLite `db.sqlite3`)* |
| `DJANGO_SECRET_KEY`     | Django secret key                      | insecure dev default                 |
| `DJANGO_DEBUG`          | Debug mode                             | `true`                               |
| `DJANGO_ALLOWED_HOSTS`  | Comma-separated hosts                  | `*`                                  |
| `CORS_ALLOWED_ORIGINS`  | Comma-separated CORS origins           | `*`                                  |
| `ORS_API_KEY`           | OpenRouteService API key (required for routing) | *(unset → routing returns an error)* |
| `ORS_URL`               | OpenRouteService base URL              | `https://api.openrouteservice.org`   |
| `ORS_PROFILE`           | Default ORS routing profile            | `driving-car`                        |
| `ORS_MATRIX_CANDIDATES` | Facilities ranked via the ORS matrix   | `25`                                 |
| `ORS_MATRIX_BATCH`      | Matrix batch size (max 49 destinations) | `25`                                |
| `DB_CONNECT_TIMEOUT`    | Seconds to wait for the PostgreSQL connection | `5`                            |
| `NEXT_API_URL`          | Frontend override for the API host     | `/api` (same-origin rewrite)         |

---

## Features

- **Find nearest facilities** from GPS location or any searched place, ranked by real road distance and travel time (OpenRouteService matrix API).
- **Service & insurance transparency** — every facility lists its services (maternity, dialysis, ICU, surgery, ...) and accepted insurance (SHA, NHIF legacy, private insurers, cash/self-pay).
- **Live routing** — road-accurate routes with turn-by-turn instructions via OpenRouteService.
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
