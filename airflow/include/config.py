"""
SismoWatch Central Pipeline Configuration
Loads environment settings with sensible defaults for local and containerized execution.
"""
import os
from typing import Dict, Any

# PostgreSQL Database Configuration
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
DB_NAME = os.getenv("POSTGRES_DB", "sismowatch")
DB_USER = os.getenv("POSTGRES_USER", "sismowatch_admin")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "sismowatch_secure_pass_2026")
DB_APP_USER = os.getenv("POSTGRES_APP_USER", "sismowatch_app")
DB_APP_PASSWORD = os.getenv("POSTGRES_APP_PASSWORD", "sismowatch_app_pass_2026")

DATABASE_URI = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
APP_DATABASE_URI = f"postgresql://{DB_APP_USER}:{DB_APP_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# USGS Endpoints
USGS_REALTIME_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson"
USGS_QUERY_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"

# Ingestion Settings
REQUEST_TIMEOUT_SECONDS = int(os.getenv("USGS_REQUEST_TIMEOUT", "15"))
MAX_RETRIES = int(os.getenv("USGS_MAX_RETRIES", "3"))

# Quality Thresholds
QUALITY_THRESHOLDS = {
    "min_latitude": -90.0,
    "max_latitude": 90.0,
    "min_longitude": -180.0,
    "max_longitude": 180.0,
    "min_magnitude": -2.0,  # Micro-earthquakes can have negative magnitude
    "max_magnitude": 10.0,  # Physically impossible on Earth above 10.0
    "min_depth_km": -5.0,   # High altitude quakes
    "max_depth_km": 800.0,  # Deepest known subduction zones
    "max_future_seconds": 3600, # Max allowable clock skew: 1 hour
    "min_timestamp_year": 1970,
    "min_hourly_volume_anomaly": 0,
    "max_hourly_volume_anomaly": 500,
}

# LLM Configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").lower()
LLM_MODEL = os.getenv("LLM_MODEL", "qwen2.5:0.5b")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://ollama:11434")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.2"))
LLM_TIMEOUT_SECONDS = int(os.getenv("LLM_TIMEOUT_SECONDS", "30"))

# Anomaly Detection Settings
ANOMALY_Z_THRESHOLD = float(os.getenv("ANOMALY_Z_THRESHOLD", "2.5"))
ANOMALY_MIN_BASELINE_HOURS = int(os.getenv("ANOMALY_MIN_BASELINE_HOURS", "24"))
