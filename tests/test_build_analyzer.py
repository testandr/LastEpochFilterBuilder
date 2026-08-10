"""Tests for build analyzer."""
import pytest

from app.analyzer.build_analyzer import BuildAnalyzer
from app.analyzer.models import AnalysisResult, ExaltedCandidate, IdolCandidate, UniqueCandidate
from app.analyzer.priority_calculator import PriorityCalculator
from app.dto.models import AffixDTO, BuildDetails, IdolDTO, ItemDTO


class TestBuildAnalyzer:
    """Tests for BuildAnalyzer."""

    def test_empty_input(self):
        """Test analyzer with empty build list."""
        analyzer = BuildAnalyzer()
        result = analyzer.analyze([])

        assert result.stats.builds_analyzed == 0
        assert result.stats.unique_builds == 0
        assert len(result.exalted_candidates) == 0
        assert len(result.idol_candidates) == 0
        assert len(result.unique_candidates) == 0

    def test_build_without_items_or_idols(self):
        """Test build with no items or idols."""
        analyzer = BuildAnalyzer()
        build = BuildDetails(
            name="Empty Build",
            items=[],
            idols=[]
        )

        result = analyzer.analyze([build])

        assert result.stats.builds_analyzed == 1
        assert result.stats.unique_builds == 1
        assert len(result.exalted_candidates) == 0
        assert len(result.idol_candidates) == 0

    def test_dedupe_same_build_by_source_url(self):
        """Test that same build (by source_url) is counted once."""
        analyzer = BuildAnalyzer()

        item = ItemDTO(
            name="Gloves",
            slot="Gloves",
            is_exalted=True,
            affixes=[AffixDTO(name="Test Affix", tier=6)],
            additional={"itemType": 1, "subType": 0}
        )

        build1 = BuildDetails(
            name="Build A",
            source_url="https://example.com/build1",
            items=[item]
        )

        build2 = BuildDetails(
            name="Build A Variant",
            source_url="https://example.com/build1",  # Same URL
            items=[item]
        )

        result = analyzer.analyze([build1, build2])

        # Should be counted as 1 unique build
        assert result.stats.builds_analyzed == 2
        assert result.stats.unique_builds == 1

        # Exalted should have build_count=1, occurrence_count=2
        assert len(result.exalted_candidates) == 1
        candidate = result.exalted_candidates[0]
        assert candidate.build_count == 1
        assert candidate.occurrence_count == 2

    def test_combine_sources(self):
        """Test that multi-source builds combine sources correctly."""
        analyzer = BuildAnalyzer()

        item = ItemDTO(
            name="Weapon",
            slot="Weapon",
            is_exalted=True,
            affixes=[AffixDTO(name="Affix A", tier=7)],
            additional={"itemType": 8, "subType": 0}
        )

        build1 = BuildDetails(
            name="Multi Build",
            source_url="https://example.com/multi",
            items=[item]
        )

        build2 = BuildDetails(
            name="Multi Build",
            source_url="https://example.com/multi",
            items=[item]
        )

        source_mapping = {
            build1.source_url: "corruption",
            build2.source_url: "bossing"  # Will be ignored, same URL
        }

        result = analyzer.analyze([build1, build2], source_mapping)

        candidate = result.exalted_candidates[0]
        # Both should map to corruption since same URL
        assert "corruption" in candidate.sources

    def test_exalted_aggregation_same_base_and_affixes(self):
        """Test exalted items with same base and affixes aggregate."""
        analyzer = BuildAnalyzer()

        item1 = ItemDTO(
            name="Gloves",
            slot="Gloves",
            is_exalted=True,
            affixes=[
                AffixDTO(name="Speed", tier=6),
                AffixDTO(name="Damage", tier=7)
            ],
            additional={"itemType": 13, "subType": 0}
        )

        item2 = ItemDTO(
            name="Gloves",
            slot="Gloves",
            is_exalted=True,
            affixes=[
                AffixDTO(name="Speed", tier=6),
                AffixDTO(name="Damage", tier=7)
            ],
            additional={"itemType": 13, "subType": 0}
        )

        build1 = BuildDetails(name="Build 1", source_url="url1", items=[item1])
        build2 = BuildDetails(name="Build 2", source_url="url2", items=[item2])

        result = analyzer.analyze([build1, build2])

        # Should aggregate into single candidate
        assert len(result.exalted_candidates) == 1
        candidate = result.exalted_candidates[0]
        assert candidate.build_count == 2
        assert candidate.occurrence_count == 2
        assert len(candidate.affixes) == 2

    def test_exalted_same_affix_in_two_builds(self):
        """Test that same affix appearing in two builds counts correctly."""
        analyzer = BuildAnalyzer()

        affix = AffixDTO(name="Critical Strike", tier=8)

        item1 = ItemDTO(
            name="Belt",
            slot="Belt",
            is_exalted=True,
            affixes=[affix],
            additional={"itemType": 17, "subType": 0}
        )

        item2 = ItemDTO(
            name="Belt",
            slot="Belt",
            is_exalted=True,
            affixes=[affix],
            additional={"itemType": 17, "subType": 0}
        )

        build1 = BuildDetails(name="B1", source_url="u1", items=[item1])
        build2 = BuildDetails(name="B2", source_url="u2", items=[item2])

        result = analyzer.analyze([build1, build2])

        assert len(result.exalted_candidates) == 1
        assert result.exalted_candidates[0].build_count == 2
        assert result.exalted_candidates[0].max_tier == 8

    def test_build_count_vs_occurrence_count(self):
        """Test distinction between build_count and occurrence_count."""
        analyzer = BuildAnalyzer()

        # Build 1: 1 exalted glove
        item1 = ItemDTO(
            name="Gloves",
            slot="Gloves",
            is_exalted=True,
            affixes=[AffixDTO(name="Speed", tier=6)],
            additional={"itemType": 13, "subType": 0}
        )

        # Build 2: 2 profile variants with same glove
        build1 = BuildDetails(name="B1", source_url="u1", items=[item1])

        build2a = BuildDetails(name="B2 v1", source_url="u2", items=[item1])
        build2b = BuildDetails(name="B2 v2", source_url="u2", items=[item1])  # Variant

        result = analyzer.analyze([build1, build2a, build2b])

        candidate = result.exalted_candidates[0]
        # 2 unique builds, but 3 total occurrences
        assert candidate.build_count == 2
        assert candidate.occurrence_count == 3

    def test_same_item_in_two_profile_variants_one_build(self):
        """Test that profile variants of same build don't inflate build_count."""
        analyzer = BuildAnalyzer()

        item = ItemDTO(
            name="Ring",
            slot="Ring 1",
            is_exalted=True,
            affixes=[AffixDTO(name="Resist", tier=5)],
            additional={"itemType": 21, "subType": 0}
        )

        variant1 = BuildDetails(name="Var 1", source_url="same_url", items=[item])
        variant2 = BuildDetails(name="Var 2", source_url="same_url", items=[item])

        result = analyzer.analyze([variant1, variant2])

        candidate = result.exalted_candidates[0]
        assert candidate.build_count == 1  # Same build
        assert candidate.occurrence_count == 2  # Two variants

    def test_idol_combination_aggregation(self):
        """Test idols with same size + modifiers aggregate."""
        analyzer = BuildAnalyzer()

        idol1 = IdolDTO(
            name="Grand Idol",
            size="Grand Idol (1x3)",
            modifiers=["Mod A", "Mod B"]
        )

        idol2 = IdolDTO(
            name="Grand Idol",
            size="Grand Idol (1x3)",
            modifiers=["Mod A", "Mod B"]  # Same combination
        )

        build1 = BuildDetails(name="B1", source_url="u1", idols=[idol1])
        build2 = BuildDetails(name="B2", source_url="u2", idols=[idol2])

        result = analyzer.analyze([build1, build2])

        assert len(result.idol_candidates) == 1
        candidate = result.idol_candidates[0]
        assert candidate.build_count == 2
        assert len(candidate.modifiers) == 2

    def test_individual_idol_modifier_stats(self):
        """Test individual modifier statistics tracking."""
        analyzer = BuildAnalyzer()

        idol1 = IdolDTO(
            size="Minor Idol (1x1)",
            modifiers=["Mod X", "Mod Y"]
        )

        idol2 = IdolDTO(
            size="Grand Idol (1x3)",
            modifiers=["Mod X", "Mod Z"]  # Mod X appears in both
        )

        build1 = BuildDetails(name="B1", source_url="u1", idols=[idol1])
        build2 = BuildDetails(name="B2", source_url="u2", idols=[idol2])

        result = analyzer.analyze([build1, build2])

        # Check individual modifier stats
        assert "Mod X" in result.modifier_stats
        assert "Mod Y" in result.modifier_stats
        assert "Mod Z" in result.modifier_stats

        mod_x_stats = result.modifier_stats["Mod X"]
        assert mod_x_stats.build_count == 2
        assert len(mod_x_stats.sizes) == 2

    def test_unique_aggregation(self):
        """Test that same unique from multiple builds aggregates."""
        analyzer = BuildAnalyzer()

        unique1 = ItemDTO(
            name="Harbinger of Stars",
            slot="Weapon",
            is_unique=True,
            additional={"uniqueID": 282}
        )

        unique2 = ItemDTO(
            name="Harbinger of Stars",
            slot="Weapon",
            is_unique=True,
            additional={"uniqueID": 282}
        )

        build1 = BuildDetails(name="B1", source_url="u1", items=[unique1])
        build2 = BuildDetails(name="B2", source_url="u2", items=[unique2])

        result = analyzer.analyze([build1, build2])

        assert len(result.unique_candidates) == 1
        candidate = result.unique_candidates[0]
        assert candidate.name == "Harbinger of Stars"
        assert candidate.unique_id == 282
        assert candidate.build_count == 2

    def test_semantic_priorities(self):
        """Test that semantic priorities are set correctly."""
        analyzer = BuildAnalyzer()

        exalted = ItemDTO(
            name="Gloves",
            slot="Gloves",
            is_exalted=True,
            affixes=[AffixDTO(name="Test", tier=6)],
            additional={"itemType": 13, "subType": 0}
        )

        idol = IdolDTO(size="Minor Idol (1x1)", modifiers=["Mod"])

        unique = ItemDTO(
            name="Unique Item",
            slot="Boots",
            is_unique=True,
            additional={"uniqueID": 1}
        )

        build = BuildDetails(
            name="Test Build",
            items=[exalted, unique],
            idols=[idol]
        )

        result = analyzer.analyze([build])

        # Check semantic priorities
        assert result.exalted_candidates[0].semantic_priority == 100
        assert result.idol_candidates[0].semantic_priority == 70
        assert result.unique_candidates[0].semantic_priority == 40

    def test_deterministic_ordering(self):
        """Test that candidates are sorted deterministically by score."""
        analyzer = BuildAnalyzer()

        # Create items with different build_counts for predictable scores
        item_high = ItemDTO(
            name="High Priority",
            slot="Weapon",
            is_exalted=True,
            affixes=[AffixDTO(name="Affix A", tier=8)],
            additional={"itemType": 8, "subType": 0}
        )

        item_low = ItemDTO(
            name="Low Priority",
            slot="Belt",
            is_exalted=True,
            affixes=[AffixDTO(name="Affix B", tier=5)],
            additional={"itemType": 17, "subType": 0}
        )

        # High priority: appears in 2 builds
        build1 = BuildDetails(name="B1", source_url="u1", items=[item_high])
        build2 = BuildDetails(name="B2", source_url="u2", items=[item_high])

        # Low priority: appears in 1 build
        build3 = BuildDetails(name="B3", source_url="u3", items=[item_low])

        result = analyzer.analyze([build1, build2, build3])

        # Should be sorted by score descending
        assert len(result.exalted_candidates) == 2
        assert result.exalted_candidates[0].build_count == 2  # Higher score
        assert result.exalted_candidates[1].build_count == 1  # Lower score

    def test_estimated_rule_count(self):
        """Test estimated rule count calculation."""
        analyzer = BuildAnalyzer()

        exalted = ItemDTO(
            name="E1",
            slot="Gloves",
            is_exalted=True,
            affixes=[AffixDTO(name="A", tier=6)],
            additional={"itemType": 13, "subType": 0}
        )

        idol = IdolDTO(size="Minor", modifiers=["M"])
        unique = ItemDTO(name="U1", is_unique=True, additional={"uniqueID": 1})

        build = BuildDetails(name="B", items=[exalted, unique], idols=[idol])

        result = analyzer.analyze([build])

        assert result.stats.estimated_exalted_rules == 1
        assert result.stats.estimated_idol_rules == 1
        assert result.stats.estimated_unique_rules == 1
        assert result.stats.estimated_total_rules == 3

    def test_exceeds_limit_warning(self):
        """Test that exceeding 140 limit only warns, doesn't remove candidates."""
        analyzer = BuildAnalyzer()

        # Create 150 different exalted items
        builds = []
        for i in range(150):
            item = ItemDTO(
                name=f"Item {i}",
                slot="Gloves",
                is_exalted=True,
                affixes=[AffixDTO(name=f"Affix {i}", tier=6)],
                additional={"itemType": 13, "subType": i}  # Unique subType
            )
            builds.append(BuildDetails(name=f"B{i}", source_url=f"u{i}", items=[item]))

        result = analyzer.analyze(builds)

        # All 150 candidates should still be present
        assert len(result.exalted_candidates) == 150
        assert result.stats.exceeds_limit is True
        assert result.stats.estimated_total_rules > 140

    def test_unknown_technical_base_identity(self):
        """Test handling of items with unknown/missing technical identity."""
        analyzer = BuildAnalyzer()

        # Item without itemType/subType in additional
        item = ItemDTO(
            name="Mystery Gloves",
            slot="Gloves",
            is_exalted=True,
            affixes=[AffixDTO(name="Test", tier=6)],
            additional={}  # No itemType/subType
        )

        build = BuildDetails(name="B", source_url="u", items=[item])

        result = analyzer.analyze([build])

        # Should still create candidate with (slot, None, None)
        assert len(result.exalted_candidates) == 1
        candidate = result.exalted_candidates[0]
        assert candidate.base_key[0] == "Gloves"
        assert candidate.base_key[1] is None
        assert candidate.base_key[2] is None


class TestPriorityCalculator:
    """Tests for PriorityCalculator."""

    def test_exalted_score_calculation(self):
        """Test exalted score formula."""
        calc = PriorityCalculator()

        candidate = ExaltedCandidate(
            base_key=("Gloves", 13, 0),
            affixes=frozenset([("Speed", 6), (" Damage", 7)]),
            build_count=3,
            occurrence_count=5,
            sources={"corruption", "bossing"},
            max_tier=7,
            avg_tier=6.5
        )

        score = calc.calculate_exalted_score(candidate)

        # base = 3*10 + 2*5 + 6.5*2 + 5*0.5 = 30 + 10 + 13 + 2.5 = 55.5
        # multiplier = 1.2 (multi-affix) * 1.1 (T6+) = 1.32
        # score = 55.5 * 1.32 = 73.26
        assert score == pytest.approx(73.26, rel=0.01)

    def test_idol_score_calculation(self):
        """Test idol score formula."""
        calc = PriorityCalculator()

        candidate = IdolCandidate(
            size="Grand Idol",
            modifiers=frozenset(["Mod A", "Mod B"]),
            build_count=2,
            occurrence_count=4,
            sources={"corruption"}
        )

        score = calc.calculate_idol_score(candidate)

        # base = 2*10 + 1*5 + 4*0.5 = 20 + 5 + 2 = 27
        # multiplier = 1.2 (multi-modifier)
        # score = 27 * 1.2 = 32.4
        assert score == pytest.approx(32.4, rel=0.01)

    def test_unique_score_calculation(self):
        """Test unique score formula."""
        calc = PriorityCalculator()

        candidate = UniqueCandidate(
            name="Harbinger",
            unique_id=282,
            build_count=5,
            occurrence_count=7,
            sources={"corruption", "bossing", "speed"}
        )

        score = calc.calculate_unique_score(candidate)

        # score = 5*10 + 3*5 + 7*0.5 = 50 + 15 + 3.5 = 68.5
        assert score == pytest.approx(68.5, rel=0.01)
