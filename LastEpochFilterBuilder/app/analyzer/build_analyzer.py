"""Build analyzer for Last Epoch loot filter candidate generation.

Processes normalized BuildDetails from multiple S-Tier builds and produces
aggregated filter candidates (Exalted, Idol, Unique) with scoring and statistics.
"""
import logging
from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple

from app.analyzer.models import (
    AnalysisResult,
    AnalysisStats,
    BaseKey,
    ExaltedCandidate,
    IdolCandidate,
    IndividualModifierStats,
    UniqueCandidate,
)
from app.analyzer.priority_calculator import PriorityCalculator
from app.dto.models import AffixDTO, BuildDetails, IdolDTO, ItemDTO

logger = logging.getLogger(__name__)


class BuildAnalyzer:
    """Analyzes multiple builds and generates filter candidates.

    Key features:
    - Build deduplication by source_url (or normalized name fallback)
    - Exalted aggregation by (slot, itemType, subType) + affix combination
    - Idol aggregation by size + full modifier combination
    - Unique aggregation by unique_id + name
    - Transparent scoring via PriorityCalculator
    - Estimated rule count tracking
    """

    def __init__(self):
        """Initialize analyzer with priority calculator."""
        self.calculator = PriorityCalculator()

    def analyze(
        self,
        builds: List[BuildDetails],
        source_mapping: Optional[Dict[str, str]] = None
    ) -> AnalysisResult:
        """Analyze multiple builds and generate filter candidates.

        Args:
            builds: List of BuildDetails from S-Tier builds
            source_mapping: Optional mapping from build name/url to source category
                           (e.g., {"Build A": "corruption", "Build B": "bossing"})

        Returns:
            AnalysisResult with aggregated candidates and statistics
        """
        if source_mapping is None:
            source_mapping = {}

        logger.info(f"Starting analysis of {len(builds)} builds")

        # Dedupe builds
        unique_builds, build_to_source = self._dedupe_builds(builds, source_mapping)

        # Initialize aggregation structures
        exalted_map: Dict[Tuple[BaseKey, frozenset], ExaltedCandidate] = {}
        idol_map: Dict[Tuple[Optional[str], frozenset], IdolCandidate] = {}
        unique_map: Dict[Tuple[str, Optional[int]], UniqueCandidate] = {}
        modifier_stats_map: Dict[str, IndividualModifierStats] = {}

        # Track stats
        stats = AnalysisStats()
        stats.builds_analyzed = len(builds)
        stats.unique_builds = len(unique_builds)

        # Process each unique build
        for build_id, build_list in unique_builds.items():
            # All builds in build_list are variants of same build
            sources = build_to_source[build_id]

            # Process all variants to count occurrences
            for build in build_list:
                stats.total_raw_items += len(build.items)
                stats.total_raw_idols += len(build.idols)

                # Track uniques count
                stats.total_raw_uniques += sum(1 for item in build.items if item.is_unique)

                # Aggregate exalted items
                self._aggregate_exalted(
                    build.items,
                    build_id,
                    sources,
                    exalted_map,
                    is_first=(build == build_list[0])
                )

                # Aggregate idols
                self._aggregate_idols(
                    build.idols,
                    build_id,
                    sources,
                    idol_map,
                    modifier_stats_map,
                    is_first=(build == build_list[0])
                )

                # Aggregate uniques
                self._aggregate_uniques(
                    build.items,
                    build_id,
                    sources,
                    unique_map,
                    is_first=(build == build_list[0])
                )

        # Convert to lists and calculate average tiers
        exalted_candidates = list(exalted_map.values())
        idol_candidates = list(idol_map.values())
        unique_candidates = list(unique_map.values())
        modifier_stats = modifier_stats_map

        # Finalize exalted avg_tier
        for candidate in exalted_candidates:
            if candidate.occurrence_count > 0:
                candidate.avg_tier = candidate.tier_sum / candidate.occurrence_count

        # Calculate scores
        self.calculator.calculate_all_scores(
            exalted_candidates,
            idol_candidates,
            unique_candidates
        )

        # Update stats
        stats.exalted_candidates = len(exalted_candidates)
        stats.idol_candidates = len(idol_candidates)
        stats.unique_candidates = len(unique_candidates)

        # Estimate rule counts (approximate - exact mapping happens in XML generator)
        stats.estimated_exalted_rules = self._estimate_exalted_rules(exalted_candidates)
        stats.estimated_idol_rules = len(idol_candidates)  # 1:1 for idols
        stats.estimated_unique_rules = len(unique_candidates)  # 1:1 for uniques

        # Build result
        result = AnalysisResult(
            exalted_candidates=exalted_candidates,
            idol_candidates=idol_candidates,
            unique_candidates=unique_candidates,
            modifier_stats=modifier_stats,
            stats=stats
        )

        # Sort by score
        result.sort_candidates()

        logger.info(
            f"Analysis complete: {stats.exalted_candidates} exalted, "
            f"{stats.idol_candidates} idols, {stats.unique_candidates} uniques. "
            f"Estimated rules: {stats.estimated_total_rules}"
        )

        if stats.exceeds_limit:
            logger.warning(
                f"Estimated rule count ({stats.estimated_total_rules}) exceeds "
                f"140 limit. Optimization will be needed."
            )

        return result

    def _dedupe_builds(
        self,
        builds: List[BuildDetails],
        source_mapping: Dict[str, str]
    ) -> Tuple[Dict[str, List[BuildDetails]], Dict[str, Set[str]]]:
        """Deduplicate builds by source_url or normalized name.

        Returns:
            (unique_builds, build_to_source)
            unique_builds: Dict[build_id, List[BuildDetails]] - all variants
            build_to_source: Dict[build_id, Set[source]] - sources for each build
        """
        unique_builds: Dict[str, List[BuildDetails]] = defaultdict(list)
        build_to_source: Dict[str, Set[str]] = defaultdict(set)

        for build in builds:
            # Build identity: prefer source_url, fallback to normalized name
            build_id = build.source_url if build.source_url else self._normalize_name(build.name)

            unique_builds[build_id].append(build)

            # Determine source
            source = source_mapping.get(build.name) or source_mapping.get(build.source_url or "")
            if source:
                build_to_source[build_id].add(source)
            else:
                # Default source if not mapped
                build_to_source[build_id].add("unknown")

        logger.info(f"Deduplicated {len(builds)} builds into {len(unique_builds)} unique builds")

        return dict(unique_builds), dict(build_to_source)

    def _normalize_name(self, name: Optional[str]) -> str:
        """Normalize build name for deduplication fallback."""
        if not name:
            return "unknown_build"
        return name.strip().lower().replace(" ", "_")

    def _aggregate_exalted(
        self,
        items: List[ItemDTO],
        build_id: str,
        sources: Set[str],
        exalted_map: Dict[Tuple[BaseKey, frozenset], ExaltedCandidate],
        is_first: bool
    ) -> None:
        """Aggregate exalted items into candidates.

        Args:
            items: Items from build
            build_id: Unique build identifier
            sources: Source categories for this build
            exalted_map: Aggregation map
            is_first: True if this is the first variant of the build
        """
        for item in items:
            # Only process exalted items
            if not item.is_exalted or item.is_unique:
                continue

            # Build base key (slot, itemType, subType)
            item_type = item.additional.get("itemType") if item.additional else None
            sub_type = item.additional.get("subType") if item.additional else None
            base_key: BaseKey = (item.slot, item_type, sub_type)

            # Build affix set (affix_id, name, tier) - frozen for hashability
            affix_set = frozenset(
                (affix.affix_id, affix.name, affix.tier or 0)
                for affix in item.affixes
                if affix.name and affix.tier
            )

            if not affix_set:
                continue  # Skip items without affixes

            key = (base_key, affix_set)

            if key not in exalted_map:
                # Create new candidate
                exalted_map[key] = ExaltedCandidate(
                    base_key=base_key,
                    affixes=affix_set
                )

            candidate = exalted_map[key]

            # Update build_count only for first variant
            if is_first:
                candidate.build_count += 1

            # Always update occurrence_count
            candidate.occurrence_count += 1

            # Update sources
            candidate.sources.update(sources)

            # Update tier tracking
            for _, _, tier in affix_set:
                candidate.max_tier = max(candidate.max_tier, tier)
                candidate.tier_sum += tier

    def _aggregate_idols(
        self,
        idols: List[IdolDTO],
        build_id: str,
        sources: Set[str],
        idol_map: Dict[Tuple[Optional[str], frozenset], IdolCandidate],
        modifier_stats_map: Dict[str, IndividualModifierStats],
        is_first: bool
    ) -> None:
        """Aggregate idols into candidates and track individual modifier stats.

        Args:
            idols: Idols from build
            build_id: Unique build identifier
            sources: Source categories
            idol_map: Aggregation map
            modifier_stats_map: Individual modifier statistics
            is_first: True if first variant
        """
        for idol in idols:
            # Build modifier set (affix_id, name, tier) - frozen for hashability
            # Backward compatibility: if modifier_affixes is empty, fallback to old string modifiers
            if idol.modifier_affixes:
                modifier_set = frozenset(
                    (affix.affix_id, affix.name, affix.tier or 0)
                    for affix in idol.modifier_affixes
                    if affix.name and affix.tier
                )
            elif idol.modifiers:
                # Fallback for old synthetic tests: parse display string "Name Tx" -> (None, Name, x)
                modifier_set = frozenset((None, mod, 0) for mod in idol.modifiers)
            else:
                modifier_set = frozenset()

            if not modifier_set:
                continue  # Skip empty idols

            key = (idol.size, modifier_set)

            if key not in idol_map:
                # Create new candidate
                idol_map[key] = IdolCandidate(
                    size=idol.size,
                    modifiers=modifier_set
                )

            candidate = idol_map[key]

            # Update build_count only for first variant
            if is_first:
                candidate.build_count += 1

            # Always update occurrence_count
            candidate.occurrence_count += 1

            # Update sources
            candidate.sources.update(sources)

            # Track individual modifiers
            for _, modifier_name, _ in modifier_set:
                if modifier_name not in modifier_stats_map:
                    modifier_stats_map[modifier_name] = IndividualModifierStats(modifier=modifier_name)

                mod_stats = modifier_stats_map[modifier_name]

                if is_first:
                    mod_stats.build_count += 1

                mod_stats.occurrence_count += 1

                if idol.size:
                    mod_stats.sizes.add(idol.size)

                mod_stats.sources.update(sources)

    def _aggregate_uniques(
        self,
        items: List[ItemDTO],
        build_id: str,
        sources: Set[str],
        unique_map: Dict[Tuple[str, Optional[int]], UniqueCandidate],
        is_first: bool
    ) -> None:
        """Aggregate unique items into candidates.

        Args:
            items: Items from build
            build_id: Unique build identifier
            sources: Source categories
            unique_map: Aggregation map
            is_first: True if first variant
        """
        for item in items:
            if not item.is_unique:
                continue

            # Get unique_id from additional
            unique_id = item.additional.get("uniqueID") if item.additional else None

            key = (item.name, unique_id)

            if key not in unique_map:
                # Create new candidate
                unique_map[key] = UniqueCandidate(
                    name=item.name,
                    unique_id=unique_id,
                    slot=item.slot
                )

            candidate = unique_map[key]

            # Update build_count only for first variant
            if is_first:
                candidate.build_count += 1

            # Always update occurrence_count
            candidate.occurrence_count += 1

            # Update sources
            candidate.sources.update(sources)

    def _estimate_exalted_rules(self, candidates: List[ExaltedCandidate]) -> int:
        """Estimate number of XML rules needed for exalted candidates.

        This is approximate - actual rule count depends on XML generator logic.
        For now, assume 1 rule per candidate (base + affix requirements).

        Args:
            candidates: Exalted candidates

        Returns:
            Estimated rule count
        """
        # Simple 1:1 estimate for now
        # In practice, some candidates might be merged into compound rules
        return len(candidates)
