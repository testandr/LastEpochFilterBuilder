"""Analyze every <script> tag in saved build HTML and report details.

Reads files from data/debug/builds/*.html (no network). Prints per-script summary and
writes data/debug/builds/script_analysis.json and .md
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List

from bs4 import BeautifulSoup


KEYS = [
    "fetch(",
    "axios",
    "xmlhttprequest",
    "graphql",
    "planner",
    "equipment",
    "item",
    "affix",
    "idol",
    "passive",
    "blessing",
    "mastery",
    "class",
]


def analyze_file(path: Path) -> Dict[str, Any]:
    html = path.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "lxml")
    scripts = soup.find_all("script")
    details: List[Dict[str, Any]] = []
    for i, s in enumerate(scripts, start=1):
        stype = s.get("type") or "text/javascript"
        src = s.get("src")
        txt = s.string or ""
        size = len(txt)
        low = txt.lower()
        info = {
            "index": i,
            "type": stype,
            "src": src,
            "size": size,
            "has_json_like": bool(re.search(r"\{\s*\"|\[\s*\{", txt)),
            "has_js_code": bool(re.search(r"\b(function|const|let|var|=>)\b", txt)),
            "has_fetch": "fetch(" in low,
            "has_axios": "axios" in low,
            "has_xhr": "xmlhttprequest" in low,
            "has_graphql": "graphql" in low,
            "mentions": {k: (k in low) for k in ["planner", "equipment", "gear", "item", "affix", "idol", "skill", "passive", "blessing", "mastery", "class"]},
            "sample": (txt[:200] + "...") if size > 200 else txt,
        }
        details.append(info)

    # search for JSON-like globals
    globals_found = {}
    patterns = [r"window\.[A-Za-z0-9_]+", r"__NEXT_DATA__", r"__INITIAL_STATE__", r"__APOLLO_STATE__", r"__PRELOADED_STATE__", r"__NUXT__", r"const\s+[A-Za-z0-9_]+\s*=\s*\{"]
    for p in patterns:
        globals_found[p] = bool(re.search(p, html))

    # extract urls
    urls = set(re.findall(r"https?://[\w\-./?=&%]+", html))
    api_urls = [u for u in urls if "/api/" in u or u.endswith('.json') or 'graphql' in u.lower()]

    # data-* attributes
    data_attrs = {}
    for el in soup.find_all(True):
        for k, v in el.attrs.items():
            if isinstance(k, str) and k.startswith("data-"):
                data_attrs.setdefault(k, 0)
                data_attrs[k] += 1

    # build id heuristics
    build_ids = []
    for m in re.finditer(r"(buildId|guideId|build_id|guide_id|data-le-id)[:=\"'\s]*([A-Za-z0-9_-]+)", html):
        build_ids.append({"key": m.group(1), "value": m.group(2)})

    return {
        "file": str(path),
        "html_size": len(html),
        "script_count": len(scripts),
        "scripts": details,
        "globals_found": globals_found,
        "api_urls": api_urls,
        "data_attributes_counts": data_attrs,
        "build_ids": build_ids,
    }


def main():
    p = Path("data/debug/builds")
    p.mkdir(parents=True, exist_ok=True)
    files = list(p.glob("*.html"))
    all_reports = []
    for f in files:
        report = analyze_file(f)
        all_reports.append(report)
        # print per-file summary
        print(f"File: {f}")
        print(f" HTML size: {report['html_size']}")
        print(f" Script count: {report['script_count']}")
        for s in report['scripts']:
            print(f"  [{s['index']}] type={s['type']} src={s['src']} size={s['size']} json_like={s['has_json_like']} fetch={s['has_fetch']} axios={s['has_axios']} xhr={s['has_xhr']} graphql={s['has_graphql']}")
        print(f" data-* keys: {len(report['data_attributes_counts'])}")
        print(f" build ids heuristics: {report['build_ids']}")
        print("")

    out = p / "reverse_engineering_report.json"
    out.write_text(json.dumps(all_reports, ensure_ascii=False, indent=2), encoding="utf-8")
    md = p / "reverse_engineering_report.md"
    md.write_text("# Reverse engineering script analysis.\nSee JSON for details.", encoding="utf-8")
    print("Wrote reports to", out)


if __name__ == '__main__':
    main()
