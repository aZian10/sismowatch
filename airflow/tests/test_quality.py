"""
Unit tests for data quality rules and validation cases (Requirement 9.2).
Tests latitude, longitude, magnitude, depth boundaries, timestamps, and required IDs.
"""
import pytest
from datetime import datetime, timezone, timedelta
from include.validation import validate_earthquake_record

def create_base_record():
    return {
        "event_id": "us7000m9xx",
        "mag": 5.2,
        "place": "Off coast of Northern California",
        "time_epoch_ms": int((datetime.now(timezone.utc) - timedelta(hours=2)).timestamp() * 1000),
        "event_time": datetime.now(timezone.utc) - timedelta(hours=2),
        "latitude": 40.5,
        "longitude": -124.5,
        "depth_km": 15.0
    }

def test_valid_record_passes_all_rules():
    record = create_base_record()
    is_valid, reasons, failed_rules = validate_earthquake_record(record)
    assert is_valid is True
    assert len(reasons) == 0
    assert len(failed_rules) == 0

def test_invalid_latitude_bounds():
    record = create_base_record()
    record["latitude"] = 95.5 # Beyond +90
    is_valid, reasons, failed_rules = validate_earthquake_record(record)
    assert is_valid is False
    assert "LATITUDE_OUT_OF_BOUNDS" in failed_rules

    record["latitude"] = -105.0 # Beyond -90
    is_valid, reasons, failed_rules = validate_earthquake_record(record)
    assert is_valid is False
    assert "LATITUDE_OUT_OF_BOUNDS" in failed_rules

def test_invalid_longitude_bounds():
    record = create_base_record()
    record["longitude"] = 195.0 # Beyond +180
    is_valid, reasons, failed_rules = validate_earthquake_record(record)
    assert is_valid is False
    assert "LONGITUDE_OUT_OF_BOUNDS" in failed_rules

def test_invalid_magnitude_bounds():
    record = create_base_record()
    record["mag"] = 15.5 # Physically impossible earthquake magnitude
    is_valid, reasons, failed_rules = validate_earthquake_record(record)
    assert is_valid is False
    assert "MAGNITUDE_OUT_OF_BOUNDS" in failed_rules

    record["mag"] = -5.0 # Lower than allowable threshold
    is_valid, reasons, failed_rules = validate_earthquake_record(record)
    assert is_valid is False
    assert "MAGNITUDE_OUT_OF_BOUNDS" in failed_rules

def test_valid_micro_magnitude_negative():
    # Micro earthquakes legitimately have negative magnitudes like -0.8
    record = create_base_record()
    record["mag"] = -0.8
    is_valid, reasons, failed_rules = validate_earthquake_record(record)
    assert is_valid is True

def test_invalid_depth_bounds():
    record = create_base_record()
    record["depth_km"] = 1200.0 # Earth's lower mantle / core
    is_valid, reasons, failed_rules = validate_earthquake_record(record)
    assert is_valid is False
    assert "DEPTH_OUT_OF_BOUNDS" in failed_rules

def test_future_timestamp_skew():
    record = create_base_record()
    record["event_time"] = datetime.now(timezone.utc) + timedelta(days=5) # 5 days in future
    record["time_epoch_ms"] = int(record["event_time"].timestamp() * 1000)
    is_valid, reasons, failed_rules = validate_earthquake_record(record)
    assert is_valid is False
    assert "TIMESTAMP_FUTURE_SKEW" in failed_rules

def test_missing_event_id():
    record = create_base_record()
    record["event_id"] = ""
    is_valid, reasons, failed_rules = validate_earthquake_record(record)
    assert is_valid is False
    assert "REQUIRED_EVENT_ID" in failed_rules
