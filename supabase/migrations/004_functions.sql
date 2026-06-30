-- Find nearest health facility

CREATE OR REPLACE FUNCTION nearest_facility(
    lon DOUBLE PRECISION,
    lat DOUBLE PRECISION
)

RETURNS TABLE (

facility_name TEXT,

distance_km DOUBLE PRECISION

)

AS $$

SELECT

facility_name,

ST_Distance(
location::geography,
ST_SetSRID(ST_MakePoint(lon,lat),4326)::geography
)/1000

FROM health_facilities

ORDER BY location <-> ST_SetSRID(ST_MakePoint(lon,lat),4326)

LIMIT 1;

$$

LANGUAGE SQL;