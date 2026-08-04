# TESTING_STRATEGY.md

# Last Epoch Smart Loot Filter Generator

## Testing Strategy Documentation

Version: 1.0


---

# 1. Purpose


This document defines the testing strategy for the application.


The goal:


- ensure application stability;
- prevent regressions;
- detect parser failures;
- guarantee valid loot filters;
- guarantee maximum 140 rules limitation.


---

# 2. Testing Principles


All code MUST have tests.


Important components:


- parsers;
- analyzers;
- optimizers;
- generators;
- database layer.


Tests should be:


- isolated;
- repeatable;
- independent from external websites.


---

# 3. Testing Stack


Testing framework:



pytest



Additional tools:



pytest-cov

pytest-mock

pytest-xdist



---

# 4. Test Structure


Project:



tests/

├── unit/

│
├── integration/

│
├── parsers/

│
├── analyzer/

│
├── generator/

│
├── fixtures/

│
└── data/



---

# 5. Testing Pyramid


The project follows:


          E2E Tests
              ▲

              |

      Integration Tests

              ▲

              |

          Unit Tests

              ▲

              |

      Static Validation


---

# 6. Unit Tests


Unit tests verify individual components.


Location:



tests/unit/



Required:


- models;
- utilities;
- calculations;
- validators.


---

# 7. Database Tests


Location:



tests/unit/test_database.py



Test:


- database creation;
- model creation;
- relationships;
- transactions.


Example:


```python
def test_build_creation():

    build = Build(
        name="Frost Claw"
    )

    assert build.name == "Frost Claw"
```



---

# 8. Configuration Tests

Test:

config loading;
environment variables;
default values.

Example:

def test_filter_limit():

    assert settings.max_rules == 140



---

# 9. Logging Tests

Verify:

logger initializes;
file created;
errors recorded.


---

# 10. Parser Testing Strategy

Parser tests are critical.

Reason:

External websites can change.

Rules:

NEVER rely only on live Maxroll.



---

# 11. Mock HTML System

Location:

tests/data/html/

Structure:

tests/data/html/


├── tier_list/

│
├── builds/

│
├── items/

└── idols/


Example:

tier_list_s_example.html

build_frost_claw.html

build_falconer.html



---

# 12. Maxroll Parser Tests

Location:

tests/parsers/test_maxroll_parser.py

Tests:

Test S-Tier detection

Input:

HTML:

S Tier

A Tier

B Tier

Expected:

Only S Tier builds returned.

Test duplicate builds

Input:

Same build in multiple sources.

Expected:

One build with multiple sources.

Test invalid HTML

Input:

Broken HTML.

Expected:

Parser returns empty result and logs warning.



---

# 13. Build Parser Tests

Location:

tests/parsers/test_build_parser.py

Test:

Extraction of:

equipment;
idols;
skills;
stats.

Example:

Input:

Frost Claw Runemaster page

Expected:

{
"items":12,
"idols":4,
"skills":5
}


---

# 14. Item Parser Tests

Location:

tests/parsers/test_item_parser.py

Test:

Unique detection

Input:

Julra's Obsession

Expected:

rarity = Unique
Exalted detection

Input:

Exalted Helmet

Expected:

rarity = Exalted
Affix normalization

Input:

Frost Claw +2

Expected:

Frost Claw Level


---

# 15. Idol Parser Tests

Test:

Input:

Large Arcane Idol

Fire Damage

Expected:

{
"size":
"Large",

"modifier":
"Fire Damage"
}


---

# 16. Analyzer Tests

Location:

tests/analyzer/


---

# 17. Item Score Tests

Verify:

Higher priority:

Exalted

gets higher score than:

Unique

Example:

assert exalted.score > unique.score


---

# 18. Build Popularity Tests

Scenario:

Item A:

used by 10 S-Tier builds

Item B:

used by 1 S-Tier build

Expected:

Item A score > Item B score


---

# 19. Affix Importance Tests

Verify:

Required build affixes receive higher priority.

Example:

Frost Claw Level

>
Random Damage


---

# 20. Rule Builder Tests

Location:

tests/generator/test_rule_builder.py

Verify:

Input:

Exalted Helmet

Output:

SHOW rule

Priority 100


---

# 21. Rule Optimizer Tests

Most important generator tests.

Rule limit test

Input:

200 rules

Expected:

<=140
Duplicate removal test

Input:

Same rule x5

Expected:

One rule
Exalted protection test

Input:

150 rules

including important exalted rules

Expected:

Exalted rules remain.



---

# 22. XML Generator Tests

Location:

tests/generator/test_xml_writer.py

Verify:

XML created;
file readable;
correct structure.


---

# 23. XML Validation Tests

Generated file:

Must pass:

xml.etree.ElementTree.parse()

Expected:

No exception.



---

# 24. Integration Tests

Location:

tests/integration/


---

# 25. Full Generation Test

Scenario:

Sample database

↓

Analyzer

↓

Rule Builder

↓

Optimizer

↓

XML Generator


Expected:

XML file exists

Rules <=140



---

# 26. Offline Mode Test

Application should work without internet.

Configuration:

offline_mode: true

Uses:

tests/data/

Expected:

Successful generation.



---

# 27. Regression Testing

Whenever parser changes:

Run:

all parser tests

Whenever optimizer changes:

Run:

all generator tests


---

# 28. Coverage Requirements

Minimum coverage:

80%

Critical modules:

Parser:

90%


Optimizer:

95%


Generator:

90%


---

# 29. Test Commands

Run all tests:

pytest

Run with coverage:

pytest --cov=app

Run only parser tests:

pytest tests/parsers

Run generator tests:

pytest tests/generator


---

# 30. Continuous Integration

Future GitHub Actions support.

File:

.github/workflows/tests.yml

Pipeline:

Install Python

↓

Install dependencies

↓

Run pytest

↓

Generate coverage



---

# 31. AI Development Rules

When creating new functionality:

Create implementation.
Create unit tests.
Create integration test if needed.
Run existing tests.
Do not remove tests to make code pass.
32. Definition of Done

A feature is complete only when:

✓ Code implemented

✓ Tests created

✓ Existing tests pass

✓ Documentation updated

✓ No regression introduced