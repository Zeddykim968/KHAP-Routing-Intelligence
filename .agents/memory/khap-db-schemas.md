---
name: KHAP database schemas
description: PostgreSQL schema layout for gis.health_facilities and routing.edges; connection requires DATABASE_URL env var.
---

## Schemas

### gis.health_facilities

Facilities from OpenStreetMap.

Columns: id, name, facility_type, operator, phone, website, emergency, opening_hours, wheelchair, geom (GEOMETRY Point 4326), vertex_id (BIGINT → routing graph)

### routing.edges

Road network from osm2pgrouting.

Columns: id, source, target, cost, reverse_cost, highway, way (GEOMETRY LineString 4326)

### routing.edges_vertices_pgr

Graph nodes created by osm2pgrouting. Column `the_geom` holds the vertex point geometry.

## Connection

Set `DATABASE_URL=postgresql://user:pass@host:5432/khap` in `.env`.

From Replit, the user's local PostgreSQL is unreachable unless exposed via a tunnel (ngrok, Cloudflare Tunnel, etc.) or hosted on a cloud provider (Neon, Railway, etc.).

**Why:** The old Supabase service key approach is fully removed. All queries now go through SQLAlchemy raw SQL using PostGIS functions (ST_Distance, ST_MakePoint, KNN <->).
