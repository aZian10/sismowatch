"""
KPIs Router.
Delivers executive operational metrics computed strictly from curated schema.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime, timedelta, timezone

from api.src.database import get_db
from api.src.auth import require_viewer_or_admin

router = APIRouter(prefix="/api/kpis", tags=["KPIs"])

class KPIResponse(BaseModel):
    total_events_24h: int
    max_magnitude_24h: float
    avg_magnitude_24h: float
    tsunami_events_24h: int
    data_quality_score: float
    last_updated_at: Optional[datetime]
    active_anomalies_24h: int

@router.get("", response_model=KPIResponse)
def get_kpis(current_user: Dict[str, Any] = Depends(require_viewer_or_admin)):
    """Computes headline KPIs for the previous 24 hours."""
    since_ts = datetime.now(timezone.utc) - timedelta(hours=24)
    
    with get_db() as conn:
        with conn.cursor() as cur:
            # 1. 24h Seismicity metrics
            cur.execute("""
                SELECT 
                    COUNT(*) as total_events,
                    COALESCE(MAX(mag), 0.0) as max_mag,
                    COALESCE(AVG(mag), 0.0) as avg_mag,
                    COUNT(*) FILTER (WHERE tsunami > 0) as tsunami_count,
                    MAX(last_synced_at) as last_sync
                FROM curated.earthquakes
                WHERE event_time >= %s;
            """, (since_ts,))
            stats = cur.fetchone()

            # 2. Latest quality score
            cur.execute("""
                SELECT quality_score
                FROM curated.quality_metrics
                ORDER BY created_at DESC
                LIMIT 1;
            """)
            quality_row = cur.fetchone()
            quality_score = float(quality_row["quality_score"]) if quality_row else 100.0

            # 3. Anomaly count in last 24h
            cur.execute("""
                SELECT COUNT(*) as alert_count
                FROM curated.anomaly_alerts
                WHERE alert_time >= %s;
            """, (since_ts,))
            alert_row = cur.fetchone()
            alert_count = alert_row["alert_count"] if alert_row else 0

    return KPIResponse(
        total_events_24h=int(stats["total_events"] or 0),
        max_magnitude_24h=round(float(stats["max_mag"] or 0.0), 2),
        avg_magnitude_24h=round(float(stats["avg_mag"] or 0.0), 2),
        tsunami_events_24h=int(stats["tsunami_count"] or 0),
        data_quality_score=round(quality_score, 2),
        last_updated_at=stats["last_sync"],
        active_anomalies_24h=int(alert_count or 0)
    )
