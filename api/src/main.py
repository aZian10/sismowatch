"""
SismoWatch FastAPI Main Application.
Configures CORS, registers modular routers, and seeds default RBAC users on startup.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.src.config import (
    CORS_ORIGINS,
    ADMIN_USERNAME,
    ADMIN_PASSWORD,
    ADMIN_EMAIL,
    ADMIN_FULL_NAME,
    VIEWER_USERNAME,
    VIEWER_PASSWORD,
    VIEWER_EMAIL,
    VIEWER_FULL_NAME
)
from api.src.database import get_db
from api.src.auth import get_password_hash
from api.src.routers import (
    auth,
    kpis,
    events,
    stats,
    reports,
    stream,
    pipeline,
    quality,
    admin
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sismowatch.api")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup initialization: auto-provision seed admin and viewer accounts if missing."""
    logger.info("Initializing SismoWatch API...")
    try:
        with get_db(admin=True) as conn:
            with conn.cursor() as cur:
                # Seed admin user
                cur.execute("""
                    INSERT INTO curated.users (username, email, password_hash, role, full_name, is_active)
                    VALUES (%s, %s, %s, 'admin', %s, TRUE)
                    ON CONFLICT (username) DO NOTHING;
                """, (
                    ADMIN_USERNAME,
                    ADMIN_EMAIL,
                    get_password_hash(ADMIN_PASSWORD),
                    ADMIN_FULL_NAME
                ))

                # Seed viewer user
                cur.execute("""
                    INSERT INTO curated.users (username, email, password_hash, role, full_name, is_active)
                    VALUES (%s, %s, %s, 'viewer', %s, TRUE)
                    ON CONFLICT (username) DO NOTHING;
                """, (
                    VIEWER_USERNAME,
                    VIEWER_EMAIL,
                    get_password_hash(VIEWER_PASSWORD),
                    VIEWER_FULL_NAME
                ))
        logger.info("Seed users verified/provisioned successfully.")
    except Exception as e:
        logger.warning(f"Could not provision seed users on startup (db may not be ready yet): {e}")

    yield
    logger.info("SismoWatch API shutting down.")

app = FastAPI(
    title="SismoWatch API",
    description="Real-time earthquake monitoring, data quality, anomaly detection, and AI reporting API.",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router)
app.include_router(kpis.router)
app.include_router(events.router)
app.include_router(stats.router)
app.include_router(reports.router)
app.include_router(stream.router)
app.include_router(pipeline.router)
app.include_router(quality.router)
app.include_router(admin.router)

@app.get("/health", tags=["Health"])
def health_check():
    """Service health probe."""
    return {"status": "healthy", "service": "sismowatch-api"}
