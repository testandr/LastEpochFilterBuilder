"""RuleOptimizer performs lossless merging of FilterRules.

RuleOptimizer Part 3A: Lossless merge only
- Does NOT perform pruning
- Does NOT enforce 140 rule limit
- Does NOT generate XML
- Does NOT mutate input

Merge policy:
- Exact duplicate merge for all categories
- Exalted: merge same affixes + different item types (cross-base)
- Unique: merge different unique IDs
- Idol: merge same modifiers + different sizes
- Does NOT merge partial affix overlap
- Does NOT perform tier relaxation

Score policy:
- Use max(component scores) when exact recalculation is not possible
- Documented as deterministic fallback

Statistics policy:
- sources = union of all component sources
- source_count = len(sources)
- occurrence_count = sum (only when semantically correct)
- build_count = sum (acknowledges potential double-counting)

Ordering policy:
- semantic_priority DESC
- score DESC
- stable identity ASC (no hash())
"""
import logging
from typing import Dict, List, Tuple
from app.generator.rule_models import FilterRule, RuleBuildResult, OptimizedRule, OptimizationResult

logger = logging.getLogger(__name__)


class RuleOptimizer:
    """Lossless rule optimizer for reducing rule count through safe merging."""

    def optimize(self, input_result: RuleBuildResult) -> OptimizationResult:
        """Optimize rules through lossless merging.

        Args:
            input_result: RuleBuildResult from RuleBuilder

        Returns:
            OptimizationResult with optimized rules and statistics
        """
        logger.info(f"Starting rule optimization: {input_result.total_count} input rules")

        # Step 1: Convert FilterRule -> OptimizedRule (1:1)
        optimized_rules = [self._convert_to_optimized(rule) for rule in input_result.rules]

        # Step 2: Lossless merge by category
        exalted_rules = [r for r in optimized_rules if r.category == 'exalted']
        idol_rules = [r for r in optimized_rules if r.category == 'idol']
        unique_rules = [r for r in optimized_rules if r.category == 'unique']

        merged_exalted, exalted_merge_count = self._merge_exalted(exalted_rules)
        merged_idol, idol_merge_count = self._merge_idol(idol_rules)
        merged_unique, unique_merge_count = self._merge_unique(unique_rules)

        # Step 3: Combine and sort deterministically
        all_merged = merged_exalted + merged_idol + merged_unique
        all_merged.sort(key=self._stable_sort_key)

        result = OptimizationResult(
            rules=all_merged,
            original_count=input_result.total_count,
            optimized_count=len(all_merged),
            exalted_merged=exalted_merge_count,
            idol_merged=idol_merge_count,
            unique_merged=unique_merge_count
        )

        logger.info(
            f"Optimization complete: {result.original_count} -> {result.optimized_count} rules "
            f"({result.total_merged} merged)"
        )

        return result

    def _convert_to_optimized(self, rule: FilterRule) -> OptimizedRule:
        """Convert FilterRule to OptimizedRule (1:1).

        Args:
            rule: FilterRule from RuleBuilder

        Returns:
            OptimizedRule with single-rule data
        """
        item_types = [(rule.item_type, rule.sub_type)] if rule.item_type is not None else []
        idol_sizes = [rule.idol_size] if rule.idol_size else []
        unique_names = [rule.unique_name] if rule.unique_name else []
        unique_ids = [rule.unique_id] if rule.unique_id is not None else []

        return OptimizedRule(
            category=rule.category,
            semantic_priority=rule.semantic_priority,
            score=rule.score,
            build_count=rule.build_count,
            occurrence_count=rule.occurrence_count,
            source_count=rule.source_count,
            sources=rule.sources.copy(),
            slot=rule.slot,
            item_types=item_types,
            affixes=rule.affixes,
            idol_sizes=idol_sizes,
            modifiers=rule.modifiers,
            unique_names=unique_names,
            unique_ids=unique_ids,
            max_tier=rule.max_tier,
            avg_tier=rule.avg_tier,
            reason=rule.reason,
            merged_count=1
        )

    def _merge_exalted(self, rules: List[OptimizedRule]) -> Tuple[List[OptimizedRule], int]:
        """Merge Exalted rules.

        Merge policy:
        - Exact duplicates: same affixes + same item_types
        - Cross-base: same affixes + different item_types
        - Does NOT merge partial affix overlap
        - Does NOT perform tier relaxation

        Args:
            rules: List of Exalted OptimizedRules

        Returns:
            Tuple of (merged rules, count of rules that were merged away)
        """
        if not rules:
            return [], 0

        # Group by affixes (key for merge candidates)
        affix_groups: Dict[FrozenSet, List[OptimizedRule]] = {}
        for rule in rules:
            affix_groups.setdefault(rule.affixes, []).append(rule)

        merged_rules = []
        merge_count = 0

        for affixes, group in affix_groups.items():
            if len(group) == 1:
                # No merge needed
                merged_rules.append(group[0])
            else:
                # Merge group into single rule
                merged = self._merge_exalted_group(group)
                merged_rules.append(merged)
                merge_count += len(group) - 1

        return merged_rules, merge_count

    def _merge_exalted_group(self, group: List[OptimizedRule]) -> OptimizedRule:
        """Merge a group of Exalted rules with same affixes.

        Args:
            group: List of OptimizedRules with identical affixes

        Returns:
            Single merged OptimizedRule
        """
        # Use first rule as base
        base = group[0]

        # Aggregate statistics
        all_sources = set()
        total_build_count = 0
        total_occurrence_count = 0
        max_score = base.score
        all_item_types = []
        merged_count = 0
        max_max_tier = base.max_tier
        sum_avg_tier = 0.0

        for rule in group:
            all_sources.update(rule.sources)
            total_build_count += rule.build_count
            total_occurrence_count += rule.occurrence_count
            max_score = max(max_score, rule.score)
            all_item_types.extend(rule.item_types)
            merged_count += rule.merged_count
            max_max_tier = max(max_max_tier, rule.max_tier)
            sum_avg_tier += rule.avg_tier * rule.merged_count

        avg_avg_tier = sum_avg_tier / merged_count if merged_count > 0 else 0.0

        # Build reason
        item_type_str = f"{len(all_item_types)} base variant(s)" if len(all_item_types) > 1 else "1 base"
        affix_names = [name for name, tier in sorted(base.affixes)]
        reason = (
            f"Exalted {base.slot} with {len(base.affixes)} affix(es) "
            f"({', '.join(affix_names[:3])}{'...' if len(affix_names) > 3 else ''}) - "
            f"{item_type_str}, merged from {merged_count} rule(s), "
            f"used by {total_build_count} build(s) across {len(all_sources)} source(s)"
        )

        return OptimizedRule(
            category=base.category,
            semantic_priority=base.semantic_priority,
            score=max_score,
            build_count=total_build_count,
            occurrence_count=total_occurrence_count,
            source_count=len(all_sources),
            sources=all_sources,
            slot=base.slot,
            item_types=all_item_types,
            affixes=base.affixes,
            idol_sizes=[],
            modifiers=frozenset(),
            unique_names=[],
            unique_ids=[],
            max_tier=max_max_tier,
            avg_tier=avg_avg_tier,
            reason=reason,
            merged_count=merged_count
        )

    def _merge_idol(self, rules: List[OptimizedRule]) -> Tuple[List[OptimizedRule], int]:
        """Merge Idol rules.

        Merge policy:
        - Exact duplicates: same modifiers + same size
        - Cross-size: same modifiers + different sizes
        - Does NOT merge different modifiers

        Args:
            rules: List of Idol OptimizedRules

        Returns:
            Tuple of (merged rules, count of rules that were merged away)
        """
        if not rules:
            return [], 0

        # Group by modifiers (key for merge candidates)
        modifier_groups: Dict[FrozenSet, List[OptimizedRule]] = {}
        for rule in rules:
            modifier_groups.setdefault(rule.modifiers, []).append(rule)

        merged_rules = []
        merge_count = 0

        for modifiers, group in modifier_groups.items():
            if len(group) == 1:
                # No merge needed
                merged_rules.append(group[0])
            else:
                # Merge group into single rule
                merged = self._merge_idol_group(group)
                merged_rules.append(merged)
                merge_count += len(group) - 1

        return merged_rules, merge_count

    def _merge_idol_group(self, group: List[OptimizedRule]) -> OptimizedRule:
        """Merge a group of Idol rules with same modifiers.

        Args:
            group: List of OptimizedRules with identical modifiers

        Returns:
            Single merged OptimizedRule
        """
        # Use first rule as base
        base = group[0]

        # Aggregate statistics
        all_sources = set()
        total_build_count = 0
        total_occurrence_count = 0
        max_score = base.score
        all_sizes = []
        merged_count = 0

        for rule in group:
            all_sources.update(rule.sources)
            total_build_count += rule.build_count
            total_occurrence_count += rule.occurrence_count
            max_score = max(max_score, rule.score)
            all_sizes.extend(rule.idol_sizes)
            merged_count += rule.merged_count

        # Build reason
        size_str = f"{len(all_sizes)} size variant(s)" if len(all_sizes) > 1 else (all_sizes[0] if all_sizes else "unknown size")
        mod_list = sorted(base.modifiers)
        reason = (
            f"Idol {size_str} with {len(base.modifiers)} modifier(s) "
            f"({', '.join(mod_list[:3])}{'...' if len(mod_list) > 3 else ''}) - "
            f"merged from {merged_count} rule(s), "
            f"used by {total_build_count} build(s) across {len(all_sources)} source(s)"
        )

        return OptimizedRule(
            category=base.category,
            semantic_priority=base.semantic_priority,
            score=max_score,
            build_count=total_build_count,
            occurrence_count=total_occurrence_count,
            source_count=len(all_sources),
            sources=all_sources,
            slot=None,
            item_types=[],
            affixes=frozenset(),
            idol_sizes=all_sizes,
            modifiers=base.modifiers,
            unique_names=[],
            unique_ids=[],
            max_tier=0,
            avg_tier=0.0,
            reason=reason,
            merged_count=merged_count
        )

    def _merge_unique(self, rules: List[OptimizedRule]) -> Tuple[List[OptimizedRule], int]:
        """Merge Unique rules.

        Merge policy:
        - Different unique IDs can be merged
        - Unique name/ID mappings preserved in lists

        Args:
            rules: List of Unique OptimizedRules

        Returns:
            Tuple of (merged rules, count of rules that were merged away)
        """
        if not rules:
            return [], 0

        # For Part 3A: merge ALL unique rules into one (simple case)
        # More sophisticated grouping (by slot, etc.) can be added later
        if len(rules) == 1:
            return rules, 0

        merged = self._merge_unique_group(rules)
        return [merged], len(rules) - 1

    def _merge_unique_group(self, group: List[OptimizedRule]) -> OptimizedRule:
        """Merge a group of Unique rules.

        Args:
            group: List of Unique OptimizedRules

        Returns:
            Single merged OptimizedRule
        """
        # Use first rule as base
        base = group[0]

        # Aggregate statistics
        all_sources = set()
        total_build_count = 0
        total_occurrence_count = 0
        max_score = base.score
        all_names = []
        all_ids = []
        merged_count = 0

        for rule in group:
            all_sources.update(rule.sources)
            total_build_count += rule.build_count
            total_occurrence_count += rule.occurrence_count
            max_score = max(max_score, rule.score)
            all_names.extend(rule.unique_names)
            all_ids.extend(rule.unique_ids)
            merged_count += rule.merged_count

        # Build reason
        name_str = f"{len(all_names)} unique item(s)" if len(all_names) > 1 else (all_names[0] if all_names else "unknown")
        reason = (
            f"Unique {name_str} - "
            f"merged from {merged_count} rule(s), "
            f"used by {total_build_count} build(s) across {len(all_sources)} source(s)"
        )

        return OptimizedRule(
            category=base.category,
            semantic_priority=base.semantic_priority,
            score=max_score,
            build_count=total_build_count,
            occurrence_count=total_occurrence_count,
            source_count=len(all_sources),
            sources=all_sources,
            slot=base.slot,
            item_types=[],
            affixes=frozenset(),
            idol_sizes=[],
            modifiers=frozenset(),
            unique_names=all_names,
            unique_ids=all_ids,
            max_tier=0,
            avg_tier=0.0,
            reason=reason,
            merged_count=merged_count
        )

    def _stable_sort_key(self, rule: OptimizedRule) -> tuple:
        """Generate stable sort key for deterministic ordering.

        Ordering policy:
        1. semantic_priority DESC -> use negative
        2. score DESC -> use negative
        3. stable identity ASC

        Args:
            rule: OptimizedRule to generate key for

        Returns:
            Tuple for sorting
        """
        # Build stable identity based on category
        if rule.category == 'exalted':
            identity = (
                rule.category,
                rule.slot or '',
                tuple(sorted(rule.item_types)),
                tuple(sorted(rule.affixes))
            )
        elif rule.category == 'idol':
            identity = (
                rule.category,
                tuple(sorted(rule.idol_sizes)),
                tuple(sorted(rule.modifiers))
            )
        elif rule.category == 'unique':
            identity = (
                rule.category,
                tuple(sorted(rule.unique_names)),
                tuple(sorted(rule.unique_ids, key=lambda x: x if x is not None else -1))
            )
        else:
            identity = (rule.category,)

        return (
            -rule.semantic_priority,
            -rule.score,
            identity
        )
