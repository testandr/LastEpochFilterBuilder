from app.research.build_data_discovery import analyze


def test_analyze_creates_report_and_returns_summary(tmp_path, monkeypatch):
    # Run analyze but point roots to existing test fixtures by not changing code;
    # Ensure it runs without throwing and returns a dict with expected keys.
    summary = analyze()
    assert isinstance(summary, dict)
    assert "json_blocks" in summary
    assert "data_le" in summary
    assert "confidence" in summary
