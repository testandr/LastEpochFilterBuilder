# COPILOT_TASKS.md

# Last Epoch Smart Loot Filter Generator

## GitHub Copilot Development Tasks

Version: 2.0


---

# 1. Purpose


This document defines the development roadmap for GitHub Copilot.


The project MUST be implemented step by step.


Do NOT generate the whole project at once.


Each task must be completed, tested, and validated before moving to the next task.


---

# 2. Important Instructions For GitHub Copilot


Before starting any task:


Read:



PROJECT_CONTEXT.md

ARCHITECTURE.md

DATA_MODELS.md

PARSER_SPECIFICATION.md

FILTER_GENERATION_SPECIFICATION.md

TESTING_STRATEGY.md

DEVELOPMENT_SETUP.md



Confirm understanding of:


- project goal;
- architecture;
- data models;
- limitations.


---

# 3. Development Rules


GitHub Copilot MUST:


1. Implement only the current task.

2. Not create future functionality.

3. Follow existing architecture.

4. Reuse existing models.

5. Write tests together with code.

6. Add type hints.

7. Add documentation.

8. Keep modules separated.


---

# 4. Forbidden Actions


Do NOT:


- create duplicate classes;
- mix parser and database logic;
- put business logic into models;
- skip tests;
- ignore the 140 rule limit;
- hardcode HTML indexes;
- remove tests to fix failures.


---

# 5. Development Phases



Phase 1

Project foundation

Phase 2

Database layer

Phase 3

Parser system

Phase 4

Data analyzer

Phase 5

Filter generation

Phase 6

CLI application

Phase 7

Integration testing



---

# PHASE 1 - PROJECT FOUNDATION


---

# TASK-001: Create Project Structure


## Goal


Create initial application structure.


## Files


Create:



app/

database/

parsers/

analyzer/

generator/

config/

data/

tests/

output/

main.py



## Requirements


- Add Python packages.
- Add __init__.py files.
- Prepare clean architecture.


## Tests


Verify:


- project imports;
- modules load correctly.


## Do not


Do not implement business logic.


---

# TASK-002: Setup Configuration System


## Goal


Create application configuration.


## Files


Create:



config/settings.py

.env

config.yaml



## Requirements


Support:



DATABASE_URL

MAX_FILTER_RULES

OFFLINE_MODE

DEBUG



## Tests


Verify:


- configuration loads;
- default values exist.


---

# TASK-003: Setup Logging


## Goal


Create centralized logging.


## Files


Create:



app/core/logger.py



## Requirements


Support:



DEBUG

INFO

WARNING

ERROR



## Tests


Verify:


- logger initializes;
- messages are written.


---

# PHASE 2 - DATABASE LAYER


---

# TASK-004: Create Database Connection


## Goal


Setup SQLAlchemy.


## Files


Create:



database/connection.py



## Requirements


Use:



SQLAlchemy 2.0
SQLite



## Tests


Verify:


- database connection;
- session creation.


---

# TASK-005: Create Database Models


## Goal


Implement models from DATA_MODELS.md.


## Files


Create:



database/models/



Implement:



Build

Item

Affix

Idol

Skill

BuildItem

BuildIdol

BuildSkill

ItemAffix



## Tests


Verify:


- model creation;
- relationships.


---

# TASK-006: Database Initialization


## Goal


Create database initialization command.


Command:



python main.py init-db



Expected:



Database created successfully



---

# PHASE 3 - PARSER SYSTEM


---

# TASK-007: Create HTTP Client


## Goal


Create external request layer.


## Files


Create:



parsers/http_client.py



Requirements:


Support:


- timeout;
- retry;
- headers;
- caching.


Tests:


Mock HTTP responses.


---

# TASK-008: Create Maxroll Tier Parser


## Goal


Parse Maxroll tier lists.


Sources:



corruption-tier-list

speed-farming-tier-list

bossing-tier-list



Requirements:


Extract only:



S Tier builds



Tests:


Use mocked HTML.


---

# TASK-009: Create Build Parser


## Goal


Parse individual build pages.


Extract:



Items

Idols

Skills

Stats



Tests:


Use local HTML fixtures.


---

# TASK-010: Create Item Parser


## Goal


Extract item information.


Support:



Exalted

Unique

Idols



Tests:


Validate rarity detection.


---

# TASK-011: Create Affix Parser


## Goal


Normalize affixes.


Example:


Before:



Frost Claw +2



After:



Frost Claw Level



Tests:


Validate normalization.


---

# PHASE 4 - ANALYZER


---

# TASK-012: Create Item Analyzer


## Goal


Calculate item importance.


Priority:



Exalted

↓

Idols

↓

Unique



Tests:


Verify scores.


---

# TASK-013: Create Build Popularity Calculator


## Goal


Calculate item usage among S-Tier builds.


Tests:


More usage = higher score.


---

# PHASE 5 - FILTER GENERATION


---

# TASK-014: Create Filter Rule Models


## Goal


Implement:



FilterRule

OptimizationResult



Tests:


Validate objects.


---

# TASK-015: Create Rule Builder


## Goal


Convert analyzed items into rules.


Create:



Exalted rules

Idol rules

Unique rules



Tests:


Verify priorities.


---

# TASK-016: Create Rule Optimizer


## Goal


Guarantee:



rules <= 140



Requirements:


Implement:


- duplicate removal;
- merging;
- priority filtering.


Tests:


Input:



200 rules



Expected:



<=140 rules



---

# TASK-017: Create XML Generator


## Goal


Generate Last Epoch filter.


Output:



output/LastEpoch_Smart_Filter.xml



Tests:


Validate XML.


---

# PHASE 6 - CLI APPLICATION


---

# TASK-018: Create CLI Commands


Commands:



init-db

test-parser

update-data

analyze

generate

full-update



Tests:


Verify commands execute.


---

# TASK-019: Create Generation Report


Output:



filter_report.json



Include:



builds analyzed

exalted rules

idol rules

unique rules

total rules



---

# PHASE 7 - FINAL INTEGRATION


---

# TASK-020: Full Application Workflow


Implement:



Maxroll

↓

Parser

↓

Database

↓

Analyzer

↓

Generator

↓

XML



Tests:


Verify:


- XML created;
- rules <=140;
- no errors.


---

# CHECKPOINTS


---

# CHECKPOINT-1


Completed:



Project structure

Configuration

Database



Validation:



pytest



---

# CHECKPOINT-2


Completed:



All parsers



Validation:



Parser tests pass



---

# CHECKPOINT-3


Completed:



Analyzer



Validation:



Scores calculated correctly



---

# CHECKPOINT-4


Completed:



Filter generator



Validation:



XML generated

Rules <=140



---

# CHECKPOINT-5


Final:



Full update works



Command:



python main.py full-update



---

# Definition Of Done


A task is complete only when:


✓ Code implemented

✓ Tests created

✓ Tests passed

✓ Documentation followed

✓ No architecture violations


---

# END OF COPILOT_TASKS.md