-- ==============================================================================
-- 03_roles_permissions.sql: Least-privilege database roles
-- ==============================================================================

DO $$
BEGIN
    -- Create application role if it doesn't exist
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'sismowatch_app') THEN
        CREATE ROLE sismowatch_app WITH LOGIN PASSWORD 'sismowatch_app_pass_2026';
    END IF;
END
$$;

-- Grant usage only on curated schema to the application role
GRANT USAGE ON SCHEMA curated TO sismowatch_app;

-- Revoke all permissions on raw and staging schemas from application role
REVOKE ALL ON SCHEMA raw FROM sismowatch_app;
REVOKE ALL ON SCHEMA staging FROM sismowatch_app;

-- Application role can read curated tables
GRANT SELECT ON curated.earthquakes TO sismowatch_app;
GRANT SELECT ON curated.quarantine TO sismowatch_app;
GRANT SELECT ON curated.quality_metrics TO sismowatch_app;
GRANT SELECT ON curated.daily_reports TO sismowatch_app;
GRANT SELECT ON curated.anomaly_alerts TO sismowatch_app;
GRANT SELECT ON curated.ai_execution_metadata TO sismowatch_app;
GRANT SELECT, INSERT, UPDATE ON curated.users TO sismowatch_app;
GRANT SELECT, INSERT, UPDATE ON curated.daily_reports TO sismowatch_app;
GRANT SELECT, INSERT ON curated.ai_execution_metadata TO sismowatch_app;

-- Sequences usage
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA curated TO sismowatch_app;
