"""
Test for quarantining invalid records and preventing publication into curated (Requirement 9.8).
"""
import pytest
from include.validation import process_and_validate_feed

def test_quarantining_blocks_curated_publication():
    """
    Given a batch containing both valid and corrupt records:
    - Corrupt records must be isolated into quarantined_records with explicit reasons.
    - Corrupt records must NEVER appear in passed_curated_records.
    - Valid records must reach passed_curated_records.
    """
    features = [
        # 1. Valid record
        {
            "type": "Feature",
            "id": "valid_quake_01",
            "properties": {
                "mag": 3.4,
                "place": "10km NE of San Jose, CA",
                "time": 1729000000000,
                "updated": 1729000100000,
                "tsunami": 0,
                "sig": 180,
                "status": "reviewed"
            },
            "geometry": {"type": "Point", "coordinates": [-121.8, 37.3, 8.0]}
        },
        # 2. Corrupt record: Latitude out of bounds (145.0)
        {
            "type": "Feature",
            "id": "corrupt_quake_lat",
            "properties": {
                "mag": 4.1,
                "place": "Invalid Latitude Region",
                "time": 1729000000000,
                "updated": 1729000100000,
                "tsunami": 0
            },
            "geometry": {"type": "Point", "coordinates": [-120.0, 145.0, 10.0]}
        },
        # 3. Corrupt record: Impossible magnitude (18.9)
        {
            "type": "Feature",
            "id": "corrupt_quake_mag",
            "properties": {
                "mag": 18.9,
                "place": "Impossible Energy Explosion",
                "time": 1729000000000,
                "updated": 1729000100000,
                "tsunami": 0
            },
            "geometry": {"type": "Point", "coordinates": [-100.0, 25.0, 12.0]}
        },
        # 4. Corrupt record: Missing ID
        {
            "type": "Feature",
            "id": None,
            "properties": {
                "mag": 2.2,
                "place": "Ghost Earthquake",
                "time": 1729000000000,
                "updated": 1729000100000,
                "tsunami": 0
            },
            "geometry": {"type": "Point", "coordinates": [-118.0, 34.0, 5.0]}
        }
    ]
    
    staging_records, quarantined_records, summary = process_and_validate_feed(features, batch_id="batch_quarantine_test")
    
    # 4 records evaluated
    assert summary["evaluated_records"] == 4
    assert summary["passed_records"] == 1
    assert summary["rejected_records"] == 3
    assert summary["quality_score"] == 25.0 # 1 / 4 * 100%
    
    # Exactly 1 passed curated record
    curated_ids = [c["event_id"] for c in summary["passed_curated_records"]]
    assert curated_ids == ["valid_quake_01"]
    
    # 3 quarantined records with respective failure reasons
    quarantined_ids = [q.get("event_id") for q in quarantined_records]
    assert "corrupt_quake_lat" in quarantined_ids
    assert "corrupt_quake_mag" in quarantined_ids
    assert None in quarantined_ids
    
    # Inspect rejection reasons
    lat_quarantine = next(q for q in quarantined_records if q.get("event_id") == "corrupt_quake_lat")
    assert "LATITUDE_OUT_OF_BOUNDS" in lat_quarantine["failed_rules"]
    
    mag_quarantine = next(q for q in quarantined_records if q.get("event_id") == "corrupt_quake_mag")
    assert "MAGNITUDE_OUT_OF_BOUNDS" in mag_quarantine["failed_rules"]
