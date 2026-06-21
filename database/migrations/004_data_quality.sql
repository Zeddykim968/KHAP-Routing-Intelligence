-- Migration 004: Data quality audit queries
-- Run these to identify issues in the facilities dataset before analysis.

-- 1. Facilities missing coordinates
SELECT COUNT(*) AS missing_coordinates
FROM facilities
WHERE latitude IS NULL OR longitude IS NULL;

-- 2. Duplicate facility names within the same county
SELECT name, county, COUNT(*) AS duplicates
FROM facilities
GROUP BY name, county
HAVING COUNT(*) > 1
ORDER BY duplicates DESC;

-- 3. Facilities with coordinates outside Kenya bounding box
-- Kenya: lat -4.7 to 4.6, lon 34.0 to 42.0
SELECT facility_id, name, county, latitude, longitude
FROM facilities
WHERE latitude  NOT BETWEEN -4.7 AND 4.6
   OR longitude NOT BETWEEN 34.0 AND 42.0;

-- 4. Facilities with zero beds and zero cots (capacity unknown)
SELECT COUNT(*) AS no_capacity_data
FROM facilities
WHERE (beds IS NULL OR beds = 0)
  AND (cots IS NULL OR cots = 0);

-- 5. Operational status summary
SELECT operational_status, COUNT(*) AS count
FROM facilities
GROUP BY operational_status
ORDER BY count DESC;

-- 6. Facility type distribution
SELECT type, COUNT(*) AS count
FROM facilities
GROUP BY type
ORDER BY count DESC;
