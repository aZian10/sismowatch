"""
SismoWatch Transformation, Quality Validation, and Curated Upsert DAG.
Processes raw batches, writes staging, quarantines invalid records,
upserts curated earthquakes, records quality scores, and checks statistical anomalies.
"""
from datetime import datetime, timedelta
import json
import logging
import os
import sys
from pathlib import Path

# Ensure root airflow directory is in python path
sys.path.insert(0, str(Path(__file__).parents[1]))
sys.path.insert(0, "/opt/airflow")

from airflow import DAG
from airflow.operators.python import PythonOperator

from include.database import (
    get_db_connection,
    insert_staging_records,
    upsert_curated_records,
    insert_quarantine_records,
    save_quality_metrics
)
from include.validation import process_and_validate_feed
from include.anomaly import detect_seismic_anomalies

logger = logging.getLogger("airflow.task")

default_args = {
    "owner": "sismowatch_data_eng",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(seconds=20),
    "execution_timeout": timedelta(minutes=5),
}

def stage_and_validate_data(**context) -> dict:
    """
    Extracts the latest or triggered raw batch, runs quality validation,
    stores staging and quarantine records, and pushes valid records for curation.
    """
    dag_run_conf = context.get("dag_run").conf or {}
    batch_id = dag_run_conf.get("batch_id")
    
    # If not triggered with batch_id, pick the latest un-processed raw feed
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            if batch_id:
                cur.execute("SELECT batch_id, raw_payload FROM raw.usgs_feed WHERE batch_id = %s LIMIT 1;", (batch_id,))
            else:
                cur.execute("SELECT batch_id, raw_payload FROM raw.usgs_feed ORDER BY ingested_at DESC LIMIT 1;")
            row = cur.fetchone()
            
    if not row:
        logger.warning("No raw feed payload found to transform.")
        return {"batch_id": None, "count": 0}

    batch_id = row["batch_id"]
    payload = row["raw_payload"]
    if isinstance(payload, str):
        payload = json.loads(payload)
        
    features = payload.get("features", [])
    staging_records, quarantined_records, quality_summary = process_and_validate_feed(features, batch_id)
    
    # 1. Insert into Staging
    if staging_records:
        insert_staging_records(staging_records)
        
    # 2. Insert into Quarantine
    if quarantined_records:
        insert_quarantine_records(quarantined_records)
        
    # 3. Idempotent Upsert into Curated
    passed_curated = quality_summary.get("passed_curated_records", [])
    if passed_curated:
        upsert_curated_records(passed_curated)
        
    # 4. Save Quality Metrics
    save_quality_metrics(
        batch_id=batch_id,
        evaluated_records=quality_summary["evaluated_records"],
        passed_records=quality_summary["passed_records"],
        rejected_records=quality_summary["rejected_records"],
        quality_score=quality_summary["quality_score"],
        freshness_seconds=quality_summary["freshness_seconds"],
        rules_summary=quality_summary["rules_summary"]
    )
    
    logger.info(
        f"Batch {batch_id} processed: "
        f"Evaluated={quality_summary['evaluated_records']}, "
        f"Passed={quality_summary['passed_records']}, "
        f"Quarantined={quality_summary['rejected_records']}, "
        f"Score={quality_summary['quality_score']}%"
    )
    
    return {
        "batch_id": batch_id,
        "evaluated": quality_summary["evaluated_records"],
        "passed": quality_summary["passed_records"],
        "quarantined": quality_summary["rejected_records"],
        "quality_score": quality_summary["quality_score"]
    }

def run_anomaly_detection(**context):
    """Executes statistical anomaly detection over the updated curated layer."""
    alerts = detect_seismic_anomalies(baseline_hours=48)
    logger.info(f"Anomaly detection completed. Found {len(alerts)} alerts.")
    return len(alerts)

with DAG(
    dag_id="sismowatch_transformation_dag",
    default_args=default_args,
    description="Validates raw feed, quarantines invalid records, upserts curated earthquakes, and computes quality score",
    schedule=None, # Triggered after ingestion
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["sismowatch", "transformation", "quality", "curated", "anomaly"],
) as dag:

    transform_task = PythonOperator(
        task_id="transform_validate_curate",
        python_callable=stage_and_validate_data,
    )

    anomaly_task = PythonOperator(
        task_id="detect_statistical_anomalies",
        python_callable=run_anomaly_detection,
    )

    transform_task >> anomaly_task
