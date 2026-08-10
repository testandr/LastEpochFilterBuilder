# XML Generator Implementation

**Status**: IMPLEMENTED  
**Version**: 1.0  
**Last Updated**: 2025-01-XX

## Overview

The XML Generator is responsible for serializing `OptimizationResult` and `OptimizedRule` objects into valid Last Epoch ItemFilter XML format.

**Module**: `app/generator/xml_generator.py`

## Responsibility

- Convert `OptimizationResult` into Last Epoch XML format
- Map categories (exalted, idol, unique) to XML condition structures
- Assign sequential Order values to rules
- Apply style defaults by category
- Validate rule structure before generation
- Fail explicitly when rules cannot be represented correctly

**Does NOT perform**:
- Rule optimization or pruning (handled by `RuleOptimizer`)
- Priority sorting (handled by `RuleOptimizer`)
- Semantic analysis (handled by `Analyzer`)

## Public API

### generate(result, metadata=None) -> str

Generates Last Epoch ItemFilter XML from an OptimizationResult.

**Parameters**:
- `result`: `OptimizationResult` - The optimization result to serialize
- `metadata`: `Optional[Dict[str, Any]]` - Override filter metadata (name, description, etc.)

**Returns**: XML string with UTF-8 encoding

**Raises**:
- `ValidationError`: OptimizationResult validation failed
- `XMLGenerationError`: Rule cannot be represented correctly
- `MissingIDError`: Required numeric ID is None
- `UnsupportedMixedAffixTierError`: Mixed tier requirements in exalted rule
- `UnsupportedCategoryError`: Unknown rule category

### save(result, path, metadata=None) -> None

Generates XML and saves to file.

**Parameters**:
- `result`: `OptimizationResult` - The optimization result to serialize
- `path`: `Union[str, Path]` - Output file path
- `metadata`: `Optional[Dict[str, Any]]` - Override filter metadata

**Behavior**:
- Creates parent directory if needed
- Writes UTF-8 encoded XML
- Overwrites existing file without backup

## Input

### OptimizationResult

Required fields:
- `rules`: List of `OptimizedRule` objects
- `final_count`: Number of rules
- `success`: Must be True for generation

Validated before serialization.

### OptimizedRule

Supported categories:
- `exalted`: Exalted items with affix requirements
- `idol`: Idols with modifier requirements
- `unique`: Unique items by numeric ID

Category-specific fields:
- **exalted**: `item_types`, `affixes`
- **idol**: `idol_sizes`, `modifiers`
- **unique**: `unique_items`

## Output

### Root Structure

```
<ItemFilter xmlns:xsi="..." xmlns:i="...">
  <name>Last Epoch Smart Loot Filter</name>
  <filterIcon>0</filterIcon>
  <filterIconColor>0</filterIconColor>
  <description>Automatically generated filter</description>
  <lastModifiedInVersion>1.4.7</lastModifiedInVersion>
  <lootFilterVersion>0</lootFilterVersion>
  <rules>
	<!-- Rule elements -->
  </rules>
</ItemFilter>
```

### Metadata Defaults

| Field | Default | Override |
|-------|---------|----------|
| name | "Last Epoch Smart Loot Filter" | metadata["name"] |
| filterIcon | 0 | metadata["filterIcon"] |
| filterIconColor | 0 | metadata["filterIconColor"] |
| description | "Automatically generated..." | metadata["description"] |
| lastModifiedInVersion | "1.4.7" | metadata["lastModifiedInVersion"] |
| lootFilterVersion | 0 | metadata["lootFilterVersion"] |

## Rule Order

Rules are assigned sequential Order values:
- First OptimizedRule → Order 0
- Second → Order 1
- ...
- Nth → Order N-1

**Important**:
- Order is assigned in the sequence rules appear in `OptimizationResult.rules`
- XML Generator does NOT re-sort by score or category
- RuleOptimizer already ensures correct ordering
- XML document serialization follows ascending Order for readability

## Common Rule Fields

Every generated rule includes:

```
<Rule>
  <type>SHOW</type>
  <conditions>...</conditions>
  <recolor>true/false</recolor>
  <color>RRGGBB</color>
  <emphasized>true/false</emphasized>
  <nameOverride></nameOverride>
  <SoundId>0/1</SoundId>
  <MapIconId>0-5</MapIconId>
  <BeamOverride>true/false</BeamOverride>
  <BeamSizeOverride>1-40</BeamSizeOverride>
  <BeamColorOverride>RRGGBB</BeamColorOverride>
  <isEnabled>true</isEnabled>
  <Order>N</Order>
</Rule>
```

All v1 rules use `<type>SHOW</type>`. No HIDE rules generated.

## Style Defaults by Category

### Exalted
- recolor: true
- color: FFA500 (orange)
- emphasized: true
- SoundId: 1
- MapIconId: 3
- BeamOverride: true
- BeamSizeOverride: 25
- BeamColorOverride: FFA500

### Idol
- recolor: true
- color: 9370DB (purple)
- emphasized: false
- SoundId: 0
- MapIconId: 2
- BeamOverride: false
- BeamSizeOverride: 15
- BeamColorOverride: 9370DB

### Unique
- recolor: true
- color: FFD700 (gold)
- emphasized: true
- SoundId: 1
- MapIconId: 5
- BeamOverride: true
- BeamSizeOverride: 30
- BeamColorOverride: FFD700

No user-configurable style system in v1.

## Exalted Rule Generation

### RarityCondition

```
<Condition xsi:type="RarityCondition">
  <rarity>EXALTED</rarity>
</Condition>
```

### SubTypeCondition

Generated from `OptimizedRule.item_types`:

```
<Condition xsi:type="SubTypeCondition">
  <subType>
	<EquipmentType>BODY_ARMOR</EquipmentType>
	<EquipmentType>HELMET</EquipmentType>
	<!-- One element per confirmed mapped item_type -->
  </subType>
</Condition>
```

Uses `equipment_type_mapper.map_equipment_type(item_type, sub_type)`.

**Unsupported item types fail explicitly**:
- item_type 11 (Fist) → `EquipmentTypeMappingError`
- item_type 24 (Crossbow) → `EquipmentTypeMappingError`
- Unknown item_type → `EquipmentTypeMappingError`

These errors propagate as `XMLGenerationError` with rule identification.

### AffixCondition

Generated from `OptimizedRule.affixes`:

```
<Condition xsi:type="AffixCondition">
  <affixes>
	<int>1</int>    <!-- Health numeric ID -->
	<int>49</int>   <!-- Armor numeric ID -->
  </affixes>
  <minOnTheSameItem>2</minOnTheSameItem>
  <advanced>true</advanced>
  <comparsion>MORE_OR_EQUAL</comparsion>
  <comparsionValue>6</comparsionValue>
</Condition>
```

**Important**:
- Uses numeric affix IDs directly from 3-tuple `(affix_id, name, tier)`
- Never performs name → ID lookup
- `minOnTheSameItem` = number of affixes (all required)
- Tier values are already displayed 1-based; no +1 adjustment

### Mixed Tier Limitation

Last Epoch XML `AffixCondition` has ONE shared `comparsionValue` for all selected affixes.

**Cannot represent**:
- Affix A T6+ AND Affix B T7+ (different tier requirements)

**Behavior**:
- If all affixes have same tier: serialize normally
- If multiple different tiers: raise `UnsupportedMixedAffixTierError`

This is intentional correctness-first behavior. No silent fallback to max/min tier.

## Idol Rule Generation

### SubTypeCondition

Generated from `OptimizedRule.idol_sizes`:

```
<Condition xsi:type="SubTypeCondition">
  <subType>
	<EquipmentType>IDOL_2x4</EquipmentType>
	<!-- One element per idol size -->
  </subType>
</Condition>
```

Uses `idol_size_mapper.map_idol_size(size)`.

Supported formats:
- "Grand Idol (2x4)" → IDOL_2x4
- "Large Idol (2x3)" → IDOL_2x3
- etc.

Unknown idol sizes raise `IdolSizeMappingError` → `XMLGenerationError`.

### AffixCondition

Generated from `OptimizedRule.modifiers`:

```
<Condition xsi:type="AffixCondition">
  <affixes>
	<int>301</int>  <!-- Minion Damage numeric ID -->
	<int>302</int>  <!-- Minion Health numeric ID -->
  </affixes>
  <minOnTheSameItem>2</minOnTheSameItem>
  <advanced>false</advanced>
  <comparsion>MORE_OR_EQUAL</comparsion>
  <comparsionValue>1</comparsionValue>
</Condition>
```

**Important**:
- Uses numeric modifier IDs from 3-tuple `(modifier_id, name, tier)`
- Never uses human-readable modifier name as XML identity
- If modifier_id is None: raise `MissingIDError`

## Unique Rule Generation

### UniqueModifiersCondition

Generated from `OptimizedRule.unique_items`:

```
<Condition xsi:type="UniqueModifiersCondition">
  <UniqueIds>
	<UniqueId>
	  <uniqueId>101</uniqueId>
	  <Rolls i:nil="true" />
	</UniqueId>
	<UniqueId>
	  <uniqueId>102</uniqueId>
	  <Rolls i:nil="true" />
	</UniqueId>
  </UniqueIds>
</Condition>
```

**Important**:
- Uses numeric unique_id from 2-tuple `(unique_id, name)`
- Never filters by name
- If unique_id is None: raise `MissingIDError`
- Rolls are always nil (no roll filtering in v1)

Multiple uniques in one `OptimizedRule` serialize within the same `UniqueModifiersCondition`.

## Validation

Before serialization, validates:

1. `OptimizationResult.success` is True
2. `final_count` ≤ 140 (project budget)
3. All rules have supported categories
4. All required numeric IDs present (affix, modifier, unique)
5. No mixed-tier exalted rules
6. All equipment type mappings succeed
7. All idol size mappings succeed
8. Order values unique and sequential

If validation fails:
- Raises `ValidationError` or category-specific error
- No XML file written
- Error includes rule identification for debugging

## Error Handling

### Exception Hierarchy

- `XMLGenerationError` (base)
  - `ValidationError`: Pre-generation validation failed
  - `MissingIDError`: Required numeric ID is None
  - `UnsupportedMixedAffixTierError`: Mixed affix tiers
  - `UnsupportedCategoryError`: Unknown category

Mapper errors propagate as `XMLGenerationError` with context:
- `EquipmentTypeMappingError` → includes item_type, rule index
- `IdolSizeMappingError` → includes idol size, rule index

### Error Messages

Include:
- Rule category
- Rule index in optimization result
- Specific failure reason (missing ID, unsupported type, etc.)
- Relevant values (affix name, item_type, etc.)

Example:
```
Exalted rule at index 0: affix 'Health' t6 has no numeric ID. Cannot generate valid AffixCondition.
```

## Known Limitations

### Unsupported Item Types

Last Epoch XML does not support:
- **item_type 11**: Fist (no XML EquipmentType)
- **item_type 24**: Crossbow (no XML EquipmentType)

These fail explicitly with `EquipmentTypeMappingError`.

**Important**: Do NOT fabricate XML enums for these types.

### Mixed Affix Tiers

Cannot represent rules like:
- Affix A T6+ AND Affix B T7+

Last Epoch XML `AffixCondition` provides one `comparsionValue` shared across all affixes.

Generation fails explicitly with `UnsupportedMixedAffixTierError`.

### Rule Budget

Project automatic generation budget: **140 rules**

- Game supports 200 total
- ~60 reserved for manual user rules
- XML Generator validates but does NOT prune
- RuleOptimizer handles budget before XML generation

### No HIDE Rules

v1 generates only `<type>SHOW</type>` rules.

HIDE rules not implemented.

### No User Style Configuration

Style defaults are hardcoded by category.

No per-rule style overrides or user configuration in v1.

### No Unique Roll Filtering

Unique rules use nil Rolls structure.

No filtering by unique modifier roll ranges.

## Determinism

Same `OptimizationResult` + same `metadata` → identical XML output

- Sequential Order assignment is deterministic
- Frozenset iteration order is stable (sorted internally)
- No timestamp or random data in output

## XML Format

- UTF-8 encoding
- XML declaration: `<?xml version="1.0" encoding="utf-8"?>`
- 2-space indentation
- Namespace declarations on root element
- Follows confirmed Last Epoch XML structure

Semantic correctness prioritized over whitespace equality with real exports.

## Testing

**Test Suite**: `tests/test_xml_generator.py`

Coverage:
- Empty successful result
- Metadata generation
- Sequential Order values
- Preserved optimizer order
- Exalted rarity/subtype/affix mapping
- Same-tier affix serialization
- Mixed-tier explicit failure
- Missing affix ID failure
- Unsupported Fist explicit failure
- Unsupported Crossbow explicit failure
- Idol size mapping
- Idol modifier numeric IDs
- Missing idol modifier ID failure
- Unique numeric IDs
- Multiple unique_items serialization
- Missing unique ID failure
- Unknown category failure
- OptimizationResult success=False rejection
- 140 rule budget rejection
- Deterministic output
- Input immutability
- UTF-8 save behavior
- XML parse validation

**Test Result**: 38 passed, 0 failed (as of implementation completion)

## Integration

### Usage Example

```python
from app.generator.xml_generator import generate, save
from app.generator.rule_models import OptimizationResult

# Generate XML string
result = OptimizationResult(rules=rules, final_count=5, success=True)
xml = generate(result, metadata={"name": "My Filter"})

# Save to file
save(result, "output/my_filter.xml", metadata={"name": "My Filter"})
```

### Pipeline Position

```
Analyzer → RuleBuilder → RuleOptimizer → XML Generator → Last Epoch Import
```

XML Generator is the final serialization step before user import into game.

## Next Steps

Future enhancements (not in v1):
- HIDE rule support
- User-configurable style system
- Manual user-rule injection
- XML post-processing hooks
- Unique roll filtering
- Additional unsupported item type mappings (if Last Epoch adds them)

## References

- `docs/LAST_EPOCH_FILTER_XML_SPECIFICATION.md`: Real XML structure
- `docs/XML_GENERATOR_MAPPING_SPECIFICATION.md`: Mapping rules
- `data/debug/filters/xml_semantics_test.xml`: Real XML fixture
- `app/generator/equipment_type_mapper.py`: Equipment type mapping
- `app/generator/idol_size_mapper.py`: Idol size mapping
