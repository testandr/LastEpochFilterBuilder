"""Idol Size Mapper for Last Epoch XML Generator.

Maps human-readable idol size strings to Last Epoch XML EquipmentType enum strings.

Phase 0B2: Idol size dimension-based mapping.
"""

import re
from typing import Optional


class IdolSizeMappingError(Exception):
    """Raised when idol size cannot be mapped to XML EquipmentType."""
    pass


# Regex to extract dimensions from parser format: "Name (WxH)"
_DIMENSION_PATTERN = re.compile(r'\((\d+)x(\d+)\)')


def map_idol_size(size: Optional[str]) -> str:
    """Map human-readable idol size to Last Epoch XML EquipmentType enum string.

    Args:
        size: Human-readable idol size string from parser (e.g., "Minor Idol (1x1)")
              or None

    Returns:
        XML EquipmentType enum string in format "IDOL_WxH" (e.g., "IDOL_1x1")

    Raises:
        IdolSizeMappingError: If size is None, empty, or does not contain valid dimensions

    Notes:
        - Extracts dimensions from parentheses using regex pattern: (WxH)
        - Formats as IDOL_WxH where W=width, H=height
        - Does not validate idol name or perform fuzzy matching
        - Does not fallback to generic values
        - Unknown or malformed sizes fail explicitly

    Examples:
        >>> map_idol_size("Minor Idol (1x1)")
        "IDOL_1x1"

        >>> map_idol_size("Grand Idol (1x3)")
        "IDOL_1x3"

        >>> map_idol_size("Unknown Idol")
        Raises IdolSizeMappingError
    """
    if size is None:
        raise IdolSizeMappingError("idol size is None: cannot map to EquipmentType")

    size_normalized = size.strip()

    if not size_normalized:
        raise IdolSizeMappingError("idol size is empty: cannot map to EquipmentType")

    # Extract dimensions from (WxH) pattern
    match = _DIMENSION_PATTERN.search(size_normalized)

    if not match:
        raise IdolSizeMappingError(
            f"idol size '{size}' does not contain valid dimensions in (WxH) format. "
            "Cannot map to EquipmentType."
        )

    width = match.group(1)
    height = match.group(2)

    return f"IDOL_{width}x{height}"


def map_idol_item_type(item_type: Optional[int]) -> str:
    """Map numeric idol item_type to Last Epoch XML EquipmentType enum string.

    Args:
        item_type: Numeric idol item type from planner/game data

    Returns:
        XML EquipmentType enum string in format "IDOL_WxH"

    Raises:
        IdolSizeMappingError: If item_type is None, unknown, or not an idol type

    Notes:
        - Uses confirmed mapping from planner parser IDOL_SIZES constant
        - Only supports item_type values with known dimensions
        - Does not query game_data directly
        - Unknown item_type fails explicitly
        - Internally delegates to map_idol_size for dimension extraction

    Known mappings:
        26 -> "Minor Idol (1x1)" -> IDOL_1x1
        27 -> "Humble Idol (1x2)" -> IDOL_1x2
        29 -> "Grand Idol (1x3)" -> IDOL_1x3
        33 -> "Adorned Idol (1x4)" -> IDOL_1x4
    """
    if item_type is None:
        raise IdolSizeMappingError("item_type is None: cannot map to idol EquipmentType")

    # Confirmed mapping from planner parser IDOL_SIZES
    IDOL_ITEM_TYPE_MAP = {
        26: "Minor Idol (1x1)",
        27: "Humble Idol (1x2)",
        29: "Grand Idol (1x3)",
        33: "Adorned Idol (1x4)",
    }

    if item_type not in IDOL_ITEM_TYPE_MAP:
        # Check if it's an idol range but unmapped
        if 25 <= item_type <= 41:
            raise IdolSizeMappingError(
                f"item_type {item_type} is in idol range but dimensions are unknown. "
                "Only item_type 26, 27, 29, 33 have confirmed dimension mappings."
            )
        else:
            raise IdolSizeMappingError(
                f"item_type {item_type} is not an idol type. "
                "Idol types are in range 25-41."
            )

    size_string = IDOL_ITEM_TYPE_MAP[item_type]
    return map_idol_size(size_string)
