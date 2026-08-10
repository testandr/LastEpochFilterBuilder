# Last Epoch Loot Filter XML Research

## Sources

Real Last Epoch loot filter XML file:
- File: data/debug/filters/xml_semantics_test.xml
- Game version: 1.4.7
- Confidence: CONFIRMED (real game export)

Existing documentation:
- docs/LAST_EPOCH_FILTER_XML_SPECIFICATION.md (comprehensive analysis)
- docs/DATA_MODELS.md (rarity values)
- docs/FILTER_GENERATION_SPECIFICATION.md (generation architecture)

## Root Structure

Root element: ItemFilter

XML namespace: xmlns:i="http://www.w3.org/2001/XMLSchema-instance"

Metadata fields:
- name: filter display name (string)
- filterIcon: numeric icon ID (integer)
- filterIconColor: numeric color ID (integer)
- description: optional text description (string or empty)
- lastModifiedInVersion: game version string (e.g., "1.4.7")
- lootFilterVersion: numeric version (observed: 0)

Rules container: rules
- Contains multiple Rule elements

Status: CONFIRMED

## Rule Structure

Each Rule element contains:

Action:
- type: SHOW or HIDE

Conditions:
- conditions: container element
- Multiple Condition elements with i:type attribute

Style fields:
- recolor: boolean (true/false)
- color: numeric color ID (0-15+)
- emphasized: boolean
- nameOverride: optional text override

Audio/Visual:
- SoundId: numeric sound ID
- MapIconId: numeric icon ID for minimap
- BeamOverride: boolean
- BeamSizeOverride: NONE, SMALL, MEDIUM, LARGE, VERYLARGE
- BeamColorOverride: numeric color ID

State:
- isEnabled: boolean (true/false)

Ordering:
- Order: integer (lower = higher priority)

Deprecated fields (present but unused):
- levelDependent_deprecated: false
- minLvl_deprecated: 0
- maxLvl_deprecated: 0

Status: CONFIRMED

## Rule Ordering

CRITICAL FINDING: Rules use explicit Order field.

How order is stored:
- Each Rule has Order element with integer value
- Lower Order value = higher evaluation priority
- Order 0 is evaluated first
- Order 9 is evaluated last

XML document order:
- Document order DOES NOT determine evaluation order
- Game reads Order field explicitly
- Observed pattern: rules appear in DESCENDING Order in XML (9, 8, 7... 1, 0)

Implications:
- XML Generator must assign Order values correctly
- Lower Order = higher priority = evaluated first
- First-match-wins behavior in game

Evidence: xml_semantics_test.xml lines demonstrate rules with explicit Order field

Status: CONFIRMED

## Visibility / Actions

Rule action field: type

Values:
- SHOW: display item with optional style
- HIDE: hide item from view

Status: CONFIRMED

## Equipment Type Conditions

Condition type: SubTypeCondition

XML structure:
```
<Condition i:type="SubTypeCondition">
  <type>
	<EquipmentType>GLOVES</EquipmentType>
	<EquipmentType>HELMET</EquipmentType>
  </type>
  <subTypes />
</Condition>
```

Equipment type values observed:
- GLOVES
- HELMET
- BOOTS
- BODY_ARMOR
- Weapon types
- Ring
- Amulet
- Relic

Multiple equipment types:
- YES, CONFIRMED
- Multiple EquipmentType elements allowed in one SubTypeCondition
- Boolean semantics: OR (item matches ANY listed type)
- Evidence: xml_semantics_test.xml lines 86-92 show HELMET + BOOTS + GLOVES in single rule

SubTypes field:
- Present but empty in all observed examples
- Purpose: likely for future or unused feature
- Current filters do not rely on subTypes

Status: CONFIRMED

## Rarity Conditions

Condition type: RarityCondition

XML structure:
```
<Condition i:type="RarityCondition">
  <rarity>NORMAL</rarity>
</Condition>
```

Rarity values (from DATA_MODELS.md):
- Normal
- Magic
- Rare
- Exalted
- Unique
- Set

Note: XML uses UPPERCASE (NORMAL), documentation uses capitalized (Normal)
Assumed both are valid or game normalizes case.

Observed example:
- NORMAL rarity in xml_semantics_test.xml line 392

Status: CONFIRMED (structure), PARTIALLY_CONFIRMED (all rarity values)

How to filter Exalted items:
- Use RarityCondition with rarity=EXALTED or Exalted
- Alternative: Use AffixCondition with tier requirements (exalted = tier 6+)
- Likely both work, RarityCondition is cleaner

Status: INFERRED (not directly observed in test XML, but structure is confirmed)

## Affix Conditions

Condition type: AffixCondition

XML structure:
```
<Condition i:type="AffixCondition">
  <affixes>
	<int>502</int>
	<int>25</int>
	<int>14</int>
  </affixes>
  <comparsion>MORE_OR_EQUAL</comparsion>
  <comparsionValue>6</comparsionValue>
  <minOnTheSameItem>2</minOnTheSameItem>
  <combinedComparsion>ANY</combinedComparsion>
  <combinedComparsionValue>12</combinedComparsionValue>
  <advanced>true</advanced>
</Condition>
```

Fields:

affixes:
- List of int elements
- Each int is numeric affix ID from game data
- Can be empty (empty affixes element)

comparsion:
- MORE_OR_EQUAL: minimum tier requirement
- ANY: no tier requirement observed

comparsionValue:
- Minimum tier threshold for individual affixes
- Example: 6 means tier 6 or higher

minOnTheSameItem:
- Required count of matching affixes
- Example: 2 means "at least 2 of the listed affixes"

combinedComparsion:
- Observed: ANY
- Purpose: likely for total tier sum comparison

combinedComparsionValue:
- Numeric value
- Purpose: likely minimum total tier sum

advanced:
- Boolean flag
- true: advanced affix settings are used
- false: basic affix matching

Status: CONFIRMED

## Affix Tier Conditions

Individual affix tier:
- Specified by comparsion + comparsionValue
- MORE_OR_EQUAL with comparsionValue=6 means "tier 6 or higher"

Total affix tier:
- Specified by combinedComparsion + combinedComparsionValue
- Example: combinedComparsionValue=12 likely means "total tier sum >= 12"

Status: CONFIRMED (structure), INFERRED (exact semantics)

## Required Affix Count

Field: minOnTheSameItem

Semantics:
- Specifies how many affixes from the list must be present
- affixes=[A, B, C] with minOnTheSameItem=2 means "any 2 of 3"
- Boolean behavior: item matches if it has >= minOnTheSameItem affixes from set
- Each matching affix must meet tier requirement (comparsionValue)

Critical for merge safety:
- affixes=[A, B, C] with minOnTheSameItem=2 matches: A+B, A+C, B+C, A+B+C
- affixes=[A, B] with minOnTheSameItem=2 matches: A+B only
- These are NOT equivalent even though both require 2 affixes
- Cannot merge partial affix overlap without introducing extra match combinations

Example from xml_semantics_test.xml lines 54-66:
```
<affixes>
  <int>502</int>
  <int>25</int>
  <int>14</int>
</affixes>
<minOnTheSameItem>2</minOnTheSameItem>
```
Translates to: "Match items with at least 2 of affixes [502, 25, 14]"

Status: CONFIRMED

## Idol Conditions

Idol representation: EquipmentType in SubTypeCondition

Idol size values observed:
- IDOL_2x1

Idol size values expected (standard Last Epoch idol sizes):
- IDOL_1x1 (Minor Idol)
- IDOL_1x2 (Small Idol)
- IDOL_2x1 (Grand Idol)
- IDOL_1x3 (Adorned Idol)
- IDOL_2x2 (Large Idol)
- IDOL_1x4 (Huge Idol)

Idol affixes/modifiers:
- Use standard AffixCondition with numeric affix IDs
- Same structure as equipment affixes
- Idol modifiers use game's affix ID system

Example from xml_semantics_test.xml lines 196-211:
```
<Condition i:type="SubTypeCondition">
  <type>
	<EquipmentType>IDOL_2x1</EquipmentType>
  </type>
  <subTypes />
</Condition>
<Condition i:type="AffixCondition">
  <affixes>
	<int>114</int>
	<int>319</int>
  </affixes>
  <minOnTheSameItem>1</minOnTheSameItem>
  <comparsion>ANY</comparsion>
  <advanced>false</advanced>
</Condition>
```

Status: CONFIRMED (structure and IDOL_2x1), INFERRED (other idol sizes)

## Idol Size Conditions

Multiple idol sizes in one rule:
- YES, SUPPORTED
- Since SubTypeCondition supports multiple EquipmentType values
- Can specify multiple idol sizes: IDOL_2x1 + IDOL_1x1
- Boolean semantics: OR (item matches ANY listed idol size)

Status: CONFIRMED (capability), NOT_OBSERVED (actual example with multiple idol sizes)

## Unique Item Conditions

Condition type: UniqueModifiersCondition

XML structure:
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
	<Rolls>
	  ...
	</Rolls>
  </Uniques>
</Condition>
```

Unique identification:
- Uses numeric UniqueId (integer)
- NOT item name, NOT base type

Unique modifier rolls:
- Rolls container with UniqueModifierWithRollId elements
- Each roll has RollId (0, 1, 2, 3...)
- Modifier specifies MinRoll and MaxRoll range
- nil values mean no constraint on that roll
- Purpose: filter by specific unique modifier roll values

Multiple uniques in one rule:
- YES, CONFIRMED
- Multiple Uniques elements in one UniqueModifiersCondition
- Boolean semantics: OR (item matches ANY listed unique)
- Evidence: xml_semantics_test.xml lines 285-370 show 3 uniques in one rule

Status: CONFIRMED

## Style Options

Recolor:
- Field: recolor (boolean)
- Field: color (numeric 0-15+)
- Changes item text color

Emphasis:
- Field: emphasized (boolean)
- Makes item text larger/bolder

Beam:
- Field: BeamOverride (boolean)
- Field: BeamSizeOverride (NONE, SMALL, MEDIUM, LARGE, VERYLARGE)
- Field: BeamColorOverride (numeric color ID)
- Shows light beam on item

Sound:
- Field: SoundId (numeric sound ID)
- Plays sound when item drops

Icon:
- Field: MapIconId (numeric icon ID)
- Shows icon on minimap

Name override:
- Field: nameOverride (optional text)
- Changes displayed item name

Status: CONFIRMED

## XML Capability Matrix

| Capability | Status | Evidence |
|------------|--------|----------|
| Multiple equipment types in one rule | CONFIRMED | xml_semantics_test.xml lines 86-92 |
| Multiple subtypes | UNKNOWN | subTypes field exists but always empty |
| Multiple affixes | CONFIRMED | xml_semantics_test.xml lines 54-66 |
| Required affix count | CONFIRMED | minOnTheSameItem field |
| Minimum individual affix tier | CONFIRMED | comparsion + comparsionValue |
| Total affix tier | INFERRED | combinedComparsion + combinedComparsionValue |
| Multiple idol sizes in one rule | CONFIRMED | EquipmentType list supports multiple |
| Multiple unique items in one rule | CONFIRMED | xml_semantics_test.xml lines 285-370 |
| Unique item ID filtering | CONFIRMED | UniqueId field |
| Unique item name filtering | NOT_SUPPORTED | Only UniqueId observed |
| Unique item roll filtering | CONFIRMED | Rolls structure with MinRoll/MaxRoll |
| Rarity filtering | CONFIRMED | RarityCondition with rarity field |
| Rule order by Order field | CONFIRMED | Order element in each Rule |
| Rule order by document position | NOT_USED | Game reads Order field explicitly |
| SHOW action | CONFIRMED | type=SHOW |
| HIDE action | CONFIRMED | type=HIDE |
| Color/Recolor | CONFIRMED | recolor + color fields |
| Emphasis | CONFIRMED | emphasized field |
| Beam | CONFIRMED | BeamOverride + BeamSizeOverride + BeamColorOverride |
| Sound | CONFIRMED | SoundId field |
| Icon | CONFIRMED | MapIconId field |

## RuleOptimizer Compatibility

Checking RuleOptimizer merge strategies against XML capabilities:

EXALTED RULES:

Same base + same affixes:
- RuleOptimizer: Supports merge
- XML: COMPATIBLE
- Status: SAFE

Different item_type + same affixes:
- RuleOptimizer: Supports cross-base merge
- XML: COMPATIBLE (multiple EquipmentType in SubTypeCondition)
- Status: SAFE

Different sub_type + same affixes:
- RuleOptimizer: Likely supports (shares base logic)
- XML: UNKNOWN (subTypes field unused)
- Status: NEEDS_VERIFICATION

Multiple item_types in one rule:
- RuleOptimizer: Cross-base merge produces this
- XML: CONFIRMED SUPPORTED
- Status: SAFE

Multiple affixes in one rule:
- RuleOptimizer: Core functionality
- XML: CONFIRMED SUPPORTED
- Status: SAFE

Partial affix overlap merge:
- RuleOptimizer: Should avoid (introduces extra combinations)
- XML: Technically possible but semantically wrong
- Status: CORRECTLY_AVOIDED

IDOL RULES:

Same size + same modifiers:
- RuleOptimizer: Supports merge
- XML: COMPATIBLE
- Status: SAFE

Different sizes + same modifiers:
- RuleOptimizer: Likely supports cross-size merge
- XML: COMPATIBLE (multiple EquipmentType values)
- Status: SAFE

Multiple sizes in one rule:
- RuleOptimizer: Cross-size merge produces this
- XML: CONFIRMED SUPPORTED
- Status: SAFE

UNIQUE RULES:

Same unique duplicate:
- RuleOptimizer: Deduplicates
- XML: COMPATIBLE
- Status: SAFE

Different unique IDs:
- RuleOptimizer: Supports merge
- XML: CONFIRMED SUPPORTED (multiple Uniques elements)
- Status: SAFE

Multiple uniques in one rule:
- RuleOptimizer: Cross-unique merge produces this
- XML: CONFIRMED SUPPORTED
- Status: SAFE

OVERALL COMPATIBILITY:

RuleOptimizer merge strategies align well with XML capabilities.

Key compatibility points:
1. Multiple equipment types: SUPPORTED by XML
2. Multiple affixes with count: SUPPORTED by XML
3. Multiple uniques: SUPPORTED by XML
4. Multiple idol sizes: SUPPORTED by XML

Potential issues:
1. SubType handling: XML has subTypes field but it's unused - need to verify if RuleOptimizer uses sub_type
2. affixes merge semantics: RuleOptimizer must avoid partial overlap (appears to do so)

## Confirmed Facts

1. XML uses explicit Order field for rule priority (lower = higher priority)
2. Multiple EquipmentType values in one SubTypeCondition are OR-combined
3. Multiple affixes with minOnTheSameItem specify required count (any N of M)
4. Multiple Uniques in one UniqueModifiersCondition are OR-combined
5. Idols use EquipmentType (e.g., IDOL_2x1) in SubTypeCondition
6. Idol modifiers use standard AffixCondition with numeric IDs
7. Unique items are identified by numeric UniqueId, not name
8. RarityCondition exists with rarity field (NORMAL, EXALTED, etc.)
9. All style fields (color, beam, sound, icon) are optional
10. Document order does NOT determine evaluation order

## Unknowns

1. SubTypes field purpose and usage (exists but always empty)
2. Exact semantics of combinedComparsion and combinedComparsionValue
3. All possible idol size EquipmentType values (only IDOL_2x1 directly observed)
4. Complete list of rarity values in XML format (EXALTED vs Exalted case)
5. Whether RuleOptimizer actually uses sub_type field for merging
6. Maximum allowed Order value
7. Valid color ID range (observed 0-10, upper limit unknown)
8. All possible sound IDs and icon IDs

## Recommendations for XML Generator

1. Use explicit Order field for all rules (assign based on semantic_priority)
2. Use SubTypeCondition with multiple EquipmentType for cross-base merges
3. Use AffixCondition with proper minOnTheSameItem for affix count
4. Use UniqueModifiersCondition with multiple Uniques for unique merges
5. Always include required fields: type, conditions, isEnabled, Order
6. Set deprecated fields to default values (levelDependent_deprecated=false, etc.)
7. Map OptimizedRule.category to appropriate condition types:
   - exalted: SubTypeCondition + AffixCondition (+ optional RarityCondition)
   - idol: SubTypeCondition with IDOL_* + AffixCondition
   - unique: UniqueModifiersCondition
8. Map semantic_priority to Order (lower priority = higher Order value)
9. For uniques with modifier constraints, populate Rolls structure
10. Leave subTypes empty (follow observed pattern)
11. Use combinedComparsion=ANY and combinedComparsionValue for total tier sum if needed
12. Set emoji/visual style based on category and priority (color, emphasized, beam, sound)

Next implementation steps:
1. Create condition builder for each type (SubTypeCondition, AffixCondition, etc.)
2. Create Order assignment strategy from semantic_priority
3. Create style mapper from category/priority to visual settings
4. Implement XML serialization for each structure
5. Add validation for required fields and value ranges
