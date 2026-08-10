"""RuleOptimizer performs lossless merging of FilterRules.

RuleOptimizer Part 3A: Lossless merge only
- Does NOT perform pruning
- Does NOT enforce 140 rule limit
- Does NOT generate XML
- Does NOT mutate input

Merge policy:
- Exact duplicate merge for all categories
- Exalted: merge same affixes + same slot + different confirmed item_types ONLY
  (sub_type differences NOT merged until semantics confirmed)
- Unique: merge different unique IDs (preserving ID<->name pairing)
- Idol: merge same modifiers + different sizes
- Does NOT merge partial affix overlap
- Does NOT perform tier relaxation

Score policy:
- Use max(component scores) - exact recalculation not possible without Analyzer formula
- Documented as conservative deterministic fallback

Statistics policy:
- sources = union of all component sources
- source_count = len(sources)
- occurrence_count = max(component occurrence_count) - conservative, avoids potential double-count
- build_count = max(component build_count) - conservative until build identities available
  (sum would risk double-counting same build appearing in multiple merged rules)

Ordering policy:
- semantic_priority DESC
- score DESC
- stable identity ASC (no hash())
"""
import logging
from typing import Dict, FrozenSet, List, Tuple
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

        # Store unique ID<->name as immutable pair to preserve mapping
        unique_items = frozenset()
        if rule.unique_id is not None or rule.unique_name:
            unique_items = frozenset([(rule.unique_id, rule.unique_name or '')])

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
            unique_items=unique_items,
            max_tier=rule.max_tier,
            avg_tier=rule.avg_tier,
            reason=rule.reason,
            merged_count=1
        )

    def _merge_exalted(self, rules: List[OptimizedRule]) -> Tuple[List[OptimizedRule], int]:
        """Merge Exalted rules.

        Merge policy:
        - Exact duplicates: same slot + same affixes + same item_types
        - Cross-base: same slot + same affixes + different CONFIRMED item_types
        - Does NOT merge different sub_type until subType semantics confirmed
        - Does NOT merge partial affix overlap
        - Does NOT perform tier relaxation

        Args:
            rules: List of Exalted OptimizedRules

        Returns:
            Tuple of (merged rules, count of rules that were merged away)
        """
        if not rules:
            return [], 0

        # Group by (slot, affixes) for merge candidates
        merge_groups: Dict[Tuple[str, FrozenSet], List[OptimizedRule]] = {}
        for rule in rules:
            key = (rule.slot or '', rule.affixes)
            merge_groups.setdefault(key, []).append(rule)

        merged_rules = []
        merge_count = 0

        for key, group in merge_groups.items():
            if len(group) == 1:
                # No merge needed
                merged_rules.append(group[0])
            else:
                # Check if merge is safe: can only merge if item_type differs
                # but sub_type is same (or we have confirmed EquipmentType coverage)
                sub_groups = self._split_exalted_by_merge_safety(group)
                for sub_group in sub_groups:
                    if len(sub_group) == 1:
                        merged_rules.append(sub_group[0])
                    else:
                        merged = self._merge_exalted_group(sub_group)
                        merged_rules.append(merged)
                        merge_count += len(sub_group) - 1

        return merged_rules, merge_count

    def _split_exalted_by_merge_safety(self, group: List[OptimizedRule]) -> List[List[OptimizedRule]]:
        """Split exalted group into mergeable sub-groups.

        Only merge rules where differences can be represented via confirmed EquipmentType.
        Do NOT merge rules with different sub_type until subType semantics confirmed.

        Args:
            group: List of rules with same slot and affixes

        Returns:
            List of sub-groups that can be safely merged
        """
        # Group by sub_type - only merge within same sub_type group
        # (different item_type with same sub_type can merge via multiple EquipmentType)
        sub_type_groups: Dict[Tuple, List[OptimizedRule]] = {}

        for rule in group:
            # Extract all sub_types from item_types list
            sub_types = frozenset(sub_type for _, sub_type in rule.item_types)
            sub_type_groups.setdefault(sub_types, []).append(rule)

        return list(sub_type_groups.values())

    def _merge_exalted_group(self, group: List[OptimizedRule]) -> OptimizedRule:
        """Merge a group of Exalted rules with same slot and affixes.

        Args:
            group: List of OptimizedRules with identical slot and affixes

        Returns:
            Single merged OptimizedRule
        """
        # Use first rule as base
        base = group[0]

        # Aggregate statistics - use CONSERVATIVE policies
        all_sources = set()
        max_build_count = base.build_count
        max_occurrence_count = base.occurrence_count
        max_score = base.score
        all_item_types = []
        merged_count = 0
        max_max_tier = base.max_tier
        sum_avg_tier = 0.0

        for rule in group:
            all_sources.update(rule.sources)
            # Conservative: use max to avoid double-counting builds
            max_build_count = max(max_build_count, rule.build_count)
            max_occurrence_count = max(max_occurrence_count, rule.occurrence_count)
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
            f"build_count={max_build_count} (max, conservative), "
            f"sources={len(all_sources)}"
        )

        return OptimizedRule(
            category=base.category,
            semantic_priority=base.semantic_priority,
            score=max_score,
            build_count=max_build_count,
            occurrence_count=max_occurrence_count,
            source_count=len(all_sources),
            sources=all_sources,
            slot=base.slot,
            item_types=all_item_types,
            affixes=base.affixes,
            idol_sizes=[],
            modifiers=frozenset(),
            unique_items=frozenset(),
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

        # Aggregate statistics - use CONSERVATIVE policies
        all_sources = set()
        max_build_count = base.build_count
        max_occurrence_count = base.occurrence_count
        max_score = base.score
        all_sizes = []
        merged_count = 0

        for rule in group:
            all_sources.update(rule.sources)
            # Conservative: use max to avoid double-counting builds
            max_build_count = max(max_build_count, rule.build_count)
            max_occurrence_count = max(max_occurrence_count, rule.occurrence_count)
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
            f"build_count={max_build_count} (max, conservative), "
            f"sources={len(all_sources)}"
        )

        return OptimizedRule(
            category=base.category,
            semantic_priority=base.semantic_priority,
            score=max_score,
            build_count=max_build_count,
            occurrence_count=max_occurrence_count,
            source_count=len(all_sources),
            sources=all_sources,
            slot=None,
            item_types=[],
            affixes=frozenset(),
            idol_sizes=all_sizes,
            modifiers=base.modifiers,
            unique_items=frozenset(),
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

        # Aggregate statistics - use CONSERVATIVE policies
        all_sources = set()
        max_build_count = base.build_count
        max_occurrence_count = base.occurrence_count
        max_score = base.score
        all_unique_items = set()
        merged_count = 0

        for rule in group:
            all_sources.update(rule.sources)
            # Conservative: use max to avoid double-counting builds
            max_build_count = max(max_build_count, rule.build_count)
            max_occurrence_count = max(max_occurrence_count, rule.occurrence_count)
            max_score = max(max_score, rule.score)
            all_unique_items.update(rule.unique_items)
            merged_count += rule.merged_count

        # Build reason
        name_str = f"{len(all_unique_items)} unique item(s)" if len(all_unique_items) > 1 else (
            list(all_unique_items)[0][1] if all_unique_items else "unknown"
        )
        reason = (
            f"Unique {name_str} - "
            f"merged from {merged_count} rule(s), "
            f"build_count={max_build_count} (max, conservative), "
            f"sources={len(all_sources)}"
        )

        return OptimizedRule(
            category=base.category,
            semantic_priority=base.semantic_priority,
            score=max_score,
            build_count=max_build_count,
            occurrence_count=max_occurrence_count,
            source_count=len(all_sources),
            sources=all_sources,
            slot=base.slot,
            item_types=[],
            affixes=frozenset(),
            idol_sizes=[],
            modifiers=frozenset(),
            unique_items=frozenset(all_unique_items),
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
            # Use unique_items directly for stable sorting (preserves ID<->name pairing)
            identity = (
                rule.category,
                tuple(sorted(rule.unique_items))
            )
        else:
            identity = (rule.category,)

        return (
            -rule.semantic_priority,
            -rule.score,
            identity
        )
