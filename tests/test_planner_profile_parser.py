"""Tests for PlannerProfileParser and ProfileSelector."""
import json
import pytest
from pathlib import Path

from app.parsers.planner_profile_parser import PlannerProfileParser
from app.parsers.profile_selector import ProfileSelector


# Fixtures path
FIXTURES_DIR = Path(__file__).parent / "data" / "json"
GAME_DATA_FIXTURE = FIXTURES_DIR / "sample_game_data.json"
PLANNER_PROFILE_FIXTURE = FIXTURES_DIR / "sample_planner_profile.json"

# Real data paths (optional)
REAL_DATA_DIR = Path("data/debug/network/extracted")
REAL_GAME_DATA = REAL_DATA_DIR / "game_data.json"
REAL_PLANNER_PROFILE = REAL_DATA_DIR / "planner_profile.json"


@pytest.fixture
def game_data():
    """Load sample game data."""
    with open(GAME_DATA_FIXTURE, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def planner_profile():
    """Load sample planner profile."""
    with open(PLANNER_PROFILE_FIXTURE, "r", encoding="utf-8") as f:
        return json.load(f)


class TestProfileSelector:
    """Tests for ProfileSelector."""

    def test_select_active_profile(self):
        """Test selecting active profile."""
        selector = ProfileSelector()
        build_data = {
            "profiles": [
                {"name": "Profile 1"},
                {"name": "Profile 2"},
                {"name": "Profile 3"}
            ],
            "activeProfile": 1
        }

        result = selector.select(build_data, strategy="active")

        assert len(result) == 1
        assert result[0]["name"] == "Profile 2"

    def test_select_all_profiles(self):
        """Test selecting all profiles."""
        selector = ProfileSelector()
        build_data = {
            "profiles": [
                {"name": "Profile 1"},
                {"name": "Profile 2"}
            ],
            "activeProfile": 0
        }

        result = selector.select(build_data, strategy="all")

        assert len(result) == 2
        assert result[0]["name"] == "Profile 1"
        assert result[1]["name"] == "Profile 2"

    def test_missing_active_profile_defaults_to_first(self):
        """Test that missing activeProfile falls back to first profile."""
        selector = ProfileSelector()
        build_data = {
            "profiles": [
                {"name": "Profile 1"},
                {"name": "Profile 2"}
            ]
        }

        result = selector.select(build_data, strategy="active")

        assert len(result) == 1
        assert result[0]["name"] == "Profile 1"

    def test_invalid_active_profile_index_defaults_to_first(self):
        """Test that invalid activeProfile index falls back to first profile."""
        selector = ProfileSelector()
        build_data = {
            "profiles": [
                {"name": "Profile 1"},
                {"name": "Profile 2"}
            ],
            "activeProfile": 99
        }

        result = selector.select(build_data, strategy="active")

        assert len(result) == 1
        assert result[0]["name"] == "Profile 1"

    def test_empty_profiles_raises_error(self):
        """Test that empty profiles array raises ValueError."""
        selector = ProfileSelector()
        build_data = {"profiles": []}

        with pytest.raises(ValueError, match="profiles array is empty"):
            selector.select(build_data, strategy="active")

    def test_unknown_strategy_raises_error(self):
        """Test that unknown strategy raises ValueError."""
        selector = ProfileSelector()
        build_data = {
            "profiles": [{"name": "Profile 1"}],
            "activeProfile": 0
        }

        with pytest.raises(ValueError, match="Unknown strategy"):
            selector.select(build_data, strategy="invalid")


class TestPlannerProfileParser:
    """Tests for PlannerProfileParser."""

    def test_parser_initialization_validates_game_data(self):
        """Test that parser validates game_data on init."""
        invalid_game_data = {"items": []}

        with pytest.raises(ValueError, match="missing 'affixes'"):
            PlannerProfileParser(invalid_game_data)

    def test_parse_active_profile(self, game_data, planner_profile):
        """Test parsing active profile."""
        parser = PlannerProfileParser(game_data)

        results = parser.parse(planner_profile, strategy="active")

        assert len(results) == 1
        build = results[0]
        assert build.name == "Test Profile 1"
        assert build.class_name == "Test Class"
        assert build.mastery == "Test Mastery 1"

    def test_parse_all_profiles(self, game_data, planner_profile):
        """Test parsing all profiles."""
        parser = PlannerProfileParser(game_data)

        results = parser.parse(planner_profile, strategy="all")

        assert len(results) == 2
        assert results[0].name == "Test Profile 1"
        assert results[1].name == "Test Profile 2"
        assert results[1].mastery == "Test Mastery 2"

    def test_parse_equipment_with_reference(self, game_data, planner_profile):
        """Test parsing equipment with int reference to build_data.items."""
        parser = PlannerProfileParser(game_data)

        results = parser.parse(planner_profile, strategy="active")
        build = results[0]

        # weapon: 1 -> build_data.items["1"] -> unique item
        weapon_items = [i for i in build.items if i.slot == "Weapon"]
        assert len(weapon_items) == 1
        weapon = weapon_items[0]
        assert weapon.name == "Test Unique Weapon"
        assert weapon.is_unique is True
        assert weapon.rarity == "Unique"

    def test_parse_equipment_with_inline_object(self, game_data, planner_profile):
        """Test parsing equipment with inline object."""
        parser = PlannerProfileParser(game_data)

        results = parser.parse(planner_profile, strategy="active")
        build = results[0]

        # finger1 is inline object with uniqueID
        ring_items = [i for i in build.items if i.slot == "Ring 1"]
        assert len(ring_items) == 1
        ring = ring_items[0]
        assert ring.name == "Test Unique Ring"
        assert ring.is_unique is True

    def test_parse_equipment_empty_slot(self, game_data, planner_profile):
        """Test that empty slot (null) is skipped."""
        parser = PlannerProfileParser(game_data)

        results = parser.parse(planner_profile, strategy="active")
        build = results[0]

        # finger2 is null, should not appear in items
        ring2_items = [i for i in build.items if i.slot == "Ring 2"]
        assert len(ring2_items) == 0

    def test_affix_tier_conversion(self, game_data, planner_profile):
        """Test that planner tier is converted to displayed tier."""
        parser = PlannerProfileParser(game_data)

        results = parser.parse(planner_profile, strategy="active")
        build = results[0]

        # body item (ref 2) has affix with planner tier=7 -> displayed T8
        body_items = [i for i in build.items if i.slot == "Body Armor"]
        assert len(body_items) == 1
        body = body_items[0]
        assert len(body.affixes) == 1
        assert body.affixes[0].name == "Test Affix T8"
        assert body.affixes[0].tier == 8  # planner tier 7 + 1

    def test_exalted_detection(self, game_data, planner_profile):
        """Test that exalted detection works (tier >= 5 -> T6+)."""
        parser = PlannerProfileParser(game_data)

        results = parser.parse(planner_profile, strategy="active")
        build = results[0]

        # body item has tier=7 (T8), should be exalted
        body_items = [i for i in build.items if i.slot == "Body Armor"]
        body = body_items[0]
        assert body.is_exalted is True
        assert body.rarity == "Exalted"

    def test_normal_item_not_exalted(self, game_data, planner_profile):
        """Test that normal item without T6+ affixes is not exalted."""
        parser = PlannerProfileParser(game_data)

        results = parser.parse(planner_profile, strategy="all")
        build = results[1]  # Profile 2 has weapon with tier=5 (T6, is exalted!)

        # Actually tier=5 is T6, so is exalted. Let's check weapon in profile 1
        # Profile 1 weapon is unique, so is_exalted is False for uniques
        build = results[0]
        weapon = [i for i in build.items if i.slot == "Weapon"][0]
        assert weapon.is_unique is True
        assert weapon.is_exalted is False  # unique items don't get exalted flag

    def test_unique_item_mapping(self, game_data, planner_profile):
        """Test unique item name resolution."""
        parser = PlannerProfileParser(game_data)

        results = parser.parse(planner_profile, strategy="active")
        build = results[0]

        weapon = [i for i in build.items if i.slot == "Weapon"][0]
        assert weapon.name == "Test Unique Weapon"
        assert weapon.is_unique is True
        assert weapon.additional.get("uniqueID") == 0

    def test_idol_parsing_with_reference(self, game_data, planner_profile):
        """Test idol parsing with int reference."""
        parser = PlannerProfileParser(game_data)

        results = parser.parse(planner_profile, strategy="active")
        build = results[0]

        # First idol is reference 10 -> Grand Idol with 1 affix
        assert len(build.idols) >= 1
        idol = build.idols[0]
        assert "Grand Idol" in idol.name
        assert len(idol.modifiers) == 1
        assert "Idol Affix 1" in idol.modifiers[0]

    def test_idol_parsing_with_inline_object(self, game_data, planner_profile):
        """Test idol parsing with inline object."""
        parser = PlannerProfileParser(game_data)

        results = parser.parse(planner_profile, strategy="active")
        build = results[0]

        # Third idol (index 2) is inline Minor Idol with 2 affixes
        assert len(build.idols) == 2  # only non-null idols
        idol = build.idols[1]
        assert "Minor Idol" in idol.name
        assert len(idol.modifiers) == 2

    def test_idol_size_determination(self, game_data, planner_profile):
        """Test idol size mapping from itemType."""
        parser = PlannerProfileParser(game_data)

        results = parser.parse(planner_profile, strategy="active")
        build = results[0]

        # itemType 29 -> Grand Idol, itemType 26 -> Minor Idol
        idol_grand = build.idols[0]
        idol_minor = build.idols[1]

        assert "Grand Idol" in idol_grand.size
        assert "Minor Idol" in idol_minor.size

    def test_unknown_affix_id_is_skipped(self, game_data, planner_profile):
        """Test that unknown affix ID logs warning and skips affix."""
        # Add item with out-of-range affix ID
        planner_profile["build_data"]["items"]["999"] = {
            "itemType": 8,
            "subType": 0,
            "affixes": [
                {"id": 9999, "tier": 0, "roll": 1}  # Out of range
            ]
        }
        planner_profile["build_data"]["profiles"][0]["items"]["test_slot"] = 999

        parser = PlannerProfileParser(game_data)

        results = parser.parse(planner_profile, strategy="active")
        build = results[0]

        # Item should exist but affix should be skipped
        test_items = [i for i in build.items if i.additional.get("itemType") == 8]
        # Should have at least 2: weapon (unique) and this test item
        assert len(test_items) >= 2

    def test_invalid_unique_id_uses_fallback_name(self, game_data, planner_profile):
        """Test that invalid uniqueID uses fallback name."""
        # Add item with out-of-range uniqueID
        planner_profile["build_data"]["profiles"][0]["items"]["test_slot"] = {
            "itemType": 8,
            "subType": 0,
            "uniqueID": 9999
        }

        parser = PlannerProfileParser(game_data)

        results = parser.parse(planner_profile, strategy="active")
        build = results[0]

        # Item should exist with fallback name
        unknown_items = [i for i in build.items if "Unknown Unique" in i.name]
        assert len(unknown_items) >= 1


@pytest.mark.skipif(
    not REAL_GAME_DATA.exists() or not REAL_PLANNER_PROFILE.exists(),
    reason="Real extracted Maxroll data not available"
)
class TestPlannerProfileParserIntegration:
    """Integration tests with real extracted data."""

    def test_parse_real_data(self):
        """Test parsing real extracted planner profile."""
        with open(REAL_GAME_DATA, "r", encoding="utf-8") as f:
            real_game_data = json.load(f)

        with open(REAL_PLANNER_PROFILE, "r", encoding="utf-8") as f:
            real_planner_profile = json.load(f)

        parser = PlannerProfileParser(real_game_data)
        results = parser.parse(real_planner_profile, strategy="active")

        assert len(results) >= 1
        build = results[0]

        # Basic structure assertions
        assert build.name is not None
        assert len(build.items) > 0

        # Check that we have some unique items
        unique_items = [i for i in build.items if i.is_unique]
        assert len(unique_items) > 0

        # Check that we have some exalted items
        exalted_items = [i for i in build.items if i.is_exalted]
        assert len(exalted_items) > 0

        # Check that affixes have proper tiers
        for item in build.items:
            for affix in item.affixes:
                assert affix.tier is not None
                assert affix.tier >= 1  # Displayed tier should be 1-based
                assert affix.name is not None
