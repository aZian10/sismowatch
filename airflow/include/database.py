"""
Database helper utilities for SismoWatch.
Handles connection management, raw storage, staging insertion, curated upserts, and quarantine.
"""
import json
import logging
from contextlib import contextmanager
from typing import Generator, List, Dict, Any, Optional
import psycopg2
from psycopg2.extras import RealDictCursor, execute_values

try:
    from include.config import (
        DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD,
        DB_APP_USER, DB_APP_PASSWORD
    )
except ImportError:
    from airflow.include.config import (
        DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD,
        DB_APP_USER, DB_APP_PASSWORD
    )

logger = logging.getLogger("sismowatch.database")

@contextmanager
def get_db_connection(use_app_role: bool = False) -> Generator[psycopg2.extensions.connection, None, None]:
    """Provides a transactional database connection with automatic commit/rollback."""
    user = DB_APP_USER if use_app_role else DB_USER
    password = DB_APP_PASSWORD if use_app_role else DB_PASSWORD
    
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=user,
        password=password,
        cursor_factory=RealDictCursor,
        connect_timeout=10
    )
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Database transaction error: {e}")
        raise
    finally:
        conn.close()

def save_raw_feed(batch_id: str, feed_url: str, status_code: int, payload: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> int:
    """Saves raw USGS API payload into raw.usgs_feed for complete auditability."""
    event_count = len(payload.get("features", [])) if isinstance(payload, dict) else 0
    query = """
        INSERT INTO raw.usgs_feed (batch_id, feed_url, status_code, raw_payload, event_count, execution_metadata)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id;
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (
                batch_id,
                feed_url,
                status_code,
                json.dumps(payload),
                event_count,
                json.dumps(metadata or {})
            ))
            row = cur.fetchone()
            return row["id"]

def insert_staging_records(records: List[Dict[str, Any]]) -> int:
    """Inserts normalized records into staging.earthquakes."""
    if not records:
        return 0
    
    query = """
        INSERT INTO staging.earthquakes (
            batch_id, event_id, mag, place, time_epoch_ms, event_time,
            updated_epoch_ms, updated_time, tsunami, sig, status,
            mag_type, event_type, url, longitude, latitude, depth_km, raw_properties
        ) VALUES %s;
    """
    
    tuples = [
        (
            r["batch_id"],
            r["event_id"],
            r["mag"],
            r["place"],
            r["time_epoch_ms"],
            r["event_time"],
            r["updated_epoch_ms"],
            r["updated_time"],
            r["tsunami"],
            r["sig"],
            r["status"],
            r["mag_type"],
            r["event_type"],
            r["url"],
            r["longitude"],
            r["latitude"],
            r["depth_km"],
            json.dumps(r.get("raw_properties", {}))
        )
        for r in records
    ]
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            execute_values(cur, query, tuples)
            return len(records)

def upsert_curated_records(records: List[Dict[str, Any]]) -> int:
    """
    Idempotent upsert into curated.earthquakes keyed on event_id.
    Updates event if incoming updated_time is newer or equal.
    """
    if not records:
        return 0
    
    query = """
        INSERT INTO curated.earthquakes (
            event_id, mag, place, event_time, updated_time, tsunami, sig,
            status, mag_type, event_type, url, longitude, latitude, depth_km,
            last_synced_at
        ) VALUES %s
        ON CONFLICT (event_id) DO UPDATE SET
            mag = EXCLUDED.mag,
            place = EXCLUDED.place,
            updated_time = EXCLUDED.updated_time,
            tsunami = EXCLUDED.tsunami,
            sig = EXCLUDED.sig,
            status = EXCLUDED.status,
            mag_type = EXCLUDED.mag_type,
            event_type = EXCLUDED.event_type,
            url = EXCLUDED.url,
            longitude = EXCLUDED.longitude,
            latitude = EXCLUDED.latitude,
            depth_km = EXCLUDED.depth_km,
            last_synced_at = NOW()
        WHERE EXCLUDED.updated_time >= curated.earthquakes.updated_time;
    """
    
    tuples = [
        (
            r["event_id"],
            r["mag"],
            r["place"],
            r["event_time"],
            r["updated_time"],
            r["tsunami"],
            r["sig"],
            r["status"],
            r["mag_type"],
            r["event_type"],
            r["url"],
            r["longitude"],
            r["latitude"],
            r["depth_km"],
            r.get("last_synced_at")
        )
        for r in records
    ]
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            execute_values(cur, query, tuples)
            return len(records)

def insert_quarantine_records(quarantined: List[Dict[str, Any]]) -> int:
    """Stores rejected records into curated.quarantine with reasons and failed rules."""
    if not quarantined:
        return 0
    
    query = """
        INSERT INTO curated.quarantine (
            batch_id, event_id, rejection_reasons, failed_rules, raw_record
        ) VALUES %s;
    """
    
    tuples = [
        (
            q["batch_id"],
            q.get("event_id"),
            q["rejection_reasons"],
            q["failed_rules"],
            json.dumps(q.get("raw_record", {}))
        )
        for q in quarantined
    ]
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            execute_values(cur, query, tuples)
            return len(quarantined)

def save_quality_metrics(
    batch_id: str,
    evaluated_records: int,
    passed_records: int,
    rejected_records: int,
    quality_score: float,
    freshness_seconds: Optional[int] = None,
    rules_summary: Optional[Dict[str, Any]] = None
) -> int:
    """Records quality execution metrics."""
    query = """
        INSERT INTO curated.quality_metrics (
            batch_id, evaluated_records, passed_records, rejected_records,
            quality_score, freshness_seconds, rules_summary
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (batch_id) DO UPDATE SET
            evaluated_records = EXCLUDED.evaluated_records,
            passed_records = EXCLUDED.passed_records,
            rejected_records = EXCLUDED.rejected_records,
            quality_score = EXCLUDED.quality_score,
            freshness_seconds = EXCLUDED.freshness_seconds,
            rules_summary = EXCLUDED.rules_summary
        RETURNING id;
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (
                batch_id,
                evaluated_records,
                passed_records,
                rejected_records,
                round(quality_score, 2),
                freshness_seconds,
                json.dumps(rules_summary or {})
            ))
            row = cur.fetchone()
            return row["id"]
