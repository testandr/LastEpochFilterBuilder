"""Script: extract planner profile and game data from HAR export.

Usage: python scripts/extract_maxroll_profile_from_har.py path/to/maxroll.har

It writes into data/debug/network/extracted/planner_profile.json and game_data.json
when found.
"""
import sys
from pathlib import Path

from app.research.har_profile_extractor import extract_from_har, save_extracted


def main():
    if len(sys.argv) < 2:
        print("Usage: extract_maxroll_profile_from_har.py path/to/file.har")
        return 2
    har_path = Path(sys.argv[1])
    if not har_path.exists():
        print("File not found:", har_path)
        return 2
    found = extract_from_har(har_path)
    out_dir = Path("data") / "debug" / "network" / "extracted"
    planner_path, game_path = save_extracted(found, out_dir)
    if planner_path:
        print("Planner profile extracted to:", planner_path)
    else:
        print("Planner profile not found or invalid in HAR.")
    if game_path:
        print("Game data extracted to:", game_path)
    else:
        print("Game data not found or invalid in HAR.")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
