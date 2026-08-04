"""Diagnostic script to check Maxroll tier list pages and TierListParser behavior.

Usage:
    python scripts/check_tier_lists.py

This script:
- loads configuration via ConfigManager
- creates CacheManager, RetryPolicy, HttpClient
- requests tier list pages (uses cache)
- saves responses to data/debug/tier_lists/
- runs TierListParser.parse_html on saved HTML and prints summary
"""
from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Dict

import sys
from pathlib import Path as _Path

# Ensure repo root is in sys.path for imports when running as script
_ROOT = _Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from app.config.config_manager import ConfigManager
from app.utils.cache_manager import CacheManager
from app.utils.retry import RetryPolicy
from app.utils.http_client import HttpClient
from app.parsers.tier_list_parser import TierListParser
from bs4 import BeautifulSoup


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("scripts.check_tier_lists")


def source_name_for_url(url: str) -> str:
    if "corruption-tier-list" in url:
        return "corruption"
    if "speed-farming-tier-list" in url:
        return "speed_farming"
    if "bossing-tier-list" in url:
        return "bossing"
    # fallback to safe name
    return url.replace("https://", "").replace("/", "_")[:50]


def ensure_debug_path() -> Path:
    p = Path("data/debug/tier_lists")
    p.mkdir(parents=True, exist_ok=True)
    return p


def summarize_html(html: str) -> Dict[str, object]:
    soup = BeautifulSoup(html, "lxml")
    title = soup.title.string.strip() if soup.title and soup.title.string else None
    has_s_tier = "s tier" in html.lower() or "s-tier" in html.lower()
    return {"title": title, "has_s_tier": has_s_tier, "length": len(html)}


def main():
    cfgm = ConfigManager()
    cfg = cfgm.load()

    cache_cfg = cfg.cache
    dbg = ensure_debug_path()

    cache = CacheManager(base_path=cache_cfg.path, ttl_seconds=cache_cfg.ttl_seconds)
    rp = RetryPolicy(attempts=3, delay_seconds=cfg.maxroll.request_delay, backoff_factor=2.0)
    client = HttpClient(timeout=cfg.maxroll.timeout, user_agent=None, cache=cache, retry_policy=rp)

    parser = TierListParser(http_client=client)

    results = []
    for url in cfg.maxroll.urls:
        name = source_name_for_url(url)
        print(f"\n=== Checking {name} ({url}) ===")
        try:
            resp = client.get(url, cache_subdir="tier_lists", use_cache=True)
            html = resp.text
            status = resp.status_code
            summary = summarize_html(html)

            # save debug html
            outp = dbg / f"{name}.html"
            outp.write_text(html, encoding="utf-8")

            # run parser
            builds = parser.parse_html(html, url, name)

            print(f"URL: {url}")
            print(f"HTTP status: {status}")
            print(f"HTML size: {summary['length']} chars")
            print(f"<title>: {summary['title']}")
            print(f"Contains 'S Tier' text: {summary['has_s_tier']}")
            print(f"BuildSummary found: {len(builds)}")
            for b in builds[:10]:
                print(f" - {b.name} -> {b.url}")

            results.append({"name": name, "url": url, "status": status, "count": len(builds)})

            # create minimal fixture: extract first Tierlist block if present
            try:
                soup = BeautifulSoup(html, "lxml")
                tier_blocks = soup.select("[class*='Tierlist']")
                if tier_blocks:
                    frag = str(tier_blocks[0])
                    fixtures_dir = Path("tests/data/html")
                    fixtures_dir.mkdir(parents=True, exist_ok=True)
                    fixture_file = fixtures_dir / f"maxroll_{name}_real.html"
                    fixture_file.write_text(frag, encoding="utf-8")

                    # expected JSON
                    expected = [
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
                        for b in builds
                    ]
                    json_dir = Path("tests/data/json")
                    json_dir.mkdir(parents=True, exist_ok=True)
                    json_file = json_dir / f"maxroll_{name}_real.json"
                    import json

                    json_file.write_text(json.dumps(expected, ensure_ascii=False, indent=2), encoding="utf-8")
                    print(f"Saved fixture and expected JSON for {name}")
            except Exception:
                logger.exception("Failed to create regression fixture for %s", name)

        except Exception as e:
            logger.exception("Failed to fetch or parse %s", url)
            print(f"Error for {url}: {e}")
        # be polite
        time.sleep(cfg.maxroll.request_delay)

    print("\n=== Summary ===")
    for r in results:
        print(f"{r['name']}: {r['status']} - {r['count']} builds")


if __name__ == "__main__":
    main()
