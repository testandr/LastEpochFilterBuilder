"""Selector configuration for parsers.

Словарь SELECTORS содержит именованные наборы CSS/XPath селекторов для парсеров.
Это позволяет менять селекторы без правки логики парсеров.
"""

SELECTORS = {
    "tier_list": {
        # Primary selectors
        "tier_section": [".tier-section", ".tier-list", "div.tier", "._Tierlist_cxko4_1", "[class*='Tierlist']"],
        "tier_label": [".tier-label", "h2.tier", ".tier-name"],
        # include anchors to build pages as a last-resort card selector
        "build_card": [".build-card", ".card", "li.build-item", "a[href*='/last-epoch/build-guides/']"],
        # precise selectors for build name (try these first)
        "build_name_strict": [".Tierlist__tierItemTitle", "._Tierlist__tierItemTitle_cxko4_1", "a[href*='/last-epoch/build-guides/'] > .title", "a[href*='/last-epoch/build-guides/']"],
        "build_name": [".build-name", ".name", "h3 a", "a.title"],
        "build_link": ["a", "a[href]", "a[href*='/last-epoch/build-guides/']"],
        "class_mastery": [".class", ".class-mastery", ".meta .class"],
        "author": [".author", ".byline", ".meta .author"],
        "popularity": [".popularity", ".score", ".meta .pop"],
        # Fallback/semantic
        "card_container": [".cards", "ul.builds", "div.cards"],
    },
    "build_page": {
        "equipment_section": "",
        "idols_section": "",
        "skills_section": "",
        "stats_section": "",
    },
}
