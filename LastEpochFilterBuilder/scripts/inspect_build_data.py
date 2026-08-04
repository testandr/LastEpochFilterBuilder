"""Inspect saved build HTML for script tags and potential embedded JSON data.

Outputs a JSON report to data/debug/builds/inspection_report.json
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from bs4 import BeautifulSoup


def inspect_file(path: Path) -> dict:
    html = path.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "lxml")

    scripts = soup.find_all("script")
    total_scripts = len(scripts)

    types = {}
    json_ld_objects = 0
    next_data_present = False
    json_like_scripts = 0
    keys_found = {k: 0 for k in ["equipment","gear","idols","skills","planner","item","affix","blessings"]}
    api_links = set()
    data_attrs = []
    iframes = []
    planner_links = []

    for s in scripts:
        t = s.get("type") or "text/javascript"
        types[t] = types.get(t, 0) + 1
        txt = s.string or ""
        if t == "application/ld+json":
            try:
                parsed = json.loads(txt)
                # count graph nodes
                if isinstance(parsed, list):
                    json_ld_objects += len(parsed)
                elif isinstance(parsed, dict) and "@graph" in parsed and isinstance(parsed["@graph"], list):
                    json_ld_objects += len(parsed["@graph"])
                else:
                    json_ld_objects += 1
            except Exception:
                # ignore malformed
                pass
        if s.get("id") == "__NEXT_DATA__" or s.get("id") == "next-data" or s.get("id") == "__NEXT_DATA__":
            next_data_present = True
        # quick JSON-like heuristic
        if txt and (txt.strip().startswith("{") or txt.strip().startswith("[")):
            json_like_scripts += 1
        # search for keys
        for k in keys_found.keys():
            if re.search(r"\b" + re.escape(k) + r"\b", txt, re.IGNORECASE):
                keys_found[k] += 1
        # find potential API urls
        for m in re.finditer(r"https?://[\w./?-]+", txt or ""):
            u = m.group(0)
            if "/api/" in u or u.endswith('.json'):
                api_links.add(u)

    # data-* attributes
    for el in soup.find_all(True):
        for k, v in el.attrs.items():
            if isinstance(k, str) and k.startswith("data-"):
                data_attrs.append({"attr": k, "value": v})

    for ifr in soup.find_all("iframe"):
        src = ifr.get("src")
        if src:
            iframes.append(src)

    # find links to planner/build planner
    for a in soup.find_all("a", href=True):
        href = a.get('href')
        if href and ("planner" in href.lower() or "build-planner" in href.lower() or "/planner" in href.lower()):
            planner_links.append(href)

    report = {
        "file": str(path),
        "total_scripts": total_scripts,
        "script_types": types,
        "json_ld_objects": json_ld_objects,
        "__NEXT_DATA__": next_data_present,
        "json_like_scripts": json_like_scripts,
        "keys_found": keys_found,
        "api_links": list(sorted(api_links)),
        "data_attributes": data_attrs[:50],
        "iframes": iframes,
        "planner_links": planner_links,
    }
    return report


def main():
    p = Path("data/debug/builds")
    p.mkdir(parents=True, exist_ok=True)
    files = list(p.glob("*.html"))
    if not files:
        print("No build HTML found in data/debug/builds. Run check_build_page first.")
        return
    reports = []
    for f in files:
        r = inspect_file(f)
        reports.append(r)

    out = p / "inspection_report.json"
    out.write_text(json.dumps(reports, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Inspection complete. Report written to:", out)


if __name__ == '__main__':
    main()
