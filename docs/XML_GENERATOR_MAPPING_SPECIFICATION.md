# XML Generator Mapping Specification

Version: 1.0
Status: Design Phase
Created: 2024

## 1. Purpose

This document specifies the exact mapping from OptimizedRule (output of RuleOptimizer) to Last Epoch XML Rule format.

This specification is intended for XML Generator implementation and must be complete enough to avoid guesswork during coding.

Scope: Exalted, Idol, and Unique rules only.

## 2. Input Model

Source: OptimizedRule (app/generator/rule_models.py)

**Updated after Phase 0A (affix ID preservation):**

```
@dataclass
class OptimizedRule:
	category: str  # "exalted", "idol", "unique"
	semantic_priority: int
	score: float
	build_count: int
	occurrence_count: int
	source_count: int
	sources: Set[str]
	slot: Optional[str]
	item_types: List[Tuple[Optional[int], Optional[int]]]  # [(item_type, sub_type)]
	affixes: FrozenSet[Tuple[Optional[int], str, int]]  # ✅ Updated: (affix_id, name, tier)
	idol_sizes: List[str]
	modifiers: FrozenSet[Tuple[Optional[int], str, int]]  # ✅ Updated: (affix_id, name, tier)
	unique_items: FrozenSet[Tuple[Optional[int], str]]  # (unique_id, name)
	max_tier: int
	avg_tier: float
	reason: str
	merged_count: int
```

**Phase 0A Changes:**
- affixes: Now preserves numeric affix_id alongside name and tier
- modifiers: Now preserves numeric affix_id for idol modifiers
- Backward compatibility: affix_id can be None for synthetic tests

Input: List[OptimizedRule] sorted by priority (highest priority first)

Order: Rules are already sorted by RuleOptimizer:
1. semantic_priority DESC
2. score DESC
3. stable identity

## 3. Output XML

Target: Last Epoch loot filter XML format (see XML_FILTER_RESEARCH.md)

Root structure:
```
<ItemFilter xmlns:i="http://www.w3.org/2001/XMLSchema-instance">
  <name>...</name>
  <filterIcon>0</filterIcon>
  <filterIconColor>0</filterIconColor>
  <description />
  <lastModifiedInVersion>1.4.7</lastModifiedInVersion>
  <lootFilterVersion>0</lootFilterVersion>
  <rules>
	<Rule>
	  ...
	</Rule>
  </rules>
</ItemFilter>
```

## 4. Root Metadata Mapping

### Filter Name
- Source: Config or default
- Default: "Last Epoch Smart Loot Filter"
- Mapping: ConfigManager.application.name or hardcoded default

### Filter Icon
- Default: 0
- Type: integer
- Notes: Icon ID for filter in-game display

### Filter Icon Color
- Default: 0
- Type: integer
- Notes: Color ID for filter icon

### Description
- Default: empty element `<description />`
- Type: optional string
- Notes: User-visible filter description

### Last Modified Version
- Default: "1.4.7"
- Type: string
- Notes: Game version, should match current Last Epoch version

### Loot Filter Version
- Default: 0
- Type: integer
- Notes: Internal filter format version

Implementation: All metadata fields use fixed defaults for v1.

## 5. Rule Ordering

### Order Assignment Algorithm

Input: List[OptimizedRule] already sorted by RuleOptimizer

Output: Each XML Rule gets sequential Order value starting from 0

Algorithm:
```
for index, optimized_rule in enumerate(sorted_rules):
	xml_rule.Order = index
```

Rationale:
- Lower Order = higher evaluation priority in game
- Order 0 is first match
- First-match-wins semantics
- RuleOptimizer already sorted by semantic_priority DESC, score DESC
- XML Generator serializes this ordering as-is

Critical: Do NOT re-sort or recalculate priority at XML generation stage.

### XML Document Order

Rules in XML document: Can be in any order (game reads Order field explicitly)

Preferred: Serialize in ascending Order (0, 1, 2...) for readability

### Category Priority

Business priority: Exalted > Idol > Unique

This is ALREADY enforced by semantic_priority values:
- Exalted: 100
- Idol: 70
- Unique: 30

RuleOptimizer sorts by semantic_priority DESC, so exalted rules naturally come first.

XML Generator does NOT need category-based ordering logic.

## 6. Common XML Rule Fields

All rules share these fields:

### type
- Source: Fixed value
- Value: "SHOW"
- Type: string
- Notes: All generated rules are SHOW (project does not generate HIDE rules)

### conditions
- Source: Category-specific (see sections 7-9)
- Type: XML container with multiple Condition elements
- Notes: AND semantics between conditions

### recolor
- Source: Style policy (see section 11)
- Type: boolean (true/false)
- Default: true for styled categories, false otherwise

### color
- Source: Style policy
- Type: integer (0-15+)
- Default: Category-dependent

### emphasized
- Source: Style policy
- Type: boolean
- Default: false

### nameOverride
- Source: Not used
- Type: optional string
- Default: empty element `<nameOverride />`

### SoundId
- Source: Style policy
- Type: integer
- Default: 0 (no sound)

### MapIconId
- Source: Style policy
- Type: integer
- Default: 0 (no icon)

### BeamOverride
- Source: Style policy
- Type: boolean
- Default: false

### BeamSizeOverride
- Source: Style policy
- Type: string enum
- Value: "NONE", "SMALL", "MEDIUM", "LARGE", "VERYLARGE"
- Default: "NONE"

### BeamColorOverride
- Source: Style policy
- Type: integer
- Default: 0

### isEnabled
- Source: Fixed value
- Value: true
- Type: boolean
- Notes: All generated rules are enabled

### Deprecated fields (always included for compatibility)
- levelDependent_deprecated: false
- minLvl_deprecated: 0
- maxLvl_deprecated: 0

### Order
- Source: Sequential assignment (see section 5)
- Type: integer
- Notes: Lower = higher priority

## 7. Exalted Mapping

Category: exalted

Required conditions: 3 minimum

### Condition 1: RarityCondition

```
<Condition i:type="RarityCondition">
  <rarity>EXALTED</rarity>
</Condition>
```

- Type: RarityCondition
- Field: rarity
- Value: "EXALTED" (uppercase)
- Notes: Filters for exalted rarity items only

### Condition 2: SubTypeCondition

```
<Condition i:type="SubTypeCondition">
  <type>
	<EquipmentType>GLOVES</EquipmentType>
	<EquipmentType>HELMET</EquipmentType>
  </type>
  <subTypes />
</Condition>
```

- Type: SubTypeCondition
- Container: type
- Child elements: Multiple EquipmentType (OR semantics)
- Source: OptimizedRule.item_types
- Mapping: See section 7.1
- subTypes: Empty element (unused)

### Condition 3: AffixCondition

```
<Condition i:type="AffixCondition">
  <affixes>
	<int>502</int>
	<int>25</int>
  </affixes>
  <comparsion>MORE_OR_EQUAL</comparsion>
  <comparsionValue>6</comparsionValue>
  <minOnTheSameItem>2</minOnTheSameItem>
  <combinedComparsion>ANY</combinedComparsion>
  <combinedComparsionValue>0</combinedComparsionValue>
  <advanced>true</advanced>
</Condition>
```

- Type: AffixCondition
- Source: OptimizedRule.affixes
- Mapping: See section 8

### 7.1 Equipment Type Mapping

Source: OptimizedRule.item_types: List[Tuple[Optional[int], Optional[int]]]

Each tuple is (item_type, sub_type)

Output: Multiple EquipmentType XML elements

**RESOLVED (Phase 0B1):**

Mapper: app/generator/equipment_type_mapper.py

Function: map_equipment_type(item_type, sub_type=None) -> str

Data source: game_data.json itemTypes array (confirmed from real extracted data)

Mapping table (confirmed core equipment slots):

| item_type | displayName | XML EquipmentType |
|-----------|-------------|-------------------|
| 0         | Helmet      | HELMET            |
| 1         | Body Armor  | BODY_ARMOR        |
| 2         | Belt        | BELT              |
| 3         | Boots       | BOOTS             |
| 4         | Gloves      | GLOVES            |
| 20        | Amulet      | AMULET            |
| 21        | Ring        | RING              |
| 22        | Relic       | RELIC             |

Behavior:
- Confirmed types return XML enum string
- Unknown types raise EquipmentTypeMappingError (explicit failure, no silent fallback)
- Weapon types (5-16, 23-24) raise explicit out-of-scope error
- Off-hand types (17-19) raise explicit out-of-scope error
- Idol types (25-33) raise explicit out-of-scope error (handled in Phase 0B2)

Status: RESOLVED for core equipment slots

Remaining gaps: Weapon and Off-hand EquipmentType values require additional research.

**Phase 0B3 Research Status: INCOMPLETE - INSUFFICIENT XML EVIDENCE**

Research findings:
- Verified 17 weapon/off-hand item_type values in game_data.json (item types 5-19, 23-24)
- Item types confirmed: One-Handed Axe, Dagger, One-Handed Mace, Sceptre, One-Handed Sword, Wand, Fist, Two-Handed Axe, Two-Handed Mace, Two-Handed Spear, Two-Handed Staff, Two-Handed Sword, Quiver, Shield, Off-Hand Catalyst, Bow, Crossbow
- Searched all local XML files for weapon/off-hand EquipmentType enum evidence
- Result: NO confirmed XML EquipmentType enum values for any weapon or off-hand type
- Only XML file available: data/debug/filters/xml_semantics_test.xml (contains only core equipment and IDOL_2x1)
- game_data.json provides displayName but NO XML-compatible EquipmentType or enum hints
- Documentation contains ONLY generic references to "Weapon types" without enum values
- No lootFilterNameOverride values present for weapon/off-hand types

**Evidence gap:**
Real Last Epoch XML filters containing weapon/off-hand SubTypeCondition rules are required to confirm exact EquipmentType enum strings.

**Cannot implement mapping:**
Without confirmed XML enum evidence, any weapon/off-hand mapping would be fabricated guesswork.
Equipment type mapper Phase 0B1 implementation explicitly rejects weapon/off-hand types with EquipmentTypeMappingError.

**Required for completion:**
User must create real Last Epoch loot filter rules for:
1. One-handed weapons (verify if item_type alone determines EquipmentType or if sub_type differentiates weapon types)
2. Two-handed weapons
3. Bow/Crossbow
4. Shield
5. Quiver
6. Off-Hand Catalyst

Export those filters as XML and add to repository for Phase 0B3 evidence-based mapping.

Status: BLOCKED - MORE XML EVIDENCE REQUIRED

### 7.2 SubType Handling

Source: OptimizedRule.item_types contains sub_type integers

XML: subTypes element exists but semantics UNKNOWN

Research conclusion: subTypes always empty in observed real XML

Current RuleOptimizer: Does NOT merge different sub_type values

Decision for v1: Leave subTypes empty

Equipment type mapper: sub_type parameter accepted but currently unused

Phase 0B1 finding: sub_type does not affect EquipmentType selection for confirmed core equipment slots

Consequence: Generated rules may be wider than original technical base filtering

Risk: LOW (sub_type differentiation rare in current builds)

Status: NON-BLOCKING (can use empty subTypes safely)

## 8. Affix Mapping

Source: OptimizedRule.affixes: FrozenSet[Tuple[str, int]]

Each tuple is (affix_name, tier)

Output: AffixCondition XML

### 8.1 Affix IDs

CRITICAL MODEL GAP IDENTIFIED:

OptimizedRule.affixes contains (name, tier) tuples.

XML requires numeric affix IDs (e.g., 502, 25, 14).

Current pipeline:
1. Parser reads affix_id from planner JSON
2. Parser looks up affix_name from game_data
3. Parser creates AffixDTO(name, tier) - ID IS LOST
4. Analyzer aggregates by (name, tier)
5. RuleBuilder preserves (name, tier)
6. Optimizer preserves (name, tier)

Affix ID is lost at Parser -> DTO boundary.

GAP: BLOCKING - Cannot generate valid AffixCondition without numeric IDs.

Recommended solution:
- Add affix_id field to AffixDTO
- Preserve ID through entire pipeline
- Alternative: Create name -> ID reverse lookup from game_data

### 8.2 Tier Mapping

Source: OptimizedRule tier values are displayed tiers (1-based)

Parser already converts: planner tier (0-based) -> displayed tier (1-based)

Example: planner tier 5 -> displayed tier 6 (T6)

XML comparsionValue: Uses displayed tier directly

Mapping:
```
OptimizedRule affix tuple (name, 6) -> comparsionValue = 6
```

No conversion needed at XML generation stage.

### 8.3 Tier Comparison

Field: comparsion

Value: "MORE_OR_EQUAL"

Semantics: Each selected affix must have tier >= comparsionValue

All generated exalted rules use MORE_OR_EQUAL (match T6+, T7+, etc).

### 8.4 Required Affix Count

Field: minOnTheSameItem

Source: Count of affixes in OptimizedRule.affixes

Semantics: Item must have at least N of the listed affixes

Current model assumption: ALL affixes in set are required

Mapping:
```
minOnTheSameItem = len(OptimizedRule.affixes)
```

Rationale:
- Analyzer creates candidates with specific affix combinations
- Each candidate represents exact combination observed in builds
- Example: (Affix A T6, Affix B T7) means both required
- Optimizer preserves exact combination during merge

Verification: Current RuleOptimizer does NOT support partial affix sets

Status: READY (model matches XML semantics)

### 8.5 Individual Affix Tiers

CRITICAL ISSUE IDENTIFIED:

OptimizedRule can contain affixes with DIFFERENT tier requirements:
- (Affix A, 6)
- (Affix B, 7)
- (Affix C, 6)

XML AffixCondition has SINGLE comparsionValue for all selected affixes.

Current XML cannot represent: "Affix A must be T6+ AND Affix B must be T7+"

XML forces same tier requirement for all affixes.

Options:
A. Use minimum tier (6) - Too permissive
B. Use maximum tier (7) - Too restrictive
C. Use most common tier
D. Use average tier
E. Generate separate rules for each tier requirement

Current Analyzer design: Creates candidates with consistent tiers per combination

Verification needed: Does current Analyzer create mixed-tier candidates?

If YES: GAP - BLOCKING
If NO: Use single tier value (max_tier or common tier)

Preliminary recommendation: Use max_tier from OptimizedRule

Status: POTENTIAL GAP (needs verification)

### 8.6 Combined Comparison

Fields:
- combinedComparsion: "ANY"
- combinedComparsionValue: integer

Purpose: Total tier sum filtering (e.g., "total tiers >= 12")

Current model: Does NOT use total tier sum logic

Recommendation: Set combinedComparsion="ANY", combinedComparsionValue=0

Status: READY (unused feature)

### 8.7 Advanced Flag

Field: advanced

Value: true (when using minOnTheSameItem and tier requirements)

Mapping: Always true for generated rules

Status: READY

## 9. Idol Mapping

Category: idol

Required conditions: 2 minimum

### Condition 1: SubTypeCondition (Idol Size)

```
<Condition i:type="SubTypeCondition">
  <type>
	<EquipmentType>IDOL_2x1</EquipmentType>
	<EquipmentType>IDOL_1x1</EquipmentType>
  </type>
  <subTypes />
</Condition>
```

- Type: SubTypeCondition
- Source: OptimizedRule.idol_sizes
- Mapping: See section 9.1

### Condition 2: AffixCondition (Idol Modifiers)

Same structure as exalted affixes but:
- comparsion: "ANY" (idols typically don't have tier requirements)
- comparsionValue: 0
- minOnTheSameItem: len(modifiers)
- advanced: false (simpler filtering)

Source: OptimizedRule.modifiers

Mapping: See section 9.2

### 9.1 Idol Size Mapping

Source: OptimizedRule.idol_sizes: List[str]

Examples: "Grand Idol (1x3)", "Minor Idol (1x1)"

XML requires EquipmentType format: "IDOL_1x3", "IDOL_1x1", etc.

**RESOLVED (Phase 0B2):**

Mapper: app/generator/idol_size_mapper.py

Functions:
- map_idol_size(size: str) -> str
- map_idol_item_type(item_type: int) -> str

Data source: Parser IDOL_SIZES constant (item_type -> human-readable size string)

Mapping approach: Extract dimensions from (WxH) pattern in size string, format as IDOL_WxH

Confirmed mappings:
- "Minor Idol (1x1)" -> IDOL_1x1 (item_type 26)
- "Humble Idol (1x2)" -> IDOL_1x2 (item_type 27)
- "Grand Idol (1x3)" -> IDOL_1x3 (item_type 29)
- "Adorned Idol (1x4)" -> IDOL_1x4 (item_type 33)

Note: Parser IDOL_SIZES maps only 4 idol types. Game_data contains 10 idol types (25-33, 41), but only 4 have confirmed dimension mappings in parser.

Behavior:
- Extracts dimensions using regex pattern: r'\\((\\d+)x(\\d+)\\)'
- Formats as IDOL_WxH where W=width, H=height
- Unknown or malformed sizes raise IdolSizeMappingError (explicit failure)
- No fallback to generic values
- No fuzzy matching on idol names

Status: RESOLVED for all parser-supported idol sizes

### 9.2 Idol Modifier Mapping

Source: OptimizedRule.modifiers: FrozenSet[str]

Modifier names like "Mod X", "Mod Y"

XML requires numeric affix IDs (same as equipment affixes)

CRITICAL MODEL GAP IDENTIFIED:

Same issue as exalted affixes - modifier names stored, IDs lost.

Idol modifiers use same game affix system as equipment.

Parser reads modifier ID from planner JSON, looks up name, loses ID.

GAP: BLOCKING - Cannot generate valid idol AffixCondition without numeric IDs.

Recommended solution: Same as exalted - preserve IDs in DTO.

### 9.3 Idol Modifier Count

Field: minOnTheSameItem

Current model: All modifiers in set are required

Mapping:
```
minOnTheSameItem = len(OptimizedRule.modifiers)
```

Status: READY

## 10. Unique Mapping

Category: unique

Required conditions: 1

### Condition: UniqueModifiersCondition

```
<Condition i:type="UniqueModifiersCondition">
  <Uniques>
	<UniqueId>300</UniqueId>
	<Rolls>
	  <UniqueModifierWithRollId>
		<RollId>0</RollId>
		<Modifier>
		  <MinRoll i:nil="true" />
		  <MaxRoll i:nil="true" />
		</Modifier>
	  </UniqueModifierWithRollId>
	</Rolls>
  </Uniques>
  <Uniques>
	<UniqueId>296</UniqueId>
	<Rolls>...</Rolls>
  </Uniques>
</Condition>
```

### 10.1 Unique ID Mapping

Source: OptimizedRule.unique_items: FrozenSet[Tuple[Optional[int], str]]

Each tuple: (unique_id, name)

XML: Multiple Uniques elements with UniqueId

Mapping:
```
for unique_id, name in optimized_rule.unique_items:
	<Uniques>
	  <UniqueId>{unique_id}</UniqueId>
	  <Rolls>...</Rolls>
	</Uniques>
```

Status: READY (unique_id is preserved in model)

### 10.2 Unique Roll Filtering

Project scope: Does NOT filter by unique modifier roll values

Decision: All Rolls elements use nil constraints (no filtering)

For each unique, generate default Rolls structure with all constraints nil.

Number of rolls: Varies by unique item (0-4+ modifiers)

ISSUE: How many UniqueModifierWithRollId elements to generate?

Research finding: Some XML examples show multiple roll entries even when not filtering.

Recommendation for v1: Generate NO roll constraints (minimal valid structure)

Alternative: Always generate 4 roll entries with nil values (safer compatibility)

Requires testing: Can Uniques element have empty Rolls?

Preliminary: Use empty Rolls container for v1 simplicity

Status: PARTIALLY_READY (needs validation of minimal structure)

### 10.3 Multiple Uniques in One Rule

XML supports multiple Uniques elements (OR semantics).

RuleOptimizer Part 3B keeps different uniques separate for pruning granularity.

Decision: XML Generator performs 1:1 serialization (one OptimizedRule -> one XML Rule)

Rationale:
- Simpler implementation
- Preserves optimizer decisions
- No semantic changes at serialization stage

Multiple uniques in single OptimizedRule.unique_items are serialized as multiple Uniques elements within one UniqueModifiersCondition.

Status: READY

## 11. Style Policy

Style fields affect visual presentation only, not filtering logic.

### 11.1 Category-Based Defaults

Exalted:
- recolor: true
- color: 2 (example from real XML)
- emphasized: false
- SoundId: 0
- MapIconId: 0
- BeamOverride: false
- BeamSizeOverride: "NONE"
- BeamColorOverride: 0

Idol:
- recolor: true
- color: 4 (example from real XML)
- emphasized: false
- SoundId: 0
- MapIconId: 0
- BeamOverride: false
- BeamSizeOverride: "NONE"
- BeamColorOverride: 0

Unique:
- recolor: false (no recoloring for uniques)
- color: 0
- emphasized: false
- SoundId: 0
- MapIconId: 0
- BeamOverride: false
- BeamSizeOverride: "NONE"
- BeamColorOverride: 0

### 11.2 Priority-Based Styling

Optional enhancement (NOT required for v1):

High-priority rules (semantic_priority 100, high score) could use:
- emphasized: true
- BeamOverride: true
- SoundId: non-zero

Decision for v1: Use simple category-based defaults only.

### 11.3 Configurability

Future enhancement: Allow user customization via config file

Not implemented in v1.

Status: READY (simple hardcoded defaults)

## 12. Defaults Summary

All generated rules:
- type: "SHOW"
- isEnabled: true
- levelDependent_deprecated: false
- minLvl_deprecated: 0
- maxLvl_deprecated: 0

All exalted rules:
- RarityCondition with rarity="EXALTED"
- SubTypeCondition with item types
- AffixCondition with affixes
- recolor: true, color: 2

All idol rules:
- SubTypeCondition with idol sizes
- AffixCondition with modifiers
- recolor: true, color: 4

All unique rules:
- UniqueModifiersCondition with unique IDs
- recolor: false, color: 0

## 13. Validation Requirements

XML Generator must validate:

1. Every OptimizedRule has recognized category ("exalted", "idol", "unique")
2. Exalted rules have non-empty item_types
3. Exalted rules have non-empty affixes
4. Idol rules have non-empty idol_sizes
5. Idol rules have non-empty modifiers
6. Unique rules have non-empty unique_items
7. All unique_id values are not None
8. Order values are sequential 0, 1, 2...
9. No duplicate Order values

Validation failures should raise clear exceptions.

## 14. Model Gap Analysis

Analysis of OptimizedRule fields vs XML requirements:

### 14.1 READY Fields

These fields exist and can be used directly:

- category: Maps to condition type selection
- semantic_priority: Used for ordering (already sorted)
- score: Used for ordering (already sorted)
- build_count: Statistics only, not in XML
- sources: Statistics only, not in XML
- unique_items: Contains (unique_id, name), ID is preserved ✓
- max_tier: Can be used for comparsionValue
- Order: Derived from list position

### 14.2 DERIVABLE Fields

These can be computed from existing data:

- minOnTheSameItem: len(affixes) or len(modifiers)
- Rule Order: enumerate(rules)
- comparsion: Fixed "MORE_OR_EQUAL"
- advanced: Fixed true

### 14.3 MISSING Fields

These are required for XML but missing or lossy in current model:

#### BLOCKING GAPS:

**STATUS: 4 of 4 CORE GAPS RESOLVED (Phase 0A, 0B1, 0B2 completed)**

1. **Numeric Affix IDs (exalted) — ✅ RESOLVED (Phase 0A)**
   - Current: Affix IDs preserved as (affix_id, name, tier) tuples
   - Required: Numeric IDs (e.g., 502, 25, 14)
   - Impact: Can generate valid AffixCondition
   - Solution: Added affix_id to AffixDTO, preserved through pipeline
   - Verification: tests/test_phase_0a_affix_id.py (4/4 passed)

2. **Numeric Affix IDs (idol modifiers) — ✅ RESOLVED (Phase 0A)**
   - Current: Modifier IDs preserved as (affix_id, name, tier) tuples
   - Required: Numeric IDs (e.g., 114, 319)
   - Impact: Can generate valid idol AffixCondition
   - Solution: Added modifier_affixes to IdolDTO, preserved through pipeline
   - Verification: tests/test_phase_0a_affix_id.py (4/4 passed)

3. **Equipment Type Mapping (exalted) — ✅ RESOLVED (Phase 0B1)**
   - Current: Numeric item_type (e.g., 0, 1, 4) with mapper available
   - Required: String EquipmentType (e.g., "HELMET", "BODY_ARMOR", "GLOVES")
   - Impact: Can generate valid SubTypeCondition for core equipment
   - Solution: Created app/generator/equipment_type_mapper.py with confirmed mappings
   - Coverage: 8 core equipment slots (Helmet, Body Armor, Belt, Boots, Gloves, Amulet, Ring, Relic)
   - Verification: tests/test_equipment_type_mapper.py (31/31 passed)
   - Remaining: Weapon/off-hand EquipmentType values require additional research (Phase 0B3)

4. **Idol Size Format (idol) — ✅ RESOLVED (Phase 0B2)**
   - Current: Human-readable with mapper available (e.g., "Grand Idol (1x3)")
   - Required: Machine format (e.g., "IDOL_1x3")
   - Impact: Can generate valid idol SubTypeCondition
   - Solution: Created app/generator/idol_size_mapper.py with dimension extraction
   - Coverage: 4 parser-supported idol sizes (Minor 1x1, Humble 1x2, Grand 1x3, Adorned 1x4)
   - Verification: tests/test_idol_size_mapper.py (35/35 passed)
   - Note: Parser only maps 4 of 10 idol types; additional idol dimensions unknown

#### NON-BLOCKING GAPS:

5. SubTypes semantics
   - Current: Numeric sub_type preserved
   - Required: Not fully understood
   - Impact: Rules may be slightly wider than intended
   - Mitigation: Use empty subTypes (observed pattern)
   - Risk: LOW

6. Individual affix tier requirements
   - Current: Multiple (name, tier) tuples
   - Required: Single comparsionValue
   - Impact: Cannot represent mixed tier requirements
   - Mitigation: Use max_tier or verify all tiers match
   - Risk: MEDIUM (verify Analyzer doesn't create mixed tiers)

7. Color/Sound IDs
   - Current: Not stored
   - Required: Numeric IDs for styling
   - Impact: Limited visual customization
   - Mitigation: Use defaults from real XML (2, 4, etc.)
   - Risk: LOW (styling only)

## 15. Blocking Gaps Summary

**Phase 0B3 Status: INCOMPLETE - XML EVIDENCE REQUIRED ⚠️**

CORE BLOCKING GAPS RESOLVED for currently supported equipment/idol types:

1. ~~Affix ID loss (exalted affixes)~~ — ✅ RESOLVED Phase 0A
2. ~~Affix ID loss (idol modifiers)~~ — ✅ RESOLVED Phase 0A
3. ~~Item type -> EquipmentType mapping missing~~ — ✅ RESOLVED Phase 0B1 (core equipment)
4. ~~Idol size format conversion needed~~ — ✅ RESOLVED Phase 0B2 (parser-supported idols)

WEAPON/OFF-HAND MAPPING GAPS REMAIN UNRESOLVED:

5. Weapon EquipmentType mapping — ⚠️ BLOCKED (Phase 0B3 research incomplete)
6. Off-hand EquipmentType mapping — ⚠️ BLOCKED (Phase 0B3 research incomplete)

**Phase 0B3 Research Summary:**

Verified 17 weapon/off-hand item_type values exist in game_data.json:
- 12 weapon types: item_type 5-16, 23-24
- 3 off-hand types: item_type 17-19

XML evidence search results:
- Searched: data/debug/filters/xml_semantics_test.xml (only available XML file)
- Found: Core equipment (HELMET, BODY_ARMOR, BELT, BOOTS, GLOVES, AMULET, RING, RELIC) and IDOL_2x1
- NOT found: Any weapon or off-hand EquipmentType enum values

Conclusion: Cannot implement evidence-based weapon/off-hand mapping without real XML examples.

**Current XML Generator capability:**

Can produce valid rules for:
- Exalted items: Core equipment slots only (Helmet, Body Armor, Belt, Boots, Gloves, Amulet, Ring, Relic)
- Idol items: Parser-supported sizes (Minor 1x1, Humble 1x2, Grand 1x3, Adorned 1x4)
- Unique items: All unique IDs (no equipment type filtering needed)

Cannot produce rules for:
- Weapon exalted items (mapping unknown)
- Off-hand exalted items (mapping unknown)

**Next action required:**

Create real Last Epoch loot filter rules in-game for weapon/off-hand item types, export as XML, add to repository for Phase 0B3 evidence-based mapping completion.

**REMAINING GAPS (BLOCKING for weapon/off-hand exalted rules):**

5. **Weapon EquipmentType mapping — ⚠️ BLOCKED (Phase 0B3 incomplete)**
   - Research completed: 12 weapon item_type values verified in game_data (5-16, 23-24)
   - XML evidence: NONE - no weapon EquipmentType enums confirmed in available XML files
   - Impact: Cannot generate weapon exalted rules
   - Required: Real Last Epoch XML filters containing weapon SubTypeCondition rules
   - Status: BLOCKED - MORE XML EVIDENCE REQUIRED

6. **Off-hand EquipmentType mapping — ⚠️ BLOCKED (Phase 0B3 incomplete)**
   - Research completed: 3 off-hand item_type values verified in game_data (17-19: Quiver, Shield, Off-Hand Catalyst)
   - XML evidence: NONE - no off-hand EquipmentType enums confirmed in available XML files
   - Impact: Cannot generate off-hand exalted rules
   - Required: Real Last Epoch XML filters containing off-hand SubTypeCondition rules
   - Status: BLOCKED - MORE XML EVIDENCE REQUIRED

**NON-BLOCKING GAPS:**

7. Additional idol sizes (25, 28, 30, 31, 32, 41) not mapped by parser

Weapon and off-hand exalted rules cannot be generated until Phase 0B3 research completes with real XML evidence.

**Verification:**
- Affix ID preservation: tests/test_phase_0a_affix_id.py (4/4 passed)
- EquipmentType mapping: tests/test_equipment_type_mapper.py (31/31 passed)
- IdolSize mapping: tests/test_idol_size_mapper.py (35/35 passed)
- Total test coverage: 232 passed, 1 skipped, 0 failed

## 16. Non-Blocking Gaps Summary

THREE NON-BLOCKING LIMITATIONS:

1. SubTypes handling (can use empty safely)
2. Mixed affix tiers (verify Analyzer behavior or use max_tier)
3. Style customization (can use hardcoded defaults)

These can be addressed with defaults or simple fallbacks.

## 17. Recommended Implementation Plan

### Phase 0: Fix Blocking Gaps (REQUIRED before XML Generator)

1. Add affix_id field to AffixDTO
   - Modify: app/dto/models.py
   - Update: AffixDTO dataclass

2. Preserve affix_id in Parser
   - Modify: app/parsers/planner_profile_parser.py
   - Change: _parse_affix to include ID

3. Update Analyzer to use affix_id
   - Modify: app/analyzer/build_analyzer.py
   - Change: Aggregate by (affix_id, name, tier)

4. Update rule models
   - Modify: app/generator/rule_models.py
   - Change: FilterRule.affixes to FrozenSet[Tuple[int, str, int]] (id, name, tier)
   - Change: OptimizedRule.affixes likewise
   - Change: OptimizedRule.modifiers to include IDs

5. Create EquipmentType mapping
   - Create: app/generator/equipment_type_mapper.py
   - Function: map_item_type_to_equipment_type(item_type: int) -> str
   - Data: Static dict or loaded from game_data

6. Create IdolSize parser
   - Create: app/generator/idol_size_mapper.py
   - Function: parse_idol_size(size_str: str) -> str
   - Logic: Extract dimensions, format as "IDOL_{w}x{h}"

### Phase 1: XML Generator Implementation (AFTER Phase 0)

7. Create XML condition builders
   - SubTypeCondition builder
   - AffixCondition builder
   - RarityCondition builder
   - UniqueModifiersCondition builder

8. Create XML rule serializer
   - Map OptimizedRule to XML Rule
   - Apply style policy
   - Assign Order

9. Create XML document writer
   - Root metadata
   - Rules container
   - XML namespace handling

10. Add validation
	- Schema validation
	- Required field checks
	- Order sequence verification

### Phase 2: Testing

11. Unit tests for each component
12. Integration test with sample OptimizedRule list
13. Validation against real XML structure
14. Manual testing in Last Epoch game

## 18. Architectural Decision

VERDICT: MODEL ADJUSTMENT REQUIRED BEFORE XML GENERATOR

Blocking gaps prevent proceeding to XML Generator implementation.

Recommended sequence:
1. Fix all 4 blocking gaps (Phase 0)
2. Run full test suite to verify no regressions
3. Implement XML Generator (Phase 1)

Estimated impact of Phase 0 changes:
- Modified files: 5-6
- New files: 2-3
- Test updates: ~20 tests may need affix ID updates
- Risk: MEDIUM (touches multiple pipeline stages)

## 19. Alternative: Partial Implementation

If blocking gap fixes are delayed, XML Generator can be implemented with:

STUB MODE:
- Placeholder affix IDs (USE NEGATIVE VALUES like -1, -2 to indicate placeholder)
- Placeholder EquipmentType ("UNKNOWN_TYPE")
- Warning logs for missing data

This allows XML Generator structure to be built and tested with fake data.

NOT RECOMMENDED: Stub mode will produce invalid XML that won't work in game.

## 20. Verification Questions

Before starting implementation, verify:

1. Does current Analyzer create candidates with mixed affix tiers?
   - Action: Check analyzer code and test cases
   - If YES: Need separate rules or tier unification strategy

2. Are there item_type values in current builds that need mapping?
   - Action: Examine real planner profiles
   - Create mapping for all observed item_type values

3. What unique modifiers actually exist in game?
   - Action: Check if Rolls can be completely empty
   - Verify minimal valid UniqueModifiersCondition structure

4. Are there idol sizes beyond the 6 standard ones?
   - Action: Verify complete idol size inventory
   - Ensure regex covers all formats

## 21. Success Criteria

XML Generator implementation is considered successful when:

1. All blocking gaps are resolved
2. Generated XML validates against Last Epoch XML schema
3. Generated filter loads in Last Epoch game without errors
4. Generated rules match expected items in game (manual verification)
5. Order assignment produces first-match-wins behavior correctly
6. Style policy makes categories visually distinct
7. 100% unit test coverage for XML generation logic
8. Integration test validates complete pipeline: Analyzer -> RuleBuilder -> RuleOptimizer -> XML Generator

## 22. Out of Scope

XML Generator v1 does NOT include:

- HIDE rules
- Level-dependent filtering
- User-configurable style profiles
- Dynamic color assignment
- Sound customization
- Unique roll filtering
- Complex affix tier logic
- Multiple filter generation
- Filter update/merge functionality

These are future enhancements.

## 23. Dependencies

XML Generator depends on:

- Python 3.10+
- No additional libraries required (use standard xml.etree.ElementTree)
- RuleOptimizer output (List[OptimizedRule])
- Config (for metadata)
- EquipmentType mapper (to be created)
- IdolSize parser (to be created)

## 24. Performance Considerations

Expected performance for typical filter generation:

- Input: ~50-150 OptimizedRule instances
- Output: ~5-20 KB XML file
- Processing time: < 100ms
- Memory: Minimal (all data in memory already)

No performance optimization needed for v1.

## 25. Error Handling

XML Generator must handle:

- Invalid OptimizedRule (missing required fields) -> ValueError with clear message
- Unknown category -> ValueError
- Missing unique_id -> ValueError
- Empty condition data -> ValueError
- Duplicate Order -> ValueError (implementation bug)

All errors should be fail-fast with descriptive messages.

Do NOT silently skip invalid rules.

## 26. Logging

XML Generator should log:

- INFO: Generation started, rule count
- INFO: Generation completed, output file path
- DEBUG: Each rule being processed
- DEBUG: Style policy applied
- WARNING: Non-blocking gaps encountered (using defaults)
- ERROR: Blocking gaps or validation failures

Use structured logging with component name.

## 27. Testing Strategy

Unit tests (per component):
- OrderAssigner: Verify sequential order assignment
- ConditionBuilder: Each condition type separately
- RuleSerializer: Complete rule with all fields
- MetadataBuilder: Root structure
- StylePolicy: Category-based defaults

Integration tests:
- End-to-end: OptimizedRule list -> valid XML
- Real scenario: Sample from XML_FILTER_RESEARCH examples
- Edge cases: Empty affix list, single unique, merged rules

Validation tests:
- XML well-formed
- Order sequence correct
- Required fields present
- Namespace correct

## 28. Documentation Requirements

After implementation, create:

- XML_GENERATOR.md: Component design and architecture
- XML_GENERATOR_API.md: Public functions and usage
- Update PROJECT_CONTEXT.md: Add XML Generator to pipeline diagram

## 29. Migration Path

When blocking gaps are fixed:

1. Update all existing tests with affix IDs
2. Regenerate test fixtures with new model
3. Verify RuleOptimizer tests still pass
4. Verify Analyzer tests still pass
5. Update sample_game_data.json if needed

Estimated test update effort: 2-4 hours

## 30. Conclusion

This specification provides complete mapping design from OptimizedRule to Last Epoch XML.

CRITICAL FINDING: 4 blocking gaps prevent immediate implementation.

RECOMMENDED NEXT STEP: Fix blocking gaps (Phase 0) before implementing XML Generator.

Once gaps are resolved, this specification provides sufficient detail for unambiguous implementation.

---

End of Specification
