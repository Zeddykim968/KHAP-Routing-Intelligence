# Database

PostgreSQL 18 + PostGIS 3.6

## Schemas

### gis

Healthcare facility data imported from OpenStreetMap.

```sql
CREATE SCHEMA gis;

CREATE TABLE gis.health_facilities (
    id            SERIAL PRIMARY KEY,
    name          TEXT,
    facility_type TEXT,
    operator      TEXT,
    phone         TEXT,
    website       TEXT,
    emergency     TEXT,
    opening_hours TEXT,
    wheelchair    TEXT,
    geom          GEOMETRY(Point, 4326),
    vertex_id     BIGINT
);

-- Spatial index for fast KNN / distance queries
CREATE INDEX idx_health_facilities_geom
    ON gis.health_facilities USING GIST (geom);
```

### routing

Road network imported via `osm2pgrouting` for pgRouting support.

```sql
CREATE SCHEMA routing;

-- edges and edges_vertices_pgr are created automatically by osm2pgrouting:
--   osm2pgrouting -f kenya.osm -c mapconfig.xml -d khap -U postgres
```

Key tables:
- `routing.edges` — road segments with source/target/cost/reverse_cost
- `routing.edges_vertices_pgr` — graph vertices (intersections)

## Setup

1. Create the database and enable extensions:

```sql
CREATE DATABASE khap;
\c khap
CREATE EXTENSION postgis;
CREATE EXTENSION pgrouting;
```

2. Create the `gis` schema and import facilities from OpenStreetMap.

3. Import the Kenya OSM road network with `osm2pgrouting` into the `routing` schema.

4. Set `DATABASE_URL` in `.env`:

```
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/khap
```
