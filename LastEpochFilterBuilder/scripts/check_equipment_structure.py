"""Diagnostic script: inspect equipment structure in a local HTML fixture.

Usage: run from repo root (no network). It prints a short summary of the
discovered equipment container and slots.
"""
from pathlib import Path
from bs4 import BeautifulSoup

from app.parsers.equipment_structure_parser import parse_html


def short_attr_desc(attrs: dict) -> str:
    keys = sorted(attrs.keys())
    return ", ".join(keys)


def main() -> None:
    fixture = Path("tests/data/html/equipment_layout_fixture.html")
    if not fixture.exists():
        print("Fixture not found:", fixture)
        return
    html = fixture.read_text(encoding="utf-8")
    layout = parse_html(html)
    print("Equipment container found:", bool(layout.container_selector))
    print("Container selector:", layout.container_selector)
    print("Slots found:", len(layout.slots))
    names = [s.slot_name or "<unknown>" for s in layout.slots]
    print("Slot names:", names)
    print("Order (position -> slot_name):")
    for s in sorted(layout.slots, key=lambda x: (x.position or 0)):
        print(f"  {s.position} -> {s.slot_name} (tag attrs: {short_attr_desc(s.html_attributes)})")


if __name__ == "__main__":
    main()
