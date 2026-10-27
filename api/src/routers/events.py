"""
Events Query Router.
Provides filtered, paginated access to curated earthquake records with parameterized queries.
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime
from psycopg2 import sql

from api.src.database import get_db
from api.src.auth import require_viewer_or_admin

router = APIRouter(prefix="/api/events", tags=["Events"])

class EarthquakeItem(BaseModel):
    event_id: str
    mag: float
    place: str
    event_time: datetime
    updated_time: datetime
    tsunami: int
    sig: int
    status: str
    mag_type: Optional[str]
    event_type: str
    url: Optional[str]
    longitude: float
    latitude: float
    depth_km: float

class PaginatedEventsResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: List[EarthquakeItem]

@router.get("", response_model=PaginatedEventsResponse)
def list_events(
    min_mag: Optional[float] = Query(None, description="Minimum magnitude threshold"),
    max_mag: Optional[float] = Query(None, description="Maximum magnitude threshold"),
    region: Optional[str] = Query(None, description="Substring search on place"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD or ISO timestamp)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD or ISO timestamp)"),
    tsunami_only: bool = Query(False, description="Filter only events with tsunami flag"),
    limit: int = Query(100, ge=1, le=1000, description="Items per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    current_user: Dict[str, Any] = Depends(require_viewer_or_admin)
):
    """Retrieves curated earthquake events matching filter criteria."""
    conditions = [sql.SQL("TRUE")]
    params: List[Any] = []

    if min_mag is not None:
        conditions.append(sql.SQL("mag >= %s"))
        params.append(min_mag)

    if max_mag is not None:
        conditions.append(sql.SQL("mag <= %s"))
        params.append(max_mag)

    if region:
        conditions.append(sql.SQL("place ILIKE %s"))
        params.append(f"%{region}%")

    if start_date:
        conditions.append(sql.SQL("event_time >= %s"))
        params.append(start_date)

    if end_date:
        conditions.append(sql.SQL("event_time <= %s"))
        params.append(end_date)

    if tsunami_only:
        conditions.append(sql.SQL("tsunami > 0"))

    where_sql = sql.SQL(" AND ").join(conditions)

    count_query = sql.SQL("SELECT COUNT(*) as total FROM curated.earthquakes WHERE {}").format(where_sql)
    data_query = sql.SQL("""
        SELECT 
            event_id, mag, place, event_time, updated_time, tsunami, sig,
            status, mag_type, event_type, url, longitude, latitude, depth_km
        FROM curated.earthquakes
        WHERE {}
        ORDER BY event_time DESC
        LIMIT %s OFFSET %s
    """).format(where_sql)

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(count_query, params)
            total = cur.fetchone()["total"]

            cur.execute(data_query, params + [limit, offset])
            rows = cur.fetchall()

    items = [
        EarthquakeItem(
            event_id=r["event_id"],
            mag=float(r["mag"]),
            place=r["place"],
            event_time=r["event_time"],
            updated_time=r["updated_time"],
            tsunami=int(r["tsunami"]),
            sig=int(r["sig"]),
            status=r["status"],
            mag_type=r["mag_type"],
            event_type=r["event_type"],
            url=r["url"],
            longitude=float(r["longitude"]),
            latitude=float(r["latitude"]),
            depth_km=float(r["depth_km"])
        )
        for r in rows
    ]

    return PaginatedEventsResponse(
        total=total,
        limit=limit,
        offset=offset,
        items=items
    )

@router.get("/{event_id}", response_model=EarthquakeItem)
def get_event_by_id(event_id: str, current_user: Dict[str, Any] = Depends(require_viewer_or_admin)):
    """Retrieves a single earthquake event by its unique USGS ID."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    event_id, mag, place, event_time, updated_time, tsunami, sig,
                    status, mag_type, event_type, url, longitude, latitude, depth_km
                FROM curated.earthquakes
                WHERE event_id = %s;
            """, (event_id,))
            row = cur.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail=f"Earthquake event '{event_id}' not found.")

    return EarthquakeItem(
        event_id=row["event_id"],
        mag=float(row["mag"]),
        place=row["place"],
        event_time=row["event_time"],
        updated_time=row["updated_time"],
        tsunami=int(row["tsunami"]),
        sig=int(row["sig"]),
        status=row["status"],
        mag_type=row["mag_type"],
        event_type=row["event_type"],
        url=row["url"],
        longitude=float(row["longitude"]),
        latitude=float(row["latitude"]),
        depth_km=float(row["depth_km"])
    )
