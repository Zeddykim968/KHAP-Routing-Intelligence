# KHAP V3 — Local Development Guide

## Prerequisites

- Python 3.12+
- Node.js 18+ (for dashboard)
- A Supabase project with PostGIS enabled

## Setup

### 1. Clone and configure

```bash
git clone <your-repo-url>
cd KHAP-Routing-Intelligence
```

Create `.env` in the project root:
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key
JWT_SECRET_KEY=your-random-secret-at-least-32-chars
JWT_EXPIRE_MINUTES=60
# Optional — Redis for production caching:
# REDIS_URL=redis://localhost:6379
```

### 2. Python environment

```bash
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows

pip install -r requirements.txt
```

### 3. Database setup

Run migrations in order in your Supabase SQL Editor:
```
database/migrations/001_enable_postgis.sql
database/migrations/002_add_geometry_columns.sql
database/migrations/005_v3_schemas.sql
database/migrations/006_v3_rls_policies.sql
```

### 4. Start the API

```bash
uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload
```

API: http://localhost:5000
Docs: http://localhost:5000/docs

### 5. Start the dashboard

```bash
cd frontend
npm install
npm run dev
```

Dashboard: http://localhost:5173

## Testing Endpoints

```bash
# System health
curl http://localhost:5000/health

# Facility stats
curl http://localhost:5000/api/v3/facilities/stats

# Nearest facility with road route
curl "http://localhost:5000/api/v3/routing/nearest-facility?lat=-1.29&lon=36.82&with_route=true"

# Accessibility scores
curl http://localhost:5000/api/v3/analytics/accessibility

# County report
curl "http://localhost:5000/api/v3/reports/county-report?county=Nairobi"

# National summary
curl http://localhost:5000/api/v3/reports/national-summary

# New facility impact
curl "http://localhost:5000/api/v3/analytics/impact?lat=-1.5&lon=37.2"

# Emergency response zones
curl "http://localhost:5000/api/v3/gis/emergency-zones?lat=-1.29&lon=36.82"
```

## Environment Variables Reference

| Variable              | Required | Description                             |
|-----------------------|----------|-----------------------------------------|
| SUPABASE_URL          | Yes      | Your Supabase project URL               |
| SUPABASE_KEY          | Yes      | Anon/public key                         |
| SUPABASE_SERVICE_KEY  | Yes      | Service role key (for admin operations) |
| JWT_SECRET_KEY        | Yes      | Secret for signing JWT tokens           |
| JWT_EXPIRE_MINUTES    | No       | Token TTL, default 60                   |
| REDIS_URL             | No       | Redis URL, falls back to memory cache   |
