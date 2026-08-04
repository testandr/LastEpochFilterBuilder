from app.parsers.equipment_structure_parser import parse_html


def test_equipment_layout_fixture_basic():
    html = open("tests/data/html/equipment_layout_fixture.html", "r", encoding="utf-8").read()
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
