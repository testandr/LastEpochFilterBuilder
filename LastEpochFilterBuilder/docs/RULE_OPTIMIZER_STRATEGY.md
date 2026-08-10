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

PlannerProfileParser - Analyzer - RuleBuilder - RuleOptimizer - XML Generator

RuleOptimizer sits between:
- Upstream: RuleBuilder (provides independent rule candidates)
- Downstream: XML Generator (serializes to Last Epoch XML)

## Two-Stage Processing

Stage 1: Lossless Merge
Goal: Reduce rule count WITHOUT changing which items are shown
Operations: duplicate removal, safe semantic merges

Stage 2: Lossy Pruning
Goal: Enforce 140-rule hard limit by removing lowest-value rules
Only executed: IF Stage 1 output still exceeds 140

## Lossless Merge Strategy

### Exalted Rules

CASE A: Exact Duplicate
Condition: Same base_key AND same affixes
Result: SAFE - merge into one rule
Statistics: sum build_count, union sources

CASE B: Same Base + Partial Affix Overlap
Example: Rule 1 Gloves + Affix A + Affix B vs Rule 2 Gloves + Affix A + Affix C
Result: UNSAFE - cannot merge
Reason: Affixes within one rule are AND conditions. Changes semantics.

CASE C: Same Affixes + Different Bases
Example: Rule 1 Helmet + Affix X vs Rule 2 Body Armour + Affix X
Result: CONDITIONAL - only if XML supports multi-base matching
Recommendation: Do NOT merge until XML capability confirmed.

CASE D: Different Affix Tiers
Example: Rule 1 Affix A T6+ vs Rule 2 Affix A T7+
Result: SAFE with tier relaxation - keep lower minimum tier T6
Reason: T6+ includes T7+, lossless.

### Idol Rules

CASE A: Exact Duplicate
Condition: Same size AND same modifiers
Result: SAFE - merge into one rule

CASE B: Same Size + Partial Modifier Overlap
Example: Grand Idol + Mod A + Mod B vs Grand Idol + Mod A + Mod C
Result: UNSAFE - cannot merge
Reason: Modifiers likely AND. Changes semantics.

CASE C: Same Modifiers + Different Sizes
Result: CONDITIONAL - only if XML supports multi-size matching
Recommendation: Do NOT merge until confirmed.

### Unique Rules

CASE A: Exact Duplicate
Condition: Same name AND same unique_id
Result: SAFE - merge into one rule

CASE B: Multiple Uniques Same Slot
Example: Ring A vs Ring B
Result: CONDITIONAL - only if XML supports multi-unique-ID lists
Recommendation: Do NOT merge until confirmed.

## Merge Matrix

EXALTED
same base + same affixes: SAFE (exact duplicate)
same base + different affixes: UNSAFE (boolean mismatch)
different base + same affixes: CONDITIONAL (XML unconfirmed)
same affix different tiers: SAFE (use lower tier)

IDOL
same size + same modifiers: SAFE (exact duplicate)
same size + different modifiers: UNSAFE (boolean mismatch)
different size + same modifiers: CONDITIONAL (XML unconfirmed)

UNIQUE
same name + same id: SAFE (exact duplicate)
different uniques same slot: CONDITIONAL (XML unconfirmed)

## Lossy Pruning Strategy

Pruning is ONLY applied if Stage 1 output exceeds 140 rules.

Category Priority Order:
Exalted HIGHEST priority (removed last)
Idol MEDIUM priority
Unique LOWEST priority (removed first)

Within-Category Pruning Order:

Unique: lower score, lower build_count, lower source_count first
Idol: lower score, lower build_count, fewer modifiers, lower source_count first
Exalted: lower score, lower build_count, lower source_count, lower max_tier first

All tie-breaks use stable identity (deterministic field-based sort, NOT hash).

## Protected Rules

A rule is PROTECTED if it meets ANY condition:

- Top 20 percent scores within category
- Build_count >= 5
- Source_count >= 2 (multi-source rules)
- Semantic_priority >= 100 AND build_count >= 3

Protected rules CANNOT be removed by normal pruning.

If optimizer cannot reach 140 without removing protected rules:
- Return success=False
- Log explicit failure with statistics

## Rule Budget Model

Dynamic budget based on actual input and priorities.

Algorithm:
1. Perform lossless merge
2. IF total <= 140: done
3. IF total > 140: compute protected count per category
4. Available budget = 140 - protected_count
5. IF available < 0: FAIL
6. Distribute by semantic priority (Exalted max, Idol next, Unique remainder)
7. Apply pruning within each category

No fixed budget. Adaptive based on candidates and protection.

## Deterministic Behavior

RuleOptimizer must produce identical output for identical input.

Sorting Keys for pruning order:
1. Category semantic_priority ASC (Unique < Idol < Exalted)
2. Score ASC (lower removed first)
3. Build_count ASC
4. Source_count ASC
5. Stable identity from fields (NOT Python hash)

Stable identity:
- Exalted: (category, slot, item_type, sub_type, sorted affixes tuple)
- Idol: (category, idol_size, sorted modifiers tuple)
- Unique: (category, unique_name, unique_id)

## Unconfirmed XML Semantics

Must be verified before implementing corresponding merge logic:

UNCONFIRMED 1: Can one XML rule match multiple itemType values?
UNCONFIRMED 2: Are multiple affixes combined with AND or OR?
UNCONFIRMED 3: Can XML specify list of affix IDs with OR?
UNCONFIRMED 4: How does XML handle minimum affix tier?
UNCONFIRMED 5: Can unique rule match multiple IDs or names?
UNCONFIRMED 6: Are idol modifiers AND or OR?
UNCONFIRMED 7: Can idol rule match multiple sizes?
UNCONFIRMED 8: Rule evaluation order (first match or all matches)?
UNCONFIRMED 9: SHOW and HIDE conflict resolution?
UNCONFIRMED 10: Is 140 enforced maximum or guideline?
rithm
Step 1: Validate input
Step 2: LOSSLESS MERGE STAGE
  - Group by category
  - Exalted: merge exact duplicates, merge tier-relaxation cases
  - Idol: merge exact duplicates
  - Unique: merge exact duplicates
  - Rebuild rule list
Step 3: CHECK RULE COUNT
  - IF <= 140: return success
  - ELSE: proceed to Stage 2
Step 4: LOSSY PRUNING STAGE
  - Identify protected rules
  - Compute prunable rules
  - IF cannot fit: FAIL
  - Sort prunable by priority (Unique first, Idol, Exalted)
  - Remove bottom N rules where N = (total - 140)
Step 5: VALIDATE OUTPUT
  - Ensure <= 140
  - Ensure protected present
Step 6: RETURN RESULT

OptimizationResult contains:
- rules (optimized list)
- original_count
- final_count
- merged_count
- pruned_count
- success bool
- protected_count
- message

## Test Plan for Future Implementation

TEST 1: Exact duplicate merge Exalted
TEST 2: Tier relaxation merge Exalted
TEST 3: Partial affix overlap NOT merged
TEST 4: Exact duplicate merge Idol
TEST 5: Exact duplicate merge Unique
TEST 6: No pruning when <= 140
TEST 7: Pruning when > 140
TEST 8: Category priority preservation
TEST 9: Protected rule survives
TEST 10: Deterministic result
TEST 11: Exactly 140 output
TEST 12: Impossible budget failure
TEST 13: Input not mutated
TEST 14: Statistics preserved after merge
TEST 15: Stable identity determinism
rithm  Rebuild rule list
Step 3 CHECK RULE COUNT
  IF <= 140 return success
  ELSE proceed to Stage 2
Step 4 LOSSY PRUNING STAGE
  Identify protected rules
  Compute prunable rules
  IF cannot fit FAIL
  Sort prunable by priority Unique first Idol Exalted
  Remove bottom N rules where N equals total minus 140
Step 5 VALIDATE OUTPUT
  Ensure <= 140
  Ensure protected present
Step 6 RETURN RESULT

OptimizationResult contains rules original_count final_count merged_count pruned_count success protected_count message

## Test Plan for Future Implementation

TEST 1 Exact duplicate merge Exalted
TEST 2 Tier relaxation merge Exalted
TEST 3 Partial affix overlap NOT merged
TEST 4 Exact duplicate merge Idol
TEST 5 Exact duplicate merge Unique
TEST 6 No pruning when <= 140
TEST 7 Pruning when > 140
TEST 8 Category priority preservation
TEST 9 Protected rule survives
TEST 10 Deterministic result
TEST 11 Exactly 140 output
TEST 12 Impossible budget failure
TEST 13 Input not mutated
TEST 14 Statistics preserved after merge
TEST 15 Stable identity determinism

## Known Unsafe Merges

UNSAFE 1 Exalted same base different affix sets
UNSAFE 2 Idol same size different modifier sets
UNSAFE 3 Single-modifier idol with multi-modifier idol
UNSAFE 4 Unique same name different IDs
UNSAFE 5 Cross-category merges

## Implementation Notes

DO NOT implement RuleOptimizer yet. Research document only.
Next step XML semantics verification.
Production file app/generator/rule_optimizer.py
Tests file tests/test_rule_optimizer.py
