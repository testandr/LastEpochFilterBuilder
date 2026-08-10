"""Analyze real extracted planner profile."""
import json
from pathlib import Path

def main():
    profile_path = Path("data/debug/network/extracted/planner_profile.json")
    gamedata_path = Path("data/debug/network/extracted/game_data.json")

    # Load planner profile
    with open(profile_path, 'r', encoding='utf-8') as f:
        planner = json.load(f)

    meta = planner['profile_metadata']
    bd = planner['build_data']

    print("=" * 80)
    print("REAL PLANNER PROFILE ANALYSIS")
    print("=" * 80)
    print()

    print("=== PROFILE METADATA ===")
    print(f"Profile ID: {meta.get('id')}")
    print(f"Name: {meta.get('name')}")
    print(f"Class: {meta.get('class')}")
    print(f"Season: {meta.get('season')}")
    print(f"Mainset: {meta.get('mainset')}")
    print(f"Category: {meta.get('category')}")
    print(f"Date: {meta.get('date')}")
    print(f"Username: {meta.get('user', {}).get('username')}")
    print(f"Type: {meta.get('type')}")
    print()

    print("=== BUILD DATA OVERVIEW ===")
    profiles = bd.get('profiles', [])
    items = bd.get('items', {})
    print(f"Profiles count: {len(profiles)}")
    print(f"Items dict entries: {len(items)}")
    print(f"activeProfile: {bd.get('activeProfile')}")
    print(f"activeEmbed: {bd.get('activeEmbed')}")
    print(f"embeds count: {len(bd.get('embeds', []))}")
    print(f"lootFilters count: {len(bd.get('lootFilters', []))}")
    print()

    print("=== PROFILE VARIANTS ===")
    for i, prof in enumerate(profiles):
        print(f"Profile {i}: {prof.get('name')}")
    print()

    print("=" * 80)
    print("DETAILED PROFILE INSPECTION")
    print("=" * 80)
    print()

    for i, prof in enumerate(profiles):
        print(f"--- Profile {i}: {prof.get('name')} ---")
        print(f"  Class: {prof.get('class')} | Mastery: {prof.get('mastery')} | Level: {prof.get('level')}")

        # Count item references
        item_refs = prof.get('items', [])
        print(f"  Item references: {len(item_refs)}")

        # Idols
        idols = prof.get('idols', [])
        print(f"  Idols: {len(idols)}")

        # Blessings
        blessings = prof.get('blessings', [])
        print(f"  Blessings: {len(blessings)}")
        if blessings:
            print(f"    Example: {blessings[0] if isinstance(blessings[0], int) else blessings[0]}")

        # Passives
        passives = prof.get('passives', [])
        print(f"  Passives: {len(passives)} total")
        if passives:
            allocated = [p for p in passives if p.get('allocated', 0) > 0]
            print(f"    Allocated: {len(allocated)}")
            if allocated:
                example = allocated[0]
                print(f"    Example: id={example.get('id')}, points={example.get('allocated')}")

        # Skill trees
        skill_trees = prof.get('skillTrees', [])
        print(f"  Skill trees: {len(skill_trees)}")
        if skill_trees:
            example = skill_trees[0]
            print(f"    Example: skillId={example.get('skillId')}, points allocated={len([n for n in example.get('nodes', []) if n.get('allocated', 0) > 0])}")

        # Active skills
        active_skills = prof.get('activeSkills', [])
        print(f"  Active skills: {len(active_skills)}")
        if active_skills:
            print(f"    IDs: {active_skills}")

        # Specialized skills
        specialized_skills = prof.get('specializedSkills', [])
        print(f"  Specialized skills: {len(specialized_skills)}")
        if specialized_skills:
            print(f"    IDs: {specialized_skills}")

        print()

    print("=" * 80)
    print("GAME DATA ANALYSIS")
    print("=" * 80)
    print()

    # Load game data
    with open(gamedata_path, 'r', encoding='utf-8') as f:
        gamedata = json.load(f)

    print("=== TOP-LEVEL KEYS ===")
    for key in sorted(gamedata.keys()):
        value = gamedata[key]
        if isinstance(value, list):
            print(f"  {key}: list[{len(value)}]")
        elif isinstance(value, dict):
            print(f"  {key}: dict[{len(value)}]")
        else:
            print(f"  {key}: {type(value).__name__}")
    print()

    print("=" * 80)
    print("ENTITY MAPPING SAMPLES")
    print("=" * 80)
    print()

    # Get first item from planner
    if profiles and profiles[0].get('items'):
        first_item_ref = profiles[0]['items'][0]
        item_id = first_item_ref.get('itemId') or first_item_ref.get('id')
        print(f"=== SAMPLE 1: First profile item ===")
        print(f"Profile item reference: {json.dumps(first_item_ref, indent=2)}")
        print()

        # Look up in items dict
        if str(item_id) in items:
            item_data = items[str(item_id)]
            print(f"Items dict entry [{item_id}]:")
            print(f"  {json.dumps(item_data, indent=2)[:500]}...")
        print()

    # Sample unique item
    print("=== SAMPLE 2: Unique item from game_data ===")
    uniques = gamedata.get('uniques', [])
    if uniques:
        unique_example = uniques[0]
        print(f"First unique: {json.dumps(unique_example, indent=2)[:500]}...")
    print()

    # Sample affix
    print("=== SAMPLE 3: Affix from game_data ===")
    affixes = gamedata.get('affixes', [])
    if affixes:
        affix_example = affixes[0]
        print(f"First affix: {json.dumps(affix_example, indent=2)[:500]}...")
    print()

    # Sample idol
    print("=== SAMPLE 4: Idol from profile ===")
    if profiles and profiles[0].get('idols'):
        idol_example = profiles[0]['idols'][0]
        print(f"First idol reference: {json.dumps(idol_example, indent=2)[:500]}...")
    print()

    # Sample skill/blessing
    print("=== SAMPLE 5: Blessing from profile ===")
    if profiles and profiles[0].get('blessings'):
        blessing_id = profiles[0]['blessings'][0]
        print(f"First blessing ID: {blessing_id}")

        # Look up in game_data
        blessings_data = gamedata.get('blessings', [])
        matching = [b for b in blessings_data if b.get('id') == blessing_id]
        if matching:
            print(f"Matching blessing data: {json.dumps(matching[0], indent=2)[:500]}...")
    print()

if __name__ == '__main__':
    main()
