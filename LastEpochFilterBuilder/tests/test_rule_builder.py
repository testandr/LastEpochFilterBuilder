import pytest
from app.analyzer.models import AnalysisResult, ExaltedCandidate, IdolCandidate, UniqueCandidate
from app.generator.rule_builder import RuleBuilder
from app.generator.rule_models import FilterRule, RuleBuildResult


class TestRuleBuilderBasic:
    def test_empty_analysis_result(self):
        builder = RuleBuilder()
        result = builder.build(AnalysisResult())
        assert result.total_count == 0
        assert result.exalted_count == 0
        assert not result.exceeds_limit
    
    def test_exalted_candidate_conversion(self):
        candidate = ExaltedCandidate(
            base_key=('Body Armour', 1, 2),
            affixes=frozenset([(None, 'Health', 5), (None, 'Armor', 4)]),
            build_count=3, occurrence_count=10, sources={'corruption', 'bossing'},
            max_tier=5, avg_tier=4.5, score=85.0, semantic_priority=100
        )
        result = RuleBuilder().build(AnalysisResult(exalted_candidates=[candidate]))
        assert result.total_count == 1
        rule = result.rules[0]
        assert rule.category == 'exalted'
        assert rule.slot == 'Body Armour'
        assert rule.score == 85.0
        assert rule.build_count == 3

    def test_idol_candidate_conversion(self):
        candidate = IdolCandidate(
            size='Grand', modifiers=frozenset([(None, 'MA', 0), (None, 'MB', 0)]),
            build_count=2, score=70.0, semantic_priority=70
        )
        result = RuleBuilder().build(AnalysisResult(idol_candidates=[candidate]))
        assert result.idol_count == 1
        assert result.rules[0].category == 'idol'
    
    def test_unique_candidate_conversion(self):
        candidate = UniqueCandidate(
            name='Ravenous Void', unique_id=123, slot='Ring',
            build_count=5, score=50.0, semantic_priority=40
        )
        result = RuleBuilder().build(AnalysisResult(unique_candidates=[candidate]))
        assert result.unique_count == 1
        assert result.rules[0].unique_name == 'Ravenous Void'


class TestRuleBuilderAffixPreservation:
    def test_multiple_affixes_stay_together(self):
        candidate = ExaltedCandidate(
            base_key=('Helmet', 3, 4),
            affixes=frozenset([(None, 'A', 3), (None, 'B', 4), (None, 'C', 5)]),
            build_count=1, score=60.0, semantic_priority=100
        )
        result = RuleBuilder().build(AnalysisResult(exalted_candidates=[candidate]))
        assert result.total_count == 1
        assert len(result.rules[0].affixes) == 3
    
    def test_multiple_idol_modifiers_stay_together(self):
        candidate = IdolCandidate(
            size='Small', modifiers=frozenset([(None, 'M1', 0), (None, 'M2', 0), (None, 'M3', 0)]),
            build_count=1, score=55.0, semantic_priority=70
        )
        result = RuleBuilder().build(AnalysisResult(idol_candidates=[candidate]))
        assert result.total_count == 1
        assert len(result.rules[0].modifiers) == 3


class TestRuleBuilderDataPreservation:
    def test_semantic_priority_preserved(self):
        e = ExaltedCandidate(base_key=('W', 1, 1), affixes=frozenset([(None, 'D', 5)]), score=100.0, semantic_priority=100)
        i = IdolCandidate(size='L', modifiers=frozenset([(None, 'C', 0)]), score=80.0, semantic_priority=70)
        u = UniqueCandidate(name='Test', score=60.0, semantic_priority=40)
        result = RuleBuilder().build(AnalysisResult(exalted_candidates=[e], idol_candidates=[i], unique_candidates=[u]))
        assert result.rules[0].semantic_priority == 100
        assert result.rules[1].semantic_priority == 70
        assert result.rules[2].semantic_priority == 40
    
    def test_analyzer_score_preserved_exactly(self):
        candidate = ExaltedCandidate(
            base_key=('Item', 1, 1), affixes=frozenset([(None, 'Test', 3)]),
            score=123.456, semantic_priority=100
        )
        result = RuleBuilder().build(AnalysisResult(exalted_candidates=[candidate]))
        assert result.rules[0].score == 123.456
    
    def test_statistics_preserved(self):
        candidate = ExaltedCandidate(
            base_key=('Test', 1, 1), affixes=frozenset([(None, 'Stat', 2)]),
            build_count=7, occurrence_count=21, sources={'s1', 's2', 's3'},
            score=90.0, semantic_priority=100
        )
        result = RuleBuilder().build(AnalysisResult(exalted_candidates=[candidate]))
        rule = result.rules[0]
        assert rule.build_count == 7
        assert rule.occurrence_count == 21
        assert rule.source_count == 3
    
    def test_sources_preserved_and_copied(self):
        original = {'source1', 'source2'}
        candidate = ExaltedCandidate(
            base_key=('Test', 1, 1), affixes=frozenset([(None, 'A', 1)]),
            sources=original, score=50.0, semantic_priority=100
        )
        result = RuleBuilder().build(AnalysisResult(exalted_candidates=[candidate]))
        result.rules[0].sources.add('source3')
        assert 'source3' not in original


class TestRuleBuilderOrdering:
    def test_deterministic_ordering(self):
        e1 = ExaltedCandidate(base_key=('S1', 1, 1), affixes=frozenset([(None, 'A', 1)]), score=90.0, semantic_priority=100)
        e2 = ExaltedCandidate(base_key=('S2', 2, 2), affixes=frozenset([(None, 'B', 2)]), score=95.0, semantic_priority=100)
        analysis = AnalysisResult(exalted_candidates=[e1, e2])
        result1 = RuleBuilder().build(analysis)
        result2 = RuleBuilder().build(analysis)
        for i in range(len(result1.rules)):
            assert result1.rules[i].slot == result2.rules[i].slot
    
    def test_same_input_produces_identical_output(self):
        candidates = [
            ExaltedCandidate(base_key=(f'Slot{i}', i, i), affixes=frozenset([]), score=100-i, semantic_priority=100)
            for i in range(5)
        ]
        results = [RuleBuilder().build(AnalysisResult(exalted_candidates=candidates)) for _ in range(10)]
        for r in results[1:]:
            for i, rule in enumerate(r.rules):
                assert rule.slot == results[0].rules[i].slot


class TestRuleBuilderCounts:
    def test_correct_category_counts(self):
        analysis = AnalysisResult(
            exalted_candidates=[
                ExaltedCandidate(base_key=('A', 1, 1), affixes=frozenset([(None, 'X', 1)]), score=10, semantic_priority=100),
                ExaltedCandidate(base_key=('B', 2, 2), affixes=frozenset([(None, 'Y', 2)]), score=20, semantic_priority=100)
            ],
            idol_candidates=[IdolCandidate(size='S1', modifiers=frozenset([(None, 'M', 0)]), score=30, semantic_priority=70)],
            unique_candidates=[UniqueCandidate(name=f'U{i}', score=40+i, semantic_priority=40) for i in range(3)]
        )
        result = RuleBuilder().build(analysis)
        assert result.exalted_count == 2
        assert result.idol_count == 1
        assert result.unique_count == 3
        assert result.total_count == 6
    
    def test_correct_total_rule_count(self):
        analysis = AnalysisResult(
            exalted_candidates=[ExaltedCandidate(base_key=(f'A{i}', i, i), affixes=frozenset([(None, 'X', 1)]), score=10, semantic_priority=100) for i in range(10)],
            idol_candidates=[IdolCandidate(size=f'S{i}', modifiers=frozenset([(None, 'M', 0)]), score=20, semantic_priority=70) for i in range(5)]
        )
        result = RuleBuilder().build(analysis)
        assert result.total_count == result.exalted_count + result.idol_count


class TestRuleBuilder140Limit:
    def test_over_140_rules_are_not_deleted(self):
        candidates = [
            ExaltedCandidate(base_key=(f'Slot{i}', i%10, i%5), affixes=frozenset([]), score=100-i, semantic_priority=100)
            for i in range(150)
        ]
        result = RuleBuilder().build(AnalysisResult(exalted_candidates=candidates))
        assert result.total_count == 150
        assert len(result.rules) == 150
    
    def test_over_140_produces_exceeds_limit_warning(self):
        candidates = [
            ExaltedCandidate(base_key=(f'S{i}', i%10, i%5), affixes=frozenset([(None, 'A', 1)]), score=10, semantic_priority=100)
            for i in range(145)
        ]
        result = RuleBuilder().build(AnalysisResult(exalted_candidates=candidates))
        assert result.exceeds_limit
        assert result.total_count == 145


class TestRuleBuilderImmutability:
    def test_rulebuilder_does_not_mutate_analysis_result(self):
        original_sources = {'source1'}
        candidate = ExaltedCandidate(
            base_key=('Test', 1, 1), affixes=frozenset([(None, 'Stat', 2)]),
            sources=original_sources, score=50.0, semantic_priority=100
        )
        analysis = AnalysisResult(exalted_candidates=[candidate])
        result = RuleBuilder().build(analysis)
        
        assert len(analysis.exalted_candidates) == 1
        assert analysis.exalted_candidates[0].score == 50.0
        
        result.rules[0].sources.add('source2')
        assert len(original_sources) == 1
