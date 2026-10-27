"""
FastAPI Backend Configuration.
Reads environment variables for database, JWT secrets, seeds, and CORS.
"""
import os
from typing import List

# Database
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
DB_NAME = os.getenv("POSTGRES_DB", "sismowatch")
# Backend uses least-privilege role by default
DB_APP_USER = os.getenv("POSTGRES_APP_USER", "sismowatch_app")
DB_APP_PASSWORD = os.getenv("POSTGRES_APP_PASSWORD", "sismowatch_app_pass_2026")
# Admin user for admin-specific tasks if needed
DB_ADMIN_USER = os.getenv("POSTGRES_USER", "sismowatch_admin")
DB_ADMIN_PASSWORD = os.getenv("POSTGRES_PASSWORD", "sismowatch_secure_pass_2026")

DATABASE_URL = f"postgresql://{DB_APP_USER}:{DB_APP_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
ADMIN_DATABASE_URL = f"postgresql://{DB_ADMIN_USER}:{DB_ADMIN_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# JWT & Authentication
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "sismowatch_jwt_super_secret_signing_key_change_in_production_2026")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "480"))

# Seed Users (Provisioned on startup)
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "AdminSecure2026!")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@sismowatch.internal")
ADMIN_FULL_NAME = os.getenv("ADMIN_FULL_NAME", "System Administrator")

VIEWER_USERNAME = os.getenv("VIEWER_USERNAME", "viewer")
VIEWER_PASSWORD = os.getenv("VIEWER_PASSWORD", "ViewerSecure2026!")
VIEWER_EMAIL = os.getenv("VIEWER_EMAIL", "viewer@sismowatch.internal")
VIEWER_FULL_NAME = os.getenv("VIEWER_FULL_NAME", "Risk Analyst Viewer")

# CORS Origins
raw_cors = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173")
CORS_ORIGINS: List[str] = [origin.strip() for origin in raw_cors.split(",") if origin.strip()]

# Airflow Integration
AIRFLOW_URL = os.getenv("AIRFLOW_URL", "http://airflow-webserver:8080")
