import re
import sys

def fix_affixes(text):
    # Single affix: frozenset([('Name', tier)]) -> frozenset([(None, 'Name', tier)])
    text = re.sub(r"frozenset\(\[\('([^']+)',\s*(\d+)\)\]\)", r"frozenset([(None, '\1', \2)])", text)

    # Multiple affixes: frozenset([('A', 5), ('B', 4)]) -> frozenset([(None, 'A', 5), (None, 'B', 4)])
    def replace_multi(match):
        pairs = re.findall(r"\('([^']+)',\s*(\d+)\)", match.group(1))
        fixed = ", ".join([f"(None, '{name}', {tier})" for name, tier in pairs])
        return f"frozenset([{fixed}])"

    text = re.sub(r"frozenset\(\[(\('([^']+)',\s*\d+\),\s*)+\('([^']+)',\s*\d+\)\]\)", replace_multi, text)

    # idol modifiers: frozenset(['Mod X']) -> frozenset([(None, 'Mod X', 0)])
    def replace_idol(match):
        mods = re.findall(r"'([^']+)'", match.group(1))
        fixed = ", ".join([f"(None, '{m}', 0)" for m in mods])
        return f"modifiers=frozenset([{fixed}])"

    text = re.sub(r"modifiers=frozenset\(\[([^]]+)\]\)", replace_idol, text)

    return text

if __name__ == "__main__":
    with open("tests/test_rule_optimizer.py", "r", encoding="utf-8") as f:
        content = f.read()

    fixed = fix_affixes(content)

    with open("tests/test_rule_optimizer.py", "w", encoding="utf-8") as f:
        f.write(fixed)

    print("Fixed test_rule_optimizer.py")
