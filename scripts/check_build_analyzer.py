"""Diagnostic script for build analyzer.

Loads S-Tier build/profile data from local sources, runs PlannerProfileParser,
feeds BuildDetails into Analyzer, and outputs diagnostic information.
"""
import json
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.analyzer.build_analyzer import BuildAnalyzer
from app.analyzer.models import AnalysisResult
from app.dto.models import BuildDetails
from app.parsers.planner_profile_parser import PlannerProfileParser

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def load_local_planner_profiles():
    """Load planner profiles from local debug data."""
    data_dir = project_root / "data" / "debug" / "network" / "extracted"
    profile_file = data_dir / "planner_profile.json"

    if not profile_file.exists():
        logger.warning(f"No planner profile found at {profile_file}")
        return []

    logger.info(f"Loading planner profile from {profile_file}")

    with open(profile_file, 'r', encoding='utf-8') as f:
        profile_data = json.load(f)

    return [profile_data]


def load_game_data():
    """Load game data for parser."""
    data_dir = project_root / "data" / "debug" / "network" / "extracted"
    game_data_file = data_dir / "game_data.json"

    if not game_data_file.exists():
        logger.error(f"No game_data found at {game_data_file}")
        return None

    logger.info(f"Loading game_data from {game_data_file}")

    with open(game_data_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    """Main diagnostic function."""
    logger.info("=" * 80)
    logger.info("BUILD ANALYZER DIAGNOSTIC")
    logger.info("=" * 80)

    # Load game data
    game_data = load_game_data()
    if not game_data:
        logger.error("Cannot proceed without game_data")
        return

    # Load local data
    profiles = load_local_planner_profiles()

    if not profiles:
        logger.error("No local planner profiles available")
        logger.info("\n" + "="*80)
        logger.info("LIMITATION: Only unit tests validated (no real multi-build data)")
        logger.info("="*80)
        return

    logger.info(f"\nLoaded {len(profiles)} planner profile(s) locally")
    logger.info(f"Note: This is NOT a full S-Tier analysis - only {len(profiles)} build(s) available\n")

    # Parse profiles
    parser = PlannerProfileParser(game_data)
    builds = []

    for i, profile in enumerate(profiles):
        logger.info(f"Parsing profile {i+1}...")
        try:
            # Parse returns List[BuildDetails] now
            build_list = parser.parse(profile, strategy='active')
            builds.extend(build_list)
            for build_details in build_list:
                logger.info(f"  Build: {build_details.name}")
                logger.info(f"  Items: {len(build_details.items)}")
                logger.info(f"  Idols: {len(build_details.idols)}")
        except Exception as e:
            logger.error(f"  Failed to parse profile {i+1}: {e}")

    if not builds:
        logger.error("No builds successfully parsed")
        return

    # Run analyzer
    logger.info(f"\nAnalyzing {len(builds)} build(s)...")
    analyzer = BuildAnalyzer()

    # For this diagnostic, assume single-source (no source_mapping needed)
    result: AnalysisResult = analyzer.analyze(builds)

    # Sort candidates by score
    result.sort_candidates()

    # Output results
    logger.info("\n" + "="*80)
    logger.info("ANALYSIS RESULTS")
    logger.info("="*80)

    stats = result.stats
    logger.info(f"\nBuilds analyzed: {stats.builds_analyzed}")
    logger.info(f"Unique builds: {stats.unique_builds}")
    logger.info(f"Total raw items: {stats.total_raw_items}")
    logger.info(f"Total raw idols: {stats.total_raw_idols}")
    logger.info(f"Total raw uniques: {stats.total_raw_uniques}")

    logger.info(f"\n{'-'*80}")
    logger.info("CANDIDATES")
    logger.info(f"{'-'*80}")
    logger.info(f"Exalted candidates: {stats.exalted_candidates}")
    logger.info(f"Idol candidates: {stats.idol_candidates}")
    logger.info(f"Unique candidates: {stats.unique_candidates}")

    logger.info(f"\n{'-'*80}")
    logger.info("ESTIMATED RULES")
    logger.info(f"{'-'*80}")
    logger.info(f"Exalted rules: {stats.estimated_exalted_rules}")
    logger.info(f"Idol rules: {stats.estimated_idol_rules}")
    logger.info(f"Unique rules: {stats.estimated_unique_rules}")
    logger.info(f"TOTAL: {stats.estimated_total_rules}")

    if stats.exceeds_limit:
        logger.warning(f"\n⚠ Estimated rules ({stats.estimated_total_rules}) exceed 140 limit")
        logger.warning("Optimization will be needed in future RuleOptimizer stage")

    # Top 20 Exalted
    if result.exalted_candidates:
        logger.info(f"\n{'-'*80}")
        logger.info("TOP 20 EXALTED CANDIDATES (by score)")
        logger.info(f"{'-'*80}")

        for i, cand in enumerate(result.exalted_candidates[:20], 1):
            slot, item_type, sub_type = cand.base_key
            affixes_str = ", ".join(f"{name} T{tier}" for name, tier in sorted(cand.affixes))
            sources_str = ", ".join(sorted(cand.sources))

            logger.info(f"\n{i}. Score: {cand.score:.2f}")
            logger.info(f"   Slot: {slot}")
            logger.info(f"   Base: itemType={item_type}, subType={sub_type}")
            logger.info(f"   Affixes: {affixes_str}")
            logger.info(f"   Build count: {cand.build_count}")
            logger.info(f"   Occurrence count: {cand.occurrence_count}")
            logger.info(f"   Sources: {sources_str}")
            logger.info(f"   Max tier: {cand.max_tier}, Avg tier: {cand.avg_tier:.1f}")

    # Top 20 Idols
    if result.idol_candidates:
        logger.info(f"\n{'-'*80}")
        logger.info("TOP 20 IDOL CANDIDATES (by score)")
        logger.info(f"{'-'*80}")

        for i, cand in enumerate(result.idol_candidates[:20], 1):
            mods_str = ", ".join(sorted(cand.modifiers))
            sources_str = ", ".join(sorted(cand.sources))

            logger.info(f"\n{i}. Score: {cand.score:.2f}")
            logger.info(f"   Size: {cand.size}")
            logger.info(f"   Modifiers: {mods_str}")
            logger.info(f"   Build count: {cand.build_count}")
            logger.info(f"   Occurrence count: {cand.occurrence_count}")
            logger.info(f"   Sources: {sources_str}")

    # Top 20 Uniques
    if result.unique_candidates:
        logger.info(f"\n{'-'*80}")
        logger.info("TOP 20 UNIQUE CANDIDATES (by score)")
        logger.info(f"{'-'*80}")

        for i, cand in enumerate(result.unique_candidates[:20], 1):
            sources_str = ", ".join(sorted(cand.sources))

            logger.info(f"\n{i}. Score: {cand.score:.2f}")
            logger.info(f"   Name: {cand.name}")
            logger.info(f"   UniqueID: {cand.unique_id}")
            logger.info(f"   Slot: {cand.slot}")
            logger.info(f"   Build count: {cand.build_count}")
            logger.info(f"   Occurrence count: {cand.occurrence_count}")
            logger.info(f"   Sources: {sources_str}")

    logger.info(f"\n{'='*80}")
    logger.info("IMPORTANT LIMITATION")
    logger.info(f"{'='*80}")
    logger.info(f"Only {len(builds)} real build(s) available locally.")
    logger.info("This is NOT a representative S-Tier analysis.")
    logger.info("Do NOT draw conclusions about item/affix popularity from this output.")
    logger.info("Use unit tests for functional validation.")
    logger.info(f"{'='*80}\n")


if __name__ == "__main__":
    main()
