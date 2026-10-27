"""
Seismic Analytics and Statistics Router.
Aggregates hourly time series, magnitude distributions, and regional concentrations.
"""
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from typing import Dict, Any, List
from datetime import datetime, timedelta, timezone

from api.src.database import get_db
from api.src.auth import require_viewer_or_admin

router = APIRouter(prefix="/api/stats", tags=["Stats"])

class HourlyBucket(BaseModel):
    hour: str
    count: int
    avg_mag: float

class MagBucket(BaseModel):
    bucket: str
    count: int

class RegionCount(BaseModel):
    region: str
    count: int
    avg_mag: float

class TimeseriesStatsResponse(BaseModel):
    hourly: List[HourlyBucket]
    magnitude_distribution: List[MagBucket]
    top_regions: List[RegionCount]

@router.get("/timeseries", response_model=TimeseriesStatsResponse)
def get_timeseries_stats(
    hours: int = Query(24, ge=1, le=168, description="Time window in hours"),
    current_user: Dict[str, Any] = Depends(require_viewer_or_admin)
):
    """Computes hourly activity, magnitude distributions, and top regions."""
    since_ts = datetime.now(timezone.utc) - timedelta(hours=hours)

    with get_db() as conn:
        with conn.cursor() as cur:
            # 1. Hourly aggregation
            cur.execute("""
                SELECT 
                    to_char(date_trunc('hour', event_time), 'YYYY-MM-DD"T"HH24:00:00"Z"') as hour_str,
                    COUNT(*) as count,
                    COALESCE(ROUND(AVG(mag), 2), 0.0) as avg_mag
                FROM curated.earthquakes
                WHERE event_time >= %s
                GROUP BY date_trunc('hour', event_time)
                ORDER BY date_trunc('hour', event_time) ASC;
            """, (since_ts,))
            hourly_rows = cur.fetchall()

            # 2. Magnitude distribution
            cur.execute("""
                SELECT 
                    CASE 
                        WHEN mag < 2.0 THEN '< 2.0'
                        WHEN mag >= 2.0 AND mag < 4.0 THEN '2.0 - 3.9'
                        WHEN mag >= 4.0 AND mag < 6.0 THEN '4.0 - 5.9'
                        ELSE '6.0+'
                    END as bucket,
                    COUNT(*) as count
                FROM curated.earthquakes
                WHERE event_time >= %s
                GROUP BY 1
                ORDER BY 1;
            """, (since_ts,))
            mag_rows = cur.fetchall()

            # 3. Top regions
            cur.execute("""
                SELECT 
                    CASE 
                        WHEN place LIKE '%% of %%' THEN SPLIT_PART(place, ' of ', 2)
                        WHEN place LIKE '%%, %%' THEN SPLIT_PART(place, ', ', 2)
                        ELSE place
                    END AS region,
                    COUNT(*) as count,
                    ROUND(AVG(mag), 2) as avg_mag
                FROM curated.earthquakes
                WHERE event_time >= %s
                GROUP BY 1
                ORDER BY count DESC
                LIMIT 5;
            """, (since_ts,))
            region_rows = cur.fetchall()

    hourly = [
        HourlyBucket(hour=r["hour_str"], count=r["count"], avg_mag=float(r["avg_mag"]))
        for r in hourly_rows
    ]

    mag_dist = [
        MagBucket(bucket=r["bucket"], count=r["count"])
        for r in mag_rows
    ]

    top_regions = [
        RegionCount(region=r["region"], count=r["count"], avg_mag=float(r["avg_mag"]))
        for r in region_rows
    ]

    return TimeseriesStatsResponse(
        hourly=hourly,
        magnitude_distribution=mag_dist,
        top_regions=top_regions
    )
