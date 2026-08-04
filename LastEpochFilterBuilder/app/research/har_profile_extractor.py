"""HAR-based extractor for Maxroll planner profiles and game data.

Utilities to locate planner profile responses and the large game data JSON
inside a HAR file (or equivalent JSON export), decode response bodies, handle
base64 encoding, and write parsed JSON to disk under data/debug/network/extracted.

Also provides small research DTOs and an HTML helper to extract data-le-profile ids.
"""
from __future__ import annotations

import base64
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class HarEndpointMatch:
    url: str
    status: int
    content_text: Optional[str]


@dataclass
class PlannerProfileSummary:
    profile_metadata: Dict[str, Any]
    build_data: Dict[str, Any]


@dataclass
class GameDataSectionSummary:
    top_keys: List[str]
    sizes: Dict[str, int]


@dataclass
class EntityMappingResult:
    planner_key: str
    planner_entry: Dict[str, Any]
    game_entry: Optional[Dict[str, Any]]
    confidence: float


PLANNER_PATTERN = re.compile(r"https?://planners\.maxroll\.gg/profiles/load/le/([A-Za-z0-9_-]+)")
GAMEDATA_PATTERN = re.compile(r"https?://assets-ng\.maxroll\.gg/leplanner/game/data\.json")


def _safe_load_json(text: str) -> Optional[Any]:
    try:
        return json.loads(text)
    except Exception:
        return None


def _decode_content(content: Dict[str, Any]) -> Optional[str]:
    # HAR response.content can have fields: text, encoding
    if not content:
        return None
    text = content.get("text")
    if text is None:
        return None
    encoding = content.get("encoding")
    if encoding == "base64":
        try:
            data = base64.b64decode(text)
            # try to decode as utf-8 ignoring errors
            return data.decode("utf-8", errors="replace")
        except Exception:
            return None
    return text


def extract_from_har(har_path: Path) -> Dict[str, HarEndpointMatch]:
    har = json.loads(har_path.read_text(encoding="utf-8"))
    entries = []
    # HAR may have log.entries
    if isinstance(har, dict) and "log" in har and "entries" in har["log"]:
        entries = har["log"]["entries"]
    elif isinstance(har, dict) and "entries" in har:
        entries = har["entries"]
    else:
        # assume har_path itself is an array of entries
        if isinstance(har, list):
            entries = har

    found: Dict[str, HarEndpointMatch] = {}

    for e in entries:
        request = e.get("request", {})
        response = e.get("response", {})
        url = request.get("url") or request.get("method") or ""
        if not url:
            continue
        # check planner pattern
        m = PLANNER_PATTERN.search(url)
        if m:
            text = _decode_content(response.get("content", {}))
            status = response.get("status", 0)
            found_key = f"planner:{m.group(1)}"
            found[found_key] = HarEndpointMatch(url=url, status=status, content_text=text)
            continue
        if GAMEDATA_PATTERN.search(url):
            text = _decode_content(response.get("content", {}))
            status = response.get("status", 0)
            found["game_data"] = HarEndpointMatch(url=url, status=status, content_text=text)

    return found


def save_extracted(found: Dict[str, HarEndpointMatch], out_dir: Path) -> Tuple[Optional[Path], Optional[Path]]:
    out_dir.mkdir(parents=True, exist_ok=True)
    planner_path = None
    game_data_path = None
    # prefer planner with any key
    for k, match in found.items():
        if k.startswith("planner:"):
            # parse JSON text
            if not match.content_text or match.status != 200:
                continue
            parsed = _safe_load_json(match.content_text)
            if parsed is None:
                continue
            # field 'data' is a JSON-encoded string per analysis
            data_field = parsed.get("data")
            build_data = None
            if isinstance(data_field, str):
                build_data = _safe_load_json(data_field)
            elif isinstance(data_field, dict):
                build_data = data_field
            planner_obj = {
                "profile_metadata": {k: v for k, v in parsed.items() if k != "data"},
                "build_data": build_data,
            }
            planner_path = out_dir / "planner_profile.json"
            planner_path.write_text(json.dumps(planner_obj, ensure_ascii=False, indent=2), encoding="utf-8")

    # game data
    g = found.get("game_data")
    if g and g.status == 200 and g.content_text:
        parsed = _safe_load_json(g.content_text)
        if parsed is not None:
            game_data_path = out_dir / "game_data.json"
            # write compact to avoid huge indentation
            game_data_path.write_text(json.dumps(parsed, ensure_ascii=False), encoding="utf-8")

    return planner_path, game_data_path


def extract_profile_ids_from_html(html: str) -> List[str]:
    ids: List[str] = []
    # find data-le-profile attributes
    for m in re.finditer(r"data-le-profile\s*=\s*\"([A-Za-z0-9_-]+)\"", html):
        val = m.group(1)
        if val not in ids:
            ids.append(val)
    return ids


def map_planner_items_to_game(planner_build_data: Dict[str, Any], game_data: Dict[str, Any], sample_keys: List[str]) -> List[EntityMappingResult]:
    # planner_build_data contains profiles -> items etc.
    res: List[EntityMappingResult] = []
    items_dict = game_data.get("items") if isinstance(game_data, dict) else None
    if not items_dict:
        return res
    # iterate sample keys which are planner keys present under build_data['items']
    planner_items = planner_build_data.get("items") or {}
    for key in sample_keys:
        p_entry = planner_items.get(key)
        game_entry = None
        confidence = 0.0
        if isinstance(p_entry, dict):
            # try match by base or id fields
            for candidate_key, candidate in items_dict.items():
                if not isinstance(candidate, dict):
                    continue
                # heuristic: match by id or base
                if p_entry.get("base") and candidate.get("base_id") and str(candidate.get("base_id")) == str(p_entry.get("base")):
                    game_entry = candidate
                    confidence = 0.9
                    break
                if p_entry.get("unique") and candidate.get("unique_id") and str(candidate.get("unique_id")) == str(p_entry.get("unique")):
                    game_entry = candidate
                    confidence = 0.95
                    break
        res.append(EntityMappingResult(planner_key=key, planner_entry=p_entry or {}, game_entry=game_entry, confidence=confidence))
    return res
