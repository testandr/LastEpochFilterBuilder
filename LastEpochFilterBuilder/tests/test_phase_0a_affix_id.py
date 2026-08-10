"""Phase 0A integration test: affix ID preservation through pipeline."""
import pytest
from app.dto.models import AffixDTO, ItemDTO, IdolDTO, BuildDetails
from app.analyzer.build_analyzer import BuildAnalyzer
from app.generator.rule_builder import RuleBuilder
from app.generator.rule_optimizer import RuleOptimizer


def test_affix_id_preserved_through_pipeline():
    """Numeric affix ID should survive from DTO through Analyzer to OptimizedRule."""
    # Create item with explicitly set affix_id
    item = ItemDTO(
        name="Test Gloves",
        slot="Gloves",
        is_exalted=True,
        affixes=[
            AffixDTO(name="Health", affix_id=123, tier=6),
            AffixDTO(name="Armor", affix_id=456, tier=5)
        ],
        additional={"itemType": 1, "subType": 0}
    )

    build = BuildDetails(
        name="Test Build",
        source_url="test://build1",
        items=[item]
    )

    # Run through pipeline
    analyzer = BuildAnalyzer()
    analysis = analyzer.analyze([build])

    # Check analyzer preserves affix_id
    assert len(analysis.exalted_candidates) == 1
    candidate = analysis.exalted_candidates[0]

    affixes_list = list(candidate.affixes)
    assert len(affixes_list) == 2

    # Check affix_id is present
    affix_ids = {affix_id for affix_id, name, tier in affixes_list}
    assert 123 in affix_ids
    assert 456 in affix_ids

    # Check names preserved
    names = {name for affix_id, name, tier in affixes_list}
    assert "Health" in names
    assert "Armor" in names

    # Check tiers preserved
    tiers = {tier for affix_id, name, tier in affixes_list}
    assert 6 in tiers
    assert 5 in tiers

    # Build rules
    builder = RuleBuilder()
    result = builder.build(analysis)

    assert len(result.rules) == 1
    rule = result.rules[0]

    # Check rule preserves affix IDs
    rule_affixes = list(rule.affixes)
    rule_ids = {affix_id for affix_id, name, tier in rule_affixes}
    assert 123 in rule_ids
    assert 456 in rule_ids

    # Optimize
    optimizer = RuleOptimizer()
    opt_result = optimizer.optimize(result)

    assert len(opt_result.rules) == 1
    opt_rule = opt_result.rules[0]

    # Final check: affix IDs survived to OptimizedRule
    opt_affixes = list(opt_rule.affixes)
    opt_ids = {affix_id for affix_id, name, tier in opt_affixes}
    assert 123 in opt_ids, "Affix ID 123 lost in optimization"
    assert 456 in opt_ids, "Affix ID 456 lost in optimization"


def test_backward_compatibility_without_affix_id():
    """Old synthetic tests creating AffixDTO without affix_id should still work."""
    # Create affix WITHOUT explicit affix_id
    item = ItemDTO(
        name="Test Helmet",
        slot="Helmet",
        is_exalted=True,
        affixes=[AffixDTO(name="Critical Strike", tier=7)],
        additional={"itemType": 2, "subType": 1}
    )

    build = BuildDetails(
        name="Synthetic Build",
        source_url="test://synthetic",
        items=[item]
    )

    analyzer = BuildAnalyzer()
    analysis = analyzer.analyze([build])

    assert len(analysis.exalted_candidates) == 1
    candidate = analysis.exalted_candidates[0]

    affixes_list = list(candidate.affixes)
    assert len(affixes_list) == 1

    # Should have None affix_id for backward compat
    affix_id, name, tier = affixes_list[0]
    assert affix_id is None
    assert name == "Critical Strike"
    assert tier == 7


def test_idol_modifier_affix_id_preserved():
    """Idol modifier affix IDs should be preserved."""
    idol = IdolDTO(
        name="Grand Idol",
        size="Grand Idol (1x3)",
        modifiers=["Health T6", "Armor T5"],
        modifier_affixes=[
            AffixDTO(name="Health", affix_id=789, tier=6),
            AffixDTO(name="Armor", affix_id=101, tier=5)
        ]
    )

    build = BuildDetails(
        name="Idol Build",
        source_url="test://idol",
        idols=[idol]
    )

    analyzer = BuildAnalyzer()
    analysis = analyzer.analyze([build])

    assert len(analysis.idol_candidates) == 1
    candidate = analysis.idol_candidates[0]

    mods_list = list(candidate.modifiers)
    assert len(mods_list) == 2

    mod_ids = {affix_id for affix_id, name, tier in mods_list}
    assert 789 in mod_ids
    assert 101 in mod_ids


def test_same_name_different_id_not_merged():
    """Items with same name but different affix IDs should NOT merge."""
    item1 = ItemDTO(
        name="Gloves A",
        slot="Gloves",
        is_exalted=True,
        affixes=[AffixDTO(name="Fire Damage", affix_id=100, tier=6)],
        additional={"itemType": 1, "subType": 0}
    )

    item2 = ItemDTO(
        name="Gloves B",
        slot="Gloves",
        is_exalted=True,
        affixes=[AffixDTO(name="Fire Damage", affix_id=200, tier=6)],
        additional={"itemType": 1, "subType": 0}
    )

    build1 = BuildDetails(name="B1", source_url="test://b1", items=[item1])
    build2 = BuildDetails(name="B2", source_url="test://b2", items=[item2])

    analyzer = BuildAnalyzer()
    analysis = analyzer.analyze([build1, build2])

    # Should create TWO candidates because affix IDs differ
    assert len(analysis.exalted_candidates) == 2
