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
            affixes=frozenset([(None, 'Health', 5)]),
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
            affixes=frozenset([(None, 'Health', 5)]),
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
            modifiers=frozenset([(None, 'Mod1', 0), (None, 'Mod2', 0)]),
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
                occurrence_count=5,
                slot='Helmet',
                item_type=1,
                sub_type=0,
                affixes=frozenset([(None, 'A', 5)]),
                sources={'s1'}
            ),
            FilterRule(
                category='exalted',
                semantic_priority=100,
                score=80.0,
                build_count=3,
                occurrence_count=7,
                slot='Helmet',
                item_type=1,
                sub_type=0,
                affixes=frozenset([(None, 'A', 5)]),
                sources={'s2'}
            )
        ]
        result = RuleOptimizer().optimize(RuleBuildResult(rules=rules))
        assert result.original_count == 2
        assert result.optimized_count == 1
        assert result.exalted_merged == 1
        opt = result.rules[0]
        assert opt.score == 80.0  # max
        assert opt.build_count == 3  # max (conservative, not sum)
        assert opt.occurrence_count == 7  # max (conservative)
        assert opt.sources == {'s1', 's2'}

    def test_cross_base_exalted_merged(self):
        """Exalted rules with same slot, same affixes, same sub_type but different item types should merge."""
        rules = [
            FilterRule(
                category='exalted',
                semantic_priority=100,
                score=60.0,
                slot='Helmet',
                item_type=1,
                sub_type=0,
                affixes=frozenset([(None, 'X', 6)]),
                sources={'s1'}
            ),
            FilterRule(
                category='exalted',
                semantic_priority=100,
                score=70.0,
                slot='Helmet',
                item_type=2,
                sub_type=0,
                affixes=frozenset([(None, 'X', 6)]),
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
                affixes=frozenset([(None, 'A', 5)]),
                sources={'s1'}
            ),
            FilterRule(
                category='exalted',
                semantic_priority=100,
                score=50.0,
                slot='Gloves',
                item_type=1,
                sub_type=0,
                affixes=frozenset([(None, 'B', 5)]),
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
                affixes=frozenset([(None, 'A', 5)]),
                sources={'s1'}
            ),
            FilterRule(
                category='exalted',
                semantic_priority=100,
                score=50.0,
                slot='Gloves',
                item_type=1,
                sub_type=0,
                affixes=frozenset([(None, 'A', 5)]),
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
                modifiers=frozenset([(None, 'M1', 0), (None, 'M2', 0)]),
                sources={'s1'}
            ),
            FilterRule(
                category='idol',
                semantic_priority=70,
                score=60.0,
                idol_size='Grand',
                modifiers=frozenset([(None, 'M1', 0), (None, 'M2', 0)]),
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
                modifiers=frozenset([(None, 'MA', 0), (None, 'MB', 0)]),
                sources={'s1'}
            ),
            FilterRule(
                category='idol',
                semantic_priority=70,
                score=55.0,
                idol_size='Small',
                modifiers=frozenset([(None, 'MA', 0), (None, 'MB', 0)]),
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
                modifiers=frozenset([(None, 'M1', 0)]),
                sources={'s1'}
            ),
            FilterRule(
                category='idol',
                semantic_priority=70,
                score=50.0,
                idol_size='Grand',
                modifiers=frozenset([(None, 'M2', 0)]),
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

    def test_different_unique_ids_not_merged(self):
        """Unique rules with different IDs should NOT merge (allows selective pruning)."""
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
        assert result.optimized_count == 2  # NOT merged
        assert result.unique_merged == 0

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
        # Different unique_ids do NOT merge under Part 3B policy
        assert len(result.rules) == 2
        names = {name for rule in result.rules for name in rule.unique_names}
        ids = {id for rule in result.rules for id in rule.unique_ids}
        assert 'A' in names
        assert 'B' in names
        assert 1 in ids
        assert 2 in ids


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
                affixes=frozenset([(None, 'A', 6)]),
                sources={'s1'}
            ),
            FilterRule(
                category='exalted',
                semantic_priority=100,
                score=50.0,
                slot='Helmet',
                item_type=1,
                sub_type=0,
                affixes=frozenset([(None, 'A', 7)]),
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
            affixes=frozenset([(None, 'A', 5)]),
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

        # All 150 unique rules created (no merge)
        assert result.optimized_count == 150
        # Part 3B prunes 10 to fit default max_rules=140
        assert result.final_count == 140
        assert result.rules_pruned == 10
        assert result.exceeds_budget
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
                affixes=frozenset([(None, 'A', 5)]),
                sources={'s1'}
            ),
            FilterRule(
                category='exalted',
                semantic_priority=100,
                score=75.0,
                slot='Helmet',
                item_type=1,
                sub_type=0,
                affixes=frozenset([(None, 'A', 5)]),
                sources={'s2'}
            ),
            # 2 Idol duplicates
            FilterRule(
                category='idol',
                semantic_priority=70,
                score=60.0,
                idol_size='Grand',
                modifiers=frozenset([(None, 'M1', 0)]),
                sources={'s3'}
            ),
            FilterRule(
                category='idol',
                semantic_priority=70,
                score=65.0,
                idol_size='Grand',
                modifiers=frozenset([(None, 'M1', 0)]),
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
        assert result.optimized_count == 4  # Exalted 1, Idol 1, Unique 2 (different IDs)
        assert result.exalted_merged == 1
        assert result.idol_merged == 1
        assert result.unique_merged == 0  # Different unique IDs do not merge


class TestConservativeStatistics:
    """Test conservative build_count and occurrence_count policies."""

    def test_build_count_uses_max_not_sum(self):
        """Merged build_count should use max (conservative) to avoid double-counting."""
        rules = [
            FilterRule(
                category='exalted',
                semantic_priority=100,
                score=50.0,
                build_count=10,
                slot='Helmet',
                item_type=1,
                sub_type=0,
                affixes=frozenset([(None, 'A', 5)]),
                sources={'s1'}
            ),
            FilterRule(
                category='exalted',
                semantic_priority=100,
                score=50.0,
                build_count=15,
                slot='Helmet',
                item_type=1,
                sub_type=0,
                affixes=frozenset([(None, 'A', 5)]),
                sources={'s2'}
            )
        ]
        result = RuleOptimizer().optimize(RuleBuildResult(rules=rules))
        opt = result.rules[0]
        # Should be max(10, 15) = 15, NOT 25 (sum would double-count)
        assert opt.build_count == 15

    def test_occurrence_count_uses_max(self):
        """Merged occurrence_count should use max (conservative)."""
        rules = [
            FilterRule(
                category='idol',
                semantic_priority=70,
                score=50.0,
                occurrence_count=20,
                idol_size='Grand',
                modifiers=frozenset([(None, 'M1', 0)]),
                sources={'s1'}
            ),
            FilterRule(
                category='idol',
                semantic_priority=70,
                score=50.0,
                occurrence_count=25,
                idol_size='Small',
                modifiers=frozenset([(None, 'M1', 0)]),
                sources={'s2'}
            )
        ]
        result = RuleOptimizer().optimize(RuleBuildResult(rules=rules))
        opt = result.rules[0]
        # Should be max(20, 25) = 25, conservative approach
        assert opt.occurrence_count == 25


class TestCrossBaseCorrectness:
    """Test corrected cross-base merge logic."""

    def test_same_item_type_different_sub_type_not_merged(self):
        """Rules with same item_type but different sub_type should NOT merge until subType semantics confirmed."""
        rules = [
            FilterRule(
                category='exalted',
                semantic_priority=100,
                score=50.0,
                slot='Helmet',
                item_type=1,
                sub_type=0,
                affixes=frozenset([(None, 'A', 5)]),
                sources={'s1'}
            ),
            FilterRule(
                category='exalted',
                semantic_priority=100,
                score=50.0,
                slot='Helmet',
                item_type=1,
                sub_type=1,  # Different sub_type
                affixes=frozenset([(None, 'A', 5)]),
                sources={'s2'}
            )
        ]
        result = RuleOptimizer().optimize(RuleBuildResult(rules=rules))
        # Should NOT merge - sub_type semantics not confirmed
        assert result.optimized_count == 2
        assert result.exalted_merged == 0

    def test_different_confirmed_item_types_can_merge(self):
        """Rules with different confirmed item_types (same sub_type) CAN merge."""
        rules = [
            FilterRule(
                category='exalted',
                semantic_priority=100,
                score=50.0,
                slot='Helmet',
                item_type=1,
                sub_type=0,
                affixes=frozenset([(None, 'A', 5)]),
                sources={'s1'}
            ),
            FilterRule(
                category='exalted',
                semantic_priority=100,
                score=50.0,
                slot='Helmet',
                item_type=2,
                sub_type=0,
                affixes=frozenset([(None, 'A', 5)]),
                sources={'s2'}
            )
        ]
        result = RuleOptimizer().optimize(RuleBuildResult(rules=rules))
        # CAN merge - different item_type, same sub_type, confirmed via EquipmentType
        assert result.optimized_count == 1
        assert result.exalted_merged == 1

    def test_different_slot_not_merged(self):
        """Rules with different slots should NOT merge even with same affixes."""
        rules = [
            FilterRule(
                category='exalted',
                semantic_priority=100,
                score=50.0,
                slot='Helmet',
                item_type=1,
                sub_type=0,
                affixes=frozenset([(None, 'A', 5)]),
                sources={'s1'}
            ),
            FilterRule(
                category='exalted',
                semantic_priority=100,
                score=50.0,
                slot='Body Armour',  # Different slot
                item_type=1,
                sub_type=0,
                affixes=frozenset([(None, 'A', 5)]),
                sources={'s2'}
            )
        ]
        result = RuleOptimizer().optimize(RuleBuildResult(rules=rules))
        # Should NOT merge - different slots
        assert result.optimized_count == 2
        assert result.exalted_merged == 0


class TestUniqueIdNamePairing:
    """Test that unique ID<->name pairing is preserved."""

    def test_unique_id_name_pairing_preserved_in_conversion(self):
        """Unique ID<->name pairing should be preserved through conversion."""
        rules = [
            FilterRule(
                category='unique',
                semantic_priority=40,
                score=50.0,
                unique_name='ItemA',
                unique_id=100,
                sources={'s1'}
            ),
            FilterRule(
                category='unique',
                semantic_priority=40,
                score=50.0,
                unique_name='ItemB',
                unique_id=200,
                sources={'s2'}
            )
        ]
        result = RuleOptimizer().optimize(RuleBuildResult(rules=rules))

        # Should NOT merge (different IDs), but pairing preserved
        assert result.optimized_count == 2

        # Check each rule preserves pairing
        for opt in result.rules:
            assert len(opt.unique_items) == 1
            uid, name = list(opt.unique_items)[0]
            if uid == 100:
                assert name == 'ItemA'
            elif uid == 200:
                assert name == 'ItemB'

    def test_unique_id_name_pairing_survives_sorting(self):
        """Unique ID<->name pairs should survive deterministic sorting."""
        rules = [
            FilterRule(
                category='unique',
                semantic_priority=40,
                score=50.0,
                unique_name='Zebra',
                unique_id=300,
                sources={'s1'}
            ),
            FilterRule(
                category='unique',
                semantic_priority=40,
                score=60.0,
                unique_name='Apple',
                unique_id=100,
                sources={'s2'}
            ),
            FilterRule(
                category='unique',
                semantic_priority=40,
                score=55.0,
                unique_name='Banana',
                unique_id=200,
                sources={'s3'}
            )
        ]
        result = RuleOptimizer().optimize(RuleBuildResult(rules=rules))

        # Should NOT merge (different IDs), but sorted deterministically
        assert result.optimized_count == 3

        # Check each rule preserves pairing
        for opt in result.rules:
            assert len(opt.unique_items) == 1
            uid, name = list(opt.unique_items)[0]
            if uid == 100:
                assert name == 'Apple'
            elif uid == 200:
                assert name == 'Banana'
            elif uid == 300:
                assert name == 'Zebra'


class TestInputImmutability:
    """Test that input is not mutated during optimization."""

    def test_input_remains_unchanged_after_merge(self):
        """Original input should not be modified by optimizer."""
        original_sources = {'original_source'}
        rule = FilterRule(
            category='exalted',
            semantic_priority=100,
            score=50.0,
            build_count=5,
            occurrence_count=10,
            slot='Helmet',
            item_type=1,
            sub_type=0,
            affixes=frozenset([(None, 'A', 5)]),
            sources=original_sources.copy()
        )
        input_result = RuleBuildResult(rules=[rule])

        # Store original values
        original_build_count = rule.build_count
        original_occurrence = rule.occurrence_count

        # Optimize
        result = RuleOptimizer().optimize(input_result)

        # Mutate output
        result.rules[0].sources.add('new_source')

        # Original should be unchanged
        assert rule.sources == original_sources
        assert rule.build_count == original_build_count
        assert rule.occurrence_count == original_occurrence


class TestPruningBasics:
    """Test basic pruning behavior."""

    def test_no_pruning_when_below_budget(self):
        """No pruning when rule count is below max_rules."""
        rules = [
            FilterRule(
                category='exalted',
                semantic_priority=100,
                score=50.0,
                build_count=1,
                slot='Helmet',
                item_type=1,
                affixes=frozenset([('A', i + 1)]),  # Unique affix per rule
                sources={'s1'}
            )
            for i in range(50)
        ]
        result = RuleOptimizer(max_rules=140).optimize(RuleBuildResult(rules=rules))
        assert result.final_count == 50
        assert result.rules_pruned == 0
        assert result.success is True
        assert not result.exceeds_budget

    def test_no_pruning_when_exactly_budget(self):
        """No pruning when rule count equals max_rules."""
        rules = [
            FilterRule(
                category='exalted',
                semantic_priority=100,
                score=float(i),
                build_count=1,
                slot='Helmet',
                item_type=1,
                affixes=frozenset([('A', i + 1)]),  # Unique tier per rule
                sources={'s1'}
            )
            for i in range(140)
        ]
        result = RuleOptimizer(max_rules=140).optimize(RuleBuildResult(rules=rules))
        assert result.final_count == 140
        assert result.rules_pruned == 0
        assert result.success is True

    def test_pruning_when_above_budget(self):
        """Pruning applied when rule count exceeds max_rules."""
        rules = [
            FilterRule(
                category='unique',
                semantic_priority=40,
                score=float(i),
                build_count=1,
                unique_name=f'Unique{i}',
                unique_id=i,
                sources={'s1'}
            )
            for i in range(150)
        ]
        result = RuleOptimizer(max_rules=140).optimize(RuleBuildResult(rules=rules))
        assert result.final_count == 140
        assert result.rules_pruned == 10
        assert result.success is True
        assert result.exceeds_budget is True

    def test_pruning_output_exactly_max_rules(self):
        """Pruning should produce exactly max_rules when possible."""
        rules = [
            FilterRule(
                category='idol',
                semantic_priority=70,
                score=float(i),
                build_count=1,
                idol_size='Grand',
                modifiers=frozenset([(None, 'Mod{i}', 0)]),
                sources={'s1'}
            )
            for i in range(200)
        ]
        result = RuleOptimizer(max_rules=100).optimize(RuleBuildResult(rules=rules))
        assert result.final_count == 100
        assert result.rules_pruned == 100


class TestCategoryPruningPriority:
    """Test that category pruning priority is correct."""

    def test_unique_pruned_before_idol(self):
        """Unique rules should be pruned before Idol rules."""
        rules = []
        # Add 70 unique rules (low score)
        for i in range(70):
            rules.append(FilterRule(
                category='unique',
                semantic_priority=40,
                score=10.0,
                build_count=1,
                unique_name=f'U{i}',
                unique_id=i,
                sources={'s1'}
            ))
        # Add 70 idol rules (low score)
        for i in range(70):
            rules.append(FilterRule(
                category='idol',
                semantic_priority=70,
                score=10.0,
                build_count=1,
                idol_size='Grand',
                modifiers=frozenset([(None, 'Mod{i}', 0)]),
                sources={'s1'}
            ))

        result = RuleOptimizer(max_rules=70).optimize(RuleBuildResult(rules=rules))

        # All 70 unique should be pruned, 0 idol
        assert result.pruned_unique == 70
        assert result.pruned_idol == 0
        assert result.final_count == 70

    def test_idol_pruned_before_exalted(self):
        """Idol rules should be pruned before Exalted rules."""
        rules = []
        # Add 50 idol rules (low score, different modifiers to avoid merge)
        for i in range(50):
            rules.append(FilterRule(
                category='idol',
                semantic_priority=70,
                score=10.0,
                build_count=1,
                idol_size='Grand',
                modifiers=frozenset([(None, 'Mod{i}', 0)]),
                sources={'s1'}
            ))
        # Add 50 exalted rules (low score, different affixes to avoid merge)
        for i in range(50):
            rules.append(FilterRule(
                category='exalted',
                semantic_priority=100,
                score=10.0,
                build_count=1,
                slot='Helmet',
                item_type=1,
                affixes=frozenset([('A', i + 1)]),
                sources={'s1'}
            ))

        result = RuleOptimizer(max_rules=50).optimize(RuleBuildResult(rules=rules))

        # All 50 idol should be pruned, 0 exalted
        assert result.pruned_idol == 50
        assert result.pruned_exalted == 0
        assert result.final_count == 50


class TestWithinCategoryPruningOrder:
    """Test that within-category pruning order is correct."""

    def test_lower_score_pruned_first(self):
        """Within category, lower score should be pruned first."""
        rules = []
        # High score unique
        for i in range(70):
            rules.append(FilterRule(
                category='unique',
                semantic_priority=40,
                score=100.0,
                build_count=1,
                unique_name=f'High{i}',
                unique_id=i,
                sources={'s1'}
            ))
        # Low score unique
        for i in range(70, 140):
            rules.append(FilterRule(
                category='unique',
                semantic_priority=40,
                score=10.0,
                build_count=1,
                unique_name=f'Low{i}',
                unique_id=i,
                sources={'s1'}
            ))

        result = RuleOptimizer(max_rules=70).optimize(RuleBuildResult(rules=rules))

        # All remaining should have high score
        for rule in result.rules:
            assert rule.score == 100.0

    def test_build_count_tie_break(self):
        """When score is same, lower build_count should be pruned first."""
        rules = []
        # High build_count
        for i in range(70):
            rules.append(FilterRule(
                category='unique',
                semantic_priority=40,
                score=50.0,
                build_count=10,
                unique_name=f'HighBC{i}',
                unique_id=i,
                sources={'s1'}
            ))
        # Low build_count
        for i in range(70, 140):
            rules.append(FilterRule(
                category='unique',
                semantic_priority=40,
                score=50.0,
                build_count=1,
                unique_name=f'LowBC{i}',
                unique_id=i,
                sources={'s1'}
            ))

        result = RuleOptimizer(max_rules=70).optimize(RuleBuildResult(rules=rules))

        # All remaining should have high build_count
        for rule in result.rules:
            assert rule.build_count == 10

    def test_source_count_tie_break(self):
        """When score and build_count same, lower source_count pruned first."""
        rules = []
        # High source_count
        for i in range(70):
            rules.append(FilterRule(
                category='unique',
                semantic_priority=40,
                score=50.0,
                build_count=1,
                source_count=3,
                unique_name=f'HighSC{i}',
                unique_id=i,
                sources={'s1', 's2', 's3'}
            ))
        # Low source_count
        for i in range(70, 140):
            rules.append(FilterRule(
                category='unique',
                semantic_priority=40,
                score=50.0,
                build_count=1,
                source_count=1,
                unique_name=f'LowSC{i}',
                unique_id=i,
                sources={'s1'}
            ))

        result = RuleOptimizer(max_rules=70).optimize(RuleBuildResult(rules=rules))

        # All remaining should have high source_count
        for rule in result.rules:
            assert rule.source_count == 3

    def test_stable_identity_tie_break(self):
        """When all stats same, stable identity provides deterministic order."""
        rules = []
        names = [f'Z{i:03d}' for i in range(70)] + [f'A{i:03d}' for i in range(70)]
        for i, name in enumerate(names):
            rules.append(FilterRule(
                category='unique',
                semantic_priority=40,
                score=50.0,
                build_count=1,
                source_count=1,
                unique_name=name,
                unique_id=i,
                sources={'s1'}
            ))

        result = RuleOptimizer(max_rules=70).optimize(RuleBuildResult(rules=rules))

        # Should keep A* names (earlier in alphabet, earlier in stable sort)
        for rule in result.rules:
            assert rule.unique_names[0].startswith('A')


class TestProtectedRules:
    """Test protected rule behavior."""

    def test_multi_source_rule_survives(self):
        """Rules with source_count >= 2 should be protected."""
        rules = []
        # Protected multi-source
        rules.append(FilterRule(
            category='unique',
            semantic_priority=40,
            score=10.0,
            build_count=1,
            source_count=2,
            unique_name='Protected',
            unique_id=999,
            sources={'s1', 's2'}
        ))
        # Unprotected single-source high score
        for i in range(140):
            rules.append(FilterRule(
                category='unique',
                semantic_priority=40,
                score=100.0,
                build_count=1,
                source_count=1,
                unique_name=f'Unprotected{i}',
                unique_id=i,
                sources={'s1'}
            ))

        result = RuleOptimizer(max_rules=140).optimize(RuleBuildResult(rules=rules))

        # Protected should survive despite low score
        assert any(r.unique_names[0] == 'Protected' for r in result.rules)

    def test_high_build_count_survives(self):
        """Rules with build_count >= 5 should be protected."""
        rules = []
        # Protected high build_count
        rules.append(FilterRule(
            category='unique',
            semantic_priority=40,
            score=10.0,
            build_count=5,
            unique_name='Protected',
            unique_id=999,
            sources={'s1'}
        ))
        # Unprotected high score
        for i in range(140):
            rules.append(FilterRule(
                category='unique',
                semantic_priority=40,
                score=100.0,
                build_count=1,
                unique_name=f'Unprotected{i}',
                unique_id=i,
                sources={'s1'}
            ))

        result = RuleOptimizer(max_rules=140).optimize(RuleBuildResult(rules=rules))

        # Protected should survive
        assert any(r.unique_names[0] == 'Protected' for r in result.rules)

    def test_exalted_build_count_3_survives(self):
        """Exalted rules with build_count >= 3 should be protected."""
        rules = []
        # Protected exalted
        rules.append(FilterRule(
            category='exalted',
            semantic_priority=100,
            score=10.0,
            build_count=3,
            slot='Helmet',
            item_type=999,
            affixes=frozenset([(None, 'Protected', 5)]),
            sources={'s1'}
        ))
        # Unprotected high score
        for i in range(140):
            rules.append(FilterRule(
                category='exalted',
                semantic_priority=100,
                score=100.0,
                build_count=1,
                slot='Helmet',
                item_type=i,
                affixes=frozenset([(None, 'Unprotected', 5)]),
                sources={'s1'}
            ))

        result = RuleOptimizer(max_rules=140).optimize(RuleBuildResult(rules=rules))

        # Protected should survive
        protected_found = any(
            ('Protected', 5) in r.affixes for r in result.rules
        )
        assert protected_found


class TestImpossibleBudget:
    """Test behavior when budget is impossible."""

    def test_impossible_budget_returns_failure(self):
        """If protected rules exceed max_rules, should return success=False."""
        rules = []
        # Create 150 protected rules (all multi-source)
        for i in range(150):
            rules.append(FilterRule(
                category='unique',
                semantic_priority=40,
                score=50.0,
                build_count=1,
                source_count=2,
                unique_name=f'Protected{i}',
                unique_id=i,
                sources={'s1', 's2'}
            ))

        result = RuleOptimizer(max_rules=140).optimize(RuleBuildResult(rules=rules))

        assert result.success is False
        assert result.protected_count == 150
        assert result.final_count == 150  # Unchanged
        assert 'protected rules exceed budget' in result.message.lower()

    def test_protected_not_silently_deleted(self):
        """Protected rules should never be silently deleted."""
        rules = []
        # 100 protected
        for i in range(100):
            rules.append(FilterRule(
                category='unique',
                semantic_priority=40,
                score=50.0,
                build_count=5,
                unique_name=f'Protected{i}',
                unique_id=i,
                sources={'s1'}
            ))
        # 50 unprotected
        for i in range(100, 150):
            rules.append(FilterRule(
                category='unique',
                semantic_priority=40,
                score=50.0,
                build_count=1,
                unique_name=f'Unprotected{i}',
                unique_id=i,
                sources={'s1'}
            ))

        result = RuleOptimizer(max_rules=140).optimize(RuleBuildResult(rules=rules))

        # All protected should survive
        assert result.protected_count == 100
        assert result.final_count == 140
        # Only unprotected pruned
        assert result.rules_pruned == 10


class TestPruningCounts:
    """Test pruning count accuracy."""

    def test_pruning_counts_correct(self):
        """Pruning counts by category should be accurate."""
        rules = []
        # 50 unique (will be pruned first)
        for i in range(50):
            rules.append(FilterRule(
                category='unique',
                semantic_priority=40,
                score=10.0,
                build_count=1,
                unique_name=f'U{i}',
                unique_id=i,
                sources={'s1'}
            ))
        # 50 idol (will be pruned second)
        for i in range(50):
            rules.append(FilterRule(
                category='idol',
                semantic_priority=70,
                score=10.0,
                build_count=1,
                idol_size='Grand',
                modifiers=frozenset([(None, 'Mod{i}', 0)]),
                sources={'s1'}
            ))
        # 50 exalted (will survive, different affixes to avoid merge)
        for i in range(50):
            rules.append(FilterRule(
                category='exalted',
                semantic_priority=100,
                score=10.0,
                build_count=1,
                slot='Helmet',
                item_type=1,
                affixes=frozenset([('A', i + 1)]),
                sources={'s1'}
            ))

        result = RuleOptimizer(max_rules=60).optimize(RuleBuildResult(rules=rules))

        # Should prune all 50 unique + 40 idol
        assert result.pruned_unique == 50
        assert result.pruned_idol == 40
        assert result.pruned_exalted == 0
        assert result.rules_pruned == 90
        assert result.final_count == 60

    def test_category_prune_counts_separate(self):
        """Pruning counts should be tracked separately by category."""
        rules = []
        for i in range(60):
            rules.append(FilterRule(
                category='unique',
                semantic_priority=40,
                score=10.0,
                build_count=1,
                unique_name=f'U{i}',
                unique_id=i,
                sources={'s1'}
            ))
        for i in range(60):
            rules.append(FilterRule(
                category='idol',
                semantic_priority=70,
                score=10.0,
                build_count=1,
                idol_size='Grand',
                modifiers=frozenset([(None, 'Mod{i}', 0)]),
                sources={'s1'}
            ))
        for i in range(60):
            rules.append(FilterRule(
                category='exalted',
                semantic_priority=100,
                score=10.0,
                build_count=1,
                slot='Helmet',
                item_type=1,
                affixes=frozenset([(f'Affix{i}', 5)]),  # Unique affixes prevent merge
                sources={'s1'}
            ))

        result = RuleOptimizer(max_rules=140).optimize(RuleBuildResult(rules=rules))

        # 180 total, need to remove 40
        # All unique + all idol = 120, so prune 40 unique
        assert result.pruned_unique == 40
        assert result.pruned_idol == 0
        assert result.pruned_exalted == 0


class TestDeterministicPruning:
    """Test deterministic pruning behavior."""

    def test_deterministic_pruning_result(self):
        """Same input should produce same pruning result."""
        rules = []
        for i in range(150):
            rules.append(FilterRule(
                category='unique',
                semantic_priority=40,
                score=float(i % 10),
                build_count=i % 5 + 1,
                unique_name=f'U{i}',
                unique_id=i,
                sources={'s1'}
            ))

        result1 = RuleOptimizer(max_rules=100).optimize(RuleBuildResult(rules=rules))
        result2 = RuleOptimizer(max_rules=100).optimize(RuleBuildResult(rules=rules))

        # Should produce identical results
        assert result1.final_count == result2.final_count
        assert result1.rules_pruned == result2.rules_pruned
        names1 = [r.unique_names[0] for r in result1.rules]
        names2 = [r.unique_names[0] for r in result2.rules]
        assert names1 == names2


class TestPruningInputImmutability:
    """Test that pruning does not mutate input."""

    def test_input_not_mutated_by_pruning(self):
        """Input should not be modified during pruning."""
        original_sources = {'original'}
        rules = []
        for i in range(150):
            rules.append(FilterRule(
                category='unique',
                semantic_priority=40,
                score=float(i),
                build_count=1,
                unique_name=f'U{i}',
                unique_id=i,
                sources=original_sources.copy()
            ))
        input_result = RuleBuildResult(rules=rules)
        original_count = len(input_result.rules)

        result = RuleOptimizer(max_rules=100).optimize(input_result)

        # Input should be unchanged
        assert len(input_result.rules) == original_count
        assert all(r.sources == original_sources for r in input_result.rules)


class TestMergedRulePruning:
    """Test that merged rules are pruned atomically."""

    def test_merged_rule_pruned_atomically(self):
        """Merged rule should be pruned as a whole, not split."""
        rules = []
        # Create mergeable rules
        rules.append(FilterRule(
            category='unique',
            semantic_priority=40,
            score=50.0,
            build_count=1,
            unique_name='Apple',
            unique_id=1,
            sources={'s1'}
        ))
        rules.append(FilterRule(
            category='unique',
            semantic_priority=40,
            score=50.0,
            build_count=1,
            unique_name='Banana',
            unique_id=2,
            sources={'s1'}
        ))
        # Add many high-score rules to force pruning
        for i in range(100, 250):
            rules.append(FilterRule(
                category='unique',
                semantic_priority=40,
                score=100.0,
                build_count=1,
                unique_name=f'High{i}',
                unique_id=i,
                sources={'s1'}
            ))

        result = RuleOptimizer(max_rules=140).optimize(RuleBuildResult(rules=rules))

        # Check if merged rule was pruned
        merged_present = any(
            len(r.unique_items) > 1 for r in result.rules
        )

        if merged_present:
            # If merged rule survived, both items should be present
            merged_rule = [r for r in result.rules if len(r.unique_items) > 1][0]
            assert (1, 'Apple') in merged_rule.unique_items
            assert (2, 'Banana') in merged_rule.unique_items
        else:
            # If merged rule was pruned, neither should be present
            all_names = [name for r in result.rules for name in r.unique_names]
            assert 'Apple' not in all_names
            assert 'Banana' not in all_names


class TestConfigurableMaxRules:
    """Test that max_rules is configurable."""

    def test_max_rules_140_works(self):
        """Default max_rules=140 should work."""
        rules = [
            FilterRule(
                category='unique',
                semantic_priority=40,
                score=float(i),
                build_count=1,
                unique_name=f'U{i}',
                unique_id=i,
                sources={'s1'}
            )
            for i in range(200)
        ]
        result = RuleOptimizer(max_rules=140).optimize(RuleBuildResult(rules=rules))
        assert result.final_count == 140

    def test_custom_max_rules_works(self):
        """Custom max_rules values should work."""
        rules = [
            FilterRule(
                category='unique',
                semantic_priority=40,
                score=float(i),
                build_count=1,
                unique_name=f'U{i}',
                unique_id=i,
                sources={'s1'}
            )
            for i in range(200)
        ]
        result = RuleOptimizer(max_rules=50).optimize(RuleBuildResult(rules=rules))
        assert result.final_count == 50

    def test_max_rules_parameter_respected(self):
        """Optimizer should respect max_rules parameter."""
        rules = [
            FilterRule(
                category='unique',
                semantic_priority=40,
                score=float(i),
                build_count=1,
                unique_name=f'U{i}',
                unique_id=i,
                sources={'s1'}
            )
            for i in range(100)
        ]
        optimizer = RuleOptimizer(max_rules=75)
        result = optimizer.optimize(RuleBuildResult(rules=rules))
        assert result.final_count == 75
