# DEVELOPMENT_SETUP.md

# Last Epoch Smart Loot Filter Generator

## Development Environment Setup

Version: 1.0


---

# 1. Purpose


This document describes how to prepare the development environment.


The goal:

- install required software;
- configure Python;
- run the application;
- run tests;
- prepare development workflow.


---

# 2. Required Software


## Operating System


Supported:



Windows 10/11
Linux
macOS



Primary development environment:



Windows 10/11



---

# 3. Required Applications


Install:


## Python


Required version:



Python 3.12+



Verify:


```bash
python --version
```
Expected:

Python 3.12.x
Visual Studio Code / Visual Studio

Recommended:

Visual Studio Code

Required extensions:

Python

Pylance

GitHub Copilot

GitHub Copilot Chat

Python Debugger
Git

Verify:

git --version



---

# 4. Project Creation

Create project:

mkdir last_epoch_filter_generator

cd last_epoch_filter_generator

Initialize Git:

git init



---

# 5. Python Virtual Environment

Create environment:

Windows:

python -m venv venv

Activate:

Windows:

venv\Scripts\activate

Linux/macOS:

source venv/bin/activate



---

# 6. Project Dependencies

Create:

requirements.txt

Initial dependencies:

beautifulsoup4

requests

lxml

sqlalchemy

alembic

pydantic

python-dotenv

pyyaml

pytest

pytest-cov

pytest-mock

rich

Install:

pip install -r requirements.txt



---

# 7. Project Structure

Final structure:

last_epoch_filter_generator/


├── app/


│
├── database/


│
├── parsers/


│
├── analyzer/


│
├── generator/


│
├── config/


│
├── data/


│
├── tests/


│
├── output/


│
├── main.py


├── requirements.txt


├── README.md


├── .env


└── config.yaml




---

# 8. Application Modules
app

Main application package.

Contains:

core logic
parsers

External data extraction.

Contains:

Maxroll parsers
analyzer

Item evaluation.

Contains:

scoring logic
priority calculation
generator

Filter generation.

Contains:

rules
optimization
XML creation
database

Database layer.

Contains:

models
repositories
migrations



---

# 9. Configuration

Create:

.env

Example:

APP_ENV=development

DATABASE_URL=sqlite:///data/database.sqlite

CACHE_ENABLED=true

OFFLINE_MODE=false

MAX_FILTER_RULES=140

Create:

config.yaml

Example:

application:

  name:
    Last Epoch Smart Loot Filter


parser:

  request_delay: 1

  timeout: 20

  offline_mode: false


filter:

  max_rules: 140


database:

  type: sqlite

  path: data/database.sqlite




---

# 10. Database Setup

Default database:

SQLite

Location:

data/database.sqlite

Initialize:

python main.py init-db

Expected:

Database created successfully



---

# 11. Cache Setup

Create folders:

data/cache/


├── tierlists

├── builds

└── items


Purpose:

save downloaded pages;
reduce Maxroll requests;
allow offline testing.



---

# 12. Running Application

Main command:

python main.py

Help:

python main.py --help



---

# 13. Available Commands
Initialize database
python main.py init-db
Test parser
python main.py test-parser
Update Maxroll data
python main.py update-data
Analyze items
python main.py analyze
Generate filter
python main.py generate
Full update

Complete workflow:

python main.py full-update

Process:

Download data

↓

Parse builds

↓

Analyze items

↓

Generate rules

↓

Optimize rules

↓

Create XML

↓

Generate report



---

# 14. Output Files

Generated files:

output/


├── LastEpoch_Smart_Filter.xml


├── filter_report.json


└── backups/




---

# 15. Running Tests

All tests:

pytest

With coverage:

pytest --cov=app

Parser tests:

pytest tests/parsers

Generator tests:

pytest tests/generator



---

# 16. Development Mode

Recommended:

OFFLINE_MODE=true

during development.

Reason:

faster testing;
no dependency on Maxroll;
prevents blocking.



---

# 17. Debug Mode

Enable:

.env

DEBUG=true

Debug mode should provide:

detailed logs;
parser information;
generated rules preview.



---

# 18. Logging

Location:

logs/

Example:

logs/application.log

Log levels:

DEBUG

INFO

WARNING

ERROR



---

# 19. Git Structure

Recommended branches:

main

develop

feature/*

Example:

feature/maxroll-parser

feature/filter-generator

feature/xml-writer



---

# 20. Commit Rules

Commit messages:

Good:

Add Maxroll tier parser

Fix rule optimizer limit

Add idol extraction tests

Bad:

changes

update

fix



---

# 21. Copilot Usage Rules

GitHub Copilot should:

read all *.md documentation first;
implement one task at a time;
create tests together with code;
not change architecture without approval.

Before coding:

Ask Copilot:

Read:

PROJECT_CONTEXT.md

ARCHITECTURE.md

DATA_MODELS.md

PARSER_SPECIFICATION.md

FILTER_GENERATION_SPECIFICATION.md

TESTING_STRATEGY.md

DEVELOPMENT_SETUP.md


Confirm understanding before implementation.



---

# 22. First Development Run

After installation:

Execute:

python main.py init-db

pytest

python main.py test-parser

Expected:

Database initialized

Tests passed

Parser environment ready



---

# 23. Troubleshooting
Python not found

Solution:

Install Python and add to PATH.

Module not found

Solution:

Activate venv:

Windows:

venv\Scripts\activate

Install:

pip install -r requirements.txt
Parser blocked

Solution:

Enable:

OFFLINE_MODE=true

Use cached data.




---

# 24. Definition of Ready

The project is ready for development when:

✓ Python installed

✓ Virtual environment created

✓ Dependencies installed

✓ Database initialized

✓ Tests run successfully

✓ Copilot has access to documentation