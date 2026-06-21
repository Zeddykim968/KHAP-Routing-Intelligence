-- Migration 002: Add spatial geometry column to health_facilities table
-- Run AFTER 001_enable_postgis.sql

-- Step 1: Add geography column (uses WGS84 / EPSG:4326)
ALTER TABLE facilities
ADD COLUMN IF NOT EXISTS geom GEOGRAPHY(POINT, 4326);

-- Step 2: Populate geometry from existing lat/lon columns
UPDATE facilities
SET geom = ST_SetSRID(
    ST_MakePoint(longitude, latitude),
    4326
)::geography
WHERE latitude IS NOT NULL
  AND longitude IS NOT NULL;

-- Step 3: Create spatial index for fast proximity queries
CREATE INDEX IF NOT EXISTS idx_facilities_geom
ON facilities USING GIST (geom);

-- Step 4: Verify — count facilities with valid geometry
SELECT COUNT(*) AS facilities_with_geometry
FROM facilities
WHERE geom IS NOT NULL;
