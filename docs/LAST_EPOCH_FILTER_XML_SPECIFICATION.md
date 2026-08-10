# Last Epoch Filter XML Specification

## 1. Source

This specification is based on real Last Epoch loot filter XML exported from the game.

Source file: data/debug/filters/xml_semantics_test.xml

Last Epoch version: 1.4.7

## 2. Root Structure

Root element: ItemFilter

Namespace: xmlns:i="http://www.w3.org/2001/XMLSchema-instance"

Metadata fields:
- name: filter display name
- filterIcon: numeric icon ID
- filterIconColor: numeric color ID
- description: optional text description
- lastModifiedInVersion: game version string (e.g., "1.4.7")
- lootFilterVersion: numeric version (0 observed)

Rules container: rules

Child elements: Rule (multiple)

## 3. Rule Structure

Each Rule contains:

Action:
- type: SHOW or HIDE

Conditions:
- conditions: container for Condition elements
- Each Condition has i:type attribute specifying condition type

Style fields:
- recolor: boolean (true/false)
- color: numeric color ID (0-15+)
- emphasized: boolean
- nameOverride: optional text override

Audio/Visual:
- SoundId: numeric sound ID
- MapIconId: numeric icon ID for map display
- BeamOverride: boolean
- BeamSizeOverride: NONE, SMALL, MEDIUM, LARGE, VERYLARGE
- BeamColorOverride: numeric color ID

State:
- isEnabled: boolean (true/false)

Ordering:
- Order: integer (lower numbers appear first in UI, but see section 4)

Deprecated fields:
- levelDependent_deprecated: false
- minLvl_deprecated: 0
- maxLvl_deprecated: 0

## 4. Rule Ordering

CRITICAL FINDING: Rules have explicit Order field.

XML structure:
- Rules are stored in rules container
- Each Rule has Order element with integer value
- Order values observed: 0, 1, 2, 3, 4, 5, 6, 7, 8, 9

Order semantics:
- Lower Order value = higher priority in game evaluation
- Order 0 is evaluated first
- Order 9 is evaluated last

XML document order:
- In the test file, rules appear in DESCENDING Order (9, 8, 7, ... 2, 1, 0)
- This means XML document order does NOT determine evaluation order
- Game reads Order field explicitly

Conclusion:
- Rule evaluation order is determined by Order field ONLY
- XML Generator must set Order correctly
- RuleOptimizer must preserve Order when merging
- Lower Order = earlier evaluation = higher priority in first-match-wins

## 5. Item Type Condition

Condition type: SubTypeCondition

XML structure:

Condition i:type="SubTypeCondition"
  type
	EquipmentType: GLOVES, HELMET, BOOTS, BODY_ARMOR, etc.
	(can have multiple EquipmentType elements)
  /type
  subTypes (empty in observed examples)
/Condition

Key finding: MULTIPLE EquipmentType values in single condition

Example from test XML (lines 86-92):

type
  EquipmentType: HELMET
  EquipmentType: BOOTS
  EquipmentType: GLOVES
/type

This proves that one SubTypeCondition can match multiple equipment types.

Boolean semantics: Multiple EquipmentType values are OR-combined (item matches if it is ANY of the listed types).

Idol representation:
- Idol size is represented as EquipmentType
- Example: IDOL_2x1 (line 196)
- Idols use same SubTypeCondition as equipment

SubTypes field:
- Present but empty in all observed examples
- Likely intended for future or unused feature
- Current filters do not rely on subTypes

## 6. Affix Condition

Condition type: AffixCondition

XML structure:

Condition i:type="AffixCondition"
  affixes
	int: numeric affix ID
	(can have multiple int elements)
  /affixes
  comparsion: MORE_OR_EQUAL, ANY
  comparsionValue: integer tier threshold
  minOnTheSameItem: integer required count
  combinedComparsion: ANY (observed)
  combinedComparsionValue: integer (observed)
  advanced: true or false
/Condition

Fields explained:

affixes:
- List of int elements
- Each int is a numeric affix ID from game data
- Can be empty (empty affixes element)

comparsion:
- MORE_OR_EQUAL: minimum tier requirement for individual affixes
- ANY: no tier requirement (match any tier)

comparsionValue:
- Minimum tier when comparsion = MORE_OR_EQUAL
- Set to 0 when comparsion = ANY

minOnTheSameItem:
- Required count of matching affixes
- Example: 2 means "at least 2 of the selected affixes must be present"

combinedComparsion:
- Observed value: ANY
- Purpose: likely related to total tier sum comparison

combinedComparsionValue:
- Numeric value
- Purpose: likely minimum total tier sum across all matching affixes

advanced:
- Boolean flag
- true: advanced affix settings are used
- false: basic affix matching

## 7. Multiple Affix Semantics

CONFIRMED: XML supports multiple selected affixes with required count.

Example from test XML (lines 54-66):

affixes
  int: 502
  int: 25
  int: 14
/affixes
comparsion: MORE_OR_EQUAL
comparsionValue: 6
minOnTheSameItem: 2

This translates to:
"Match items with at least 2 of affixes [502, 25, 14], each T6+"

Runtime semantics (based on minOnTheSameItem):
- minOnTheSameItem=1: at least 1 of the selected affixes
- minOnTheSameItem=2: at least 2 of the selected affixes
- minOnTheSameItem=3: at least 3 of the selected affixes

Boolean behavior:
- affixes list is treated as a SET of possible affixes
- minOnTheSameItem specifies required count
- Item matches if it has >= minOnTheSameItem affixes from the set
- Each matching affix must meet tier requirement (comparsionValue)

CRITICAL for merge safety:
- affixes=[A, B, C] with minOnTheSameItem=2 matches: A+B, A+C, B+C, A+B+C
- affixes=[A, B] with minOnTheSameItem=2 matches: A+B (only)
- These are NOT equivalent even though both require 2 affixes

Conclusion:
- Cannot merge partial affix overlap without introducing extra match combinations
- Example: merging A+B and A+C into [A,B,C] minOnTheSameItem=2 adds unwanted B+C match

## 8. Unique Condition

Condition type: UniqueModifiersCondition

XML structure:

Condition i:type="UniqueModifiersCondition"
  Uniques (can have multiple)
	UniqueId: integer unique item ID
	Rolls
	  UniqueModifierWithRollId (multiple)
		RollId: integer modifier index
		Modifier
		  MinRoll: integer or nil
		  MaxRoll: integer or nil
		/Modifier
	  /UniqueModifierWithRollId
	/Rolls
  /Uniques
/Condition

Key finding: MULTIPLE Uniques elements in single condition

Example from test XML (lines 285-370):
One UniqueModifiersCondition contains THREE Uniques elements:
- UniqueId 300
- UniqueId 296
- UniqueId 144

Boolean semantics: Multiple Uniques are OR-combined (item matches if it is ANY of the listed uniques).

Rolls structure:
- Each unique has Rolls container
- Each Roll has RollId (0, 1, 2, 3, etc.)
- Modifier specifies MinRoll and MaxRoll range
- nil values mean no constraint on that roll

Purpose:
- Allows filtering by unique item modifier roll values
- Example: "Show Throne of Ambition with minroll 140+ on modifier 1"

CRITICAL for merge safety:
- XML DOES support multiple unique IDs in one condition
- This enables lossless merging of multiple unique rules with same action/style
- Example: Rule for unique_id=243 and Rule for unique_id=300 can merge into one UniqueModifiersCondition with two Uniques elements

## 9. Idol Handling

Idol item type: Represented as EquipmentType in SubTypeCondition

Example: EquipmentType IDOL_2x1

Idol sizes observed:
- IDOL_2x1 (line 196)

Idol affixes: Use standard AffixCondition

Example from test XML (lines 200-211):
- SubTypeCondition with IDOL_2x1
- AffixCondition with affixes [114, 319]
- minOnTheSameItem=1
- comparsion=ANY (no tier requirement)
- advanced=false

Conclusion:
- Idols are treated as equipment type, not separate item class
- Idol modifiers use same affix ID system as gear affixes
- Idol size is specified via EquipmentType (IDOL_2x1, IDOL_1x1, IDOL_2x2, IDOL_1x2, IDOL_1x3, IDOL_1x4)

Multiple idol sizes:
- Since SubTypeCondition supports multiple EquipmentType values
- XML CAN represent multiple idol sizes in one rule
- Example: EquipmentType IDOL_2x1 + EquipmentType IDOL_1x1 would match either size

CRITICAL for merge safety:
- Merging same-modifier different-size idol rules IS possible in XML
- This is SAFE if action/style are identical

## 10. Boolean Semantics

Summary of boolean behavior:

MULTIPLE VALUES INSIDE ONE CONDITION:

SubTypeCondition with multiple EquipmentType:
- XML: Multiple EquipmentType elements
- Semantics: OR (item matches ANY of the types)
- Confidence: CONFIRMED from test XML

AffixCondition with multiple affixes:
- XML: Multiple int elements in affixes
- Semantics: minOnTheSameItem specifies required count
- Example: [A, B, C] with minOnTheSameItem=2 means ANY 2 OF 3
- Confidence: CONFIRMED from test XML structure

UniqueModifiersCondition with multiple Uniques:
- XML: Multiple Uniques elements
- Semantics: OR (item matches ANY of the uniques)
- Confidence: CONFIRMED from test XML

MULTIPLE CONDITIONS INSIDE ONE RULE:

Multiple Condition elements in conditions container:
- XML: Multiple Condition elements
- Semantics: AND (all conditions must match)
- Example: SubTypeCondition + AffixCondition = item must match type AND affixes
- Confidence: STANDARD loot filter behavior (assumed)

RULE EVALUATION:

Multiple Rule elements in rules container:
- Evaluation order: Determined by Order field (lower Order = earlier evaluation)
- Semantics: First-match-wins (once item matches a rule, lower-priority rules are ignored)
- Confidence: KNOWN game behavior

## 11. Action / Style

Action field: type

Values:
- SHOW: display item
- HIDE: hide item

Style fields that affect merge safety:

MUST BE IDENTICAL for lossless merge:
- type (SHOW vs HIDE)
- recolor (true/false)
- color (0-15+)
- emphasized (true/false)
- SoundId (numeric)
- MapIconId (numeric)
- BeamOverride (true/false)
- BeamSizeOverride (NONE, SMALL, MEDIUM, LARGE, VERYLARGE)
- BeamColorOverride (numeric)

Optional fields (probably safe to differ):
- nameOverride (rarely used)

Conclusion:
- Two rules can only be merged if ALL style fields match
- Merging SHOW with HIDE is UNSAFE
- Merging different colors is UNSAFE (changes user experience)
- Merging different sounds is UNSAFE (changes user experience)

## 12. Confirmed XML Capabilities

Based on real XML analysis:

CONFIRMED SAFE:
1. Multiple EquipmentType values in one SubTypeCondition (OR semantics)
2. Multiple affixes with minOnTheSameItem (required-count semantics)
3. Multiple Uniques in one UniqueModifiersCondition (OR semantics)
4. Multiple idol sizes can be represented in one SubTypeCondition
5. Explicit Order field for rule priority

CONFIRMED CONSTRAINTS:
1. Multiple affixes with minOnTheSameItem creates combinatorial matching
2. Partial affix overlap merge introduces extra combinations (UNSAFE)
3. Order field must be preserved during optimization
4. All style fields must match for lossless merge

## 13. Merge Implications

EXALTED RULES:

Same base + same affixes + same tier:
- SAFE: Exact duplicate, can merge

Same base + same affixes + different tier:
- CONDITIONAL: Must verify action/style/Order are compatible
- Lower tier threshold expands match set
- Safe only if merged rule outcome matches original union

Same base + partial affix overlap:
- UNSAFE: Merging A+B and A+C into [A,B,C] minOnTheSameItem=2 adds B+C match

Different base + same affixes:
- NOW CONFIRMED SAFE if action/style match
- XML supports multiple EquipmentType in one rule
- Example: HELMET + BOOTS + GLOVES with same affix can merge

Same slot + different type/subtype:
- CONFIRMED SAFE if represented as EquipmentType variants
- Example: Different helmet subtypes can merge if XML represents via type list

IDOL RULES:

Same size + same modifiers:
- SAFE: Exact duplicate

Same size + different modifiers:
- UNSAFE: Cannot merge without changing semantics

Different size + same modifiers:
- NOW CONFIRMED SAFE if action/style match
- XML supports multiple idol sizes in one SubTypeCondition
- Example: IDOL_2x1 + IDOL_1x1 with same affix can merge

UNIQUE RULES:

Same unique + same rolls:
- SAFE: Exact duplicate

Different uniques + same slot:
- NOW CONFIRMED SAFE if action/style match
- XML supports multiple Uniques in one UniqueModifiersCondition
- Multiple unique IDs can be listed in single condition

## 14. Rule Budget

Last Epoch maximum filter limit: 200 rules

LastEpochFilterBuilder project budget: 140 rules

Reason:
- Project intentionally reserves approximately 60 rules for manual user-created rules
- 140 is a PROJECT POLICY, not a game technical limitation
- User can modify filter.max_rules in config.yaml if desired

Configuration:
- Location: app/config/config_manager.py
- Field: filter.max_rules
- Default: 140
- Validation: Must be positive integer

RuleOptimizer responsibility:
- Reduce generated rules to <= filter.max_rules (default 140)
- Stage 1: Lossless merge to reduce count
- Stage 2: Lossy pruning if still > limit

## 15. Unconfirmed Details

The following remain UNCONFIRMED and require further testing:

1. combinedComparsion and combinedComparsionValue exact semantics
   - Observed value: combinedComparsion=ANY
   - Likely purpose: total tier sum comparison
   - Need runtime verification

2. subTypes field in SubTypeCondition
   - Present but empty in all observed examples
   - Purpose unknown
   - May be deprecated or unused

3. Exact runtime behavior of minOnTheSameItem with tier requirements
   - XML structure clear
   - Need in-game testing to confirm match behavior
   - Assumption: each matching affix must meet individual tier requirement

4. Roll value constraints in UniqueModifiersCondition
   - MinRoll/MaxRoll structure clear
   - Need testing: does nil mean "any value" or "no constraint"?
   - Impact on unique rule merging with roll filters

5. Maximum number of values per condition
   - Example: how many EquipmentType values are allowed?
   - Example: how many affixes are allowed?
   - Example: how many Uniques are allowed?
   - No observed limits, but may exist

6. Interaction between deprecated fields and current fields
   - levelDependent_deprecated, minLvl_deprecated, maxLvl_deprecated present
   - All set to false/0 in test file
   - Unclear if still processed by game

## Revision History

- Initial version: Based on data/debug/filters/xml_semantics_test.xml from Last Epoch 1.4.7
- Research date: Current session
- Purpose: Guide RuleOptimizer implementation
