"""Regression tests for Phase 0A affix ID preservation in RuleOptimizer.

These tests ensure that after Phase 0A changes, the optimizer correctly
handles 3-tuple affix/modifier identities (affix_id, name, tier) and does
not incorrectly merge rules with different affix IDs.
"""
import pytest
from app.generator.rule_models import FilterRule, RuleBuildResult
from app.generator.rule_optimizer import RuleOptimizer


def test_different_affix_ids_not_merged():
    """Rules with different affix IDs should NOT merge even if names/tiers match."""
    rules = [
        FilterRule(
            category='exalted',
            semantic_priority=100,
            score=50.0,
            build_count=1,
            slot='Gloves',
            item_type=1,
            sub_type=0,
            affixes=frozenset([(101, 'Health', 5)]),
            sources={'s1'}
        ),
        FilterRule(
            category='exalted',
            semantic_priority=100,
            score=50.0,
            build_count=1,
            slot='Gloves',
            item_type=1,
            sub_type=0,
            affixes=frozenset([(102, 'Health', 5)]),
            sources={'s2'}
        )
    ]
    result = RuleOptimizer().optimize(RuleBuildResult(rules=rules))
    assert result.optimized_count == 2, "Different affix IDs should not merge"
    assert result.exalted_merged == 0


def test_same_affix_id_merges():
    """Rules with same affix ID, name, tier should merge."""
    rules = [
        FilterRule(
            category='exalted',
            semantic_priority=100,
            score=50.0,
            build_count=1,
            slot='Gloves',
            item_type=1,
            sub_type=0,
            affixes=frozenset([(101, 'Health', 5)]),
            sources={'s1'}
        ),
        FilterRule(
            category='exalted',
            semantic_priority=100,
            score=50.0,
            build_count=1,
            slot='Gloves',
            item_type=1,
            sub_type=0,
            affixes=frozenset([(101, 'Health', 5)]),
            sources={'s2'}
        )
    ]
    result = RuleOptimizer().optimize(RuleBuildResult(rules=rules))
    assert result.optimized_count == 1, "Same affix ID should merge"
    assert result.exalted_merged == 1


def test_none_affix_id_fallback_deterministic():
    """Rules with None affix_id should fall back to name comparison deterministically."""
    rules = [
        FilterRule(
            category='exalted',
            semantic_priority=100,
            score=50.0,
            build_count=1,
            slot='Gloves',
            item_type=1,
            sub_type=0,
            affixes=frozenset([(None, 'Health', 5)]),
            sources={'s1'}
        ),
        FilterRule(
            category='exalted',
            semantic_priority=100,
            score=50.0,
            build_count=1,
            slot='Gloves',
            item_type=1,
            sub_type=0,
            affixes=frozenset([(None, 'Health', 5)]),
            sources={'s2'}
        )
    ]
    result = RuleOptimizer().optimize(RuleBuildResult(rules=rules))
    assert result.optimized_count == 1, "None fallback should merge same names"
    assert result.exalted_merged == 1


def test_none_vs_numeric_id_not_merged():
    """Rules with None affix_id should NOT merge with rules having numeric ID even if name matches."""
    rules = [
        FilterRule(
            category='exalted',
            semantic_priority=100,
            score=50.0,
            build_count=1,
            slot='Gloves',
            item_type=1,
            sub_type=0,
            affixes=frozenset([(None, 'Health', 5)]),
            sources={'s1'}
        ),
        FilterRule(
            category='exalted',
            semantic_priority=100,
            score=50.0,
            build_count=1,
            slot='Gloves',
            item_type=1,
            sub_type=0,
            affixes=frozenset([(101, 'Health', 5)]),
            sources={'s2'}
        )
    ]
    result = RuleOptimizer().optimize(RuleBuildResult(rules=rules))
    assert result.optimized_count == 2, "None vs numeric ID should not merge"
    assert result.exalted_merged == 0


def test_different_idol_modifier_ids_not_merged():
    """Idol rules with different modifier affix IDs should NOT merge."""
    rules = [
        FilterRule(
            category='idol',
            semantic_priority=70,
            score=50.0,
            build_count=1,
            idol_size='Grand',
            modifiers=frozenset([(201, 'Armor', 5)]),
            sources={'s1'}
        ),
        FilterRule(
            category='idol',
            semantic_priority=70,
            score=50.0,
            build_count=1,
            idol_size='Grand',
            modifiers=frozenset([(202, 'Armor', 5)]),
            sources={'s2'}
        )
    ]
    result = RuleOptimizer().optimize(RuleBuildResult(rules=rules))
    assert result.optimized_count == 2, "Different modifier IDs should not merge"
    assert result.idol_merged == 0


def test_same_idol_modifier_id_merges():
    """Idol rules with same modifier affix ID should merge."""
    rules = [
        FilterRule(
            category='idol',
            semantic_priority=70,
            score=50.0,
            build_count=1,
            idol_size='Grand',
            modifiers=frozenset([(201, 'Armor', 5)]),
            sources={'s1'}
        ),
        FilterRule(
            category='idol',
            semantic_priority=70,
            score=50.0,
            build_count=1,
            idol_size='Lagre',
            modifiers=frozenset([(201, 'Armor', 5)]),
            sources={'s2'}
        )
    ]
    result = RuleOptimizer().optimize(RuleBuildResult(rules=rules))
    assert result.optimized_count == 1, "Same modifier ID should merge"
    assert result.idol_merged == 1


def test_partial_overlap_with_affix_ids_not_merged():
    """Rules with partial affix overlap should NOT merge even with affix IDs."""
    rules = [
        FilterRule(
            category='exalted',
            semantic_priority=100,
            score=50.0,
            build_count=1,
            slot='Gloves',
            item_type=1,
            sub_type=0,
            affixes=frozenset([(101, 'A', 5), (102, 'B', 5)]),
            sources={'s1'}
        ),
        FilterRule(
            category='exalted',
            semantic_priority=100,
            score=50.0,
            build_count=1,
            slot='Gloves',
            item_type=1,
            sub_type=0,
            affixes=frozenset([(101, 'A', 5), (103, 'C', 5)]),
            sources={'s2'}
        )
    ]
    result = RuleOptimizer().optimize(RuleBuildResult(rules=rules))
    assert result.optimized_count == 2, "Partial overlap should not merge"
    assert result.exalted_merged == 0


def test_many_unique_affixes_no_collapse():
    """Many rules with unique affix IDs should NOT collapse into one."""
    rules = [
        FilterRule(
            category='exalted',
            semantic_priority=100,
            score=float(i),
            build_count=1,
            slot='Helmet',
            item_type=1,
            affixes=frozenset([(100 + i, f'Affix{i}', 5)]),
            sources={'s1'}
        )
        for i in range(50)
    ]
    result = RuleOptimizer().optimize(RuleBuildResult(rules=rules))
    assert result.optimized_count == 50, "Unique affix IDs should not merge"
    assert result.exalted_merged == 0


def test_many_unique_idol_modifiers_no_collapse():
    """Many idol rules with unique modifier IDs should NOT collapse."""
    rules = [
        FilterRule(
            category='idol',
            semantic_priority=70,
            score=float(i),
            build_count=1,
            idol_size='Grand',
            modifiers=frozenset([(200 + i, f'Mod{i}', 0)]),
            sources={'s1'}
        )
        for i in range(50)
    ]
    result = RuleOptimizer().optimize(RuleBuildResult(rules=rules))
    assert result.optimized_count == 50, "Unique modifier IDs should not merge"
    assert result.idol_merged == 0


def test_mixed_none_and_numeric_ids_distinct():
    """Rules with mixed None and numeric affix IDs should remain distinct."""
    rules = [
        FilterRule(
            category='exalted',
            semantic_priority=100,
            score=50.0,
            build_count=1,
            slot='Gloves',
            item_type=1,
            affixes=frozenset([(None, 'A', 5), (None, 'B', 5)]),
            sources={'s1'}
        ),
        FilterRule(
            category='exalted',
            semantic_priority=100,
            score=50.0,
            build_count=1,
            slot='Gloves',
            item_type=1,
            affixes=frozenset([(101, 'A', 5), (102, 'B', 5)]),
            sources={'s2'}
        )
    ]
    result = RuleOptimizer().optimize(RuleBuildResult(rules=rules))
    assert result.optimized_count == 2, "Mixed None/numeric should not merge"
    assert result.exalted_merged == 0


def test_same_name_different_tier_different_id_not_merged():
    """Rules with same name but different tier and ID should NOT merge."""
    rules = [
        FilterRule(
            category='exalted',
            semantic_priority=100,
            score=50.0,
            build_count=1,
            slot='Gloves',
            item_type=1,
            affixes=frozenset([(101, 'Health', 5)]),
            sources={'s1'}
        ),
        FilterRule(
            category='exalted',
            semantic_priority=100,
            score=50.0,
            build_count=1,
            slot='Gloves',
            item_type=1,
            affixes=frozenset([(102, 'Health', 6)]),
            sources={'s2'}
        )
    ]
    result = RuleOptimizer().optimize(RuleBuildResult(rules=rules))
    assert result.optimized_count == 2, "Different tier should not merge"
    assert result.exalted_merged == 0
