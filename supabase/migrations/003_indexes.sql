CREATE INDEX idx_county_geom
ON counties
USING GIST(geom);

CREATE INDEX idx_subcounty_geom
ON subcounties
USING GIST(geom);

CREATE INDEX idx_ward_geom
ON wards
USING GIST(geom);

CREATE INDEX idx_facility_location
ON health_facilities
USING GIST(location);

CREATE INDEX idx_road_geom
ON roads
USING GIST(geometry);

CREATE INDEX idx_patient_location
ON patients
USING GIST(location);

CREATE INDEX idx_ambulance_location
ON ambulances
USING GIST(current_location);

CREATE INDEX idx_route_geom
ON routing_history
USING GIST(route);