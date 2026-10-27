-- ==============================================================================
-- 01_schemas.sql: Create 3 separated layers for SismoWatch
-- raw: Original payloads and metadata
-- staging: Normalized and typed records
-- curated: Analytics, reports, quality metrics, alerts, and users
-- ==============================================================================

CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS curated;

COMMENT ON SCHEMA raw IS 'Preserves untouched API responses and ingestion traceability';
COMMENT ON SCHEMA staging IS 'Contains normalized, parsed, and typed records prior to validation';
COMMENT ON SCHEMA curated IS 'Stores validated, deduplicated, query-ready analytical records';
