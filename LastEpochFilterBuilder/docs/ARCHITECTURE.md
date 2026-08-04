# ARCHITECTURE.md

# Last Epoch Smart Loot Filter Generator

## Architecture Documentation

Version: 1.0

---

# 1. General Architecture


The application follows a layered architecture.


Main layers:

┌─────────────────────────────┐
│ User Interface │
│ CLI Layer │
└──────────────┬──────────────┘
│
▼
┌─────────────────────────────┐
│ Application Layer │
│ Services │
└──────────────┬──────────────┘
│
▼
┌─────────────────────────────┐
│ Business Layer │
│ Analyzer Engine │
└──────────────┬──────────────┘
│
▼
┌─────────────────────────────┐
│ Data Layer │
│ Database + Parsers │
└─────────────────────────────┘



---

# 2. Component Overview


## 2.1 CLI Layer


Location:



main.py



Responsibilities:


- receive user commands;
- start application workflows;
- display results.


Available commands:



update

generate

full-update



Example:



python main.py update



Flow:



CLI

↓

UpdateService

↓

Parser Layer

↓

Database



---

# 3. Application Layer


Location:



app/services/



Contains:



update_service.py

generation_service.py



---

# 3.1 Update Service


Class:



UpdateService



Purpose:


Collect fresh information from Maxroll.


Responsibilities:


1. Start parsers.
2. Download tier lists.
3. Extract S-Tier builds.
4. Parse build pages.
5. Save results.


Flow:



UpdateService

    |
    |
    ▼

MaxrollParser

    |
    |
    ▼

BuildParser

    |
    |
    ▼

Database



---

# 3.2 Generation Service


Class:



GenerationService



Purpose:


Create final loot filter.


Responsibilities:


1. Load database information.
2. Analyze items.
3. Calculate priorities.
4. Create rules.
5. Optimize rules.
6. Generate XML.


Flow:



GenerationService

    |

    ▼

ItemAnalyzer

    |

    ▼

PriorityCalculator

    |

    ▼

RuleOptimizer

    |

    ▼

FilterGenerator

    |

    ▼

XML File



---

# 4. Parser Layer


Location:



app/parsers/



Purpose:


Convert external website data into application objects.


---

# 4.1 Maxroll Parser


File:



maxroll_parser.py



Class:



MaxrollParser



Responsibilities:


Input:



Maxroll tier list URLs



Output:



List[Build]



Example:


Input:



Corruption Tier List



Output:



[
{
name:
"Frost Claw Runemaster",

tier:
"S"
}
]



---

# 4.2 Build Parser


File:



build_parser.py



Class:



BuildParser



Responsibilities:


Extract:


- equipment;
- idols;
- skills;
- required stats.


Input:



Build URL



Output:



BuildDetails



---

# 4.3 Item Parser


File:



item_parser.py



Class:



ItemParser



Responsibilities:


Normalize items.


Example:


Raw:



Julra's Obsession
Unique Gloves



Converted:



Item(

name="Julra's Obsession",

rarity="Unique",

slot="Gloves"

)



---

# 5. Business Layer


Location:



app/analyzer/



This is the core of the application.


---

# 5.1 Item Analyzer


File:



item_analyzer.py



Class:



ItemAnalyzer



Purpose:


Determine item value.


Input:



Items from builds



Output:



ItemScore



Example:



Julra's Obsession

Score:

85



Factors:



Build count

Item type

Affixes

Popularity

Tier



---

# 5.2 Priority Calculator


File:



priority_calculator.py



Class:



PriorityCalculator



Converts item score into filter priority.


Priority:



Exalted:

100

Idol:

80

Unique:

50



Example:


Input:



Exalted Helmet



Output:



Priority:

100



---

# 5.3 Rule Optimizer


File:



rule_optimizer.py



Class:



RuleOptimizer



Purpose:


Keep filter below 140 rules.


Input:



200 rules



Output:



135 rules



Algorithm:



Remove duplicates

↓

Merge similar conditions

↓

Remove lowest priority rules

↓

Validate count



---

# 6. Generator Layer


Location:



app/generator/



---

# 6.1 Filter Generator


File:



filter_generator.py



Class:



FilterGenerator



Purpose:


Convert internal rules into Last Epoch XML format.


Input:



List[FilterRule]



Output:



LastEpoch_Smart_Filter.xml



---

# 7. Database Architecture


Location:



app/database/



Database:



SQLite



File:



data/database.sqlite



ORM:



SQLAlchemy 2.0



---

# 8. Data Flow


Full application flow:


             USER

              |

              ▼


          main.py


              |

              ▼


    UpdateService


              |

              ▼


      Maxroll Parser


              |

              ▼


      Build Parser


              |

              ▼


         Database


              |

              ▼


   GenerationService


              |

              ▼


      Item Analyzer


              |

              ▼


    Rule Optimizer


              |

              ▼


   Filter Generator


              |

              ▼


   LastEpoch XML Filter


---

# 9. Object Communication


## Build Object


Created by:



BuildParser



Used by:



Database

Analyzer



Contains:



name

class

mastery

items

idols

skills



---

## Item Object


Created by:



ItemParser



Used by:



Analyzer

Generator



Contains:



name

type

slot

rarity

affixes



---

## FilterRule Object


Created by:



Analyzer



Used by:



Optimizer

Generator



Contains:



type

condition

priority

color



---

# 10. Dependency Rules


IMPORTANT.


Modules may depend only in one direction.


Correct:



Parser

↓

Database

↓

Analyzer

↓

Generator



Incorrect:



Generator

↓

Parser



The generator must never know about Maxroll.


---

# 11. Error Handling Architecture


Errors should flow upward.


Example:



HTTP Error

↓

Parser Exception

↓

Service catches error

↓

Logger records

↓

Application continues



---

# 12. Logging Architecture


All layers use:



app.utils.logger



Example:


```python
logger.info(
"Parsed 25 S Tier builds"
)
```




---

# 13. Future Expansion

Architecture should allow adding:

Additional Sources

Example:

Build Planner

Community Builds

Reddit Builds

without changing:

Analyzer

Generator
GUI

Possible future:

PySide6 Interface

Existing services must work without GUI.




---

# 14. Development Rule for AI

When creating new code:

Check ARCHITECTURE.md.
Place code in correct layer.
Do not mix responsibilities.
Do not put parsing logic into analyzer.
Do not put database queries into generator.
Keep classes small.
Prefer reusable services.