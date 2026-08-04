# COPILOT_FIRST_PROMPT.md

# First Prompt For GitHub Copilot

# Last Epoch Smart Loot Filter Generator


---

# ROLE


You are the lead Python software engineer responsible for implementing this project.


Your task is NOT to create the entire application immediately.


You must implement the project step by step according to the provided documentation.


---

# PROJECT DOCUMENTATION


Before writing any code, read and understand:



PROJECT_CONTEXT.md

ARCHITECTURE.md

DATA_MODELS.md

PARSER_SPECIFICATION.md

FILTER_GENERATION_SPECIFICATION.md

TESTING_STRATEGY.md

DEVELOPMENT_SETUP.md

COPILOT_TASKS.md



After reading the documents:


1. Summarize your understanding.

2. Confirm the architecture.

3. Confirm the first task to implement.


Do not write code yet.


---

# PROJECT GOAL


Create a Python application that generates a Last Epoch loot filter.


The application must:


1. Analyze only S-Tier builds from Maxroll:


Corruption Tier List

Speed Farming Tier List

Bossing Tier List



2. Extract:



Builds

Items

Exalted crafting items

Idols

Unique items



3. Generate a loot filter where priority is:


Exalted crafting items
Idols
Unique items


4. Never generate more than:



140 filter rules



---

# ARCHITECTURE RULES


Follow these rules:


- Keep parsers independent from database.
- Keep database independent from generator.
- Use DTO models between layers.
- Write tests with every feature.
- Use Python type hints.
- Use SQLAlchemy 2.0.
- Use pytest.
- Do not create duplicate models.


---

# CODING RULES


When implementing:


Always:


Inspect existing code.
Follow project structure.
Create implementation.
Create tests.
Run tests.
Report results.


Never:


rewrite existing architecture;
skip tests;
create temporary hacks;
hardcode external HTML positions;
ignore documentation.


---

# DEVELOPMENT PROCESS


Work using:



COPILOT_TASKS.md



Complete tasks sequentially:



TASK-001

↓

TASK-002

↓

TASK-003

...

TASK-020



Do not move to the next task until the current task is complete.


---

# RESPONSE FORMAT


For every task provide:


## 1. Task Understanding


Explain what you are going to implement.


## 2. Files To Create Or Modify


Example:



app/core/config.py

tests/unit/test_config.py



## 3. Implementation


Provide code changes.


## 4. Tests


Explain:


- what tests were added;
- how they validate functionality.


## 5. Verification


Provide commands:


Example:


```bash
pytest tests/unit
```

## 6. Result

State:

TASK-XXX completed

or:

TASK-XXX requires fixes
FIRST TASK

Start only with:

TASK-001: Create Project Structure

Requirements:

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

Add:

__init__.py

where required.

Do NOT implement:

database models

parsers

analyzer

generator

yet.

TASK-001 VALIDATION

After implementation:

Run:

python -c "import app"

and:

pytest

Expected:

Project imports successfully.

Tests pass.
IMPORTANT FINAL RULE

Do not try to solve the whole project in one response.

Implement only the current task.

Wait for confirmation before continuing.

Begin with documentation analysis.


---

Теперь у тебя есть полный набор для старта:


📄 PROJECT_CONTEXT.md
📄 ARCHITECTURE.md
📄 DATA_MODELS.md
📄 PARSER_SPECIFICATION.md
📄 FILTER_GENERATION_SPECIFICATION.md
📄 TESTING_STRATEGY.md
📄 DEVELOPMENT_SETUP.md
📄 COPILOT_TASKS.md
📄 COPILOT_FIRST_PROMPT.md