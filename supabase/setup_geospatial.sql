-- ============================================================
-- KHAP v3 — Complete Geospatial Setup
-- Run this in Supabase SQL Editor (one-time)
-- ============================================================

-- 1. Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 2. Create schemas
CREATE SCHEMA IF NOT EXISTS gis;
CREATE SCHEMA IF NOT EXISTS routing;
CREATE SCHEMA IF NOT EXISTS analytics;

-- 3. Counties table (with centroid points)
CREATE TABLE IF NOT EXISTS gis.counties (
    county_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    county_name VARCHAR(100) UNIQUE NOT NULL,
    latitude    DOUBLE PRECISION,
    longitude   DOUBLE PRECISION,
    geom        geometry(Point, 4326),
    population  INTEGER,
    area_km2    DOUBLE PRECISION,
    created_at  TIMESTAMPTZ DEFAULT now()
);

-- 4. Sub-counties
CREATE TABLE IF NOT EXISTS gis.subcounties (
    subcounty_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    county_id      UUID REFERENCES gis.counties(county_id),
    subcounty_name VARCHAR(100),
    geom           geometry(MultiPolygon, 4326),
    created_at     TIMESTAMPTZ DEFAULT now()
);

-- 5. Wards
CREATE TABLE IF NOT EXISTS gis.wards (
    ward_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subcounty_id UUID REFERENCES gis.subcounties(subcounty_id),
    ward_name    VARCHAR(100),
    geom         geometry(MultiPolygon, 4326),
    created_at   TIMESTAMPTZ DEFAULT now()
);

-- 6. Saved routes (for future user-auth features)
CREATE TABLE IF NOT EXISTS routing.saved_routes (
    id            BIGSERIAL PRIMARY KEY,
    origin_lat    DOUBLE PRECISION,
    origin_lon    DOUBLE PRECISION,
    dest_lat      DOUBLE PRECISION,
    dest_lon      DOUBLE PRECISION,
    distance_km   DOUBLE PRECISION,
    duration_min  DOUBLE PRECISION,
    route_geom    geometry(LineString, 4326),
    created_at    TIMESTAMPTZ DEFAULT now()
);

-- 7. Add geom column to facilities if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'facilities' AND column_name = 'geom'
    ) THEN
        ALTER TABLE public.facilities ADD COLUMN geom geometry(Point, 4326);
    END IF;
END $$;

-- 8. Sync facility geom from lat/lon (run once, then trigger maintains it)
UPDATE public.facilities
SET geom = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
WHERE latitude IS NOT NULL
  AND longitude IS NOT NULL
  AND geom IS NULL;

-- 9. Trigger to keep geom in sync
CREATE OR REPLACE FUNCTION sync_facility_geom()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.latitude IS NOT NULL AND NEW.longitude IS NOT NULL THEN
        NEW.geom := ST_SetSRID(ST_MakePoint(NEW.longitude, NEW.latitude), 4326);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_sync_facility_geom ON public.facilities;
CREATE TRIGGER trg_sync_facility_geom
BEFORE INSERT OR UPDATE OF latitude, longitude
ON public.facilities
FOR EACH ROW EXECUTE FUNCTION sync_facility_geom();

-- 10. Spatial index on facilities
CREATE INDEX IF NOT EXISTS idx_facilities_geom ON public.facilities USING GIST(geom);
CREATE INDEX IF NOT EXISTS idx_counties_geom   ON gis.counties      USING GIST(geom);

-- 11. PostGIS function: nearest facilities within radius
CREATE OR REPLACE FUNCTION public.facilities_within_radius(
    p_lat     DOUBLE PRECISION,
    p_lon     DOUBLE PRECISION,
    p_radius  DOUBLE PRECISION  -- metres
)
RETURNS SETOF public.facilities AS $$
    SELECT *
    FROM public.facilities
    WHERE geom IS NOT NULL
      AND ST_DWithin(
            geom::geography,
            ST_SetSRID(ST_MakePoint(p_lon, p_lat), 4326)::geography,
            p_radius
          )
    ORDER BY geom <-> ST_SetSRID(ST_MakePoint(p_lon, p_lat), 4326)
$$ LANGUAGE SQL STABLE;

-- 12. Seed all 47 Kenya county centroids
INSERT INTO gis.counties (county_name, latitude, longitude, geom) VALUES
('Baringo',          0.8555,  36.0885, ST_SetSRID(ST_MakePoint(36.0885,  0.8555), 4326)),
('Bomet',           -0.7820,  35.3419, ST_SetSRID(ST_MakePoint(35.3419, -0.7820), 4326)),
('Bungoma',          0.5635,  34.5606, ST_SetSRID(ST_MakePoint(34.5606,  0.5635), 4326)),
('Busia',            0.3355,  34.1211, ST_SetSRID(ST_MakePoint(34.1211,  0.3355), 4326)),
('Elgeyo Marakwet',  1.0507,  35.4804, ST_SetSRID(ST_MakePoint(35.4804,  1.0507), 4326)),
('Embu',            -0.5399,  37.4556, ST_SetSRID(ST_MakePoint(37.4556, -0.5399), 4326)),
('Garissa',         -0.4532,  39.6461, ST_SetSRID(ST_MakePoint(39.6461, -0.4532), 4326)),
('Homa Bay',        -0.5273,  34.4571, ST_SetSRID(ST_MakePoint(34.4571, -0.5273), 4326)),
('Isiolo',           0.3540,  38.4792, ST_SetSRID(ST_MakePoint(38.4792,  0.3540), 4326)),
('Kajiado',         -2.0984,  36.7819, ST_SetSRID(ST_MakePoint(36.7819, -2.0984), 4326)),
('Kakamega',         0.2827,  34.7519, ST_SetSRID(ST_MakePoint(34.7519,  0.2827), 4326)),
('Kericho',         -0.3689,  35.2863, ST_SetSRID(ST_MakePoint(35.2863, -0.3689), 4326)),
('Kiambu',          -1.0313,  36.8073, ST_SetSRID(ST_MakePoint(36.8073, -1.0313), 4326)),
('Kilifi',          -3.5108,  39.6480, ST_SetSRID(ST_MakePoint(39.6480, -3.5108), 4326)),
('Kirinyaga',       -0.5590,  37.2697, ST_SetSRID(ST_MakePoint(37.2697, -0.5590), 4326)),
('Kisii',           -0.6812,  34.7660, ST_SetSRID(ST_MakePoint(34.7660, -0.6812), 4326)),
('Kisumu',          -0.1022,  34.7617, ST_SetSRID(ST_MakePoint(34.7617, -0.1022), 4326)),
('Kitui',           -1.3668,  38.0106, ST_SetSRID(ST_MakePoint(38.0106, -1.3668), 4326)),
('Kwale',           -4.1703,  39.4516, ST_SetSRID(ST_MakePoint(39.4516, -4.1703), 4326)),
('Laikipia',         0.3606,  36.7870, ST_SetSRID(ST_MakePoint(36.7870,  0.3606), 4326)),
('Lamu',            -2.2686,  40.9020, ST_SetSRID(ST_MakePoint(40.9020, -2.2686), 4326)),
('Machakos',        -1.5177,  37.2634, ST_SetSRID(ST_MakePoint(37.2634, -1.5177), 4326)),
('Makueni',         -2.2527,  37.6248, ST_SetSRID(ST_MakePoint(37.6248, -2.2527), 4326)),
('Mandera',          3.9366,  41.5627, ST_SetSRID(ST_MakePoint(41.5627,  3.9366), 4326)),
('Marsabit',         2.3284,  37.9962, ST_SetSRID(ST_MakePoint(37.9962,  2.3284), 4326)),
('Meru',             0.0477,  37.6493, ST_SetSRID(ST_MakePoint(37.6493,  0.0477), 4326)),
('Migori',          -1.0634,  34.4731, ST_SetSRID(ST_MakePoint(34.4731, -1.0634), 4326)),
('Mombasa',         -4.0435,  39.6682, ST_SetSRID(ST_MakePoint(39.6682, -4.0435), 4326)),
('Murang''a',       -0.7830,  37.0419, ST_SetSRID(ST_MakePoint(37.0419, -0.7830), 4326)),
('Nairobi',         -1.2921,  36.8219, ST_SetSRID(ST_MakePoint(36.8219, -1.2921), 4326)),
('Nakuru',          -0.3031,  36.0800, ST_SetSRID(ST_MakePoint(36.0800, -0.3031), 4326)),
('Nandi',            0.1836,  35.1236, ST_SetSRID(ST_MakePoint(35.1236,  0.1836), 4326)),
('Narok',           -1.0817,  35.8719, ST_SetSRID(ST_MakePoint(35.8719, -1.0817), 4326)),
('Nyamira',         -0.5669,  34.9349, ST_SetSRID(ST_MakePoint(34.9349, -0.5669), 4326)),
('Nyandarua',       -0.1818,  36.5243, ST_SetSRID(ST_MakePoint(36.5243, -0.1818), 4326)),
('Nyeri',           -0.4166,  36.9517, ST_SetSRID(ST_MakePoint(36.9517, -0.4166), 4326)),
('Samburu',          1.4165,  36.8716, ST_SetSRID(ST_MakePoint(36.8716,  1.4165), 4326)),
('Siaya',            0.0617,  34.2422, ST_SetSRID(ST_MakePoint(34.2422,  0.0617), 4326)),
('Taita Taveta',    -3.3160,  38.3577, ST_SetSRID(ST_MakePoint(38.3577, -3.3160), 4326)),
('Tana River',      -1.5364,  39.5474, ST_SetSRID(ST_MakePoint(39.5474, -1.5364), 4326)),
('Tharaka Nithi',   -0.2956,  37.8968, ST_SetSRID(ST_MakePoint(37.8968, -0.2956), 4326)),
('Trans Nzoia',      1.1176,  34.9500, ST_SetSRID(ST_MakePoint(34.9500,  1.1176), 4326)),
('Turkana',          3.1238,  35.5955, ST_SetSRID(ST_MakePoint(35.5955,  3.1238), 4326)),
('Uasin Gishu',      0.5519,  35.2697, ST_SetSRID(ST_MakePoint(35.2697,  0.5519), 4326)),
('Vihiga',           0.0748,  34.7241, ST_SetSRID(ST_MakePoint(34.7241,  0.0748), 4326)),
('Wajir',            1.7471,  40.0573, ST_SetSRID(ST_MakePoint(40.0573,  1.7471), 4326)),
('West Pokot',       1.6215,  35.3937, ST_SetSRID(ST_MakePoint(35.3937,  1.6215), 4326))
ON CONFLICT (county_name) DO UPDATE
    SET latitude = EXCLUDED.latitude,
        longitude = EXCLUDED.longitude,
        geom = EXCLUDED.geom;

-- Done!
SELECT 'Setup complete. ' || COUNT(*) || ' counties seeded.' AS result FROM gis.counties;
