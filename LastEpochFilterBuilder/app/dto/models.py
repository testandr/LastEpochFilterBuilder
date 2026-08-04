"""Data Transfer Objects (DTO) used across the application.

All DTOs are simple dataclasses without logic, independent from other modules.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class AffixDTO:
    name: str
    category: Optional[str] = None
    tier: Optional[int] = None
    description: Optional[str] = None
    value: Optional[str] = None


@dataclass
class ItemDTO:
    name: str
    item_type: Optional[str] = None
    slot: Optional[str] = None
    rarity: Optional[str] = None
    is_unique: bool = False
    is_exalted: bool = False
    affixes: List[AffixDTO] = field(default_factory=list)
    additional: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IdolDTO:
    name: str
    size: Optional[str] = None
    modifiers: List[str] = field(default_factory=list)
    rarity: Optional[str] = None


@dataclass
class SkillDTO:
    name: str
    description: Optional[str] = None
    level: Optional[int] = None
    specialized: bool = False


@dataclass
class BuildSummary:
    name: str
    tier: str
    class_name: Optional[str] = None
    mastery: Optional[str] = None
    url: Optional[str] = None
    sources: List[str] = field(default_factory=list)
    author: Optional[str] = None
    popularity_score: Optional[int] = None


@dataclass
class BuildStatDTO:
    stat_name: str
    value: str
    priority: Optional[int] = None


@dataclass
class BuildDetails:
    name: str
    class_name: Optional[str] = None
    mastery: Optional[str] = None
    author: Optional[str] = None
    items: List[ItemDTO] = field(default_factory=list)
    idols: List[IdolDTO] = field(default_factory=list)
    skills: List[SkillDTO] = field(default_factory=list)
    stats: List[BuildStatDTO] = field(default_factory=list)
    source_url: Optional[str] = None


@dataclass
class FilterRuleDTO:
    rule_type: str  # SHOW, HIDE, COLOR
    item_type: Optional[str] = None
    rarity: Optional[str] = None
    item_name: Optional[str] = None
    affixes: List[str] = field(default_factory=list)
    priority: int = 0
    color: Optional[str] = None
    enabled: bool = True
    id: Optional[int] = None
