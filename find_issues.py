#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Find remaining issues in test file."""

with open('tests/test_rule_optimizer.py', 'r', encoding='utf-8') as f:
    content = f.read()
    lines = content.split('\n')

print("=== REMAINING ISSUES ===\n")

# Find Helmet slots
helmet_lines = [(i+1, line) for i, line in enumerate(lines) if "slot='Helmet'" in line]
if helmet_lines:
    print(f"Found {len(helmet_lines)} Helmet slot constants:")
    for line_num, line in helmet_lines[:5]:
        print(f"  Line {line_num}: {line.strip()}")
    print()

# Find ('A', i % patterns
affix_a_patterns = [(i+1, line) for i, line in enumerate(lines) if "('A', i %" in line]
if affix_a_patterns:
    print(f"Found {len(affix_a_patterns)} old affix patterns ('A', i %):")
    for line_num, line in affix_a_patterns[:5]:
        print(f"  Line {line_num}: {line.strip()}")
    print()

# Find unique_name='Test' or unique_name='Test2'
test_names = [(i+1, line) for i, line in enumerate(lines) if "unique_name='Test'" in line or "unique_name='Test2'" in line]
if test_names:
    print(f"Found {len(test_names)} old Test unique names:")
    for line_num, line in test_names[:5]:
        print(f"  Line {line_num}: {line.strip()}")
    print()

# Find 'B' in unique names
b_names = [(i+1, line) for i, line in enumerate(lines) if "unique_name='B'" in line]
if b_names:
    print(f"Found {len(b_names)} unique_name='B' occurrences:")
    for line_num, line in b_names:
        print(f"  Line {line_num}: {line.strip()}")
    print()

# Find assert 'B' in unique_names
b_asserts = [(i+1, line) for i, line in enumerate(lines) if "assert 'B' in" in line]
if b_asserts:
    print(f"Found {len(b_asserts)} assert 'B' in occurrences:")
    for line_num, line in b_asserts:
        print(f"  Line {line_num}: {line.strip()}")
    print()

print("\n=== SUMMARY ===")
print(f"Total issues found: {len(helmet_lines) + len(affix_a_patterns) + len(test_names) + len(b_names) + len(b_asserts)}")
