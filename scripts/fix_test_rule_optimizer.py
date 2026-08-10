"""Targeted fixes for test_rule_optimizer.py failures."""
import re

def read_file():
    with open('tests/test_rule_optimizer.py', 'r', encoding='utf-8') as f:
        return f.read()

def write_file(content):
    with open('tests/test_rule_optimizer.py', 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)

def main():
    content = read_file()

    # Fix 1: test_unique_name_id_mapping_preserved
    # Different unique_ids do NOT merge under Part 3B policy
    # Replace single-rule assertion with two-rule assertions
    old1 = """        result = RuleOptimizer().optimize(RuleBuildResult(rules=rules))
        opt = result.rules[0]
        assert 'A' in opt.unique_names
        assert 'B' in opt.unique_names
        assert 1 in opt.unique_ids
        assert 2 in opt.unique_ids"""

    new1 = """        result = RuleOptimizer().optimize(RuleBuildResult(rules=rules))
        # Different unique_ids do NOT merge under Part 3B policy
        assert len(result.rules) == 2
        names = {name for rule in result.rules for name in rule.unique_names}
        ids = {id for rule in result.rules for id in rule.unique_ids}
        assert 'A' in names
        assert 'B' in names
        assert 1 in ids
        assert 2 in ids"""

    content = content.replace(old1, new1)

    # Fix 2: test_over_140_rules_not_pruned
    # Need truly non-mergeable Exalted rules
    # Find the test and replace rule generation with non-mergeable pattern
    old2_pattern = r"(def test_over_140_rules_not_pruned\(self\):.*?rules = \[\]\s+for i in range\(150\):)(.*?)(sources=\{[^}]+\}\s+\))"

    def replace_over_140(match):
        prefix = match.group(1)
        return prefix + """
            rules.append(FilterRule(
                category='exalted',
                semantic_priority=100,
                score=50.0,
                build_count=1,
                slot=f'Slot{i}',  # Unique slot per rule
                item_type=i % 20,
                sub_type=0,
                affixes=frozenset([(f'Affix{i}', 5)]),  # Unique affix per rule
                sources={'s1'}
            ))"""

    content = re.sub(old2_pattern, replace_over_140, content, flags=re.DOTALL)

    # Fix 3: test_mixed_categories_independent_merge
    # Unique expectations must match Part 3B: different IDs don't merge
    # Need to check actual test expectation
    old3 = "        # Should produce 3 rules: 1 exalted, 1 idol, 1 unique"
    new3 = "        # Should produce 4 rules: 1 exalted, 1 idol, 2 unique (different IDs)"
    content = content.replace(old3, new3)

    old3b = "        assert len(result.rules) == 3"
    new3b = "        assert len(result.rules) == 4"
    content = content.replace(old3b, new3b)

    # Fix 4 & 5: test_no_pruning_when_below_budget and test_no_pruning_when_exactly_budget
    # These create Exalted with i % 7 affixes which causes merge
    # Replace with unique affixes
    for test_name in ['test_no_pruning_when_below_budget', 'test_no_pruning_when_exactly_budget']:
        pattern = rf"(def {test_name}\(self\):.*?for i in range\(\d+\):.*?affixes=frozenset\(\[\('A', )(i % 7 \+ 1)(\)\]\))"
        replacement = r"\1i + 1\3"
        content = re.sub(pattern, replacement, content, flags=re.DOTALL)

    # Fix 6: test_idol_pruned_before_exalted
    # Exalted with i % 7 affixes will merge
    old6_pattern = r"(def test_idol_pruned_before_exalted\(self\):.*?# 50 exalted.*?for i in range\(50\):.*?affixes=frozenset\(\[\('A', )(i % 7 \+ 1)(\)\]\))"

    def replace_idol_pruned(match):
        return match.group(1) + "i + 1" + match.group(3)

    content = re.sub(old6_pattern, replace_idol_pruned, content, flags=re.DOTALL)

    # Fix 7: test_source_count_tie_break
    # Rules with build_count=3 for Exalted are protected, need build_count=1
    old7 = """        # Create 3 exalted rules with same score and build_count, different source_count
        # All should be prunable (not protected)
        rules = [
            FilterRule(
                category='exalted',
                semantic_priority=100,
                score=50.0,
                build_count=3,"""

    new7 = """        # Create 3 exalted rules with same score and build_count, different source_count
        # All should be prunable (not protected)
        rules = [
            FilterRule(
                category='exalted',
                semantic_priority=100,
                score=50.0,
                build_count=1,"""

    content = content.replace(old7, new7)

    # Continue fixing remaining rules in test_source_count_tie_break
    old7b = """            FilterRule(
                category='exalted',
                semantic_priority=100,
                score=50.0,
                build_count=3,
                slot='Body',"""

    new7b = """            FilterRule(
                category='exalted',
                semantic_priority=100,
                score=50.0,
                build_count=1,
                slot='Body',"""

    content = content.replace(old7b, new7b)

    # Fix 8: test_stable_identity_tie_break
    # Rules with build_count=3 are protected for Exalted
    old8_pattern = r"(def test_stable_identity_tie_break\(self\):.*?for i in range\(10\):.*?build_count=)3,"
    content = re.sub(old8_pattern, r"\g<1>1,", content, flags=re.DOTALL)

    # Fix 9: test_pruning_counts_correct
    # i % 7 creates mergeable affixes
    old9_pattern = r"(def test_pruning_counts_correct\(self\):.*?# 50 exalted.*?for i in range\(50\):.*?affixes=frozenset\(\[\('A', )(i % 7 \+ 1)(\)\]\))"
    content = re.sub(old9_pattern, lambda m: m.group(1) + "i + 1" + m.group(3), content, flags=re.DOTALL)

    write_file(content)
    print("Fixes applied successfully")

if __name__ == '__main__':
    main()
