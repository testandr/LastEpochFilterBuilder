# RuleBuilder Specification

## Overview
RuleBuilder is a pure conversion layer that transforms Analyzer output into intermediate FilterRule objects.

## Responsibility
- Convert each candidate to one FilterRule
- Preserve Analyzer scores and statistics
- Maintain deterministic ordering
- Detect 140-rule limit but NOT enforce it

## Architecture
PlannerProfileParser - Analyzer - RuleBuilder - RuleOptimizer - XML Generator

## Conversion
ONE ExaltedCandidate produces ONE FilterRule (all affixes together)
ONE IdolCandidate produces ONE FilterRule (all modifiers together)
ONE UniqueCandidate produces ONE FilterRule

## Ordering
1. Semantic priority DESC (Exalted 100, Idol 70, Unique 40)
2. Score DESC
3. Stable identity ASC (deterministic field-based, NOT hash)

## 140 Limit
RuleBuilder does NOT prune, delete, or merge rules.
If 173 candidates exist, all 173 become rules.
Sets exceeds_limit=True and logs warning.
Optimization is RuleOptimizer job (future stage).

## Immutability
AnalysisResult is not mutated.
Source sets are copied when creating FilterRule objects.
