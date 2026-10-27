"""
SismoWatch Real-Time Ingestion DAG.
Fetches public USGS GeoJSON feed every 5 minutes and triggers the transformation & quality DAG.
"""
from datetime import datetime, timedelta, timezone
import os
import sys
from pathlib import Path
import uuid

# Ensure root airflow directory is in python path
sys.path.insert(0, str(Path(__file__).parents[1]))
sys.path.insert(0, "/opt/airflow")

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator

from include.config import USGS_REALTIME_URL
from include.usgs_client import USGSClient
from include.database import save_raw_feed

default_args = {
    "owner": "sismowatch_data_eng",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 3,
    "retry_delay": timedelta(seconds=30),
    "execution_timeout": timedelta(minutes=4),
}

def ingest_usgs_realtime_feed(**context) -> str:
    """
    Fetches the 1-hour GeoJSON feed from USGS, saves the untouched raw payload into raw.usgs_feed,
    and pushes the batch_id to XCom for downstream processing.
    """
    ti = context["task_instance"]
    batch_id = f"batch_{uuid.uuid4().hex[:12]}"
    execution_date = context.get("logical_date") or context.get("execution_date") or datetime.now(timezone.utc)
    
    client = USGSClient()
    payload = client.fetch_realtime_hour_feed()
    
    metadata = {
        "dag_id": "sismowatch_ingestion_dag",
        "task_id": "fetch_and_store_usgs_feed",
        "logical_date": str(execution_date),
        "source": "USGS_all_hour"
    }
    
    raw_id = save_raw_feed(
        batch_id=batch_id,
        feed_url=USGS_REALTIME_URL,
        status_code=200,
        payload=payload,
        metadata=metadata
    )
    
    ti.xcom_push(key="batch_id", value=batch_id)
    ti.xcom_push(key="raw_id", value=raw_id)
    ti.xcom_push(key="feature_count", value=len(payload.get("features", [])))
    
    return batch_id

with DAG(
    dag_id="sismowatch_ingestion_dag",
    default_args=default_args,
    description="Ingests USGS real-time earthquake GeoJSON every 5 minutes into raw schema",
    schedule="*/5 * * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["sismowatch", "ingestion", "usgs", "raw"],
) as dag:

    fetch_and_store = PythonOperator(
        task_id="fetch_and_store_usgs_feed",
        python_callable=ingest_usgs_realtime_feed,
    )

    trigger_transform = TriggerDagRunOperator(
        task_id="trigger_transformation_dag",
        trigger_dag_id="sismowatch_transformation_dag",
        conf={"batch_id": "{{ task_instance.xcom_pull(task_ids='fetch_and_store_usgs_feed', key='batch_id') }}"},
        wait_for_completion=False,
        reset_dag_run=True,
    )

    fetch_and_store >> trigger_transform
