# KHAP V3 Database Schema

## Schemas

| Schema    | Purpose                             |
|-----------|-------------------------------------|
| public    | Core tables (facilities, users, etc)|
| routing   | Road network, intersections, routes |
| analytics | Materialized views, aggregates      |
| etl       | Import tracking                     |

## Running Migrations

Run in order in Supabase SQL Editor:

```
001_enable_postgis.sql          — Enable PostGIS extension
002_add_geometry_columns.sql    — Add geom column to facilities
003_spatial_queries.sql         — Example PostGIS queries
004_data_quality.sql            — Data audit queries
005_v3_schemas.sql              — Full V3 schema setup
006_v3_rls_policies.sql         — Row Level Security
```

## Core Tables

### public.facilities (existing)
| Column             | Type           | Notes                          |
|--------------------|----------------|--------------------------------|
| facility_id        | SERIAL PK      |                                |
| name               | TEXT           |                                |
| county             | TEXT           |                                |
| type               | TEXT           | Facility type                  |
| latitude           | DOUBLE         |                                |
| longitude          | DOUBLE         |                                |
| geom               | GEOGRAPHY      | Auto-synced via trigger        |
| operational_status | TEXT           |                                |
| beds, cots         | INTEGER        |                                |
| open_24_hours      | BOOLEAN        |                                |
| open_weekends      | BOOLEAN        |                                |

### public.api_keys
| Column     | Type        | Notes                          |
|------------|-------------|--------------------------------|
| id         | SERIAL PK   |                                |
| user_id    | UUID FK     | auth.users                     |
| name       | TEXT        | Human-readable key name        |
| key_hash   | TEXT UNIQUE | SHA-256 of raw key             |
| is_active  | BOOLEAN     |                                |
| last_used  | TIMESTAMPTZ |                                |
| created_at | TIMESTAMPTZ |                                |

### routing.road_network
| Column     | Type              | Notes                      |
|------------|-------------------|----------------------------|
| id         | BIGSERIAL PK      |                            |
| osm_id     | BIGINT            | OpenStreetMap way ID       |
| name       | TEXT              |                            |
| highway    | TEXT              | OSM highway classification |
| maxspeed   | INTEGER           | km/h                       |
| geom       | GEOGRAPHY(LINE)   | Spatial index              |
| length_km  | DOUBLE GENERATED  | Auto-computed              |

### routing.saved_routes
| Column          | Type            | Notes                     |
|-----------------|-----------------|---------------------------|
| id              | BIGSERIAL PK    |                           |
| user_id         | UUID FK         | auth.users                |
| origin_lat/lon  | DOUBLE          |                           |
| dest_lat/lon    | DOUBLE          |                           |
| distance_km     | DOUBLE          |                           |
| duration_min    | DOUBLE          |                           |
| route_geom      | GEOGRAPHY(LINE) |                           |
| created_at      | TIMESTAMPTZ     |                           |

## PostGIS Functions

### facilities_within_radius(lat, lon, radius_metres)
Returns facilities within radius using native ST_DWithin — much faster than Haversine on large datasets.

```sql
SELECT * FROM public.facilities_within_radius(-1.2921, 36.8219, 10000);
```

## Materialized Views

### analytics.county_facility_summary
Refreshed after ETL imports:
```sql
REFRESH MATERIALIZED VIEW CONCURRENTLY analytics.county_facility_summary;
```

## Triggers

### trg_sync_facility_geom
Automatically updates `geom` column when `latitude` or `longitude` changes.
