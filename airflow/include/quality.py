"""
Quality Pipeline Orchestrator.
Coordinates the end-to-end execution:
1. Parsing raw payload
2. Inserting staging records
3. Executing quality validations
4. Writing quarantine records
5. Idempotent upsert into curated.earthquakes
6. Storing quality metrics
"""
import logging
import uuid
from typing import Dict, Any, Tuple

try:
    from include.validation import process_and_validate_feed
    from include.database import (
        save_raw_feed,
        insert_staging_records,
        upsert_curated_records,
        insert_quarantine_records,
        save_quality_metrics
    )
except ImportError:
    from airflow.include.validation import process_and_validate_feed
    from airflow.include.database import (
        save_raw_feed,
        insert_staging_records,
        upsert_curated_records,
        insert_quarantine_records,
        save_quality_metrics
    )

logger = logging.getLogger("sismowatch.quality")

def execute_ingestion_and_quality_pipeline(
    raw_payload: Dict[str, Any],
    feed_url: str,
    batch_id: str = None,
    metadata: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Executes the full data flow for an ingested GeoJSON payload:
    USGS API -> Raw -> Staging -> Quality Validation -> Quarantine / Curated -> Metrics
    """
    if not batch_id:
        batch_id = f"batch_{uuid.uuid4().hex[:12]}"
        
    logger.info(f"Starting pipeline execution for batch_id: {batch_id}")
    
    # 1. Store Raw Payload
    raw_id = save_raw_feed(
        batch_id=batch_id,
        feed_url=feed_url,
        status_code=200,
        payload=raw_payload,
        metadata=metadata
    )
    logger.info(f"Raw feed saved with id {raw_id}")
    
    # 2. Extract and Validate
    features = raw_payload.get("features", [])
    staging_records, quarantined_records, quality_summary = process_and_validate_feed(features, batch_id)
    
    # 3. Store into Staging Schema
    if staging_records:
        insert_staging_records(staging_records)
        logger.info(f"Inserted {len(staging_records)} records into staging.earthquakes")
        
    # 4. Store Quarantined Records
    if quarantined_records:
        insert_quarantine_records(quarantined_records)
        logger.warning(f"Quarantined {len(quarantined_records)} invalid records into curated.quarantine")
        
    # 5. Idempotent Upsert into Curated Schema
    passed_curated = quality_summary.get("passed_curated_records", [])
    if passed_curated:
        upsert_curated_records(passed_curated)
        logger.info(f"Successfully upserted {len(passed_curated)} valid records into curated.earthquakes")
        
    # 6. Save Quality Execution Metrics
    save_quality_metrics(
        batch_id=batch_id,
        evaluated_records=quality_summary["evaluated_records"],
        passed_records=quality_summary["passed_records"],
        rejected_records=quality_summary["rejected_records"],
        quality_score=quality_summary["quality_score"],
        freshness_seconds=quality_summary["freshness_seconds"],
        rules_summary=quality_summary["rules_summary"]
    )
    logger.info(f"Saved quality metrics for batch {batch_id}: Score = {quality_summary['quality_score']}%")
    
    return {
        "batch_id": batch_id,
        "raw_id": raw_id,
        "evaluated": quality_summary["evaluated_records"],
        "passed": quality_summary["passed_records"],
        "quarantined": quality_summary["rejected_records"],
        "quality_score": quality_summary["quality_score"],
        "freshness_seconds": quality_summary["freshness_seconds"]
    }
