"""
Statistical Anomaly Detection Engine for SismoWatch.
Computes lightweight rolling z-scores on hourly event volumes and magnitude metrics.
Distinguishes statistical anomalies from confirmed seismic threats.
"""
import logging
import math
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional

try:
    from include.config import ANOMALY_Z_THRESHOLD, ANOMALY_MIN_BASELINE_HOURS
    from include.database import get_db_connection
except ImportError:
    from airflow.include.config import ANOMALY_Z_THRESHOLD, ANOMALY_MIN_BASELINE_HOURS
    from airflow.include.database import get_db_connection

logger = logging.getLogger("sismowatch.anomaly")

def detect_seismic_anomalies(
    reference_time: Optional[datetime] = None,
    baseline_hours: int = 72,
    threshold: float = ANOMALY_Z_THRESHOLD
) -> List[Dict[str, Any]]:
    """
    Computes statistical z-scores for recent hourly earthquake activity.
    Compares the most recent complete hour against the baseline distribution.
    """
    if reference_time is None:
        reference_time = datetime.now(timezone.utc)
        
    # Baseline window: [reference_time - baseline_hours, reference_time - 1 hour]
    # Current window: [reference_time - 1 hour, reference_time]
    window_current_start = reference_time - timedelta(hours=1)
    window_baseline_start = reference_time - timedelta(hours=baseline_hours)
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # 1. Fetch hourly counts and mean magnitudes for the baseline
            cur.execute("""
                WITH hourly_stats AS (
                    SELECT 
                        date_trunc('hour', event_time) as hour_bucket,
                        COUNT(*) as event_count,
                        COALESCE(AVG(mag), 0.0) as avg_mag
                    FROM curated.earthquakes
                    WHERE event_time >= %s AND event_time < %s
                    GROUP BY 1
                )
                SELECT 
                    COUNT(*) as observed_hours,
                    COALESCE(AVG(event_count), 0.0) as mean_count,
                    COALESCE(STDDEV_SAMP(event_count), 0.0) as std_count,
                    COALESCE(AVG(avg_mag), 0.0) as mean_mag,
                    COALESCE(STDDEV_SAMP(avg_mag), 0.0) as std_mag
                FROM hourly_stats;
            """, (window_baseline_start, window_current_start))
            baseline = cur.fetchone()
            
            # 2. Fetch current hour metrics
            cur.execute("""
                SELECT 
                    COUNT(*) as current_count,
                    COALESCE(AVG(mag), 0.0) as current_avg_mag,
                    COALESCE(MAX(mag), 0.0) as current_max_mag
                FROM curated.earthquakes
                WHERE event_time >= %s AND event_time <= %s;
            """, (window_current_start, reference_time))
            current = cur.fetchone()

    observed_hours = baseline["observed_hours"] if baseline else 0
    if observed_hours < 6:
        logger.info(f"Insufficient baseline history ({observed_hours} hours). Skipping anomaly detection.")
        return []

    alerts = []
    
    # --- Check 1: Hourly Event Volume ---
    curr_count = float(current["current_count"])
    mean_count = float(baseline["mean_count"])
    std_count = float(baseline["std_count"])
    
    z_count = 0.0
    if std_count > 0.001:
        z_count = (curr_count - mean_count) / std_count
    elif curr_count > mean_count:
        z_count = 3.0 # Definite deviation if std is 0 but count jumped
        
    if abs(z_count) >= threshold:
        severity = "critical" if abs(z_count) >= 4.0 else ("high" if abs(z_count) >= 3.0 else "medium")
        direction = "surge" if z_count > 0 else "drop"
        explanation = (
            f"Statistically significant {direction} in seismic event frequency: "
            f"recorded {curr_count:.0f} events/hr versus baseline mean of {mean_count:.1f}±{std_count:.1f} "
            f"(z-score: {z_count:+.2f}, threshold: {threshold}). "
            f"Informational statistical anomaly only; does NOT indicate earthquake prediction."
        )
        alerts.append({
            "metric_name": "hourly_event_frequency",
            "current_value": curr_count,
            "baseline_mean": mean_count,
            "baseline_std": std_count,
            "z_score": round(z_count, 3),
            "threshold": threshold,
            "severity": severity,
            "explanation": explanation,
            "is_seismic_threat": False
        })

    # --- Check 2: Hourly Average Magnitude ---
    curr_mag = float(current["current_avg_mag"])
    mean_mag = float(baseline["mean_mag"])
    std_mag = float(baseline["std_mag"])
    
    if curr_count > 0 and std_mag > 0.01:
        z_mag = (curr_mag - mean_mag) / std_mag
        if z_mag >= threshold:
            severity = "critical" if z_mag >= 4.0 else ("high" if z_mag >= 3.0 else "medium")
            explanation = (
                f"Elevated average seismic intensity detected: "
                f"current average magnitude M{curr_mag:.2f} vs baseline mean M{mean_mag:.2f}±{std_mag:.2f} "
                f"(z-score: {z_mag:+.2f}, threshold: {threshold}). "
                f"Maximum recorded magnitude in hour: M{current['current_max_mag']:.1f}. "
                f"Statistical indicator based strictly on measured sensor data."
            )
            alerts.append({
                "metric_name": "hourly_average_magnitude",
                "current_value": curr_mag,
                "baseline_mean": mean_mag,
                "baseline_std": std_mag,
                "z_score": round(z_mag, 3),
                "threshold": threshold,
                "severity": severity,
                "explanation": explanation,
                "is_seismic_threat": False
            })

    # Store any generated alerts into curated.anomaly_alerts
    if alerts:
        query_insert = """
            INSERT INTO curated.anomaly_alerts (
                metric_name, current_value, baseline_mean, baseline_std,
                z_score, threshold, severity, explanation, is_seismic_threat
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
        """
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                for a in alerts:
                    cur.execute(query_insert, (
                        a["metric_name"],
                        a["current_value"],
                        a["baseline_mean"],
                        a["baseline_std"],
                        a["z_score"],
                        a["threshold"],
                        a["severity"],
                        a["explanation"],
                        a["is_seismic_threat"]
                    ))
        logger.info(f"Recorded {len(alerts)} statistical anomaly alert(s).")
        
    return alerts
