"""RuleBuilder converts Analyzer results into intermediate rule candidates."""
import logging
from typing import List
from app.analyzer.models import AnalysisResult, ExaltedCandidate, IdolCandidate, UniqueCandidate
from app.generator.rule_models import FilterRule, RuleBuildResult

logger = logging.getLogger(__name__)

class RuleBuilder:
    def build(self, analysis_result: AnalysisResult) -> RuleBuildResult:
        rules = []
        for c in analysis_result.exalted_candidates:
            rules.append(self._convert_exalted(c))
        for c in analysis_result.idol_candidates:
            rules.append(self._convert_idol(c))
        for c in analysis_result.unique_candidates:
            rules.append(self._convert_unique(c))
        rules.sort(key=lambda r: (-r.semantic_priority, -r.score, self._get_stable_identity(r)))
        result = RuleBuildResult(rules=rules, exalted_count=len(analysis_result.exalted_candidates),
            idol_count=len(analysis_result.idol_candidates), unique_count=len(analysis_result.unique_candidates))
        if result.exceeds_limit:
            logger.warning(f"Rule count ({result.total_count}) exceeds 140")
        return result

    def _convert_exalted(self, c: ExaltedCandidate) -> FilterRule:
        slot, item_type, sub_type = c.base_key
        affix_names = [n for aid, n, t in sorted(c.affixes)]
        reason = f"Exalted {slot} - {c.build_count} builds"
        return FilterRule(category="exalted", semantic_priority=c.semantic_priority, score=c.score,
            build_count=c.build_count, occurrence_count=c.occurrence_count, source_count=len(c.sources),
            sources=c.sources.copy(), slot=slot, item_type=item_type, sub_type=sub_type,
            affixes=c.affixes, max_tier=c.max_tier, avg_tier=c.avg_tier, reason=reason)
    
    def _convert_idol(self, c: IdolCandidate) -> FilterRule:
        reason = f"Idol {c.size} - {c.build_count} builds"
        return FilterRule(category="idol", semantic_priority=c.semantic_priority, score=c.score,
            build_count=c.build_count, occurrence_count=c.occurrence_count, source_count=len(c.sources),
            sources=c.sources.copy(), idol_size=c.size, modifiers=c.modifiers, reason=reason)
    
    def _convert_unique(self, c: UniqueCandidate) -> FilterRule:
        reason = f"Unique {c.name} - {c.build_count} builds"
        return FilterRule(category="unique", semantic_priority=c.semantic_priority, score=c.score,
            build_count=c.build_count, occurrence_count=c.occurrence_count, source_count=len(c.sources),
            sources=c.sources.copy(), unique_name=c.name, unique_id=c.unique_id, slot=c.slot, reason=reason)
    
    def _get_stable_identity(self, r: FilterRule):
        if r.category == "exalted":
            return (r.category, r.slot or "", r.item_type or 0, r.sub_type or 0, tuple(sorted(r.affixes)))
        elif r.category == "idol":
            return (r.category, r.idol_size or "", tuple(sorted(r.modifiers)))
        else:
            return (r.category, r.unique_name or "", r.unique_id or 0)
