# Analyzer Specification

## Overview

The Analyzer is a DTO-based analytical layer that processes normalized `BuildDetails` from multiple S-Tier builds and generates aggregated filter candidates for Exalted items, Idols, and Unique items.

**Key Design Principles:**
- Strictly DTO-based (no HTML, HAR, or HTTP knowledge)
- Build deduplication by identity
- Technical base identity for non-unique items (no invented names)
- Transparent, explainable scoring
- Report-only for 140-rule limit (no enforcement at this stage)

## Architecture

### Modules

**app/analyzer/models.py**
- Candidate dataclasses (`ExaltedCandidate`, `IdolCandidate`, `UniqueCandidate`)
- Statistics containers (`AnalysisStats`, `IndividualModifierStats`)
- Analysis result wrapper (`AnalysisResult`)

**app/analyzer/priority_calculator.py**
- Transparent scoring formulas
- Configurable weights and bonuses
- Category-specific calculation methods

**app/analyzer/build_analyzer.py**
- Core aggregation logic
- Build deduplication
- Candidate generation for all three categories
- Integration with priority calculator

## Build Identity

### Deduplication Rule

Builds are considered identical if they share the same `source_url`.

**Fallback:** If `source_url` is not available, use normalized `name` (lowercase, spaces→underscores).

### Consequences

- **Same build, different sources:** Build count = 1, but sources are merged.
- **Profile variants:** Variants of the same build (same identity) count as 1 build but increase `occurrence_count`.

### Example

```python
build1 = BuildDetails(name="Build A", source_url="https://example.com/build1", ...)
build2 = BuildDetails(name="Build A Variant", source_url="https://example.com/build1", ...)

# Result: build_count = 1, occurrence_count = 2
```

## Exalted Aggregation

### Technical Base Identity

For non-unique exalted items without confirmed base names:

```python
base_key = (slot, itemType, subType)
```

**Never** invent human-readable base names.

### Aggregation Key

```python
key = (base_key, frozenset(affixes))
```

Where `affixes` is a frozen set of `(affix_name, tier)` tuples.

### Tracked Statistics

- `build_count`: Number of unique builds using this combination
- `occurrence_count`: Total occurrences across all profiles
- `sources`: Set of source categories (e.g., {"corruption", "bossing"})
- `max_tier`: Highest tier seen across all occurrences
- `avg_tier`: Average tier across all occurrences
- `tier_sum`: Internal accumulator for average calculation

### Example

Two builds both using:
- Gloves (itemType=13, subType=0)
- +Increased Melee Attack Speed T6
- +Lightning Penetration T7

Result: **One** `ExaltedCandidate` with `build_count=2`.

## Idol Aggregation

### Identity

Idols are identified by:

```python
key = (size, frozenset(modifiers))
```

**Critical:** Idol with two modifiers is ONE idol, not two separate idols.

### Example

```python
idol = IdolDTO(
	name="Grand Idol",
	size="Grand Idol (1x3)",
	modifiers=["Mod A", "Mod B"]
)
```

This creates **one** `IdolCandidate` with that full modifier combination.

### Individual Modifier Statistics

The analyzer also tracks individual modifier popularity separately in `modifier_stats` for future optimization:

```python
modifier_stats["Mod A"] = IndividualModifierStats(
	modifier="Mod A",
	build_count=...,
	occurrence_count=...,
	sizes={"Grand Idol (1x3)", "Minor Idol (1x1)"},
	sources={"corruption", "bossing"}
)
```

## Unique Aggregation

### Identity

```python
key = (name, unique_id)
```

Where `unique_id` comes from `ItemDTO.additional["uniqueID"]`.

### Example

```python
unique = ItemDTO(
	name="Harbinger of Stars",
	is_unique=True,
	additional={"uniqueID": 282},
	...
)
```

All instances of this unique across builds aggregate into **one** `UniqueCandidate`.

## Scoring

### Philosophy

Scores are **transparent** and **explainable**. No ML, no magic numbers.

### Weights

```python
BUILD_WEIGHT = 10.0       # Most important - how many builds use this
SOURCE_WEIGHT = 5.0       # Moderately important - usefulness across contexts
TIER_WEIGHT = 2.0         # For exalted - higher tiers preferred
OCCURRENCE_WEIGHT = 0.5   # Minor - raw occurrence count
```

### Bonuses

```python
MULTI_AFFIX_BONUS = 1.2   # For exalted/idols with multiple requirements
HIGH_TIER_BONUS = 1.1     # For T6+ affixes
```

### Formula: Exalted

```python
base_score = (
	build_count * BUILD_WEIGHT +
	source_count * SOURCE_WEIGHT +
	avg_tier * TIER_WEIGHT +
	occurrence_count * OCCURRENCE_WEIGHT
)

multiplier = 1.0
if affix_count > 1:
	multiplier *= MULTI_AFFIX_BONUS
if avg_tier >= 6:
	multiplier *= HIGH_TIER_BONUS

score = base_score * multiplier
```

### Formula: Idol

```python
base_score = (
	build_count * BUILD_WEIGHT +
	source_count * SOURCE_WEIGHT +
	occurrence_count * OCCURRENCE_WEIGHT
)

multiplier = 1.0
if modifier_count > 1:
	multiplier *= MULTI_AFFIX_BONUS

score = base_score * multiplier
```

### Formula: Unique

```python
score = (
	build_count * BUILD_WEIGHT +
	source_count * SOURCE_WEIGHT +
	occurrence_count * OCCURRENCE_WEIGHT
)
```

## Semantic Priority

**Category priorities** are separate from score:

- **Exalted**: Priority 100 (highest)
- **Idol**: Priority 70 (medium)
- **Unique**: Priority 40 (lowest)

These are fixed constants on the candidate dataclasses.

## Build Count vs Occurrence Count

**build_count**: Number of unique builds using this candidate.

**occurrence_count**: Total number of times seen across all profile variants.

### Example

- Build A (1 profile): uses gloves with affix X → +1 build, +1 occurrence
- Build B (2 profile variants): both variants use the same gloves → +1 build, +2 occurrences

Result: `build_count=2`, `occurrence_count=3`

## Profile Variants

Multiple profile variants of the **same build** (same `source_url` or normalized name):

- Increment `occurrence_count` for each variant
- **Do not** increment `build_count` again

Only the **first variant** of each build increments `build_count`.

## Estimated Rule Count

The analyzer estimates how many XML rules will be needed:

```python
estimated_total_rules = (
	estimated_exalted_rules +
	estimated_idol_rules +
	estimated_unique_rules
)
```

### Current Logic

- **Exalted**: 1:1 (one rule per candidate)
- **Idols**: 1:1 (one rule per candidate)
- **Uniques**: 1:1 (one rule per candidate)

**Note:** Actual XML generation may merge some candidates into compound rules. This estimate is intentionally conservative.

## 140-Rule Limit

### Current Behavior

The analyzer **reports only** if `estimated_total_rules > 140`.

```python
if stats.exceeds_limit:
	logger.warning(f"Estimated rules ({stats.estimated_total_rules}) exceed 140 limit")
```

### No Enforcement

The analyzer **does not** remove or filter candidates at this stage.

All candidates are preserved for future `RuleOptimizer` stage.

## Analysis Result

### Structure

```python
@dataclass
class AnalysisResult:
	exalted_candidates: List[ExaltedCandidate]
	idol_candidates: List[IdolCandidate]
	unique_candidates: List[UniqueCandidate]
	modifier_stats: Dict[str, IndividualModifierStats]
	stats: AnalysisStats

	def sort_candidates(self):
		# Sorts all lists by score descending
		...
```

### Statistics

```python
@dataclass
class AnalysisStats:
	builds_analyzed: int           # Total builds passed to analyzer
	unique_builds: int             # After deduplication
	exalted_candidates: int
	idol_candidates: int
	unique_candidates: int
	total_raw_items: int
	total_raw_idols: int
	total_raw_uniques: int
	estimated_exalted_rules: int
	estimated_idol_rules: int
	estimated_unique_rules: int

	@property
	def estimated_total_rules(self) -> int:
		...

	@property
	def exceeds_limit(self) -> bool:
		...
```

## Usage Example

```python
from app.analyzer.build_analyzer import BuildAnalyzer
from app.dto.models import BuildDetails

# Get BuildDetails from parser
builds: List[BuildDetails] = [...]

# Optional source mapping
source_mapping = {
	"https://example.com/build1": "corruption",
	"https://example.com/build2": "bossing",
}

# Analyze
analyzer = BuildAnalyzer()
result = analyzer.analyze(builds, source_mapping)

# Sort by score
result.sort_candidates()

# Access results
print(f"Exalted candidates: {result.stats.exalted_candidates}")
print(f"Estimated total rules: {result.stats.estimated_total_rules}")

# Top exalted
for i, cand in enumerate(result.exalted_candidates[:10], 1):
	print(f"{i}. Score: {cand.score:.2f}, Build count: {cand.build_count}")
```

## Limitations

### Current Stage

- **No XML generation**: Analyzer only produces candidates
- **No optimization**: All candidates preserved
- **No API integration**: Expects pre-parsed `BuildDetails`
- **No SQLite**: In-memory analysis only

### Base Name Problem

For non-unique items, we store `(slot, itemType, subType)` as technical identity.

**We do not** invent human-readable base names without confirmed lookup data.

Future `RuleBuilder` will need to map these technical IDs to actual Last Epoch base names.

## Testing

### Unit Tests

- **17** BuildAnalyzer tests
- **3** PriorityCalculator tests
- Total: **20** analyzer tests (currently **19** after test file cleanup)

### Coverage

- Empty input
- Build deduplication
- Source merging
- Exalted aggregation
- Idol aggregation (full combination + individual modifiers)
- Unique aggregation
- Build count vs occurrence count
- Profile variant handling
- Semantic priorities
- Deterministic ordering
- Estimated rule count
- >140 warning behavior
- Unknown technical base identity

### Real Data Validation

**Limitation**: Local data may contain only 1 real build.

**Do not** draw conclusions about affix/unique popularity from single-build diagnostics.

Use `scripts/check_build_analyzer.py` for real-data smoke tests only.

## Future Work

### RuleBuilder

Will consume `AnalysisResult` and generate actual Last Epoch XML filter rules.

Must resolve technical base identities to human-readable names.

### RuleOptimizer

Will handle cases where `estimated_total_rules > 140`:

- Merge candidates with shared requirements
- Apply thresholds (e.g., minimum build_count)
- Generate compound rules where possible

### SQLite (Optional)

For caching/tracking analysis results across runs.

Not required for MVP.

## Appendix: Dataclass Reference

### ExaltedCandidate

```python
@dataclass
class ExaltedCandidate:
	base_key: BaseKey  # (slot, itemType, subType)
	affixes: FrozenSet[Tuple[str, int]]  # Set of (name, min_tier)
	build_count: int
	occurrence_count: int
	sources: Set[str]
	max_tier: int
	avg_tier: float
	tier_sum: int  # For avg calculation
	score: float
	semantic_priority: int = 100
```

### IdolCandidate

```python
@dataclass
class IdolCandidate:
	size: Optional[str]
	modifiers: FrozenSet[str]
	build_count: int
	occurrence_count: int
	sources: Set[str]
	score: float
	semantic_priority: int = 70
```

### UniqueCandidate

```python
@dataclass
class UniqueCandidate:
	name: str
	unique_id: Optional[int]
	slot: Optional[str]
	build_count: int
	occurrence_count: int
	sources: Set[str]
	score: float
	semantic_priority: int = 40
```

### IndividualModifierStats

```python
@dataclass
class IndividualModifierStats:
	modifier: str
	build_count: int
	occurrence_count: int
	sizes: Set[str]
	sources: Set[str]
```

---

**Version**: 1.0  
**Date**: 2025  
**Status**: Implemented and validated
