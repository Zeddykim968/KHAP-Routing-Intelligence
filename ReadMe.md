# KHAP — Kenya Health Access Platform

**Routing Intelligence · Emergency Dispatch · Geospatial Analysis**

A full-stack platform mapping **7,390 verified Kenyan healthcare facilities** across all 47 counties.  
Backend: FastAPI on PostgreSQL. Frontend: React 18 + Leaflet interactive map.  
Supports three access channels: **Web (REST + Map UI)**, **USSD (`*384*43149#`)**, and **SMS**.

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Features](#features)
4. [Project Structure](#project-structure)
5. [Prerequisites](#prerequisites)
6. [Local Setup (Replit)](#local-setup-replit)
7. [Environment Variables](#environment-variables)
8. [Running the App](#running-the-app)
9. [API Reference](#api-reference)
   - [Recommendations](#recommendations)
   - [Smart Routing](#smart-routing)
   - [GIS Intelligence](#gis-intelligence)
   - [Analytics](#analytics)
   - [Emergency / Ambulance](#emergency--ambulance)
   - [USSD](#ussd)
   - [SMS](#sms)
10. [Scoring Algorithms](#scoring-algorithms)
11. [USSD Flow](#ussd-flow)
12. [SMS Commands](#sms-commands)
13. [Deployment](#deployment)
14. [Roadmap](#roadmap)

---

## Overview

KHAP Routing Intelligence answers the question: **"What is the best healthcare facility for this person, right now?"**

It combines geospatial facility data, emergency-type matching, insurance/financial filtering, and real road routing (OSRM) to rank and direct users to the most appropriate facility — delivered over a React map UI, USSD feature-phone menu, and SMS.

---

## Architecture

```
Kenya Health Access Platform
            │
┌───────────┼──────────────┐
│           │              │
Web / Map  USSD           SMS
(React +  *384*43149#  (Africa's Talking
Leaflet)               webhook)
│           │              │
└───────────┼──────────────┘
            │
   KHAP Routing Intelligence
        (FastAPI · port 5000)
            │
   Replit PostgreSQL
   (7,390 facilities · PostGIS)
```

**Dev server ports:**
| Service | Port | Notes |
|---|---|---|
| FastAPI backend | 5000 | Uvicorn, auto-reload |
| React / Vite frontend | 5173 | Hot-reload, proxies `/api`, `/smart`, `/gis`, etc. to :5000 |

---

## Features

| Category | Capability |
|---|---|
| **Map UI** | Interactive Leaflet map · dark/light theme · facility colour-coding · county filter · search |
| **Smart Routing** | Emergency-type routing · insurance filter · financial-level filter · radius slider · ranked results with scores |
| **Road Directions** | Real road route polylines via OSRM · drive time · distance · straight-line fallback |
| **Population Monitoring** | Catchment population estimate · beds per 1,000 vs WHO benchmark · facility density |
| **Recommendations** | Scored facility list · nearby search · name search · facility detail · county/type lists |
| **GIS Intelligence** | Coverage analysis · accessibility scoring · travel-time estimation · catchment analysis |
| **Analytics** | National summary · county rankings · per-county drill-down |
| **Emergency** | Nearest emergency-capable facility with alternatives (`/ambulance`) |
| **USSD** | Full `*384*43149#` session — nearby and county-based flows |
| **SMS** | `FIND [county]` and `HELP` command parsing |

---

## Project Structure

```
khap/
├── app/
│   ├── main.py                  # FastAPI app, CORS, router registration
│   ├── config.py                # DATABASE_URL from environment
│   ├── recommendation_engine.py # Scoring algorithm + haversine
│   ├── routes/
│   │   ├── recommendatons.py    # GET /recommendations/*
│   │   ├── smart_routing.py     # GET /smart/* (emergency, OSRM, population)
│   │   ├── ambulance.py         # GET /ambulance
│   │   ├── analytics.py         # GET /analytics/*
│   │   ├── gis.py               # GET /gis/*
│   │   ├── ussd.py              # POST /ussd
│   │   └── sms.py               # POST /sms, /sms/webhook
│   └── services/
│       ├── db_service.py        # psycopg2 PostgreSQL client
│       ├── enrichment.py        # Insurance / financial level / emergency-type derivation
│       └── location_service.py  # Nominatim geocoding
├── database/
│   ├── setup_local_db.py        # Seeds 7,390 facilities from CSV into PostgreSQL
│   └── migrations/              # Schema SQL files
├── frontend/
│   ├── src/
│   │   ├── App.jsx              # Root component — state, layer switching
│   │   ├── api/index.js         # All fetch helpers (no direct fetch() elsewhere)
│   │   └── components/
│   │       ├── MapView.jsx      # Leaflet map, markers, route polylines, legend
│   │       ├── Sidebar.jsx      # All panels: facilities, emergency, coverage, reports
│   │       └── TopBar.jsx       # Navigation, layer switcher, search, theme toggle
│   ├── index.html
│   └── vite.config.js           # Proxy: /smart /gis /analytics /api → :5000
├── requirements.txt
└── ReadMe.md
```

---

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.10 + | 3.12 recommended |
| Node.js | 18 + | For the React frontend |
| PostgreSQL | 14 + | Provided automatically by Replit |

> No Docker, Redis, or external Supabase account required. The database is provisioned by Replit and exposed via `DATABASE_URL`.

---

## Local Setup (Replit)

The project is designed to run in Replit with zero manual configuration.

### 1. Database seed (first run only)

```bash
python database/setup_local_db.py
```

This creates the `facilities` table and imports all 7,390 facilities from the MoH CSV.

### 2. Start workflows

Two workflows run in parallel:

| Workflow | Command |
|---|---|
| `Start application` | `uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload` |
| `Start dashboard` | `cd frontend && npm run dev` |

Both are pre-configured in `.replit` and start automatically.

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | **Yes** | PostgreSQL connection string — set automatically by Replit |

> All secrets are managed through the Replit Secrets panel. No `.env` file is needed.

---

## Running the App

### Backend only

```bash
uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload
```

### Frontend only

```bash
cd frontend
npm install
npm run dev
```

### Both (Replit)

Start both workflows from the Replit interface. The map UI is served at port **5173**; the API at port **5000**.

- **Map UI:** `https://<repl>.replit.dev:5173`
- **API docs (Swagger):** `http://localhost:5000/docs`
- **OpenAPI schema:** `http://localhost:5000/openapi.json`

---

## API Reference

All endpoints return JSON unless stated otherwise. USSD returns `text/plain`.

Base URL: `http://localhost:5000`

---

### Recommendations

#### `GET /recommendations`

Returns scored facilities nearest to the user's location.

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `lat` | float | Yes | — | User latitude |
| `lon` | float | Yes | — | User longitude |
| `limit` | int | No | 10 | Max results (1–50) |
| `type` | string | No | — | Filter by facility type |
| `county` | string | No | — | Filter by county |
| `radius_km` | float | No | — | Only within this radius |
| `operational_only` | bool | No | true | Skip non-operational |

```bash
curl "http://localhost:5000/recommendations?lat=-1.2864&lon=36.8172&limit=5&radius_km=10"
```

---

#### `GET /recommendations/list`

Flat list for map rendering — no user coordinates needed.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `county` | string | — | Filter by county |
| `type` | string | — | Filter by type |
| `operational_only` | bool | true | — |
| `limit` | int | 500 | Max results (up to 2000) |

---

#### `GET /recommendations/search`

Full-text search by name or nearest town.

```bash
curl "http://localhost:5000/recommendations/search?q=kenyatta"
```

---

#### `GET /recommendations/nearby`

Nearest facilities within a radius, sorted by score.

```bash
curl "http://localhost:5000/recommendations/nearby?lat=-1.2864&lon=36.8172&radius_km=5&limit=3"
```

---

#### `GET /recommendations/facility/{facility_id}`

Single facility by integer ID.

---

#### `GET /recommendations/counties`

All 47 Kenya county names.

---

#### `GET /recommendations/types`

All distinct facility type strings.

---

### Smart Routing

The `/smart/*` endpoints provide emergency-aware, insurance-aware, OSRM-routed recommendations.

---

#### `GET /smart/recommend`

Returns facilities ranked for a specific emergency type with optional insurance and financial-level filters.

**Scoring weights:**

| Factor | Weight |
|---|---|
| Emergency type match | 35 % |
| Distance | 30 % |
| Availability (24h, weekends) | 20 % |
| Capacity (beds/cots) | 15 % |

| Parameter | Type | Default | Description |
|---|---|---|---|
| `lat` | float | — | User latitude |
| `lon` | float | — | User longitude |
| `location` | string | — | Town name (alternative to lat/lon) |
| `emergency_type` | string | `general` | `cardiac`, `trauma`, `maternity`, `pediatric`, `mental_health`, `dental`, `eye`, `general` |
| `insurance` | string | — | `NHIF`, `SHA`, `AAR`, `Jubilee`, `APA`, `CIC`, `Madison`, `Resolution`, `Britam`, `UAP`, `Medigold` |
| `financial_level` | string | — | `Free/Subsidized`, `Low`, `Medium`, `High` |
| `radius_km` | float | 50 | Search radius (1–300 km) |
| `limit` | int | 10 | Max results (1–30) |

```bash
curl "http://localhost:5000/smart/recommend?lat=-1.2921&lon=36.8219&emergency_type=cardiac&insurance=NHIF&limit=5"
```

**Response (sample):**

```json
{
  "query": {
    "emergency_type": { "id": "cardiac", "label": "Cardiac / Heart Attack", "icon": "❤️" },
    "insurance_filter": "NHIF",
    "radius_km": 50
  },
  "total_found": 983,
  "results": [
    {
      "name": "Kenyatta National Hospital",
      "type": "National Referral Hospital",
      "county": "Nairobi",
      "distance_km": 0.82,
      "estimated_minutes": 2,
      "score": 74.26,
      "financial_level": "Low",
      "insurance_providers": ["NHIF", "SHA"],
      "match_reason": "Best facility type for Cardiac / Heart Attack · 1800 beds/cots · Accepts: NHIF, SHA · Low cost"
    }
  ]
}
```

---

#### `GET /smart/road-route`

Returns a real road route geometry from OSRM with drive distance and time. Falls back to a 1.35× straight-line estimate if OSRM is unreachable.

| Parameter | Type | Required |
|---|---|---|
| `from_lat` | float | Yes |
| `from_lon` | float | Yes |
| `to_lat` | float | Yes |
| `to_lon` | float | Yes |

```bash
curl "http://localhost:5000/smart/road-route?from_lat=-1.2921&from_lon=36.8219&to_lat=-1.3032&to_lon=36.8263"
```

**Response:**

```json
{
  "source": "osrm",
  "distance_km": 2.0,
  "duration_minutes": 4,
  "geometry": {
    "type": "LineString",
    "coordinates": [[36.8219, -1.2921], ...]
  }
}
```

---

#### `GET /smart/population-served`

Estimates catchment population and compares facility density against the WHO benchmark (10 beds per 1,000 people). Uses Kenya average population density (~100 persons/km²).

| Parameter | Type | Default | Description |
|---|---|---|---|
| `lat` | float | — | Centre latitude |
| `lon` | float | — | Centre longitude |
| `radius_km` | float | 10 | Catchment radius (1–100 km) |

```bash
curl "http://localhost:5000/smart/population-served?lat=-1.2921&lon=36.8219&radius_km=10"
```

**Response (sample):**

```json
{
  "radius_km": 10,
  "catchment": {
    "estimated_population": 31416,
    "operational_facilities": 680,
    "beds_per_1000_people": 251.05,
    "who_beds_benchmark_per_1000": 10,
    "benchmark_status": "Above WHO benchmark"
  }
}
```

---

#### `GET /smart/emergency-types`

Lists all supported emergency types with labels and icons.

```bash
curl "http://localhost:5000/smart/emergency-types"
```

---

#### `GET /smart/insurance-providers`

Lists all insurance providers derived from facility ownership data.

```bash
curl "http://localhost:5000/smart/insurance-providers"
```

---

### GIS Intelligence

#### `GET /gis/coverage`

Everything within a radius — facility types, bed count, ownership mix, nearest facility.

```bash
curl "http://localhost:5000/gis/coverage?lat=-1.2864&lon=36.8172&radius_km=5"
```

---

#### `GET /gis/accessibility`

Accessibility score (0–100) and rating for a location based on facility density.

| Rating | Score |
|---|---|
| Excellent | 70–100 |
| Good | 45–69 |
| Moderate | 20–44 |
| Poor | 0–19 |

```bash
curl "http://localhost:5000/gis/accessibility?lat=-1.2864&lon=36.8172"
curl "http://localhost:5000/gis/accessibility?lat=3.5&lon=41.0"  # remote area
```

---

#### `GET /gis/travel-time`

Estimated road travel time (1.35 tortuosity factor, 40 km/h average speed).

```bash
curl "http://localhost:5000/gis/travel-time?from_lat=-1.2864&from_lon=36.8172&to_lat=-1.3&to_lon=36.9"
```

---

#### `GET /gis/catchment`

All facilities that could serve a population at a location within a radius.

```bash
curl "http://localhost:5000/gis/catchment?lat=-1.2864&lon=36.8172&radius_km=10"
```

---

### Analytics

#### `GET /analytics/summary`

National overview — totals, type breakdown, ownership breakdown.

```bash
curl "http://localhost:5000/analytics/summary"
```

**Response (sample):**

```json
{
  "total_facilities": 7390,
  "operational": 7114,
  "operational_rate_pct": 96.3,
  "total_beds_and_cots": 53354,
  "counties_covered": 47,
  "facility_type_breakdown": {
    "Dispensary": 3556,
    "Medical Clinic": 2163,
    "Health Centre": 951
  },
  "ownership_breakdown": {
    "Government": 3904,
    "Private": 2386,
    "Faith-Based": 303,
    "NGO": 813
  }
}
```

---

#### `GET /analytics/counties`

All 47 counties ranked by accessibility score.

```bash
curl "http://localhost:5000/analytics/counties"
```

---

#### `GET /analytics/county/{county_name}`

Full drill-down for a single county.

```bash
curl "http://localhost:5000/analytics/county/Nairobi"
curl "http://localhost:5000/analytics/county/Turkana"
```

---

### Emergency / Ambulance

#### `GET /ambulance`

Nearest emergency-capable facility (requires beds) plus 3 alternatives. Prioritises hospitals and medical centres.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `lat` | float | — | Emergency latitude |
| `lon` | float | — | Emergency longitude |
| `require_beds` | bool | true | Only match facilities with beds > 0 |

```bash
curl "http://localhost:5000/ambulance?lat=-1.2864&lon=36.8172"
curl "http://localhost:5000/ambulance?lat=-4.05&lon=39.67"   # Mombasa
curl "http://localhost:5000/ambulance?lat=0.517&lon=35.269"  # Eldoret
```

---

### USSD

#### `POST /ussd`

Africa's Talking USSD callback. Returns `text/plain` starting with `CON` (continue) or `END` (terminate).

```bash
# Welcome screen
curl -X POST http://localhost:5000/ussd \
  -d "sessionId=test&serviceCode=*384*43149%23&phoneNumber=%2B254712345678&text="

# Select nearby, enter coordinates
curl -X POST http://localhost:5000/ussd \
  -d "sessionId=test&serviceCode=*384*43149%23&phoneNumber=%2B254712345678&text=1*-1.28,36.82"

# Select service type (Hospital) → results
curl -X POST http://localhost:5000/ussd \
  -d "sessionId=test&serviceCode=*384*43149%23&phoneNumber=%2B254712345678&text=1*-1.28,36.82*2"
```

---

### SMS

#### `POST /sms`

JSON body. Parses `FIND` and `HELP` commands.

```bash
curl -X POST http://localhost:5000/sms \
  -H "Content-Type: application/json" \
  -d '{"message": "FIND MOMBASA HOSPITAL", "phone": "+254712345678"}'
```

#### `POST /sms/webhook`

Africa's Talking format — accepts `text`/`message` + `from`/`phone` fields.

---

### Meta

```bash
curl "http://localhost:5000/"       # Service info
curl "http://localhost:5000/health" # {"status": "ok"}
```

---

## Scoring Algorithms

### Standard recommendation scoring (`/recommendations`)

| Factor | Weight | How measured |
|---|---|---|
| Distance | 40 % | Haversine; closer = higher score |
| Capacity | 30 % | Beds + cots, normalised to dataset max |
| Facility level | 10 % | National Referral > Provincial > District > Health Centre > Clinic |
| Availability | 20 % | Open 24h (+10 pts), open weekends (+5), operational (+5) |

### Smart routing scoring (`/smart/recommend`)

| Factor | Weight | How measured |
|---|---|---|
| Emergency type match | 35 % | Preferred facility type match; 24h bonus; bed count penalty below minimum |
| Distance | 30 % | Proportional within radius |
| Availability | 20 % | Open 24h (60 pts), open weekends (40 pts) |
| Capacity | 15 % | Beds + cots × 2, capped at 100 |

### Insurance & Financial level derivation

Both fields are derived at runtime from the `owner` column — they are not stored in the database:

| Owner keyword | Financial level | Insurance providers |
|---|---|---|
| Government / County | Low | NHIF, SHA |
| NGO | Free/Subsidized | NHIF, SHA |
| Mission / Church / Catholic | Medium | NHIF, SHA, CIC, Jubilee, AAR |
| Private | High | NHIF, SHA, AAR, Jubilee, APA, CIC, Madison, Resolution, Britam, UAP, Medigold |
| Aga Khan | High | All 11 providers |

---

## USSD Flow

Dial `*384*43149#` on any Kenyan network.

```
Welcome to KHAP
1. Find nearby facility
2. Search by county
99. Exit

── Option 1: Nearby ──────────────────
Enter your coordinates (lat,lon)
→ -1.28,36.82

Select service type:
1. Any Facility  2. Hospital  3. Health Centre
4. Medical Clinic  5. Dispensary  6. Maternity Home
7. Dental Clinic  8. Eye Centre  9. Laboratory

→ Results: nearest 4 facilities with distance and town

── Option 2: County ──────────────────
Select your county (paginated list of 47)
→ same service type menu
→ Top 5 facilities in that county
```

---

## SMS Commands

| Command | Description | Example |
|---|---|---|
| `HELP` | Show available commands | `HELP` |
| `FIND [county]` | Top facilities in a county | `FIND NAIROBI` |
| `FIND [county] [type]` | Filter by type | `FIND MOMBASA HOSPITAL` |

**Supported types:** `HOSPITAL`, `CLINIC`, `DISPENSARY`, `MATERNITY`, `DENTAL`, `CENTRE`, `LAB`

---

## Deployment

### Replit (current)

Two workflows run in the Replit environment:

```
# Backend
uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload

# Frontend
cd frontend && npm run dev
```

`DATABASE_URL` is injected automatically by Replit. No `.env` file needed.

### Production server (VPS / cloud)

```bash
pip install -r requirements.txt
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:5000
```

For the frontend:

```bash
cd frontend
npm install
npm run build
# Serve dist/ with nginx or a static host
```

### CORS

All origins are currently allowed (`"*"`) for development. For production, restrict `allow_origins` in `app/main.py` to your domain.

---

## Roadmap

| Phase | Description | Status |
|---|---|---|
| 0 | Project foundation & dev environment | ✅ Done |
| 1 | PostgreSQL database (7,390 MoH facilities) | ✅ Done |
| 2 | ETL — CSV import via `database/setup_local_db.py` | ✅ Done |
| 3 | FastAPI microservice (Recommendations, USSD, SMS, Emergency, Search) | ✅ Done |
| 4 | GIS intelligence (Coverage, Accessibility, Catchment, Travel-time) | ✅ Done |
| 5 | Analytics (National summary, county rankings, drill-down) | ✅ Done |
| 6 | React + Leaflet interactive map frontend | ✅ Done |
| 7 | Smart Routing — emergency type routing, insurance/financial filtering | ✅ Done |
| 8 | OSRM real road routing with polyline display | ✅ Done |
| 9 | Population monitoring vs WHO benchmark | ✅ Done |
| 10 | Replit PostgreSQL migration (off Supabase) | ✅ Done |
| 11 | JWT auth, rate limiting, audit logs | Planned |
| 12 | Redis caching layer | Planned |
| 13 | Automated test suite | Planned |
| 14 | Docker + CI/CD deployment | Planned |
| 15 | Full KHAP platform integration (appointments, telemedicine) | In progress |
