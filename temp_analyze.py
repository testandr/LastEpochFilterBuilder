import json
from pathlib import Path

profile_path = Path("data/debug/network/extracted/planner_profile.json")
gamedata_path = Path("data/debug/network/extracted/game_data.json")

with open(profile_path) as f:
    planner = json.load(f)

with open(gamedata_path) as f:
    gamedata = json.load(f)

meta = planner["profile_metadata"]
bd = planner["build_data"]

print("="*80)
print("REAL PLANNER PROFILE ANALYSIS")
print("="*80)
print()
print(f"Profile ID: {meta['id']}")
print(f"Name: {meta['name']}")
print(f"Class: {meta['class']}")
print(f"Season: {meta['season']}")
print(f"Mainset: {meta.get('mainset')}")
print(f"Profiles count: {len(bd['profiles'])}")
print(f"Items dict entries: {len(bd['items'])}")
print(f"activeProfile: {bd.get('activeProfile')}")
print(f"activeEmbed: {bd.get('activeEmbed')}")
print()
print("Profile variants:")
for i, p in enumerate(bd['profiles']):
    print(f"  {i}: {p['name']}")
print()
print("Game data top-level keys:")
for k in sorted(gamedata.keys()):
    v = gamedata[k]
    t = f"list[{len(v)}]" if isinstance(v, list) else f"dict[{len(v)}]" if isinstance(v, dict) else type(v).__name__
    print(f"  {k}: {t}")
