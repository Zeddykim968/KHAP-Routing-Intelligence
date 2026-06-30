-- Migration 006: Row Level Security Policies for V3
-- Run AFTER 005_v3_schemas.sql

-- Enable RLS on sensitive tables
ALTER TABLE public.api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE routing.saved_routes ENABLE ROW LEVEL SECURITY;

-- API keys: users can only see their own keys
CREATE POLICY api_keys_owner ON public.api_keys
    USING (user_id = auth.uid());

-- Saved routes: users see only their own
CREATE POLICY saved_routes_owner ON routing.saved_routes
    USING (user_id = auth.uid());

-- Facilities: publicly readable
ALTER TABLE public.facilities ENABLE ROW LEVEL SECURITY;
CREATE POLICY facilities_public_read ON public.facilities
    FOR SELECT USING (TRUE);

-- Import logs: admin only (via service_role key)
ALTER TABLE public.import_logs ENABLE ROW LEVEL SECURITY;
CREATE POLICY import_logs_service_only ON public.import_logs
    USING (auth.role() = 'service_role');

-- Refresh materialized views (run as cron or after ETL)
-- REFRESH MATERIALIZED VIEW CONCURRENTLY analytics.county_facility_summary;
-- REFRESH MATERIALIZED VIEW analytics.facility_type_summary;
