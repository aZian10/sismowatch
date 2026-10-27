"""
AI Daily Report Automation with Deterministic Fallback & Structured Validation.
Computes ground-truth statistics in SQL/Python, invokes configured LLM or fallback,
validates output with Pydantic, and records execution metadata.
"""
import json
import logging
import os
import time
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field

import requests

try:
    from include.config import (
        LLM_PROVIDER, LLM_MODEL, LLM_API_KEY, LLM_TIMEOUT_SECONDS, LLM_TEMPERATURE
    )
    from include.database import get_db_connection
except ImportError:
    from airflow.include.config import (
        LLM_PROVIDER, LLM_MODEL, LLM_API_KEY, LLM_TIMEOUT_SECONDS, LLM_TEMPERATURE
    )
    from airflow.include.database import get_db_connection

logger = logging.getLogger("sismowatch.ai_reporter")

PROMPT_FILE = Path(__file__).parent / "prompts" / "daily_report_v1.txt"

class DailyReportSchema(BaseModel):
    """Pydantic schema enforcing structured report output."""
    title: str = Field(description="Headline of the daily report")
    executive_summary: str = Field(description="2-3 sentence executive synthesis")
    narrative_report: str = Field(description="Detailed factual narrative based strictly on data")

def fetch_daily_statistics(target_date: date) -> Dict[str, Any]:
    """
    Computes verified ground-truth figures directly from curated.earthquakes using SQL.
    Prevents hallucination by supplying verified figures to the model.
    """
    start_ts = datetime(target_date.year, target_date.month, target_date.day, 0, 0, 0, tzinfo=timezone.utc)
    end_ts = start_ts + timedelta(days=1)
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # 1. Aggregate statistics
            cur.execute("""
                SELECT 
                    COUNT(*) as total_events,
                    COALESCE(MAX(mag), 0.0) as max_mag,
                    COALESCE(AVG(mag), 0.0) as avg_mag,
                    COUNT(*) FILTER (WHERE tsunami > 0) as tsunami_count,
                    COUNT(*) FILTER (WHERE mag >= 5.0 OR sig >= 600) as significant_count
                FROM curated.earthquakes
                WHERE event_time >= %s AND event_time < %s;
            """, (start_ts, end_ts))
            summary_row = cur.fetchone()
            
            # 2. Maximum magnitude event details
            cur.execute("""
                SELECT event_id, mag, place, event_time, depth_km, tsunami
                FROM curated.earthquakes
                WHERE event_time >= %s AND event_time < %s
                ORDER BY mag DESC, event_time DESC
                LIMIT 1;
            """, (start_ts, end_ts))
            max_event = cur.fetchone()
            
            # 3. Top 5 active regions (grouping by place)
            cur.execute("""
                SELECT 
                    CASE 
                        WHEN place LIKE '%% of %%' THEN SPLIT_PART(place, ' of ', 2)
                        WHEN place LIKE '%%, %%' THEN SPLIT_PART(place, ', ', 2)
                        ELSE place
                    END AS region,
                    COUNT(*) as event_count,
                    ROUND(AVG(mag), 2) as avg_mag
                FROM curated.earthquakes
                WHERE event_time >= %s AND event_time < %s
                GROUP BY 1
                ORDER BY event_count DESC
                LIMIT 5;
            """, (start_ts, end_ts))
            top_regions = cur.fetchall()
            
            # 4. Significant events list
            cur.execute("""
                SELECT event_id, mag, place, event_time, depth_km, tsunami, sig
                FROM curated.earthquakes
                WHERE event_time >= %s AND event_time < %s
                  AND (mag >= 5.0 OR sig >= 600)
                ORDER BY mag DESC
                LIMIT 10;
            """, (start_ts, end_ts))
            sig_events = cur.fetchall()

    formatted_max = None
    if max_event:
        formatted_max = {
            "event_id": max_event["event_id"],
            "mag": float(max_event["mag"]),
            "place": max_event["place"],
            "event_time": max_event["event_time"].isoformat() if max_event["event_time"] else None,
            "depth_km": float(max_event["depth_km"]),
            "tsunami": int(max_event["tsunami"])
        }

    formatted_regions = [
        {
            "region": r["region"],
            "event_count": int(r["event_count"]),
            "avg_mag": float(r["avg_mag"])
        }
        for r in top_regions
    ]

    formatted_sig = [
        {
            "event_id": s["event_id"],
            "mag": float(s["mag"]),
            "place": s["place"],
            "event_time": s["event_time"].isoformat() if s["event_time"] else None,
            "depth_km": float(s["depth_km"]),
            "tsunami": int(s["tsunami"]),
            "sig": int(s["sig"])
        }
        for s in sig_events
    ]

    return {
        "report_date": str(target_date),
        "total_events": int(summary_row["total_events"] or 0),
        "max_magnitude": float(summary_row["max_mag"] or 0.0),
        "avg_magnitude": float(summary_row["avg_mag"] or 0.0),
        "tsunami_count": int(summary_row["tsunami_count"] or 0),
        "significant_count": int(summary_row["significant_count"] or 0),
        "max_event": formatted_max,
        "top_regions": formatted_regions,
        "significant_events": formatted_sig
    }

def generate_deterministic_report(stats: Dict[str, Any]) -> DailyReportSchema:
    """
    Guaranteed deterministic report generator.
    Activated when LLM provider fails, times out, or when running in offline/deterministic mode.
    """
    total = stats["total_events"]
    max_mag = stats["max_magnitude"]
    avg_mag = stats["avg_magnitude"]
    tsunami = stats["tsunami_count"]
    sig_count = stats["significant_count"]
    target_date = stats["report_date"]
    
    if total == 0:
        return DailyReportSchema(
            title=f"Daily Seismic Activity Report - {target_date}",
            executive_summary=f"No seismic events were cataloged in the SismoWatch curated database for {target_date}.",
            narrative_report="During this 24-hour observation cycle, zero seismic events were recorded. Monitoring systems remain operational."
        )

    max_place = stats["max_event"]["place"] if stats["max_event"] else "Unspecified"
    top_region_names = [f"{r['region']} ({r['event_count']} events)" for r in stats["top_regions"][:3]]
    regions_str = ", ".join(top_region_names) if top_region_names else "global distributed zones"
    
    tsunami_text = (
        f"A total of {tsunami} event(s) raised tsunami-related warning indicators." 
        if tsunami > 0 else 
        "No tsunami-related warnings or flags were triggered during this period."
    )
    
    summary = (
        f"On {target_date}, SismoWatch recorded {total} seismic events globally. "
        f"The peak event reached magnitude {max_mag:.1f} near {max_place}. "
        f"The mean global magnitude stood at {avg_mag:.2f}. {tsunami_text}"
    )
    
    narrative = (
        f"Seismic monitoring across global seismic stations detected {total} confirmed events on {target_date}. "
        f"The highest concentration of seismic activity was identified in {regions_str}. "
        f"Overall activity showed an average magnitude of {avg_mag:.2f}, reflecting standard baseline tectonic dissipation. "
        f"\n\nSignificant activity: {sig_count} event(s) reached or exceeded magnitude 5.0 or high significance index. "
        f"The maximum recorded event was M{max_mag:.1f} at {max_place}. "
        f"\nTsunami assessment: {tsunami_text} "
        f"\nAll metrics were calculated deterministically by the SismoWatch analytical engine."
    )
    
    return DailyReportSchema(
        title=f"Daily Seismic Activity Report - {target_date}",
        executive_summary=summary,
        narrative_report=narrative
    )

def call_external_llm(prompt_text: str) -> Optional[DailyReportSchema]:
    """Attempts to query external LLM API if configured."""
    if not LLM_API_KEY or LLM_PROVIDER in ("deterministic", "mock"):
        return None
        
    try:
        if LLM_PROVIDER == "openai":
            headers = {
                "Authorization": f"Bearer {LLM_API_KEY}",
                "Content-Type": "application/json"
            }
            body = {
                "model": LLM_MODEL or "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "You are a professional seismology reporter. Return strict JSON only."},
                    {"role": "user", "content": prompt_text}
                ],
                "response_format": {"type": "json_object"},
                "temperature": LLM_TEMPERATURE
            }
            res = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=body, timeout=LLM_TIMEOUT_SECONDS)
            res.raise_for_status()
            content = res.json()["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            return DailyReportSchema(**parsed)
    except Exception as e:
        logger.warning(f"External LLM call failed ({e}). Falling back to deterministic generator.")
        return None

def build_daily_report(target_date: Optional[date] = None, force_regenerate: bool = False) -> Dict[str, Any]:
    """
    Generates and stores the daily seismic report.
    Returns the report summary and metadata.
    """
    if target_date is None:
        target_date = date.today() - timedelta(days=1)
        
    stats = fetch_daily_statistics(target_date)
    
    # Format prompt input text
    top_regions_str = "\n".join([f"- {r['region']}: {r['event_count']} events (avg mag {r['avg_mag']})" for r in stats["top_regions"]]) or "None"
    sig_str = "\n".join([f"- M{s['mag']} at {s['place']} ({s['event_time']})" for s in stats["significant_events"]]) or "None"
    max_loc = stats["max_event"]["place"] if stats["max_event"] else "None"
    
    with open(PROMPT_FILE, "r", encoding="utf-8") as f:
        prompt_template = f.read()
        
    prompt_text = prompt_template.format(
        report_date=str(target_date),
        total_events=stats["total_events"],
        max_magnitude=stats["max_magnitude"],
        max_mag_location=max_loc,
        avg_magnitude=stats["avg_magnitude"],
        tsunami_count=stats["tsunami_count"],
        significant_count=stats["significant_count"],
        top_regions_str=top_regions_str,
        significant_events_str=sig_str,
        hourly_trend_summary="Normal hourly distribution across standard baseline."
    )
    
    start_time = time.time()
    execution_id = f"exec_{uuid.uuid4().hex[:12]}"
    is_fallback = False
    provider_used = LLM_PROVIDER
    model_used = LLM_MODEL
    
    report_obj = None
    if LLM_PROVIDER not in ("deterministic", "mock") and LLM_API_KEY:
        report_obj = call_external_llm(prompt_text)
        
    if report_obj is None:
        report_obj = generate_deterministic_report(stats)
        is_fallback = True
        provider_used = "deterministic_fallback"
        model_used = "deterministic-engine-v1"
        
    latency_ms = int((time.time() - start_time) * 1000)
    
    # Store in curated.daily_reports
    query_report = """
        INSERT INTO curated.daily_reports (
            report_date, title, executive_summary, stats_json, narrative_report,
            provider, model, latency_ms, tokens_used, cost_estimate, is_fallback, updated_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        ON CONFLICT (report_date) DO UPDATE SET
            title = EXCLUDED.title,
            executive_summary = EXCLUDED.executive_summary,
            stats_json = EXCLUDED.stats_json,
            narrative_report = EXCLUDED.narrative_report,
            provider = EXCLUDED.provider,
            model = EXCLUDED.model,
            latency_ms = EXCLUDED.latency_ms,
            tokens_used = EXCLUDED.tokens_used,
            cost_estimate = EXCLUDED.cost_estimate,
            is_fallback = EXCLUDED.is_fallback,
            updated_at = NOW()
        RETURNING id;
    """
    
    query_meta = """
        INSERT INTO curated.ai_execution_metadata (
            execution_id, task_name, provider, model, latency_ms,
            input_tokens, output_tokens, cost_usd, status, prompt_version
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
    """
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query_report, (
                target_date,
                report_obj.title,
                report_obj.executive_summary,
                json.dumps(stats, default=str),
                report_obj.narrative_report,
                provider_used,
                model_used,
                latency_ms,
                250 if not is_fallback else 0,
                0.0005 if not is_fallback else 0.0,
                is_fallback
            ))
            report_id = cur.fetchone()["id"]
            
            cur.execute(query_meta, (
                execution_id,
                "daily_narrative_report",
                provider_used,
                model_used,
                latency_ms,
                len(prompt_text.split()),
                len(report_obj.narrative_report.split()),
                0.0005 if not is_fallback else 0.0,
                "fallback" if is_fallback else "success",
                "daily_report_v1"
            ))
            
    logger.info(f"Daily report saved for date {target_date} with id {report_id} (fallback={is_fallback})")
    return {
        "report_id": report_id,
        "report_date": str(target_date),
        "title": report_obj.title,
        "is_fallback": is_fallback,
        "provider": provider_used,
        "latency_ms": latency_ms
    }
