"""RuleBuilder converts Analyzer results into intermediate rule candidates.

RuleBuilder does NOT:
- Generate XML
- Optimize or merge rules
- Apply the 140 rule limit (only warns)
- Recalculate scores

RuleBuilder creates independent rule candidates that will be processed
by RuleOptimizer and XML Generator in later stages.
"""
import logging
from typing import List

from app.analyzer.models import (
    AnalysisResult,
    ExaltedCandidate,
    IdolCandidate,
    UniqueCandidate,
)
from app.generator.rule_models import FilterRule, RuleBuildResult

logger = logging.getLogger(__name__)


class RuleBuilder:
    """Converts Analyzer candidates into intermediate FilterRule objects.

    Each candidate from Analyzer becomes exactly one FilterRule.
    No merging, no optimization, no deletion.
    """

    def build(self, analysis_result: AnalysisResult) -> RuleBuildResult:
        """Convert AnalysisResult into RuleBuildResult.

        Args:
            analysis_result: Output from BuildAnalyzer

        Returns:
            RuleBuildResult with all rule candidates
        """
        logger.info("Starting rule building from analysis result")

        rules: List[FilterRule] = []

        # Convert Exalted candidates
        for candidate in analysis_result.exalted_candidates:
            rule = self._convert_exalted(candidate)
            rules.append(rule)

        # Convert Idol candidates
        for candidate in analysis_result.idol_candidates:
            rule = self._convert_idol(candidate)
            rules.append(rule)

        # Convert Unique candidates
        for candidate in analysis_result.unique_candidates:
            rule = self._convert_unique(candidate)
            rules.append(rule)

        # Sort rules deterministically:
        # 1. semantic_priority DESC
        # 2. score DESC
        # 3. stable by identity (category, then hash)
        rules.sort(key=lambda r: (
            -r.semantic_priority,
            -r.score,
            r.category,
            hash(r)
        ))

        # Build result
        result = RuleBuildResult(
            rules=rules,
            exalted_count=len(analysis_result.exalted_candidates),
            idol_count=len(analysis_result.idol_candidates),
            unique_count=len(analysis_result.unique_candidates)
        )

        logger.info(
            f"Rule building complete: {result.total_count} rules "
            f"(Exalted: {result.exalted_count}, Idol: {result.idol_count}, "
            f"Unique: {result.unique_count})"
        )

        if result.exceeds_limit:
            logger.warning(
                f"Rule count ({result.total_count}) exceeds 140 limit. "
                f"RuleOptimizer will be needed."
            )

        return result

    def _convert_exalted(self, candidate: ExaltedCandidate) -> FilterRule:
        """Convert ExaltedCandidate to FilterRule.

        Args:
            candidate: Exalted candidate from Analyzer

        Returns:
            FilterRule for exalted item
        """
        slot, item_type, sub_type = candidate.base_key

        # Build reason string
        affix_names = [name for name, tier in sorted(candidate.affixes)]
        reason = (
            f"Exalted {slot} with {len(candidate.affixes)} affix(es) "
            f"({', '.join(affix_names[:3])}{'...' if len(affix_names) > 3 else ''}) - "
            f"used by {candidate.build_count} build(s) "
            f"across {len(candidate.sources)} source(s)"
        )

        return FilterRule(
            category="exalted",
            semantic_priority=candidate.semantic_priority,
            score=candidate.score,
            build_count=candidate.build_count,
            occurrence_count=candidate.occurrence_count,
            source_count=len(candidate.sources),
            sources=candidate.sources.copy(),
            slot=slot,
            item_type=item_type,
            sub_type=sub_type,
            affixes=candidate.affixes,
            max_tier=candidate.max_tier,
            avg_tier=candidate.avg_tier,
            reason=reason
        )

    def _convert_idol(self, candidate: IdolCandidate) -> FilterRule:
        """Convert IdolCandidate to FilterRule.

        Args:
            candidate: Idol candidate from Analyzer

        Returns:
            FilterRule for idol
        """
        # Build reason string
        mod_list = sorted(candidate.modifiers)
        reason = (
            f"Idol {candidate.size or 'unknown size'} with "
            f"{len(candidate.modifiers)} modifier(s) "
            f"({', '.join(mod_list[:3])}{'...' if len(mod_list) > 3 else ''}) - "
            f"used by {candidate.build_count} build(s) "
            f"across {len(candidate.sources)} source(s)"
        )

        return FilterRule(
            category="idol",
            semantic_priority=candidate.semantic_priority,
            score=candidate.score,
            build_count=candidate.build_count,
            occurrence_count=candidate.occurrence_count,
            source_count=len(candidate.sources),
            sources=candidate.sources.copy(),
            idol_size=candidate.size,
            modifiers=candidate.modifiers,
            reason=reason
        )

    def _convert_unique(self, candidate: UniqueCandidate) -> FilterRule:
        """Convert UniqueCandidate to FilterRule.

        Args:
            candidate: Unique candidate from Analyzer

        Returns:
            FilterRule for unique item
        """
        # Build reason string
        reason = (
            f"Unique '{candidate.name}' "
            f"(ID: {candidate.unique_id if candidate.unique_id is not None else 'unknown'}) - "
            f"used by {candidate.build_count} build(s) "
            f"across {len(candidate.sources)} source(s)"
        )

        return FilterRule(
            category="unique",
            semantic_priority=candidate.semantic_priority,
            score=candidate.score,
            build_count=candidate.build_count,
            occurrence_count=candidate.occurrence_count,
            source_count=len(candidate.sources),
            sources=candidate.sources.copy(),
            unique_name=candidate.name,
            unique_id=candidate.unique_id,
            slot=candidate.slot,
            reason=reason
        )
