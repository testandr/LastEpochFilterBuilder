"""Equipment Type Mapper for Last Epoch XML Generator.

Maps numeric item_type values from planner/game data to Last Epoch XML Equipment Type enum strings.

Phase 0B1: Core equipment slots (helmet, armor, belt, boots, gloves, amulet, ring, relic)
Phase 0B3: Weapon and off-hand equipment types
"""

from typing import Optional


class EquipmentTypeMappingError(Exception):
    """Raised when item_type cannot be mapped to XML EquipmentType."""
    pass


# Confirmed mapping from game_data.json itemTypes array
#
# Source:  data/debug/network/extracted/game_data.json
#
# itemTypes[i].displayName -> XML EquipmentType enum
#
# Mapping confirmed by cross-referencing:
# - game_data.json itemTypes array indices
# - Real XML exports:
#   - data/debug/filters/xml_semantics_test.xml (core equipment, idol)
#   - data/debug/filters/weapon_offhand_evidence.xml (weapon, off-hand)
# - Parser slot mapping in app/parsers/planner_profile_parser.py
#
# Phase 0B1 scope: Core equipment slots
# - Helmet, Body Armor, Belt, Boots, Gloves (armor)
# - Amulet, Ring, Relic (jewelry)
#
# Phase 0B3 scope: Weapon and off-hand equipment
# - One-handed weapons: Axe, Dagger, Mace, Sceptre, Sword, Wand
# - Two-handed weapons: Axe, Mace, Spear, Staff, Sword
# - Ranged weapons: Bow
# - Off-hand: Quiver, Shield, Catalyst
#
# NOT INCLUDED:
# - Fist weapon (item_type 11): No XML evidence found
# - Crossbow (item_type 24): No XML evidence found
# - Idols (item_type 25-33): Handled in Phase 0B2 with idol size mapping
#
EQUIPMENT_TYPE_MAP = {
    # Core equipment (Phase 0B1)
    0: "HELMET",
    1: "BODY_ARMOR",
    2: "BELT",
    3: "BOOTS",
    4: "GLOVES",
    20: "AMULET",
    21: "RING",
    22: "RELIC",

    # One-handed weapons (Phase 0B3)
    5: "ONE_HANDED_AXE",
    6: "ONE_HANDED_DAGGER",
    7: "ONE_HANDED_MACES",
    8: "ONE_HANDED_SCEPTRE",
    9: "ONE_HANDED_SWORD",
    10: "WAND",
    # 11: Fist - NO XML EVIDENCE

    # Two-handed weapons (Phase 0B3)
    12: "TWO_HANDED_AXE",
    13: "TWO_HANDED_MACE",
    14: "TWO_HANDED_SPEAR",
    15: "TWO_HANDED_STAFF",
    16: "TWO_HANDED_SWORD",

    # Off-hand (Phase 0B3)
    17: "QUIVER",
    18: "SHIELD",
    19: "CATALYST",

    # Ranged weapons (Phase 0B3)
    23: "BOW",
    # 24: Crossbow - NO XML EVIDENCE
}


def map_equipment_type(item_type: Optional[int], sub_type: Optional[int] = None) -> str:
    """Map numeric item_type to Last Epoch XML EquipmentType enum string.

    Args:
        item_type: Numeric item type from planner/game data
        sub_type: Numeric sub type (currently unused, reserved for future)

    Returns:
        XML EquipmentType enum string (e.g., "HELMET", "GLOVES", "ONE_HANDED_AXE", "SHIELD")

    Raises:
        EquipmentTypeMappingError: If item_type is None, unknown, or unmapped

    Notes:
        - sub_type is accepted but currently unused. Sub-type semantics remain unresolved.
        - Idols are handled separately by idol_size_mapper.py (Phase 0B2).
        - Fist (item_type 11) and Crossbow (item_type 24) have no XML evidence.
        - No fallback or guessing. Unknown types fail fast with clear error message.
    """
    if item_type is None:
        raise EquipmentTypeMappingError("item_type is None: cannot map to EquipmentType")

    if item_type not in EQUIPMENT_TYPE_MAP:
        # Check if it's a known but unmapped type
        if item_type == 11:
            raise EquipmentTypeMappingError(
                f"item_type {item_type} is Fist weapon (no XML EquipmentType evidence). "
                "Cannot generate XML rules for Fist weapons."
            )
        elif item_type == 24:
            raise EquipmentTypeMappingError(
                f"item_type {item_type} is Crossbow (no XML EquipmentType evidence). "
                "Cannot generate XML rules for Crossbow weapons."
            )
        elif 25 <= item_type <= 33:
            raise EquipmentTypeMappingError(
                f"item_type {item_type} is an idol type. "
                "Idol EquipmentType handled separately by idol_size_mapper.py (Phase 0B2)."
            )
        else:
            raise EquipmentTypeMappingError(
                f"item_type {item_type} is unknown or unmapped. "
                "No EquipmentType mapping available."
            )

    return EQUIPMENT_TYPE_MAP[item_type]
