from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

from bs4 import BeautifulSoup

from app.parsers.base_parser import BaseParser
from app.parsers.selectors import SELECTORS
from app.dto.models import BuildDetails

logger = logging.getLogger("app.parsers.build_parser")


class BuildParser(BaseParser):
    """Parser for individual build pages.

    Extracts basic metadata: name, class_name, mastery, author, page title and structured data.
    """

    def parse(self, source: str) -> BuildDetails:
        if not self.http_client:
            raise RuntimeError("HttpClient not provided to BuildParser.parse")
        resp = self.http_client.get(source, cache_subdir="builds", use_cache=True)
        return self.parse_html(resp.text, source)

    def parse_html(self, html: str, source_url: str) -> BuildDetails:
        soup = BeautifulSoup(html, "lxml")

        title = self._extract_page_title(soup)

        structured = self._extract_structured_data(soup)

        # Prefer structured data name when available
        name = (structured.get("name") if isinstance(structured.get("name"), str) else None) or self._extract_build_name(soup) or title

        class_name = self._extract_class_name(soup) or structured.get("author", {}).get("jobTitle") if isinstance(structured.get("author"), dict) else None

        mastery = self._extract_mastery(soup)

        author = self._extract_author(soup) or (
            structured.get("author", {}).get("name") if isinstance(structured.get("author"), dict) else None
        )

        # clean trailing 'Guide' phrases from name if present
        try:
            import re

            if name:
                name = re.sub(r"(?i)\s*guide(\s*for.*)?$", "", name).strip()
        except Exception:
            pass

        bd = BuildDetails(
            name=name or "",
            class_name=class_name,
            mastery=mastery,
            author=author,
            items=[],
            idols=[],
            skills=[],
            stats=[],
            source_url=source_url,
        )
        return bd

    # --- helpers
    def _extract_page_title(self, soup: BeautifulSoup) -> Optional[str]:
        sels = SELECTORS.get("build_page", {}).get("page_title", [])
        for sel in sels:
            if not sel:
                continue
            if sel.startswith("meta"):
                # handle meta property selectors
                el = soup.select_one(sel)
                if el and el.get("content"):
                    return el.get("content").strip()
            else:
                el = soup.select_one(sel)
                if el and el.get_text(strip=True):
                    return el.get_text(strip=True)
        # fallback
        if soup.title and soup.title.string:
            return soup.title.string.strip()
        return None

    def _extract_structured_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        data: Dict[str, Any] = {}
        # JSON-LD: collect all objects
        try:
            objs = self._extract_json_ld_objects(soup)
            for obj in objs:
                if isinstance(obj, dict):
                    # merge top-level keys if not present
                    for k, v in obj.items():
                        if k not in data:
                            data[k] = v
            # no exception on malformed blocks
        except Exception:
            logger.exception("Error extracting JSON-LD objects")
        # __NEXT_DATA__
        try:
            el = soup.select_one("script#__NEXT_DATA__")
            if not el:
                el = soup.select_one("script[id='__NEXT_DATA__']")
            if el and el.string:
                try:
                    parsed = json.loads(el.string)
                    data["__NEXT_DATA__"] = parsed
                except json.JSONDecodeError:
                    logger.warning("Invalid __NEXT_DATA__ JSON ignored")
        except Exception:
            logger.exception("Error extracting __NEXT_DATA__")

        return data

    def _extract_json_ld_objects(self, soup: BeautifulSoup) -> list[dict[str, Any]]:
        """Extract all JSON-LD objects safely and return a flat list of dicts.

        Handles:
        - single object
        - array
        - @graph
        - multiple script tags
        - ignores invalid JSON blocks but continues
        """
        results: list[dict[str, Any]] = []
        for el in soup.select("script[type='application/ld+json']"):
            txt = el.string
            if not txt or not txt.strip():
                continue
            try:
                parsed = json.loads(txt)
            except json.JSONDecodeError:
                # try to recover by stripping leading/trailing non-json
                try:
                    # naive recovery: find first '{' or '[' and last '}' or ']'
                    s = txt
                    start = min((s.find('{') if '{' in s else len(s)), (s.find('[') if '[' in s else len(s)))
                    end = max((s.rfind('}') if '}' in s else -1), (s.rfind(']') if ']' in s else -1))
                    if 0 <= start < end:
                        parsed = json.loads(s[start:end+1])
                    else:
                        raise
                except Exception:
                    logger.warning("Invalid JSON-LD block ignored")
                    continue

            # parsed could be dict, list
            if isinstance(parsed, dict):
                # @graph support
                if "@graph" in parsed and isinstance(parsed["@graph"], list):
                    for item in parsed["@graph"]:
                        if isinstance(item, dict):
                            results.append(item)
                else:
                    results.append(parsed)
            elif isinstance(parsed, list):
                for item in parsed:
                    if isinstance(item, dict):
                        results.append(item)
        return results

    def _find_struct_selectors(self, key: str):
        """Helper to return selectors for build_page keys."""
        return SELECTORS.get("build_page", {}).get(key, [])

    def _extract_build_name(self, soup: BeautifulSoup) -> Optional[str]:
        sels = SELECTORS.get("build_page", {}).get("build_name", [])
        for sel in sels:
            if not sel:
                continue
            el = soup.select_one(sel)
            if el and el.get_text(strip=True):
                return el.get_text(strip=True)
        # fallback: h1
        h1 = soup.find("h1")
        if h1 and h1.get_text(strip=True):
            return h1.get_text(strip=True)
        return None

    def _extract_class_name(self, soup: BeautifulSoup) -> Optional[str]:
        sels = SELECTORS.get("build_page", {}).get("class_name", [])
        for sel in sels:
            if not sel:
                continue
            if sel.startswith("meta"):
                el = soup.select_one(sel)
                if el and el.get("content"):
                    return el.get("content").strip()
            else:
                el = soup.select_one(sel)
                if el and el.get_text(strip=True):
                    return el.get_text(strip=True)
        # heuristic: look for breadcrumbs or subtitle
        return None

    def _extract_mastery(self, soup: BeautifulSoup) -> Optional[str]:
        sels = SELECTORS.get("build_page", {}).get("mastery", [])
        for sel in sels:
            if not sel:
                continue
            el = soup.select_one(sel)
            if el and el.get_text(strip=True):
                return el.get_text(strip=True)
        return None

    def _extract_author(self, soup: BeautifulSoup) -> Optional[str]:
        sels = SELECTORS.get("build_page", {}).get("author", [])
        for sel in sels:
            if not sel:
                continue
            if sel.startswith("meta"):
                el = soup.select_one(sel)
                if el and el.get("content"):
                    return el.get("content").strip()
            else:
                el = soup.select_one(sel)
                if el and el.get_text(strip=True):
                    return el.get_text(strip=True)
        return None
