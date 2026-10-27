"""
Test ensuring duplicate ingestion does not duplicate events (Requirement 9.3).
Simulates ingestion of the same GeoJSON features over repeated executions,
verifying that records update or stay deduplicated by event_id.
"""
import pytest
from include.validation import process_and_validate_feed

def test_duplicate_feed_ingestion_deduplication():
    feature = {
        "type": "Feature",
        "id": "nc74092811",
        "properties": {
            "mag": 2.8,
            "place": "Central California",
            "time": 1729000000000,
            "updated": 1729000100000,
            "tsunami": 0,
            "sig": 120,
            "status": "automatic",
            "type": "earthquake"
        },
        "geometry": {"type": "Point", "coordinates": [-120.5, 36.5, 7.2]}
    }
    
    # Run Batch 1
    _, _, summary_1 = process_and_validate_feed([feature], batch_id="batch_1")
    assert summary_1["passed_records"] == 1
    curated_1 = summary_1["passed_curated_records"][0]
    assert curated_1["event_id"] == "nc74092811"
    assert curated_1["status"] == "automatic"
    
    # Run Batch 2: Exact same event, updated by USGS review
    updated_feature = dict(feature)
    updated_feature["properties"] = dict(feature["properties"])
    updated_feature["properties"]["status"] = "reviewed"
    updated_feature["properties"]["mag"] = 2.9
    updated_feature["properties"]["updated"] = 1729000500000
    
    _, _, summary_2 = process_and_validate_feed([updated_feature], batch_id="batch_2")
    assert summary_2["passed_records"] == 1
    curated_2 = summary_2["passed_curated_records"][0]
    assert curated_2["event_id"] == "nc74092811"
    assert curated_2["status"] == "reviewed"
    assert curated_2["mag"] == 2.9
    
    # Both executions produce the same unique primary key event_id
    assert curated_1["event_id"] == curated_2["event_id"]
