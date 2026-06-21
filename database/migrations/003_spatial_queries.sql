-- Migration 003: Example PostGIS spatial queries
-- These replace Haversine lookups with native GIS functions once PostGIS is enabled.

-- Find all facilities within 10 km of Nairobi CBD (-1.2921, 36.8219)
SELECT
    facility_id,
    name,
    county,
    type,
    ST_Distance(
        geom,
        ST_SetSRID(ST_MakePoint(36.8219, -1.2921), 4326)::geography
    ) / 1000 AS distance_km
FROM facilities
WHERE ST_DWithin(
    geom,
    ST_SetSRID(ST_MakePoint(36.8219, -1.2921), 4326)::geography,
    10000  -- metres
)
ORDER BY distance_km;


-- Count facilities per county with average distance between them
SELECT
    county,
    COUNT(*) AS facility_count,
    ROUND(
        AVG(
            ST_Distance(geom, centroid_geom)::numeric / 1000
        )::numeric, 2
    ) AS avg_dist_from_centroid_km
FROM facilities,
LATERAL (
    SELECT ST_Centroid(ST_Collect(geom)) AS centroid_geom
    FROM facilities f2
    WHERE f2.county = facilities.county
) sub
WHERE geom IS NOT NULL
GROUP BY county
ORDER BY facility_count DESC;


-- Identify facilities with no neighbour within 15 km (isolated / high load)
SELECT
    a.facility_id,
    a.name,
    a.county,
    COUNT(b.facility_id) AS neighbours_within_15km
FROM facilities a
LEFT JOIN facilities b
    ON a.facility_id != b.facility_id
    AND ST_DWithin(a.geom, b.geom, 15000)
WHERE a.geom IS NOT NULL
GROUP BY a.facility_id, a.name, a.county
HAVING COUNT(b.facility_id) = 0
ORDER BY a.county;
