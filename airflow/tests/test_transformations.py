"""
Unit tests for converting USGS GeoJSON feature into a staging record (Requirement 9.1).
"""
import pytest
from datetime import datetime, timezone
from include.validation import parse_geojson_feature

def test_parse_valid_geojson_feature():
    """Verify standard USGS GeoJSON feature mapping to staging schema."""
    sample_feature = {
        "type": "Feature",
        "properties": {
            "mag": 4.82,
            "place": "12 km SSW of Volcano, Hawaii",
            "time": 1729000000000,
            "updated": 1729000500000,
            "tsunami": 0,
            "sig": 350,
            "status": "reviewed",
            "magType": "ml",
            "type": "earthquake",
            "url": "https://earthquake.usgs.gov/earthquakes/eventpage/hv74291882"
        },
        "geometry": {
            "type": "Point",
            "coordinates": [-155.234, 19.345, 10.5]
        },
        "id": "hv74291882"
    }
    
    staged = parse_geojson_feature(sample_feature, batch_id="batch_test_01")
    
    assert staged["batch_id"] == "batch_test_01"
    assert staged["event_id"] == "hv74291882"
    assert staged["mag"] == 4.82
    assert staged["place"] == "12 km SSW of Volcano, Hawaii"
    assert staged["longitude"] == -155.234
    assert staged["latitude"] == 19.345
    assert staged["depth_km"] == 10.5
    assert staged["tsunami"] == 0
    assert staged["sig"] == 350
    assert staged["status"] == "reviewed"
    assert staged["mag_type"] == "ml"
    assert staged["event_type"] == "earthquake"
    assert isinstance(staged["event_time"], datetime)
    assert staged["event_time"].tzinfo == timezone.utc

def test_parse_feature_with_missing_coordinates():
    """Verify graceful handling when coordinates or properties are incomplete."""
    incomplete_feature = {
        "type": "Feature",
        "properties": {
            "mag": None,
            "place": None,
            "time": None
        },
        "geometry": {
            "type": "Point",
            "coordinates": []
        },
        "id": "missing_coords_01"
    }
    
    staged = parse_geojson_feature(incomplete_feature, batch_id="batch_test_02")
    assert staged["event_id"] == "missing_coords_01"
    assert staged["longitude"] is None
    assert staged["latitude"] is None
    assert staged["depth_km"] is None
    assert staged["mag"] is None
    assert staged["event_time"] is None
