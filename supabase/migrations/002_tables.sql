-- Counties

CREATE TABLE gis.counties (

    county_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    county_name VARCHAR(100) UNIQUE NOT NULL,

    geom geometry(MultiPolygon,4326)

);

-----------------------------------------------------

-- Sub Counties

CREATE TABLE gis.subcounties (

    subcounty_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    county_id UUID REFERENCES gis.counties(county_id),

    subcounty_name VARCHAR(100),

    geom geometry(MultiPolygon,4326)

);

-----------------------------------------------------

-- Wards

CREATE TABLE gis.wards (

    ward_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    subcounty_id UUID REFERENCES gis.subcounties(subcounty_id),

    ward_name VARCHAR(100),

    geom geometry(MultiPolygon,4326)

);

-----------------------------------------------------

-- Health Facilities

CREATE TABLE health_facilities (

    facility_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    facility_name TEXT NOT NULL,

    county_id UUID REFERENCES gis.counties(county_id),

    ward_id UUID REFERENCES gis.wards(ward_id),

    ownership VARCHAR(50),

    facility_type VARCHAR(100),

    level INTEGER,

    phone TEXT,

    email TEXT,

    latitude DOUBLE PRECISION,

    longitude DOUBLE PRECISION,

    location geometry(Point,4326),

    created_at TIMESTAMP DEFAULT NOW()

);

-----------------------------------------------------

-- Roads

CREATE TABLE gis.roads (

    road_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    road_name TEXT,

    road_class VARCHAR(50),

    surface VARCHAR(50),

    speed_limit INTEGER,

    one_way BOOLEAN DEFAULT FALSE,

    length_km DOUBLE PRECISION,

    geometry geometry(LineString,4326)

);

-----------------------------------------------------

-- Ambulances

CREATE TABLE gis.ambulances (

    ambulance_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    registration_number VARCHAR(20) UNIQUE,

    facility_id UUID REFERENCES health_facilities(facility_id),

    status VARCHAR(30),

    driver_name TEXT,

    phone TEXT,

    current_location geometry(Point,4326),

    updated_at TIMESTAMP DEFAULT NOW()

);

-----------------------------------------------------

-- Patients

CREATE TABLE patients (

    patient_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    patient_name TEXT,

    age INTEGER,

    gender VARCHAR(10),

    emergency_level INTEGER,

    location geometry(Point,4326),

    created_at TIMESTAMP DEFAULT NOW()

);

-----------------------------------------------------

-- Routing History

CREATE TABLE routing_history (

    route_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    ambulance_id UUID REFERENCES ambulances(ambulance_id),

    patient_id UUID REFERENCES patients(patient_id),

    facility_id UUID REFERENCES health_facilities(facility_id),

    distance_km DOUBLE PRECISION,

    estimated_minutes DOUBLE PRECISION,

    route geometry(LineString,4326),

    created_at TIMESTAMP DEFAULT NOW()

);