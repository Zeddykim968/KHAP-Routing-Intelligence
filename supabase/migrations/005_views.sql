CREATE VIEW facility_summary AS

SELECT
    
facility_name,

facility_type,

ownership,

county_name

FROM health_facilities hf

JOIN counties c

ON hf.county_id = c.county_id;