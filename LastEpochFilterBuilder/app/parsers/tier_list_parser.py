from __future__ import annotations

import logging
from typing import List, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from app.parsers.base_parser import BaseParser
from app.parsers.selectors import SELECTORS
from app.dto.models import BuildSummary

logger = logging.getLogger("app.parsers.tier_list_parser")


class TierListParser(BaseParser):
    """Parser for Maxroll tier list pages. Extracts only S-Tier builds.

    Methods:
    - parse_html(html, source_url, source_name) -> list[BuildSummary]
    - parse(source, source_name) -> list[BuildSummary] (can fetch via http_client)
    """

    def parse_html(self, html: str, source_url: str, source_name: str, debug: bool = False) -> List[BuildSummary]:
        """Parse HTML and return BuildSummary list for S tier only.

        If debug=True, collect diagnostic information and log it.
        """
        soup = BeautifulSoup(html, "lxml")

        base_containers = self._find_tier_sections(soup)
        if not base_containers:
            logger.warning("No tier sections found for source %s", source_url)
            return []

        diagnostics = []
        builds: List[BuildSummary] = []

        # For each base container, find label elements (tier headers) and process each as its own section
        for base in base_containers:
            label_elements = self._find_label_elements(base)
            if not label_elements:
                # nothing to do for this base
                continue

            for label_el in label_elements:
                raw_tier = label_el.get_text(strip=True)
                norm_tier = self._normalize_tier(raw_tier)

                # find cards strictly relative to this label/section
                cards = self._extract_build_cards_for_label(label_el, base)

                diagnostics.append({"tier": norm_tier, "count": len(cards)})

                if norm_tier != "S":
                    continue

                for card in cards:
                    try:
                        bs = self._parse_build_card(card, source_url, source_name)
                        if bs:
                            builds.append(bs)
                    except Exception:
                        logger.exception("Failed to parse build card, skipping")
                        continue

        if debug:
            # print diagnostics summary grouped
            groups = {}
            for d in diagnostics:
                groups.setdefault(d["tier"], 0)
                groups[d["tier"]] += d["count"]
            logger.debug("Tier groups for %s: %s", source_url, groups)

        # merge duplicates
        merged = merge_build_summaries(builds)
        return merged

    def parse(self, source: str, source_name: str) -> List[BuildSummary]:
        # source is a URL
        if not self.http_client:
            raise RuntimeError("HttpClient not provided to TierListParser.parse")
        resp = self.http_client.get(source, cache_subdir="tier_lists", use_cache=True)
        return self.parse_html(resp.text, source, source_name)

    # --- helper methods
    def _find_tier_sections(self, soup: BeautifulSoup):
        selectors = SELECTORS.get("tier_list", {})
        sec_selectors = selectors.get("tier_section", [])
        sections = []
        for sel in sec_selectors:
            if not sel:
                continue
            found = soup.select(sel)
            if found:
                sections.extend(found)
        # If none found, try attribute selector fallback
        if not sections:
            try:
                found = soup.select("[class*='Tierlist']")
                if found:
                    sections.extend(found)
            except Exception:
                pass
        # Filter out nested containers: keep only top-level containers
        unique_sections = []
        for sec in sections:
            # check if any ancestor of sec is already in sections (or unique_sections)
            skip = False
            for anc in sec.parents:
                if anc in sections:
                    skip = True
                    break
            if not skip:
                unique_sections.append(sec)

        # If dedup produced nothing, fall back to original list
        return unique_sections or sections

    def _find_label_elements(self, base):
        selectors = SELECTORS.get("tier_list", {})
        label_els = []
        for sel in selectors.get("tier_label", []):
            if not sel:
                continue
            try:
                found = base.select(sel)
            except Exception:
                found = []
            if found:
                label_els.extend(found)

        # fallback: any header tags under base
        if not label_els:
            for h in base.find_all(["h2", "h3", "h4"]):
                if h and h.get_text(strip=True):
                    label_els.append(h)
        # Filter label elements to those that look like actual tier labels (S/A/B/C/D)
        filtered = []
        for el in label_els:
            txt = el.get_text(strip=True)
            norm = self._normalize_tier(txt)
            if norm and (len(norm) == 1 and norm in {"S", "A", "B", "C", "D"} or norm == "S"):
                filtered.append(el)

        return filtered

    def _extract_build_cards_for_label(self, label_el, base):
        """Find build card elements that belong to the section identified by label_el.

        Strategy:
        1. Try to find an ancestor of label_el (up to base) that contains build_card elements.
        2. If not found, search label_el's next siblings until another label is encountered.
        """
        selectors = SELECTORS.get("tier_list", {})
        build_card_selectors = selectors.get("build_card", [])

        # 1) ancestor approach
        ancestor = label_el.parent
        while ancestor and ancestor is not base:
            cards = []
            for sel in build_card_selectors:
                try:
                    found = ancestor.select(sel)
                except Exception:
                    found = []
                if found:
                    cards.extend(found)
            if cards:
                return cards
            ancestor = ancestor.parent

        # 2) sibling scan: collect cards from next siblings until another label is reached
        cards = []
        for sib in label_el.find_next_siblings():
            # stop if this sibling itself looks like a label
            is_label = False
            for lab_sel in selectors.get("tier_label", []):
                try:
                    if sib.select_one(lab_sel):
                        is_label = True
                        break
                except Exception:
                    continue
            if is_label:
                break

            for sel in build_card_selectors:
                try:
                    found = sib.select(sel)
                except Exception:
                    found = []
                if found:
                    cards.extend(found)

        return cards

    def _extract_tier_name(self, section) -> Optional[str]:
        selectors = SELECTORS.get("tier_list", {})
        for sel in selectors.get("tier_label", []):
            if not sel:
                continue
            el = section.select_one(sel)
            if el and el.get_text(strip=True):
                return el.get_text(strip=True)
        # fallback: look for header inside section
        h = section.find(["h2", "h3", "h4"])  # type: ignore[arg-type]
        if h and h.get_text(strip=True):
            return h.get_text(strip=True)
        return None

    def _extract_build_cards(self, section):
        selectors = SELECTORS.get("tier_list", {})
        cards = []
        for sel in selectors.get("build_card", []):
            if not sel:
                continue
            found = section.select(sel)
            if found:
                cards.extend(found)
        # if still empty, try container
        if not cards:
            for sel in selectors.get("card_container", []):
                cont = section.select_one(sel)
                if cont:
                    # look for children that might be cards
                    for child_sel in selectors.get("build_card", []):
                        found = cont.select(child_sel)
                        if found:
                            cards.extend(found)
        return cards

    def _parse_build_card(self, card, source_url: str, source_name: str) -> Optional[BuildSummary]:
        selectors = SELECTORS.get("tier_list", {})

        # name
        name = None
        href = None
        for sel in selectors.get("build_name", []):
            if not sel:
                continue
            el = card.select_one(sel)
            if el and el.get_text(strip=True):
                name = el.get_text(strip=True)
                # try to find link inside
                link_el = el if el.name == "a" else el.find("a")
                href = link_el.get("href") if link_el else None
                break
        # fallback: any link with text or the card itself may be an anchor
        if not name:
            # if card itself is an <a>
            if getattr(card, "name", None) == "a" and card.get_text(strip=True):
                name = card.get_text(strip=True)
                href = card.get("href")
            else:
                # try to find link with title inside
                a = card.find("a")
                if a and a.get_text(strip=True):
                    name = a.get_text(strip=True)
                    href = a.get("href")

        # if name still missing, skip
        if not name or not name.strip():
            logger.warning("Build card skipped: missing name in source %s", source_url)
            return None

        # Final cleaning pass to remove UI artifacts that may remain
        try:
            import re
            name = re.sub(r"(?i)\bgo\s*to\s*build\b", "", name)
            name = name.replace("*", "").replace("Ч", "")
            name = " ".join(name.split())
        except Exception:
            pass

        # if href not found earlier, try selectors for link
        if not href:
            for sel in selectors.get("build_link", []):
                if not sel:
                    continue
                a = card.select_one(sel)
                if a and a.get("href"):
                    href = a.get("href")
                    break

        if not href:
            logger.warning("Build card skipped: missing link for '%s' in %s", name, source_url)
            return None

        url = urljoin(source_url, href)

        # class and mastery
        class_name = None
        mastery = None
        cls_sel = selectors.get("class_mastery", [])
        if cls_sel:
            for sel in cls_sel:
                el = card.select_one(sel)
                if el and el.get_text(strip=True):
                    txt = el.get_text(strip=True)
                    # try to split by '/'
                    parts = [p.strip() for p in txt.split("/") if p.strip()]
                    if parts:
                        class_name = parts[0]
                        if len(parts) > 1:
                            mastery = parts[1]
                        break

        # author
        author = None
        for sel in selectors.get("author", []):
            el = card.select_one(sel)
            if el and el.get_text(strip=True):
                author = el.get_text(strip=True)
                break

        # popularity
        popularity = None
        for sel in selectors.get("popularity", []):
            el = card.select_one(sel)
            if el and el.get_text(strip=True):
                txt = el.get_text(strip=True)
                try:
                    popularity = int("".join(ch for ch in txt if ch.isdigit()))
                except Exception:
                    popularity = None
                break

        bs = BuildSummary(
            name=name,
            tier="S",
            class_name=class_name,
            mastery=mastery,
            url=url,
            sources=[source_name],
            author=author,
            popularity_score=popularity,
        )
        return bs

    @staticmethod
    def _normalize_text(value: str) -> str:
        if value is None:
            return ""
        # collapse whitespace and trim
        return " ".join(value.split())

    @staticmethod
    def _normalize_tier(value: str) -> str:
        if value is None:
            return ""
        v = " ".join(value.strip().split())
        v = v.replace("-", " ")
        low = v.lower()
        # remove the word 'tier' if present
        no_tier = low.replace("tier", "").strip()
        if no_tier == "s" or no_tier.startswith("s "):
            return "S"
        if low == "s":
            return "S"
        return low.upper()

    def _extract_build_name(self, card) -> Optional[str]:
        """Extract a clean build name from a build card element.

        Strategy:
        1. Prefer anchor text for links to /last-epoch/build-guides/, excluding CTA/badge children.
        2. If no such anchor, look for heading tags inside the card.
        3. If still nothing, use title/aria-label attributes if they seem clean.
        4. Fallback: clean card.get_text() by removing known UI fragments.
        """
        from bs4 import NavigableString

        selectors = SELECTORS.get("tier_list", {})

        # 1) find preferred anchor
        a = None
        try:
            a = card.select_one("a[href*='/last-epoch/build-guides/']")
        except Exception:
            a = None
        if not a:
            a = card.find("a", href=True)

        def clean_text_nodes(tag):
            parts = []
            for desc in tag.descendants:
                if isinstance(desc, NavigableString):
                    txt = desc.strip()
                    if not txt:
                        continue
                    # skip CTA/button texts and decorative elements via ancestor class heuristics
                    skip = False
                    for anc in desc.parents:
                        if anc is tag:
                            break
                        cls = anc.get("class") or []
                        for c in cls:
                            c_l = c.lower()
                            if "cta" in c_l or "badge" in c_l or "icon" in c_l or "extra" in c_l:
                                skip = True
                                break
                        if skip:
                            break
                    if skip:
                        continue
                    if "go to build" in txt.lower():
                        continue
                    parts.append(txt)
            return " ".join(parts).strip()

        if a:
            name = clean_text_nodes(a)
            if name:
                # post-clean: remove stray symbols like trailing '*' or 'Ч'
                import re
                name = re.sub(r"(?i)\bgo\s*to\s*build\b", "", name)
                name = name.replace("*", "").replace("Ч", "")
                name = " ".join(name.split())
                return name

        # 2) heading inside card
        for htag in ("h1", "h2", "h3", "h4", "strong"):
            h = card.find(htag)
            if h and h.get_text(strip=True):
                txt = h.get_text(strip=True)
                txt = txt.replace("*", "").replace("Ч", "")
                txt = txt.replace("Go To Build", "")
                return " ".join(txt.split())

        # 3) attributes
        for attr in ("title", "aria-label"):
            val = card.get(attr)
            if val and "go to build" not in val.lower():
                txt = val.replace("*", "").replace("Ч", "")
                return " ".join(txt.split())

        # 4) fallback: clean entire card text
        txt = card.get_text(separator=" ", strip=True)
        # remove UI fragments
        import re
        txt = re.sub(r"(?i)\bgo\s*to\s*build\b", "", txt)
        txt = txt.replace("*", "").replace("Ч", "")
        txt = " ".join(txt.split())
        # heuristic: if result is too long or empty, return None
        if not txt:
            return None
        return txt


def merge_build_summaries(builds: List[BuildSummary]) -> List[BuildSummary]:
    """Merge duplicates by URL (preferred) or by normalized name.

    Rules:
    - preserve non-None fields
    - combine sources without duplicates
    - deterministic order (first occurrence order)
    """
    seen = {}
    result: List[BuildSummary] = []
    for b in builds:
        key = (b.url or "") or b.name.strip().lower()
        norm_key = key.lower() if key else b.name.strip().lower()
        if norm_key in seen:
            existing = seen[norm_key]
            # merge fields: if existing field is None and new has value, set it
            for field in ("class_name", "mastery", "author", "popularity_score"):
                val_new = getattr(b, field)
                if getattr(existing, field) is None and val_new is not None:
                    setattr(existing, field, val_new)
            # merge sources
            combined = list(dict.fromkeys(existing.sources + b.sources))
            existing.sources = combined
        else:
            seen[norm_key] = b
            result.append(b)
    return result
