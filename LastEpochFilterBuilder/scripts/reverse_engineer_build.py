"""Reverse-engineer saved build HTML to locate data sources.

Reads files from data/debug/builds/*.html and writes:
- data/debug/builds/reverse_engineering_report.json
- data/debug/builds/reverse_engineering_report.md

This is a static analysis only — no network.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List

from bs4 import BeautifulSoup


KEYS = [
    "equipment",
    "gear",
    "idols",
    "skills",
    "planner",
    "item",
    "affix",
    "blessing",
    "passive",
    "mastery",
    "class",
]


def analyze_script(tag) -> Dict[str, Any]:
    src = tag.get("src")
    t = tag.get("type") or "text/javascript"
    txt = tag.string or ""
    size = len(txt)
    lower = txt.lower()
    info = {
        "type": t,
        "src": src,
        "size": size,
        "has_json": False,
        "has_js": False,
        "has_fetch": "fetch(" in lower,
        "has_axios": "axios" in lower,
        "has_xhr": "xmlhttprequest" in lower,
        "has_graphql": "graphql" in lower,
        "keys": {},
    }
    # JSON detection: looks like starts with { or [ or contains :" or ':
    if re.search(r"\{\s*\"|\[\s*\{", txt) or txt.strip().startswith(('{', '[')):
        info["has_json"] = True
    # JS detection: presence of function, var, let, const, =>
    if re.search(r"\b(function|const|let|var|=>)\b", txt):
        info["has_js"] = True
    for k in KEYS:
        info["keys"][k] = bool(re.search(rf"\b{k}\b", lower))
    return info


def extract_data_attrs(soup) -> Dict[str, Dict[str, Any]]:
    counts: Dict[str, int] = {}
    examples: Dict[str, List[str]] = {}
    for el in soup.find_all(True):
        for k, v in el.attrs.items():
            if isinstance(k, str) and k.startswith("data-"):
                counts[k] = counts.get(k, 0) + 1
                examples.setdefault(k, [])
                if len(examples[k]) < 5:
                    examples[k].append(str(v))
    return {"counts": counts, "examples": examples}


def find_hidden_json(soup) -> List[Dict[str, Any]]:
    results = []
    tags = ["textarea", "template", "noscript", "input"]
    for tag in tags:
        for el in soup.find_all(tag):
            txt = el.string or el.get("value") or ""
            if not txt:
                continue
            txt_strip = txt.strip()
            if txt_strip.startswith("{") or txt_strip.startswith("["):
                # try parse
                try:
                    parsed = json.loads(txt_strip)
                    results.append({"tag": tag, "content": parsed})
                except Exception:
                    results.append({"tag": tag, "content": "invalid_json"})
    # also scan script tags with non-standard types
    for s in soup.find_all("script"):
        t = s.get("type") or "text/javascript"
        if t not in ("text/javascript", "module", "application/ld+json"):
            txt = s.string or ""
            if txt and (txt.strip().startswith("{") or txt.strip().startswith("[")):
                try:
                    parsed = json.loads(txt)
                    results.append({"tag": f"script[{t}]", "content": parsed})
                except Exception:
                    results.append({"tag": f"script[{t}]", "content": "invalid_json"})
    return results


def extract_links(soup) -> Dict[str, List[str]]:
    urls = []
    for a in soup.find_all("a", href=True):
        urls.append(a["href"])
    # classify
    out = {"images": [], "fonts": [], "css": [], "js": [], "api": [], "planner": [], "json": [], "graphql": [], "cdn": [], "build": []}
    for u in set(urls):
        low = u.lower()
        if any(low.endswith(ext) for ext in (".png", ".jpg", ".webp", ".gif", ".svg")):
            out["images"].append(u)
        if ".css" in low:
            out["css"].append(u)
        if ".js" in low:
            out["js"].append(u)
        if "/api/" in low or low.endswith('.json'):
            out["api"].append(u)
        if "/planner" in low or "community-builds" in low:
            out["planner"].append(u)
        if "graphql" in low:
            out["graphql"].append(u)
        if "/build-guides/" in low or "/build/" in low:
            out["build"].append(u)
        if "cdn" in low or "assets-ng" in low or "amazonaws" in low:
            out["cdn"].append(u)
        if ".json" in low:
            out["json"].append(u)
    return out


def find_build_id(soup) -> List[Dict[str, str]]:
    results = []
    # look for common keys in data attributes and scripts
    # data-le-id appears often
    for el in soup.find_all(True):
        for k, v in el.attrs.items():
            if isinstance(k, str) and ("buildid" in k.lower() or "build-id" in k.lower() or "data-le-id" == k.lower() or "guideid" in k.lower() or "guide-id" in k.lower()):
                results.append({"field": k, "value": str(v)})
    # search scripts for buildId or guideId
    for s in soup.find_all("script"):
        txt = s.string or ""
        for key in ("buildId", "guideId", "build_id", "guide_id", "guideid"):
            m = re.search(rf"{key}\s*[:=]\s*[\"']?([\w-]+)[\"']?", txt)
            if m:
                results.append({"field": key, "value": m.group(1)})
    return results


def search_keywords_context(soup, keywords: List[str], context_chars: int = 80) -> Dict[str, List[str]]:
    out = {}
    text = soup.get_text(separator=" ", strip=True)
    low = text.lower()
    for k in keywords:
        out[k] = []
        for m in re.finditer(re.escape(k), low):
            start = max(0, m.start() - context_chars)
            end = min(len(text), m.end() + context_chars)
            out[k].append(text[start:end])
    return out


def main():
    p = Path("data/debug/builds")
    p.mkdir(parents=True, exist_ok=True)
    files = list(p.glob("*.html"))
    reports = []
    for f in files:
        html = f.read_text(encoding="utf-8")
        soup = BeautifulSoup(html, "lxml")
        scripts = soup.find_all("script")
        script_details = [analyze_script(s) for s in scripts]
        data_attrs = extract_data_attrs(soup)
        hidden_json = find_hidden_json(soup)
        links = extract_links(soup)
        build_ids = find_build_id(soup)
        keywords_ctx = search_keywords_context(soup, ["equipment","gear","idols","skills","passive","affix","blessings","item"])

        report = {
            "file": str(f),
            "size": len(html),
            "total_scripts": len(scripts),
            "script_details": script_details,
            "json_ld_count": sum(1 for d in script_details if d.get("type") == "application/ld+json" and d.get("has_json")),
            "__NEXT_DATA__": bool(soup.select_one("script#__NEXT_DATA__") or soup.select_one("script[id='__NEXT_DATA__']")),
            "json_like_scripts": sum(1 for d in script_details if d.get("has_json") or d.get("has_js")),
            "data_attributes": data_attrs,
            "hidden_json": hidden_json,
            "links": links,
            "build_ids": build_ids,
            "keyword_contexts": keywords_ctx,
        }
        reports.append(report)

    out = p / "reverse_engineering_report.json"
    out.write_text(json.dumps(reports, ensure_ascii=False, indent=2), encoding="utf-8")

    # also write markdown summary
    md = ["# Reverse Engineering Report", ""]
    for r in reports:
        md.append(f"## File: {r['file']}")
        md.append(f"- size: {r['size']}")
        md.append(f"- total_scripts: {r['total_scripts']}")
        md.append(f"- json_ld_count: {r['json_ld_count']}")
        md.append(f"- __NEXT_DATA__: {r['__NEXT_DATA__']}")
        md.append(f"- total data-* attributes: {sum(r['data_attributes']['counts'].values())}")
        md.append(f"- total links: {sum(len(v) for v in r['links'].values())}")
        md.append("")
        md.append("### Script summary (first 10)")
        for s in r['script_details'][:10]:
            md.append(f"- type: {s['type']} src: {s['src']} size: {s['size']} has_json: {s['has_json']} has_fetch: {s['has_fetch']}")
        md.append("")
        md.append("### data-* samples")
        for k, ex in list(r['data_attributes']['examples'].items())[:10]:
            md.append(f"- {k}: {ex}")
        md.append("")
        md.append("### build ids found")
        for bid in r['build_ids']:
            md.append(f"- {bid}")
        md.append("")
    md_file = p / "reverse_engineering_report.md"
    md_file.write_text("\n".join(md), encoding="utf-8")
    print("Report written:", out, md_file)


if __name__ == '__main__':
    main()
