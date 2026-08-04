from app.parsers.build_parser import BuildParser
from bs4 import BeautifulSoup


def test_json_ld_single_object():
    html = '<script type="application/ld+json">{"name": "X"}</script>'
    soup = BeautifulSoup(html, "lxml")
    bp = BuildParser()
    objs = bp._extract_json_ld_objects(soup)
    assert isinstance(objs, list)
    assert objs and objs[0].get("name") == "X"


def test_json_ld_array():
    html = '<script type="application/ld+json">[{"name": "A"}, {"name": "B"}]</script>'
    soup = BeautifulSoup(html, "lxml")
    bp = BuildParser()
    objs = bp._extract_json_ld_objects(soup)
    assert len(objs) == 2


def test_json_ld_graph():
    html = '<script type="application/ld+json">{"@graph": [{"name":"G1"}, {"name":"G2"}]}</script>'
    soup = BeautifulSoup(html, "lxml")
    bp = BuildParser()
    objs = bp._extract_json_ld_objects(soup)
    assert len(objs) == 2


def test_multiple_json_ld_and_malformed():
    html = (
        '<script type="application/ld+json">{"name":"Good"}</script>'
        '<script type="application/ld+json">not json</script>'
        '<script type="application/ld+json">[{"name":"List"}]</script>'
    )
    soup = BeautifulSoup(html, "lxml")
    bp = BuildParser()
    objs = bp._extract_json_ld_objects(soup)
    # should contain Good and List
    names = [o.get("name") for o in objs]
    assert "Good" in names and "List" in names
