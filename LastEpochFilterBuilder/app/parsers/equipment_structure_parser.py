"""Equipment structure discovery from build HTML.

This module provides a simple HTML-only analyzer that locates the equipment
container and discovers equipment slots. It purposely does NOT parse item
details, affixes, idols or skills.

Interface:
    parse_html(html: str) -> EquipmentLayout

Heuristics used:
- Find equipment container using selectors from selectors.SELECTORS['build_page']['equipment_section']
- Within the container, consider child elements as candidate slots when they
  have a data-slot or data-position attribute, or a class name containing
  'slot' or 'equipment', or contain a child with class 'slot-name'.
- Slot name is taken from (in order): data-slot, descendant with class 'slot-name',
  aria-label/title attribute, or the element's text (trimmed). Position is taken
  from data-position attribute when present or the discovery index.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from bs4 import BeautifulSoup, Tag

from app.parsers.selectors import SELECTORS
from app.dto.models import EquipmentLayout, EquipmentSlot


def _first_matching_container(soup: BeautifulSoup) -> Optional[Tag]:
    candidates = SELECTORS.get("build_page", {}).get("equipment_section", [])
    for sel in candidates:
        found = soup.select_one(sel)
        if found:
            return found
    return None


def _is_slot_element(el: Tag) -> bool:
    # data attributes
    if el.has_attr("data-slot") or el.has_attr("data-position"):
        return True
    # classes that often indicate slots
    cls = " ".join(el.get("class", []))
    if "slot" in cls or "equipment-slot" in cls or "equipment" == el.name:
        return True
    # contains an explicit slot-name child
    if el.select_one(".slot-name"):
        return True
    return False


def _extract_slot_name(el: Tag) -> Optional[str]:
    if el.has_attr("data-slot"):
        return el.get("data-slot")
    name_el = el.select_one(".slot-name")
    if name_el and name_el.get_text(strip=True):
        return name_el.get_text(strip=True)
    for attr in ("aria-label", "title"):
        if el.has_attr(attr) and el.get(attr).strip():
            return el.get(attr).strip()
    # fallback: small text content
    text = el.get_text(separator=" ", strip=True)
    if text and len(text) < 40:
        return text
    return None


def parse_html(html: str) -> EquipmentLayout:
    """Parse HTML and return EquipmentLayout describing container and slots.

    The function is defensive and works with incomplete or noisy HTML.
    """
    soup = BeautifulSoup(html, "html.parser")
    container = _first_matching_container(soup)
    layout = EquipmentLayout(container_selector=None)
    if container is None:
        return layout

    # try to determine a selector string for diagnostics
    # prefer ID or class
    selector = None
    if container.has_attr("id"):
        selector = f"#{container.get('id')}"
    elif container.has_attr("class"):
        selector = "." + ".".join(container.get("class", []))
    layout.container_selector = selector

    # find candidate slot elements among direct children and nearby descendants
    candidates: List[Tag] = []
    # direct children first
    for child in container.find_all(recursive=False):
        if isinstance(child, Tag) and _is_slot_element(child):
            candidates.append(child)

    # if none, look deeper but limit depth to avoid huge scans
    if not candidates:
        for child in container.find_all(limit=50):
            if isinstance(child, Tag) and _is_slot_element(child):
                candidates.append(child)

    # build slots
    slots: List[EquipmentSlot] = []
    for idx, el in enumerate(candidates, start=1):
        slot_name = _extract_slot_name(el)
        position = None
        if el.has_attr("data-position"):
            try:
                position = int(el.get("data-position"))
            except Exception:
                position = None
        else:
            position = idx
        slot = EquipmentSlot(
            slot_name=slot_name,
            html_fragment=str(el)[:1000],
            html_attributes=dict(el.attrs),
            position=position,
        )
        slots.append(slot)

    layout.slots = slots
    return layout
