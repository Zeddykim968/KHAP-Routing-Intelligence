# KHAP V3 API Reference

Full interactive docs: `GET /docs` (Swagger) or `GET /redoc`

## Authentication

### JWT Bearer Token
```
Authorization: Bearer <token>
```

### API Key
```
X-API-Key: khap_<key>
```

---

## Auth Module — /api/v3/auth

| Method | Path              | Auth     | Description              |
|--------|-------------------|----------|--------------------------|
| POST   | /login            | None     | Get JWT token            |
| POST   | /register         | None     | Create account           |
| GET    | /me               | JWT      | Current user profile     |
| POST   | /api-keys         | JWT      | Generate API key         |
| DELETE | /api-keys/{name}  | JWT      | Revoke API key           |

---

## Facilities — /api/v3/facilities

| Method | Path          | Auth | Description                   |
|--------|---------------|------|-------------------------------|
| GET    | /             | None | List with filter + pagination |
| GET    | /counties     | None | All county names              |
| GET    | /types        | None | All facility types            |
| GET    | /stats        | None | Aggregate statistics          |
| GET    | /{id}         | None | Single facility detail        |

**Query parameters (list):**
- `county` — filter by county name
- `type` — filter by facility type
- `operational_only` — default true
- `limit` — max 2000, default 500
- `offset` — pagination offset

---

## Routing — /api/v3/routing

| Method | Path               | Auth | Description                    |
|--------|--------------------|------|--------------------------------|
| GET    | /nearest-facility  | None | Nearest facilities with routes |
| GET    | /route             | None | Road geometry (GeoJSON)        |
| GET    | /travel-time       | None | Duration + distance            |
| GET    | /driving-routes    | None | Full route with geometry       |

**nearest-facility parameters:**
- `lat`, `lon` — required
- `facility_type` — optional filter
- `radius_km` — default 50
- `limit` — 1–20, default 5
- `with_route` — include geometry, default false

---

## Analytics — /api/v3/analytics

| Method | Path              | Auth | Description                  |
|--------|-------------------|------|------------------------------|
| GET    | /accessibility    | None | County accessibility scores  |
| GET    | /coverage         | None | Coverage bands from a point  |
| GET    | /facility-load    | None | Facility load pressure       |
| GET    | /gap-analysis     | None | Coverage gaps                |
| GET    | /impact           | None | New facility impact estimate |
| GET    | /county-rankings  | None | All counties ranked          |

**Accessibility score formula:**
```
Score = 40% Travel Time + 30% Facility Density + 20% Coverage + 10% Facility Level
```

**Score bands:**
- 80–100: Excellent
- 60–80: Good
- 40–60: Moderate
- 20–40: Poor
- 0–20: Critical

---

## GIS — /api/v3/gis

| Method | Path               | Auth | Description                   |
|--------|--------------------|------|-------------------------------|
| GET    | /buffer            | None | GeoJSON circle buffer         |
| GET    | /catchment         | None | Catchment area analysis       |
| GET    | /nearest           | None | Nearest with bearing          |
| GET    | /network-analysis  | None | Kenya-wide network metrics    |
| GET    | /emergency-zones   | None | Response time classification  |
| GET    | /county-analysis   | None | Full county spatial profile   |

---

## Reports — /api/v3/reports

| Method | Path                  | Auth | Description                |
|--------|-----------------------|------|----------------------------|
| GET    | /national-summary     | None | Kenya-wide report          |
| GET    | /county-report        | None | Single county deep report  |
| GET    | /emergency-readiness  | None | County readiness rankings  |

---

## Admin — /api/v3/admin

| Method | Path            | Auth  | Description          |
|--------|-----------------|-------|----------------------|
| GET    | /health         | None  | System health check  |
| POST   | /etl/validate   | Admin | Validate records     |
| POST   | /etl/import     | Admin | Import facilities    |
| GET    | /etl/logs       | Admin | Import audit trail   |
| DELETE | /cache          | Admin | Flush cache          |
| GET    | /stats          | Admin | Platform statistics  |

---

## Rate Limits

| Endpoint Class    | Limit        |
|-------------------|--------------|
| Public endpoints  | 60 req/min   |
| Analytics         | 30 req/min   |
| Authenticated     | 300 req/min  |
| Login             | 10 req/min   |
| Register          | 5 req/min    |
