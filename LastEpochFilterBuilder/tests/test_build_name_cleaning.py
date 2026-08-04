from bs4 import BeautifulSoup

from app.parsers.tier_list_parser import TierListParser


def extract_name_from_html(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    card = soup.select_one(".card") or soup.find()
    parser = TierListParser()
    return parser._extract_build_name(card)


def test_name_with_go_to_build():
    html = '<div class="card"><a href="/last-epoch/build-guides/x">Shadow Rend Bladedancer<span class="cta">Go To Build</span></a></div>'
    assert extract_name_from_html(html) == "Shadow Rend Bladedancer"


def test_name_with_decorative_symbol():
    html = '<div class="card"><a href="/last-epoch/build-guides/x">Flay Mana Lich *<span class="cta">Go To Build</span></a></div>'
    assert extract_name_from_html(html) == "Flay Mana Lich"


def test_name_with_parentheses():
    html = '<div class="card"><a href="/last-epoch/build-guides/x">Ballista Falconer (ZHP)<span class="cta">Go To Build</span></a></div>'
    assert extract_name_from_html(html) == "Ballista Falconer (ZHP)"


def test_name_plain():
    html = '<div class="card"><a href="/last-epoch/build-guides/x">Warpath Void Knight</a></div>'
    assert extract_name_from_html(html) == "Warpath Void Knight"


def test_name_in_nested_heading():
    html = '<div class="card"><h3><a href="/last-epoch/build-guides/x"><span>Judgement Paladin</span></a></h3></div>'
    assert extract_name_from_html(html) == "Judgement Paladin"


def test_fallback_uses_general_text():
    html = '<div class="card">Some prefix <span>Bladestorm Bladedancer</span> <button>Go To Build</button></div>'
    assert extract_name_from_html(html) == "Some prefix Bladestorm Bladedancer"


def test_different_names_remain_distinct():
    html1 = '<div class="card"><a href="/last-epoch/build-guides/x">Acolyte Build</a></div>'
    html2 = '<div class="card"><a href="/last-epoch/build-guides/y">Acolyte Build (ZHP)</a></div>'
    assert extract_name_from_html(html1) != extract_name_from_html(html2)
