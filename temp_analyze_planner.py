import json

p = json.load(open('data/debug/network/extracted/planner_profile.json'))
meta = p['profile_metadata']
bd = p['build_data']

print('=== PLANNER PROFILE METADATA ===')
print(f'Profile ID: {meta.get("id", "N/A")}')
print(f'Name: {meta.get("name", "N/A")}')
print(f'Class: {meta.get("class", "N/A")}')
print(f'Season: {meta.get("season", "N/A")}')

print()
print('=== BUILD DATA ===')
print(f'activeProfile: {bd.get("activeProfile", "N/A")}')
print(f'activeEmbed: {bd.get("activeEmbed", "N/A")}')
print(f'mainset exists: {"mainset" in bd}')
print(f'Profiles count: {len(bd.get("profiles", []))}')
print(f'Items dict count: {len(bd.get("items", {}))}')

print()
print('=== PROFILE VARIANTS ===')
for i, prof in enumerate(bd.get('profiles', [])):
    print(f'\nProfile {i}:')
    print(f'  name: {prof.get("name")}')
    print(f'  class: {prof.get("class")}')
    print(f'  mastery: {prof.get("mastery")}')
    print(f'  level: {prof.get("level")}')
    print(f'  item references: {len(prof.get("items", {}))}')
    print(f'  idols: {len(prof.get("idols", []))}')
    print(f'  blessings: {len(prof.get("blessings", []))}')
    print(f'  passives: {len(prof.get("passives", []))}')
    print(f'  skillTrees: {len(prof.get("skillTrees", []))}')
    print(f'  activeSkills: {prof.get("activeSkills", "N/A")}')
    print(f'  specializedSkills: {prof.get("specializedSkills", "N/A")}')

    # Show actual item refs
    if prof.get("items"):
        print(f'  Item slots:')
        for slot, item in prof.get("items", {}).items():
            print(f'    {slot}: {item}')

print()
print('=== ITEMS DICTIONARY ===')
items = bd.get('items', {})
print(f'Total items: {len(items)}')
print(f'Key type: {type(list(items.keys())[0]) if items else "N/A"}')

for item_id, item_data in list(items.items())[:10]:
    print(f'\n  Item {item_id}:')
    print(f'    Fields: {list(item_data.keys())}')
    for field, value in item_data.items():
        print(f'      {field}: {value} (type: {type(value).__name__})')
