# KHAP — Kenya Health Access Platform

> A geospatial healthcare routing platform built with PostgreSQL, PostGIS, FastAPI, React, and OSRM.

---

## Overview

KHAP helps users discover healthcare facilities across Kenya and calculate the shortest driving routes between them using OpenStreetMap data.

The project combines:

- **PostgreSQL + PostGIS** for storing and querying spatial healthcare data.
- **OSRM** for high-performance road routing.
- **FastAPI** as the backend service layer.
- **React + Leaflet** for the web application.

---

## Architecture

```
                   OpenStreetMap
                         │
          ┌──────────────┴──────────────┐
          │                             │
     PostgreSQL                    OSRM Engine
      + PostGIS                  (Routing Server)
          │                             │
          └──────────────┬──────────────┘
                         │
                      FastAPI
                         │
                      React UI
```

---

## Technology Stack

| Layer            | Technology       |
|------------------|------------------|
| Database         | PostgreSQL 18    |
| Spatial Database | PostGIS 3.6      |
| Routing Engine   | OSRM             |
| Backend          | FastAPI          |
| ORM              | SQLAlchemy       |
| Validation       | Pydantic         |
| Frontend         | React            |
| Mapping          | Leaflet          |
| Routing Data     | OpenStreetMap    |

---

## Project Structure

```
KHAP/
│
├── backend/
│   └── app/
│       ├── api/
│       │   ├── facilities.py    # GET /facilities  /facilities/{id}  /facilities/nearest
│       │   ├── routing.py       # POST /route
│       │   ├── search.py        # GET /search
│       │   └── health.py        # GET /health
│       │
│       ├── database/
│       │   ├── session.py       # SQLAlchemy engine + session + health check
│       │   └── models.py        # HealthFacility, Edge ORM models
│       │
│       ├── schemas/
│       │   ├── facility.py      # FacilityResponse, NearestFacilityResponse
│       │   └── route.py         # RouteRequest, RouteResponse
│       │
│       ├── services/
│       │   ├── facility_service.py   # PostGIS queries
│       │   ├── osrm_service.py       # OSRM HTTP client
│       │   └── routing_service.py    # Orchestrates routing + vertex snapping
│       │
│       ├── core/
│       │   ├── config.py        # DATABASE_URL, OSRM_URL env vars
│       │   └── security.py      # JWT auth (Phase 5 placeholder)
│       │
│       └── main.py              # FastAPI app, routers, CORS
│
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── Map/             # Leaflet map with markers + route polyline
│       │   ├── SearchBar/       # Text + GPS search
│       │   ├── FacilityCard/    # Facility info panel
│       │   └── RouteSummary/    # Distance + duration display
│       │
│       ├── pages/
│       │   ├── Dashboard/       # Main map view
│       │   ├── Facilities/      # Browsable facility list with filters
│       │   └── Routing/         # Facility-to-facility routing
│       │
│       ├── services/
│       │   ├── api.js           # /facilities, /search, /health calls
│       │   └── routing.js       # POST /route
│       │
│       ├── App.jsx              # Page router + nav bar
│       └── main.jsx             # React entry point
│
├── database/
│   └── README.md                # Schema setup (gis + routing schemas)
│
├── osrm/
│   ├── data/                    # Kenya OSM extract + processed OSRM files
│   ├── profiles/                # Lua routing profiles
│   └── README.md                # OSRM setup and Docker commands
│
├── docs/
│
├── .env.example                 # Environment variable template
├── requirements.txt             # Python dependencies
└── README.md                    ← you are here
```

---

## Database

Two schemas in a single PostgreSQL database.

### gis schema — healthcare facilities

```
gis.health_facilities
│
├── id            SERIAL PRIMARY KEY
├── name          TEXT
├── facility_type TEXT
├── operator      TEXT
├── phone         TEXT
├── website       TEXT
├── emergency     TEXT
├── opening_hours TEXT
├── wheelchair    TEXT
├── geom          GEOMETRY(Point, 4326)   ← PostGIS spatial column
└── vertex_id     BIGINT                  ← links to routing graph
```

### routing schema — road network

```
routing.edges                        ← road segments
├── id, source, target
├── cost, reverse_cost
├── highway, way

routing.edges_vertices_pgr           ← graph nodes (intersections)
```

---

## API Endpoints

### Health

```
GET /health
```

### Facilities

```
GET  /facilities                       list all (paginated)
GET  /facilities/{id}                  single facility
GET  /facilities/nearest?lon=&lat=     N nearest by GPS
```

### Search

```
GET  /search?q=&facility_type=&operator=
```

### Routing

```
POST /route
Body: { start_lat, start_lon, end_lat, end_lon }

Response: { distance_m, duration_s, route: [[lon,lat], ...] }
```

---

## Application Workflow

```
User
 ↓
React (Leaflet map + SearchBar)
 ↓
FastAPI (validates request)
 ↓
PostGIS (nearest facility query via ST_Distance / KNN)
 ↓
OSRM (road routing → distance + duration + geometry)
 ↓
JSON response
 ↓
React + Leaflet (draws route polyline on map)
```

---

## Quick Start

### 1. Backend

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your DATABASE_URL and OSRM_URL

# Run the API
cd backend
uvicorn app.main:app --reload --port 8000
```

API docs at: http://localhost:8000/docs

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Dashboard at: http://localhost:5173

### 3. OSRM (local, via Docker)

See `osrm/README.md` for the full setup.  
Quick start with the public demo server (no setup required):

```
OSRM_URL=http://router.project-osrm.org
```

---

## Environment Variables

| Variable       | Description                            | Default                           |
|----------------|----------------------------------------|-----------------------------------|
| `DATABASE_URL` | PostgreSQL connection string           | `postgresql://postgres:...@localhost:5432/khap` |
| `OSRM_URL`     | OSRM routing engine base URL           | `http://router.project-osrm.org`  |

Set `VITE_API_URL` in `frontend/.env.local` if the backend runs on a non-default host.

---

## Development Roadmap

| Phase | Description                         | Status      |
|-------|-------------------------------------|-------------|
| 1     | Database (PostgreSQL + PostGIS)      | ✅ Complete  |
| 2     | Backend (FastAPI + SQLAlchemy)       | ✅ Complete  |
| 3     | Routing (OSRM integration)           | ✅ Complete  |
| 4     | Frontend (React + Leaflet)           | ✅ Complete  |
| 5     | Deployment (Linux + Nginx + HTTPS)   | 🔜 Planned  |

---

## Future Improvements

- Ambulance routing
- Multi-stop routing
- Healthcare accessibility analysis
- Travel-time isochrones
- Emergency response optimization
- Live traffic integration
- Healthcare analytics dashboard

---

## License

MIT License

---

## Author

**Zedrick Kimutai Biwott**  
BSc Applied Statistics & Data Science  
The Co-operative University of Kenya  
Kenya
