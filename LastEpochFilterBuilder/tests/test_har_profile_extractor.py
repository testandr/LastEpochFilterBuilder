import json
from pathlib import Path

from app.research.har_profile_extractor import (
    extract_from_har,
    save_extracted,
    extract_profile_ids_from_html,
    _safe_load_json,
)


_CANDIDATES = [
    Path(__file__).parent / "data" / "json" / "sample_maxroll_profile.har.json",
    Path(__file__).parent.parent / "tests" / "data" / "json" / "sample_maxroll_profile.har.json",
    Path(__file__).parent.parent.parent / "tests" / "data" / "json" / "sample_maxroll_profile.har.json",
]


def _locate_fixture() -> Path:
    for p in _CANDIDATES:
        if p.exists():
            return p
    # fallback: try relative to repo root
    root = Path(__file__).resolve().parents[3]
    p = root / "tests" / "data" / "json" / "sample_maxroll_profile.har.json"
    return p


FIXTURE_PATH = _locate_fixture()


def test_fixture_exists():
    assert FIXTURE_PATH.exists(), (
        f"HAR fixture not found: {FIXTURE_PATH}. Checked candidates: {_CANDIDATES}"
    )


def test_extract_from_sample_har(tmp_path):
    har = FIXTURE_PATH
    found = extract_from_har(har)
    assert any(k.startswith("planner:") for k in found.keys())
    assert "game_data" in found


def test_save_extracted(tmp_path):
    har = FIXTURE_PATH
    found = extract_from_har(har)
    out = tmp_path / "out"
    planner_path, game_path = save_extracted(found, out)
    assert planner_path is not None and planner_path.exists()
    assert game_path is not None and game_path.exists()
    # planner JSON contains build_data
    p = json.loads(planner_path.read_text(encoding="utf-8"))
    assert "build_data" in p


def test_extract_profile_ids_from_html_dedup():
    html = '<div data-le-profile="testprofile123"></div><span data-le-profile="testprofile123"></span><a data-le-profile="other321"></a>'
    ids = extract_profile_ids_from_html(html)
    assert ids == ["testprofile123", "other321"]


def test_safe_load_json_invalid():
    assert _safe_load_json('{invalid:}') is None
