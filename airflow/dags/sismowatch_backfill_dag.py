"""
SismoWatch Parameterized Historical Backfill DAG.
Queries the USGS FDSNWS query endpoint for up to 30 days of historical data,
executes quality validation, isolates invalid records in quarantine,
and idempotently upserts valid events into curated.earthquakes.
Triggered exclusively by administrators via the web platform or Airflow UI.
"""
from datetime import datetime, timedelta, date, timezone
import logging
import os
import sys
import uuid
from pathlib import Path

# Ensure root airflow directory is in python path
sys.path.insert(0, str(Path(__file__).parents[1]))
sys.path.insert(0, "/opt/airflow")

from airflow import DAG
from airflow.models.param import Param
from airflow.operators.python import PythonOperator

from include.config import USGS_QUERY_URL
from include.usgs_client import USGSClient
from include.quality import execute_ingestion_and_quality_pipeline

logger = logging.getLogger("airflow.task")

default_args = {
    "owner": "sismowatch_admin",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
    "execution_timeout": timedelta(minutes=30),
}

def run_historical_backfill(**context) -> dict:
    """
    Executes historical backfill using configured or passed parameters.
    Default range: past 30 days, min magnitude 2.5.
    """
    params = context.get("params", {})
    dag_run_conf = context.get("dag_run").conf or {}
    
    # Merge dag_run conf with params
    merged_params = {**params, **dag_run_conf}
    
    default_end = date.today().strftime("%Y-%m-%d")
    default_start = (date.today() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    starttime = merged_params.get("starttime") or default_start
    endtime = merged_params.get("endtime") or default_end
    minmagnitude = float(merged_params.get("minmagnitude", 2.5))
    
    logger.info(f"Initiating USGS historical backfill from {starttime} to {endtime} (min mag {minmagnitude})")
    
    client = USGSClient(timeout=45)
    payload = client.fetch_historical_events(
        starttime=starttime,
        endtime=endtime,
        minmagnitude=minmagnitude
    )
    
    batch_id = f"backfill_{uuid.uuid4().hex[:12]}"
    metadata = {
        "operation": "historical_backfill",
        "starttime": starttime,
        "endtime": endtime,
        "minmagnitude": minmagnitude,
        "triggered_by": merged_params.get("triggered_by", "system_admin"),
        "triggered_at": datetime.now(timezone.utc).isoformat()
    }
    
    result = execute_ingestion_and_quality_pipeline(
        raw_payload=payload,
        feed_url=f"{USGS_QUERY_URL}?format=geojson&starttime={starttime}&endtime={endtime}&minmagnitude={minmagnitude}",
        batch_id=batch_id,
        metadata=metadata
    )
    
    logger.info(f"Historical backfill finished successfully: {result}")
    return result

with DAG(
    dag_id="sismowatch_backfill_dag",
    default_args=default_args,
    description="Administrator-triggered historical backfill from USGS event catalog (idempotent upsert)",
    schedule=None, # Manual / API trigger only
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
    params={
        "starttime": Param(
            default=(date.today() - timedelta(days=30)).strftime("%Y-%m-%d"),
            type="string",
            description="Start date (YYYY-MM-DD)"
        ),
        "endtime": Param(
            default=date.today().strftime("%Y-%m-%d"),
            type="string",
            description="End date (YYYY-MM-DD)"
        ),
        "minmagnitude": Param(
            default=2.5,
            type="number",
            description="Minimum earthquake magnitude filter"
        ),
    },
    tags=["sismowatch", "admin", "backfill", "historical", "usgs"],
) as dag:

    backfill_task = PythonOperator(
        task_id="execute_usgs_historical_backfill",
        python_callable=run_historical_backfill,
    )
