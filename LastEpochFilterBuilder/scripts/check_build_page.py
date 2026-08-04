"""Diagnostic script for a single build page.

Usage: python scripts/check_build_page.py

Fetches a build page, saves raw HTML to data/debug/builds/, and prints metadata found by BuildParser.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

# ensure project root in path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config.config_manager import ConfigManager
from app.utils.cache_manager import CacheManager
from app.utils.retry import RetryPolicy
from app.utils.http_client import HttpClient
from app.parsers.build_parser import BuildParser
from bs4 import BeautifulSoup


def run_check(update_fixtures: bool = False, client: Optional[Any] = None) -> None:
    cfg = ConfigManager().load()
    cache = CacheManager(base_path=cfg.cache.path, ttl_seconds=cfg.cache.ttl_seconds)
    rp = RetryPolicy(attempts=3, delay_seconds=cfg.maxroll.request_delay, backoff_factor=2.0)
    client = client or HttpClient(timeout=cfg.maxroll.timeout, user_agent=None, cache=cache, retry_policy=rp)

    # choose a sample build from config or default
    url = "https://maxroll.gg/last-epoch/build-guides/shadow-rend-bladedancer-guide"
    print(f"Fetching {url}")
    parser = BuildParser(http_client=client)
    try:
        resp = client.get(url, cache_subdir="builds", use_cache=True)
        html = resp.text
        status = resp.status_code

        outp = Path("data/debug/builds")
        outp.mkdir(parents=True, exist_ok=True)
        file = outp / "shadow-rend-bladedancer.html"
        file.write_text(html, encoding="utf-8")

        print(f"HTTP status: {status}")
        print(f"HTML size: {len(html)} chars")
        soup = BeautifulSoup(html, "lxml")
        title = soup.title.string.strip() if soup.title and soup.title.string else None
        print(f"Page title: {title}")

        # run parser
        bd = parser.parse_html(html, url)
        print("Parsed BuildDetails:")
        print(f" - name: {bd.name}")
        print(f" - class_name: {bd.class_name}")
        print(f" - mastery: {bd.mastery}")
        print(f" - author: {bd.author}")
        print(f" - source_url: {bd.source_url}")

        # create minimal fixture for tests: extract main content or article
        try:
            from app.parsers.selectors import SELECTORS as SELS
            main_selectors = SELS.get("build_page", {}).get("main_content", [])
            frag = None
            for ms in main_selectors:
                if not ms:
                    continue
                el = soup.select_one(ms)
                if el:
                    frag = str(el)
                    break
            if not frag:
                # fallback to article or main
                el = soup.find("article") or soup.find("main")
                frag = str(el) if el else soup.title.string if soup.title else ""

            fixtures_dir = Path("tests/data/html")
            fixtures_dir.mkdir(parents=True, exist_ok=True)
            fixture_file = fixtures_dir / "build_page_metadata_real.html"
            fixture_file.write_text(frag, encoding="utf-8")

            expected = {
                "name": bd.name,
                "class_name": bd.class_name,
                "mastery": bd.mastery,
                "author": bd.author,
                "source_url": bd.source_url,
            }
            json_dir = Path("tests/data/json")
            json_dir.mkdir(parents=True, exist_ok=True)
            json_file = json_dir / "build_page_metadata_real.json"
            candidate_file = json_dir / "build_page_metadata_real.candidate.json"
            import json

            candidate_file.write_text(json.dumps(expected, ensure_ascii=False, indent=2), encoding="utf-8")
            print("Saved candidate JSON (requires manual verification):", candidate_file)
            if update_fixtures:
                print("WARNING: Overwriting expected fixture with candidate. Manual verification required.")
                json_file.write_text(json.dumps(expected, ensure_ascii=False, indent=2), encoding="utf-8")
                print("Updated expected JSON at:", json_file)
        except Exception as e:
            print("Failed to create fixture:", e)

        # structured data checks
        has_json_ld = bool(soup.select_one("script[type='application/ld+json']"))
        has_next = bool(soup.select_one("script#__NEXT_DATA__") or soup.select_one("script[id='__NEXT_DATA__']"))
        print(f"Has JSON-LD: {has_json_ld}")
        print(f"Has __NEXT_DATA__: {has_next}")

        # basic diagnostics for presence of sections
        for sec in ("equipment_section", "idols_section", "skills_section"):
            sels = SELECTORS.get("build_page", {}).get(sec, [])
            found = False
            for s in sels:
                if s and soup.select_one(s):
                    found = True
                    break
            print(f"Section {sec} present: {found}")

    except Exception as e:
        print(f"Failed to fetch or parse: {e}")


if __name__ == '__main__':
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--update-fixtures", action="store_true", help="Overwrite expected JSON with candidate (manual verify)")
    args = p.parse_args()
    run_check(update_fixtures=args.update_fixtures)
