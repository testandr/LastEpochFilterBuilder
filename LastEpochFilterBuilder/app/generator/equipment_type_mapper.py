"""Equipment Type Mapper for Last Epoch XML Generator.

Maps numeric item_type values from planner/game data to Last Epoch XML Equipment Type enum strings.

Phase 0B1: Core equipment slots only (no weapons, no off-hand, no idols).
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
# - Real XML export: data/debug/filters/xml_semantics_test.xml
# - Parser slot mapping in app/parsers/planner_profile_parser.py
#
# Phase 0B1 scope: Core equipment slots only
# - Helmet, Body Armor, Belt, Boots, Gloves (armor)
# - Amulet, Ring, Relic (jewelry)
#
# NOT INCLUDED (future phases):
# - Weapons (item_type 5-16, 23-24): Require weapon-specific XML EquipmentType research
# - Off-hand (item_type 17-19): Require off-hand-specific XML EquipmentType research
# - Idols (item_type 25-33): Handled in Phase 0B2 with idol size mapping
#
EQUIPMENT_TYPE_MAP = {
    0: "HELMET",
    1: "BODY_ARMOR",
    2: "BELT",
    3: "BOOTS",
    4: "GLOVES",
    20: "AMULET",
    21: "RING",
    22: "RELIC",
}


def map_equipment_type(item_type: Optional[int], sub_type: Optional[int] = None) -> str:
    """Map numeric item_type to Last Epoch XML EquipmentType enum string.

    Args:
        item_type: Numeric item type from planner/game data
        sub_type: Numeric sub type (currently unused, reserved for future)

    Returns:
        XML EquipmentType enum string (e.g., "HELMET", "GLOVES", "RING")

    Raises:
        EquipmentTypeMappingError: If item_type is None, unknown, or out of scope

    Notes:
        - sub_type is accepted but currently unused. Sub-type semantics remain unresolved.
        - Weapons, off-hand, and idols are out of scope and will raise explicit errors.
        - No fallback or guessing. Unknown types fail fast with clear error message.
    """
    if item_type is None:
        raise EquipmentTypeMappingError("item_type is None: cannot map to EquipmentType")

    if item_type not in EQUIPMENT_TYPE_MAP:
        # Check if it's a weapon, off-hand, or idol (out of scope but recognizable)
        if 5 <= item_type <= 16 or item_type in (23, 24):
            raise EquipmentTypeMappingError(
                f"item_type {item_type} is a weapon type (out of scope for Phase 0B1). "
                "Weapon EquipmentType mapping requires additional research."
            )
        elif 17 <= item_type <= 19:
            raise EquipmentTypeMappingError(
                f"item_type {item_type} is an off-hand type (out of scope for Phase 0B1). "
                "Off-hand EquipmentType mapping requires additional research."
            )
        elif 25 <= item_type <= 33:
            raise EquipmentTypeMappingError(
                f"item_type {item_type} is an idol type (out of scope for Phase 0B1). "
                "Idol EquipmentType handled separately in Phase 0B2."
            )
        else:
            raise EquipmentTypeMappingError(
                f"item_type {item_type} is unknown or unmapped. "
                "No EquipmentType mapping available."
            )

    return EQUIPMENT_TYPE_MAP[item_type]
