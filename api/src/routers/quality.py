"""
Data Quality and Quarantine Router (Admin Only).
Allows administrators to inspect records rejected by quality validation and their failure reasons.
"""
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from api.src.database import get_db
from api.src.auth import require_admin

router = APIRouter(prefix="/api/quality", tags=["Quality"])

class QuarantineItem(BaseModel):
    id: int
    batch_id: str
    event_id: Optional[str]
    rejection_reasons: List[str]
    failed_rules: List[str]
    raw_record: Dict[str, Any]
    quarantined_at: datetime

class PaginatedQuarantineResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: List[QuarantineItem]

@router.get("/quarantine", response_model=PaginatedQuarantineResponse)
def list_quarantine_records(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_admin: Dict[str, Any] = Depends(require_admin)
):
    """
    Retrieves quarantined records that failed quality control.
    Strictly restricted to users with 'admin' role. Viewers receive 403 Forbidden.
    """
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) as total FROM curated.quarantine;")
            total = cur.fetchone()["total"]

            cur.execute("""
                SELECT id, batch_id, event_id, rejection_reasons, failed_rules, raw_record, quarantined_at
                FROM curated.quarantine
                ORDER BY quarantined_at DESC
                LIMIT %s OFFSET %s;
            """, (limit, offset))
            rows = cur.fetchall()

    items = [
        QuarantineItem(
            id=r["id"],
            batch_id=r["batch_id"],
            event_id=r["event_id"],
            rejection_reasons=r["rejection_reasons"],
            failed_rules=r["failed_rules"],
            raw_record=r["raw_record"] if isinstance(r["raw_record"], dict) else {},
            quarantined_at=r["quarantined_at"]
        )
        for r in rows
    ]

    return PaginatedQuarantineResponse(total=total, limit=limit, offset=offset, items=items)
