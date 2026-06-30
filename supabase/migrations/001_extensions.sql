-- Migration 001: Enable PostGIS extension in Supabase
-- Run this in the Supabase SQL Editor (Dashboard → SQL Editor)

-- Enable UUID extension for generating unique identifiers
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";


-- Enable PostGIS
CREATE EXTENSION IF NOT EXISTS postgis;

-- Enable cryptographic functions for PostGIS
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Step 2: Enable PostGIS Topology (optional, only if needed)
CREATE EXTENSION IF NOT EXISTS postgis_topology;
