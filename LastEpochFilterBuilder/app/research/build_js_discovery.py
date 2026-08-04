"""Discover JS bundles and client-side data sources for build pages.

This module analyzes saved HTML files (tests/data/html and data/debug/builds)
to locate <script src=> tags, classify bundles (main/page/chunk), search
inline JS for domain-specific tokens, and detect serialized hydration objects
like window.__NEXT_DATA__ or window.__APOLLO_STATE__.

Produces a markdown report at data/debug/build_data_location.md.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from bs4 import BeautifulSoup


@dataclass
class ScriptInfo:
    src: Optional[str]
    filename: Optional[str]
    inline: bool
    size: Optional[int]
    classification: Optional[str]


JS_KEYWORDS = [
    "equipment",
    "gear",
    "idol",
    "affix",
    "unique",
    "planner",
    "build",
    "skill",
    "passive",
    "blessing",
    "timeline",
    "echo",
    "last epoch",
]

HYDRATION_VARS = [
    "__INITIAL_STATE__",
    "__NEXT_DATA__",
    "__NUXT__",
    "__APOLLO_STATE__",
    "__PRELOADED_STATE__",
    "__DATA__",
    "__INITIAL_PROPS__",
]


def _find_html_files() -> List[Path]:
    roots = [Path("data") / "debug" / "builds", Path("tests") / "data" / "html"]
    files = []
    for r in roots:
        if not r.exists():
            continue
        files.extend(sorted(r.rglob("*.html")))
    return files


def _classify_src(src: str) -> str:
    s = src.lower()
    if "main" in s or "runtime" in s:
        return "main bundle"
    if "vendor" in s or "vendors" in s:
        return "vendor chunk"
    if "chunk" in s or ".chunk." in s or "/static/js/" in s:
        return "webpack chunk"
    if "page" in s or "build" in s or "guides" in s:
        return "page bundle"
    return "unknown"


def analyze() -> dict:
    files = _find_html_files()
    scripts_by_file = {}
    inline_keyword_hits = defaultdict(list)
    hydration_found = {}
    dynamic_imports = []

    for f in files:
        text = f.read_text(encoding="utf-8")
        soup = BeautifulSoup(text, "html.parser")
        scripts = []
        for s in soup.find_all("script"):
            src = s.get("src")
            inline = not bool(src)
            filename = None
            size = None
            classification = None
            if src:
                filename = src.split("/")[-1]
                classification = _classify_src(src)
                # if src is local file path, try to read it
                if not src.startswith("http://") and not src.startswith("https://"):
                    p = (f.parent / src).resolve()
                    if p.exists():
                        try:
                            size = p.stat().st_size
                        except Exception:
                            size = None
            else:
                text_content = s.string or ""
                size = len(text_content)
                # search for dynamic import calls
                if re.search(r"\bimport\([^)]*\)", text_content):
                    dynamic_imports.append(str(f))
                # scan for keywords in inline JS
                for kw in JS_KEYWORDS:
                    if re.search(r"\b" + re.escape(kw) + r"\b", text_content, flags=re.I):
                        inline_keyword_hits[f.name].append(kw)
                # detect hydration vars
                for hv in HYDRATION_VARS:
                    if hv in text_content or hv.replace("__", "window.__") in text_content:
                        hydration_found.setdefault(f.name, []).append(hv)

            scripts.append(ScriptInfo(src=src, filename=filename, inline=inline, size=size, classification=classification))

        # also check entire HTML for hydration variables (e.g., <script id="__NEXT_DATA__">)
        for hv in HYDRATION_VARS:
            if hv in text:
                hydration_found.setdefault(f.name, []).append(hv)

        scripts_by_file[f.name] = scripts

    # aggregate srcs
    all_srcs = []
    for v in scripts_by_file.values():
        for s in v:
            if s.src:
                all_srcs.append(s)

    # attempt to identify main/page bundles heuristically
    main_bundles = [s for s in all_srcs if s.classification == "main bundle"]
    page_bundles = [s for s in all_srcs if s.classification == "page bundle"]
    webpack_chunks = [s for s in all_srcs if s.classification == "webpack chunk"]

    # search for keywords inside any inline script across files
    keyword_summary = {k: [] for k in JS_KEYWORDS}
    for fname, kws in inline_keyword_hits.items():
        for kw in kws:
            keyword_summary[kw].append(fname)

    # build report
    report = {
        "files_analyzed": [str(p) for p in _find_html_files()],
        "script_summary": {fname: [s.__dict__ for s in lst] for fname, lst in scripts_by_file.items()},
        "main_bundles": [s.__dict__ for s in main_bundles],
        "page_bundles": [s.__dict__ for s in page_bundles],
        "webpack_chunks": [s.__dict__ for s in webpack_chunks],
        "dynamic_imports_in_files": sorted(set(dynamic_imports)),
        "inline_keyword_hits": dict(inline_keyword_hits),
        "keyword_summary": keyword_summary,
        "hydration_found": hydration_found,
    }

    outdir = Path("data") / "debug"
    outdir.mkdir(parents=True, exist_ok=True)
    with (outdir / "build_data_location.md").open("w", encoding="utf-8") as fh:
        fh.write("# JS Bundles and Build Data Location Report\n\n")
        fh.write(f"Files analyzed: {len(report['files_analyzed'])}\n\n")
        fh.write("## Script summary per file\n\n")
        for fname, scripts in report["script_summary"].items():
            fh.write(f"### {fname}\n")
            for s in scripts:
                fh.write(f"- src: {s['src']}, inline: {s['inline']}, size: {s['size']}, class: {s['classification']}\n")
            fh.write("\n")

        fh.write("## Bundles (heuristic)\n\n")
        fh.write(f"Main bundles: {[s['src'] for s in report['main_bundles']]}\n")
        fh.write(f"Page bundles: {[s['src'] for s in report['page_bundles']]}\n")
        fh.write(f"Webpack chunks: {[s['src'] for s in report['webpack_chunks']]}\n\n")

        fh.write("## Inline JS keyword hits\n\n")
        for fname, kws in report['inline_keyword_hits'].items():
            fh.write(f"- {fname}: {kws}\n")
        fh.write("\n")

        fh.write("## Hydration / Serialized state variables found\n\n")
        for f, vars in report['hydration_found'].items():
            fh.write(f"- {f}: {vars}\n")
        fh.write("\n")

        # conclusion heuristics
        fh.write("# Conclusion\n\n")
        if report['main_bundles'] or report['page_bundles'] or report['webpack_chunks']:
            fh.write("JS bundles exist; likely build data is present in bundles or built at runtime via React state.\n")
        else:
            fh.write("No external script bundles discovered in saved HTML fixtures.\n")

    return report


if __name__ == '__main__':
    r = analyze()
    print('Report written to data/debug/build_data_location.md')
