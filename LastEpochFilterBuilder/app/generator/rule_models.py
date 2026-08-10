from dataclasses import dataclass, field
from typing import FrozenSet, List, Optional, Set, Tuple

@dataclass
class FilterRule:
    category: str
    semantic_priority: int
    score: float
    build_count: int = 0
    occurrence_count: int = 0
    source_count: int = 0
    sources: Set[str] = field(default_factory=set)
    slot: Optional[str] = None
    item_type: Optional[int] = None
    sub_type: Optional[int] = None
    affixes: FrozenSet[Tuple[str, int]] = field(default_factory=frozenset)
    idol_size: Optional[str] = None
    modifiers: FrozenSet[str] = field(default_factory=frozenset)
    unique_name: Optional[str] = None
    unique_id: Optional[int] = None
    max_tier: int = 0
    avg_tier: float = 0.0
    reason: str = ''

@dataclass
class RuleBuildResult:
    rules: List[FilterRule] = field(default_factory=list)
    exalted_count: int = 0
    idol_count: int = 0
    unique_count: int = 0

    @property
    def total_count(self) -> int:
        return len(self.rules)

    @property
    def exceeds_limit(self) -> bool:
        return self.total_count > 140

@dataclass
class OptimizedRule:
    """Optimized rule after merging multiple FilterRules.

    Represents one or more merged FilterRules with aggregated statistics.
    Used by RuleOptimizer for lossless merging.
    """
    category: str
    semantic_priority: int
    score: float
    build_count: int = 0
    occurrence_count: int = 0
    source_count: int = 0
    sources: Set[str] = field(default_factory=set)
    slot: Optional[str] = None
    item_types: List[Tuple[Optional[int], Optional[int]]] = field(default_factory=list)
    affixes: FrozenSet[Tuple[str, int]] = field(default_factory=frozenset)
    idol_sizes: List[str] = field(default_factory=list)
    modifiers: FrozenSet[str] = field(default_factory=frozenset)
    unique_items: FrozenSet[Tuple[Optional[int], str]] = field(default_factory=frozenset)
    max_tier: int = 0
    avg_tier: float = 0.0
    reason: str = ''
    merged_count: int = 1

    @property
    def unique_ids(self) -> List[Optional[int]]:
        """Derived property for backward compatibility."""
        return [uid for uid, _ in sorted(self.unique_items)]

    @property
    def unique_names(self) -> List[str]:
        """Derived property for backward compatibility."""
        return [name for _, name in sorted(self.unique_items)]

@dataclass
class OptimizationResult:
    """Result from RuleOptimizer containing optimized rules and statistics."""
    rules: List[OptimizedRule] = field(default_factory=list)
    original_count: int = 0
    optimized_count: int = 0
    exalted_merged: int = 0
    idol_merged: int = 0
    unique_merged: int = 0
    final_count: int = 0
    rules_pruned: int = 0
    pruned_exalted: int = 0
    pruned_idol: int = 0
    pruned_unique: int = 0
    protected_count: int = 0
    success: bool = True
    exceeds_budget: bool = False
    message: str = ''

    @property
    def total_merged(self) -> int:
        return self.exalted_merged + self.idol_merged + self.unique_merged

    @property
    def rules_saved_by_merge(self) -> int:
        return self.total_merged

    @property
    def exceeds_limit(self) -> bool:
        return self.final_count > 140
