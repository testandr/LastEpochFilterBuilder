# FILTER_GENERATION_SPECIFICATION.md

# Last Epoch Smart Loot Filter Generator

## Filter Generation Architecture Specification

Version: 1.0


---

# 1. Purpose


This document describes how analyzed build data is converted into a Last Epoch Loot Filter.


The Filter Generation System is responsible for:


- creating loot filter rules;
- assigning priorities;
- optimizing rule count;
- generating XML;
- validating the final filter.


---

# 2. Main Goal


Create a filter that highlights items worth keeping or selling.


Priority:

1. Exalted crafting items
2. Idols
3. Unique items
4. Other valuable items


The generated filter must always respect:

Maximum rules:

140


---

# 3. Generation Workflow


Full generation process:

Database

|

▼

Item Analyzer

|

▼

Priority Calculator

|

▼

Rule Builder

|

▼

Rule Optimizer

|

▼

Filter Validator

|

▼

XML Generator

|

▼

LastEpoch_Smart_Filter.xml


---

# 4. Generator Components


Location:

app/generator/


Structure:

generator/

├── filter_generator.py

├── rule_builder.py

├── rule_optimizer.py

├── xml_writer.py

├── validators.py

└── generator_models.py


---

# 5. Generator Responsibilities


The generator MUST:


- receive analyzed data;
- create rules;
- sort rules by importance;
- optimize rules;
- generate XML;
- validate result.


The generator MUST NOT:


- parse websites;
- access Maxroll;
- calculate build popularity.


---

# 6. Filter Rule Architecture


Each rule represents one game filter condition.


Model:


```python
@dataclass
class FilterRule:


    rule_type: str


    item_type: str | None


    rarity: str | None


    item_name: str | None


    affixes: list[str]


    priority: int


    color: str


    enabled: bool

```
---

# 7. Rule Types

Supported:

SHOW

Highlights valuable items.

Example:
Show Exalted Helmet with Intelligence

COLOR

Changes visual appearance.

Example:
Show Unique item with orange color

HIDE

Removes unwanted loot.

Example: 
Hide Normal items


---

# 8. Item Priority System

Priority is mandatory.

Every rule receives a priority value.

Priority Levels
Tier 1

Exalted crafting items
Priority:
100

Color:
Bright Yellow

Tier 2

Idols

Priority:

80

Color:

Purple
Tier 3

Unique items

Priority:

50

Color:

Orange


---

# 9. Exalted Rule Generation

Exalted items have highest importance.

The generator should create rules based on:

equipment slot;
item base;
required affixes.

Example:

Input:

Build:

Frost Claw Runemaster


Required:

Helmet

Frost Claw Level

Intelligence

Output:

SHOW


Rarity:

Exalted


Slot:

Helmet


Affixes:

Frost Claw Level

Intelligence

Priority:

100


---

# 10. Exalted Rule Merging

Different builds may require similar bases.

Example:

Build A:

Helmet

Intelligence

Build B:

Helmet

Intelligence

Ward

Before:

Rule 1

Rule 2

After:

Rule:


Helmet

Exalted

Intelligence


---

# 11. Idol Rule Generation

Idols are second priority.

Rule should include:

idol size;
modifiers.

Example:

Input:

Large Arcane Idol

Fire Damage

Output:

SHOW


Type:

Large Idol


Modifier:

Fire Damage


Priority:

80


---

# 12. Unique Rule Generation

Unique items have lowest priority.

Only include:

Unique items from S-Tier builds;
commonly used items.

Example:

Input:

Julra's Obsession

Output:

SHOW


Unique:

Julra's Obsession


Priority:

50


---

# 13. Rule Sorting

Before optimization:

Rules must be sorted:

Exalted

↓

Idols

↓

Unique

↓

Other

Example:

Rule 1:

Exalted Helmet


Rule 2:

Large Idol


Rule 3:

Unique Gloves


---

# 14. Rule Builder

File:

rule_builder.py

Class:

class RuleBuilder:
    pass

Responsibilities:

Convert analyzed items into FilterRule objects.

Methods:

create_exalted_rule()

create_idol_rule()

create_unique_rule()

create_hide_rule()


---

# 15. Rule Builder Example

Input:

{
"type":
"Exalted",

"slot":
"Helmet",

"affixes":
[
"Intelligence"
]
}

Output:

{
"rule_type":
"SHOW",

"rarity":
"Exalted",

"priority":
100
}


---

# 16. Hide Rules

The filter should also hide unnecessary items.

Default hide candidates:

Normal items

Magic items

Rare items

Unused uniques

Unused bases

Important:

Hide rules should be generated only after valuable rules.


---

# 17. Rule Count Validation

After generation:

Check:

len(rules) <= 140

If:

rules <= 140

Continue.

If:

rules > 140

# 18. Rule Optimizer Specification


File:
app/generator/rule_optimizer.py

Class:


```python
class RuleOptimizer:
    pass
```



---

# 19. Optimizer Purpose

The optimizer guarantees that the generated filter does not exceed Last Epoch limitations.

Maximum:

140 rules

Input:

List[FilterRule]

Output:

Optimized List[FilterRule]


---

# 20. Optimization Strategy

Optimization must happen in stages.

Order is important.

Stage 1

↓

Remove exact duplicates


Stage 2

↓

Merge similar rules


Stage 3

↓

Remove low priority rules


Stage 4

↓

Validate final count



---

# 21. Stage 1 - Duplicate Removal

Example:

Before:

Rule 1:

SHOW

Exalted Helmet

Intelligence



Rule 2:

SHOW

Exalted Helmet

Intelligence


After:

Rule:

SHOW

Exalted Helmet

Intelligence



---

# 22. Stage 2 - Similar Rule Merging

Rules with the same:

item type;
rarity;
slot;

should be merged.

Example:

Before:

Rule 1:

Exalted Helmet

Intelligence


Rule 2:

Exalted Helmet

Ward


Rule 3:

Exalted Helmet

Health


After:

Exalted Helmet


Required Affixes:


Intelligence

Ward

Health



---

# 23. Stage 3 - Priority Based Removal

If rules are still above 140:

Remove in this order:

First:

Unused Unique items.

Priority:

50
Second:

Single-build Unique items.

Third:

Low popularity idols.

Never remove:
Priority >= 100

Exalted crafting rules

Priority >= 80

Important idols



---

# 24. Rule Compression

The optimizer should try to reduce rules by grouping.

Example:

Before:

Rule 1:

Helmet

Intelligence


Rule 2:

Helmet

Critical Chance


Rule 3:

Helmet

Ward


After:

Helmet


Exalted


Any:


Intelligence

Critical Chance

Ward



---

# 25. Optimization Result

The optimizer must return:

OptimizationResult

Model:

@dataclass
class OptimizationResult:


    original_count: int


    final_count: int


    removed_rules: int


    merged_rules: int


    success: bool



---

# 26. Filter Validation

File:

validators.py

Class:

FilterValidator


---

# 27. Validation Rules

Before saving:

The validator MUST check:

Rule count
rules_count <= 140
Required fields

Every rule must have:

rule_type

priority

enabled
Priority validation

Allowed:

0-100
XML validation

Generated XML must be:

valid XML;
readable;
importable.


---

# 28. XML Generator

File:

xml_writer.py

Class:

XmlWriter


---

# 29. XML Generation Purpose

Convert internal FilterRule objects into Last Epoch compatible XML.

Input:

List[FilterRule]

Output:

LastEpoch_Smart_Filter.xml


---

# 30. XML Generation Rules

The generator must:

preserve rule order;
preserve priority;
escape special characters;
create valid XML structure.


---

# 31. XML File Metadata

Generated file should contain:

Filter Name:

Last Epoch Smart Filter


Generated:

timestamp


Rules:

number of rules



---

# 32. Output Location

Default:

output/LastEpoch_Smart_Filter.xml


---

# 33. XML Generation Example

Internal rule:

{
"type":
"SHOW",

"rarity":
"Exalted",

"slot":
"Helmet",

"priority":
100
}

Generated XML:

<Rule>

<Type>SHOW</Type>

<Rarity>Exalted</Rarity>

<Slot>Helmet</Slot>

<Priority>100</Priority>

</Rule>


---

# 34. Filter Import Safety

Before generating final file:

Create backup:

output/backups/

Example:

LastEpoch_Filter_2026_08_03.xml


---

# 35. Generation Report

After creating filter:

Generate:

output/filter_report.json

Example:

{
"builds_analyzed":35,

"exalted_rules":75,

"idol_rules":28,

"unique_rules":20,

"total_rules":123
}


---

# 36. CLI Integration

Generation command:

python main.py generate

Process:

Load database

↓

Analyze items

↓

Create rules

↓

Optimize

↓

Validate

↓

Generate XML

↓

Create report



---

# 37. Full Update Command

Command:

python main.py full-update

Process:

Update Maxroll data

↓

Refresh database

↓

Generate filter

↓

Create report



---

# 38. Testing Requirements

Location:

tests/generator/

Structure:

tests/


generator/


├── test_rule_builder.py

├── test_optimizer.py

├── test_xml_writer.py

└── test_validator.py



---

# 39. Rule Builder Tests

Test:

Input:

Exalted Helmet

Intelligence

Expected:

SHOW rule

Priority 100



---

# 40. Optimizer Tests

Example:

Input:

200 rules

Expected:

<=140 rules


---

# 41. XML Writer Tests

Check:

Generated XML:

exists;
opens correctly;
contains rules.


---

# 42. Integration Test

Scenario:

Sample Database


↓

Analyzer


↓

Generator


↓

XML



Validate:

File created

Rules <=140

XML valid



---

# 43. Sample Test Data

Location:

tests/data/filter_samples/

Examples:

exalted_items.json

idols.json

unique_items.json



---

# 44. AI Implementation Rules

When implementing filter generation:

Never exceed 140 rules.
Never remove Exalted crafting rules.
Always optimize before XML generation.
Always validate output.
Keep generator independent from parsers.
Keep XML generation separate from rule creation.
Add tests for every component.


---

# 45. Future Extensions

Architecture should allow:

Multiple Filters

Example:

Market Filter

SSF Filter

Endgame Filter

User Profiles

Example:

Player chooses:

Falconer

Mage

Sentinel


Generator creates personalized filter.

Price Integration

Future:

Trade API

Market prices

Automatic value scoring