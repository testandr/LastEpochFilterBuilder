# PARSER_SPECIFICATION.md

# Last Epoch Smart Loot Filter Generator

## Parser Architecture Specification

Version: 1.0


---

# 1. Purpose


This document describes how external data should be collected and processed.

The main external source:
Maxroll.gg

The parser system is responsible for:


- downloading tier list pages;
- finding S-Tier builds;
- opening build pages;
- extracting items;
- extracting idols;
- extracting required affixes;
- converting raw HTML into application models.


---

# 2. Parser Architecture


Parser layer:

            Maxroll Website

                  |

                  ▼


          HTTP Client Layer

                  |

                  ▼


          HTML Parser Layer

                  |

                  ▼


         Data Extraction Layer

                  |

                  ▼


          Normalized Models

                  |

                  ▼


              Database
              

---

# 3. Parser Components


The parser system contains:

app/parsers/

├── maxroll_parser.py

├── build_parser.py

├── item_parser.py

├── idol_parser.py

├── affix_parser.py

└── parser_models.py


---

# 4. Parser Rules


All parsers MUST:


- be independent;
- not contain database logic;
- not contain analyzer logic;
- return structured objects;
- use logging;
- handle missing data.


Incorrect:

Parser

↓

Database insert


Correct:

Parser

↓

Model

↓

Service

↓

Database


---

# 5. HTTP Client Specification


Location:

app/utils/http_client.py


Class:


```python
HttpClient
```

# 6. HTTP Client Requirements

The client MUST support:

Timeout

Default:

20 seconds

Configurable through:

config.yaml
Headers

Every request should include:

User-Agent

Accept-Language

Accept

Example:

User-Agent:

Mozilla/5.0
Retry System

When request fails:

Retry:

Attempt 1

↓

wait

↓

Attempt 2

↓

wait

↓

Attempt 3


After 3 failures:

log error;
return failed result.

# 7. Cache System

The parser MUST support caching.

Purpose:

reduce requests;
speed up development;
allow offline testing.

Cache location:

data/cache/

Structure:

data/cache/


├── tierlists/

├── builds/

└── items/

8. Maxroll Sources

The parser uses only:

Corruption Tier List
https://maxroll.gg/last-epoch/tierlists/corruption-tier-list
Speed Farming Tier List
https://maxroll.gg/last-epoch/tierlists/speed-farming-tier-list
Bossing Tier List
https://maxroll.gg/last-epoch/tierlists/bossing-tier-list

# 9. Maxroll Tier List Parser

File:

maxroll_parser.py

Class:

class MaxrollParser:
    pass

# 10. MaxrollParser Responsibilities

The parser MUST:

Download tier list page.
Find build categories.
Identify tier labels.
Extract only S Tier builds.
Return build URLs.

# 11. MaxrollParser Interface

Example:

class MaxrollParser:


    def parse_tier_list(
        self,
        url: str
    ) -> list[BuildSummary]:
        pass

# 12. BuildSummary Model

Temporary parser object.

Location:

parser_models.py

Example:

@dataclass
class BuildSummary:


    name: str

    tier: str

    class_name: str

    mastery: str

    url: str

# 13. S-Tier Filtering Logic

IMPORTANT:

Only:

tier == "S"

is allowed.

Example:

Input:

S

A

B

C

Output:

S only


# 14. Duplicate Build Handling

Different tier lists may contain the same build.

Example:

Frost Claw Runemaster


appears in:


Corruption

Speed Farming

Bossing

The parser MUST merge them.

Result:

Build:


Frost Claw Runemaster


Sources:


- Corruption

- Speed Farming

- Bossing


# 15. Build Parser

File:

build_parser.py

Class:

BuildParser

Purpose:

Extract detailed information from individual build pages.


# 16. Build Parser Input

Input:

Build URL

Example:

https://maxroll.gg/last-epoch/build-guides/...


# 17. Build Parser Output

Output:

BuildDetails

Contains:

Build information

+

Equipment

+

Idols

+

Skills

+

Required stats


# 18. BuildDetails Model

Example:

@dataclass
class BuildDetails:


    name: str

    class_name: str

    mastery: str

    items: list[Item]

    idols: list[Idol]

    skills: list[Skill]

    stats: list[BuildStat]


# 19. Build Page Extraction

The parser should search for:

Equipment section

Possible names:

Equipment

Gear

Items

Recommended Gear

Extract:

item name;
rarity;
slot.
Idols section

Possible names:

Idols

Idol Setup

Idol Planner

Extract:

idol size;
modifiers.
Skills section

Possible names:

Skills

Abilities

Skill Tree

Extract:

skill name;
specialization.
Stats section

Possible names:

Stats

Important Stats

Required Stats

Extract:

stat name;
priority.

# 20. Missing Data Rules

If section does not exist:

Example:

No idols:

Action:

Return empty list

Do NOT:

crash application;
stop parser.

Log:

WARNING:

No idols found for build X

21. Parser Logging

Every parser action must log:

Example:

INFO:

Parsing build:

Frost Claw Runemaster


INFO:

Found items:

12


WARNING:

No idols section found


ERROR:

Failed loading page

# 22. Item Parser Specification


File:



app/parsers/item_parser.py



Class:


```python
class ItemParser:
    pass
```

# 23. Item Parser Purpose

The Item Parser converts raw item information from build pages into normalized Item objects.

It must identify:

item name;
item type;
equipment slot;
rarity;
unique/exalted status;
required affixes.

# 24. Supported Item Types

The parser should support:

Weapon

Off-hand

Helmet

Body Armor

Gloves

Boots

Belt

Ring

Amulet

Relic

Idol

Unknown types should be stored as:

Unknown

and logged.

# 25. Item Rarity Detection

Supported rarities:

Normal

Magic

Rare

Exalted

Unique

Set

Detection examples:

Exalted:

Exalted Helmet

Unique:

Unique Gloves

# 26. Exalted Item Extraction

Exalted items are the highest priority.

The parser MUST extract:

Item base

Slot

Affixes

Affix tiers if available

Example:

Input:

Exalted Solarum Bracers

+2 Frost Claw

+ Intelligence

+ Critical Strike Chance

Output:

{
"name":
"Solarum Bracers",

"rarity":
"Exalted",

"affixes":
[
"Frost Claw Level",
"Intelligence",
"Critical Strike Chance"
]
}

# 27. Exalted Base Logic

Important:

The application does NOT need every Exalted item from the game.

It needs only Exalted bases required by S-Tier builds.

Example:

Good:

Exalted Helmet

required for Frost Claw Runemaster

Ignore:

Random Exalted Sword

not used by analyzed builds

# 28. Affix Parser

File:

app/parsers/affix_parser.py

Class:

class AffixParser:
    pass

# 29. Affix Extraction

The parser must normalize affixes.

Examples:

Different formats:

+2 Frost Claw

Frost Claw +2

Frost Claw Level: 2

Must become:

Frost Claw Level

# 30. Affix Categories

Supported categories:

Damage

Defense

Skill Level

Critical

Resistance

Health

Ward

Mana

Utility

# 31. Idol Parser

File:

app/parsers/idol_parser.py

Class:

class IdolParser:
    pass

# 32. Idol Extraction

The parser must extract:

Idol size

Idol type

Modifiers

Example:

Input:

Large Arcane Idol

Chance to cast Flame Wave

Fire Damage

Output:

{
"size":
"Large",

"type":
"Arcane",

"modifiers":
[
"Chance to cast Flame Wave",
"Fire Damage"
]
}

# 33. Idol Priority

Idols should receive priority based on:

Number of builds using them.
Number of S-Tier builds using modifier.
Modifier rarity.

Example:

High priority:

Large Idol

used by 8 S-Tier builds

Low priority:

Small Idol

used by 1 build

# 34. Parser Normalization Layer

All parser output must pass through normalization.

Location:

app/parsers/normalizer.py

# 35. Normalization Rules

Examples:

Before:

Mage Runemaster

After:

class_name:

Mage


mastery:

Runemaster

Before:

Exalted Helm

After:

slot:

Helmet

rarity:

Exalted

# 36. Parser Failure Protection

Website structure may change.

The parser must NOT assume fixed HTML positions.

Bad:

element = soup.find_all()[10]

Good:

find_by_text(
"Equipment"
)

# 37. Selector Strategy

Priority:

First:

Semantic search:

section title

heading text

labels
Second:

CSS selectors.

Third:

Fallback parsing.

# 38. Parser Fallback System

Example:

Primary selector:

div.equipment-section

Failed.

Fallback:

search text:

Equipment

Failed.

Action:

log warning

return empty result

# 39. Parser Cache Strategy

Every successfully downloaded page should be cached.

Example:

data/cache/builds/

File name:

hash_of_url.html

Before requesting:

Check cache.

# 40. Parser Rate Limiting

The application should avoid aggressive requests.

Requirements:

Minimum delay:

1 second

between requests.

Configurable:

parser:

request_delay: 1

# 41. Offline Development Mode

The parser must support offline mode.

Configuration:

parser:

offline_mode: true

When enabled:

Use:

data/cache/

instead of website.

# 42. Parser Data Validation

Before returning data:

Validate:

Build:

name exists

tier exists

url exists

Item:

name exists

rarity valid

Idol:

size exists

modifier exists

# 43. Parser Result Objects

Parser layer should return DTO objects.

Location:

app/parsers/parser_models.py

Contains:

BuildSummary

BuildDetails

ParsedItem

ParsedAffix

ParsedIdol

# 44. ParsedItem DTO

Example:

@dataclass
class ParsedItem:


    name: str

    rarity: str

    slot: str

    item_type: str

    affixes: list[str]

# 45. ParsedIdol DTO

Example:

@dataclass
class ParsedIdol:


    name: str

    size: str

    modifiers: list[str]


# 46. Parser Testing Strategy

All parsers must have unit tests.

Location:

tests/parsers/

Structure:

tests/

 └── parsers/

      ├── test_maxroll_parser.py

      ├── test_build_parser.py

      ├── test_item_parser.py

      └── test_idol_parser.py

# 47. Mock HTML Testing

Do not test only against live website.

Create:

tests/data/html/

Example:

tier_list.html

build_page.html

item_page.html

Tests should use local HTML.


# 48. Parser Test Examples
S-Tier Detection

Input:

HTML with S,A,B tiers

Expected:

Only S returned
Item Parsing

Input:

Exalted Helmet

+ Intelligence

Expected:

{
"rarity":
"Exalted",

"affix":
"Intelligence"
}
Idol Parsing

Input:

Large Idol

Fire Damage

Expected:

size:

Large

# 49. Live Parser Validation

Create optional command:

python main.py test-parser

Purpose:

check Maxroll availability;
download sample page;
validate selectors.
50. Parser Development Rules for AI

When implementing parsers:

Never hardcode HTML indexes.
Always add logging.
Always handle missing data.
Always create tests.
Keep parser independent from database.
Return DTO objects.
Never put scoring logic into parser.