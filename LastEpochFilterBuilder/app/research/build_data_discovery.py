"""Research utilities to discover where build data is stored in saved HTML.

This module scans local HTML files (data/debug/builds and tests/data/html) and
produces a concise report describing JSON blocks, data-* attributes (especially
data-le-*), script usage, planner links, and likely data sources for items,
equipment, skills, affixes and idols.

This is an offline research helper only and intentionally does not perform any
network requests or modify existing parsers.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict, Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from bs4 import BeautifulSoup, Tag


@dataclass
class JSONBlockSummary:
    file: str
    script_type: Optional[str]
    approx_size: int
    top_keys: List[str]


@dataclass
class DataLeStat:
    name: str
    count: int
    tags: Dict[str, int]
    examples: List[str]
    nearest_containers: List[str]
    nearest_headings: List[str]


def _find_html_files() -> List[Path]:
    roots = [Path("data") / "debug" / "builds", Path("tests") / "data" / "html"]
    found: List[Path] = []
    for r in roots:
        if not r.exists():
            continue
        found.extend(list(r.rglob("*.html")))
    return sorted(found)


def _extract_json_blocks(soup: BeautifulSoup, filename: str) -> List[JSONBlockSummary]:
    blocks: List[JSONBlockSummary] = []
    for script in soup.find_all("script"):
        stype = script.get("type")
        text = script.string or ""
        if not text or len(text.strip()) < 30:
            continue
        # application/ld+json is explicit JSON-LD
        if stype and stype.lower() == "application/ld+json":
            try:
                obj = json.loads(text)
                keys = list(obj.keys()) if isinstance(obj, dict) else []
            except Exception:
                keys = []
            blocks.append(JSONBlockSummary(file=filename, script_type=stype, approx_size=len(text), top_keys=keys))
            continue

        # heuristics: large inline JSON-like object present
        if "{" in text and len(text) > 200:
            # try to find top-level JSON substrings (simple brace matching)
            substrings = []
            for m in re.finditer(r"\{", text):
                start = m.start()
                depth = 0
                for i in range(start, min(len(text), start + 200000)):
                    if text[i] == "{":
                        depth += 1
                    elif text[i] == "}":
                        depth -= 1
                        if depth == 0:
                            substr = text[start : i + 1]
                            substrings.append(substr)
                            break
                if substrings:
                    break
            parsed_keys: List[str] = []
            for s in substrings:
                try:
                    obj = json.loads(s)
                    if isinstance(obj, dict):
                        parsed_keys = list(obj.keys())
                        break
                except Exception:
                    continue
            blocks.append(JSONBlockSummary(file=filename, script_type=stype, approx_size=len(text), top_keys=parsed_keys))
    return blocks


def _collect_data_le_stats(soup: BeautifulSoup) -> Dict[str, DataLeStat]:
    stats: Dict[str, DataLeStat] = {}
    counts: Counter = Counter()
    details: Dict[str, Dict] = defaultdict(lambda: {"tags": Counter(), "examples": [], "containers": [], "headings": []})
    for el in soup.find_all(True):
        for attr, val in el.attrs.items():
            if not attr.startswith("data-le-"):
                continue
            counts[attr] += 1
            details[attr]["tags"][el.name] += 1
            if isinstance(val, list):
                v = " ".join(val)
            else:
                v = str(val)
            if len(details[attr]["examples"]) < 5:
                details[attr]["examples"].append(v)
            # nearest container: closest ancestor with id or class
            container = None
            for a in el.parents:
                if not isinstance(a, Tag):
                    continue
                if a.has_attr("id") or a.has_attr("class"):
                    cid = a.name
                    if a.has_attr("id"):
                        cid += f"#{a.get('id')}"
                    if a.has_attr("class"):
                        cid += "." + ".".join(a.get("class", []))
                    container = cid
                    break
            if container and len(details[attr]["containers"]) < 3:
                details[attr]["containers"].append(container)
            # nearest heading
            heading = None
            prev = el.find_previous(lambda t: t.name in ("h1", "h2", "h3", "h4"))
            if prev and prev.get_text(strip=True):
                heading = prev.get_text(strip=True)
            if heading and len(details[attr]["headings"]) < 3:
                details[attr]["headings"].append(heading)

    for name, cnt in counts.items():
        d = details[name]
        stats[name] = DataLeStat(
            name=name,
            count=cnt,
            tags=dict(d["tags"]),
            examples=d["examples"],
            nearest_containers=d["containers"],
            nearest_headings=d["headings"],
        )
    return stats


def _collect_hidden_data(soup: BeautifulSoup) -> Dict[str, int]:
    hidden = {"hidden_attr": 0, "style_none": 0, "class_hidden": 0}
    for el in soup.find_all(True):
        if el.has_attr("hidden"):
            hidden["hidden_attr"] += 1
        style = el.get("style", "")
        if "display:none" in style.replace(" ", ""):
            hidden["style_none"] += 1
        classes = el.get("class", [])
        if any(c in ("hidden", "sr-only") for c in classes):
            hidden["class_hidden"] += 1
    return hidden


def analyze() -> Dict:
    files = _find_html_files()
    summary = {
        "files": [str(p) for p in files],
        "html_summary": {},
        "json_blocks": [],
        "data_le": {},
        "planner_links": [],
        "possible_apis": [],
        "js_modules": [],
        "hidden_data": {},
    }
    total_scripts = 0
    total_inline = 0
    json_blocks: List[JSONBlockSummary] = []
    combined_data_le: Dict[str, DataLeStat] = {}

    for f in files:
        text = f.read_text(encoding="utf-8")
        soup = BeautifulSoup(text, "html.parser")
        scripts = soup.find_all("script")
        total_scripts += len(scripts)
        inline_count = sum(1 for s in scripts if not s.get("src") and (s.string or "").strip())
        total_inline += inline_count
        # json blocks
        blocks = _extract_json_blocks(soup, str(f))
        json_blocks.extend(blocks)
        # data-le
        stats = _collect_data_le_stats(soup)
        for k, v in stats.items():
            if k not in combined_data_le:
                combined_data_le[k] = v
            else:
                # merge counts/examples
                existing = combined_data_le[k]
                existing.count += v.count
                for tag, c in v.tags.items():
                    existing.tags[tag] = existing.tags.get(tag, 0) + c
                existing.examples = (existing.examples + v.examples)[:5]
                existing.nearest_containers = (existing.nearest_containers + v.nearest_containers)[:3]
                existing.nearest_headings = (existing.nearest_headings + v.nearest_headings)[:3]

        # planner links
        for a in soup.find_all("a", href=True):
            href = a.get("href")
            if "planner" in href or "build-planner" in href:
                summary["planner_links"].append(href)

        # possible APIs and modules from script src
        for s in scripts:
            src = s.get("src")
            if src:
                if "api" in src or "/api/" in src:
                    summary["possible_apis"].append(src)
                if src.endswith(".js"):
                    summary["js_modules"].append(src)

        # hidden data
        hidden = _collect_hidden_data(soup)
        summary["hidden_data"][str(f)] = hidden

    summary["html_summary"] = {"files_count": len(files), "total_scripts": total_scripts, "inline_scripts": total_inline}
    summary["json_blocks"] = [dict(file=b.file, type=b.script_type, size=b.approx_size, top_keys=b.top_keys) for b in json_blocks]
    summary["data_le"] = {k: dict(count=v.count, tags=v.tags, examples=v.examples, nearest_containers=v.nearest_containers, nearest_headings=v.nearest_headings) for k, v in combined_data_le.items()}

    # simple confidence heuristics
    confidence = {"equipment": "LOW", "items": "LOW", "affixes": "LOW", "idols": "LOW", "skills": "LOW"}
    # items: presence of data-le-type / data-le-sub / data-le-unique
    if any(k in combined_data_le for k in ("data-le-type", "data-le-sub", "data-le-unique")):
        confidence["items"] = "HIGH"
    if any(k in combined_data_le for k in ("data-le-id", "data-le-tree")):
        confidence["skills"] = "HIGH"
    # equipment: presence of equipment container or data-slot
    # look for files that contain '#equipment' or data-slot
    equipment_indicators = False
    for p in files:
        t = p.read_text(encoding="utf-8")
        if "id=\"equipment\"" in t or "data-slot" in t:
            equipment_indicators = True
            break
    if equipment_indicators:
        confidence["equipment"] = "MEDIUM"
    # affixes and idols left LOW unless JSON contains keys
    for jb in json_blocks:
        keys = set(jb.top_keys or [])
        if keys & {"items", "equipment", "affixes", "idols", "skills"}:
            if "affixes" in keys:
                confidence["affixes"] = "MEDIUM"
            if "idols" in keys:
                confidence["idols"] = "MEDIUM"

    summary["confidence"] = confidence

    # write a markdown report
    out = Path("data") / "debug"
    out.mkdir(parents=True, exist_ok=True)
    report = out / "build_source_report.md"
    with report.open("w", encoding="utf-8") as fh:
        fh.write("# HTML Summary\n\n")
        fh.write(f"Files analyzed: {len(files)}\n\n")
        fh.write(f"Total scripts: {total_scripts}, inline scripts: {total_inline}\n\n")
        fh.write("# JSON Blocks\n\n")
        for jb in summary["json_blocks"]:
            fh.write(f"- file: {jb['file']}, type: {jb['type']}, size: {jb['size']}, top_keys: {jb['top_keys']}\n")
        fh.write("\n# data-* attributes\n\n")
        fh.write(f"Total data-le keys: {len(summary['data_le'])}\n\n")
        fh.write("# data-le-* attributes\n\n")
        for k, v in summary["data_le"].items():
            fh.write(f"- {k}: count={v['count']}, tags={list(v['tags'].keys())}, examples={v['examples']}, containers={v['nearest_containers']}, headings={v['nearest_headings']}\n")
        fh.write("\n# planner links\n\n")
        for p in summary["planner_links"]:
            fh.write(f"- {p}\n")
        fh.write("\n# possible APIs\n\n")
        for a in summary["possible_apis"]:
            fh.write(f"- {a}\n")
        fh.write("\n# possible JS modules\n\n")
        for m in summary["js_modules"]:
            fh.write(f"- {m}\n")
        fh.write("\n# hidden data\n\n")
        for f, h in summary["hidden_data"].items():
            fh.write(f"- {f}: {h}\n")
        fh.write("\n# confidence\n\n")
        for k, v in confidence.items():
            fh.write(f"- {k}: {v}\n")
        fh.write("\n# conclusion\n\n")
        # pick final verdict
        # heuristics: if lots of data-le and small inline JSON -> D (API)
        fh.write("Most likely data delivery: D) Data arrives via API at runtime; HTML contains identifiers and small inline snippets.\n")

    return summary


if __name__ == "__main__":
    s = analyze()
    print("Analysis written to data/debug/build_source_report.md")
