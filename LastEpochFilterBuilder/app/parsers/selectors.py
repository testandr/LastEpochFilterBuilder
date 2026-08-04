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
        "page_title": ["h1", "title", "meta[property='og:title']"],
        "build_name": ["h1.entry-title", "h1", ".post-title", "meta[property='og:title']"],
        "class_name": [".class-name", ".build-class", "meta[itemprop='author']"],
        "mastery": [".mastery", ".build-mastery", ".sub-title"],
        "author": [".author", ".byline", "meta[name='author']"],
        "main_content": ["main", "article", "#content"],
        "metadata": ["script[type='application/ld+json']", "script#__NEXT_DATA__", "meta[property='og:title']"],
        "equipment_section": ["#equipment", ".equipment", "[data-section='equipment']"],
        "idols_section": ["#idols", ".idols", "[data-section='idols']"],
        "skills_section": ["#skills", ".skills", "[data-section='skills']"],
        "stats_section": ["#stats", ".stats", "[data-section='stats']"],
    },
}
