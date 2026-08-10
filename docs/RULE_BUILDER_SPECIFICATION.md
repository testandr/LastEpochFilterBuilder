# RULE_BUILDER_SPECIFICATION.md

# Last Epoch Smart Loot Filter Generator

## RuleBuilder Specification

Version: 1.0

---

## 1. Purpose

**RuleBuilder** is responsible for converting aggregated analysis results from the **Analyzer** into intermediate rule candidates.

RuleBuilder creates WHAT should be shown in the filter, not HOW it will be serialized.

---

## 2. Responsibilities

RuleBuilder:
- Converts AnalysisResult into FilterRule objects
- Preserves all Analyzer statistics
- Maintains deterministic ordering
- Warns if rule count exceeds 140
- Does NOT mutate input data

RuleBuilder does NOT:
- Generate XML
- Optimize or merge rules
- Delete or prune rules
- Apply 140 rule limit (only warns)
- Recalculate scores
- Change priorities

---

## 3. Architecture

### 3.1 Component Chain

```
PlannerProfileParser
		|
		v
  BuildDetails[]
		|
		v
	Analyzer
		|
		v
  AnalysisResult
		|
		v
  RuleBuilder  <--- THIS COMPONENT
		|
		v
 RuleBuildResult
		|
		v
 RuleOptimizer (future)
		|
		v
  XML Generator (future)
```

### 3.2 Module Structure

```
app/generator/
├── __init__.py
├── rule_models.py      # FilterRule, RuleBuildResult
└── rule_builder.py     # RuleBuilder class
```

---

## 4. Input

RuleBuilder accepts `AnalysisResult` from Analyzer.

```python
@dataclass
class AnalysisResult:
	exalted_candidates: List[ExaltedCandidate]
	idol_candidates: List[IdolCandidate]
	unique_candidates: List[UniqueCandidate]
	modifier_stats: Dict[str, IndividualModifierStats]
	stats: AnalysisStats
```

---

## 5. Output

RuleBuilder produces `RuleBuildResult`.

```python
@dataclass
class RuleBuildResult:
	rules: List[FilterRule]
	exalted_count: int
	idol_count: int
	unique_count: int

	@property
	def total_count(self) -> int

	@property
	def exceeds_limit(self) -> bool
```

---

## 6. Rule Model

### 6.1 FilterRule

```python
@dataclass
class FilterRule:
	# Category
	category: str  # "exalted", "idol", "unique"

	# Priority and scoring (from Analyzer)
	semantic_priority: int  # 100=Exalted, 70=Idol, 40=Unique
	score: float

	# Statistics (from Analyzer)
	build_count: int
	occurrence_count: int
	source_count: int
	sources: Set[str]

	# Exalted-specific fields
	slot: Optional[str]
	item_type: Optional[int]
	sub_type: Optional[int]
	affixes: FrozenSet[Tuple[str, int]]  # (name, min_tier)
	max_tier: int
	avg_tier: float

	# Idol-specific fields
	idol_size: Optional[str]
	modifiers: FrozenSet[str]

	# Unique-specific fields
	unique_name: Optional[str]
	unique_id: Optional[int]

	# Debug information
	reason: str  # Human-readable explanation
```

### 6.2 Rule Identity

Each rule is uniquely identified by:

**Exalted:**
```python
(category="exalted", slot, item_type, sub_type, affixes)
```

**Idol:**
```python
(category="idol", idol_size, modifiers)
```

**Unique:**
```python
(category="unique", unique_name, unique_id)
```

---

## 7. Conversion Rules

### 7.1 Exalted Conversion

**One ExaltedCandidate → One FilterRule**

```python
ExaltedCandidate(
	base_key=("Gloves", 13, 0),
	affixes=frozenset([("Speed", 6), ("Damage", 7)]),
	build_count=3,
	occurrence_count=5,
	sources={"corruption", "bossing"},
	max_tier=7,
	avg_tier=6.5,
	score=45.0,
	semantic_priority=100
)
```

Becomes:

```python
FilterRule(
	category="exalted",
	slot="Gloves",
	item_type=13,
	sub_type=0,
	affixes=frozenset([("Speed", 6), ("Damage", 7)]),
	build_count=3,
	occurrence_count=5,
	source_count=2,
	sources={"corruption", "bossing"},
	max_tier=7,
	avg_tier=6.5,
	score=45.0,
	semantic_priority=100,
	reason="Exalted Gloves with 2 affix(es) (Damage, Speed) - used by 3 build(s) across 2 source(s)"
)
```

**Important:**
- All affixes stay together in one rule
- Technical base identity (slot, itemType, subType) is preserved
- No base name invention
- All statistics copied from candidate

### 7.2 Idol Conversion

**One IdolCandidate → One FilterRule**

```python
IdolCandidate(
	size="Grand Idol (1x3)",
	modifiers=frozenset(["Fire Damage", "Crit Chance"]),
	build_count=2,
	occurrence_count=4,
	sources={"corruption"},
	score=25.0,
	semantic_priority=70
)
```

Becomes:

```python
FilterRule(
	category="idol",
	idol_size="Grand Idol (1x3)",
	modifiers=frozenset(["Fire Damage", "Crit Chance"]),
	build_count=2,
	occurrence_count=4,
	source_count=1,
	sources={"corruption"},
	score=25.0,
	semantic_priority=70,
	reason="Idol Grand Idol (1x3) with 2 modifier(s) (Crit Chance, Fire Damage) - used by 2 build(s) across 1 source(s)"
)
```

**Important:**
- All modifiers stay together in one rule
- Do NOT split idol with 2 modifiers into 2 separate rules

### 7.3 Unique Conversion

**One UniqueCandidate → One FilterRule**

```python
UniqueCandidate(
	name="Harbinger of Stars",
	unique_id=282,
	slot="Weapon",
	build_count=4,
	occurrence_count=6,
	sources={"corruption", "bossing", "speed-farming"},
	score=55.0,
	semantic_priority=40
)
```

Becomes:

```python
FilterRule(
	category="unique",
	unique_name="Harbinger of Stars",
	unique_id=282,
	slot="Weapon",
	build_count=4,
	occurrence_count=6,
	source_count=3,
	sources={"corruption", "bossing", "speed-farming"},
	score=55.0,
	semantic_priority=40,
	reason="Unique 'Harbinger of Stars' (ID: 282) - used by 4 build(s) across 3 source(s)"
)
```

---

## 8. Ordering

Rules are sorted deterministically:

```python
# Sort key:
(-semantic_priority, -score, category, hash(rule))
```

1. **semantic_priority** (DESC) - Exalted first, then Idol, then Unique
2. **score** (DESC) - Higher scores first within same priority
3. **category** (ASC) - Stable sorting within same priority and score
4. **hash** (ASC) - Deterministic tie-breaking

### 8.1 Example

Given:
- Exalted (priority=100, score=50.0)
- Exalted (priority=100, score=60.0)
- Idol (priority=70, score=100.0)
- Unique (priority=40, score=80.0)

Order:
1. Exalted with score=60.0
2. Exalted with score=50.0
3. Idol with score=100.0
4. Unique with score=80.0

---

## 9. Statistics

### 9.1 Category Counts

```python
result.exalted_count  # Number of exalted rules
result.idol_count     # Number of idol rules
result.unique_count   # Number of unique rules
result.total_count    # Total rules = len(result.rules)
```

### 9.2 Rule Count

Actual rule count equals number of candidates:

```
total_count = exalted_count + idol_count + unique_count
```

No merging or optimization happens in RuleBuilder.

### 9.3 140 Limit Warning

```python
if result.exceeds_limit:  # total_count > 140
	logger.warning(f"Rule count ({result.total_count}) exceeds 140 limit")
```

**Important:** Rules are NOT deleted. All candidates become rules.

---

## 10. Reason Strings

Each rule includes a human-readable reason:

**Exalted:**
```
"Exalted Gloves with 2 affix(es) (Damage, Speed) - used by 3 build(s) across 2 source(s)"
```

**Idol:**
```
"Idol Grand Idol (1x3) with 2 modifier(s) (Crit Chance, Fire Damage) - used by 2 build(s) across 1 source(s)"
```

**Unique:**
```
"Unique 'Harbinger of Stars' (ID: 282) - used by 4 build(s) across 3 source(s)"
```

Reason strings are used for:
- Debugging
- Diagnostics
- Future RuleOptimizer decisions
- Explaining why a rule exists

---

## 11. Immutability

RuleBuilder does NOT mutate the input `AnalysisResult`.

All collections (e.g., `sources`) are copied, not referenced.

```python
# Correct:
sources=candidate.sources.copy()

# Incorrect:
sources=candidate.sources  # Would share reference
```

---

## 12. Usage Example

```python
from app.analyzer.build_analyzer import BuildAnalyzer
from app.generator.rule_builder import RuleBuilder

# Step 1: Analyze builds
analyzer = BuildAnalyzer()
analysis_result = analyzer.analyze(builds, source_mapping)

# Step 2: Build rules
builder = RuleBuilder()
rule_result = builder.build(analysis_result)

# Step 3: Examine results
print(f"Total rules: {rule_result.total_count}")
print(f"Exalted: {rule_result.exalted_count}")
print(f"Idol: {rule_result.idol_count}")
print(f"Unique: {rule_result.unique_count}")

if rule_result.exceeds_limit:
	print(f"WARNING: Exceeds 140 limit")

# Access rules
for rule in rule_result.rules[:10]:
	print(f"{rule.category} - score: {rule.score} - {rule.reason}")
```

---

## 13. Boundary Between Components

### 13.1 Analyzer → RuleBuilder

**Analyzer** is responsible for:
- Aggregating builds
- Calculating scores
- Deduplicating items/idols/uniques
- Statistics tracking
- Warning if estimated rules > 140

**RuleBuilder** is responsible for:
- Converting candidates to rules
- Preserving all Analyzer data
- Deterministic ordering
- Creating reason strings
- Warning if actual rules > 140

### 13.2 RuleBuilder → RuleOptimizer (future)

**RuleBuilder** creates:
- Independent rule candidates
- One rule per candidate
- No merging, no optimization

**RuleOptimizer** (future) will:
- Merge compatible rules
- Prune low-priority rules if needed
- Apply 140 limit enforcement
- Optimize for XML generation

### 13.3 RuleOptimizer → XML Generator (future)

**RuleOptimizer** produces:
- Final optimized rule set
- Guaranteed ≤ 140 rules (if needed)
- Merging decisions logged

**XML Generator** will:
- Serialize rules to Last Epoch XML format
- Apply XML-specific formatting
- Generate final .xml file

---

## 14. Testing Requirements

All RuleBuilder functionality MUST be covered by tests:

1. Empty input
2. Exalted candidate → rule conversion
3. Idol candidate → rule conversion
4. Unique candidate → rule conversion
5. Multiple affixes stay together
6. Multiple idol modifiers stay together
7. Semantic priority preserved
8. Analyzer score preserved (not recalculated)
9. Statistics preserved
10. Sources preserved
11. Deterministic ordering
12. Same input → identical output
13. Correct category counts
14. Correct total rule count
15. >140 rules NOT deleted
16. >140 produces warning metadata
17. RuleBuilder does not mutate AnalysisResult

---

## 15. Design Principles

### 15.1 One-to-One Mapping

Each Analyzer candidate becomes exactly one FilterRule.

No merging, no splitting, no optimization.

### 15.2 Data Preservation

All Analyzer data is preserved:
- Scores (not recalculated)
- Priorities (not changed)
- Statistics (copied exactly)
- Sources (copied, not referenced)

### 15.3 Deterministic Output

Given the same input, RuleBuilder always produces the same output.

No randomness, no time-based decisions.

### 15.4 Separation of Concerns

RuleBuilder focuses ONLY on conversion.

Optimization, XML generation, and limit enforcement are separate stages.

### 15.5 Transparency

Each rule includes a `reason` string explaining why it exists.

Debug information is first-class, not an afterthought.

---

## 16. Limitations

RuleBuilder intentionally does NOT:

1. **Generate XML** - That's XML Generator's job
2. **Optimize rules** - That's RuleOptimizer's job
3. **Apply 140 limit** - Only warns, doesn't enforce
4. **Merge rules** - Creates independent candidates
5. **Delete rules** - Preserves all candidates
6. **Recalculate scores** - Uses Analyzer scores
7. **Invent base names** - Uses technical identity
8. **Split multi-affix items** - Keeps affixes together
9. **Split multi-modifier idols** - Keeps modifiers together

---

## 17. Future Extensions

RuleBuilder is designed to support future enhancements:

### 17.1 Additional Rule Metadata

Easy to add:
- Estimated XML size
- Complexity score
- Mergeable candidates
- Alternative representations

### 17.2 Rule Validation

Could add pre-flight checks:
- Valid slot names
- Valid affix names
- Unique ID validation
- Tier ranges

### 17.3 Performance Metrics

Could track:
- Conversion time
- Memory usage
- Rule complexity distribution

---

## 18. Related Components

**Input from:**
- `app/analyzer/build_analyzer.py` - BuildAnalyzer
- `app/analyzer/models.py` - AnalysisResult, Candidates

**Output to:**
- RuleOptimizer (future implementation)
- XML Generator (future implementation)

**Models:**
- `app/generator/rule_models.py` - FilterRule, RuleBuildResult

---

## 19. Summary

RuleBuilder is the conversion layer between analysis and generation:

✅ Converts AnalysisResult → RuleBuildResult
✅ One candidate → One rule
✅ Preserves all Analyzer data
✅ Deterministic ordering
✅ Warns if >140 rules (doesn't delete)
✅ Independent from XML serialization
✅ Prepares data for RuleOptimizer

RuleBuilder does NOT optimize, merge, or generate XML.

---

**End of Specification**
