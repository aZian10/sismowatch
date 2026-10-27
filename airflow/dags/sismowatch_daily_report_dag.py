"""
SismoWatch Daily AI Narrative Report DAG.
Executes daily at 01:00 UTC to compute verified SQL statistics for the previous day,
invoke the LLM (or deterministic fallback), validate structured output with Pydantic,
and store the report and AI execution metadata into curated schema.
"""
from datetime import datetime, timedelta, date, timezone
import logging
import os
import sys
from pathlib import Path

# Ensure root airflow directory is in python path
sys.path.insert(0, str(Path(__file__).parents[1]))
sys.path.insert(0, "/opt/airflow")

from airflow import DAG
from airflow.operators.python import PythonOperator

from include.ai_reporter import build_daily_report

logger = logging.getLogger("airflow.task")

default_args = {
    "owner": "sismowatch_data_eng",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
    "execution_timeout": timedelta(minutes=10),
}

def generate_daily_report_task(**context) -> dict:
    """
    Computes verified stats and creates the daily executive report.
    Picks yesterday's date relative to logical_date or current date.
    """
    logical_date = context.get("logical_date") or context.get("execution_date")
    if logical_date:
        target_date = (logical_date - timedelta(days=1)).date()
    else:
        target_date = date.today() - timedelta(days=1)
        
    logger.info(f"Generating SismoWatch Daily Report for target date: {target_date}")
    result = build_daily_report(target_date=target_date, force_regenerate=True)
    logger.info(f"Report successfully generated: {result}")
    return result

with DAG(
    dag_id="sismowatch_daily_report_dag",
    default_args=default_args,
    description="Daily AI executive report summarizing seismicity with ground-truth verification and deterministic fallback",
    schedule="0 1 * * *", # Daily at 01:00 UTC
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["sismowatch", "ai", "reports", "daily", "curated"],
) as dag:

    report_task = PythonOperator(
        task_id="generate_daily_executive_report",
        python_callable=generate_daily_report_task,
    )
