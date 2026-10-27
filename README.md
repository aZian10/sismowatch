# SismoWatch — AI & Data Engineering Platform

**SismoWatch** is a containerized, resilient data platform that ingests real-time and historical earthquake event feeds from the United States Geological Survey (USGS) public API, enforces multi-layer Pandera data quality rules, isolates invalid records in quarantine, detects statistical seismic anomalies, generates executive AI-driven narrative reports with deterministic fallbacks, and serves insights via an RBAC-protected FastAPI backend and React frontend.

---

## Architecture Overview

```
USGS Earthquake Feed
         │
         ▼
Apache Airflow DAGs (Ingestion, Transformation, Daily Reports, Backfills)
         │
         ▼
PostgreSQL Multi-Tier Schemas:
 ├── raw.usgs_feed           (Untouched API responses, execution metadata)
 ├── staging.earthquakes     (Normalized, parsed timestamps, coordinate types)
 ├── curated.quarantine      (Rejected records & detailed rejection reasons)
 ├── curated.quality_metrics (Execution audit scores & freshness lag)
 ├── curated.earthquakes     (Deduplicated, idempotent analytical store)
 ├── curated.daily_reports   (Executive AI & deterministic fallback reports)
 ├── curated.anomaly_alerts  (Z-Score volume and magnitude anomalies)
 └── curated.users           (Bcrypt-hashed credentials, RBAC admin/viewer)
         │
         ▼
FastAPI Backend (JWT Authentication, RBAC, REST, Server-Sent Events /api/stream)
         │
         ▼
React + TypeScript + Vite Web Dashboard (Dark Theme, Interactive Map, Live Updates)
```

For detailed component descriptions, schema models, and technical trade-offs, see [`docs/ARQUITECTURA.md`](docs/ARQUITECTURA.md).

---

## Prerequisites

- **Docker Engine** (v24.0+) & **Docker Compose** (v2.20+)
- **Python** 3.11+ (for local test execution or development)
- **Node.js** v18+ and **npm** (for local frontend development)
- At least 4 GB of available system RAM for local Docker execution

---

## Quick Start (Docker Compose)

### 1. Clone & Configure Environment

Clone the repository and copy the environment template:

```bash
cp .env.example .env
```

Review `.env` parameters if needed (database credentials, JWT secret, Fernet key, LLM configuration). Default values are pre-configured for instant local execution.

### 2. Build and Start Services

Launch the full stack in detached mode:

```bash
docker compose up -d
```

### 3. Verify Container Health

Check that all services are healthy and running:

```bash
docker compose ps
```

The system initializes automatically:
1. `postgres` creates schemas (`raw`, `staging`, `curated`), tables, roles, and default users via `/docker-entrypoint-initdb.d`.
2. `airflow-init` runs database migrations and creates the Airflow admin user.
3. `airflow-scheduler` and `airflow-webserver` start orchestration.
4. `api` starts FastAPI on port 8000.
5. `web` starts the React interface via Nginx on port 5173.

---

## Access Endpoints & Default Credentials

| Service | URL | Role / User | Password (from `.env`) |
|---|---|---|---|
| **Web Application** | [http://localhost:5173](http://localhost:5173) | `admin` | `AdminSecure2026!` |
| **Web Application** | [http://localhost:5173](http://localhost:5173) | `viewer` | `ViewerSecure2026!` |
| **FastAPI Interactive Docs** | [http://localhost:8000/docs](http://localhost:8000/docs) | Bearer Token | Authenticate via `/auth/login` |
| **FastAPI OpenAPI Schema** | [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json) | Public | — |
| **Airflow Web UI** | [http://localhost:8080](http://localhost:8080) | `admin` | `admin_sismowatch_2026` |

> [!NOTE]
> The login screen includes **Quick-Fill** buttons for both `admin` and `viewer` accounts for ease of evaluation.

---

## Airflow Orchestration DAGs

1. **`sismowatch_ingestion_dag`**:
   - Schedule: `*/5 * * * *` (Every 5 minutes)
   - Fetches the USGS real-time GeoJSON feed.
   - Saves the untouched payload in `raw.usgs_feed`.
   - Triggers `sismowatch_transformation_dag`.
2. **`sismowatch_transformation_dag`**:
   - Runs validation rules (coordinate boundaries, depth limits, plausible magnitudes, schema constraints).
   - Quarantines invalid records with rejection reasons into `curated.quarantine`.
   - Idempotently upserts valid records into `curated.earthquakes`.
   - Computes and records batch quality score into `curated.quality_metrics`.
   - Computes statistical anomaly alerts (Z-Score on hourly volume and average magnitude).
3. **`sismowatch_daily_report_dag`**:
   - Schedule: `0 1 * * *` (Daily at 01:00 UTC)
   - Computes verified ground-truth figures directly from SQL.
   - Produces structured Pydantic report using the configured LLM or deterministic fallback engine.
4. **`sismowatch_backfill_dag`**:
   - Schedule: `None` (Admin on-demand / API triggered)
   - Queries historical USGS catalog for custom date ranges and minimum magnitude filters.

---

## Running Automated Tests

Run the complete test suite with a single command using `pytest`:

```bash
# In your virtual environment with dependencies installed:
pytest -v
```

### Test Suite Coverage
- **Transformations**: `test_parse_valid_geojson_feature`, `test_parse_feature_with_missing_coordinates`
- **Data Quality**: Coordinate bounds, physical magnitude limits, micro-earthquake handling, depth plausibility, future clock skew, missing ID detection.
- **Idempotence**: Verifies repeated ingestion of the same event updates without duplicating.
- **Quarantine**: Verifies corrupt records are strictly blocked from reaching curated.
- **Airflow DAG Integrity**: Verifies all 4 DAG files import with 0 errors.
- **API Authentication**: Login success, bad password rejection, unauthenticated endpoint protection.
- **RBAC Authorization**: Proves viewers receive `403 Forbidden` on admin endpoints (`/api/quality/quarantine`, `/api/admin/backfill`, `/api/admin/reports/regenerate`).
- **AI Report Fallback**: Confirms deterministic generator works reliably without external API access.

---

## Running Security Scans

The project has been scanned using **Bandit**:

```bash
bandit -r airflow/include api/src -ll
```

### Actual Scan Results
```text
Run started: 2026-10-27 12:46:50+00:00
Test results: No issues identified.
Code scanned: 2,133 lines of code.
Total issues: Medium: 0, High: 0.
Total lines skipped (#nosec): 0.
```

---

## Capturing UI Screenshots

To capture screenshots of the platform for submission:
1. Open [http://localhost:5173](http://localhost:5173) and sign in as `admin`.
2. **Dashboard**: Navigate to Dashboard showing KPI cards, global map, hourly activity chart, and filtered earthquake records. Capture screenshot as `docs/screenshots/dashboard.png`.
3. **AI Reports**: Navigate to AI Reports view showing historical report catalog and detailed executive summary. Capture as `docs/screenshots/reports.png`.
4. **Live Stream**: Open Live Feed view showing real-time green connection pulse and incoming stream events. Capture as `docs/screenshots/live_feed.png`.
5. **Airflow UI**: Open [http://localhost:8080](http://localhost:8080) showing all 4 DAGs enabled with successful execution runs. Capture as `docs/screenshots/airflow_dags.png`.

---

## Creating the Delivery ZIP Package

To create the clean submission archive excluding `.env`, virtual environments, and `node_modules`:

```bash
zip -r sismowatch_delivery.zip . \
  -x "*.git*" \
  -x "*.env" \
  -x "*node_modules*" \
  -x "*.venv*" \
  -x "*__pycache__*" \
  -x "*.pytest_cache*" \
  -x "*dist*"
```

---

## Known Limitations & Production Roadmap

1. **Airflow Scale**: Currently configured with `LocalExecutor` on a single container. In enterprise production, migrate to `KubernetesExecutor` on AWS EKS or GCP GKE.
2. **Geospatial Storage**: Coordinates are currently stored as numeric lat/lon. Adding PostGIS spatial indexing (`ST_Point`) will unlock sub-millisecond polygon containment queries.
3. **Push-Notification Tier**: Add WebSocket or webhook integration to notify third-party operations systems when critical anomaly alerts occur.
