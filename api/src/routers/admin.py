"""
Admin Operations Router (Admin Only).
Provides endpoints to trigger historical backfills and regenerate daily AI reports.
Strictly enforced on the backend with 403 Forbidden for viewers.
"""
from datetime import datetime, date, timedelta, timezone
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from api.src.auth import require_admin
from airflow.include.usgs_client import USGSClient
from airflow.include.quality import execute_ingestion_and_quality_pipeline
from airflow.include.ai_reporter import build_daily_report

router = APIRouter(prefix="/api/admin", tags=["Admin Operations"])

class BackfillRequest(BaseModel):
    starttime: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)", example="2026-10-01")
    endtime: Optional[str] = Field(None, description="End date (YYYY-MM-DD)", example="2026-10-27")
    minmagnitude: float = Field(2.5, ge=0.0, le=10.0, description="Minimum magnitude filter")

class BackfillResponse(BaseModel):
    message: str
    batch_id: str
    evaluated: int
    passed: int
    quarantined: int
    quality_score: float

class RegenerateReportRequest(BaseModel):
    target_date: Optional[str] = Field(None, description="Target report date (YYYY-MM-DD)", example="2026-10-26")

class RegenerateReportResponse(BaseModel):
    message: str
    report_id: int
    report_date: str
    title: str
    is_fallback: bool
    provider: str

@router.post("/backfill", response_model=BackfillResponse)
def trigger_historical_backfill(
    payload: BackfillRequest,
    current_admin: Dict[str, Any] = Depends(require_admin)
):
    """
    Triggers an idempotent historical backfill from the USGS query endpoint.
    Admin role required. Viewers receive 403 Forbidden.
    """
    default_end = date.today().strftime("%Y-%m-%d")
    default_start = (date.today() - timedelta(days=30)).strftime("%Y-%m-%d")

    start_str = payload.starttime or default_start
    end_str = payload.endtime or default_end

    # Validate date format
    try:
        start_d = datetime.strptime(start_str, "%Y-%m-%d").date()
        end_d = datetime.strptime(end_str, "%Y-%m-%d").date()
        if start_d > end_d:
            raise HTTPException(status_code=400, detail="starttime cannot be after endtime.")
    except ValueError:
        raise HTTPException(status_code=400, detail="Dates must be in valid YYYY-MM-DD format.")

    try:
        client = USGSClient(timeout=45)
        usgs_data = client.fetch_historical_events(
            starttime=start_str,
            endtime=end_str,
            minmagnitude=payload.minmagnitude
        )
        
        metadata = {
            "triggered_by": current_admin["username"],
            "operation": "api_admin_backfill",
            "triggered_at": datetime.now(timezone.utc).isoformat()
        }

        pipeline_result = execute_ingestion_and_quality_pipeline(
            raw_payload=usgs_data,
            feed_url=f"https://earthquake.usgs.gov/fdsnws/event/1/query?starttime={start_str}&endtime={end_str}",
            metadata=metadata
        )

        return BackfillResponse(
            message=f"Historical backfill completed successfully for period {start_str} to {end_str}.",
            batch_id=pipeline_result["batch_id"],
            evaluated=pipeline_result["evaluated"],
            passed=pipeline_result["passed"],
            quarantined=pipeline_result["quarantined"],
            quality_score=pipeline_result["quality_score"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backfill execution failed: {str(e)}")

@router.post("/reports/regenerate", response_model=RegenerateReportResponse)
def trigger_report_regeneration(
    payload: RegenerateReportRequest,
    current_admin: Dict[str, Any] = Depends(require_admin)
):
    """
    Regenerates the daily seismic AI report for a given date.
    Admin role required. Viewers receive 403 Forbidden.
    """
    target_date = None
    if payload.target_date:
        try:
            target_date = datetime.strptime(payload.target_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="target_date must be in YYYY-MM-DD format.")
    else:
        target_date = date.today() - timedelta(days=1)

    try:
        result = build_daily_report(target_date=target_date, force_regenerate=True)
        return RegenerateReportResponse(
            message=f"Report for {result['report_date']} regenerated successfully.",
            report_id=result["report_id"],
            report_date=result["report_date"],
            title=result["title"],
            is_fallback=result["is_fallback"],
            provider=result["provider"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report regeneration failed: {str(e)}")
