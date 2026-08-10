"""Tests for RuleOptimizer Part 3A: Lossless merge only."""
import pytest
from app.generator.rule_models import FilterRule, RuleBuildResult, OptimizedRule, OptimizationResult
from app.generator.rule_optimizer import RuleOptimizer


class TestRuleOptimizerBasic:
    """Basic functionality tests."""

    def test_empty_input(self):
        """Empty input should produce empty output."""
        optimizer = RuleOptimizer()
        result = optimizer.optimize(RuleBuildResult())
        assert result.original_count == 0
        assert result.optimized_count == 0
        assert result.total_merged == 0

    def test_single_rule_unmodified(self):
        """Single rule should pass through without merge."""
        rule = FilterRule(
            category='exalted',
            semantic_priority=100,
            score=50.0,
            build_count=1,
            slot='Helmet',
            item_type=1,
            sub_type=0,
            affixes=frozenset([('Health', 5)]),
            sources={'test'}
        )
        input_result = RuleBuildResult(rules=[rule])
        result = RuleOptimizer().optimize(input_result)
        assert result.original_count == 1
        assert result.optimized_count == 1
        assert result.total_merged == 0


class TestFilterRuleToOptimizedRuleConversion:
    """Test FilterRule -> OptimizedRule conversion."""

    def test_exalted_conversion(self):
        """Exalted FilterRule should convert to OptimizedRule."""
        rule = FilterRule(
            category='exalted',
            semantic_priority=100,
            score=75.0,
            build_count=3,
            occurrence_count=10,
            source_count=2,
            sources={'s1', 's2'},
            slot='Body Armour',
            item_type=1,
            sub_type=2,
            affixes=frozenset([('Health', 5), ('Armor', 4)]),
            max_tier=5,
            avg_tier=4.5,
            reason='Test reason'
        )
        result = RuleOptimizer().optimize(RuleBuildResult(rules=[rule]))
        opt = result.rules[0]
        assert opt.category == 'exalted'
        assert opt.score == 75.0
        assert opt.build_count == 3
        assert opt.item_types == [(1, 2)]
        assert opt.affixes == rule.affixes
        assert opt.merged_count == 1

    def test_idol_conversion(self):
        """Idol FilterRule should convert to OptimizedRule."""
        rule = FilterRule(
            category='idol',
            semantic_priority=70,
            score=60.0,
            idol_size='Grand',
            modifiers=frozenset(['Mod1', 'Mod2']),
            sources={'s1'}
        )
        result = RuleOptimizer().optimize(RuleBuildResult(rules=[rule]))
        opt = result.rules[0]
        assert opt.category == 'idol'
        assert opt.idol_sizes == ['Grand']
        assert opt.modifiers == rule.modifiers

    def test_unique_conversion(self):
        """Unique FilterRule should convert to OptimizedRule."""
        rule = FilterRule(
            category='unique',
            semantic_priority=40,
            score=50.0,
            unique_name='Test Unique',
            unique_id=123,
            slot='Ring'
        )
        result = RuleOptimizer().optimize(RuleBuildResult(rules=[rule]))
        opt = result.rules[0]
        assert opt.category == 'unique'
        assert opt.unique_names == ['Test Unique']
        assert opt.unique_ids == [123]


class TestExaltedMerge:
    """Test Exalted rule merging."""

    def test_exact_duplicate_exalted_merged(self):
        """Exact duplicate Exalted rules should merge."""
        rules = [
            FilterRule(
                category='exalted',
                semantic_priority=100,
                score=70.0,
                build_count=2,
                slot='Helmet',
                item_type=1,
                sub_type=0,
                affixes=frozenset([('A', 5), ('B', 4)]),
                sources={'s1'}
            ),
            FilterRule(
                category='exalted',
                semantic_priority=100,
                score=80.0,
                build_count=3,
                slot='Helmet',
                item_type=1,
                sub_type=0,
                affixes=frozenset([('A', 5), ('B', 4)]),
                sources={'s2'}
            )
        ]
        result = RuleOptimizer().optimize(RuleBuildResult(rules=rules))
        assert result.original_count == 2
        assert result.optimized_count == 1
        assert result.exalted_merged == 1
        opt = result.rules[0]
        assert opt.score == 80.0  # max
        assert opt.build_count == 5
        assert opt.sources == {'s1', 's2'}

    def test_cross_base_exalted_merged(self):
        """Exalted rules with same affixes but different item types should merge."""
        rules = [
            FilterRule(
                category='exalted',
                semantic_priority=100,
                score=60.0,
                slot='Helmet',
                item_type=1,
                sub_type=0,
                affixes=frozenset([('X', 6)]),
                sources={'s1'}
            ),
            FilterRule(
                category='exalted',
                semantic_priority=100,
                score=70.0,
                slot='Helmet',
                item_type=2,
                sub_type=0,
                affixes=frozenset([('X', 6)]),
                sources={'s2'}
            )
        ]
        result = RuleOptimizer().optimize(RuleBuildResult(rules=rules))
        assert result.optimized_count == 1
        assert result.exalted_merged == 1
        opt = result.rules[0]
        assert len(opt.item_types) == 2
        assert (1, 0) in opt.item_types
        assert (2, 0) in opt.item_types

    def test_different_affixes_not_merged(self):
        """Exalted rules with different affixes should NOT merge."""
        rules = [
            FilterRule(
                category='exalted',
                semantic_priority=100,
                score=50.0,
                slot='Gloves',
                item_type=1,
                sub_type=0,
                affixes=frozenset([('A', 5)]),
                sources={'s1'}
            ),
            FilterRule(
                category='exalted',
                semantic_priority=100,
                score=50.0,
                slot='Gloves',
                item_type=1,
                sub_type=0,
                affixes=frozenset([('B', 5)]),
                sources={'s2'}
            )
        ]
        result = RuleOptimizer().optimize(RuleBuildResult(rules=rules))
        assert result.optimized_count == 2
        assert result.exalted_merged == 0

    def test_partial_affix_overlap_not_merged(self):
        """Partial affix overlap should NOT merge (would expand match set)."""
        rules = [
            FilterRule(
                category='exalted',
                semantic_priority=100,
                score=50.0,
                slot='Gloves',
                item_type=1,
                sub_type=0,
                affixes=frozenset([('A', 5), ('B', 5)]),
                sources={'s1'}
            ),
            FilterRule(
                category='exalted',
                semantic_priority=100,
                score=50.0,
                slot='Gloves',
                item_type=1,
                sub_type=0,
                affixes=frozenset([('A', 5), ('C', 5)]),
                sources={'s2'}
            )
        ]
        result = RuleOptimizer().optimize(RuleBuildResult(rules=rules))
        assert result.optimized_count == 2
        assert result.exalted_merged == 0


class TestIdolMerge:
    """Test Idol rule merging."""

    def test_exact_duplicate_idol_merged(self):
        """Exact duplicate Idol rules should merge."""
        rules = [
            FilterRule(
                category='idol',
                semantic_priority=70,
                score=50.0,
                idol_size='Grand',
                modifiers=frozenset(['M1', 'M2']),
                sources={'s1'}
            ),
            FilterRule(
                category='idol',
                semantic_priority=70,
                score=60.0,
                idol_size='Grand',
                modifiers=frozenset(['M1', 'M2']),
                sources={'s2'}
            )
        ]
        result = RuleOptimizer().optimize(RuleBuildResult(rules=rules))
        assert result.optimized_count == 1
        assert result.idol_merged == 1
        opt = result.rules[0]
        assert opt.score == 60.0  # max

    def test_same_modifiers_different_sizes_merged(self):
        """Idol rules with same modifiers but different sizes should merge."""
        rules = [
            FilterRule(
                category='idol',
                semantic_priority=70,
                score=50.0,
                idol_size='Grand',
                modifiers=frozenset(['MA', 'MB']),
                sources={'s1'}
            ),
            FilterRule(
                category='idol',
                semantic_priority=70,
                score=55.0,
                idol_size='Small',
                modifiers=frozenset(['MA', 'MB']),
                sources={'s2'}
            )
        ]
        result = RuleOptimizer().optimize(RuleBuildResult(rules=rules))
        assert result.optimized_count == 1
        assert result.idol_merged == 1
        opt = result.rules[0]
        assert len(opt.idol_sizes) == 2
        assert 'Grand' in opt.idol_sizes
        assert 'Small' in opt.idol_sizes

    def test_different_modifiers_not_merged(self):
        """Idol rules with different modifiers should NOT merge."""
        rules = [
            FilterRule(
                category='idol',
                semantic_priority=70,
                score=50.0,
                idol_size='Grand',
                modifiers=frozenset(['M1']),
                sources={'s1'}
            ),
            FilterRule(
                category='idol',
                semantic_priority=70,
                score=50.0,
                idol_size='Grand',
                modifiers=frozenset(['M2']),
                sources={'s2'}
            )
        ]
        result = RuleOptimizer().optimize(RuleBuildResult(rules=rules))
        assert result.optimized_count == 2
        assert result.idol_merged == 0


class TestUniqueMerge:
    """Test Unique rule merging."""

    def test_exact_duplicate_unique_merged(self):
        """Exact duplicate Unique rules should merge."""
        rules = [
            FilterRule(
                category='unique',
                semantic_priority=40,
                score=50.0,
                unique_name='Test',
                unique_id=100,
                sources={'s1'}
            ),
            FilterRule(
                category='unique',
                semantic_priority=40,
                score=60.0,
                unique_name='Test',
                unique_id=100,
                sources={'s2'}
            )
        ]
        result = RuleOptimizer().optimize(RuleBuildResult(rules=rules))
        assert result.optimized_count == 1
        assert result.unique_merged == 1

    def test_different_unique_ids_merged(self):
        """Unique rules with different IDs should merge."""
        rules = [
            FilterRule(
                category='unique',
                semantic_priority=40,
                score=50.0,
                unique_name='Unique1',
                unique_id=100,
                sources={'s1'}
            ),
            FilterRule(
                category='unique',
                semantic_priority=40,
                score=55.0,
                unique_name='Unique2',
                unique_id=200,
                sources={'s2'}
            )
        ]
        result = RuleOptimizer().optimize(RuleBuildResult(rules=rules))
        assert result.optimized_count == 1
        assert result.unique_merged == 1
        opt = result.rules[0]
        assert len(opt.unique_names) == 2
        assert len(opt.unique_ids) == 2

    def test_unique_name_id_mapping_preserved(self):
        """Unique name/ID mappings should be preserved in lists."""
        rules = [
            FilterRule(
                category='unique',
                semantic_priority=40,
                score=50.0,
                unique_name='A',
                unique_id=1,
                sources={'s1'}
            ),
            FilterRule(
                category='unique',
                semantic_priority=40,
                score=50.0,
                unique_name='B',
                unique_id=2,
                sources={'s2'}
            )
        ]
        result = RuleOptimizer().optimize(RuleBuildResult(rules=rules))
        opt = result.rules[0]
        assert 'A' in opt.unique_names
        assert 'B' in opt.unique_names
        assert 1 in opt.unique_ids
        assert 2 in opt.unique_ids


class TestNoTierRelaxation:
    """Test that tier relaxation is NOT performed."""

    def test_different_tiers_not_merged(self):
        """Rules with same affixes but different tiers should NOT merge (not implemented)."""
        # This is explicitly NOT part of Part 3A
        # Different tier rules will only merge if they have identical tier values
        # in the affix frozenset
        rules = [
            FilterRule(
                category='exalted',
                semantic_priority=100,
                score=50.0,
                slot='Helmet',
                item_type=1,
                sub_type=0,
                affixes=frozenset([('A', 6)]),
                sources={'s1'}
            ),
            FilterRule(
                category='exalted',
                semantic_priority=100,
                score=50.0,
                slot='Helmet',
                item_type=1,
                sub_type=0,
                affixes=frozenset([('A', 7)]),
                sources={'s2'}
            )
        ]
        result = RuleOptimizer().optimize(RuleBuildResult(rules=rules))
        # Different tiers = different affixes frozenset = no merge
        assert result.optimized_count == 2
        assert result.exalted_merged == 0


class TestDeterministicOrdering:
    """Test deterministic ordering without hash()."""

    def test_same_input_produces_identical_order(self):
        """Multiple runs with same input should produce identical output order."""
        rules = [
            FilterRule(
                category='exalted',
                semantic_priority=100,
                score=50.0 + i,
                slot=f'Slot{i}',
                item_type=i,
                sub_type=0,
                affixes=frozenset([(f'A{i}', 5)]),
                sources={'s1'}
            )
            for i in range(5)
        ]

        results = [
            RuleOptimizer().optimize(RuleBuildResult(rules=rules.copy()))
            for _ in range(5)
        ]

        # All results should have identical ordering
        for r in results[1:]:
            for i in range(len(r.rules)):
                assert r.rules[i].slot == results[0].rules[i].slot


class TestInputNotMutated:
    """Test that input is not mutated."""

    def test_input_rules_not_modified(self):
        """Original input rules should not be modified."""
        original_sources = {'s1', 's2'}
        rule = FilterRule(
            category='exalted',
            semantic_priority=100,
            score=50.0,
            slot='Helmet',
            item_type=1,
            sub_type=0,
            affixes=frozenset([('A', 5)]),
            sources=original_sources.copy()
        )
        input_result = RuleBuildResult(rules=[rule])

        # Optimize
        result = RuleOptimizer().optimize(input_result)

        # Modify output
        result.rules[0].sources.add('s3')

        # Original should be unchanged
        assert 's3' not in rule.sources
        assert rule.sources == original_sources


class TestNoPruning:
    """Test that pruning is NOT performed."""

    def test_over_140_rules_not_pruned(self):
        """Rules over 140 limit should NOT be pruned in Part 3A."""
        rules = [
            FilterRule(
                category='exalted',
                semantic_priority=100,
                score=50.0,
                slot=f'Slot{i}',
                item_type=i,
                sub_type=0,
                affixes=frozenset([(f'A{i}', 5)]),
                sources={'s1'}
            )
            for i in range(150)
        ]

        result = RuleOptimizer().optimize(RuleBuildResult(rules=rules))

        # All 150 unique rules should remain (no merge, no pruning)
        assert result.optimized_count == 150
        assert result.exceeds_limit  # Should still flag the issue
        assert result.total_merged == 0


class TestMixedCategories:
    """Test mixed category handling."""

    def test_mixed_categories_independent_merge(self):
        """Different categories should merge independently."""
        rules = [
            # 2 Exalted duplicates
            FilterRule(
                category='exalted',
                semantic_priority=100,
                score=70.0,
                slot='Helmet',
                item_type=1,
                sub_type=0,
                affixes=frozenset([('A', 5)]),
                sources={'s1'}
            ),
            FilterRule(
                category='exalted',
                semantic_priority=100,
                score=75.0,
                slot='Helmet',
                item_type=1,
                sub_type=0,
                affixes=frozenset([('A', 5)]),
                sources={'s2'}
            ),
            # 2 Idol duplicates
            FilterRule(
                category='idol',
                semantic_priority=70,
                score=60.0,
                idol_size='Grand',
                modifiers=frozenset(['M1']),
                sources={'s3'}
            ),
            FilterRule(
                category='idol',
                semantic_priority=70,
                score=65.0,
                idol_size='Grand',
                modifiers=frozenset(['M1']),
                sources={'s4'}
            ),
            # 2 Unique duplicates
            FilterRule(
                category='unique',
                semantic_priority=40,
                score=50.0,
                unique_name='Test',
                unique_id=100,
                sources={'s5'}
            ),
            FilterRule(
                category='unique',
                semantic_priority=40,
                score=55.0,
                unique_name='Test2',
                unique_id=200,
                sources={'s6'}
            )
        ]

        result = RuleOptimizer().optimize(RuleBuildResult(rules=rules))

        assert result.original_count == 6
        assert result.optimized_count == 3  # Each category merged to 1
        assert result.exalted_merged == 1
        assert result.idol_merged == 1
        assert result.unique_merged == 1
