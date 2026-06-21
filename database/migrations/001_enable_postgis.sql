-- Migration 001: Enable PostGIS extension in Supabase
-- Run this in the Supabase SQL Editor (Dashboard → SQL Editor)

-- Step 1: Enable PostGIS
CREATE EXTENSION IF NOT EXISTS postgis;

-- Step 2: Verify installation
SELECT postgis_version();
