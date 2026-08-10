"""Priority calculation for filter candidates.

Provides transparent, explainable scoring formulas for Exalted, Idol, and Unique candidates.
"""
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.analyzer.models import ExaltedCandidate, IdolCandidate, UniqueCandidate

logger = logging.getLogger(__name__)


class PriorityCalculator:
    """Calculates priority scores for filter candidates.

    Score formulas are transparent and explainable:
    - Higher build_count = higher priority (item used in more builds)
    - Higher source_count = higher priority (item useful in multiple contexts)
    - Higher tier = higher priority (for exalted affixes)
    - Unique combination bonus (for complex requirements)

    Weights:
    - BUILD_WEIGHT: 10.0 (most important - how many builds use this)
    - SOURCE_WEIGHT: 5.0 (moderately important - versatility)
    - TIER_WEIGHT: 2.0 (for exalted - higher tiers preferred)
    - OCCURRENCE_WEIGHT: 0.5 (minor - raw occurrence count)
    """

    # Score weights
    BUILD_WEIGHT = 10.0
    SOURCE_WEIGHT = 5.0
    TIER_WEIGHT = 2.0
    OCCURRENCE_WEIGHT = 0.5

    # Bonus multipliers
    MULTI_AFFIX_BONUS = 1.2  # Bonus for exalted with multiple affixes
    HIGH_TIER_BONUS = 1.1    # Bonus for T6+ affixes

    def calculate_exalted_score(self, candidate: "ExaltedCandidate") -> float:
        """Calculate score for exalted candidate.

        Formula:
          base_score = (build_count * BUILD_WEIGHT) +
                       (source_count * SOURCE_WEIGHT) +
                       (avg_tier * TIER_WEIGHT) +
                       (occurrence_count * OCCURRENCE_WEIGHT)

          multiplier = 1.0
          if affix_count > 1: multiplier *= MULTI_AFFIX_BONUS
          if avg_tier >= 6: multiplier *= HIGH_TIER_BONUS

          score = base_score * multiplier

        Args:
            candidate: ExaltedCandidate to score

        Returns:
            Calculated score
        """
        base_score = (
            candidate.build_count * self.BUILD_WEIGHT +
            len(candidate.sources) * self.SOURCE_WEIGHT +
            candidate.avg_tier * self.TIER_WEIGHT +
            candidate.occurrence_count * self.OCCURRENCE_WEIGHT
        )

        multiplier = 1.0

        # Bonus for complex requirements (multiple affixes)
        if len(candidate.affixes) > 1:
            multiplier *= self.MULTI_AFFIX_BONUS

        # Bonus for high-tier affixes (T6+)
        if candidate.avg_tier >= 6:
            multiplier *= self.HIGH_TIER_BONUS

        return base_score * multiplier

    def calculate_idol_score(self, candidate: "IdolCandidate") -> float:
        """Calculate score for idol candidate.

        Formula:
          base_score = (build_count * BUILD_WEIGHT) +
                       (source_count * SOURCE_WEIGHT) +
                       (occurrence_count * OCCURRENCE_WEIGHT)

          multiplier = 1.0
          if modifier_count > 1: multiplier *= MULTI_AFFIX_BONUS

          score = base_score * multiplier

        Args:
            candidate: IdolCandidate to score

        Returns:
            Calculated score
        """
        base_score = (
            candidate.build_count * self.BUILD_WEIGHT +
            len(candidate.sources) * self.SOURCE_WEIGHT +
            candidate.occurrence_count * self.OCCURRENCE_WEIGHT
        )

        multiplier = 1.0

        # Bonus for complex idols (multiple modifiers)
        if len(candidate.modifiers) > 1:
            multiplier *= self.MULTI_AFFIX_BONUS

        return base_score * multiplier

    def calculate_unique_score(self, candidate: "UniqueCandidate") -> float:
        """Calculate score for unique candidate.

        Formula:
          score = (build_count * BUILD_WEIGHT) +
                  (source_count * SOURCE_WEIGHT) +
                  (occurrence_count * OCCURRENCE_WEIGHT)

        Args:
            candidate: UniqueCandidate to score

        Returns:
            Calculated score
        """
        return (
            candidate.build_count * self.BUILD_WEIGHT +
            len(candidate.sources) * self.SOURCE_WEIGHT +
            candidate.occurrence_count * self.OCCURRENCE_WEIGHT
        )

    def calculate_all_scores(
        self,
        exalted_candidates: list,
        idol_candidates: list,
        unique_candidates: list
    ) -> None:
        """Calculate scores for all candidates in-place.

        Args:
            exalted_candidates: List of ExaltedCandidate
            idol_candidates: List of IdolCandidate
            unique_candidates: List of UniqueCandidate
        """
        for candidate in exalted_candidates:
            candidate.score = self.calculate_exalted_score(candidate)

        for candidate in idol_candidates:
            candidate.score = self.calculate_idol_score(candidate)

        for candidate in unique_candidates:
            candidate.score = self.calculate_unique_score(candidate)

        logger.info(
            f"Calculated scores: {len(exalted_candidates)} exalted, "
            f"{len(idol_candidates)} idols, {len(unique_candidates)} uniques"
        )
