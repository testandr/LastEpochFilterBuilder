"""Models for build analysis and filter candidate generation.

Contains dataclasses for aggregated candidates (Exalted, Idol, Unique)
and analysis results.
"""
from dataclasses import dataclass, field
from typing import Dict, FrozenSet, List, Optional, Set, Tuple


# Technical base identity for items without confirmed base names
# (slot, itemType, subType)
BaseKey = Tuple[str, Optional[int], Optional[int]]


@dataclass
class ExaltedCandidate:
    """Aggregated exalted item candidate for loot filter.

    Represents a combination of base (slot + technical identity)
    and affix requirements that appear across multiple builds.
    """
    # Technical base identity
    base_key: BaseKey  # (slot, itemType, subType)

    # Affix requirements (name, min_tier)
    # Frozen for hashability
    affixes: FrozenSet[Tuple[str, int]]

    # Aggregation stats
    build_count: int = 0  # Number of unique builds using this combination
    occurrence_count: int = 0  # Total occurrences across all profiles
    sources: Set[str] = field(default_factory=set)  # e.g., {"corruption", "bossing"}

    # Tier tracking
    max_tier: int = 0
    avg_tier: float = 0.0
    tier_sum: int = field(default=0, repr=False)  # For avg calculation

    # Priority/score (calculated later)
    score: float = 0.0
    semantic_priority: int = 100  # EXALTED category base priority

    def __hash__(self):
        """Make hashable for deduplication."""
        return hash((self.base_key, self.affixes))

    def __eq__(self, other):
        """Equality based on base_key and affixes."""
        if not isinstance(other, ExaltedCandidate):
            return False
        return self.base_key == other.base_key and self.affixes == other.affixes


@dataclass
class IdolCandidate:
    """Aggregated idol candidate for loot filter.

    Represents a specific idol size + modifier combination.
    """
    # Idol identity
    size: Optional[str]  # e.g., "Grand Idol (1x3)"

    # Full modifier combination (frozen for hashability)
    modifiers: FrozenSet[str]

    # Aggregation stats
    build_count: int = 0
    occurrence_count: int = 0
    sources: Set[str] = field(default_factory=set)

    # Priority/score
    score: float = 0.0
    semantic_priority: int = 70  # IDOL category base priority

    def __hash__(self):
        """Make hashable for deduplication."""
        return hash((self.size, self.modifiers))

    def __eq__(self, other):
        """Equality based on size and modifiers."""
        if not isinstance(other, IdolCandidate):
            return False
        return self.size == other.size and self.modifiers == other.modifiers


@dataclass
class UniqueCandidate:
    """Aggregated unique item candidate for loot filter."""
    # Unique identity
    name: str
    unique_id: Optional[int] = None
    slot: Optional[str] = None

    # Aggregation stats
    build_count: int = 0
    occurrence_count: int = 0
    sources: Set[str] = field(default_factory=set)

    # Priority/score
    score: float = 0.0
    semantic_priority: int = 40  # UNIQUE category base priority (lowest)

    def __hash__(self):
        """Make hashable for deduplication."""
        return hash((self.name, self.unique_id))

    def __eq__(self, other):
        """Equality based on name and unique_id."""
        if not isinstance(other, UniqueCandidate):
            return False
        return self.name == other.name and self.unique_id == other.unique_id


@dataclass
class IndividualModifierStats:
    """Statistics for individual idol modifiers (for future optimization)."""
    modifier: str
    build_count: int = 0
    occurrence_count: int = 0
    sizes: Set[str] = field(default_factory=set)
    sources: Set[str] = field(default_factory=set)


@dataclass
class AnalysisStats:
    """Statistics about the analysis run."""
    builds_analyzed: int = 0
    unique_builds: int = 0
    exalted_candidates: int = 0
    idol_candidates: int = 0
    unique_candidates: int = 0
    total_raw_items: int = 0
    total_raw_idols: int = 0
    total_raw_uniques: int = 0

    # Estimated rule count (approximate - exact mapping to XML happens later)
    estimated_exalted_rules: int = 0
    estimated_idol_rules: int = 0
    estimated_unique_rules: int = 0

    @property
    def estimated_total_rules(self) -> int:
        """Total estimated rules across all categories."""
        return (self.estimated_exalted_rules + 
                self.estimated_idol_rules + 
                self.estimated_unique_rules)

    @property
    def exceeds_limit(self) -> bool:
        """Check if estimated rules exceed 140 limit."""
        return self.estimated_total_rules > 140


@dataclass
class AnalysisResult:
    """Complete analysis result with all candidates and statistics."""
    exalted_candidates: List[ExaltedCandidate] = field(default_factory=list)
    idol_candidates: List[IdolCandidate] = field(default_factory=list)
    unique_candidates: List[UniqueCandidate] = field(default_factory=list)

    # Individual modifier stats for future optimization
    modifier_stats: Dict[str, IndividualModifierStats] = field(default_factory=dict)

    stats: AnalysisStats = field(default_factory=AnalysisStats)

    def sort_candidates(self):
        """Sort all candidate lists by score descending."""
        self.exalted_candidates.sort(key=lambda c: c.score, reverse=True)
        self.idol_candidates.sort(key=lambda c: c.score, reverse=True)
        self.unique_candidates.sort(key=lambda c: c.score, reverse=True)
