# DATA_MODELS.md

# Last Epoch Smart Loot Filter Generator

## Data Model Documentation

Version: 1.0


---

# 1. Purpose


This document describes all data entities used in the application.


All developers and AI assistants MUST follow these models.


Do not create duplicate models.

Do not create similar objects with different names.


---

# 2. General Data Flow


External Data:

# DATA_MODELS.md

# Last Epoch Smart Loot Filter Generator

## Data Model Documentation

Version: 1.0


---

# 1. Purpose


This document describes all data entities used in the application.


All developers and AI assistants MUST follow these models.


Do not create duplicate models.

Do not create similar objects with different names.


---

# 2. General Data Flow


External Data:



Maxroll Website

    |

    ▼

Parser Models

    |

    ▼

Database Models

    |

    ▼

Analyzer Models

    |

    ▼

Filter Models

    |

    ▼

XML Generator



---

# 3. Base Model Rules


All database entities MUST contain:


```python
id: int

created_at: datetime

updated_at: datetime
```

All models:

must use Python type hints;
must use SQLAlchemy 2.0 style;
must have docstrings;
must have clear relationships.



---

# 4. Build Model
Purpose

Represents an S-Tier Last Epoch build from Maxroll.

Database Entity

Table:

builds
Fields
class Build:
    
    id: int

    name: str

    class_name: str

    mastery: str

    tier: str

    source_url: str

    author: str | None

    popularity_score: int

    created_at: datetime

    updated_at: datetime

Example
{
"name":
"Frost Claw Runemaster",

"class_name":
"Mage",

"mastery":
"Runemaster",

"tier":
"S",

"source_url":
"https://maxroll.gg/..."
}
Relationships

Build HAS MANY:

Items

Idols

Skills

Stats



---

# 5. Item Model
Purpose

Represents an equipment item used by a build.

Database Entity

Table:

items
Fields
class Item:


    id: int


    name: str


    item_type: str


    slot: str


    rarity: str


    is_unique: bool


    is_exalted: bool


    created_at: datetime


    updated_at: datetime

Item Types

Allowed:

Helmet

Body Armor

Gloves

Boots

Weapon

Off-hand

Ring

Amulet

Relic

Idol

Rarity Values

Allowed:

Normal

Magic

Rare

Exalted

Unique

Set
Example
{
"name":
"Julra's Obsession",

"item_type":
"Gloves",

"slot":
"Hands",

"rarity":
"Unique",

"is_unique":
true
}



---

# 6. Affix Model
Purpose

Represents item modifiers.

Database Entity

Table:

affixes
Fields
class Affix:


    id: int


    name: str


    category: str


    tier: int | None


    description: str | None

Examples
+ Intelligence

+ Critical Strike Chance

+ Frost Claw Level

+ Ward Retention




---

# 7. ItemAffix Model
Purpose

Many-to-many relation:

Item ↔ Affix

Fields
class ItemAffix:


    id: int


    item_id: int


    affix_id: int


    value: str


    tier: int

Example

Item:

Helmet

Affixes:

+2 Frost Claw

+ Intelligence




---

# 8. Idol Model
Purpose

Represents idols required by builds.

Database Entity

Table:

idols
Fields
class Idol:


    id: int


    name: str


    size: str


    modifier: str


    rarity: str | None


Example
{
"name":
"Large Arcane Idol",

"size":
"Large",

"modifier":
"Chance to cast Flame Wave"
}



---

# 9. Skill Model
Purpose

Represents skills used by builds.

Fields
class Skill:


    id: int


    name: str


    description: str | None

Examples
Frost Claw

Flame Rush

Runic Invocation




---

# 10. BuildItem Model
Purpose

Relationship:

Build ↔ Item

Fields
class BuildItem:


    id: int


    build_id: int


    item_id: int


    required: bool


    priority: int


Example
Build:

Frost Claw Runemaster


Item:

Exsanguinous


required:

true

priority:

100




---

# 11. BuildIdol Model
Purpose

Relationship:

Build ↔ Idol

Fields
class BuildIdol:


    id: int


    build_id: int


    idol_id: int


    required: bool


    priority: int




---

# 12. BuildSkill Model
Purpose

Relationship:

Build ↔ Skill

Fields
class BuildSkill:


    id: int


    build_id: int


    skill_id: int


    level: int


    specialized: bool




---

# 13. BuildStat Model
Purpose

Stores important build requirements.

Fields
class BuildStat:


    id: int


    build_id: int


    stat_name: str


    value: str


    priority: int

Examples
Intelligence

Critical Strike Chance

Ward

Health




---

# 14. Item Score Model
Purpose

Temporary analyzer object.

Not stored in database.

Python Model
@dataclass

class ItemScore:


    item_id: int


    score: float


    build_count: int


    priority: int


    reasons: list[str]

Example
{
"item":
"Julra's Obsession",

"score":
87.5,

"reasons":
[
"Used by 5 S Tier builds",
"Unique required item"
]
}



---

# 15. FilterRule Model
Purpose

Represents one Last Epoch filter rule.

Python Model
@dataclass

class FilterRule:


    id: int


    rule_type: str


    item_type: str


    rarity: str | None


    affixes: list[str]


    priority: int


    color: str


    enabled: bool




---

# 16. Rule Types

Allowed:

SHOW

HIDE

COLOR



---

# 17. Filter Rule Examples
Exalted Rule
{
"type":
"SHOW",

"rarity":
"Exalted",

"item_type":
"Helmet",

"affixes":
[
"Frost Claw Level"
],

"priority":
100
}
Idol Rule
{
"type":
"SHOW",

"item_type":
"Large Idol",

"priority":
80
}
Unique Rule
{
"type":
"SHOW",

"rarity":
"Unique",

"item_name":
"Julra's Obsession",

"priority":
50
}



---

# 18. Database Relationships

Final relationship diagram:

BUILD

 |

 |----< BUILD_ITEM >---- ITEM

                          |

                          |

                    ITEM_AFFIX

                          |

                        AFFIX



BUILD

 |

 |----< BUILD_IDOL >---- IDOL



BUILD

 |

 |----< BUILD_SKILL >---- SKILL




---

# 19. Model Separation Rules

IMPORTANT:

Database models:

database/models.py

are NOT the same as:

Parser DTO models:

parsers/models.py

Analyzer models:

analyzer/models.py

Generator models:

generator/models.py

Do not mix them.




---

# 20. Serialization Rules

All models should support conversion:

Example:

item.to_dict()

Output:

{
"name":
"Julra's Obsession",

"rarity":
"Unique"
}



---

# 21. Validation Rules

Before saving data:

Validate:

Build:

tier == "S"

Item:

rarity in allowed values

Filter:

rules_count <= 140



---

# 22. AI Development Rules

When creating new classes:

Check this document.
Reuse existing models.
Do not create duplicate entities.
Keep database models separate from business models.
Add type hints.
Add docstrings.