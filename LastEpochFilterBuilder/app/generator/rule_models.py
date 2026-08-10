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
