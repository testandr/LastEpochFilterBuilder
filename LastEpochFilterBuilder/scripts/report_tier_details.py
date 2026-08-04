"""Detailed report for tier list fixtures saved in data/debug/tier_lists.

This script loads saved HTML files and uses TierListParser helper methods
to report exact counts per tier section and the S-Tier results.

Run with:
  python scripts/report_tier_details.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# ensure repo root on path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.parsers.tier_list_parser import TierListParser
from app.parsers.selectors import SELECTORS


def source_name_for_file(fname: str) -> str:
    if "corruption" in fname:
        return "corruption"
    if "speed_farming" in fname:
        return "speed_farming"
    if "bossing" in fname:
        return "bossing"
    return fname


def main():
    dbg = Path("data/debug/tier_lists")
    files = list(dbg.glob("*.html"))
    if not files:
        print("No debug HTML files found in data/debug/tier_lists")
        return

    parser = TierListParser()

    for f in sorted(files):
        html = f.read_text(encoding="utf-8")
        source = source_name_for_file(f.name)
        url = "https://maxroll.gg/last-epoch/tierlists/" + source.replace("_", "-") + "-tier-list"
        print(f"\n{source.title().replace('_', ' ')} Tier List")
        # parse base containers
        base_containers = parser._find_tier_sections(__import__('bs4').BeautifulSoup(html, 'lxml'))
        print(f"HTTP: 200")

        # Now examine each base container and collect unique section signatures
        sections = []
        seen_section_signatures = set()
        for base in base_containers:
            labels = parser._find_label_elements(base)
            if not labels:
                continue
            for lab in labels:
                tier_name = lab.get_text(strip=True)
                # compute card URLs by scanning siblings after the label until next label
                # this avoids relying on parser internal card element shape
                card_urls = []
                for sib in lab.find_next_siblings():
                    # stop if this sibling contains another label element
                    stop = False
                    for lab_sel in SELECTORS.get("tier_list", {}).get("tier_label", []):
                        try:
                            if sib.select_one(lab_sel):
                                stop = True
                                break
                        except Exception:
                            continue
                    if stop:
                        break

                    # collect anchors inside this sibling
                    try:
                        for a in sib.find_all('a', href=True):
                            href = a.get('href')
                            if '/last-epoch/build-guides/' in href:
                                card_urls.append(href)
                    except Exception:
                        continue

                signature = tuple(sorted(set(card_urls)))
                if signature in seen_section_signatures:
                    # duplicate rendering of same section, skip
                    continue
                seen_section_signatures.add(signature)

                sections.append({"tier": tier_name, "count": len(card_urls)})

        # Print overall sections count and per-section counts
        print(f"Tier sections found: {len(sections)}")
        for sec in sections:
            norm = parser._normalize_tier(sec['tier'])
            print(f"\nTier {norm}: {sec['count']}")

        # final merged BuildSummary list from parse_html (this performs merging)
        final_builds = parser.parse_html(html, url, source)

        print(f"\nAfter S-Tier filtering: {len(final_builds)}")
        print(f"\nS-Tier builds:")
        for i, b in enumerate(final_builds, start=1):
            print(f"{i}. {b.name} — {b.url}")

        # Additional checks
        # No A/B/C/D build should be in final_builds
        other_tiers = [b for b in final_builds if parser._normalize_tier(b.tier) != "S"]
        if other_tiers:
            print("\nERROR: Some returned builds are not S tier")

        # check duplicates
        urls = [b.url for b in final_builds]
        dup_urls = [u for u in urls if urls.count(u) > 1]
        if dup_urls:
            print("\nERROR: Duplicate URLs found in S-Tier builds:")
            for d in sorted(set(dup_urls)):
                print(d)


if __name__ == '__main__':
    main()
