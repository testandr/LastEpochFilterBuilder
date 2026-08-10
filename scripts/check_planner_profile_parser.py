"""Diagnostic script to check PlannerProfileParser on real data.

Loads real extracted planner profile and game data, parses them,
and outputs a human-readable summary.
"""
import json
import sys
from pathlib import Path

# Add project root to path - handle both execution contexts
script_path = Path(__file__).resolve()
project_root = script_path.parent.parent

# If we're in LastEpochFilterBuilder/LastEpochFilterBuilder, go up one more level
if project_root.name == "LastEpochFilterBuilder" and (project_root.parent / "LastEpochFilterBuilder").exists():
    project_root = project_root / "LastEpochFilterBuilder"

sys.path.insert(0, str(project_root))

from app.parsers.planner_profile_parser import PlannerProfileParser


def main():
    """Run diagnostic on real extracted data."""
    # Paths to real extracted data
    data_dir = project_root / "data" / "debug" / "network" / "extracted"
    game_data_path = data_dir / "game_data.json"
    planner_profile_path = data_dir / "planner_profile.json"

    # Check if files exist
    if not game_data_path.exists():
        print(f"[ERROR] game_data.json not found at: {game_data_path}")
        print("   Run extract_maxroll_profile_from_har.py first.")
        return 1

    if not planner_profile_path.exists():
        print(f"[ERROR] planner_profile.json not found at: {planner_profile_path}")
        print("   Run extract_maxroll_profile_from_har.py first.")
        return 1

    print("=" * 70)
    print("PLANNER PROFILE PARSER DIAGNOSTIC")
    print("=" * 70)
    print()

    # Load data
    print("Loading data...")
    with open(game_data_path, "r", encoding="utf-8") as f:
        game_data = json.load(f)

    with open(planner_profile_path, "r", encoding="utf-8") as f:
        planner_profile = json.load(f)

    print(f"[OK] game_data.json loaded ({len(game_data.get('affixes', []))} affixes, "
          f"{len(game_data.get('uniques', []))} uniques)")
    print(f"[OK] planner_profile.json loaded")
    print()

    # Initialize parser
    parser = PlannerProfileParser(game_data)

    # Parse active profile
    print("Parsing active profile...")
    results = parser.parse(planner_profile, strategy="active")

    if not results:
        print("[ERROR] No profiles parsed")
        return 1

    print(f"[OK] Parsed {len(results)} profile(s)")
    print()

    # Print detailed summary
    for idx, build in enumerate(results):
        print_build_summary(build, idx + 1)

    return 0


def print_build_summary(build, number):
    """Print detailed build summary.

    Args:
        build: BuildDetails DTO
        number: Profile number for display
    """
    print("=" * 70)
    print(f"PROFILE #{number}: {build.name}")
    print("=" * 70)
    print()

    # Basic info
    print("BUILD INFO:")
    print(f"  Class:   {build.class_name or 'Unknown'}")
    print(f"  Mastery: {build.mastery or 'Unknown'}")
    print()

    # Equipment summary
    print("EQUIPMENT SUMMARY:")
    unique_count = sum(1 for i in build.items if i.is_unique)
    # Exalted count excludes uniques (unique items can have T6+ affixes but aren't "exalted" items)
    exalted_count = sum(1 for i in build.items if i.is_exalted and not i.is_unique)
    normal_count = len(build.items) - unique_count - exalted_count

    print(f"  Total items: {len(build.items)}")
    print(f"  Unique:      {unique_count}")
    print(f"  Exalted:     {exalted_count}")
    print(f"  Normal/Rare: {normal_count}")
    print()

    # Detailed equipment
    print("EQUIPMENT DETAILS:")
    for item in build.items:
        print(f"  [{item.slot}]")
        print(f"    Name:    {item.name}")
        if item.is_unique:
            print(f"    Type:    Unique (ID: {item.additional.get('uniqueID', 'N/A')})")
        elif item.is_exalted:
            print(f"    Type:    Exalted")
        else:
            print(f"    Type:    {item.rarity or 'Normal'}")

        if item.affixes:
            print(f"    Affixes:")
            for affix in item.affixes:
                tier_str = f"T{affix.tier}" if affix.tier else "?"
                print(f"      - {affix.name} ({tier_str})")
        print()

    # Idols summary
    print("IDOLS:")
    print(f"  Total: {len(build.idols)}")
    if build.idols:
        print(f"  Details:")
        for idx, idol in enumerate(build.idols, 1):
            print(f"    {idx}. {idol.name}")
            print(f"       Size: {idol.size or 'Unknown'}")
            if idol.modifiers:
                print(f"       Modifiers:")
                for mod in idol.modifiers:
                    print(f"         - {mod}")
            print()
    print()


if __name__ == "__main__":
    sys.exit(main())
