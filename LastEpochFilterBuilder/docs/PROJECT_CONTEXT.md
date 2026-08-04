# PROJECT_CONTEXT.md

# Last Epoch Smart Loot Filter Generator

## Project Version

1.0

## Language

Python 3.13

## Purpose

Automatic generation of Last Epoch Loot Filter based on S-Tier builds from Maxroll.

---

# 1. Project Overview

## 1.1 Description

Last Epoch Smart Loot Filter Generator is a Python application that analyzes current meta builds from Maxroll and automatically creates an optimized Loot Filter.

The goal of the application is not to analyze all game items.

The goal is:

- find valuable items used in popular S-Tier builds;
- highlight items worth picking up;
- reduce unnecessary loot;
- create a filter that can be imported into Last Epoch.

---

# 2. Main Requirements

The application MUST analyze only S-Tier builds.

Allowed sources:

## Corruption Tier List

https://maxroll.gg/last-epoch/tierlists/corruption-tier-list


## Speed Farming Tier List

https://maxroll.gg/last-epoch/tierlists/speed-farming-tier-list


## Bossing Tier List

https://maxroll.gg/last-epoch/tierlists/bossing-tier-list


The application MUST ignore:

- A Tier
- B Tier
- C Tier
- D Tier

---

# 3. Main Application Logic


Workflow:

START

↓

Download Maxroll tier lists

↓

Find S-Tier builds

↓

Open build pages

↓

Extract:

Items
Idols
Exalted bases
Required affixes

↓

Analyze importance

↓

Create loot filter rules

↓

Optimize rules count

↓

Generate XML filter

↓

END



---

# 4. Item Priority System


Items MUST have priority.


## Priority 1

# Exalted Items


Highest priority.


Reason:

Exalted items are required for Legendary Crafting.


The application should identify:

- item base;
- equipment slot;
- required affixes;
- affix tier if available.


Example:

Helmet

Exalted

Required:

+2 Frost Claw

Intelligence
Critical Strike Chance




Generated rule:

SHOW

Item Type:
Helmet

Rarity:
Exalted

Affixes:

Frost Claw Level



---

# Priority 2

# Idols


The application should identify:


- Idol size;
- Idol type;
- Required modifiers.


Example:

Large Arcane Idol

Modifier:

Fire Damage

Flame Wave Chance



Generated rule:

Large Idol

Modifier:

Fire Damage



---

# Priority 3

# Unique Items


Unique items have lowest priority.


Only uniques used by S-Tier builds should be included.


Example:

Julra's Obsession

Exsanguinous

Ravenous Void


---

# 5. Rule Limit

Last Epoch has a filter limitation.


Maximum:
140 rules


The generated filter MUST NEVER contain more than 140 rules.


---

# 6. Rule Optimization


If generated rules:
<= 140

No optimization needed.


If:
140

Optimizer must reduce rules.


Optimization priority:


1. Combine identical rules.

Example:


Before:
Helmet + Intelligence

Helmet + Intelligence + Ward


After:

Helmet

Intelligence


---

2. Remove duplicate rules.


3. Merge similar affixes.


4. Remove low importance Unique rules.


5. Never remove important Exalted rules.


---

# 7. Technology Stack


## Programming Language

Python 3.13


## Database

SQLite


ORM:

SQLAlchemy 2.0


## HTML Parsing

BeautifulSoup4

lxml


## HTTP Client

requests

httpx


## Configuration

yaml

python-dotenv


## Logging

logging

loguru


## Testing

pytest


---

# 8. Project Structure

last_epoch_filter_generator/

│
├── PROJECT_CONTEXT.md
│
├── main.py
│
├── requirements.txt
│
├── config.yaml
│
│
├── app/
│
│
├── database/
│
│ ├── database.py
│ ├── models.py
│
│
├── parsers/
│
│ ├── maxroll_parser.py
│ ├── build_parser.py
│ ├── item_parser.py
│
│
├── analyzer/
│
│ ├── item_analyzer.py
│ ├── priority_calculator.py
│ ├── rule_optimizer.py
│
│
├── generator/
│
│ └── filter_generator.py
│
│
├── output/
│
│ └── LastEpoch_Filter.xml
│
│
├── logs/
│
└── tests/

---

# 9. Coding Rules


All generated code MUST follow:


## Python Style

PEP8


## Type hints

Required.


Example:

```python
def parse_build(url: str) -> Build:
    pass
```

Documentation

Every class and public function requires docstring.

Example:
class MaxrollParser:
    """
    Parser for extracting S-Tier builds from Maxroll.
    """

Error Handling

Every external operation must handle errors:

Examples:

HTTP request failure;
invalid HTML;
missing data;
database error.


---

# 10. Configuration

All settings must be stored in:
config.yaml

Example:

sources:
  maxroll:
    enabled: true


database:
  path: data/database.sqlite


filter:
  max_rules: 140


parser:
  timeout: 20



---

# 11. Database Requirements

Database:
SQLite

Location:
data/database.sqlite


---

# 12. Database Entities

Build
Stores build information.

Fields:
id
name
class_name
mastery
tier
source_url
created_at
updated_at



Item
Stores item information.

Fields:
id
name
type
slot
rarity


Affix
Stores affixes.

Fields:
id
name
category
tier


Idol
Stores idol information.

Fields:
id
name
size
modifier


FilterRule
Stores generated rules.

Fields:
id
rule_type
condition
priority
enabled



---

# 13. Parser Requirements
Maxroll Parser

Responsibilities:

download tier list pages;
detect S-Tier builds;
collect build URLs.

Output: 
List[Build]


Build Parser

Responsibilities:

Extract:

equipment;
idols;
skills;
required stats.

Output:
BuildDetails

Item Parser

Responsibilities:

Normalize item data.

Example:

Input:
Julra's Obsession

Output:

name:
Julra's Obsession

type:
Unique

slot:
Gloves

# 14. Analyzer System


Analyzer is responsible for converting raw parsed data into valuable loot filter rules.


Main goal:

Determine which items are worth showing to the player.


---

# 15. Item Importance Calculation


Every item receives a score.


Formula:    
Item Score = Build Usage Score + Item Type Priority + Affix Importance + Build Count + Meta Popularity



---

# 16. Build Usage Score


The more S-Tier builds use an item, the higher its priority.


Example:


Item:
Exsanguinous


Used by:
5 S-Tier builds



Score:

High



Item:
Random Unique


Used by:

1 build


Score:

Low



---

# 17. Item Type Priority


Priority values:

Exalted:
100

Idol:
80

Unique:
50

Set:
20



The system must always prefer Exalted items over Unique items.


---

# 18. Affix Analysis


The application must analyze which affixes are important.


Example:


Build requires:

Helmet:

+2 Frost Claw

Intelligence
Critical Strike Chance


The analyzer stores:

Slot:
Helmet

Required Affixes:

Frost Claw Level

Intelligence

Critical Strike Chance


---

# 19. Duplicate Detection


The system must detect duplicates.


Example:


Build A:
Helmet

Intelligence


Build B:
Helmet

Intelligence
Ward


The system should merge:

Helmet

Required:

Intelligence


---

# 20. Rule Optimizer


Responsible for reducing filter rules.


Input:

Generated Rules:

200


Output:

Optimized Rules:

<=140


---

# 21. Rule Optimization Algorithm


Optimization order:


## Step 1

Merge identical rules.


Example:


Before:

Rule 1:

Helmet
Intelligence

Rule 2:

Helmet
Intelligence


After:

Rule:

Helmet
Intelligence


---

## Step 2

Merge rules with common conditions.


Example:


Before:

Helmet
Intelligence

Helmet
Ward


After:

Helmet

Intelligence OR Ward


---

## Step 3

Remove low priority rules.


Remove order:


1. Low popularity Unique items.

2. Items used by only one non-important build.

3. Duplicate Unique rules.


Never remove:


- Exalted crafting bases.
- Important idols.
- Items used by multiple S-Tier builds.


---

# 22. Loot Filter Generator


The generator creates a Last Epoch XML filter file.


Output:

output/

LastEpoch_Smart_Filter.xml


---

# 23. Generated Filter Structure


The XML must contain:

Filter

├── Rules

│
├── Rule 1

│
├── Rule 2

│
└── Rule N


Maximum:

140 rules


---

# 24. Rule Types


Supported rules:


## Show Rule


Used for valuable items.


Example:

SHOW

Unique

Julra's Obsession


---

## Hide Rule


Used to hide unnecessary items.


Example:

HIDE

Normal items


---

## Color Rule


Optional.


Used for highlighting priority.


Example:

Exalted:

Gold color


---

# 25. Rule Priority Colors


Recommended:


## Tier 1

Exalted crafting bases:


Color:

Bright Yellow


Priority:

100



## Tier 2

Idols:


Color:

Purple


Priority:

80



## Tier 3

Unique:


Color:

Orange


Priority:

50



---

# 26. Application Interface


Initial version:

CLI application.


Commands:


---

## Update database


Command:

python main.py update


Function:


- download Maxroll data;
- parse S-Tier builds;
- update database.


---

## Generate filter


Command:

python main.py generate


Function:


- analyze items;
- optimize rules;
- create XML filter.


---

## Full update


Command:

python main.py full-update


Runs:

update

generate


---

# 27. Logging


All operations must be logged.


Location:

logs/application.log


Example:

2026-08-03 12:00

INFO

Found S Tier builds: 35

INFO

Extracted items: 240

INFO

Generated rules: 136

INFO

Filter created successfully


---

# 28. Error Handling


The application must handle:


## Network errors


Example:


Maxroll unavailable.


Action:


- retry request;
- write error to log;
- continue processing.


---

## Parsing errors


Example:


Unknown HTML structure.


Action:


- skip item;
- log problem.


---

## Database errors


Action:


- rollback transaction;
- log error.


---

# 29. Caching System


The application should cache downloaded pages.


Purpose:


- reduce Maxroll requests;
- speed up development;
- prevent unnecessary traffic.


Structure:

data/cache/

maxroll/

builds/

items/


---

# 30. Parser Request Rules


HTTP requests must:


- use timeout;
- use User-Agent;
- handle HTTP errors.


Example:

timeout = 20 seconds


---

# 31. Testing Requirements


Testing framework:

pytest


---

# 32. Unit Tests


Required tests:


## Parser tests


Check:


- S-Tier detection;
- build extraction;
- item extraction.


---

## Analyzer tests


Check:


- item score calculation;
- priority calculation;
- duplicate detection.


---

## Generator tests


Check:


- XML creation;
- rule count <= 140.


---

# 33. Test Example


Example:


```python
def test_filter_rule_limit():

    rules = generate_rules()

    assert len(rules) <= 140

```


---

# 34. Development Phases

The project must be developed sequentially.

Phase 1

Project initialization.

Create:

folder structure;
requirements;
configuration;
logging.
Phase 2

Database.

Create:

SQLAlchemy models;
SQLite initialization.
Phase 3

Maxroll Parser.

Implement:

tier list parser;
S-Tier extraction.
Phase 4

Build Parser.

Implement:

build page parsing;
item extraction.
Phase 5

Analyzer.

Implement:

item scoring;
priority calculation.
Phase 6

Rule Optimizer.

Implement:

duplicate removal;
rule merging;
limit enforcement.
Phase 7

Filter Generator.

Implement:

XML generation;
validation.
Phase 8

Testing.

Add:

unit tests;
integration tests.


---

# 35. GitHub Copilot Development Rules

Before creating any module:

Read PROJECT_CONTEXT.md.
Understand existing architecture.
Do not change existing architecture without approval.
Do not create unnecessary dependencies.
Use existing classes and services.


---

# 36. Copilot Prompt Format

Every development request should follow:
Read PROJECT_CONTEXT.md.


Implement:

[module name]


Requirements:

[list]


Do not:

[list]


Return:

[list]


---

# 37. First Development Order

Copilot must implement in this order:

Project structure.

Configuration system.

Logging.

Database.

Models.

Maxroll parser.

Build parser.

Analyzer.

Optimizer.

Filter generator.

Tests.



---

# 38. Final Project Goal

The finished application must:

automatically analyze S-Tier Last Epoch builds;
identify valuable loot;
create optimized Loot Filter;
never exceed 140 rules;
reduce manual market searching;
help players find items worth selling.