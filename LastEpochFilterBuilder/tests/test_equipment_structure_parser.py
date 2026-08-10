from pathlib import Path
from app.parsers.equipment_structure_parser import parse_html


def test_equipment_layout_fixture_basic():
    test_dir = Path(__file__).parent
    html_file = test_dir / "data" / "html" / "equipment_layout_fixture.html"
    html = html_file.read_text(encoding="utf-8")
    layout = parse_html(html)
    assert layout.container_selector is not None
    assert len(layout.slots) == 6
    # verify names and positions
    names_by_pos = {s.position: s.slot_name for s in layout.slots}
    assert names_by_pos[1] == "Helmet"
    assert names_by_pos[2] == "Chest"
    assert names_by_pos[3] == "Gloves"
    assert names_by_pos[4] == "Boots"
    assert names_by_pos[5] == "Amulet"
    assert names_by_pos[6] == "Ring"
