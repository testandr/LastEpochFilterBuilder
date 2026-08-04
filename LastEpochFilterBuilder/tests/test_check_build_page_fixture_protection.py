import json
from types import SimpleNamespace
from pathlib import Path

from scripts.check_build_page import run_check


class DummyClient:
    def __init__(self, html: str):
        self._html = html

    def get(self, url, cache_subdir=None, use_cache=True):
        return SimpleNamespace(text=self._html, status_code=200)


def test_expected_json_not_overwritten(tmp_path, monkeypatch):
    # prepare: copy existing expected to tmp location and run run_check pointing tests to tmp
    expected_file = Path("tests/data/json/build_page_metadata_real.json")
    original = expected_file.read_text(encoding="utf-8")

    # prepare a dummy client returning fixture content
    html = Path("tests/data/html/build_page_metadata_real.html").read_text(encoding="utf-8")
    client = DummyClient(html)

    # run without update_fixtures
    run_check(update_fixtures=False, client=client)

    # ensure expected file unchanged
    after = expected_file.read_text(encoding="utf-8")
    assert after == original
