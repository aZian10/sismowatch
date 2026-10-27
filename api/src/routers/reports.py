"""
Reports Router.
Provides query, pagination, and multi-format export (CSV, HTML) for daily AI reports.
"""
import io
import csv
from datetime import date, datetime
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, Response
from pydantic import BaseModel

from api.src.database import get_db
from api.src.auth import require_viewer_or_admin

router = APIRouter(prefix="/api/reports", tags=["Reports"])

class DailyReportItem(BaseModel):
    id: int
    report_date: date
    title: str
    executive_summary: str
    narrative_report: str
    stats_json: Dict[str, Any]
    provider: str
    model: str
    latency_ms: Optional[int]
    is_fallback: bool
    created_at: datetime

class PaginatedReportsResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: List[DailyReportItem]

@router.get("", response_model=PaginatedReportsResponse)
def list_reports(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: Dict[str, Any] = Depends(require_viewer_or_admin)
):
    """Retrieves paginated historical daily reports."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) as total FROM curated.daily_reports;")
            total = cur.fetchone()["total"]

            cur.execute("""
                SELECT 
                    id, report_date, title, executive_summary, narrative_report,
                    stats_json, provider, model, latency_ms, is_fallback, created_at
                FROM curated.daily_reports
                ORDER BY report_date DESC
                LIMIT %s OFFSET %s;
            """, (limit, offset))
            rows = cur.fetchall()

    items = [
        DailyReportItem(
            id=r["id"],
            report_date=r["report_date"],
            title=r["title"],
            executive_summary=r["executive_summary"],
            narrative_report=r["narrative_report"],
            stats_json=r["stats_json"] if isinstance(r["stats_json"], dict) else {},
            provider=r["provider"],
            model=r["model"],
            latency_ms=r["latency_ms"],
            is_fallback=r["is_fallback"],
            created_at=r["created_at"]
        )
        for r in rows
    ]

    return PaginatedReportsResponse(total=total, limit=limit, offset=offset, items=items)

@router.get("/export")
def export_reports(
    format: str = Query("csv", regex="^(csv|html)$"),
    current_user: Dict[str, Any] = Depends(require_viewer_or_admin)
):
    """Exports all available daily reports into CSV or clean printable HTML."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    report_date, title, executive_summary, narrative_report,
                    provider, model, is_fallback, created_at
                FROM curated.daily_reports
                ORDER BY report_date DESC;
            """)
            rows = cur.fetchall()

    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Report Date", "Title", "Executive Summary", "Narrative Report", "Provider", "Model", "Is Fallback", "Created At"])
        for r in rows:
            writer.writerow([
                r["report_date"],
                r["title"],
                r["executive_summary"],
                r["narrative_report"],
                r["provider"],
                r["model"],
                r["is_fallback"],
                r["created_at"].isoformat() if r["created_at"] else ""
            ])
        csv_content = output.getvalue()
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=sismowatch_reports.csv"}
        )

    elif format == "html":
        html_cards = "".join([
            f"""
            <div style="margin-bottom: 24px; padding: 16px; border: 1px solid #334155; border-radius: 8px; background-color: #0f172a; color: #f8fafc;">
                <h2 style="color: #38bdf8; margin-top: 0;">{r['title']}</h2>
                <p><strong>Date:</strong> {r['report_date']} | <strong>Engine:</strong> {r['provider']} ({r['model']}) | <strong>Fallback:</strong> {r['is_fallback']}</p>
                <div style="background-color: #1e293b; padding: 12px; border-radius: 6px; margin: 12px 0;">
                    <strong>Executive Summary:</strong> {r['executive_summary']}
                </div>
                <div>
                    <strong>Detailed Analysis:</strong>
                    <p style="white-space: pre-line;">{r['narrative_report']}</p>
                </div>
            </div>
            """
            for r in rows
        ])
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>SismoWatch Reports Export</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #020617; color: #f8fafc; padding: 24px; }}
            </style>
        </head>
        <body>
            <h1 style="color: #60a5fa;">SismoWatch Daily Executive Seismic Reports</h1>
            <p>Generated export on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            {html_cards}
        </body>
        </html>
        """
        return Response(content=full_html, media_type="text/html")
