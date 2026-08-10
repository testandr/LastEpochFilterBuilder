"""Quick test fixture converter for Phase 0A."""
import re

def fix_exalted_affixes(line):
    """Convert ExaltedCandidate affixes from (name, tier) to (None, name, tier)."""
    if "affixes=frozenset" not in line:
        return line

    # Match frozenset([('Name', tier), ...])
    match = re.search(r"affixes=frozenset\(\[(.*?)\]\)", line)
    if not match:
        return line

    content = match.group(1)

    # Extract all (name, tier) pairs
    pairs = re.findall(r"\('([^']+)',\s*(\d+)\)", content)

    # Convert to (None, name, tier)
    new_pairs = [f"(None, '{name}', {tier})" for name, tier in pairs]
    new_content = ", ".join(new_pairs)

    return line.replace(f"affixes=frozenset([{content}])", f"affixes=frozenset([{new_content}])")

def fix_idol_modifiers(line):
    """Convert IdolCandidate modifiers from 'str' to (None, 'str', 0)."""
    if "modifiers=frozenset" not in line:
        return line

    # Match frozenset(['Mod1', 'Mod2', ...])
    match = re.search(r"modifiers=frozenset\(\[(.*?)\]\)", line)
    if not match:
        return line

    content = match.group(1)

    # Extract all 'Name' strings
    mods = re.findall(r"'([^']+)'", content)

    # Convert to (None, name, 0)
    new_mods = [f"(None, '{mod}', 0)" for mod in mods]
    new_content = ", ".join(new_mods)

    return line.replace(f"modifiers=frozenset([{content}])", f"modifiers=frozenset([{new_content}])")

def process_file(filename):
    with open(filename, "r", encoding="utf-8") as f:
        lines = f.readlines()

    new_lines = []
    for line in lines:
        new_line = fix_exalted_affixes(line)
        new_line = fix_idol_modifiers(new_line)
        new_lines.append(new_line)

    with open(filename, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    print(f"Fixed {filename}")

if __name__ == "__main__":
    process_file("tests/test_rule_builder.py")
    process_file("tests/test_rule_optimizer.py")
