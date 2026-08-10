import json
from dataclasses import asdict
from pathlib import Path

import pytest

from app.parsers.tier_list_parser import TierListParser, merge_build_summaries


def load_fixture(name: str) -> str:
    test_dir = Path(__file__).parent
    p = test_dir / "data" / "html" / name
    return p.read_text(encoding="utf-8")


def load_expected(name: str):
    test_dir = Path(__file__).parent
    p = test_dir / "data" / "json" / name
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


def test_standard_tier_list():
    html = load_fixture("tier_list_standard.html")
    parser = TierListParser()
    builds = parser.parse_html(html, "https://maxroll.gg/last-epoch/tierlists/corruption-tier-list", "corruption")
    expected = load_expected("tier_list_standard.json")
    assert to_plain(builds) == expected


def test_alternative_tier_list():
    html = load_fixture("tier_list_alternative.html")
    parser = TierListParser()
    builds = parser.parse_html(html, "https://maxroll.gg/last-epoch/tierlists/speed-farming-tier-list", "speed_farming")
    expected = load_expected("tier_list_alternative.json")
    assert to_plain(builds) == expected


def test_broken_tier_list():
    html = load_fixture("tier_list_broken.html")
    parser = TierListParser()
    builds = parser.parse_html(html, "https://maxroll.gg/last-epoch/tierlists/bossing-tier-list", "bossing")
    expected = load_expected("tier_list_broken.json")
    assert to_plain(builds) == expected


def test_merge_duplicates():
    b1 = parser_build("B", "https://example.com/b", "s1")
    b2 = parser_build("B", "https://example.com/b", "s2")
    merged = merge_build_summaries([b1, b2])
    assert len(merged) == 1
    assert set(merged[0].sources) == {"s1", "s2"}


def parser_build(name, url, source):
    from app.dto.models import BuildSummary

    return BuildSummary(name=name, tier="S", url=url, sources=[source])
