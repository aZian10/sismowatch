"""
Data Validation and Quality Assurance Engine for SismoWatch.
Transforms USGS GeoJSON features into normalized records, runs Pandera/custom quality rules,
and isolates invalid records into quarantine.
"""
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple, Optional
try:
    from pandera.pandas import Column, Check, DataFrameSchema
except ImportError:
    import pandera as pa
    Check = getattr(pa, "Check", None)
    Column = Any
    DataFrameSchema = Any
import pandas as pd

try:
    from include.config import QUALITY_THRESHOLDS
except ImportError:
    from airflow.include.config import QUALITY_THRESHOLDS

def parse_geojson_feature(feature: Dict[str, Any], batch_id: str) -> Dict[str, Any]:
    """
    Parses a single USGS GeoJSON feature into a normalized staging dictionary.
    Handles epoch millisecond conversions to timezone-aware UTC datetime.
    """
    props = feature.get("properties") or {}
    geom = feature.get("geometry") or {}
    coords = geom.get("coordinates") or []
    
    event_id = feature.get("id") or props.get("id")
    
    # Extract coordinates: GeoJSON standard is [longitude, latitude, depth]
    lon = coords[0] if len(coords) > 0 else None
    lat = coords[1] if len(coords) > 1 else None
    depth = coords[2] if len(coords) > 2 else None
    
    # Epoch ms to datetime
    time_ms = props.get("time")
    event_time = None
    if time_ms is not None and isinstance(time_ms, (int, float)):
        try:
            event_time = datetime.fromtimestamp(time_ms / 1000.0, tz=timezone.utc)
        except (ValueError, OverflowError, OSError):
            event_time = None
            
    updated_ms = props.get("updated")
    updated_time = None
    if updated_ms is not None and isinstance(updated_ms, (int, float)):
        try:
            updated_time = datetime.fromtimestamp(updated_ms / 1000.0, tz=timezone.utc)
        except (ValueError, OverflowError, OSError):
            updated_time = None

    return {
        "batch_id": batch_id,
        "event_id": str(event_id) if event_id is not None else None,
        "mag": float(props["mag"]) if props.get("mag") is not None else None,
        "place": props.get("place"),
        "time_epoch_ms": time_ms,
        "event_time": event_time,
        "updated_epoch_ms": updated_ms,
        "updated_time": updated_time,
        "tsunami": int(props.get("tsunami", 0)) if props.get("tsunami") is not None else 0,
        "sig": int(props.get("sig", 0)) if props.get("sig") is not None else 0,
        "status": props.get("status") or "automatic",
        "mag_type": props.get("magType"),
        "event_type": props.get("type") or "earthquake",
        "url": props.get("url"),
        "longitude": float(lon) if lon is not None else None,
        "latitude": float(lat) if lat is not None else None,
        "depth_km": float(depth) if depth is not None else None,
        "raw_properties": props,
        "raw_feature": feature
    }

def validate_earthquake_record(record: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
    """
    Validates a single parsed earthquake record against documented quality rules.
    Returns: (is_valid, rejection_reasons, failed_rules)
    """
    rejection_reasons = []
    failed_rules = []
    
    # Rule 1: Required Event ID
    if not record.get("event_id") or not str(record["event_id"]).strip():
        rejection_reasons.append("Missing or empty event_id")
        failed_rules.append("REQUIRED_EVENT_ID")
        
    # Rule 2: Valid Event Time
    event_time = record.get("event_time")
    time_ms = record.get("time_epoch_ms")
    now_utc = datetime.now(timezone.utc)
    if event_time is None or time_ms is None or time_ms <= 0:
        rejection_reasons.append("Missing, non-positive, or unparseable event timestamp")
        failed_rules.append("INVALID_TIMESTAMP")
    elif (event_time - now_utc).total_seconds() > QUALITY_THRESHOLDS["max_future_seconds"]:
        rejection_reasons.append(f"Event timestamp is too far in the future (skew: {(event_time - now_utc).total_seconds():.0f}s)")
        failed_rules.append("TIMESTAMP_FUTURE_SKEW")
    elif event_time.year < QUALITY_THRESHOLDS["min_timestamp_year"]:
        rejection_reasons.append(f"Event timestamp year {event_time.year} is prior to {QUALITY_THRESHOLDS['min_timestamp_year']}")
        failed_rules.append("TIMESTAMP_OUT_OF_BOUNDS")

    # Rule 3: Coordinate existence and numeric types
    lat = record.get("latitude")
    lon = record.get("longitude")
    depth = record.get("depth_km")
    
    if lat is None or not isinstance(lat, (int, float)):
        rejection_reasons.append("Missing or non-numeric latitude")
        failed_rules.append("MISSING_LATITUDE")
    elif lat < QUALITY_THRESHOLDS["min_latitude"] or lat > QUALITY_THRESHOLDS["max_latitude"]:
        rejection_reasons.append(f"Latitude {lat} is outside valid range [-90.0, 90.0]")
        failed_rules.append("LATITUDE_OUT_OF_BOUNDS")

    if lon is None or not isinstance(lon, (int, float)):
        rejection_reasons.append("Missing or non-numeric longitude")
        failed_rules.append("MISSING_LONGITUDE")
    elif lon < QUALITY_THRESHOLDS["min_longitude"] or lon > QUALITY_THRESHOLDS["max_longitude"]:
        rejection_reasons.append(f"Longitude {lon} is outside valid range [-180.0, 180.0]")
        failed_rules.append("LONGITUDE_OUT_OF_BOUNDS")

    # Rule 4: Plausible Depth
    if depth is None or not isinstance(depth, (int, float)):
        rejection_reasons.append("Missing or non-numeric depth")
        failed_rules.append("MISSING_DEPTH")
    elif depth < QUALITY_THRESHOLDS["min_depth_km"] or depth > QUALITY_THRESHOLDS["max_depth_km"]:
        rejection_reasons.append(f"Depth {depth} km is outside physical plausible range [{QUALITY_THRESHOLDS['min_depth_km']}, {QUALITY_THRESHOLDS['max_depth_km']}]")
        failed_rules.append("DEPTH_OUT_OF_BOUNDS")

    # Rule 5: Plausible Magnitude
    # Note: Micro-earthquakes can have negative magnitude (e.g. -1.5).
    # But missing magnitude or magnitudes > 10.0 (impossible on Earth) are invalid.
    mag = record.get("mag")
    if mag is None or not isinstance(mag, (int, float)):
        rejection_reasons.append("Missing or non-numeric magnitude")
        failed_rules.append("MISSING_MAGNITUDE")
    elif mag < QUALITY_THRESHOLDS["min_magnitude"] or mag > QUALITY_THRESHOLDS["max_magnitude"]:
        rejection_reasons.append(f"Magnitude {mag} is outside physical boundary [{QUALITY_THRESHOLDS['min_magnitude']}, {QUALITY_THRESHOLDS['max_magnitude']}]")
        failed_rules.append("MAGNITUDE_OUT_OF_BOUNDS")

    # Rule 6: Place name must not be None or empty
    place = record.get("place")
    if not place or not str(place).strip():
        rejection_reasons.append("Missing or empty place description")
        failed_rules.append("MISSING_PLACE")

    is_valid = len(rejection_reasons) == 0
    return is_valid, rejection_reasons, failed_rules

def process_and_validate_feed(
    features: List[Dict[str, Any]],
    batch_id: str
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    """
    Processes all GeoJSON features for a batch.
    Returns:
        (staging_records, quarantined_records, quality_summary)
    """
    staging_records = []
    quarantined_records = []
    passed_for_curated = []
    rules_violation_counts: Dict[str, int] = {}
    
    latest_event_time = None
    
    for feat in features:
        staged = parse_geojson_feature(feat, batch_id)
        staging_records.append(staged)
        
        is_valid, reasons, failed_rules = validate_earthquake_record(staged)
        
        if is_valid:
            # Prepare clean curated record
            curated_item = {
                "event_id": staged["event_id"],
                "mag": staged["mag"],
                "place": staged["place"],
                "event_time": staged["event_time"],
                "updated_time": staged["updated_time"] or staged["event_time"],
                "tsunami": staged["tsunami"],
                "sig": staged["sig"],
                "status": staged["status"],
                "mag_type": staged["mag_type"],
                "event_type": staged["event_type"],
                "url": staged["url"],
                "longitude": staged["longitude"],
                "latitude": staged["latitude"],
                "depth_km": staged["depth_km"],
                "last_synced_at": datetime.now(timezone.utc)
            }
            passed_for_curated.append(curated_item)
            
            if latest_event_time is None or staged["event_time"] > latest_event_time:
                latest_event_time = staged["event_time"]
        else:
            quarantined_records.append({
                "batch_id": batch_id,
                "event_id": staged.get("event_id"),
                "rejection_reasons": reasons,
                "failed_rules": failed_rules,
                "raw_record": feat
            })
            for rule in failed_rules:
                rules_violation_counts[rule] = rules_violation_counts.get(rule, 0) + 1

    evaluated_count = len(features)
    passed_count = len(passed_for_curated)
    rejected_count = len(quarantined_records)
    quality_score = (passed_count / evaluated_count * 100.0) if evaluated_count > 0 else 100.0
    
    # Calculate freshness (seconds between now and latest event in the batch)
    freshness_seconds = None
    if latest_event_time:
        freshness_seconds = int((datetime.now(timezone.utc) - latest_event_time).total_seconds())

    quality_summary = {
        "batch_id": batch_id,
        "evaluated_records": evaluated_count,
        "passed_records": passed_count,
        "rejected_records": rejected_count,
        "quality_score": round(quality_score, 2),
        "freshness_seconds": freshness_seconds,
        "rules_summary": rules_violation_counts,
        "passed_curated_records": passed_for_curated
    }

    return staging_records, quarantined_records, quality_summary
