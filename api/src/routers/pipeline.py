"""
Pipeline and Data Freshness Status Router.
Provides operational visibility into Airflow executions, quality scores, and anomaly alerts.
"""
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from api.src.database import get_db
from api.src.auth import require_viewer_or_admin

router = APIRouter(prefix="/api/pipeline", tags=["Pipeline"])

class QualityMetricSummary(BaseModel):
    batch_id: str
    evaluated_records: int
    passed_records: int
    rejected_records: int
    quality_score: float
    freshness_seconds: Optional[int]
    created_at: datetime

class AnomalyAlertSummary(BaseModel):
    id: int
    alert_time: datetime
    metric_name: str
    current_value: float
    z_score: float
    severity: str
    explanation: str

class PipelineStatusResponse(BaseModel):
    total_curated_events: int
    total_quarantined_events: int
    latest_quality_score: float
    data_freshness_seconds: Optional[int]
    last_sync_timestamp: Optional[datetime]
    recent_batches: List[QualityMetricSummary]
    recent_anomalies: List[AnomalyAlertSummary]

@router.get("/status", response_model=PipelineStatusResponse)
def get_pipeline_status(current_user: Dict[str, Any] = Depends(require_viewer_or_admin)):
    """Returns real-time pipeline status, data freshness, and quality metrics."""
    with get_db() as conn:
        with conn.cursor() as cur:
            # 1. Total counts
            cur.execute("SELECT COUNT(*) as count, MAX(last_synced_at) as last_sync FROM curated.earthquakes;")
            curated_info = cur.fetchone()

            cur.execute("SELECT COUNT(*) as count FROM curated.quarantine;")
            quarantine_info = cur.fetchone()

            # 2. Recent quality batches
            cur.execute("""
                SELECT 
                    batch_id, evaluated_records, passed_records, rejected_records,
                    quality_score, freshness_seconds, created_at
                FROM curated.quality_metrics
                ORDER BY created_at DESC
                LIMIT 5;
            """)
            batch_rows = cur.fetchall()

            # 3. Recent anomaly alerts
            cur.execute("""
                SELECT 
                    id, alert_time, metric_name, current_value, z_score, severity, explanation
                FROM curated.anomaly_alerts
                ORDER BY alert_time DESC
                LIMIT 5;
            """)
            anomaly_rows = cur.fetchall()

    latest_score = float(batch_rows[0]["quality_score"]) if batch_rows else 100.0
    latest_freshness = batch_rows[0]["freshness_seconds"] if batch_rows else None

    batches = [
        QualityMetricSummary(
            batch_id=b["batch_id"],
            evaluated_records=b["evaluated_records"],
            passed_records=b["passed_records"],
            rejected_records=b["rejected_records"],
            quality_score=float(b["quality_score"]),
            freshness_seconds=b["freshness_seconds"],
            created_at=b["created_at"]
        )
        for b in batch_rows
    ]

    anomalies = [
        AnomalyAlertSummary(
            id=a["id"],
            alert_time=a["alert_time"],
            metric_name=a["metric_name"],
            current_value=float(a["current_value"]),
            z_score=float(a["z_score"]),
            severity=a["severity"],
            explanation=a["explanation"]
        )
        for a in anomaly_rows
    ]

    return PipelineStatusResponse(
        total_curated_events=curated_info["count"] or 0,
        total_quarantined_events=quarantine_info["count"] or 0,
        latest_quality_score=round(latest_score, 2),
        data_freshness_seconds=latest_freshness,
        last_sync_timestamp=curated_info["last_sync"],
        recent_batches=batches,
        recent_anomalies=anomalies
    )
