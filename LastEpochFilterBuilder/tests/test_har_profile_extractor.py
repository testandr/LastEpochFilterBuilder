import json
from pathlib import Path

from app.research.har_profile_extractor import extract_from_har, save_extracted, extract_profile_ids_from_html, _safe_load_json


def test_extract_from_sample_har(tmp_path):
    har = Path("tests/data/json/sample_maxroll_profile.har.json")
    found = extract_from_har(har)
    assert any(k.startswith("planner:") for k in found.keys())
    assert "game_data" in found


def test_save_extracted(tmp_path):
    har = Path("tests/data/json/sample_maxroll_profile.har.json")
    found = extract_from_har(har)
    out = tmp_path / "out"
    planner_path, game_path = save_extracted(found, out)
    assert planner_path is not None and planner_path.exists()
    assert game_path is not None and game_path.exists()
    # planner JSON contains build_data
    p = json.loads(planner_path.read_text(encoding="utf-8"))
    assert "build_data" in p


def test_extract_profile_ids_from_html_dedup():
    html = '<div data-le-profile="zge0t60e"></div><span data-le-profile="zge0t60e"></span><a data-le-profile="abc123"></a>'
    ids = extract_profile_ids_from_html(html)
    assert ids == ["zge0t60e", "abc123"]


def test_safe_load_json_invalid():
    assert _safe_load_json('{invalid:}') is None
