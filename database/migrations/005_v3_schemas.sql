-- Migration 005: V3 Schema Setup
-- Run in Supabase SQL Editor in order.
-- Creates all V3 schemas and core tables.

-- ============================================================
-- SCHEMAS
-- ============================================================
CREATE SCHEMA IF NOT EXISTS users;
CREATE SCHEMA IF NOT EXISTS health;
CREATE SCHEMA IF NOT EXISTS gis;
CREATE SCHEMA IF NOT EXISTS routing;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS etl;

-- ============================================================
-- ROLES TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS public.roles (
    id          SERIAL PRIMARY KEY,
    name        TEXT UNIQUE NOT NULL,  -- 'admin', 'analyst', 'user'
    description TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

INSERT INTO public.roles (name, description) VALUES
    ('admin',   'Full platform access'),
    ('analyst', 'Read + analytics access'),
    ('user',    'Basic facility search')
ON CONFLICT (name) DO NOTHING;

-- ============================================================
-- API KEYS TABLE (for KHAP platform integrations)
-- ============================================================
CREATE TABLE IF NOT EXISTS public.api_keys (
    id         SERIAL PRIMARY KEY,
    user_id    UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    name       TEXT NOT NULL,
    key_hash   TEXT UNIQUE NOT NULL,
    is_active  BOOLEAN DEFAULT TRUE,
    last_used  TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON public.api_keys(key_hash);
CREATE INDEX IF NOT EXISTS idx_api_keys_user ON public.api_keys(user_id);

-- ============================================================
-- COUNTIES TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS public.counties (
    id          SERIAL PRIMARY KEY,
    name        TEXT UNIQUE NOT NULL,
    code        INTEGER,
    region      TEXT,
    area_km2    DOUBLE PRECISION,
    population  INTEGER,
    geom        GEOGRAPHY(MULTIPOLYGON, 4326)
);

CREATE INDEX IF NOT EXISTS idx_counties_geom ON public.counties USING GIST(geom);

-- ============================================================
-- SUB-COUNTIES TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS public.sub_counties (
    id         SERIAL PRIMARY KEY,
    county_id  INTEGER REFERENCES public.counties(id),
    name       TEXT NOT NULL,
    geom       GEOGRAPHY(MULTIPOLYGON, 4326)
);

CREATE INDEX IF NOT EXISTS idx_sub_counties_geom ON public.sub_counties USING GIST(geom);

-- ============================================================
-- WARDS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS public.wards (
    id            SERIAL PRIMARY KEY,
    sub_county_id INTEGER REFERENCES public.sub_counties(id),
    name          TEXT NOT NULL,
    population    INTEGER,
    geom          GEOGRAPHY(MULTIPOLYGON, 4326)
);

CREATE INDEX IF NOT EXISTS idx_wards_geom ON public.wards USING GIST(geom);

-- ============================================================
-- SERVICES TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS public.services (
    id          SERIAL PRIMARY KEY,
    name        TEXT UNIQUE NOT NULL,
    category    TEXT,  -- 'clinical', 'diagnostic', 'support'
    description TEXT
);

-- ============================================================
-- FACILITY SERVICES (many-to-many)
-- ============================================================
CREATE TABLE IF NOT EXISTS public.facility_services (
    facility_id INTEGER NOT NULL,
    service_id  INTEGER REFERENCES public.services(id),
    PRIMARY KEY (facility_id, service_id)
);

-- ============================================================
-- ROAD NETWORK (OSM-derived)
-- ============================================================
CREATE TABLE IF NOT EXISTS routing.road_network (
    id          BIGSERIAL PRIMARY KEY,
    osm_id      BIGINT,
    name        TEXT,
    highway     TEXT,  -- OSM highway tag: primary, secondary, tertiary, etc.
    maxspeed    INTEGER,
    oneway      BOOLEAN DEFAULT FALSE,
    surface     TEXT,
    geom        GEOGRAPHY(LINESTRING, 4326),
    length_km   DOUBLE PRECISION GENERATED ALWAYS AS (ST_Length(geom::geometry) / 1000) STORED
);

CREATE INDEX IF NOT EXISTS idx_road_network_geom ON routing.road_network USING GIST(geom);
CREATE INDEX IF NOT EXISTS idx_road_network_highway ON routing.road_network(highway);

-- ============================================================
-- INTERSECTIONS
-- ============================================================
CREATE TABLE IF NOT EXISTS routing.intersections (
    id   BIGSERIAL PRIMARY KEY,
    geom GEOGRAPHY(POINT, 4326)
);

CREATE INDEX IF NOT EXISTS idx_intersections_geom ON routing.intersections USING GIST(geom);

-- ============================================================
-- SAVED ROUTES
-- ============================================================
CREATE TABLE IF NOT EXISTS routing.saved_routes (
    id              BIGSERIAL PRIMARY KEY,
    user_id         UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    origin_lat      DOUBLE PRECISION,
    origin_lon      DOUBLE PRECISION,
    dest_lat        DOUBLE PRECISION,
    dest_lon        DOUBLE PRECISION,
    distance_km     DOUBLE PRECISION,
    duration_min    DOUBLE PRECISION,
    routing_method  TEXT DEFAULT 'osrm',
    route_geom      GEOGRAPHY(LINESTRING, 4326),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- IMPORT LOGS (ETL audit trail)
-- ============================================================
CREATE TABLE IF NOT EXISTS public.import_logs (
    id              SERIAL PRIMARY KEY,
    stage           TEXT,
    source          TEXT,
    total_records   INTEGER,
    loaded_records  INTEGER,
    error_records   INTEGER,
    imported_at     TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- ANALYTICS: MATERIALIZED VIEWS
-- ============================================================

-- County facility summary (refresh daily)
CREATE MATERIALIZED VIEW IF NOT EXISTS analytics.county_facility_summary AS
SELECT
    county,
    COUNT(*)                                                AS total_facilities,
    COUNT(*) FILTER (WHERE operational_status = 'Operational') AS operational,
    COUNT(*) FILTER (WHERE open_24_hours = TRUE)           AS open_24h,
    SUM(COALESCE(beds, 0) + COALESCE(cots, 0))             AS total_beds_cots,
    AVG(COALESCE(beds, 0) + COALESCE(cots, 0))             AS avg_beds_cots
FROM public.facilities
GROUP BY county
ORDER BY total_facilities DESC;

CREATE UNIQUE INDEX IF NOT EXISTS idx_county_facility_summary
    ON analytics.county_facility_summary(county);

-- Facility type distribution
CREATE MATERIALIZED VIEW IF NOT EXISTS analytics.facility_type_summary AS
SELECT
    type,
    COUNT(*)                                                AS total,
    COUNT(*) FILTER (WHERE operational_status = 'Operational') AS operational
FROM public.facilities
GROUP BY type
ORDER BY total DESC;

-- ============================================================
-- TRIGGER: update facilities.geom on lat/lon change
-- ============================================================
CREATE OR REPLACE FUNCTION public.sync_facility_geom()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.latitude IS NOT NULL AND NEW.longitude IS NOT NULL THEN
        NEW.geom := ST_SetSRID(ST_MakePoint(NEW.longitude, NEW.latitude), 4326)::geography;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_sync_facility_geom ON public.facilities;
CREATE TRIGGER trg_sync_facility_geom
    BEFORE INSERT OR UPDATE OF latitude, longitude
    ON public.facilities
    FOR EACH ROW EXECUTE FUNCTION public.sync_facility_geom();

-- ============================================================
-- DATABASE FUNCTION: facilities within radius (PostGIS)
-- ============================================================
CREATE OR REPLACE FUNCTION public.facilities_within_radius(
    p_lat    DOUBLE PRECISION,
    p_lon    DOUBLE PRECISION,
    p_radius DOUBLE PRECISION  -- in metres
)
RETURNS TABLE (
    facility_id       INTEGER,
    name              TEXT,
    county            TEXT,
    type              TEXT,
    latitude          DOUBLE PRECISION,
    longitude         DOUBLE PRECISION,
    distance_m        DOUBLE PRECISION
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        f.facility_id,
        f.name,
        f.county,
        f.type,
        f.latitude,
        f.longitude,
        ST_Distance(f.geom, ST_SetSRID(ST_MakePoint(p_lon, p_lat), 4326)::geography) AS distance_m
    FROM public.facilities f
    WHERE f.geom IS NOT NULL
      AND ST_DWithin(f.geom, ST_SetSRID(ST_MakePoint(p_lon, p_lat), 4326)::geography, p_radius)
    ORDER BY distance_m;
END;
$$ LANGUAGE plpgsql STABLE;
