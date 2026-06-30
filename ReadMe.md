# KHAP Routing Intelligence

**Kenya Health Access Platform — Routing Intelligence Microservice**

A production-ready FastAPI microservice serving **7,406 verified Kenyan healthcare facilities** across all 47 counties. Supports three access channels: Web API, USSD (`*384*43149#`), and SMS. Built to integrate with the Kenya Health Access Platform (appointments, emergency response, facility directory, and telemedicine modules).

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Features](#features)
4. [Project Structure](#project-structure)
5. [Prerequisites](#prerequisites)
6. [Local Setup](#local-setup)
7. [Environment Variables](#environment-variables)
8. [Running the Server](#running-the-server)
9. [API Reference](#api-reference)
   - [Recommendations](#recommendations)
   - [GIS Intelligence](#gis-intelligence)
   - [Analytics](#analytics)
   - [Emergency](#emergency)
   - [USSD](#ussd)
   - [SMS](#sms)
10. [Scoring Algorithm](#scoring-algorithm)
11. [USSD Flow](#ussd-flow)
12. [SMS Commands](#sms-commands)
13. [Deployment](#deployment)
14. [Roadmap](#roadmap)

---

## Overview

KHAP Routing Intelligence is a geospatial microservice that answers the question: **"What is the best healthcare facility for this person, right now?"**

It scores facilities using a weighted algorithm (distance, capacity, facility level, and availability), exposes the results via REST API, and delivers them over Web, USSD, and SMS channels to cover both smartphone and feature-phone users across Kenya.

---

## Architecture

```
Kenya Health Access Platform
            │
┌───────────┼───────────┐
│           │           │
Web       USSD         SMS
(REST)  *384*43149#  (Africa's Talking / Webhook)
│           │           │
└───────────┼───────────┘
            │
   KHAP Routing Intelligence
        (FastAPI)
            │
        Supabase
   (7,406 facilities)
```

---

## Features

| Category | Endpoints |
|---|---|
| **Recommendations** | Scored facility list, nearby search, name search, facility detail, county/type lists |
| **GIS Intelligence** | Coverage analysis, accessibility scoring, travel-time estimation, catchment analysis |
| **Analytics** | National summary, county rankings, per-county drill-down |
| **Emergency** | Single nearest emergency-capable facility with alternatives |
| **USSD** | Full `*384*43149#` session — nearby and county-based flows |
| **SMS** | `FIND [county]` and `HELP` command parsing |

---

## Project Structure

```
khap-routing-intelligence/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI app, CORS, router registration
│   ├── config.py                # Environment variable loading
│   ├── recommendation_engine.py # Scoring algorithm + haversine
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── recommendatons.py    # /recommendations/*
│   │   ├── ambulance.py         # /ambulance
│   │   ├── analytics.py         # /analytics/*
│   │   ├── gis.py               # /gis/*
│   │   ├── ussd.py              # /ussd
│   │   └── sms.py               # /sms, /sms/webhook
│   └── services/
│       ├── __init__.py
│       └── supabase_service.py  # Supabase client singleton
├── requirements.txt             # Production dependencies
├── requirements-local.txt       # Windows / Python 3.14 local dev overrides
└── ReadMe.md
```

---

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.10 + | 3.12 recommended |
| pip | Any | Comes with Python |
| Supabase account | — | Free tier works |
| Supabase project | — | With `facilities` table populated |

> **No Docker, Redis, or OSRM needed** to run the current version. Those are planned for V3 Phase 4–5.

---

## Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/your-org/khap-routing-intelligence.git
cd khap-routing-intelligence
```

### 2. Create a virtual environment

```bash
python -m venv venv

# macOS / Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Install dependencies

**Standard (macOS / Linux / Python ≤ 3.13):**

```bash
pip install -r requirements.txt
```

**Windows or Python 3.14+ (avoids pyiceberg build errors):**

```bash
pip install -r requirements-local.txt
```

### 4. Set up environment variables

Create a `.env` file in the project root:

```env
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-anon-public-key
SUPABASE_SERVICE_KEY=your-service-role-secret-key
```

> **Important:** Use the **service role key** (`SUPABASE_SERVICE_KEY`) for all database reads. The anon key will be blocked by Row Level Security on the `facilities` table.

> **Important:** If your Supabase URL ends with `/rest/v1` or `/rest/v1/`, the app strips it automatically — paste either form.

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `SUPABASE_URL` | Yes | Your Supabase project URL |
| `SUPABASE_KEY` | Yes | Anon / public key (fallback) |
| `SUPABASE_SERVICE_KEY` | Yes | Service role key — bypasses RLS |

---

## Running the Server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload
```

The API will be available at:

- **API root:** `http://localhost:5000/`
- **Interactive docs (Swagger UI):** `http://localhost:5000/docs`
- **OpenAPI schema:** `http://localhost:5000/openapi.json`

> **Note:** If your Supabase project is on the free tier, it auto-pauses after 1 week of inactivity. If you get connection errors, log in to [supabase.com/dashboard](https://supabase.com/dashboard) and click **Restore project**.

---

## API Reference

All endpoints return JSON unless stated otherwise. USSD returns `text/plain`.

Base URL (local): `http://localhost:5000`

---

### Recommendations

#### `GET /recommendations`

Returns scored facilities nearest to the user's location.

**Query parameters:**

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `lat` | float | Yes | — | User latitude |
| `lon` | float | Yes | — | User longitude |
| `limit` | int | No | 10 | Max results (1–50) |
| `type` | string | No | — | Filter by facility type |
| `county` | string | No | — | Filter by county |
| `radius_km` | float | No | — | Only within this radius |
| `operational_only` | bool | No | true | Skip non-operational |

**Example:**

```bash
curl "http://localhost:5000/recommendations?lat=-1.286389&lon=36.817223&limit=5&radius_km=10"
```

**Response:**

```json
{
  "user_location": { "latitude": -1.286389, "longitude": 36.817223 },
  "filters": { "type": null, "county": null, "radius_km": 10, "operational_only": true },
  "total_found": 214,
  "results": [
    {
      "facility_id": 70,
      "name": "Avenue Hospital",
      "county": "Nairobi",
      "type": "Other Hospital",
      "beds": 65,
      "distance_km": 0.0,
      "score": 77.5
    }
  ]
}
```

---

#### `GET /recommendations/nearby`

Shortcut — returns the nearest facilities within a radius, sorted by score.

```bash
curl "http://localhost:5000/recommendations/nearby?lat=-1.286389&lon=36.817223&radius_km=5&limit=3"
```

---

#### `GET /recommendations/search`

Full-text search by facility name or nearest town across all 7,406 facilities.

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `q` | string | Yes | — | Search term (min 2 chars) |
| `limit` | int | No | 10 | Max results |
| `operational_only` | bool | No | true | — |

```bash
curl "http://localhost:5000/recommendations/search?q=kenyatta"
curl "http://localhost:5000/recommendations/search?q=mater&limit=5"
curl "http://localhost:5000/recommendations/search?q=nakuru"
```

---

#### `GET /recommendations/types`

Returns all distinct facility types in the database.

```bash
curl "http://localhost:5000/recommendations/types"
```

```json
{
  "types": ["Dental Clinic", "Dispensary", "District Hospital", "Eye Centre", ...]
}
```

---

#### `GET /recommendations/counties`

Returns all 47 counties.

```bash
curl "http://localhost:5000/recommendations/counties"
```

---

#### `GET /recommendations/list`

Returns facilities as a flat list — intended for map rendering. No coordinates required.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `county` | string | — | Filter by county |
| `type` | string | — | Filter by type |
| `operational_only` | bool | true | — |
| `limit` | int | 500 | Max results (up to 2000) |

```bash
curl "http://localhost:5000/recommendations/list?county=Nairobi&type=District+Hospital"
```

---

#### `GET /recommendations/facility/{facility_id}`

Returns a single facility by its integer ID.

```bash
curl "http://localhost:5000/recommendations/facility/70"
```

---

### GIS Intelligence

#### `GET /gis/coverage`

Breaks down everything within a radius of a point — facility types, bed count, ownership mix, nearest facility.

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `lat` | float | Yes | — | Centre latitude |
| `lon` | float | Yes | — | Centre longitude |
| `radius_km` | float | No | 10 | Radius (1–200 km) |

```bash
curl "http://localhost:5000/gis/coverage?lat=-1.286389&lon=36.817223&radius_km=5"
```

**Response:**

```json
{
  "centre": { "latitude": -1.286389, "longitude": 36.817223 },
  "radius_km": 5.0,
  "total_facilities": 109,
  "total_beds_and_cots": 768,
  "open_24h_facilities": 0,
  "facility_type_breakdown": { "Medical Clinic": 66, "Dispensary": 22, ... },
  "ownership_breakdown": { "Private": 73, "Government": 6, ... },
  "nearest_facility": { "name": "...", "type": "...", "distance_km": 0.0 }
}
```

---

#### `GET /gis/accessibility`

Returns an accessibility score (0–100) and rating for a location based on facility density within 5 km, 15 km, and 50 km.

| Rating | Score Range |
|---|---|
| Excellent | 70–100 |
| Good | 45–69 |
| Moderate | 20–44 |
| Poor | 0–19 |

```bash
curl "http://localhost:5000/gis/accessibility?lat=-1.286389&lon=36.817223"

# Remote area example
curl "http://localhost:5000/gis/accessibility?lat=3.5&lon=41.0"
```

**Response:**

```json
{
  "location": { "latitude": -1.286389, "longitude": 36.817223 },
  "accessibility_score": 100,
  "rating": "Excellent",
  "catchment_summary": {
    "within_5km": { "facilities": 683, "beds": 7891, "open_24h": 0 },
    "within_15km": { "facilities": 937 },
    "within_50km": { "facilities": 986 }
  }
}
```

---

#### `GET /gis/travel-time`

Estimates road travel time between two coordinates using a 1.35 tortuosity factor and 40 km/h average speed.

```bash
curl "http://localhost:5000/gis/travel-time?from_lat=-1.286389&from_lon=36.817223&to_lat=-1.3&to_lon=36.9"
```

**Response:**

```json
{
  "straight_line_km": 9.33,
  "estimated_road_km": 12.59,
  "estimated_minutes": 19,
  "note": "Estimate based on 1.35 tortuosity factor and 40 km/h average speed."
}
```

---

#### `GET /gis/catchment`

Returns all facilities that could serve a population at a given location within a radius, with distance and drive time per facility.

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `lat` | float | Yes | — | — |
| `lon` | float | Yes | — | — |
| `radius_km` | float | No | 20 | Max radius (1–100 km) |
| `facility_type` | string | No | — | e.g. `Dispensary`, `District Hospital` |

```bash
curl "http://localhost:5000/gis/catchment?lat=-1.286389&lon=36.817223&radius_km=10&facility_type=District+Hospital"
```

---

### Analytics

All analytics endpoints paginate through all 7,406 rows from Supabase (8 batches of 1,000) to ensure complete data. Expect response times of 3–8 seconds on first call.

#### `GET /analytics/summary`

National overview — totals, type breakdown, ownership breakdown.

```bash
curl "http://localhost:5000/analytics/summary"
```

**Response (sample):**

```json
{
  "total_facilities": 7406,
  "operational": 7114,
  "non_operational": 292,
  "operational_rate_pct": 96.1,
  "total_beds_and_cots": 53354,
  "counties_covered": 47,
  "facility_type_breakdown": {
    "Dispensary": 3556,
    "Medical Clinic": 2163,
    "Health Centre": 951,
    ...
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

All 47 counties ranked by accessibility score. Score is a weighted composite of facility count (40%), bed count (40%), and hospital count (20%), normalised to 0–100.

```bash
curl "http://localhost:5000/analytics/counties"
```

**Response (sample):**

```json
{
  "total_counties": 47,
  "counties": [
    {
      "rank": 1,
      "county": "Nairobi",
      "facilities": 540,
      "beds": 7201,
      "hospitals": 25,
      "health_centres": 71,
      "dispensaries": 119,
      "open_24h": 0,
      "accessibility_score": 100.0
    },
    ...
  ]
}
```

---

#### `GET /analytics/county/{county_name}`

Full drill-down for a single county — type breakdown, district breakdown, top owners, largest facility.

```bash
curl "http://localhost:5000/analytics/county/Nairobi"
curl "http://localhost:5000/analytics/county/Mombasa"
curl "http://localhost:5000/analytics/county/Turkana"
```

---

### Emergency

#### `GET /ambulance`

Returns the single highest-scoring emergency-capable facility with beds, plus 3 alternatives. Prioritises hospitals, medical centres, and health centres with beds.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `lat` | float | — | Emergency location latitude |
| `lon` | float | — | Emergency location longitude |
| `require_beds` | bool | true | Only match facilities with beds/cots > 0 |

```bash
curl "http://localhost:5000/ambulance?lat=-1.286389&lon=36.817223"
curl "http://localhost:5000/ambulance?lat=-4.05&lon=39.67"   # Mombasa
curl "http://localhost:5000/ambulance?lat=0.517&lon=35.269"  # Eldoret
```

**Response (sample):**

```json
{
  "emergency": true,
  "user_location": { "latitude": -1.286389, "longitude": 36.817223 },
  "nearest_facility": {
    "name": "Kenyatta National Hospital",
    "type": "National Referral Hospital",
    "county": "Nairobi",
    "beds": 1800,
    "distance_km": 2.4,
    "estimated_drive_minutes": 4
  },
  "alternatives": [...]
}
```

---

### USSD

#### `POST /ussd`

Handles Africa's Talking USSD callback format. Returns `text/plain` — must start with `CON` (continue session) or `END` (terminate session).

**Request format** (`application/x-www-form-urlencoded`):

| Field | Description |
|---|---|
| `sessionId` | Session identifier |
| `serviceCode` | USSD code e.g. `*384*43149#` |
| `phoneNumber` | Caller phone number |
| `text` | Accumulated input (e.g. `1*-1.28,36.82*2`) |

**Test with curl:**

```bash
# Welcome screen
curl -X POST http://localhost:5000/ussd \
  -d "sessionId=test123&serviceCode=*384*43149%23&phoneNumber=%2B254712345678&text="

# User pressed 1 (Find nearby)
curl -X POST http://localhost:5000/ussd \
  -d "sessionId=test123&serviceCode=*384*43149%23&phoneNumber=%2B254712345678&text=1"

# User entered coordinates
curl -X POST http://localhost:5000/ussd \
  -d "sessionId=test123&serviceCode=*384*43149%23&phoneNumber=%2B254712345678&text=1*-1.28,36.82"

# User selected service type 2 (Hospital)
curl -X POST http://localhost:5000/ussd \
  -d "sessionId=test123&serviceCode=*384*43149%23&phoneNumber=%2B254712345678&text=1*-1.28,36.82*2"

# County search — user pressed 2, then county 30 (Nairobi), then service 1 (Any)
curl -X POST http://localhost:5000/ussd \
  -d "sessionId=test123&serviceCode=*384*43149%23&phoneNumber=%2B254712345678&text=2*30*1"
```

---

### SMS

#### `POST /sms`

JSON body. Parses `FIND` and `HELP` commands.

```bash
# Help
curl -X POST http://localhost:5000/sms \
  -H "Content-Type: application/json" \
  -d '{"message": "HELP", "phone": "+254712345678"}'

# Find any facility in Mombasa
curl -X POST http://localhost:5000/sms \
  -H "Content-Type: application/json" \
  -d '{"message": "FIND MOMBASA", "phone": "+254712345678"}'

# Find hospitals in Kisumu
curl -X POST http://localhost:5000/sms \
  -H "Content-Type: application/json" \
  -d '{"message": "FIND KISUMU HOSPITAL", "phone": "+254712345678"}'

# Find dispensaries in Kitui
curl -X POST http://localhost:5000/sms \
  -H "Content-Type: application/json" \
  -d '{"message": "FIND KITUI DISPENSARY", "phone": "+254712345678"}'
```

#### `POST /sms/webhook`

Africa's Talking / webhook format — accepts any JSON with `text`/`message` and `from`/`phone` fields.

```bash
curl -X POST http://localhost:5000/sms/webhook \
  -H "Content-Type: application/json" \
  -d '{"text": "FIND NAIROBI HOSPITAL", "from": "+254712345678"}'
```

---

### Meta

```bash
curl "http://localhost:5000/"        # Service info
curl "http://localhost:5000/health"  # Health check → {"status": "ok"}
```

---

## Scoring Algorithm

Facilities are ranked using a weighted composite score:

| Factor | Weight | How measured |
|---|---|---|
| Distance | 40% | Haversine great-circle distance; closer = higher score |
| Capacity | 30% | Total beds + cots; normalised to dataset max |
| Facility level | 10% | National Referral > Provincial > District > Health Centre > Clinic |
| Availability | 20% | Open 24h (+10), open weekends (+5), operational (+5) |

**Formula:**

```
score = (distance_score × 0.40)
      + (capacity_score × 0.30)
      + (level_score   × 0.10)
      + (availability  × 0.20)
```

Scores range from 0 to 100. The top-scoring facility for a given location wins.

---

## USSD Flow

Dial `*384*43149#` on any Kenyan network.

```
Welcome to KHAP
1. Find nearby facility
2. Search by county
99. Exit

─── Option 1: Nearby ───────────────
Enter your coordinates (lat,lon)
→ -1.28,36.82

Select service type:
1. Any Facility
2. Hospital
3. Health Centre
4. Medical Clinic
5. Dispensary
6. Maternity Home
7. Dental Clinic
8. Eye Centre
9. Laboratory

→ Results: nearest 4 facilities with distance and town

─── Option 2: County ───────────────
Select your county (paginated list of 47)
→ same service type menu
→ Top 5 facilities in that county
```

---

## SMS Commands

| Command | Description | Example |
|---|---|---|
| `HELP` | Show available commands | `HELP` |
| `FIND [county]` | List top facilities in a county | `FIND NAIROBI` |
| `FIND [county] [type]` | Filter by type | `FIND MOMBASA HOSPITAL` |

**Supported types:** `HOSPITAL`, `CLINIC`, `DISPENSARY`, `MATERNITY`, `DENTAL`, `CENTRE`, `LAB`

---

## Deployment

### Replit (current)

The project runs on Replit using the workflow:

```
uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload
```

Secrets (`SUPABASE_URL`, `SUPABASE_KEY`, `SUPABASE_SERVICE_KEY`) are managed via the Replit Secrets panel — no `.env` file needed on Replit.

### Production server (VPS / cloud)

```bash
# Install
pip install -r requirements.txt

# Run with gunicorn + uvicorn workers
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:5000
```

### CORS

The following origins are allowed by default:

```
https://kenya-health-access.vercel.app
http://localhost:3000
http://localhost:5173
http://localhost:5000
```

To add more origins, update `allow_origins` in `app/main.py`.

---

## Roadmap

| Phase | Description | Status |
|---|---|---|
| 0 | Project foundation & dev environment | Done |
| 1 | Supabase facilities database | Done |
| 2 | ETL — 7,406 MoH facilities imported | Done |
| 6 | FastAPI microservice (Recommendations, USSD, SMS, Emergency, Search) | Done |
| 7 | GIS intelligence (Coverage, Accessibility, Catchment, Travel-time) | Done |
| 10 | Analytics (National summary, county rankings, drill-down) | Done |
| 3 | OpenStreetMap road network via PgSnapshot | Planned |
| 4 | OSRM routing engine (real road times) | Planned |
| 5 | Redis caching layer | Planned |
| 8 | React + MapLibre frontend | Planned |
| 9 | Full KHAP platform integration | In progress |
| 11 | JWT auth, rate limiting, audit logs | Planned |
| 12 | Automated test suite | Planned |
| 13 | Docker + CI/CD deployment | Planned |
| 14 | Full documentation | In progress |
