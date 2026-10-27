"""
Test for AI report fallback when provider fails or is unreachable (Requirement 9.7).
Verifies that:
1. Deterministic report is successfully generated from verified input statistics.
2. Structured output matches Pydantic schema.
3. Key metrics in report correspond directly to input figures without fabrication.
"""
import pytest
from include.ai_reporter import (
    DailyReportSchema,
    generate_deterministic_report,
    call_external_llm
)

def test_deterministic_report_generator_with_valid_stats():
    mock_stats = {
        "report_date": "2026-10-26",
        "total_events": 142,
        "max_magnitude": 6.3,
        "avg_magnitude": 2.45,
        "tsunami_count": 1,
        "significant_count": 3,
        "max_event": {
            "place": "120 km ENE of Kuril’sk, Russia",
            "mag": 6.3,
            "depth_km": 45.0
        },
        "top_regions": [
            {"region": "California", "event_count": 48, "avg_mag": 1.8},
            {"region": "Hawaii", "event_count": 22, "avg_mag": 2.1},
            {"region": "Alaska", "event_count": 19, "avg_mag": 2.3}
        ],
        "significant_events": [
            {"mag": 6.3, "place": "Kuril'sk, Russia", "event_time": "2026-10-26T12:00:00Z"}
        ]
    }
    
    report = generate_deterministic_report(mock_stats)
    
    # 1. Valid Pydantic model
    assert isinstance(report, DailyReportSchema)
    assert report.title == "Daily Seismic Activity Report - 2026-10-26"
    
    # 2. Key figures verified without invention
    assert "142" in report.executive_summary
    assert "6.3" in report.executive_summary
    assert "2.45" in report.executive_summary
    assert "1" in report.executive_summary # Tsunami count
    assert "Kuril’sk" in report.executive_summary

    # 3. Narrative content
    assert "California (48 events)" in report.narrative_report
    assert "M6.3" in report.narrative_report

def test_deterministic_report_generator_empty_day():
    empty_stats = {
        "report_date": "2026-10-25",
        "total_events": 0,
        "max_magnitude": 0.0,
        "avg_magnitude": 0.0,
        "tsunami_count": 0,
        "significant_count": 0,
        "max_event": None,
        "top_regions": [],
        "significant_events": []
    }
    
    report = generate_deterministic_report(empty_stats)
    assert isinstance(report, DailyReportSchema)
    assert "zero seismic events" in report.narrative_report.lower() or "no seismic events" in report.executive_summary.lower()

def test_call_external_llm_falls_back_when_offline(monkeypatch):
    """When LLM provider is misconfigured or fails, call_external_llm returns None."""
    monkeypatch.setenv("LLM_PROVIDER", "deterministic")
    monkeypatch.setenv("LLM_API_KEY", "")
    
    result = call_external_llm("Generate a report")
    assert result is None

def test_ollama_local_model_success(monkeypatch):
    """Verifies that Ollama JSON response is parsed into DailyReportSchema with token metadata."""
    import requests
    from unittest.mock import MagicMock
    from include.ai_reporter import call_llm_provider

    monkeypatch.setattr("include.ai_reporter.LLM_PROVIDER", "ollama")
    monkeypatch.setattr("include.ai_reporter.LLM_MODEL", "qwen2.5:0.5b")
    monkeypatch.setattr("include.ai_reporter.LLM_BASE_URL", "http://ollama:11434")

    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "message": {
            "content": '{"title": "Local AI Report", "executive_summary": "Summary of 42 quakes.", "narrative_report": "Detailed narrative."}'
        },
        "prompt_eval_count": 50,
        "eval_count": 80
    }
    mock_resp.raise_for_status = MagicMock()

    monkeypatch.setattr(requests, "post", lambda url, **kwargs: mock_resp)

    res = call_llm_provider("Prompt content")
    assert res is not None
    schema, prompt_tok, eval_tok = res
    assert isinstance(schema, DailyReportSchema)
    assert schema.title == "Local AI Report"
    assert schema.executive_summary == "Summary of 42 quakes."
    assert prompt_tok == 50
    assert eval_tok == 80

def test_ollama_local_model_offline_fallback(monkeypatch):
    """Verifies that when Ollama is unreachable, it logs a warning and returns None (triggering fallback)."""
    import requests
    from include.ai_reporter import call_llm_provider

    monkeypatch.setattr("include.ai_reporter.LLM_PROVIDER", "ollama")
    monkeypatch.setattr("include.ai_reporter.LLM_BASE_URL", "http://non-existent-host:11434")

    def mock_fail(*args, **kwargs):
        raise requests.ConnectionError("Connection refused")

    monkeypatch.setattr(requests, "post", mock_fail)

    res = call_llm_provider("Prompt content")
    assert res is None
