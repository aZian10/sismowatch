-- ==============================================================================
-- 02_tables.sql: Tables and constraints for raw, staging, and curated layers
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 1. RAW SCHEMA: Preserves immutable raw responses from USGS API
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS raw.usgs_feed (
    id SERIAL PRIMARY KEY,
    batch_id VARCHAR(64) NOT NULL,
    feed_url TEXT NOT NULL,
    status_code INT NOT NULL DEFAULT 200,
    raw_payload JSONB NOT NULL,
    event_count INT NOT NULL DEFAULT 0,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    execution_metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_raw_batch_id ON raw.usgs_feed(batch_id);
CREATE INDEX IF NOT EXISTS idx_raw_ingested_at ON raw.usgs_feed(ingested_at DESC);

-- ------------------------------------------------------------------------------
-- 2. STAGING SCHEMA: Normalized data ready for quality evaluation
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS staging.earthquakes (
    id SERIAL PRIMARY KEY,
    batch_id VARCHAR(64) NOT NULL,
    event_id VARCHAR(64) NOT NULL,
    mag NUMERIC(5,2),
    place TEXT,
    time_epoch_ms BIGINT,
    event_time TIMESTAMPTZ,
    updated_epoch_ms BIGINT,
    updated_time TIMESTAMPTZ,
    tsunami INT,
    sig INT,
    status VARCHAR(32),
    mag_type VARCHAR(16),
    event_type VARCHAR(32),
    url TEXT,
    longitude NUMERIC(10,5),
    latitude NUMERIC(10,5),
    depth_km NUMERIC(10,3),
    raw_properties JSONB,
    staged_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_staging_batch_id ON staging.earthquakes(batch_id);
CREATE INDEX IF NOT EXISTS idx_staging_event_id ON staging.earthquakes(event_id);

-- ------------------------------------------------------------------------------
-- 3. CURATED SCHEMA: Validated analytical store & platform tables
-- ------------------------------------------------------------------------------

-- Validated earthquake events
CREATE TABLE IF NOT EXISTS curated.earthquakes (
    event_id VARCHAR(64) PRIMARY KEY,
    mag NUMERIC(5,2) NOT NULL,
    place TEXT NOT NULL,
    event_time TIMESTAMPTZ NOT NULL,
    updated_time TIMESTAMPTZ NOT NULL,
    tsunami INT NOT NULL DEFAULT 0,
    sig INT NOT NULL DEFAULT 0,
    status VARCHAR(32) NOT NULL,
    mag_type VARCHAR(16),
    event_type VARCHAR(32) NOT NULL,
    url TEXT,
    longitude NUMERIC(10,5) NOT NULL,
    latitude NUMERIC(10,5) NOT NULL,
    depth_km NUMERIC(10,3) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_synced_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_curated_event_time ON curated.earthquakes(event_time DESC);
CREATE INDEX IF NOT EXISTS idx_curated_mag ON curated.earthquakes(mag DESC);
CREATE INDEX IF NOT EXISTS idx_curated_coords ON curated.earthquakes(latitude, longitude);
CREATE INDEX IF NOT EXISTS idx_curated_tsunami ON curated.earthquakes(tsunami) WHERE tsunami > 0;

-- Quarantined records that failed quality validation
CREATE TABLE IF NOT EXISTS curated.quarantine (
    id SERIAL PRIMARY KEY,
    batch_id VARCHAR(64) NOT NULL,
    event_id VARCHAR(64),
    rejection_reasons TEXT[] NOT NULL,
    failed_rules TEXT[] NOT NULL,
    raw_record JSONB NOT NULL,
    quarantined_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_quarantine_batch_id ON curated.quarantine(batch_id);
CREATE INDEX IF NOT EXISTS idx_quarantine_quarantined_at ON curated.quarantine(quarantined_at DESC);

-- Quality validation execution metrics
CREATE TABLE IF NOT EXISTS curated.quality_metrics (
    id SERIAL PRIMARY KEY,
    batch_id VARCHAR(64) NOT NULL UNIQUE,
    evaluated_records INT NOT NULL,
    passed_records INT NOT NULL,
    rejected_records INT NOT NULL,
    quality_score NUMERIC(5,2) NOT NULL,
    freshness_seconds INT,
    rules_summary JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_quality_metrics_created_at ON curated.quality_metrics(created_at DESC);

-- Daily AI narrative reports
CREATE TABLE IF NOT EXISTS curated.daily_reports (
    id SERIAL PRIMARY KEY,
    report_date DATE NOT NULL UNIQUE,
    title TEXT NOT NULL,
    executive_summary TEXT NOT NULL,
    stats_json JSONB NOT NULL,
    narrative_report TEXT NOT NULL,
    provider VARCHAR(64) NOT NULL,
    model VARCHAR(64) NOT NULL,
    latency_ms INT DEFAULT 0,
    tokens_used INT DEFAULT 0,
    cost_estimate NUMERIC(8,5) DEFAULT 0.0,
    is_fallback BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_daily_reports_date ON curated.daily_reports(report_date DESC);

-- Anomaly detection alerts
CREATE TABLE IF NOT EXISTS curated.anomaly_alerts (
    id SERIAL PRIMARY KEY,
    alert_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metric_name VARCHAR(64) NOT NULL,
    current_value NUMERIC(10,3) NOT NULL,
    baseline_mean NUMERIC(10,3) NOT NULL,
    baseline_std NUMERIC(10,3) NOT NULL,
    z_score NUMERIC(8,3) NOT NULL,
    threshold NUMERIC(8,3) NOT NULL,
    severity VARCHAR(16) NOT NULL,
    explanation TEXT NOT NULL,
    is_seismic_threat BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_anomaly_alerts_time ON curated.anomaly_alerts(alert_time DESC);

-- AI Execution Traceability & Metadata
CREATE TABLE IF NOT EXISTS curated.ai_execution_metadata (
    id SERIAL PRIMARY KEY,
    execution_id VARCHAR(64) NOT NULL,
    task_name VARCHAR(64) NOT NULL,
    provider VARCHAR(64) NOT NULL,
    model VARCHAR(64) NOT NULL,
    latency_ms INT NOT NULL,
    input_tokens INT DEFAULT 0,
    output_tokens INT DEFAULT 0,
    cost_usd NUMERIC(8,5) DEFAULT 0.0,
    status VARCHAR(32) NOT NULL,
    prompt_version VARCHAR(32) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ai_exec_created_at ON curated.ai_execution_metadata(created_at DESC);

-- Application Users and RBAC
CREATE TABLE IF NOT EXISTS curated.users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(64) NOT NULL UNIQUE,
    email VARCHAR(128) NOT NULL UNIQUE,
    password_hash VARCHAR(256) NOT NULL,
    role VARCHAR(16) NOT NULL CHECK (role IN ('admin', 'viewer')),
    full_name VARCHAR(128),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_username ON curated.users(username);
