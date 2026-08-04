import json
from pathlib import Path

from app.parsers.build_parser import BuildParser


def load_fixture():
    p = Path("tests/data/html/build_page_metadata_real.html")
    return p.read_text(encoding="utf-8")


def load_expected():
    p = Path("tests/data/json/build_page_metadata_real.json")
    return json.loads(p.read_text(encoding="utf-8"))


def test_parse_build_metadata_offline():
    html = load_fixture()
    parser = BuildParser()
    bd = parser.parse_html(html, "https://maxroll.gg/last-epoch/build-guides/shadow-rend-bladedancer-guide")
    expected = load_expected()
    assert bd.name == expected["name"]
    assert bd.class_name == expected["class_name"]
    assert bd.mastery == expected["mastery"]
    assert bd.author == expected["author"]
    assert bd.source_url == expected["source_url"]
    assert bd.items == []
    assert bd.idols == []
    assert bd.skills == []
    assert bd.stats == []


def test_parse_html_no_network():
    # ensure parse_html doesn't do network IO
    html = "<html><head><title>Test</title></head><body><h1>Test Build</h1></body></html>"
    parser = BuildParser()
    bd = parser.parse_html(html, "http://example.com/test")
    assert bd.name == "Test Build"
    assert bd.source_url == "http://example.com/test"
