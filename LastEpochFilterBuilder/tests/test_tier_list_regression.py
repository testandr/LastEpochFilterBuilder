import json
from pathlib import Path

from app.parsers.tier_list_parser import TierListParser


def load_fixture(name: str) -> str:
    p = Path("tests/data/html") / name
    return p.read_text(encoding="utf-8")


def load_expected(name: str):
    p = Path("tests/data/json") / name
    return json.loads(p.read_text(encoding="utf-8"))


def to_plain(bs_list):
    return [
        {
            "name": b.name,
            "tier": b.tier,
            "class_name": b.class_name,
            "mastery": b.mastery,
            "url": b.url,
            "sources": b.sources,
            "author": b.author,
            "popularity_score": b.popularity_score,
        }
        for b in bs_list
    ]


def test_maxroll_corruption_regression():
    html = load_fixture("maxroll_corruption_real.html")
    parser = TierListParser()
    builds = parser.parse_html(html, "https://maxroll.gg/last-epoch/tierlists/corruption-tier-list", "corruption")
    expected = load_expected("maxroll_corruption_real.json")
    assert to_plain(builds) == expected


def test_maxroll_speed_farming_regression():
    html = load_fixture("maxroll_speed_farming_real.html")
    parser = TierListParser()
    builds = parser.parse_html(html, "https://maxroll.gg/last-epoch/tierlists/speed-farming-tier-list", "speed_farming")
    expected = load_expected("maxroll_speed_farming_real.json")
    assert to_plain(builds) == expected


def test_maxroll_bossing_regression():
    html = load_fixture("maxroll_bossing_real.html")
    parser = TierListParser()
    builds = parser.parse_html(html, "https://maxroll.gg/last-epoch/tierlists/bossing-tier-list", "bossing")
    expected = load_expected("maxroll_bossing_real.json")
    assert to_plain(builds) == expected
