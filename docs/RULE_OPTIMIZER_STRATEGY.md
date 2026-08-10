# RuleOptimizer Strategy

## Overview

RuleOptimizer is responsible for reducing the number of FilterRule objects from RuleBuilder to meet the Last Epoch 140-rule hard limit while preserving maximum build coverage and value.

This document defines the research-driven strategy for safe rule merging, lossy pruning, and rule budget allocation.

## Responsibilities

RuleOptimizer DOES:
- Accept RuleBuildResult from RuleBuilder
- Perform lossless duplicate removal
- Perform safe semantic-preserving merges where XML allows
- Apply lossy pruning when necessary to reach 140 limit
- Maintain deterministic behavior
- Preserve protected high-value rules
- Return optimized RuleBuildResult for XML Generator

RuleOptimizer DOES NOT:
- Generate XML (XML Generator's job)
- Recalculate Analyzer scores
- Modify RuleBuilder logic
- Mutate input RuleBuildResult

## Architecture Position

PlannerProfileParser -> Analyzer -> RuleBuilder -> [RuleOptimizer] -> XML Generator

RuleOptimizer sits between:
- Upstream: RuleBuilder (provides independent rule candidates)
- Downstream: XML Generator (serializes to Last Epoch XML)

## Confirmed Game Semantics

### Rule Evaluation Order

Last Epoch loot filter evaluates rules from top to bottom.

If an item matches a rule, rules below it are NOT evaluated for that item (first-match-wins semantics).

Consequence: Rule order is part of the filter semantics. An earlier matching rule shadows later rules for the same item.

Impact on Optimizer:
- Cannot merge rules based solely on conditions
- Must consider action (SHOW/HIDE), style, priority, and rule position
- Earlier rule can shadow later rule, preventing it from ever matching
- Reordering rules can change filter behavior

### Multiple Affix Conditions

Last Epoch affix conditions can contain multiple selected affixes with advanced settings.

Confirmed capabilities:
- Select multiple affixes in one condition
- Specify required count (e.g., "match any 2 of these 3 affixes")
- Set minimum tier requirements
- Set total affix tier and other constraints

Important: Multiple selected affixes are NOT automatically AND-combined.

Structure:
  selected_affixes: [A, B, C]
  required_count: 2

This matches items with ANY 2 of the selected affixes.

Example:
  Rule with affixes [A, B, C] and required_count=2
  Matches: A+B, A+C, B+C

This is NOT equivalent to:
  Rule 1: A AND B
  Rule 2: A AND C

Because it also matches B+C (which neither original rule would match).

Impact on Optimizer:
- Grouping multiple rules by expanding selected_affix set usually changes semantics
- Required-count merge introduces additional match combinations
- Cannot safely merge partial affix overlaps into single required-count rule

## Lossless Merge Definition

A merge is LOSSLESS if and only if:

1. MatchSet(merged_rule) == union(MatchSet(original_rules))
   Every item matched by any original rule is matched by the merged rule.
   No item matched by the merged rule was unmatched by all original rules.

2. For each matched item, the outcome (action, style, visibility) is identical
   considering top-to-bottom rule evaluation order.

3. The merged rule does not change shadowing behavior with respect to other rules.

This is the fundamental correctness requirement for RuleOptimizer merging.

If any condition is violated, the merge is NOT lossless.

## Two-Stage Processing

### Stage 1: Lossless Merge
Goal: Reduce rule count WITHOUT changing which items are shown
Operations: duplicate removal, safe semantic merges
Rule count reduction: variable (depends on input overlap)

### Stage 2: Lossy Pruning
Goal: Enforce 140-rule hard limit by removing lowest-value rules
Operations: category-prioritized deletion
Only executed: IF Stage 1 output still exceeds 140

## Lossless Merge Strategy

### Exalted Rules

CASE A: Exact Duplicate
Condition: Same base_key AND same affixes
Result: SAFE - merge into one rule
Reason: Identical technical identity and affix requirements
Statistics: sum build_count, sum occurrence_count, union sources

CASE B: Same Base + Partial Affix Overlap
Example:
  Rule 1: Gloves (slot=Gloves, type=13, sub=0) + Affix A + Affix B
  Rule 2: Gloves (slot=Gloves, type=13, sub=0) + Affix A + Affix C
Condition: Same base_key, different affix sets
Result: UNSAFE - cannot merge without changing semantics
Reason: Each RuleBuilder rule represents a specific required affix combination (AND semantics). Merging into a single rule with selected_affixes=[A, B, C] and required_count=2 would ALSO match B+C, which neither original rule matched. This expands the MatchSet beyond the union of original rules.
Alternative: If XML allows selected_affixes=[A, B, C] with required_count=2 AND the optimizer has ALL possible 2-affix combinations from that set as separate rules (A+B, A+C, B+C), then merging would be lossless. However, partial coverage is UNSAFE.
Conclusion: Do NOT merge partial affix overlaps unless all combinations are present and merging is provably equivalent to the union.

CASE C: Same Affixes + Different Bases
Example:
  Rule 1: Helmet (type=1, sub=0) + Affix X
  Rule 2: Body Armour (type=2, sub=0) + Affix X
Condition: Same affixes, different base_key
Result: CONDITIONAL - only if XML supports multi-base matching in one rule
XML Requirement: UNCONFIRMED - need to verify if Last Epoch XML allows one rule to match multiple itemType values.
Recommendation: Do NOT merge until XML capability confirmed.

CASE D: Same Slot + Different ItemType/SubType
Example:
  Rule 1: Gloves (type=13, sub=0)
  Rule 2: Gloves (type=13, sub=1)
Condition: Same slot string, different type/subType
Result: CONDITIONAL - depending on XML slot-level matching
XML Requirement: UNCONFIRMED - can one rule match all itemTypes within a slot?
Recommendation: Do NOT merge until XML semantics confirmed.

CASE E: Different Affix Tiers
Example:
  Rule 1: Affix A T6+
  Rule 2: Affix A T7+
Condition: Same base_key, same affixes, different minimum tiers
Result: CONDITIONAL - lossless only if action, style, priority, and rule-order semantics are identical
Reason: Using lower minimum tier (T6+) expands the match set to include T6 items. This is lossless ONLY if both original rules have identical action (SHOW/HIDE), identical style/color, and the merged rule produces equivalent outcome for all matched items considering top-to-bottom rule evaluation order.
Risk: If rules differ in action, style, or would be shadowed differently by earlier rules, merge changes semantics.
Recommendation: Only merge tier-relaxation when rules are truly equivalent except for tier threshold AND no earlier rule would shadow the expanded match set differently.
Statistics: sum build_count, merge sources, keep max_tier from higher rule.

### Idol Rules

CASE A: Exact Duplicate
Condition: Same size AND same modifiers
Result: SAFE - merge into one rule
Reason: Identical identity
Statistics: sum build_count, union sources

CASE B: Same Size + Partial Modifier Overlap
Example:
  Rule 1: Grand Idol + Modifier A + Modifier B
  Rule 2: Grand Idol + Modifier A + Modifier C
Condition: Same size, different modifier sets
Result: UNSAFE - cannot merge
Reason: Modifiers within one idol rule are likely AND conditions. Merging changes boolean semantics unless XML supports OR for modifiers.
XML Requirement: UNCONFIRMED - does Last Epoch idol filtering support modifier OR within one rule?
Recommendation: Do NOT merge until confirmed.

CASE C: Same Modifiers + Different Sizes
Example:
  Rule 1: Grand Idol (1x3) + Modifier X
  Rule 2: Large Idol (1x2) + Modifier X
Condition: Same modifiers, different idol size
Result: CONDITIONAL - only if XML supports multi-size idol matching
XML Requirement: UNCONFIRMED
Recommendation: Do NOT merge until confirmed.

CASE D: Single-Modifier vs Multi-Modifier Idol
Example:
  Rule 1: Grand Idol + Modifier A
  Rule 2: Grand Idol + Modifier A + Modifier B
Condition: Subset relationship in modifiers
Result: UNSAFE - different semantics
Reason: Rule 1 shows idols with only A (or A + anything). Rule 2 requires both A AND B. Merging loses specificity.
Recommendation: Keep separate.

### Unique Rules

CASE A: Exact Duplicate
Condition: Same name AND same unique_id
Result: SAFE - merge into one rule
Reason: Identical unique item
Statistics: sum build_count, union sources

CASE B: Multiple Uniques Same Slot
Example:
  Rule 1: Ravenous Void (Ring)
  Rule 2: Throne of Ambition (Ring)
Condition: Different uniques, same slot
Result: CONDITIONAL - only if XML supports multi-unique-ID lists in one rule
XML Requirement: UNCONFIRMED - can one XML rule match multiple unique item names or IDs?
Recommendation: If XML supports list of unique IDs in one condition, SAFE. Otherwise keep separate.

CASE C: Same Name Different IDs
Example:
  Rule 1: Item Name (id=123)
  Rule 2: Item Name (id=456)
Condition: Same name string, different numeric IDs
Result: Likely data error or different item versions
Recommendation: Keep separate unless confirmed identical by game data.

## Merge Matrix

Category: EXALTED
Identity: same base + same affixes -> SAFE (exact duplicate)
Identity: same base + different affixes -> UNSAFE (partial overlap introduces extra combinations)
Identity: different base + same affixes -> CONDITIONAL (XML unconfirmed)
Identity: same slot different type/sub -> CONDITIONAL (XML unconfirmed)
Tiers: same affix different tiers -> CONDITIONAL (lossless only if action/style/priority/order identical)

Category: IDOL
Identity: same size + same modifiers -> SAFE (exact duplicate)
Identity: same size + different modifiers -> UNSAFE (boolean mismatch)
Identity: different size + same modifiers -> CONDITIONAL (XML unconfirmed)
Subset: single vs multi-modifier -> UNSAFE (semantic difference)

Category: UNIQUE
Identity: same name + same id -> SAFE (exact duplicate)
Identity: different uniques same slot -> CONDITIONAL (XML unconfirmed)
Identity: same name different id -> UNSAFE (likely data issue)

Note: CONDITIONAL means merge ONLY if XML capability is confirmed AND lossless merge definition is satisfied. Default behavior is DO NOT MERGE.

## Lossy Pruning Strategy

Pruning is ONLY applied if Stage 1 output exceeds 140 rules.

### Category Priority Order

Exalted rules have HIGHEST priority (removed last)
Idol rules have MEDIUM priority
Unique rules have LOWEST priority (removed first)

### Within-Category Pruning Order

Unique Pruning Order:
1. Lower score first
2. Lower build_count first
3. Lower source_count first
4. Stable identity ASC (deterministic tie-break)

Idol Pruning Order:
1. Lower score first
2. Lower build_count first
3. Fewer modifiers first (single-modifier idols removed before multi-modifier)
4. Lower source_count first
5. Stable identity ASC

Exalted Pruning Order:
1. Lower score first
2. Lower build_count first
3. Lower source_count first
4. Lower max_tier first (lower-tier bases removed before high-tier)
5. Stable identity ASC

### Pruning Algorithm

Step 1: Sort all rules by pruning priority (inverse of importance)
Step 2: Mark protected rules (cannot be deleted)
Step 3: Remove rules from lowest priority upward until total <= 140
Step 4: If 140 cannot be reached without removing protected rules, FAIL explicitly

## Protected Rules

A rule is PROTECTED if it meets ANY of these conditions:

PROTECTED_SCORE_THRESHOLD = top 20% of scores within category
PROTECTED_BUILD_COUNT_THRESHOLD >= 5 builds
PROTECTED_SOURCE_COUNT_THRESHOLD >= 2 sources (multi-source rules prioritized)
PROTECTED_SEMANTIC_PRIORITY >= 100 AND build_count >= 3 (high-value Exalted with reasonable usage)

Protected rules CANNOT be removed by normal pruning.

If optimizer cannot reach 140 without removing protected rules:
- Log explicit failure
- Return OptimizationResult with success=False
- Provide detailed statistics on why budget is impossible

NOTE: Protected thresholds are POLICY decisions, not game semantics. They represent project-level value judgments about which rules are critical for build coverage. These thresholds can be tuned based on empirical results and user feedback.

## Rule Budget Model

Dynamic budget based on actual input distribution and priorities.

Budget Allocation Algorithm:

1. Stage 1: Perform lossless merge
2. Check total after merge
3. IF total <= 140:
   - No pruning needed
   - Return result
4. IF total > 140:
   - Compute protected rule count per category
   - Compute available budget = 140 - protected_count
   - IF available budget < 0:
	 - FAIL with unable-to-fit error
   - Distribute available budget by semantic priority:
	 - Exalted gets maximum allocation
	 - Idol gets next allocation
	 - Unique gets remainder
   - Apply pruning within each category until budget met

No fixed budget like "90 Exalted + 30 Idol + 20 Unique".
Budget is adaptive based on actual candidate distribution and protection rules.

## Deterministic Behavior

RuleOptimizer must produce identical output for identical input.

Sorting Keys (for pruning order):
1. Category semantic_priority ASC (Unique < Idol < Exalted)
2. Score ASC (lower scores removed first)
3. Build_count ASC
4. Source_count ASC
5. Stable identity from rule fields (NOT Python hash)

Stable identity construction:
- Exalted: (category, slot, item_type, sub_type, sorted affixes tuple)
- Idol: (category, idol_size, sorted modifiers tuple)
- Unique: (category, unique_name, unique_id)

Tie-break must be deterministic and consistent across runs.

## Confirmed Last Epoch Semantics

CONFIRMED 1: Rule evaluation order is top-to-bottom, first-match-wins
Impact: Rule order is part of filter semantics; cannot freely reorder
Source: Confirmed game behavior

CONFIRMED 2: Earlier matching rule shadows later rules for that item
Impact: Optimizer must preserve shadowing behavior when merging
Source: Confirmed game behavior

CONFIRMED 3: Affix conditions can contain multiple selected affixes with required-count
Impact: Multiple affixes are NOT automatically AND-combined; required-count semantics apply
Source: Confirmed advanced filter settings

CONFIRMED 4: 140-rule limit is a hard constraint
Impact: Optimizer must enforce this limit or fail explicitly
Source: Project specification

## Unconfirmed XML Serialization Details

UNCONFIRMED 1: Can one XML rule match multiple itemType values (cross-base merging)?
Impact: Affects Exalted CASE C (same affixes, different bases)
Current assumption: UNKNOWN - do NOT merge until confirmed

UNCONFIRMED 2: Can one XML rule match multiple item types within same slot (cross-type merging)?
Impact: Affects Exalted CASE D (same slot, different type/subType)
Current assumption: UNKNOWN - do NOT merge until confirmed

UNCONFIRMED 3: Can one XML rule specify multiple unique IDs or names with OR semantics?
Impact: Affects Unique CASE B (different uniques, same slot)
Current assumption: UNKNOWN - do NOT merge until confirmed

UNCONFIRMED 4: Can one idol rule match multiple idol sizes?
Impact: Affects Idol CASE C (different size, same modifiers)
Current assumption: UNKNOWN - do NOT merge until confirmed

UNCONFIRMED 5: How are affix tier requirements serialized in XML?
Impact: Affects tier-relaxation merge implementation details
Current assumption: MIN_TIER attribute exists, but structure unconfirmed

UNCONFIRMED 6: How are selected_affixes and required_count serialized in XML?
Impact: Affects whether partial affix overlap can be merged if all combinations are present
Current assumption: Structure unconfirmed - do NOT merge partial overlaps

UNCONFIRMED 7: Does XML support explicit priority/ordering attributes?
Impact: Affects whether rule order must be preserved purely by XML position
Current assumption: Order preserved by XML document position

## Proposed Production Algorithm

RuleOptimizer.optimize(input: RuleBuildResult) -> OptimizationResult

Step 1: Validate input (not empty, has statistics)

Step 2: LOSSLESS MERGE STAGE
  2a. Group rules by category
  2b. For Exalted:
	  - Find exact duplicates (same base_key + same affixes) -> merge
	  - Find tier-relaxation candidates (same base_key + same affixes, different tiers):
		* ONLY merge if action, style, semantic_priority are identical
		* Verify no earlier rule would shadow the expanded match set differently
		* Use lower minimum tier
	  - DO NOT merge partial affix overlaps (CASE B)
	  - DO NOT merge different bases (CASE C) - XML unconfirmed
	  - DO NOT merge different types (CASE D) - XML unconfirmed
  2c. For Idol:
	  - Find exact duplicates (same size + same modifiers) -> merge
	  - DO NOT merge different sizes - XML unconfirmed
	  - DO NOT merge different modifiers - semantic mismatch
  2d. For Unique:
	  - Find exact duplicates (same name + same id) -> merge
	  - DO NOT merge different uniques - XML unconfirmed
  2e. Rebuild rule list with merged rules, preserving top-to-bottom order
  2f. Log merge statistics

Step 3: CHECK RULE COUNT
  IF merged_count <= 140:
	- Return success result
  ELSE:
	- Proceed to Stage 2

Step 4: LOSSY PRUNING STAGE
  4a. Identify protected rules per category
  4b. Compute prunable rules = all rules - protected rules
  4c. IF prunable_count + protected_count <= 140:
	  - Prune exactly (140 - protected_count) rules from prunable set
  4d. ELSE:
	  - Cannot fit within budget -> FAIL
  4e. Sort prunable rules by pruning priority (Unique first, then Idol, then Exalted)
  4f. Within category, sort by score ASC, build_count ASC, source_count ASC, stable identity ASC
  4g. Remove bottom N rules where N = (total - 140)
  4h. Rebuild final rule list

Step 5: VALIDATE OUTPUT
  5a. Ensure exactly <= 140 rules
  5b. Ensure all protected rules present
  5c. Log optimization summary

Step 6: RETURN RESULT
  Return OptimizationResult:
	- rules: optimized FilterRule list
	- original_count
	- final_count
	- merged_count
	- pruned_count
	- success: bool
	- protected_count
	- message: explanation

## Test Plan for Future Implementation

When production RuleOptimizer is implemented, minimum test coverage:

TEST 1: Exact duplicate merge (Exalted)
Input: 2 rules same base + same affixes
Expected: 1 rule, statistics summed

TEST 2: Tier relaxation merge only when action/style identical (Exalted)
Input: 2 rules same base + same affixes, tier 6 and tier 7, both SHOW with same style
Expected: 1 rule with tier 6 (more permissive)

TEST 3: Tier relaxation NOT merged when action differs (Exalted)
Input: 2 rules same base + same affixes, tier 6 SHOW and tier 7 HIDE
Expected: 2 rules (no merge due to different action)

TEST 4: Tier relaxation NOT merged when style differs (Exalted)
Input: 2 rules same base + same affixes, tier 6 and tier 7, different colors
Expected: 2 rules (no merge due to different style)

TEST 5: Partial affix overlap NOT merged (Exalted)
Input: 2 rules same base, affixes partially overlap (A+B vs A+C)
Expected: 2 rules (no merge due to unsafe semantics)

TEST 6: Required-count merge rejected if introduces extra combinations (Exalted)
Input: 2 rules same base (A+B, A+C) - missing B+C
Expected: 2 rules (cannot merge to selected=[A,B,C] required=2 because B+C was not in original)

TEST 7: Exact duplicate merge (Idol)
Input: 2 rules same size + same modifiers
Expected: 1 rule

TEST 8: Exact duplicate merge (Unique)
Input: 2 rules same name + same id
Expected: 1 rule

TEST 9: No pruning when <= 140
Input: 100 rules
Expected: 100 rules output, no pruning applied

TEST 10: Pruning when > 140
Input: 200 rules
Expected: 140 rules output, lowest-value 60 removed

TEST 11: Category priority preservation
Input: 150 rules (50 Exalted, 50 Idol, 50 Unique)
Expected: Uniques pruned first, Idols second, Exalted last

TEST 12: Protected rule survives pruning
Input: 150 rules, 10 protected high-score Exalted
Expected: All 10 protected rules in output, others pruned

TEST 13: Rule order preserved after merge
Input: Rules in specific semantic order
Expected: Output maintains top-to-bottom order, no reordering

TEST 14: Earlier matching rule shadows later rule
Input: 2 rules that match overlapping item set, rule 1 before rule 2
Expected: Optimizer recognizes rule 1 shadows rule 2 for overlap

TEST 15: Lossless merge preserves equivalent match set
Input: 2 duplicate rules
Expected: Merged rule MatchSet == union of original MatchSets

TEST 16: Deterministic result
Input: Same RuleBuildResult twice
Expected: Identical output both times (same rules, same order)

TEST 17: Exactly 140 output
Input: 173 rules
Expected: Exactly 140 rules output

TEST 18: Impossible budget failure
Input: 150 rules, 145 protected
Expected: success=False, explicit error message

TEST 19: Input not mutated
Input: RuleBuildResult with 100 rules
Expected: Original input object unchanged after optimize()

TEST 20: Statistics preserved after merge
Input: 2 duplicate rules with build_count=3 and build_count=5
Expected: Merged rule has build_count=8

TEST 21: Stable identity determinism
Input: Rules with identical score/build_count
Expected: Consistent tie-break order across multiple runs

## Known Unsafe Merges

The following merges are explicitly UNSAFE and must NOT be performed by RuleOptimizer:

UNSAFE 1: Exalted rules with same base but different affix sets (partial overlap)
UNSAFE 2: Idol rules with same size but different modifier sets
UNSAFE 3: Merging single-modifier idol with multi-modifier idol (subset issue)
UNSAFE 4: Unique rules with same name but different IDs (likely data error)
UNSAFE 5: Cross-category merges (Exalted + Idol, etc.)
UNSAFE 6: Merging rules with vastly different scores without proper re-weighting
UNSAFE 7: Merging rules from different slots (semantic mismatch)

## Future Enhancements

After initial RuleOptimizer implementation and XML semantics confirmation:

FUTURE 1: Cross-base merging if XML supports itemType lists
FUTURE 2: Advanced idol modifier OR merging if XML supports it
FUTURE 3: Unique ID list merging if XML supports it
FUTURE 4: Affix-level OR merging if XML allows nested conditions
FUTURE 5: User-configurable protection thresholds
FUTURE 6: Profile-specific optimization (SSF vs Trade)
FUTURE 7: Market-price-aware pruning priority
FUTURE 8: Statistical coverage analysis (percentage of builds covered)

## Implementation Notes

DO NOT implement RuleOptimizer yet. This is a research document only.

Next required step: XML semantics verification
- Inspect actual Last Epoch filter XML examples
- Document confirmed capabilities and limitations
- Update merge matrix based on confirmed XML behavior
- Only then implement production RuleOptimizer

Production implementation should be in:
app/generator/rule_optimizer.py

Tests should be in:
tests/test_rule_optimizer.py

Documentation should reference:
- This strategy document
- XML Generator specification (when created)
- Last Epoch filter XML format documentation
