"""Tests for equipment_type_mapper.py

Phase 0B1: Core equipment type mapping validation.
"""

import pytest

from app.generator.equipment_type_mapper import (
    EquipmentTypeMappingError,
    map_equipment_type,
)


class TestEquipmentTypeMappingConfirmed:
    """Test confirmed equipment type mappings from game_data.json."""

    def test_helmet_mapping(self):
        """item_type 0 maps to HELMET."""
        assert map_equipment_type(0) == "HELMET"

    def test_body_armor_mapping(self):
        """item_type 1 maps to BODY_ARMOR."""
        assert map_equipment_type(1) == "BODY_ARMOR"

    def test_belt_mapping(self):
        """item_type 2 maps to BELT."""
        assert map_equipment_type(2) == "BELT"

    def test_boots_mapping(self):
        """item_type 3 maps to BOOTS."""
        assert map_equipment_type(3) == "BOOTS"

    def test_gloves_mapping(self):
        """item_type 4 maps to GLOVES."""
        assert map_equipment_type(4) == "GLOVES"

    def test_amulet_mapping(self):
        """item_type 20 maps to AMULET."""
        assert map_equipment_type(20) == "AMULET"

    def test_ring_mapping(self):
        """item_type 21 maps to RING."""
        assert map_equipment_type(21) == "RING"

    def test_relic_mapping(self):
        """item_type 22 maps to RELIC."""
        assert map_equipment_type(22) == "RELIC"


class TestEquipmentTypeMappingDeterministic:
    """Test deterministic behavior and immutability."""

    def test_same_input_same_output(self):
        """Multiple calls with same item_type return same result."""
        result1 = map_equipment_type(4)
        result2 = map_equipment_type(4)
        assert result1 == result2
        assert result1 == "GLOVES"

    def test_all_confirmed_types_covered(self):
        """All confirmed equipment types return valid XML enum strings."""
        confirmed_types = [0, 1, 2, 3, 4, 20, 21, 22]
        for item_type in confirmed_types:
            result = map_equipment_type(item_type)
            assert isinstance(result, str)
            assert len(result) > 0
            assert result.isupper()  # XML enum convention


class TestEquipmentTypeMappingSubType:
    """Test sub_type parameter behavior."""

    def test_sub_type_accepted_but_unused(self):
        """sub_type parameter is accepted but does not affect output."""
        # Current implementation: sub_type semantics unresolved, parameter ignored
        result1 = map_equipment_type(4, sub_type=None)
        result2 = map_equipment_type(4, sub_type=0)
        result3 = map_equipment_type(4, sub_type=99)
        assert result1 == result2 == result3 == "GLOVES"

    def test_sub_type_does_not_change_confirmed_mapping(self):
        """sub_type does not override confirmed item_type mapping."""
        assert map_equipment_type(3, sub_type=0) == "BOOTS"
        assert map_equipment_type(3, sub_type=5) == "BOOTS"


class TestEquipmentTypeMappingErrorCases:
    """Test explicit failure for unknown/out-of-scope types."""

    def test_none_item_type_raises_error(self):
        """None item_type raises EquipmentTypeMappingError."""
        with pytest.raises(EquipmentTypeMappingError) as exc_info:
            map_equipment_type(None)
        assert "None" in str(exc_info.value)

    def test_weapon_type_raises_explicit_error(self):
        """Weapon item_type raises EquipmentTypeMappingError with explicit message."""
        weapon_types = [5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 23, 24]
        for item_type in weapon_types:
            with pytest.raises(EquipmentTypeMappingError) as exc_info:
                map_equipment_type(item_type)
            assert "weapon" in str(exc_info.value).lower()
            assert "0B1" in str(exc_info.value)

    def test_offhand_type_raises_explicit_error(self):
        """Off-hand item_type raises EquipmentTypeMappingError with explicit message."""
        offhand_types = [17, 18, 19]
        for item_type in offhand_types:
            with pytest.raises(EquipmentTypeMappingError) as exc_info:
                map_equipment_type(item_type)
            assert "off-hand" in str(exc_info.value).lower()
            assert "0B1" in str(exc_info.value)

    def test_idol_type_raises_explicit_error(self):
        """Idol item_type raises EquipmentTypeMappingError with explicit message."""
        idol_types = [25, 26, 27, 28, 29, 30, 31, 32, 33]
        for item_type in idol_types:
            with pytest.raises(EquipmentTypeMappingError) as exc_info:
                map_equipment_type(item_type)
            assert "idol" in str(exc_info.value).lower()
            assert "0B2" in str(exc_info.value)

    def test_unknown_type_raises_explicit_error(self):
        """Unknown item_type raises EquipmentTypeMappingError."""
        unknown_types = [99, 100, 999]
        for item_type in unknown_types:
            with pytest.raises(EquipmentTypeMappingError) as exc_info:
                map_equipment_type(item_type)
            assert "unknown" in str(exc_info.value).lower() or "unmapped" in str(exc_info.value).lower()

    def test_negative_item_type_raises_error(self):
        """Negative item_type raises EquipmentTypeMappingError."""
        with pytest.raises(EquipmentTypeMappingError):
            map_equipment_type(-1)


class TestEquipmentTypeMappingNoSilentFallback:
    """Verify no silent fallback or guessing behavior."""

    def test_no_generic_fallback(self):
        """Unknown types do NOT fall back to generic values."""
        with pytest.raises(EquipmentTypeMappingError):
            map_equipment_type(999)
        # Mapper must NOT return generic strings like "ITEM" or "UNKNOWN"

    def test_no_guessing(self):
        """Mapper does NOT guess or infer EquipmentType from nearby values."""
        # Adjacent to BOOTS (3) but unmapped
        with pytest.raises(EquipmentTypeMappingError):
            map_equipment_type(34)


class TestEquipmentTypeMappingXMLConformance:
    """Verify XML enum conformance for confirmed mappings."""

    def test_all_uppercase(self):
        """All confirmed EquipmentType strings are uppercase."""
        confirmed_types = [0, 1, 2, 3, 4, 20, 21, 22]
        for item_type in confirmed_types:
            result = map_equipment_type(item_type)
            assert result.isupper()

    def test_no_whitespace(self):
        """EquipmentType strings contain no whitespace."""
        confirmed_types = [0, 1, 2, 3, 4, 20, 21, 22]
        for item_type in confirmed_types:
            result = map_equipment_type(item_type)
            assert " " not in result
            assert "\t" not in result
            assert "\n" not in result

    def test_body_armor_uses_underscore(self):
        """BODY_ARMOR uses underscore (XML convention)."""
        assert map_equipment_type(1) == "BODY_ARMOR"
        assert "_" in map_equipment_type(1)


class TestEquipmentTypeMappingProjectSlots:
    """Verify all project-relevant equipment slots are covered."""

    def test_helmet_slot_covered(self):
        """Helmet slot is mapped."""
        assert map_equipment_type(0) == "HELMET"

    def test_body_armor_slot_covered(self):
        """Body Armor slot is mapped."""
        assert map_equipment_type(1) == "BODY_ARMOR"

    def test_gloves_slot_covered(self):
        """Gloves slot is mapped."""
        assert map_equipment_type(4) == "GLOVES"

    def test_boots_slot_covered(self):
        """Boots slot is mapped."""
        assert map_equipment_type(3) == "BOOTS"

    def test_belt_slot_covered(self):
        """Belt slot is mapped."""
        assert map_equipment_type(2) == "BELT"

    def test_amulet_slot_covered(self):
        """Amulet slot is mapped."""
        assert map_equipment_type(20) == "AMULET"

    def test_ring_slot_covered(self):
        """Ring slot is mapped."""
        assert map_equipment_type(21) == "RING"

    def test_relic_slot_covered(self):
        """Relic slot is mapped."""
        assert map_equipment_type(22) == "RELIC"
