# KHAP Routing Intelligence V3 — Architecture

## Overview

KHAP Routing Intelligence V3 is a **production-ready geospatial microservice** that integrates with the Kenya Health Access Platform, providing routing, spatial analytics, healthcare accessibility intelligence, and location-based APIs.

```
                  Kenya Health Access Platform
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
 Patient Portal      Appointment System     Emergency Module
        │                    │                    │
        └────────────────────┼────────────────────┘
                             │
                  KHAP Routing Intelligence V3
                             │
    ┌──────────┬─────────────┼──────────┬──────────────┐
    │          │             │          │              │
  FastAPI   Cache        OSRM       Supabase      ETL Services
  (V3 API)  (Memory/   (Routing)  (PostgreSQL    (Validators,
            Redis)                + PostGIS)      Pipelines)
```

## Tech Stack

| Layer        | Technology                        |
|--------------|-----------------------------------|
| API          | FastAPI 0.138, Python 3.12        |
| Database     | Supabase (PostgreSQL + PostGIS)   |
| Routing      | OSRM (via public API + fallback)  |
| Caching      | cachetools (in-memory) / Redis    |
| Auth         | JWT (python-jose) + Supabase Auth |
| Rate Limiting| slowapi                           |
| Frontend     | React 18 + Leaflet + Vite         |

## Directory Structure

```
KHAP-Routing-Intelligence/
├── app/
│   ├── api/v3/          # V3 API modules
│   │   ├── auth.py      # JWT auth, registration, API keys
│   │   ├── facilities.py# Facility CRUD, search, stats
│   │   ├── routing.py   # Road routing, travel times
│   │   ├── analytics.py # Accessibility, coverage, gaps
│   │   ├── gis.py       # Spatial analysis, buffers, catchments
│   │   ├── reports.py   # National/county/emergency reports
│   │   └── admin.py     # ETL import, cache, system stats
│   ├── auth/            # JWT, passwords, API keys
│   ├── cache/           # TTL cache, rate limiting
│   ├── etl/             # Validators, pipeline
│   ├── gis/             # Spatial computations
│   ├── routing/         # OSRM travel time, route geometry
│   ├── analytics/       # Accessibility, coverage, load, gaps
│   ├── routes/          # Legacy V1/V2 routes
│   └── services/        # Supabase client
├── database/
│   └── migrations/      # SQL migration files (001–006)
├── frontend/            # React + Leaflet dashboard
└── docs/                # Architecture, API, DB docs
```

## API Versioning

| Version | Base Path  | Status                          |
|---------|------------|---------------------------------|
| V3      | /api/v3/   | Current — production            |
| V2      | /api/      | Legacy — supported              |
| V1      | /          | Legacy — supported              |

## KHAP Platform Integration Endpoints

These endpoints are consumed by other KHAP modules:

| Use Case              | Endpoint                                     |
|-----------------------|----------------------------------------------|
| Find nearest facility | GET /api/v3/routing/nearest-facility         |
| Get road route        | GET /api/v3/routing/route                    |
| Travel time           | GET /api/v3/routing/travel-time              |
| Coverage analysis     | GET /api/v3/analytics/coverage               |
| County analysis       | GET /api/v3/gis/county-analysis              |
| Facility directory    | GET /api/v3/facilities                       |
| Facility detail       | GET /api/v3/facilities/{id}                  |
| National report       | GET /api/v3/reports/national-summary         |
| County report         | GET /api/v3/reports/county-report            |
| Emergency readiness   | GET /api/v3/reports/emergency-readiness      |
